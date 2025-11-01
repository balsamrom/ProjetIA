from django.contrib import admin
from .models import Event, TicketBooking, EventReview


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'date_start', 'date_end', 'price', 'created_at')
    list_filter = ('city', 'date_start', 'created_at')
    search_fields = ('name', 'city', 'location')
    date_hierarchy = 'date_start'


@admin.register(TicketBooking)
class TicketBookingAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'quantity', 'booking_date')
    list_filter = ('booking_date', 'event')
    search_fields = ('event__name', 'user__username')
    date_hierarchy = 'booking_date'


@admin.register(EventReview)
class EventReviewAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('event__name', 'user__username', 'review_text')
    date_hierarchy = 'created_at'