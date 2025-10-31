import email
from django.shortcuts import redirect, render , HttpResponse
from datetime import datetime
from .models import Contact , register_table , updatemail, Avis
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
# Import conditionnel du module IA
def get_analyse_function():
    """Retourne la fonction d'analyse ou une fonction de remplacement"""
    try:
        from voguevue.multimedia.karima_model.image_analyse import analyse_image
        return analyse_image
    except ImportError as e:
        print(f"Module IA non disponible: {e}")
        # Fonction de remplacement
        def analyse_image_fallback(img_path):
            return {
                "error": "Module IA non disponible. Veuillez installer TensorFlow et numpy.",
                "success": False,
                "predicted_labels": ["Module IA non disponible"],
                "probabilities": {}
            }
        return analyse_image_fallback

# Obtenir la fonction d'analyse
analyse_image = get_analyse_function()

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


def avis_list(request):
    avis_queryset = Avis.objects.select_related('user').order_by('-created_at')
    return render(request, 'main/avis_list.html', { 'avis_list': avis_queryset })


@login_required
def avis_create(request):
    if request.method == 'POST':
        comment = request.POST.get('comment')
        image = request.FILES.get('image')
        if not comment:
            messages.error(request, 'Le commentaire est obligatoire.')
            return render(request, 'main/avis_form.html')
        Avis.objects.create(user=request.user, comment=comment, image=image)
        messages.success(request, 'Votre avis a été ajouté.')
        return redirect('/multimedia')
    return render(request, 'main/avis_form.html')


@login_required
def avis_delete(request, avis_id):
    try:
        avis = Avis.objects.get(id=avis_id, user=request.user)
    except Avis.DoesNotExist:
        messages.error(request, "Avis introuvable ou non autorisé.")
        return redirect('/multimedia')
    if request.method == 'POST':
        avis.delete()
        messages.success(request, 'Avis supprimé.')
        return redirect('/multimedia')
    return render(request, 'main/avis_confirm_delete.html', { 'avis': avis })


@login_required
def avis_update(request, avis_id):
    try:
        avis = Avis.objects.get(id=avis_id, user=request.user)
    except Avis.DoesNotExist:
        messages.error(request, "Contenu introuvable ou non autorisé.")
        return redirect('/multimedia')

    if request.method == 'POST':
        comment = request.POST.get('comment')
        image = request.FILES.get('image')
        if not comment:
            messages.error(request, 'Le commentaire est obligatoire.')
        else:
            avis.comment = comment
            if image is not None:
                avis.image = image
            avis.save()
            messages.success(request, 'Contenu mis à jour.')
            return redirect('/multimedia')

    return render(request, 'main/avis_update.html', { 'avis': avis })


def _classify_image_keywords(text: str) -> dict:
    content = (text or '').lower()
    place_type = None
    if any(k in content for k in ['plage', 'beach', 'mer', 'sea', 'coast']):
        place_type = 'plage'
    elif any(k in content for k in ['montagne', 'mountain', 'alps', 'himalaya', 'everest']):
        place_type = 'montagne'
    elif any(k in content for k in ['desert', 'sahara', 'dune']):
        place_type = 'désert'
    elif any(k in content for k in ['ville', 'city', 'downtown', 'urban']):
        place_type = 'ville'

    city_guess = None
    city_keywords = {
        'paris': ['paris', 'eiffel'],
        'mumbai': ['mumbai', 'bombay', 'gateway of india'],
        'agra': ['agra', 'taj'],
        'delhi': ['delhi', 'red fort'],
        'new york': ['new york', 'nyc', 'manhattan'],
        'tunisie': ['tunisia', 'tunisie', 'hammamet', 'sidi bou'],
        'amritsar': ['amritsar', 'golden temple'],
        'mysore': ['mysore', 'mysuru', 'palace'],
    }
    for city, keys in city_keywords.items():
        if any(k in content for k in keys):
            city_guess = city
            break

    return {
        'place_type': place_type or 'inconnu',
        'city_guess': city_guess or 'inconnue',
    }


def multimedia_scan(request, avis_id):
    try:
        avis = Avis.objects.get(id=avis_id)
    except Avis.DoesNotExist:
        messages.error(request, "Contenu introuvable.")
        return redirect('/multimedia')

    scan_result = None
    if request.method == 'POST':
        if avis.image:
            # Utiliser le modèle IA pour analyser l'image
            try:
                image_path = avis.image.path
                scan_result = analyse_image(image_path)
                
                if scan_result.get('success'):
                    messages.success(request, 'Analyse IA terminée avec succès!')
                else:
                    messages.error(request, f"Erreur lors de l'analyse: {scan_result.get('error', 'Erreur inconnue')}")
            except Exception as e:
                messages.error(request, f"Erreur lors de l'analyse de l'image: {str(e)}")
                scan_result = {"error": str(e)}
        else:
            messages.error(request, "Aucune image à analyser.")

    return render(request, 'main/multimedia_scan.html', { 'avis': avis, 'scan_result': scan_result })


def upload_and_analyse(request):
    from django.http import JsonResponse
    
    if request.method == "POST" and request.FILES.get("image"):
        uploaded_file = request.FILES["image"]

        fs = FileSystemStorage()
        file_path = fs.save(uploaded_file.name, uploaded_file)
        full_path = fs.path(file_path)

        # Analyse via le modèle IA
        result = analyse_image(full_path)

        # Retourner directement JSON pour les requêtes AJAX
        return JsonResponse(result)
    
    # Si pas de fichier, retourner une erreur
    return JsonResponse({
        "success": False,
        "error": "Aucune image fournie"
    })

def ai_scanner(request):
    """Page dédiée au scanner IA avec interface améliorée"""
    return render(request, "main/ai_scanner.html")