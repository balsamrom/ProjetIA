from django.shortcuts import redirect, render, HttpResponse
from datetime import datetime
from .models import Contact, register_table, updatemail, Activity
from django.contrib import messages
from django.contrib.auth import logout as django_logout, authenticate, login
from django.urls import reverse
from django.contrib.auth.models import User
from django.http import JsonResponse
from .recommendation import HybridRecommendationEngine, get_weather_for_city
import json

# 🆕 Initialiser le moteur de recommandation une seule fois au démarrage
try:
    recommendation_engine = HybridRecommendationEngine()
    ENGINE_LOADED = True
except Exception as e:
    print(f"❌ Erreur lors du chargement du moteur : {e}")
    recommendation_engine = None
    ENGINE_LOADED = False


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
    🆕 Vue améliorée avec système de recommandation hybride
    """
    context = {
        'activities': [],
        'weather_info': None,
        'city_searched': None,
        'error': None,
        'engine_loaded': ENGINE_LOADED
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
            # 1️⃣ Récupérer la météo
            weather = get_weather_for_city(city_name)
            context['weather_info'] = weather
            context['city_searched'] = city_name.title()

            # 2️⃣ Obtenir les recommandations hybrides
            recommendations = recommendation_engine.get_recommendations(
                city_name=city_name,
                weather=weather,
                top_n=20
            )

            if recommendations:
                context['activities'] = recommendations
                messages.success(request, f"✅ {len(recommendations)} activités trouvées pour {city_name.title()}")
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


# 🆕 Vue API pour récupérer les recommandations en JSON (optionnel)
def get_recommendations_api(request):
    """
    API endpoint pour obtenir des recommandations
    Usage: /api/recommendations?city=Paris
    """
    if not ENGINE_LOADED:
        return JsonResponse({'error': 'Engine not loaded'}, status=500)

    city_name = request.GET.get('city', '')
    if not city_name:
        return JsonResponse({'error': 'City parameter required'}, status=400)

    try:
        weather = get_weather_for_city(city_name)
        recommendations = recommendation_engine.get_recommendations(
            city_name=city_name,
            weather=weather,
            top_n=20
        )

        return JsonResponse({
            'city': city_name.title(),
            'weather': weather,
            'activities': recommendations,
            'count': len(recommendations)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)