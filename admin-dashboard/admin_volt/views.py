from django.shortcuts import render, redirect
from admin_volt.forms import RegistrationForm, LoginForm, UserPasswordResetForm, UserPasswordChangeForm, UserSetPasswordForm
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordChangeView, PasswordResetConfirmView
from django.contrib.auth import logout
from django.urls import reverse, reverse_lazy

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from voguevue.models import Hotel, Room, Reservation, Review
from voguevue.forms import HotelForm, RoomForm, ReservationForm
from voguevue.events.models import Event, TicketBooking, EventReview
from voguevue.events.forms import EventForm

# Index
def index(request):
  return render(request, 'pages/index.html')

# Dashboard
def dashboard(request):
  context = {
    'segment': 'dashboard'
  }
  return render(request, 'pages/dashboard/dashboard.html', context)

# Pages
def transaction(request):
  context = {
    'segment': 'transactions'
  }
  return render(request, 'pages/transactions.html', context)

@login_required(login_url=reverse_lazy('login'))
def settings(request):
  context = {
    'segment': 'settings'
  }
  return render(request, 'pages/settings.html', context)

# Tables
def bs_tables(request):
  context = {
    'parent': 'tables',
    'segment': 'bs_tables',
  }
  return render(request, 'pages/tables/bootstrap-tables.html', context)

# Components
def buttons(request):
  context = {
    'parent': 'components',
    'segment': 'buttons',
  }
  return render(request, 'pages/components/buttons.html', context)

def notifications(request):
  context = {
    'parent': 'components',
    'segment': 'notifications',
  }
  return render(request, 'pages/components/notifications.html', context)

def forms(request):
  context = {
    'parent': 'components',
    'segment': 'forms',
  }
  return render(request, 'pages/components/forms.html', context)

def modals(request):
  context = {
    'parent': 'components',
    'segment': 'modals',
  }
  return render(request, 'pages/components/modals.html', context)

def typography(request):
  context = {
    'parent': 'components',
    'segment': 'typography',
  }
  return render(request, 'pages/components/typography.html', context)


# Authentication
def register_view(request):
  if request.method == 'POST':
    form = RegistrationForm(request.POST)
    if form.is_valid():
      print("Account created successfully!")
      form.save()
      return redirect('login')
    else:
      print("Registration failed!")
  else:
    form = RegistrationForm()
  
  context = { 'form': form }
  return render(request, 'accounts/sign-up.html', context)

class UserLoginView(LoginView):
  form_class = LoginForm
  template_name = 'accounts/sign-in.html'

class UserPasswordChangeView(PasswordChangeView):
  template_name = 'accounts/password-change.html'
  form_class = UserPasswordChangeForm

class UserPasswordResetView(PasswordResetView):
  template_name = 'accounts/forgot-password.html'
  form_class = UserPasswordResetForm

class UserPasswrodResetConfirmView(PasswordResetConfirmView):
  template_name = 'accounts/reset-password.html'
  form_class = UserSetPasswordForm

def logout_view(request):
  logout(request)
  return redirect('login')

def lock(request):
  return render(request, 'accounts/lock.html')

# Errors
def error_404(request):
  return render(request, 'pages/examples/404.html')

def error_500(request):
  return render(request, 'pages/examples/500.html')

# Extra
def upgrade_to_pro(request):
  return render(request, 'pages/upgrade-to-pro.html')



# Hotels CRUD (Volt)
@login_required(login_url=reverse_lazy('login'))
def hotel_list_volt(request):
  qs = Hotel.objects.order_by('-created_at')
  context = {
    'segment': 'hotels',
    'hotels': qs,
  }
  return render(request, 'pages/hotels/list.html', context)

@login_required(login_url=reverse_lazy('login'))
def hotel_create_volt(request):
  if request.method == 'POST':
    form = HotelForm(request.POST, request.FILES)
    if form.is_valid():
      hotel = form.save()
      messages.success(request, 'Hôtel créé avec succès')
      return redirect('volt_hotel_detail', pk=hotel.pk)
  else:
    form = HotelForm()
  context = {
    'segment': 'hotels',
    'form': form,
    'mode': 'create',
  }
  return render(request, 'pages/hotels/form.html', context)

@login_required(login_url=reverse_lazy('login'))
def hotel_detail_volt(request, pk:int):
  try:
    hotel = Hotel.objects.get(pk=pk)
  except Hotel.DoesNotExist:
    messages.error(request, 'Hôtel introuvable')
    return redirect('volt_hotel_list')
  context = {
    'segment': 'hotels',
    'hotel': hotel,
  }
  return render(request, 'pages/hotels/detail.html', context)

