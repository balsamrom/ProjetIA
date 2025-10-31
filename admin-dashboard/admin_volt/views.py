from django.shortcuts import render, redirect
from admin_volt.forms import RegistrationForm, LoginForm, UserPasswordResetForm, UserPasswordChangeForm, UserSetPasswordForm
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordChangeView, PasswordResetConfirmView
from django.contrib.auth import logout
from django.urls import reverse, reverse_lazy

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from voguevue.models import Hotel
from voguevue.forms import HotelForm

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
    form = HotelForm(request.POST)
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
    form = HotelForm(request.POST, instance=hotel)
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

