from django.shortcuts import render, redirect
from admin_volt.forms import RegistrationForm, LoginForm, UserPasswordResetForm, UserPasswordChangeForm, UserSetPasswordForm, ActivityForm
from voguevue.models import Activity, Reservation
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordChangeView, PasswordResetConfirmView
from django.contrib.auth import logout
from django.contrib import messages
from django.urls import reverse, reverse_lazy

from django.contrib.auth.decorators import login_required

# Index
def index(request):
  return render(request, 'pages/index.html')

# Dashboard
def dashboard(request):
  # Get statistics for admin dashboard
  from voguevue.models import Activity, Reservation, User
  
  total_activities = Activity.objects.count()
  total_reservations = Reservation.objects.count()
  total_users = User.objects.count()
  pending_reservations = Reservation.objects.filter(status='pending').count()
  
  # Recent activities
  recent_activities = Activity.objects.order_by('-created_at')[:5]
  
  # Recent reservations
  recent_reservations = Reservation.objects.select_related('activity', 'user').order_by('-created_at')[:5]
  
  context = {
    'segment': 'dashboard',
    'total_activities': total_activities,
    'total_reservations': total_reservations,
    'total_users': total_users,
    'pending_reservations': pending_reservations,
    'recent_activities': recent_activities,
    'recent_reservations': recent_reservations,
  }
  return render(request, 'pages/dashboard/dashboard.html', context)

# Pages
def transaction(request):
  context = {
    'segment': 'transactions'
  }
  return render(request, 'pages/transactions.html', context)

def activities(request):
  activities_qs = Activity.objects.all().order_by('name')
  context = {
    'segment': 'activities',
    'activities': activities_qs,
  }
  return render(request, 'pages/activities/index.html', context)


# ---------------- Reservations (Admin) ----------------
def reservations(request):
  qs = Reservation.objects.select_related('activity', 'user').order_by('-created_at')
  context = {
    'segment': 'reservations',
    'reservations': qs,
  }
  return render(request, 'pages/reservations/index.html', context)


def reservation_set_status(request, pk: int, status: str):
  if status not in ['confirmed', 'cancelled']:
    return redirect('admin_reservations')
  r = Reservation.objects.select_related('activity', 'user').get(pk=pk)
  r.status = status
  r.save(update_fields=['status'])
  messages.success(request, f"Réservation mise à jour: {r}")
  return redirect('admin_reservations')


def ai_recommendations_admin(request):
  from voguevue.models import Activity, Reservation, User, register_table
  
  # Get AI statistics
  total_activities = Activity.objects.count()
  total_reservations = Reservation.objects.count()
  total_users = User.objects.count()
  
  # Weather-based activity preferences
  weather_preferences = {
    'hot_weather': Activity.objects.filter(type__in=['culturelle', 'gastronomique']).count(),
    'cold_weather': Activity.objects.filter(type__in=['culturelle', 'artistique']).count(),
    'moderate_weather': Activity.objects.filter(type__in=['aventure', 'sportive']).count(),
  }
  
  # Most popular activity types
  activity_types = {}
  for activity in Activity.objects.all():
    activity_type = activity.get_type_display()
    activity_types[activity_type] = activity_types.get(activity_type, 0) + 1
  
  # Users with weather data
  users_with_weather = register_table.objects.exclude(city='').count()
  
  context = {
    'segment': 'ai_recommendations',
    'total_activities': total_activities,
    'total_reservations': total_reservations,
    'total_users': total_users,
    'users_with_weather': users_with_weather,
    'weather_preferences': weather_preferences,
    'activity_types': activity_types,
  }
  return render(request, 'pages/ai-recommendations/index.html', context)

def activity_create(request):
  if request.method == 'POST':
    form = ActivityForm(request.POST, request.FILES)
    if form.is_valid():
      form.save()
      messages.success(request, "Activité créée avec succès")
      return redirect('activities')
  else:
    form = ActivityForm()
  return render(request, 'pages/activities/form.html', { 'form': form, 'segment': 'activities', 'mode': 'create' })

def activity_edit(request, pk: int):
  activity = Activity.objects.get(pk=pk)
  if request.method == 'POST':
    form = ActivityForm(request.POST, request.FILES, instance=activity)
    if form.is_valid():
      form.save()
      messages.success(request, "Activité mise à jour")
      return redirect('activities')
  else:
    form = ActivityForm(instance=activity)
  return render(request, 'pages/activities/form.html', { 'form': form, 'segment': 'activities', 'mode': 'edit', 'activity': activity })

def activity_delete(request, pk: int):
  activity = Activity.objects.get(pk=pk)
  if request.method == 'POST':
    activity.delete()
    messages.success(request, "Activité supprimée")
    return redirect('activities')
  return render(request, 'pages/activities/confirm_delete.html', { 'segment': 'activities', 'activity': activity })

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