@login_required(login_url=reverse_lazy('login'))
def hotel_update_volt(request, pk:int):
  try:
    hotel = Hotel.objects.get(pk=pk)
  except Hotel.DoesNotExist:
    messages.error(request, 'Hôtel introuvable')
    return redirect('volt_hotel_list')
  if request.method == 'POST':
    form = HotelForm(request.POST, request.FILES, instance=hotel)
    if form.is_valid():
      form.save()
      messages.success(request, 'Hôtel modifié avec succès')
      return redirect('volt_hotel_detail', pk=pk)
  else:
    form = HotelForm(instance=hotel)
  context = {
    'segment': 'hotels',
    'form': form,
    'mode': 'update',
    'hotel': hotel,
  }
  return render(request, 'pages/hotels/form.html', context)

@login_required(login_url=reverse_lazy('login'))
def hotel_delete_volt(request, pk:int):
  try:
    hotel = Hotel.objects.get(pk=pk)
  except Hotel.DoesNotExist:
    messages.error(request, 'Hôtel introuvable')
    return redirect('volt_hotel_list')
  if request.method == 'POST':
    hotel.delete()
    messages.success(request, 'Hôtel supprimé')
    return redirect('volt_hotel_list')
  context = {
    'segment': 'hotels',
    'hotel': hotel,
  }
  return render(request, 'pages/hotels/confirm_delete.html', context)


# Rooms CRUD (Volt)
@login_required(login_url=reverse_lazy('login'))
def room_list_volt(request):
  qs = Room.objects.select_related('hotel').order_by('hotel__name', 'name')
  context = {
    'segment': 'rooms',
    'rooms': qs,
  }
  return render(request, 'pages/rooms/list.html', context)

@login_required(login_url=reverse_lazy('login'))
def room_create_volt(request):
  if request.method == 'POST':
    form = RoomForm(request.POST)
    if form.is_valid():
      room = form.save()
      messages.success(request, 'Chambre créée avec succès')
      return redirect('volt_room_list')
  else:
    form = RoomForm()
  return render(request, 'pages/rooms/form.html', {'segment': 'rooms', 'form': form, 'mode': 'create'})

@login_required(login_url=reverse_lazy('login'))
def room_update_volt(request, pk:int):
  try:
    room = Room.objects.get(pk=pk)
  except Room.DoesNotExist:
    messages.error(request, 'Chambre introuvable')
    return redirect('volt_room_list')
  if request.method == 'POST':
    form = RoomForm(request.POST, instance=room)
    if form.is_valid():
      form.save()
      messages.success(request, 'Chambre modifiée avec succès')
      return redirect('volt_room_list')
  else:
    form = RoomForm(instance=room)
  return render(request, 'pages/rooms/form.html', {'segment': 'rooms', 'form': form, 'mode': 'update', 'room': room})

@login_required(login_url=reverse_lazy('login'))
def room_delete_volt(request, pk:int):
  try:
    room = Room.objects.get(pk=pk)
  except Room.DoesNotExist:
    messages.error(request, 'Chambre introuvable')
    return redirect('volt_room_list')
  if request.method == 'POST':
    room.delete()
    messages.success(request, 'Chambre supprimée')
    return redirect('volt_room_list')
  return render(request, 'pages/rooms/confirm_delete.html', {'segment': 'rooms', 'room': room})


# Reservations CRUD (Volt)
@login_required(login_url=reverse_lazy('login'))
def reservation_list_volt(request):
  qs = Reservation.objects.select_related('room__hotel').order_by('-check_in')
  return render(request, 'pages/reservations/list.html', {'segment': 'reservations', 'reservations': qs})

@login_required(login_url=reverse_lazy('login'))
def reservation_create_volt(request):
  if request.method == 'POST':
    form = ReservationForm(request.POST)
    if form.is_valid():
      form.save()
      messages.success(request, 'Réservation créée avec succès')
      return redirect('volt_reservation_list')
  else:
    form = ReservationForm()
  return render(request, 'pages/reservations/form.html', {'segment': 'reservations', 'form': form, 'mode': 'create'})

