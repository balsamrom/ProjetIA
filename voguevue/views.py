import email
from django.shortcuts import redirect, render , HttpResponse
from datetime import datetime
from .models import Contact , register_table , updatemail, Hotel, Room, Reservation
from .forms import HotelForm, RoomForm, ReservationForm
from .hotels.ai import recommend_hotels, compute_eco_score
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import logout as django_logout

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
                return render(request , 'main/index.html' , {"success" : " Logged in Successfully "})
                

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

        reg = register_table(user=usr, contact_number=con)
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


# Hotels CRUD
def hotel_list(request):
    hotels = Hotel.objects.order_by('-created_at')
    # Simple filters
    city = request.GET.get('city') or None
    budget_str = request.GET.get('budget')
    try:
        budget = float(budget_str) if budget_str else None
    except ValueError:
        budget = None

    recommended = recommend_hotels(hotels, city=city, budget=budget, top_k=6)
    # compute eco-score per hotel and attach attribute for templates
    for h in hotels:
        try:
            h.eco_score = compute_eco_score(h)
        except Exception:
            h.eco_score = 50
    for h in recommended:
        if not hasattr(h, 'eco_score'):
            try:
                h.eco_score = compute_eco_score(h)
            except Exception:
                h.eco_score = 50
    return render(request, 'main/hotels/hotel_list.html', {
        'hotels': hotels,
        'recommended': recommended,
        'q_city': city or '',
        'q_budget': budget_str or '',
    })


def hotel_detail(request, pk):
    try:
        hotel = Hotel.objects.get(pk=pk)
    except Hotel.DoesNotExist:
        return redirect('hotel_list')
    eco_score = compute_eco_score(hotel)
    return render(request, 'main/hotels/hotel_detail.html', {'hotel': hotel, 'eco_score': eco_score})


def hotel_create(request):
    if request.method == 'POST':
        form = HotelForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Hotel créé avec succès')
            return redirect('hotel_list')
    else:
        form = HotelForm()
    return render(request, 'main/hotels/hotel_form.html', {'form': form, 'mode': 'create'})


def hotel_update(request, pk):
    try:
        hotel = Hotel.objects.get(pk=pk)
    except Hotel.DoesNotExist:
        return redirect('hotel_list')
    if request.method == 'POST':
        form = HotelForm(request.POST, instance=hotel)
        if form.is_valid():
            form.save()
            messages.success(request, 'Hotel modifié avec succès')
            return redirect('hotel_detail', pk=pk)
    else:
        form = HotelForm(instance=hotel)
    return render(request, 'main/hotels/hotel_form.html', {'form': form, 'mode': 'update', 'hotel': hotel})


def hotel_delete(request, pk):
    try:
        hotel = Hotel.objects.get(pk=pk)
    except Hotel.DoesNotExist:
        return redirect('hotel_list')
    if request.method == 'POST':
        hotel.delete()
        messages.success(request, 'Hotel supprimé')
        return redirect('hotel_list')
    return render(request, 'main/hotels/hotel_confirm_delete.html', {'hotel': hotel})


# Rooms and Reservations
def room_list(request, hotel_id=None):
    qs = Room.objects.select_related('hotel').order_by('hotel__name', 'name')
    if hotel_id:
        qs = qs.filter(hotel_id=hotel_id)
    return render(request, 'main/hotels/room_list.html', {'rooms': qs, 'hotel_id': hotel_id})


def room_create(request):
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Room created')
            return redirect('room_list')
    else:
        form = RoomForm()
    return render(request, 'main/hotels/room_form.html', {'form': form})


def reservation_create(request, room_id=None):
    initial = {}
    if room_id:
        initial['room'] = room_id
    if request.method == 'POST':
        form = ReservationForm(request.POST, initial=initial)
        if form.is_valid():
            form.save()
            messages.success(request, 'Reservation created')
            return redirect('hotel_list')
    else:
        form = ReservationForm(initial=initial)
    return render(request, 'main/hotels/reservation_form.html', {'form': form})


def reserve_cheapest(request, hotel_id: int):
    # find cheapest available room for the hotel
    try:
        hotel = Hotel.objects.get(pk=hotel_id)
    except Hotel.DoesNotExist:
        return redirect('hotel_list')
    room = Room.objects.filter(hotel=hotel, is_available=True).order_by('price_per_night').first()
    if not room:
        messages.error(request, 'No available rooms for this hotel.')
        return redirect('hotel_detail', pk=hotel_id)
    return redirect('reservation_create_for_room', room_id=room.id)