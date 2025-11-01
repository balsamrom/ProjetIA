import os
import re
import joblib
import pickle
import pandas as pd
import numpy as np
from django.shortcuts import redirect, render, HttpResponse, get_object_or_404
from datetime import datetime
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth import logout as django_logout
from django.http import JsonResponse
from django.conf import settings
from sklearn.feature_extraction.text import TfidfVectorizer
import json
try:
    import requests
except ImportError:
    requests = None
import urllib.parse
import random
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required

try:
    import openai
except Exception:
    openai = None
else:
    # Initialiser la clé API OpenAI à partir des settings si disponible
    try:
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if api_key:
            openai.api_key = api_key
    except Exception:
        pass

# Importez vos modèles et forms
from .models import Contact, register_table, Hotel, Room, Reservation, Review
from .forms import HotelForm, RoomForm, ReservationForm, ReviewForm
from .hotels.ml_models.reputation_predictor import reputation_predictor, HotelReputationPredictor
# Disponibilité dynamique du modèle
def _get_reputation_predictor():
    """Return a loaded predictor instance, attempting reload with explicit path if needed."""
    pred = reputation_predictor
    if not getattr(pred, 'model_loaded', False):
        # Essayer de recharger avec un chemin explicite
        try:
            candidates = []
            override_path = getattr(settings, 'HOTEL_REPUTATION_MODEL_PATH', None)
            if override_path:
                candidates.append(override_path)
            # À côté de manage.py (racine projet)
            candidates.append(os.path.join(settings.BASE_DIR, 'hotel_review_tfidf_logreg.pkl'))

            for p in candidates:
                try:
                    pred = HotelReputationPredictor(model_path=p)
                    if getattr(pred, 'model_loaded', False):
                        break
                except Exception:
                    continue
        except Exception:
            pass
    return pred

PREDICTOR_AVAILABLE = getattr(_get_reputation_predictor(), 'model_loaded', False)

# Normalisation des libellés de réputation pour l'UI
def _normalize_reputation_label(val):
    try:
        s = str(val).strip().lower()
    except Exception:
        s = ""
    # Binaire commun
    if s in {"1", "pos", "positive", "positif", "good", "bon", "true"}:
        return "Bon"
    if s in {"0", "neg", "negative", "négatif", "bad", "mauvais", "false"}:
        return "Mauvais"
    # Multi-classes déjà lisibles
    mapping = {
        "excellent": "Excellent",
        "tres bon": "Très bon",
        "très bon": "Très bon",
        "bon": "Bon",
        "moyen": "Moyen",
        "faible": "Mauvais",
        "mauvais": "Mauvais",
        "poor": "Mauvais",
        "average": "Moyen",
        "very good": "Très bon",
    }
    return mapping.get(s, val)

# === CONFIGURATION ML SENTIMENT ===
try:
    sentiment_model_paths = [
        os.path.join(settings.BASE_DIR, 'voguevue', 'hotels', 'ml_models', 'sentiment_fr.pkl'),
        os.path.join(settings.BASE_DIR, 'voguevue', 'hotels', 'ml_models', 'hotel_review_tfidf_logreg.pkl'),
        os.path.join(settings.BASE_DIR, 'hotel_review_tfidf_logreg.pkl'),
    ]
    
    sentiment_model = None
    for path in sentiment_model_paths:
        if os.path.exists(path):
            sentiment_model = joblib.load(path)
            print(f"Sentiment model loaded: {path}")
            break
    
    if sentiment_model is None:
        pass
        
except Exception as e:
    print(f"Error loading sentiment model: {e}")
    sentiment_model = None