@login_required(login_url=reverse_lazy('login'))
def reservation_update_volt(request, pk:int):
  try:
    reservation = Reservation.objects.get(pk=pk)
  except Reservation.DoesNotExist:
    messages.error(request, 'Réservation introuvable')
    return redirect('volt_reservation_list')
  if request.method == 'POST':
    form = ReservationForm(request.POST, instance=reservation)
    if form.is_valid():
      form.save()
      messages.success(request, 'Réservation modifiée avec succès')
      return redirect('volt_reservation_list')
  else:
    form = ReservationForm(instance=reservation)
  return render(request, 'pages/reservations/form.html', {'segment': 'reservations', 'form': form, 'mode': 'update', 'reservation': reservation})

@login_required(login_url=reverse_lazy('login'))
def reservation_delete_volt(request, pk:int):
  try:
    reservation = Reservation.objects.get(pk=pk)
  except Reservation.DoesNotExist:
    messages.error(request, 'Réservation introuvable')
    return redirect('volt_reservation_list')
  if request.method == 'POST':
    reservation.delete()
    messages.success(request, 'Réservation supprimée')
    return redirect('volt_reservation_list')
  return render(request, 'pages/reservations/confirm_delete.html', {'segment': 'reservations', 'reservation': reservation})


# Reviews (Volt) – list + delete
@login_required(login_url=reverse_lazy('login'))
def review_list_volt(request):
  qs = Review.objects.select_related('hotel', 'user').order_by('-created_at') if hasattr(Review, 'created_at') else Review.objects.select_related('hotel', 'user').all()
  return render(request, 'pages/reviews/list.html', {'segment': 'reviews', 'reviews': qs})

@login_required(login_url=reverse_lazy('login'))
def review_delete_volt(request, pk:int):
  try:
    review = Review.objects.get(pk=pk)
  except Review.DoesNotExist:
    messages.error(request, 'Avis introuvable')
    return redirect('volt_review_list')
  if request.method == 'POST':
    review.delete()
    messages.success(request, 'Avis supprimé')
    return redirect('volt_review_list')
  return render(request, 'pages/reviews/confirm_delete.html', {'segment': 'reviews', 'review': review})


# Events CRUD (Volt)
@login_required(login_url=reverse_lazy('login'))
def event_list_volt(request):
  qs = Event.objects.order_by('-date_start')
  context = {
    'segment': 'events',
    'events': qs,
  }
  return render(request, 'pages/events/list.html', context)

@login_required(login_url=reverse_lazy('login'))
def event_create_volt(request):
  if request.method == 'POST':
    form = EventForm(request.POST, request.FILES)
    if form.is_valid():
      event = form.save()
      messages.success(request, 'Événement créé avec succès')
      return redirect('volt_event_detail', pk=event.pk)
  else:
    form = EventForm()
  context = {
    'segment': 'events',
    'form': form,
    'mode': 'create',
  }
  return render(request, 'pages/events/form.html', context)

@login_required(login_url=reverse_lazy('login'))
def event_detail_volt(request, pk:int):
  try:
    event = Event.objects.get(pk=pk)
    bookings = event.bookings.all()[:10]
    reviews = event.reviews.all()[:10]
  except Event.DoesNotExist:
    messages.error(request, 'Événement introuvable')
    return redirect('volt_event_list')
  context = {
    'segment': 'events',
    'event': event,
    'bookings': bookings,
    'reviews': reviews,
  }
  return render(request, 'pages/events/detail.html', context)

@login_required(login_url=reverse_lazy('login'))
def event_update_volt(request, pk:int):
  try:
    event = Event.objects.get(pk=pk)
  except Event.DoesNotExist:
    messages.error(request, 'Événement introuvable')
    return redirect('volt_event_list')
  if request.method == 'POST':
    form = EventForm(request.POST, request.FILES, instance=event)
    if form.is_valid():
      form.save()
      messages.success(request, 'Événement modifié avec succès')
      return redirect('volt_event_detail', pk=pk)
  else:
    form = EventForm(instance=event)
  context = {
    'segment': 'events',
    'form': form,
    'mode': 'update',
    'event': event,
  }
  return render(request, 'pages/events/form.html', context)

@login_required(login_url=reverse_lazy('login'))
def event_delete_volt(request, pk:int):
  try:
    event = Event.objects.get(pk=pk)
  except Event.DoesNotExist:
    messages.error(request, 'Événement introuvable')
    return redirect('volt_event_list')
  if request.method == 'POST':
    event.delete()
    messages.success(request, 'Événement supprimé')
    return redirect('volt_event_list')
  context = {
    'segment': 'events',
    'event': event,
  }
  return render(request, 'pages/events/confirm_delete.html', context)
