from django.shortcuts import redirect, render, HttpResponse
from datetime import datetime
from .models import Contact, register_table, updatemail, Destination
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import logout as django_logout
from .forms import DestinationForm
from django.shortcuts import get_object_or_404, redirect, render
from .recommendation import recommender
import json
from .hug_face_service import hf_service

# Vos vues existantes (inchangées)
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
    return render(request, 'main/travels.html')

def signin(request):
    if request.method == "POST":
        username = request.POST.get('uname')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return render(request, 'main/index.html', {"success": " Logged in Successfully "})
        else:
            return render(request, 'authentication/signin.html', {"msg": " Enter the Correct Credentials "})
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
    return redirect("/signin", {"logsign": " Logged Out Successfully"})

def profile(request):
    if request.user.is_authenticated:
        return render(request, 'main/profile.html')
    else:
        return redirect('/signin')

def error_404(request, exception):
    return render(request, 'main/404.html')

def blog(request):
    return render(request, 'main/blog.html')

# --- CRUD Destinations avec OpenAI ---
def destination_list(request):
    q = request.GET.get('q', '')
    if q:
        destinations = Destination.objects.filter(destination__icontains=q) | Destination.objects.filter(country__icontains=q)
    else:
        destinations = Destination.objects.all().order_by('-created_at')
    return render(request, 'voguevue/destination_list.html', {'destinations': destinations, 'q': q})

def add_destination(request):
    """Ajout d'une destination avec génération IA"""
    
    if request.method == 'POST':
        # Vérifier si c'est une demande de génération IA
        if 'generate_ai' in request.POST:
            destination_name = request.POST.get('destination', '').strip()
            country = request.POST.get('country', '').strip()
            category = request.POST.get('category', '').strip()
            
            if not destination_name or not country:
                messages.error(request, '❌ Veuillez renseigner au minimum le nom et le pays')
                form = DestinationForm()
                return render(request, 'voguevue/destination_form.html', {'form': form, 'action': 'Ajouter'})
            
            print(f"🤖 Génération IA pour: {destination_name}, {country}")
            
            # Appeler OpenAI pour générer la description
            result = hf_service.generate_destination_description(
                destination_name, country, category if category else None
            )
            
            if result['success']:
                # Pré-remplir le formulaire avec les données générées
                initial_data = {
                    'destination': destination_name,
                    'country': country,
                    'category': category if category else '',
                    'description': result['data'].get('description', ''),
                    'best_time': result['data'].get('best_time', ''),
                    'cultural_significance': result['data'].get('cultural_significance', ''),
                    'famous_foods': result['data'].get('famous_foods', ''),
                }
                
                form = DestinationForm(initial=initial_data)
                
                messages.success(request, '✅ Description générée par OpenAI avec succès!')
                
                return render(request, 'voguevue/destination_form.html', {
                    'form': form,
                    'action': 'Ajouter',
                    'ai_generated': True,
                    'ai_activities': result['data'].get('activities', ''),
                })
            else:
                messages.error(request, f'❌ Erreur lors de la génération: {result["error"]}')
                form = DestinationForm(initial={
                    'destination': destination_name,
                    'country': country,
                    'category': category
                })
                return render(request, 'voguevue/destination_form.html', {'form': form, 'action': 'Ajouter'})
        
        # Sinon, sauvegarde normale du formulaire
        else:
            form = DestinationForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                messages.success(request, '✅ Destination ajoutée avec succès!')
                return redirect('destination_list')
            else:
                messages.error(request, '❌ Erreur dans le formulaire')
    else:
        form = DestinationForm()
    
    return render(request, 'voguevue/destination_form.html', {
        'form': form,
        'action': 'Ajouter'
    })

