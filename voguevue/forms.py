from django import forms
from .models import Hotel, Room, Reservation
from django.core.exceptions import ValidationError
from django.utils import timezone


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
        ]


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['hotel', 'name', 'capacity', 'price_per_night', 'is_available']


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['hotel', 'room', 'customer_name', 'check_in', 'check_out']

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

