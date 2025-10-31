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
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect, csrf_exempt

try:
    import openai
except Exception:
    openai = None

# Importez vos modèles et forms
from .models import Contact, register_table, Hotel, Room, Reservation, Review
from .forms import HotelForm, RoomForm, ReservationForm, ReviewForm

# === CLASSE HOTEL REPUTATION PREDICTOR ===
class HotelReputationPredictor:
    def __init__(self):
        print("=== INITIALISATION PRÉDICTEUR RÉPUTATION ===")
        
        # Lister tous les chemins possibles
        possible_paths = [
            'hotel_review_tfidf_logreg.pkl',  # À côté de manage.py
            'hotel_reputation_model.pkl',     # Autre nom possible
            os.path.join(settings.BASE_DIR, 'hotel_review_tfidf_logreg.pkl'),
            os.path.join(settings.BASE_DIR, 'hotel_reputation_model.pkl'),
            os.path.join(settings.BASE_DIR, 'voguevue', 'hotel_review_tfidf_logreg.pkl'),
            os.path.join(settings.BASE_DIR, 'voguevue', 'hotel_reputation_model.pkl'),
        ]
        
        print("🔍 Recherche du modèle...")
        for path in possible_paths:
            exists = "✅ EXISTE" if os.path.exists(path) else "❌ N'EXISTE PAS"
            print(f"  {exists}: {path}")
        
        self.model = None
        self.vectorizer = None
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    print(f"📂 Tentative de chargement: {path}")
                    with open(path, 'rb') as f:
                        model_data = pickle.load(f)
                    
                    print(f"📊 Type des données chargées: {type(model_data)}")
                    
                    # Gestion différente selon le type de données
                    if isinstance(model_data, dict):
                        print(f"📋 Clés disponibles: {list(model_data.keys())}")
                        self.model = model_data.get('model')
                        self.vectorizer = model_data.get('vectorizer')
                        self.accuracy = model_data.get('accuracy', 'Inconnue')
                    else:
                        # Si c'est directement le modèle
                        print("ℹ️  Modèle chargé directement")
                        self.model = model_data
                        self.vectorizer = None
                        self.accuracy = 'Inconnue'
                    
                    # Vérification que le modèle est valide
                    if self.model is not None and hasattr(self.model, 'predict'):
                        print("✅ Modèle valide avec méthode predict")
                        if self.accuracy != 'Inconnue':
                            print(f"🎯 Précision du modèle: {self.accuracy:.2%}")
                        break
                    else:
                        print("❌ Modèle invalide ou sans méthode predict")
                        self.model = None
                        
                except Exception as e:
                    print(f"❌ Erreur de chargement: {e}")
                    continue
        
        if self.model is None:
            print("🔄 Activation du mode démo intelligent...")
            self.model = 'demo'
        else:
            print("🎉 Modèle de réputation PRÊT à l'utilisation!")

    def predict_hotel_reputation(self, hotel_reviews):
        """Prédit la réputation d'un hôtel"""
        if not hotel_reviews:
            return self._empty_result()
        
        clean_reviews = [str(review).strip() for review in hotel_reviews if review and str(review).strip()]
        
        if not clean_reviews:
            return self._empty_result()
        
        # Mode réel avec modèle ML
        if self.model != 'demo':
            try:
                return self._real_ml_predict(clean_reviews)
            except Exception as e:
                print(f"❌ Erreur prédiction ML: {e}")
                return self._smart_demo_predict(clean_reviews)
        
        # Mode démo intelligent
        return self._smart_demo_predict(clean_reviews)
    
    def _real_ml_predict(self, reviews):
        """Prédiction avec le vrai modèle ML"""
        # Vectorisation
        if self.vectorizer:
            reviews_vec = self.vectorizer.transform(reviews)
        else:
            # Si pas de vectorizer, en créer un nouveau
            vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
            reviews_vec = vectorizer.fit_transform(reviews)
        
        # Prédictions
        individual_predictions = self.model.predict(reviews_vec)
        
        # Probabilités pour la confiance
        try:
            probabilities = self.model.predict_proba(reviews_vec)
            confidence_scores = [np.max(prob) for prob in probabilities]
            overall_confidence = np.mean(confidence_scores)
        except:
            confidence_scores = [0.8] * len(individual_predictions)
            overall_confidence = 0.8
        
        # Réputation globale
        pred_series = pd.Series(individual_predictions)
        reputation_counts = pred_series.value_counts()
        overall_reputation = reputation_counts.index[0]
        
        # Détail par catégorie
        breakdown = {}
        total_reviews = len(individual_predictions)
        reputation_labels = ['Mauvais', 'Moyen', 'Bon', 'Très bon', 'Excellent']
        
        for category in reputation_labels:
            count = (pred_series == category).sum()
            breakdown[category] = {
                'count': count,
                'percentage': round((count / total_reviews) * 100, 1) if total_reviews > 0 else 0
            }
        
        return {
            'reputation': overall_reputation,
            'confidence': round(overall_confidence, 3),
            'total_reviews': total_reviews,
            'prediction_breakdown': breakdown,
            'individual_predictions': individual_predictions.tolist(),
            'mode': 'ML'
        }
    
    def _smart_demo_predict(self, reviews):
        """Prédiction démo intelligente basée sur l'analyse de texte"""
        # Mots-clés pour l'analyse de sentiment
        positive_words = ['excellent', 'parfait', 'superbe', 'magnifique', 'exceptionnel', 
                         'agréable', 'confortable', 'propre', 'spacieux', 'accueillant',
                         'génial', 'merveilleux', 'fantastique', 'incroyable', 'parfaitement',
                         'idéal', 'exquis', 'luxueux', 'raffiné', 'élégant']
        
        negative_words = ['mauvais', 'terrible', 'horrible', 'déçu', 'décevant', 'sale',
                         'bruyant', 'petit', 'vieux', 'cher', 'nul', 'minable',
                         'dégoutant', 'infect', 'horreur', 'catastrophe', 'désastre',
                         'insupportable', 'inacceptable', 'médiocre']
        
        positive_count = 0
        negative_count = 0
        total_length = 0
        
        for review in reviews:
            review_lower = review.lower()
            total_length += len(review)
            
            # Compter les mots positifs/négatifs
            positive_count += sum(1 for word in positive_words if word in review_lower)
            negative_count += sum(1 for word in negative_words if word in review_lower)
        
        # Calcul du score
        total_sentiment = positive_count - negative_count
        avg_length = total_length / len(reviews)
        
        # Déterminer la réputation
        if total_sentiment > 8:
            reputation = "Excellent"
            confidence = min(0.95, 0.75 + (total_sentiment * 0.02))
        elif total_sentiment > 4:
            reputation = "Très bon"
            confidence = 0.75 + (total_sentiment * 0.03)
        elif total_sentiment >= 0:
            reputation = "Bon"
            confidence = 0.65 + (total_sentiment * 0.02)
        elif total_sentiment > -5:
            reputation = "Moyen"
            confidence = 0.55 - (total_sentiment * 0.02)
        else:
            reputation = "Mauvais"
            confidence = max(0.3, 0.5 - (total_sentiment * 0.03))
        
        # Générer une répartition réaliste
        breakdown = self._generate_realistic_breakdown(reputation, len(reviews))
        
        return {
            'reputation': reputation,
            'confidence': round(confidence, 3),
            'total_reviews': len(reviews),
            'prediction_breakdown': breakdown,
            'individual_predictions': [reputation] * len(reviews),
            'mode': 'Démo',
            'analysis_notes': f"Analysé {len(reviews)} avis - {positive_count}👍 / {negative_count}👎"
        }
    
    def _generate_realistic_breakdown(self, main_reputation, total_reviews):
        """Génère une répartition réaliste"""
        if main_reputation == "Excellent":
            return {
                'Excellent': {'count': max(1, int(total_reviews * 0.7)), 'percentage': 70},
                'Très bon': {'count': max(0, int(total_reviews * 0.2)), 'percentage': 20},
                'Bon': {'count': max(0, int(total_reviews * 0.1)), 'percentage': 10},
                'Moyen': {'count': 0, 'percentage': 0},
                'Mauvais': {'count': 0, 'percentage': 0}
            }
        elif main_reputation == "Très bon":
            return {
                'Excellent': {'count': max(0, int(total_reviews * 0.3)), 'percentage': 30},
                'Très bon': {'count': max(1, int(total_reviews * 0.5)), 'percentage': 50},
                'Bon': {'count': max(0, int(total_reviews * 0.2)), 'percentage': 20},
                'Moyen': {'count': 0, 'percentage': 0},
                'Mauvais': {'count': 0, 'percentage': 0}
            }
        elif main_reputation == "Bon":
            return {
                'Excellent': {'count': max(0, int(total_reviews * 0.1)), 'percentage': 10},
                'Très bon': {'count': max(0, int(total_reviews * 0.3)), 'percentage': 30},
                'Bon': {'count': max(1, int(total_reviews * 0.4)), 'percentage': 40},
                'Moyen': {'count': max(0, int(total_reviews * 0.2)), 'percentage': 20},
                'Mauvais': {'count': 0, 'percentage': 0}
            }
        elif main_reputation == "Moyen":
            return {
                'Excellent': {'count': 0, 'percentage': 0},
                'Très bon': {'count': max(0, int(total_reviews * 0.1)), 'percentage': 10},
                'Bon': {'count': max(0, int(total_reviews * 0.3)), 'percentage': 30},
                'Moyen': {'count': max(1, int(total_reviews * 0.5)), 'percentage': 50},
                'Mauvais': {'count': max(0, int(total_reviews * 0.1)), 'percentage': 10}
            }
        else:  # Mauvais
            return {
                'Excellent': {'count': 0, 'percentage': 0},
                'Très bon': {'count': 0, 'percentage': 0},
                'Bon': {'count': max(0, int(total_reviews * 0.1)), 'percentage': 10},
                'Moyen': {'count': max(0, int(total_reviews * 0.3)), 'percentage': 30},
                'Mauvais': {'count': max(1, int(total_reviews * 0.6)), 'percentage': 60}
            }
    
    def _empty_result(self):
        return {
            'reputation': 'Non évalué',
            'confidence': 0,
            'total_reviews': 0,
            'prediction_breakdown': {},
            'individual_predictions': []
        }

