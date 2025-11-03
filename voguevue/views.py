from django.shortcuts import redirect, render, HttpResponse
from datetime import datetime
from .models import Contact, register_table, updatemail, Activity, ChatHistory
from django.contrib import messages
from django.contrib.auth import logout as django_logout, authenticate, login
from django.urls import reverse
from django.contrib.auth.models import User
from django.http import JsonResponse
from .recommendation import get_engine
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import json
import requests
import base64
from io import BytesIO
from PIL import Image
import uuid

# 🆕 Configuration des APIs IA
from django.conf import settings

# Configuration Groq (GRATUIT et RAPIDE)
GROQ_API_KEY = getattr(settings, 'GROQ_API_KEY', '')
GROQ_ENABLED = bool(GROQ_API_KEY)
if GROQ_ENABLED:
    print("✅ Groq API configurée (GRATUIT)")

# Configuration Hugging Face (Gratuit)
HUGGINGFACE_TOKEN = getattr(settings, 'HUGGINGFACE_TOKEN', '')
HUGGINGFACE_ENABLED = bool(HUGGINGFACE_TOKEN)

# 🆕 Initialiser le moteur LightGBM
try:
    recommendation_engine = get_engine()
    ENGINE_LOADED = True
    print("✅ Moteur LightGBM chargé avec succès")
except Exception as e:
    print(f"❌ Erreur lors du chargement du moteur : {e}")
    recommendation_engine = None
    ENGINE_LOADED = False


# ==================== FONCTIONS IA ====================

def generate_activity_image(activity_name, location):
    """
    🎨 Génère une image avec Hugging Face Stable Diffusion
    100% GRATUIT - Pas de limite stricte
    """
    if not HUGGINGFACE_ENABLED:
        return None
    
    API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"}
    
    prompt = f"Beautiful tourist destination in Tunisia: {activity_name} in {location}, high quality photography, vibrant colors, 4k, professional"
    
    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json={
                "inputs": prompt,
                "parameters": {
                    "negative_prompt": "ugly, blurry, low quality, distorted",
                    "num_inference_steps": 30
                }
            },
            timeout=90
        )
        
        if response.status_code == 200:
            # Convertir en base64
            image = Image.open(BytesIO(response.content))
            
            # Redimensionner pour optimiser
            image.thumbnail((800, 600), Image.Resampling.LANCZOS)
            
            buffered = BytesIO()
            image.save(buffered, format="JPEG", quality=85)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            print(f"✅ Image générée pour {activity_name}")
            return f"data:image/jpeg;base64,{img_str}"
        
        elif response.status_code == 503:
            print(f"⏳ Modèle en cours de chargement, réessayer...")
            return "loading"
        
    except Exception as e:
        print(f"❌ Erreur génération image : {e}")
    
    return None


# ==================== VUES PRINCIPALES ====================

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
        messages.success(request, 'Your message has been sent')

    return render(request, 'main/contact.html')


def travels(request):
    """
    🆕 Vue avec système de recommandation LightGBM + Génération d'images IA
    """
    context = {
        'activities': [],
        'weather_info': None,
        'city_searched': None,
        'error': None,
        'engine_loaded': ENGINE_LOADED,
        'huggingface_enabled': HUGGINGFACE_ENABLED,
        'groq_enabled': GROQ_ENABLED
    }

    if request.method == "POST":
        city_name = request.POST.get('city', '').strip()

        if not city_name:
            context['error'] = "Veuillez entrer un nom de ville"
            return render(request, 'main/travels.html', context)

        if not ENGINE_LOADED:
            context['error'] = "Le moteur de recommandation n'est pas disponible"
            return render(request, 'main/travels.html', context)

        try:
            # 🎯 Recommandations LightGBM
            recommendations, weather = recommendation_engine.get_recommendations(
                city_name=city_name,
                top_n=5
            )

            context['weather_info'] = weather
            context['city_searched'] = city_name.title()

            if recommendations:
                # 🎨 Générer des images IA pour les activités
                for activity in recommendations:
                    # Vérifier si l'image existe déjà en DB
                    db_activity = Activity.objects.filter(
                        activity_name=activity['activity_name'],
                        location__icontains=city_name
                    ).first()
                    
                    if db_activity and db_activity.image_url:
                        # Image déjà générée
                        activity['image_url'] = db_activity.image_url
                        activity['ai_generated'] = db_activity.ai_generated
                    elif HUGGINGFACE_ENABLED:
                        # Générer nouvelle image
                        print(f"🎨 Génération image IA pour {activity['activity_name']}...")
                        image_url = generate_activity_image(
                            activity['activity_name'],
                            activity['location']
                        )
                        
                        if image_url and image_url != "loading":
                            activity['image_url'] = image_url
                            activity['ai_generated'] = True
                            
                            # Sauvegarder en DB si l'activité existe
                            if db_activity:
                                db_activity.image_url = image_url
                                db_activity.ai_generated = True
                                db_activity.save()
                        elif image_url == "loading":
                            activity['image_url'] = None
                            activity['image_loading'] = True
                    else:
                        activity['image_url'] = None
                        activity['ai_generated'] = False
                
                context['activities'] = recommendations
                messages.success(
                    request, 
                    f"✅ Top {len(recommendations)} activités trouvées pour {city_name.title()} avec images IA"
                )
            else:
                context['error'] = f"Aucune activité trouvée pour {city_name.title()}. Essayez une autre ville."

        except Exception as e:
            context['error'] = f"Erreur lors de la recherche : {str(e)}"
            print(f"❌ Erreur dans travels() : {e}")

    return render(request, 'main/travels.html', context)


