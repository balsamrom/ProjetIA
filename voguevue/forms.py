from django import forms
from .models import Hotel, Room, Reservation
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Review

class HotelForm(forms.ModelForm):
    class Meta:
        model = Hotel
        fields = [
            'name',
            'city',
            'address',
            'description',
            'price_per_night',
            'rating',
            'is_available',
            'image',
        ]


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['hotel', 'name', 'capacity', 'price_per_night', 'is_available']


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['hotel', 'room', 'customer_name', 'check_in', 'check_out']
        widgets = {
            'check_in': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'check_out': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def clean(self):
        cleaned = super().clean()
        hotel = cleaned.get('hotel')
        room = cleaned.get('room')
        check_in = cleaned.get('check_in')
        check_out = cleaned.get('check_out')

        if hotel and room and room.hotel_id != hotel.id:
            raise ValidationError('Selected room does not belong to the chosen hotel.')

        if check_in and check_out:
            if check_in >= check_out:
                raise ValidationError('Check-out must be after check-in.')
            # Overlap validation for the same room
            overlaps = Reservation.objects.filter(room=room, check_in__lt=check_out, check_out__gt=check_in)
            if self.instance.pk:
                overlaps = overlaps.exclude(pk=self.instance.pk)
            if overlaps.exists():
                raise ValidationError('This room is already reserved for the selected dates.')

        return cleaned

class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(1, '1★'), (2, '2★'), (3, '3★'), (4, '4★'), (5, '5★')],
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Review
        fields = ['review_text', 'rating']
        widgets = {
            'review_text': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Partagez votre expérience avec cet hôtel...',
                'rows': 4
            }),
        }
        labels = {
            'review_text': 'Votre avis',
            'rating': 'Note (1 à 5 étoiles)'
        }

    def clean_rating(self):
        value = self.cleaned_data.get('rating')
        try:
            ivalue = int(value)
        except Exception:
            raise ValidationError('Veuillez choisir une note entre 1 et 5.')
        if ivalue < 1 or ivalue > 5:
            raise ValidationError('Veuillez choisir une note entre 1 et 5.')
        return ivalue