# === INITIALISATION DU PRÉDICTEUR ===
print("🔄 Initialisation du système de réputation...")
reputation_predictor = HotelReputationPredictor()
PREDICTOR_AVAILABLE = True  # Toujours disponible (ML ou démo)

# === CONFIGURATION ML SENTIMENT ===
try:
    sentiment_model_paths = [
        os.path.join(settings.BASE_DIR, 'hotel_review_tfidf_logreg.pkl'),
        os.path.join(settings.BASE_DIR, 'voguevue', 'ml_models', 'hotel_review_tfidf_logreg.pkl'),
    ]
    
    sentiment_model = None
    for path in sentiment_model_paths:
        if os.path.exists(path):
            sentiment_model = joblib.load(path)
            print(f"✅ Modèle sentiment chargé: {path}")
            break
    
    if sentiment_model is None:
        print("ℹ️  Mode démo pour l'analyse de sentiment")
        
except Exception as e:
    print(f"❌ Erreur chargement modèle sentiment: {e}")
    sentiment_model = None

def predict_sentiment(text):
    """Analyse de sentiment avec fallback"""
    if sentiment_model is None:
        # Mode démo
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'perfect']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'dirty', 'broken']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return {"label": "Good", "probability": 80}
        elif negative_count > positive_count:
            return {"label": "Bad", "probability": 20}
        else:
            return {"label": "Neutral", "probability": 50}
    
    try:
        # Nettoyage du texte
        text = text.lower()
        text = re.sub(r"http\S+", "", text)
        text = re.sub(r"[^a-zA-Z\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        
        # Prédiction
        pred = sentiment_model.predict([text])[0]
        proba = sentiment_model.predict_proba([text])[0][1]
        return {
            "label": "Good" if pred == 1 else "Bad",
            "probability": round(proba * 100, 2)
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
    budget_str = request.GET.get('budget')
    
    try:
        budget = float(budget_str) if budget_str else None
    except ValueError:
        budget = None

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
    if PREDICTOR_AVAILABLE and reviews:
        review_texts = [review.review_text for review in reviews if review.review_text]
        if review_texts:
            reputation_data = reputation_predictor.predict_hotel_reputation(review_texts)
    
    eco_score = compute_eco_score(hotel)
    
    context = {
        'hotel': hotel,
        'reviews': reviews,
        'reputation_data': reputation_data,
        'eco_score': eco_score,
        'model_available': PREDICTOR_AVAILABLE,
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

def reputation_analysis(request):
    """Analyse de réputation de tous les hôtels"""
    hotels = Hotel.objects.all().prefetch_related('reviews')
    analysis_results = []
    
    if request.method == 'POST':
        print("🔄 Lancement de l'analyse de réputation...")
        # Lancer l'analyse
        for hotel in hotels:
            reviews = hotel.reviews.all()
            review_texts = [review.review_text for review in reviews if review.review_text]
            
            if review_texts:
                try:
                    result = reputation_predictor.predict_hotel_reputation(review_texts)
                    analysis_results.append({
                        'hotel': hotel,
                        'result': result,
                        'review_count': len(review_texts)
                    })
                    print(f"✅ Analysé {hotel.name}: {result['reputation']}")
                except Exception as e:
                    print(f"❌ Erreur pour {hotel.name}: {e}")
                    analysis_results.append({
                        'hotel': hotel,
                        'result': {'reputation': 'Erreur', 'mode': 'Erreur'},
                        'review_count': len(review_texts)
                    })
            else:
                analysis_results.append({
                    'hotel': hotel,
                    'result': None,
                    'review_count': 0
                })
        
        messages.success(request, f'Analyse terminée pour {len(analysis_results)} hôtels')
    
    context = {
        'hotels': hotels,
        'analysis_results': analysis_results,
        'model_available': PREDICTOR_AVAILABLE,
    }
    return render(request, 'main/hotels/reputation_analysis.html', context)
def predict_hotel_reputation_api(request, pk):
    """API pour prédire la réputation d'un hôtel"""
    hotel = get_object_or_404(Hotel, pk=pk)
    reviews = hotel.reviews.all()
    review_texts = [review.review_text for review in reviews if review.review_text]
    
    try:
        result = reputation_predictor.predict_hotel_reputation(review_texts)
        return JsonResponse({
            'success': True,
            'hotel_id': hotel.id,
            'hotel_name': hotel.name,
            'reputation': result['reputation'],
            'confidence': result['confidence'],
            'total_reviews': result['total_reviews'],
            'breakdown': result['prediction_breakdown'],
            'mode': result.get('mode', 'ML')
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def api_generate_hotel_description(request):
    """Génère une description d'hôtel avec OpenAI"""
    try:
        if request.method != 'POST':
            return JsonResponse({
                'status': 'error', 
                'message': 'Méthode POST requise'
            }, status=405)

        # Charger les données JSON
        data = json.loads(request.body)
        hotel_name = data.get('hotel_name', '').strip()
        city = data.get('city', '').strip()
        features = data.get('features', [])
        
        # Validation
        if not hotel_name:
            return JsonResponse({
                'status': 'error',
                'message': 'Le nom de l\'hôtel est requis'
            }, status=400)
        
        if not city:
            return JsonResponse({
                'status': 'error', 
                'message': 'La ville est requise'
            }, status=400)

        # Préparer les caractéristiques
        features_text = ", ".join(features) if features else "confortable et accueillant"
        
        # Prompt optimisé
        prompt = f"""
        Tu es un expert en marketing hôtelier. Crée une description attractive et unique en français pour l'hôtel suivant :

        NOM: {hotel_name}
        VILLE: {city}
        CARACTÉRISTIQUES: {features_text}

        La description doit :
        - Faire 80-120 mots
        - Être engageante et professionnelle
        - Mettre en valeur l'emplacement et les services
        - Utiliser un langage élégant et accueillant
        - Donner envie de réserver
        - Inclure une touche d'originalité
        """

        # Appel OpenAI
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": "Tu es un copywriter expert en hôtellerie de luxe. Tu crées des descriptions engageantes qui donnent envie de voyager."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            max_tokens=300,
            temperature=0.8,
            top_p=0.9
        )
        
        description = response.choices[0].message.content.strip()

        return JsonResponse({
            'status': 'success',
            'hotel_name': hotel_name,
            'city': city,
            'features': features,
            'generated_description': description,
            'word_count': len(description.split()),
            'model_used': 'gpt-3.5-turbo'
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Données JSON invalides'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erreur: {str(e)}'
        }, status=500)
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