def signin(request):
    if request.method == "POST":
        username = request.POST.get('uname')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            return render(request, 'main/index.html', {"success": "Logged in Successfully"})
        else:
            return render(request, 'authentication/signin.html', {"msg": "Enter the Correct Credentials"})

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
            return render(request, 'authentication/signup.html', {
                "error": "Ce nom d'utilisateur existe déjà. Veuillez en choisir un autre."
            })

        if User.objects.filter(email=em).exists():
            return render(request, 'authentication/signup.html', {
                "error": "Cet email est déjà utilisé."
            })

        usr = User.objects.create_user(un, em, pwd)
        usr.first_name = fname
        usr.last_name = last
        usr.save()

        reg = register_table(user=usr, contact_number=con)
        reg.save()

        messages.success(request, f"{fname}, votre compte a été créé avec succès!")
        return redirect('/signin')

    return render(request, 'authentication/signup.html')


def logout(request):
    django_logout(request)
    messages.info(request, "Logged Out Successfully")
    return redirect("/signin")


def profile(request):
    if request.user.is_authenticated:
        return render(request, 'main/profile.html')
    else:
        return redirect('/signin')


def error_404(request, exception):
    return render(request, 'main/404.html')


def blog(request):
    return render(request, 'main/blog.html')


# ==================== APIS IA ====================

