from django.shortcuts import render, redirect
from admin_volt.forms import RegistrationForm, LoginForm, UserPasswordResetForm, UserPasswordChangeForm, UserSetPasswordForm, AvisForm
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordChangeView, PasswordResetConfirmView
from django.contrib.auth import logout
from django.urls import reverse, reverse_lazy

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from voguevue.models import Avis
from django.core.paginator import Paginator

# Index
def index(request):
  return render(request, 'pages/index.html')

# Dashboard
def dashboard(request):
  total_avis = Avis.objects.count()
  total_with_image = Avis.objects.exclude(image='').exclude(image__isnull=True).count()
  total_without_image = total_avis - total_with_image
  recent_avis = Avis.objects.select_related('user').order_by('-created_at')[:6] if hasattr(Avis, 'created_at') else Avis.objects.select_related('user').all()[:6]
  context = {
    'segment': 'dashboard',
    'mm_total': total_avis,
    'mm_with_image': total_with_image,
    'mm_without_image': total_without_image,
    'mm_recent': recent_avis,
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



 


# Multimedia (Avis) CRUD (Volt)
@login_required(login_url=reverse_lazy('login'))
def multimedia_list_volt(request):
  qs = Avis.objects.select_related('user').order_by('-created_at') if hasattr(Avis, 'created_at') else Avis.objects.select_related('user').all()
  q = request.GET.get('q', '').strip()
  has_image = request.GET.get('has_image', '') == '1'
  if q:
    from django.db.models import Q
    qs = qs.filter(Q(title__icontains=q) | Q(comment__icontains=q) | Q(user__username__icontains=q))
  if has_image:
    qs = qs.exclude(image='').exclude(image__isnull=True)

  # KPIs
  total_avis = Avis.objects.count()
  total_with_image = Avis.objects.exclude(image='').exclude(image__isnull=True).count()
  total_without_image = total_avis - total_with_image

  # Pagination
  paginator = Paginator(qs, 10)
  page_number = request.GET.get('page')
  page_obj = paginator.get_page(page_number)

  ctx = {
    'segment': 'multimedia',
    'items': page_obj,
    'page_obj': page_obj,
    'q': q,
    'has_image': '1' if has_image else '',
    'mm_total': total_avis,
    'mm_with_image': total_with_image,
    'mm_without_image': total_without_image,
  }
  return render(request, 'pages/multimedia/list.html', ctx)

@login_required(login_url=reverse_lazy('login'))
def multimedia_create_volt(request):
  if request.method == 'POST':
    form = AvisForm(request.POST, request.FILES)
    if form.is_valid():
      obj = form.save(commit=False)
      obj.user = request.user
      obj.save()
      messages.success(request, 'Contenu créé avec succès')
      return redirect('volt_multimedia_list')
  else:
    form = AvisForm()
  return render(request, 'pages/multimedia/form.html', {'segment': 'multimedia', 'form': form, 'mode': 'create'})

@login_required(login_url=reverse_lazy('login'))
def multimedia_update_volt(request, pk:int):
  try:
    item = Avis.objects.get(pk=pk)
  except Avis.DoesNotExist:
    messages.error(request, 'Contenu introuvable')
    return redirect('volt_multimedia_list')
  if request.method == 'POST':
    form = AvisForm(request.POST, request.FILES, instance=item)
    if form.is_valid():
      form.save()
      messages.success(request, 'Contenu modifié avec succès')
      return redirect('volt_multimedia_list')
  else:
    form = AvisForm(instance=item)
  return render(request, 'pages/multimedia/form.html', {'segment': 'multimedia', 'form': form, 'mode': 'update', 'item': item})

@login_required(login_url=reverse_lazy('login'))
def multimedia_delete_volt(request, pk:int):
  try:
    item = Avis.objects.get(pk=pk)
  except Avis.DoesNotExist:
    messages.error(request, 'Contenu introuvable')
    return redirect('volt_multimedia_list')
  if request.method == 'POST':
    item.delete()
    messages.success(request, 'Contenu supprimé')
    return redirect('volt_multimedia_list')
  return render(request, 'pages/multimedia/confirm_delete.html', {'segment': 'multimedia', 'item': item})