def predict_sentiment(text):
    """Analyse de sentiment avec fallback"""
    if sentiment_model is None:
        return {"label": "Error", "probability": 0, "error": "sentiment_model_not_loaded"}
    
    try:
        # Nettoyage du texte
        text = text.lower()
        text = re.sub(r"http\S+", "", text)
        text = re.sub(r"[^a-zA-Z\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        
        # Prédiction
        pred = sentiment_model.predict([text])[0]
        probs = sentiment_model.predict_proba([text])[0]
        # Déterminer l'index de la classe positive depuis classes_
        classes = list(getattr(sentiment_model, 'classes_', []))
        pos_aliases = [1, 'Good', 'Positive', 'pos', 'good', 'positive']
        pos_idx = None
        for alias in pos_aliases:
            if alias in classes:
                pos_idx = classes.index(alias)
                break
        if pos_idx is None:
            # Fallback: si impossible à déduire, prendre la proba max comme confiance
            pos_idx = int(np.argmax(probs))
        proba_pos = float(probs[pos_idx])
        # Normaliser le label en 'Good'/'Bad' si possible
        if str(pred).lower() in ('1', 'good', 'positive', 'pos'):
            label = 'Good'
        elif str(pred).lower() in ('0', 'bad', 'negative', 'neg'):
            label = 'Bad'
        else:
            # si labels custom, garder tel quel mais retourner la proba de la classe positive déduite
            label = str(pred)
        # Aligner la probabilité avec le label final
        if label == 'Good':
            proba_label = proba_pos
        elif label == 'Bad':
            proba_label = 1.0 - proba_pos
        else:
            proba_label = proba_pos
        return {
            "label": label,
            "probability": round(proba_label * 100, 2)
        }
    except Exception as e:
        return {"label": "Error", "probability": 0, "error": str(e)}

# === HELPERS ===
def recommend_hotels(hotels, city=None, budget=None, top_k=6):
    """Recommandation basique"""
    try:
        filtered = hotels
        if city:
            filtered = filtered.filter(city__icontains=city)
        return list(filtered)[:top_k]
    except Exception:
        return list(hotels)[:top_k]

def compute_eco_score(hotel):
    """Score écologique basique"""
    return 65  # Valeur par défaut

# === VUES PRINCIPALES ===
def index(request):
    return render(request, 'main/index.html')

def about(request):
    return render(request, 'main/about.html')

def contact(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        contact = Contact(name=name, email=email, message=message, date=datetime.today())
        contact.save()
        messages.success(request, 'Votre message a été envoyé!')
    return render(request, 'main/contact.html')

def travels(request):
    return render(request, 'main/travels.html')

def signin(request):
    if request.method == "POST":
        username = request.POST.get('uname')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password) 
        if user is not None:
            login(request, user)
            messages.success(request, 'Connexion réussie!')
            return redirect('index')
        else:
            messages.error(request, 'Identifiants incorrects')
    return render(request, 'authentication/signin.html')

def signup(request):
    if request.method == 'POST':
        fname = request.POST.get("firstname") 
        last = request.POST.get("lastname")
        un = request.POST.get("uname")
        pwd = request.POST.get("password")
        em = request.POST.get("email")
        con = request.POST.get("contact_number")

        if User.objects.filter(username=un).exists():
            messages.error(request, "Ce nom d'utilisateur existe déjà")
            return render(request, 'authentication/signup.html')
        
        if User.objects.filter(email=em).exists():
            messages.error(request, "Cet email est déjà utilisé")
            return render(request, 'authentication/signup.html')

        usr = User.objects.create_user(un, em, pwd)
        usr.first_name = fname
        usr.last_name = last
        usr.save()

        reg = register_table(user=usr, contact_number=con)
        reg.save()

        messages.success(request, f"Compte créé avec succès, {fname}!")
        return redirect('signin')

    return render(request, 'authentication/signup.html')

def logout(request):
    django_logout(request)
    return redirect("/signin" , {"logsign" : " Logged Out Successfully"})

def profile(request):
    if request.user.is_authenticated:
        return render(request, 'main/profile.html')
    else:
        return redirect('signin')

def error_404(request, exception):
    return render(request, 'main/404.html')

def blog(request):
    return render(request, 'main/blog.html')

# === VUES HOTELS ===
def hotel_list(request):
    hotels = Hotel.objects.order_by('-created_at')
    city = request.GET.get('city') or None
    q = (request.GET.get('q') or '').strip()
    budget_str = request.GET.get('budget')
    
    try:
        budget = float(budget_str) if budget_str else None
    except ValueError:
        budget = None

    # Recherche simple par nom/ville
    if q:
        hotels = hotels.filter(models.Q(name__icontains=q) | models.Q(city__icontains=q))

    recommended = recommend_hotels(hotels, city=city, budget=budget, top_k=6)
    
    for h in hotels:
        h.eco_score = compute_eco_score(h)
    for h in recommended:
        if not hasattr(h, 'eco_score'):
            h.eco_score = compute_eco_score(h)
            
    return render(request, 'main/hotels/hotel_list.html', {
        'hotels': hotels,
        'recommended': recommended,
        'q_city': city or '',
        'q_budget': budget_str or '',
        'q': q,
        'model_available': PREDICTOR_AVAILABLE,
    })

def hotel_create(request):
    if request.method == 'POST':
        form = HotelForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Hôtel créé avec succès')
            return redirect('hotel_list')
    else:
        form = HotelForm()
    return render(request, 'main/hotels/hotel_form.html', {'form': form, 'mode': 'create'})

def hotel_detail(request, pk):
    hotel = get_object_or_404(Hotel, pk=pk)
    reviews = hotel.reviews.all()
    
    # Analyse de réputation
    reputation_data = None
    predictor = _get_reputation_predictor()
    if getattr(predictor, 'model_loaded', False) and reviews:
        review_texts = [review.review_text for review in reviews if review.review_text]
        if review_texts:
            reputation_data = predictor.predict_from_reviews(review_texts)
            if isinstance(reputation_data, dict) and 'overall_reputation' in reputation_data:
                reputation_data['overall_reputation'] = _normalize_reputation_label(reputation_data['overall_reputation'])
    
    eco_score = compute_eco_score(hotel)
    
    context = {
        'hotel': hotel,
        'reviews': reviews,
        'reputation_data': reputation_data,
        'eco_score': eco_score,
        'model_available': getattr(predictor, 'model_loaded', False),
        'predictor_error': getattr(predictor, 'last_error', None),
    }
    return render(request, 'main/hotels/hotel_detail.html', context)

def hotel_update(request, pk):
    hotel = get_object_or_404(Hotel, pk=pk)
    if request.method == 'POST':
        form = HotelForm(request.POST, instance=hotel)
        if form.is_valid():
            form.save()
            messages.success(request, 'Hôtel modifié avec succès')
            return redirect('hotel_detail', pk=pk)
    else:
        form = HotelForm(instance=hotel)
    return render(request, 'main/hotels/hotel_form.html', {'form': form, 'mode': 'update', 'hotel': hotel})

def hotel_delete(request, pk):
    hotel = get_object_or_404(Hotel, pk=pk)
    if request.method == 'POST':
        hotel.delete()
        messages.success(request, 'Hôtel supprimé')
        return redirect('hotel_list')
    return render(request, 'main/hotels/hotel_confirm_delete.html', {'hotel': hotel})

def hotel_payment(request, pk):
    """Page de paiement / récapitulatif pour un hôtel"""
    hotel = get_object_or_404(Hotel, pk=pk)
    rooms = hotel.rooms.all() if hasattr(hotel, 'rooms') else []
    if request.method == 'POST':
        name = request.POST.get('fullname', '').strip()
        room_id = request.POST.get('room_id')
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        # Validations minimales
        if not name or not room_id or not check_in or not check_out:
            messages.error(request, "Merci de renseigner tous les champs obligatoires.")
        else:
            try:
                room = Room.objects.get(id=int(room_id), hotel=hotel)
                # Créer la réservation
                Reservation.objects.create(
                    hotel=hotel,
                    room=room,
                    customer_name=name,
                    check_in=check_in,
                    check_out=check_out,
                )
                messages.success(request, "Réservation enregistrée. Vous recevrez une confirmation.")
                return redirect('hotel_detail', pk=pk)
            except Room.DoesNotExist:
                messages.error(request, "Chambre invalide pour cet hôtel.")
            except Exception as e:
                messages.error(request, f"Erreur: {e}")
    return render(request, 'main/hotels/hotel_payment.html', {
        'hotel': hotel,
        'rooms': rooms,
    })

def reputation_analysis(request):
    """Analyse de réputation de tous les hôtels"""
    hotels = Hotel.objects.all().prefetch_related('reviews')
    predictor = _get_reputation_predictor()
    analysis_results = []
    
    # Exécuter aussi en GET si le modèle est chargé (remplit la page immédiatement)
    if getattr(predictor, 'model_loaded', False):
        print("🔄 Lancement de l'analyse de réputation...")
        for hotel in hotels:
            reviews = hotel.reviews.all()
            review_texts = [review.review_text for review in reviews if review.review_text]
            if review_texts:
                try:
                    result = predictor.predict_from_reviews(review_texts)
                    if isinstance(result, dict) and 'overall_reputation' in result:
                        result['overall_reputation'] = _normalize_reputation_label(result['overall_reputation'])
                    analysis_results.append({
                        'hotel': hotel,
                        'result': result,
                        'review_count': len(review_texts)
                    })
                    print(f"Analyzed {hotel.name}: {result.get('overall_reputation')}")
                except Exception as e:
                    print(f"Error for {hotel.name}: {e}")
                    analysis_results.append({
                        'hotel': hotel,
                        'result': None,
                        'review_count': len(review_texts)
                    })
            else:
                analysis_results.append({
                    'hotel': hotel,
                    'result': None,
                    'review_count': 0
                })
        if request.method == 'POST':
            messages.success(request, f'Analyse terminée pour {len(analysis_results)} hôtels')
    
    context = {
        'hotels': hotels,
        'analysis_results': analysis_results,
        'model_available': getattr(predictor, 'model_loaded', False),
        'hotels_count': hotels.count(),
        'predictor_error': getattr(predictor, 'last_error', None),
    }
    return render(request, 'main/hotels/reputation_analysis.html', context)
def predict_hotel_reputation_api(request, pk):
    """API pour prédire la réputation d'un hôtel"""
    hotel = get_object_or_404(Hotel, pk=pk)
    reviews = hotel.reviews.all()
    review_texts = [review.review_text for review in reviews if review.review_text]
    
    try:
        result = reputation_predictor.predict_from_reviews(review_texts)
        return JsonResponse({
            'success': True,
            'hotel_id': hotel.id,
            'hotel_name': hotel.name,
            'overall_reputation': result.get('overall_reputation'),
            'confidence': result.get('confidence'),
            'total_reviews_analyzed': result.get('total_reviews_analyzed'),
            'breakdown': result.get('breakdown'),
            'model_accuracy': result.get('model_accuracy')
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def ai_hotel_summary(request, pk):
    """Résumé IA des avis: paragraphe + 3 pros/3 cons (fallback extractif)."""
    hotel = get_object_or_404(Hotel, pk=pk)
    reviews = list(hotel.reviews.values_list('review_text', flat=True))[:80]
    try:
        if not reviews:
            return JsonResponse({'success': False, 'error': 'no_reviews'})

        # OpenAI si dispo
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if api_key:
            try:
                joined = "\n- ".join([r for r in reviews if r])[:6000]
                prompt = (
                    "Voici une liste d'avis d'hôtel (français). Fais: \n"
                    "1) Un résumé concis (3-5 lignes) en français. \n"
                    "2) Trois points forts (Pros). \n"
                    "3) Trois points faibles (Cons). \n"
                    "Garde un ton neutre et utile.\n\nAvis:\n- " + joined
                )
                if requests is None:
                    return JsonResponse({'success': False, 'error': 'requests library not installed'})
                r = requests.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
                    json={
                        'model': 'gpt-3.5-turbo',
                        'messages': [
                            {'role':'system','content':'Tu es un analyste qui synthétise des avis clients.'},
                            {'role':'user','content': prompt}
                        ],
                        'max_tokens': 400,
                        'temperature': 0.4
                    }, timeout=20
                )
                if r.ok:
                    text = r.json().get('choices',[{}])[0].get('message',{}).get('content','').strip()
                    # Separation simple
                    summary = text
                    pros, cons = [], []
                    # Essayer d'extraire des lignes pros/cons si présentes
                    for line in text.splitlines():
                        s=line.strip('-• ').lower()
                        if s.startswith('pros') or s.startswith('points forts'):
                            continue
                        if s.startswith('cons') or s.startswith('points faibles'):
                            continue
                    return JsonResponse({'success': True, 'summary': summary, 'pros': pros, 'cons': cons})
            except Exception:
                pass

        # Fallback extractif simple: premiers avis + ngram
        head = [r for r in reviews if r][:3]
        summary = " ".join(head)[:600]
        return JsonResponse({'success': True, 'summary': summary, 'pros': [], 'cons': []})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def api_generate_hotel_description(request):
    """Génère une description d'hôtel avec OpenAI"""
    try:
        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'Méthode POST requise'}, status=405)

        # Charger les données JSON
        data = json.loads(request.body)
        hotel_name = data.get('hotel_name', '').strip()
        city = data.get('city', '').strip()
        features = data.get('features', [])
        address = data.get('address', '').strip()
        
        # Validation
        if not hotel_name:
            return JsonResponse({'success': False, 'error': "Le nom de l'hôtel est requis"}, status=400)
        
        if not city:
            return JsonResponse({'success': False, 'error': 'La ville est requise'}, status=400)

        # Préparer les caractéristiques
        features_text = ", ".join(features) if features else "confortable et accueillant"
        
        # Prompt optimisé
        prompt = f"""
        Tu es un expert en marketing hôtelier. Rédige une description ORIGINALE et UNIQUE en français pour l'hôtel ci-dessous.

        NOM: {hotel_name}
        VILLE: {city}
        ADRESSE: {address or 'N/A'}
        CARACTÉRISTIQUES (pistes): {features_text}

        Contraintes de style:
        - 90 à 130 mots, ton chaleureux et professionnel.
        - Ne commence PAS par "Situé à" ni par une formule générique.
        - Varie les tournures, pas de clichés (« atmosphère chaleureuse », « emplacement idéal »).
        - Mets en avant l'emplacement et 3 atouts concrets (ex: vue, accès, services, ambiance), même si tu dois les déduire du nom/ville.
        - Phrase d'ouverture marquante, dynamique.
        - Pas de listes, 1 paragraphe fluide.
        """

        used_openai = False
        description = ''
        # SerpApi (Google Search) — unique source
        def try_serpapi(qname, qcity, qaddress):
            try:
                api_key = getattr(settings, 'SERPAPI_API_KEY', None)
                if not api_key:
                    return None
                # Essayer plusieurs variantes de requêtes et moteurs
                variants = [
                    f"hôtel {qname} {qcity} {qaddress}",
                    f"hotel {qname} {qcity}",
                    f"{qname} {qcity}",
                    f"{qname}",
                ]
                for query in variants:
                    q = query.strip()
                    if not q:
                        continue
                    loc = f"{qcity}, Tunisie" if qcity else "Tunisie"
                    # 1) Moteur google (web)
                    if requests is None:
                        return None
                    try:
                        sresp = requests.get(
                            'https://serpapi.com/search.json',
                            params={
                                'engine': 'google',
                                'q': q,
                                'hl': 'fr',
                                'gl': 'fr',
                                'google_domain': 'google.fr',
                                'location': loc,
                                'num': 10,
                                'api_key': api_key,
                            }, timeout=12
                        )
                        if sresp.ok:
                            js = sresp.json()
                            kg = js.get('knowledge_graph') or {}
                            kg_desc = (kg.get('description') or kg.get('title') or '').strip()
                            if kg_desc and len(kg_desc) > 40:
                                return kg_desc
                            org = js.get('organic_results') or []
                            for item in org:
                                snip = (item.get('snippet') or '').strip()
                                if snip and len(snip) > 40:
                                    return snip
                            locals_block = js.get('local_results') or {}
                            if isinstance(locals_block, dict):
                                places = locals_block.get('places') or []
                                for p in places:
                                    desc = (p.get('description') or p.get('snippet') or '').strip()
                                    if desc and len(desc) > 40:
                                        return desc
                    except Exception:
                        pass
                    # 2) Moteur google_maps
                    if requests is None:
                        return None
                    try:
                        maps_resp = requests.get(
                            'https://serpapi.com/search.json',
                            params={
                                'engine': 'google_maps',
                                'q': q,
                                'hl': 'fr',
                                'type': 'search',
                                'api_key': api_key,
                            }, timeout=12
                        )
                        if maps_resp.ok:
                            mjs = maps_resp.json()
                            pr = mjs.get('place_results') or {}
                            if isinstance(pr, dict):
                                ed = (pr.get('editorial_summary') or {}).get('overview')
                                if ed and len(ed) > 40:
                                    return ed
                                desc2 = (pr.get('description') or pr.get('snippet') or '').strip()
                                if desc2 and len(desc2) > 40:
                                    return desc2
                    except Exception:
                        pass
            except Exception:
                return None
            return None
        # SerpApi en premier
        serp_text = try_serpapi(hotel_name, city, address)
        if serp_text:
            return JsonResponse({'success': True, 'description': serp_text, 'used_openai': False})
        # Fallback: OpenAI si clé disponible
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if api_key:
            try:
                prompt = (
                    f"Écris un paragraphe bref (80-120 mots) en français décrivant l'hôtel '{hotel_name}' à '{city}'. "
                    f"Évite les clichés trop génériques et ne commence pas par 'Situé à'."
                )
                if requests is None:
                    return JsonResponse({'success': False, 'error': 'requests library not installed'})
                http_resp = requests.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers={
                        'Authorization': f'Bearer {api_key}',
                        'Content-Type': 'application/json',
                    },
                    json={
                        'model': 'gpt-3.5-turbo',
                        'messages': [
                            { 'role': 'system', 'content': 'Tu écris des descriptions d’hôtels claires et utiles.' },
                            { 'role': 'user', 'content': prompt }
                        ],
                        'max_tokens': 280,
                        'temperature': 0.9,
                        'top_p': 0.9
                    },
                    timeout=20
                )
                if http_resp.ok:
                    payload = http_resp.json()
                    description = (payload.get('choices') or [{}])[0].get('message', {}).get('content', '').strip()
                    if description:
                        return JsonResponse({'success': True, 'description': description, 'used_openai': True})
            except Exception:
                pass
        return JsonResponse({'success': False, 'error': 'serp_no_result'}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'}, status=400)
    except Exception as e:
        # Dernier filet de sécurité: renvoyer un fallback plutôt qu'une erreur serveur quand c'est possible
        try:
            data = json.loads(request.body)
            hotel_name = data.get('hotel_name', '').strip()
            city = data.get('city', '').strip()
            features = data.get('features', [])
            if hotel_name and city:
                text = (
                    f"Situé à {city}, l'hôtel {hotel_name} accueille ses hôtes dans une atmosphère chaleureuse. "
                    f"Chambres confortables, service attentionné et emplacement idéal pour découvrir la région. "
                    f"{', '.join(features)}." if features else ""
                ).strip()
                return JsonResponse({'success': True, 'description': text, 'used_openai': False})
        except Exception:
            pass
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# === API: Filters & Search ===
def api_hotels(request):
    """GET /api/hotels?city=&min_price=&max_price=&available=true|false"""
    try:
        qs = Hotel.objects.all().order_by('name')
        city = request.GET.get('city')
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        available = request.GET.get('available')
        q = (request.GET.get('q') or '').strip()

        if city:
            qs = qs.filter(city__icontains=city)
        if q:
            qs = qs.filter(models.Q(name__icontains=q) | models.Q(city__icontains=q))
        try:
            if min_price:
                qs = qs.filter(price_per_night__gte=float(min_price))
            if max_price:
                qs = qs.filter(price_per_night__lte=float(max_price))
        except ValueError:
            pass
        if available in ('true', 'false'):
            qs = qs.filter(is_available=(available == 'true'))

        data = [
            {
                'id': h.id,
                'name': h.name,
                'city': h.city,
                'price_per_night': h.price_per_night,
                'is_available': h.is_available,
                'reviews_count': h.reviews.count(),
            }
            for h in qs
        ]
        return JsonResponse({'results': data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def api_rooms(request):
    """GET /api/rooms?hotel_id=&min_price=&max_price=&available=true|false"""
    try:
        qs = Room.objects.select_related('hotel').all().order_by('hotel__name', 'name')
        hotel_id = request.GET.get('hotel_id')
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        available = request.GET.get('available')
        q = (request.GET.get('q') or '').strip()

        if hotel_id:
            try:
                qs = qs.filter(hotel_id=int(hotel_id))
            except ValueError:
                pass
        if q:
            qs = qs.filter(models.Q(name__icontains=q) | models.Q(hotel__name__icontains=q))
        try:
            if min_price:
                qs = qs.filter(price_per_night__gte=float(min_price))
            if max_price:
                qs = qs.filter(price_per_night__lte=float(max_price))
        except ValueError:
            pass
        if available in ('true', 'false'):
            qs = qs.filter(is_available=(available == 'true'))

        data = [
            {
                'id': r.id,
                'hotel_id': r.hotel_id,
                'hotel_name': r.hotel.name,
                'name': r.name,
                'capacity': r.capacity,
                'price_per_night': r.price_per_night,
                'is_available': r.is_available,
            }
            for r in qs
        ]
        return JsonResponse({'results': data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def api_reservations(request):
    """GET /api/reservations?hotel_id=&room_id=&from=&to="""
    try:
        qs = Reservation.objects.select_related('room__hotel').all().order_by('-check_in')
        hotel_id = request.GET.get('hotel_id')
        room_id = request.GET.get('room_id')
        date_from = request.GET.get('from')
        date_to = request.GET.get('to')

        if hotel_id:
            try:
                qs = qs.filter(room__hotel_id=int(hotel_id))
            except ValueError:
                pass
        if room_id:
            try:
                qs = qs.filter(room_id=int(room_id))
            except ValueError:
                pass
        # Dates ISO (YYYY-MM-DD)
        try:
            if date_from:
                qs = qs.filter(check_in__gte=date_from)
            if date_to:
                qs = qs.filter(check_out__lte=date_to)
        except Exception:
            pass

        data = [
            {
                'id': r.id,
                'hotel_id': r.room.hotel_id,
                'hotel_name': r.room.hotel.name,
                'room_id': r.room_id,
                'room_name': r.room.name,
                'customer_name': r.customer_name,
                'check_in': r.check_in.isoformat() if hasattr(r.check_in, 'isoformat') else str(r.check_in),
                'check_out': r.check_out.isoformat() if hasattr(r.check_out, 'isoformat') else str(r.check_out),
            }
            for r in qs
        ]
        return JsonResponse({'results': data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# === Admin (staff) action: delete review ===
@require_POST
@staff_member_required
def admin_delete_review(request, pk):
    try:
        review = Review.objects.get(pk=pk)
        review.delete()
        return JsonResponse({'success': True})
    except Review.DoesNotExist:
        return JsonResponse({'error': 'Review not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
# ... (ajoutez ici vos autres vues pour rooms, reservations, reviews si nécessaire)

def predict_review_view(request):
    """Vue pour tester l'analyse de sentiment"""
    result = None
    if request.method == "POST":
        review_text = request.POST.get("review_text")
        if review_text:
            result = predict_sentiment(review_text)
            result["review_text"] = review_text
    return render(request, "main/hotels/predict_review.html", {"result": result})

# === VUES MANQUANTES - AJOUTEZ CES FONCTIONS ===

def room_list(request, hotel_id=None):
    """Liste des chambres"""
    qs = Room.objects.select_related('hotel').order_by('hotel__name', 'name')
    # Support GET filter: /rooms/?hotel_id=<id>
    if hotel_id is None:
        try:
            hotel_id = int(request.GET.get('hotel_id')) if request.GET.get('hotel_id') else None
        except ValueError:
            hotel_id = None
    if hotel_id:
        qs = qs.filter(hotel_id=hotel_id)
    # Recherche texte
    q = (request.GET.get('q') or '').strip()
    if q:
        qs = qs.filter(models.Q(name__icontains=q) | models.Q(hotel__name__icontains=q))
    return render(request, 'main/hotels/room_list.html', {'rooms': qs, 'hotel_id': hotel_id})

def room_create(request):
    """Créer une chambre"""
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Chambre créée avec succès')
            return redirect('room_list')
    else:
        form = RoomForm()
    return render(request, 'main/hotels/room_form.html', {'form': form})

def room_detail(request, pk):
    """Détail d'une chambre"""
    try:
        room = Room.objects.get(pk=pk)
    except Room.DoesNotExist:
        return redirect('room_list')
    return render(request, 'main/hotels/room_detail.html', {'room': room})

def room_update(request, pk):
    """Modifier une chambre"""
    try:
        room = Room.objects.get(pk=pk)
    except Room.DoesNotExist:
        return redirect('room_list')
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, 'Chambre modifiée avec succès')
            return redirect('room_list')
    else:
        form = RoomForm(instance=room)
    return render(request, 'main/hotels/room_form.html', {'form': form})

def room_delete(request, pk):
    """Supprimer une chambre"""
    try:
        room = Room.objects.get(pk=pk)
    except Room.DoesNotExist:
        return redirect('room_list')
    if request.method == 'POST':
        room.delete()
        messages.success(request, 'Chambre supprimée')
        return redirect('room_list')
    return render(request, 'main/hotels/room_confirm_delete.html', {'room': room})

def reservation_list(request):
    """Liste des réservations"""
    reservations = Reservation.objects.select_related('room__hotel').order_by('-check_in_date')
    return render(request, 'main/hotels/reservation_list.html', {'reservations': reservations})

def reservation_create(request, room_id=None):
    """Créer une réservation"""
    initial = {}
    if room_id:
        initial['room'] = room_id
    if request.method == 'POST':
        form = ReservationForm(request.POST, initial=initial)
        if form.is_valid():
            form.save()
            messages.success(request, 'Réservation créée avec succès')
            return redirect('reservation_list')
    else:
        form = ReservationForm(initial=initial)
    return render(request, 'main/hotels/reservation_form.html', {'form': form})

def reservation_detail(request, pk):
    """Détail d'une réservation"""
    try:
        reservation = Reservation.objects.get(pk=pk)
    except Reservation.DoesNotExist:
        return redirect('reservation_list')
    return render(request, 'main/hotels/reservation_detail.html', {'reservation': reservation})

def reservation_update(request, pk):
    """Modifier une réservation"""
    try:
        reservation = Reservation.objects.get(pk=pk)
    except Reservation.DoesNotExist:
        return redirect('reservation_list')
    if request.method == 'POST':
        form = ReservationForm(request.POST, instance=reservation)
        if form.is_valid():
            form.save()
            messages.success(request, 'Réservation modifiée avec succès')
            return redirect('reservation_list')
    else:
        form = ReservationForm(instance=reservation)
    return render(request, 'main/hotels/reservation_form.html', {'form': form})

def reservation_delete(request, pk):
    """Supprimer une réservation"""
    try:
        reservation = Reservation.objects.get(pk=pk)
    except Reservation.DoesNotExist:
        return redirect('reservation_list')
    if request.method == 'POST':
        reservation.delete()
        messages.success(request, 'Réservation supprimée')
        return redirect('reservation_list')
    return render(request, 'main/hotels/reservation_confirm_delete.html', {'reservation': reservation})

def reservation_create_for_room(request, room_id):
    """Créer une réservation pour une chambre spécifique"""
    try:
        room = Room.objects.get(id=room_id)
        initial = {'room': room}
    except Room.DoesNotExist:
        messages.error(request, 'Chambre non trouvée.')
        return redirect('room_list')
    
    if request.method == 'POST':
        form = ReservationForm(request.POST, initial=initial)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.room = room
            reservation.save()
            messages.success(request, 'Réservation créée avec succès!')
            return redirect('hotel_list')
    else:
        form = ReservationForm(initial=initial)
    
    return render(request, 'main/hotels/reservation_form.html', {
        'form': form, 
        'room': room
    })

def reserve_cheapest(request, hotel_id):
    """Réserver la chambre la moins chère"""
    try:
        hotel = Hotel.objects.get(pk=hotel_id)
    except Hotel.DoesNotExist:
        return redirect('hotel_list')
    room = Room.objects.filter(hotel=hotel, is_available=True).order_by('price_per_night').first()
    if not room:
        messages.error(request, 'Aucune chambre disponible pour cet hôtel.')
        return redirect('hotel_detail', pk=hotel_id)
    return redirect('reservation_create_for_room', room_id=room.id)

def hotel_reviews(request, hotel_id):
    """Afficher les avis d'un hôtel"""
    try:
        hotel = Hotel.objects.get(id=hotel_id)
        reviews = hotel.reviews.all().select_related('user')
        
        context = {
            'hotel': hotel,
            'reviews': reviews,
        }
        return render(request, 'main/hotels/hotel_reviews.html', context)
        
    except Hotel.DoesNotExist:
        messages.error(request, "Hôtel non trouvé.")
        return redirect('hotel_list')

def create_review(request, hotel_id):
    """Créer un avis"""
    try:
        hotel = Hotel.objects.get(id=hotel_id)
        # Empêcher les utilisateurs non authentifiés de créer un avis
        if not request.user.is_authenticated:
            messages.warning(request, "Veuillez vous connecter pour publier un avis.")
            return redirect('signin')
        
        if request.method == 'POST':
            # Forcer la note de l'avis à être celle de l'hôtel (borne 1..5)
            data = request.POST.copy()
            try:
                hrat = float(hotel.rating) if hotel.rating is not None else 5.0
            except Exception:
                hrat = 5.0
            hrat = max(1, min(5, int(round(hrat))))
            data['rating'] = str(hrat)
            form = ReviewForm(data)
            if form.is_valid():
                review = form.save(commit=False)
                review.hotel = hotel
                review.user = request.user
                # Sécurité supplémentaire
                review.rating = hrat
                review.save()
                messages.success(request, f"Votre avis sur {hotel.name} a été publié !")
                return redirect('hotel_reviews', hotel_id=hotel_id)
        else:
            form = ReviewForm()
        
        context = {
            'hotel': hotel,
            'form': form,
        }
        return render(request, 'main/hotels/create_review.html', context)
        
    except Hotel.DoesNotExist:
        messages.error(request, "Hôtel non trouvé.")
        return redirect('hotel_list')

def my_reviews(request):
    """Afficher mes avis"""
    if not request.user.is_authenticated:
        messages.warning(request, "Veuillez vous connecter pour voir vos avis.")
        return redirect('signin')
    
    reviews = Review.objects.filter(user=request.user).select_related('hotel')
    return render(request, 'main/hotels/my_reviews.html', {'reviews': reviews})


# === VUES MANQUANTES - AJOUTEZ CES FONCTIONS ===

def room_list(request, hotel_id=None):
    """Liste des chambres"""
    qs = Room.objects.select_related('hotel').order_by('hotel__name', 'name')
    if hotel_id:
        qs = qs.filter(hotel_id=hotel_id)
    return render(request, 'main/hotels/room_list.html', {'rooms': qs, 'hotel_id': hotel_id})

def room_create(request):
    """Créer une chambre"""
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Chambre créée avec succès')
            return redirect('room_list')
    else:
        form = RoomForm()
    return render(request, 'main/hotels/room_form.html', {'form': form})

def room_detail(request, pk):
    """Détail d'une chambre"""
    try:
        room = Room.objects.get(pk=pk)
    except Room.DoesNotExist:
        return redirect('room_list')
    return render(request, 'main/hotels/room_detail.html', {'room': room})

def room_update(request, pk):
    """Modifier une chambre"""
    try:
        room = Room.objects.get(pk=pk)
    except Room.DoesNotExist:
        return redirect('room_list')
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, 'Chambre modifiée avec succès')
            return redirect('room_list')
    else:
        form = RoomForm(instance=room)
    return render(request, 'main/hotels/room_form.html', {'form': form})

def room_delete(request, pk):
    """Supprimer une chambre"""
    try:
        room = Room.objects.get(pk=pk)
    except Room.DoesNotExist:
        return redirect('room_list')
    if request.method == 'POST':
        room.delete()
        messages.success(request, 'Chambre supprimée')
        return redirect('room_list')
    return render(request, 'main/hotels/room_confirm_delete.html', {'room': room})

def reservation_list(request):
    """Liste des réservations"""
    reservations = Reservation.objects.select_related('room__hotel').order_by('-check_in_date')
    return render(request, 'main/hotels/reservation_list.html', {'reservations': reservations})

def reservation_create(request, room_id=None):
    """Créer une réservation"""
    initial = {}
    if room_id:
        initial['room'] = room_id
    if request.method == 'POST':
        form = ReservationForm(request.POST, initial=initial)
        if form.is_valid():
            form.save()
            messages.success(request, 'Réservation créée avec succès')
            return redirect('reservation_list')
    else:
        form = ReservationForm(initial=initial)
    return render(request, 'main/hotels/reservation_form.html', {'form': form})

def reservation_detail(request, pk):
    """Détail d'une réservation"""
    try:
        reservation = Reservation.objects.get(pk=pk)
    except Reservation.DoesNotExist:
        return redirect('reservation_list')
    return render(request, 'main/hotels/reservation_detail.html', {'reservation': reservation})

def reservation_update(request, pk):
    """Modifier une réservation"""
    try:
        reservation = Reservation.objects.get(pk=pk)
    except Reservation.DoesNotExist:
        return redirect('reservation_list')
    if request.method == 'POST':
        form = ReservationForm(request.POST, instance=reservation)
        if form.is_valid():
            form.save()
            messages.success(request, 'Réservation modifiée avec succès')
            return redirect('reservation_list')
    else:
        form = ReservationForm(instance=reservation)
    return render(request, 'main/hotels/reservation_form.html', {'form': form})

def reservation_delete(request, pk):
    """Supprimer une réservation"""
    try:
        reservation = Reservation.objects.get(pk=pk)
    except Reservation.DoesNotExist:
        return redirect('reservation_list')
    if request.method == 'POST':
        reservation.delete()
        messages.success(request, 'Réservation supprimée')
        return redirect('reservation_list')
    return render(request, 'main/hotels/reservation_confirm_delete.html', {'reservation': reservation})

def reservation_create_for_room(request, room_id):
    """Créer une réservation pour une chambre spécifique"""
    try:
        room = Room.objects.get(id=room_id)
        initial = {'room': room}
    except Room.DoesNotExist:
        messages.error(request, 'Chambre non trouvée.')
        return redirect('room_list')
    
    if request.method == 'POST':
        form = ReservationForm(request.POST, initial=initial)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.room = room
            reservation.save()
            messages.success(request, 'Réservation créée avec succès!')
            return redirect('hotel_list')
    else:
        form = ReservationForm(initial=initial)
    
    return render(request, 'main/hotels/reservation_form.html', {
        'form': form, 
        'room': room
    })

def reserve_cheapest(request, hotel_id):
    """Réserver la chambre la moins chère"""
    try:
        hotel = Hotel.objects.get(pk=hotel_id)
    except Hotel.DoesNotExist:
        return redirect('hotel_list')
    room = Room.objects.filter(hotel=hotel, is_available=True).order_by('price_per_night').first()
    if not room:
        messages.error(request, 'Aucune chambre disponible pour cet hôtel.')
        return redirect('hotel_detail', pk=hotel_id)
    return redirect('reservation_create_for_room', room_id=room.id)

def hotel_reviews(request, hotel_id):
    """Afficher les avis d'un hôtel"""
    try:
        hotel = Hotel.objects.get(id=hotel_id)
        reviews = hotel.reviews.all().select_related('user')
        
        context = {
            'hotel': hotel,
            'reviews': reviews,
        }
        return render(request, 'main/hotels/hotel_reviews.html', context)
        
    except Hotel.DoesNotExist:
        messages.error(request, "Hôtel non trouvé.")
        return redirect('hotel_list')

def create_review(request, hotel_id):
    """Créer un avis"""
    try:
        hotel = Hotel.objects.get(id=hotel_id)
        # Empêcher les utilisateurs non authentifiés de créer un avis
        if not request.user.is_authenticated:
            messages.warning(request, "Veuillez vous connecter pour publier un avis.")
            return redirect('signin')
        
        if request.method == 'POST':
            form = ReviewForm(request.POST)
            if form.is_valid():
                review = form.save(commit=False)
                review.hotel = hotel
                review.user = request.user
                review.save()
                messages.success(request, f"Votre avis sur {hotel.name} a été publié !")
                return redirect('hotel_reviews', hotel_id=hotel_id)
        else:
            form = ReviewForm()
        
        context = {
            'hotel': hotel,
            'form': form,
        }
        return render(request, 'main/hotels/create_review.html', context)
        
    except Hotel.DoesNotExist:
        messages.error(request, "Hôtel non trouvé.")
        return redirect('hotel_list')

def my_reviews(request):
    """Afficher mes avis"""
    if not request.user.is_authenticated:
        messages.warning(request, "Veuillez vous connecter pour voir vos avis.")
        return redirect('signin')
    
    reviews = Review.objects.filter(user=request.user).select_related('hotel')
    return render(request, 'main/hotels/my_reviews.html', {'reviews': reviews})


def create_review(request, hotel_id):
    """Créer un avis"""
    try:
        hotel = Hotel.objects.get(id=hotel_id)
        # Empêcher les utilisateurs non authentifiés de créer un avis
        if not request.user.is_authenticated:
            messages.warning(request, "Veuillez vous connecter pour publier un avis.")
            return redirect('signin')
        
        if request.method == 'POST':
            # Créer un formulaire basique si ReviewForm n'existe pas
            rating = request.POST.get('rating')
            review_text = request.POST.get('review_text')
            
            if rating and review_text:
                review = Review(
                    hotel=hotel,
                    user=request.user,
                    rating=int(rating),
                    review_text=review_text
                )
                
                # Analyse de sentiment
                sentiment_result = predict_sentiment(review_text)
                review.sentiment_label = sentiment_result['label']
                review.sentiment_score = sentiment_result['probability']
                
                review.save()
                messages.success(request, f"Your review for {hotel.name} has been published!")
                return redirect('hotel_reviews', hotel_id=hotel_id)
            else:
                messages.error(request, "Please fill all fields")
        
        context = {
            'hotel': hotel,
        }
        return render(request, 'main/hotels/create_review.html', context)
        
    except Hotel.DoesNotExist:
        messages.error(request, "Hotel not found.")
        return redirect('hotel_list')