@csrf_exempt
def get_ai_chat(request):
    """
    🤖 Chatbot IA avec Groq (GRATUIT et RAPIDE)
    API 100% GRATUITE - Llama 3.3 70B
    """
    if not GROQ_ENABLED:
        return JsonResponse({
            'reply': "Le chatbot IA n'est pas configuré. Ajoutez GROQ_API_KEY dans settings.py",
            'success': False
        }, status=503)
    
    if request.method == "POST":
        try:
            # Support JSON et FormData
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                user_message = data.get('message', '')
                city = data.get('city', 'Tunisie')
            else:
                user_message = request.POST.get('message', '')
                city = request.POST.get('city', 'Tunisie')
            
            if not user_message:
                return JsonResponse({'error': 'Message requis'}, status=400)
            
            # Prompt optimisé pour le tourisme tunisien
            system_prompt = f"""Tu es un expert en tourisme passionné et chaleureux spécialisé dans le tourisme tunisien.

Contexte : Ville d'intérêt = {city}

Règles importantes :
- Réponds de manière concise (max 150 mots)
- Sois chaleureux et engageant
- Donne des conseils pratiques et locaux
- Utilise 2-3 émojis appropriés maximum
- Si la question porte sur une activité, recommande 2-3 suggestions précises
- Réponds UNIQUEMENT en français
- Concentre-toi sur les aspects touristiques de la Tunisie"""

            # Appel API Groq avec le nouveau modèle
            groq_url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama-3.3-70b-versatile",  # 🆕 Modèle mis à jour
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": 300,
                "temperature": 0.7
            }
            
            response = requests.post(groq_url, headers=headers, json=payload, timeout=30)
            
            # Debug : afficher la réponse complète en cas d'erreur
            if response.status_code != 200:
                error_detail = response.json() if response.content else {}
                print(f"❌ Erreur Groq {response.status_code}: {error_detail}")
                return JsonResponse({
                    'reply': f"Erreur API Groq ({response.status_code}). Vérifiez votre clé API.",
                    'success': False,
                    'error': str(error_detail)
                }, status=500)
            
            response.raise_for_status()
            
            data = response.json()
            ai_reply = data['choices'][0]['message']['content']
            
            # Sauvegarder l'historique
            session_id = request.session.session_key or str(uuid.uuid4())
            ChatHistory.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_id=session_id,
                city=city,
                user_message=user_message,
                ai_response=ai_reply
            )
            
            return JsonResponse({
                'reply': ai_reply,
                'success': True,
                'city': city
            })
            
        except requests.exceptions.HTTPError as e:
            print(f"❌ Erreur Groq HTTP : {e}")
            return JsonResponse({
                'reply': "Désolé, le service IA est temporairement indisponible. Réessayez dans un instant.",
                'success': False,
                'error': str(e)
            }, status=500)
        except Exception as e:
            print(f"❌ Erreur Groq : {e}")
            return JsonResponse({
                'reply': "Désolé, je ne peux pas répondre pour le moment. Réessayez dans quelques instants.",
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

def get_recommendations_api(request):
    """
    🆕 API endpoint pour obtenir des recommandations LightGBM
    Usage: /api/recommendations?city=Bizerte&top_n=5
    """
    if not ENGINE_LOADED:
        return JsonResponse({'error': 'Engine not loaded'}, status=500)

    city_name = request.GET.get('city', '')
    top_n = int(request.GET.get('top_n', 5))
    
    if not city_name:
        return JsonResponse({'error': 'City parameter required'}, status=400)

    try:
        recommendations, weather = recommendation_engine.get_recommendations(
            city_name=city_name,
            top_n=top_n
        )

        return JsonResponse({
            'city': city_name.title(),
            'weather': weather,
            'activities': recommendations,
            'count': len(recommendations)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
    # Ajoutez dans voguevue/views.py après les imports existants
# Ajoutez dans voguevue/views.py après les imports existants

# 🗺️ Configuration pour Itinéraires (utilise Groq au lieu d'Eden AI)
ITINERARY_ENABLED = GROQ_ENABLED  # Utilise la clé Groq existante
if ITINERARY_ENABLED:
    print("✅ Générateur d'itinéraires configuré (Groq)")

# ==================== NOUVELLES FONCTIONS IA ====================

def generate_smart_itinerary(city, days, interests=None, budget=None):
    """
    🗺️ Génère un itinéraire intelligent avec Groq (GRATUIT et ILLIMITÉ)
    Utilise la même clé API que le chatbot
    """
    if not GROQ_ENABLED:
        return None
    
    # Construire le prompt détaillé
    prompt_parts = [
        f"Tu es un expert en tourisme tunisien. Crée un itinéraire ULTRA-DÉTAILLÉ de {days} jour(s) à {city}, Tunisie.",
        "\n📋 STRUCTURE OBLIGATOIRE POUR CHAQUE JOUR:\n"
    ]
    
    for day in range(1, int(days) + 1):
        prompt_parts.append(f"\n{'='*50}")
        prompt_parts.append(f"🗓️ JOUR {day} - [Thème du jour]")
        prompt_parts.append(f"{'='*50}\n")
        prompt_parts.append("🌅 MATIN (8h-12h):")
        prompt_parts.append("   • Activité: [Nom précis]")
        prompt_parts.append("   • Lieu: [Adresse exacte]")
        prompt_parts.append("   • Durée: [Xh]")
        prompt_parts.append("   • Prix: [X TND]")
        prompt_parts.append("   • Conseil: [Astuce pratique]\n")
        
        prompt_parts.append("🌞 APRÈS-MIDI (14h-18h):")
        prompt_parts.append("   • Activité: [Nom précis]")
        prompt_parts.append("   • Lieu: [Adresse exacte]")
        prompt_parts.append("   • Durée: [Xh]")
        prompt_parts.append("   • Prix: [X TND]")
        prompt_parts.append("   • Conseil: [Astuce pratique]\n")
        
        prompt_parts.append("🌙 SOIRÉE (19h-22h):")
        prompt_parts.append("   • Restaurant: [Nom]")
        prompt_parts.append("   • Adresse: [Lieu précis]")
        prompt_parts.append("   • Spécialité: [Plat à essayer]")
        prompt_parts.append("   • Budget: [X TND]")
        prompt_parts.append("   • Ambiance: [Description]\n")
        
        prompt_parts.append("💡 TIPS DU JOUR:")
        prompt_parts.append("   • Transport: [Moyen + Prix]")
        prompt_parts.append("   • Budget total: [X TND]")
        prompt_parts.append("   • À éviter: [Conseil sécurité]")
        prompt_parts.append("   • Bon plan: [Astuce locale]")
    
    if interests:
        prompt_parts.append(f"\n\n🎯 Centres d'intérêt: {interests}")
    
    if budget:
        prompt_parts.append(f"💰 Budget: {budget}")
    
    prompt_parts.append("\n⚠️ IMPORTANT: Utilise UNIQUEMENT des lieux réels et vérifiables à " + city + ", Tunisie.")
    prompt_parts.append("Donne des adresses précises, des prix réalistes en TND.")
    
    prompt = "\n".join(prompt_parts)
    
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": "Tu es un guide touristique expert de la Tunisie avec 20 ans d'expérience. Tu connais tous les lieux, prix et astuces. Réponds UNIQUEMENT en français."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 3000  # Augmenté pour itinéraires longs
        }
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=45
        )
        
        if response.status_code == 200:
            data = response.json()
            itinerary = data['choices'][0]['message']['content']
            
            if itinerary:
                print(f"✅ Itinéraire généré pour {city} ({days} jours) via Groq")
                return itinerary
        else:
            print(f"❌ Erreur Groq: {response.status_code}")
            error_detail = response.json() if response.content else {}
            print(f"Détails: {error_detail}")
            
    except Exception as e:
        print(f"❌ Erreur génération itinéraire: {e}")
    
    return None


# ==================== NOUVELLES VUES ====================

def itinerary_generator(request):
    """
    🆕 Page de génération d'itinéraires intelligents
    Utilise Groq au lieu d'Eden AI (100% gratuit)
    """
    context = {
        'itinerary': None,
        'city': None,
        'days': None,
        'error': None,
        'itinerary_enabled': ITINERARY_ENABLED
    }
    
    if request.method == "POST":
        city = request.POST.get('city', '').strip()
        days = request.POST.get('days', '3')
        interests = request.POST.get('interests', '')
        budget = request.POST.get('budget', '')
        
        if not city:
            context['error'] = "Veuillez entrer une ville"
            return render(request, 'main/itinerary.html', context)
        
        if not ITINERARY_ENABLED:
            context['error'] = "Le générateur d'itinéraires n'est pas configuré"
            return render(request, 'main/itinerary.html', context)
        
        try:
            days_int = int(days)
            if days_int < 1 or days_int > 14:
                context['error'] = "La durée doit être entre 1 et 14 jours"
                return render(request, 'main/itinerary.html', context)
            
            # Générer l'itinéraire avec Groq
            print(f"🚀 Génération itinéraire: {city}, {days_int} jours")
            itinerary = generate_smart_itinerary(
                city=city,
                days=days_int,
                interests=interests,
                budget=budget
            )
            
            if itinerary:
                context['itinerary'] = itinerary
                context['city'] = city.title()
                context['days'] = days
                messages.success(
                    request,
                    f"✅ Itinéraire de {days} jours créé pour {city.title()} avec IA Groq!"
                )
            else:
                context['error'] = "Impossible de générer l'itinéraire. Réessayez dans quelques instants."
                
        except ValueError:
            context['error'] = "Durée invalide. Veuillez entrer un nombre entre 1 et 14."
        except Exception as e:
            context['error'] = f"Erreur: {str(e)}"
            print(f"❌ Erreur itinerary_generator: {e}")
    
    return render(request, 'main/itinerary.html', context)


@csrf_exempt
def get_itinerary_api(request):
    """
    🆕 API endpoint pour générer des itinéraires
    POST /api/itinerary avec JSON: {"city": "Tunis", "days": 3, "interests": "culture"}
    Utilise Groq (gratuit illimité)
    """
    if not ITINERARY_ENABLED:
        return JsonResponse({
            'error': 'Générateur d\'itinéraires non configuré',
            'success': False
        }, status=503)
    
    if request.method == "POST":
        try:
            # Support JSON et FormData
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST
            
            city = data.get('city', '').strip()
            days = int(data.get('days', 3))
            interests = data.get('interests', '')
            budget = data.get('budget', '')
            
            if not city:
                return JsonResponse({'error': 'Ville requise'}, status=400)
            
            if days < 1 or days > 14:
                return JsonResponse({'error': 'Durée entre 1 et 14 jours'}, status=400)
            
            # Générer l'itinéraire avec Groq
            itinerary = generate_smart_itinerary(
                city=city,
                days=days,
                interests=interests,
                budget=budget
            )
            
            if itinerary:
                return JsonResponse({
                    'itinerary': itinerary,
                    'city': city.title(),
                    'days': days,
                    'provider': 'Groq (gratuit)',
                    'success': True
                })
            else:
                return JsonResponse({
                    'error': 'Impossible de générer l\'itinéraire',
                    'success': False
                }, status=500)
                
        except ValueError as e:
            return JsonResponse({
                'error': f'Données invalides: {str(e)}',
                'success': False
            }, status=400)
        except Exception as e:
            print(f"❌ Erreur API itinéraire: {e}")
            return JsonResponse({
                'error': str(e),
                'success': False
            }, status=500)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)