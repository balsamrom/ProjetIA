from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Event, TicketBooking, EventReview
from .forms import EventForm, TicketBookingForm, EventReviewForm


def event_list(request):
    """Liste de tous les événements avec recherche et filtres"""
    events = Event.objects.all().order_by('-date_start')
    
    # Recherche par nom ou ville
    q = (request.GET.get('q') or '').strip()
    if q:
        events = events.filter(Q(name__icontains=q) | Q(city__icontains=q))
    
    # Filtre par ville
    city = request.GET.get('city') or None
    if city:
        events = events.filter(city__icontains=city)
    
    context = {
        'events': events,
        'q': q,
        'q_city': city or '',
    }
    return render(request, 'main/events/event_list.html', context)


def event_detail(request, pk):
    """Détail d'un événement avec avis et formulaire de réservation"""
    event = get_object_or_404(Event, pk=pk)
    reviews = event.reviews.all()[:10]  # Limiter à 10 derniers avis
    
    # Calculer la note moyenne
    avg_rating = 0
    if reviews:
        avg_rating = sum(review.rating for review in reviews) / len(reviews)
    
    context = {
        'event': event,
        'reviews': reviews,
        'reviews_count': event.reviews.count(),
        'avg_rating': round(avg_rating, 1) if avg_rating > 0 else 0,
    }
    return render(request, 'main/events/event_detail.html', context)


@login_required(login_url='/signin/')
def event_create(request):
    """Créer un nouvel événement (staff only)"""
    if not request.user.is_staff:
        messages.error(request, 'Accès réservé aux administrateurs.')
        return redirect('event_list')
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Événement créé avec succès')
            return redirect('event_list')
    else:
        form = EventForm()
    
    return render(request, 'main/events/event_form.html', {'form': form, 'mode': 'create'})


@login_required(login_url='/signin/')
def event_update(request, pk):
    """Modifier un événement (staff only)"""
    if not request.user.is_staff:
        messages.error(request, 'Accès réservé aux administrateurs.')
        return redirect('event_list')
    
    event = get_object_or_404(Event, pk=pk)
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Événement modifié avec succès')
            return redirect('event_detail', pk=pk)
    else:
        form = EventForm(instance=event)
    
    return render(request, 'main/events/event_form.html', {
        'form': form,
        'mode': 'update',
        'event': event
    })


@login_required(login_url='/signin/')
def event_delete(request, pk):
    """Supprimer un événement (staff only)"""
    if not request.user.is_staff:
        messages.error(request, 'Accès réservé aux administrateurs.')
        return redirect('event_list')
    
    event = get_object_or_404(Event, pk=pk)
    
    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Événement supprimé')
        return redirect('event_list')
    
    return render(request, 'main/events/event_confirm_delete.html', {'event': event})


@login_required(login_url='/signin/')
def ticket_booking(request, pk):
    """Page de réservation de tickets"""
    event = get_object_or_404(Event, pk=pk)
    
    if request.method == 'POST':
        form = TicketBookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.event = event
            booking.user = request.user
            booking.save()
            messages.success(request, f'Réservation confirmée! {booking.quantity} ticket(s) pour {event.name}')
            return redirect('booking_success', booking_id=booking.id)
    else:
        form = TicketBookingForm()
    
    context = {
        'event': event,
        'form': form,
    }
    return render(request, 'main/events/ticket_booking.html', context)


def booking_success(request, booking_id):
    """Page de confirmation de réservation"""
    booking = get_object_or_404(TicketBooking, pk=booking_id)
    
    # Vérifier que l'utilisateur est le propriétaire de la réservation
    if request.user != booking.user and not request.user.is_staff:
        messages.error(request, 'Accès non autorisé.')
        return redirect('event_list')
    
    # Calculer le total
    total_price = float(booking.quantity) * float(booking.event.price)
    
    context = {
        'booking': booking,
        'event': booking.event,
        'total_price': total_price,
    }
    return render(request, 'main/events/booking_success.html', context)


@login_required(login_url='/signin/')
def create_review(request, pk):
    """Créer un avis pour un événement"""
    event = get_object_or_404(Event, pk=pk)
    
    if request.method == 'POST':
        form = EventReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.event = event
            review.user = request.user
            review.save()
            messages.success(request, f'Votre avis sur {event.name} a été publié !')
            return redirect('event_detail', pk=pk)
    else:
        form = EventReviewForm()
    
    context = {
        'event': event,
        'form': form,
    }
    return render(request, 'main/events/create_review.html', context)