def edit_destination(request, id):
    """Édition avec possibilité de régénérer avec l'IA"""
    dest = get_object_or_404(Destination, id=id)
    
    if request.method == 'POST':
        # Vérifier si régénération IA demandée
        if 'regenerate_ai' in request.POST:
            print(f"🔄 Régénération IA pour: {dest.destination}")
            
            result = hf_service.generate_destination_description(
                dest.destination, dest.country, dest.category
            )
            
            if result['success']:
                # Mettre à jour avec les nouvelles données
                dest.description = result['data'].get('description', dest.description)
                dest.best_time = result['data'].get('best_time', dest.best_time)
                dest.cultural_significance = result['data'].get('cultural_significance', dest.cultural_significance)
                dest.famous_foods = result['data'].get('famous_foods', dest.famous_foods)
                dest.save()
                
                messages.success(request, '✅ Description régénérée avec OpenAI!')
                return redirect('edit_destination', id=id)
            else:
                messages.error(request, f'❌ Erreur lors de la régénération: {result["error"]}')
        
        # Sauvegarde normale
        else:
            form = DestinationForm(request.POST, request.FILES, instance=dest)
            if form.is_valid():
                form.save()
                messages.success(request, '✅ Destination modifiée avec succès!')
                return redirect('destination_list')
    else:
        form = DestinationForm(instance=dest)
    
    return render(request, 'voguevue/destination_form.html', {
        'form': form,
        'action': 'Modifier',
        'destination': dest
    })

def delete_destination(request, id):
    dest = get_object_or_404(Destination, id=id)
    if request.method == 'POST':
        dest.delete()
        messages.success(request, '✅ Destination supprimée avec succès!')
        return redirect('destination_list')
    return render(request, 'voguevue/destination_confirm_delete.html', {'destination': dest})

# --- 🤖 NOUVELLE VUE: Générateur IA complet ---
def destination_ai_generator(request):
    """
    Page dédiée pour générer une destination complète avec OpenAI
    L'utilisateur entre seulement le nom et le pays, l'IA génère tout le reste
    """
    generated_data = None
    error = None
    
    if request.method == 'POST':
        destination_name = request.POST.get('destination', '').strip()
        country = request.POST.get('country', '').strip()
        category = request.POST.get('category', '').strip()
        
        if not destination_name or not country:
            error = '❌ Veuillez renseigner le nom de la destination et le pays'
        else:
            print(f"🤖 Génération IA complète pour: {destination_name}, {country}")
            
            # Génération avec OpenAI
            result = hf_service.generate_destination_description(
                destination_name, country, category if category else None
            )
            
            if result['success']:
                generated_data = {
                    'destination': destination_name,
                    'country': country,
                    'category': category,
                    'description': result['data'].get('description', ''),
                    'best_time': result['data'].get('best_time', ''),
                    'cultural_significance': result['data'].get('cultural_significance', ''),
                    'famous_foods': result['data'].get('famous_foods', ''),
                    'activities': result['data'].get('activities', ''),
                }
                
                # Si on clique sur "Enregistrer", sauvegarder dans la BD
                if 'save_destination' in request.POST:
                    new_dest = Destination(
                        destination=destination_name,
                        country=country,
                        category=category if category else None,
                        description=generated_data['description'],
                        best_time=generated_data['best_time'],
                        cultural_significance=generated_data['cultural_significance'],
                        famous_foods=generated_data['famous_foods'],
                    )
                    new_dest.save()
                    messages.success(request, f'✅ La destination "{destination_name}" a été créée avec succès grâce à l\'IA!')
                    return redirect('destination_list')
                
                messages.success(request, '✨ Contenu généré par OpenAI avec succès!')
            else:
                error = f'❌ Erreur lors de la génération: {result["error"]}'
    
    context = {
        'generated_data': generated_data,
        'error': error,
    }
    
    return render(request, 'voguevue/destination_ai_generator.html', context)

# --- Recommandation IA ---
def recommendation_view(request):
    """Page de recommandation IA"""
    recommendations = None
    error = None
    search_query = ""
    
    destination_from_url = request.GET.get('destination', '').strip()
    if destination_from_url:
        search_query = destination_from_url
    
    if request.method == 'POST':
        search_query = request.POST.get('destination', '').strip()
    
    if search_query:
        print(f"🎯 Recherche de recommandations pour: {search_query}")
        result = recommender.recommend(search_query)
        if 'error' in result:
            error = result['error']
            print(f"❌ Erreur: {error}")
        else:
            recommendations = result
            print(f"✅ Recommandations trouvées: {len(recommendations['recommendations'])}")
    
    context = {
        'recommendations': recommendations,
        'error': error,
        'search_query': search_query,
        'model_loaded': recommender.model_loaded
    }
    
    return render(request, 'voguevue/recommendation.html', context)