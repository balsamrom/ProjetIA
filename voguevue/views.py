import email
from django.shortcuts import redirect, render , HttpResponse
from datetime import datetime
from .models import Contact , register_table , updatemail, Activity, Reservation
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import logout as django_logout
import json
import urllib.request
import urllib.parse
import urllib.error
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from django.shortcuts import get_object_or_404


# Create your views here.
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
        
    return render(request , 'main/contact.html')
    
def travels(request):
    return render(request, 'main/travels.html') 


 

def signin(request):

        if request.method == "POST":
            username = request.POST.get('uname')
            password = request.POST.get('password')

        # check if the user entered the correct credentials
            user = authenticate(username=username , password=password) 

            if user is not None:
            # A backend authenticated the credentials
                login(request, user)
                # Ensure profile exists and fetch weather for user's city if available
                weather_info = None
                profile = register_table.objects.filter(user=user).first()
                if profile is None:
                    profile = register_table.objects.create(user=user, contact_number=0, city="")
                user_city = (profile.city if profile and profile.city else '').strip()
                if user_city:
                    weather_info = _fetch_weather_for_city(user_city)

                return render(request , 'main/index.html' , {"success" : " Logged in Successfully ", "weather": weather_info})
                

            else:
            # No backend authenticated the credentials
                return render(request, 'authentication/signin.html' , {"msg" : " Enter the Correct Credentials "})


        return render(request , 'authentication/signin.html')

def signup(request):
    if request.method == 'POST':
        fname = request.POST.get("firstname") 
        last = request.POST.get("lastname")
        un = request.POST.get("uname")
        pwd = request.POST.get("password")
        em = request.POST.get("email")
        con = request.POST.get("contact_number")
        city = request.POST.get("city") or ""

        # Vérifier si le username existe déjà
        if User.objects.filter(username=un).exists():
            return render(request, 'authentication/signup.html', {
                "error": "Ce nom d'utilisateur existe déjà. Veuillez en choisir un autre."
            })
        
        # Vérifier si l'email existe déjà
        if User.objects.filter(email=em).exists():
            return render(request, 'authentication/signup.html', {
                "error": "Cet email est déjà utilisé."
            })

        # Créer l'utilisateur
        usr = User.objects.create_user(un, em, pwd)
        usr.first_name = fname
        usr.last_name = last
        usr.save()

        try:
            contact_value = int(con) if (con and str(con).isdigit()) else 0
        except Exception:
            contact_value = 0

        # Upsert profile
        reg = register_table.objects.filter(user=usr).first()
        if reg is None:
            reg = register_table(user=usr, contact_number=contact_value, city=city)
        else:
            reg.contact_number = contact_value
            reg.city = city
        reg.save()

        messages.success(request, f"{fname}, votre compte a été créé avec succès!")
        return redirect('/signin')

    return render(request, 'authentication/signup.html')
def logout(request):
    django_logout(request)
    return redirect("/signin" , {"logsign" : " Logged Out Successfully"})

def profile(request):
    # check if  user is authenticated

    if request.user.is_authenticated:
        return render(request , 'main/profile.html')
    else:
        return redirect('/signin')

def error_404(request , exception):
    return render(request , 'main/404.html')

def blog(request):
    return render(request,'main/blog.html')


# --------------------- Activities & Reservations (User side) ---------------------

def activities_list(request):
    activities = Activity.objects.filter(is_available=True).order_by('name')
    return render(request, 'main/activities_list.html', {"activities": activities})


@login_required
def reserve_activity(request, activity_id):
    activity = get_object_or_404(Activity, pk=activity_id, is_available=True)

    if request.method == 'POST':
        date_str = request.POST.get('date')  # expects ISO datetime-local or date
        if not date_str:
            messages.error(request, "Veuillez sélectionner une date.")
            return render(request, 'main/reserve_activity.html', {"activity": activity})

        try:
            # Support both date and datetime-local inputs
            if 'T' in date_str:
                scheduled_at = timezone.make_aware(timezone.datetime.fromisoformat(date_str))
            else:
                scheduled_at = timezone.make_aware(timezone.datetime.fromisoformat(date_str + 'T09:00:00'))
        except Exception:
            messages.error(request, "Format de date invalide.")
            return render(request, 'main/reserve_activity.html', {"activity": activity})

        if scheduled_at < timezone.now():
            messages.error(request, "La date doit être dans le futur.")
            return render(request, 'main/reserve_activity.html', {"activity": activity})

        Reservation.objects.create(
            activity=activity,
            user=request.user,
            date=scheduled_at,
            status='pending'
        )
        messages.success(request, "Réservation créée avec succès. En attente de validation.")
        return redirect('my_reservations')

    return render(request, 'main/reserve_activity.html', {"activity": activity})


@login_required
def my_reservations(request):
    reservations = Reservation.objects.filter(user=request.user).select_related('activity')
    return render(request, 'main/my_reservations.html', {"reservations": reservations})


# --------------------- Weather Page ---------------------
from django.contrib.auth.decorators import login_required

@login_required
def weather(request):
    weather_info = None
    profile = register_table.objects.filter(user=request.user).first()
    if profile is None:
        profile = register_table.objects.create(user=request.user, contact_number=0, city="")

    # Update city if posted
    if request.method == 'POST':
        new_city = (request.POST.get('city') or '').strip()
        profile.city = new_city
        profile.save(update_fields=['city'])

    user_city = (profile.city or '').strip()
    if user_city:
        weather_info = _fetch_weather_for_city(user_city)

    return render(request, 'main/weather.html', {"weather": weather_info, "city": user_city})


# --------------------- Helpers ---------------------
def _fetch_weather_for_city(city: str):
    # Try API Ninjas weather by city name
    try:
        api_key = "fBgrAqgdm7qdNqzztAtcEw==ot2fLHnh3p2n0xPF"
        url = f"https://api.api-ninjas.com/v1/weather?city={urllib.parse.quote(city)}"
        req = urllib.request.Request(url)
        req.add_header('X-Api-Key', api_key)
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if isinstance(data, dict) and 'temp' in data:
                return {
                    'city': city,
                    'temp': data.get('temp'),
                    'humidity': data.get('humidity'),
                    'wind_speed': data.get('wind_speed')
                }
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError):
        pass

    # Fallback: geocode with API Ninjas, then query Open-Meteo by coordinates (no API key needed)
    try:
        geo_url = f"https://api.api-ninjas.com/v1/geocoding?city={urllib.parse.quote(city)}"
        geo_req = urllib.request.Request(geo_url)
        geo_req.add_header('X-Api-Key', api_key)
        with urllib.request.urlopen(geo_req, timeout=6) as gresp:
            gdata = json.loads(gresp.read().decode('utf-8'))
            if isinstance(gdata, list) and len(gdata) > 0:
                lat = gdata[0].get('latitude')
                lon = gdata[0].get('longitude')
                if lat is not None and lon is not None:
                    om_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
                    with urllib.request.urlopen(om_url, timeout=6) as wresp:
                        wdata = json.loads(wresp.read().decode('utf-8'))
                        current = wdata.get('current_weather') or {}
                        if current:
                            return {
                                'city': city,
                                'temp': current.get('temperature'),
                                'humidity': None,  # Not provided by open-meteo current_weather
                                'wind_speed': current.get('windspeed')
                            }
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError):
        pass

    return None