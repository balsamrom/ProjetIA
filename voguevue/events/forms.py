from django import forms
from .models import Event, TicketBooking, EventReview


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'name',
            'city',
            'location',
            'date_start',
            'date_end',
            'price',
            'description',
            'image',
        ]
        widgets = {
            'date_start': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'date_end': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        date_start = cleaned_data.get('date_start')
        date_end = cleaned_data.get('date_end')

        if date_start and date_end:
            if date_start >= date_end:
                raise forms.ValidationError('La date de fin doit être après la date de début.')

        return cleaned_data


class TicketBookingForm(forms.ModelForm):
    class Meta:
        model = TicketBooking
        fields = ['quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10,
                'value': 1
            }),
        }

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity and quantity < 1:
            raise forms.ValidationError('La quantité doit être au moins 1.')
        if quantity and quantity > 10:
            raise forms.ValidationError('La quantité maximale est de 10 tickets.')
        return quantity


class EventReviewForm(forms.ModelForm):
    class Meta:
        model = EventReview
        fields = ['rating', 'review_text']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-control'}),
            'review_text': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Partagez votre expérience avec cet événement...',
                'rows': 4
            }),
        }
        labels = {
            'review_text': 'Votre avis',
            'rating': 'Note (1 à 5 étoiles)'
        }

    def clean_rating(self):
        value = self.cleaned_data.get('rating')
        if value and (value < 1 or value > 5):
            raise forms.ValidationError('Veuillez choisir une note entre 1 et 5.')
        return value
