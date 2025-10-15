from django.contrib import admin
from django.urls import path
from voguevue import views

urlpatterns = [
    path("", views.index, name='home'),
    path("about", views.about, name='about'),
    path("services", views.travels, name='services'),
    path("contact", views.contact, name='contact'),
    path("signin", views.signin , name="signin"),
    path("signup", views.signup , name="signup"), 
    path("logout", views.logout , name="logout"),
    path("profile" , views.profile , name="profile"),
    path("travels" , views.travels , name="travels"),
    path("blog" , views.blog , name="blog"),
    # Hotels CRUD
    path("hotels", views.hotel_list, name="hotel_list"),
    path("hotels/new", views.hotel_create, name="hotel_create"),
    path("hotels/<int:pk>", views.hotel_detail, name="hotel_detail"),
    path("hotels/<int:pk>/edit", views.hotel_update, name="hotel_update"),
    path("hotels/<int:pk>/delete", views.hotel_delete, name="hotel_delete"),
    # Rooms & Reservations
    path("rooms", views.room_list, name="room_list"),
    path("rooms/new", views.room_create, name="room_create"),
    path("reservations/new", views.reservation_create, name="reservation_create"),
    path("reservations/new/<int:room_id>", views.reservation_create, name="reservation_create_for_room"),
    path("hotels/<int:hotel_id>/reserve-cheapest", views.reserve_cheapest, name="reserve_cheapest"),
]