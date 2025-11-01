from django.urls import path
from . import views

urlpatterns = [
    # Events CRUD
    path("events/", views.event_list, name="event_list"),
    path("events/new/", views.event_create, name="event_create"),
    path("events/<int:pk>/", views.event_detail, name="event_detail"),
    path("events/<int:pk>/edit/", views.event_update, name="event_update"),
    path("events/<int:pk>/delete/", views.event_delete, name="event_delete"),
    
    # Ticket booking and reviews
    path("events/<int:pk>/book/", views.ticket_booking, name="ticket_booking"),
    path("bookings/<int:booking_id>/success/", views.booking_success, name="booking_success"),
    path("events/<int:pk>/review/", views.create_review, name="create_event_review"),
]
