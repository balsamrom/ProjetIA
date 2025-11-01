from django.contrib import admin
from django.urls import path
from voguevue import views

urlpatterns = [
    path("", views.index, name='home'),
    path("about/", views.about, name='about'),
    path("services/", views.travels, name='services'),
    path("contact/", views.contact, name='contact'),
    path("signin/", views.signin , name="signin"),
    path("signup/", views.signup , name="signup"), 
    path("logout/", views.logout , name="logout"),
    path("profile/", views.profile, name="profile"),
    path("travels/", views.travels, name="travels"),
    path("blog/", views.blog, name="blog"),

    # Hotels CRUD - TOUTES les URLs doivent avoir des slashs
    path("hotels/", views.hotel_list, name="hotel_list"),
    path('hotels/new/', views.hotel_create, name='hotel_create'),
    path('hotels/<int:hotel_id>/reviews/create/', views.create_review, name='create_review'),
    path("hotels/<int:pk>/", views.hotel_detail, name="hotel_detail"),
    path("hotels/<int:pk>/edit/", views.hotel_update, name="hotel_update"),
    path("hotels/<int:pk>/payment/", views.hotel_payment, name="hotel_payment"),
    path("hotels/<int:pk>/delete/", views.hotel_delete, name="hotel_delete"),
    path("hotels/<int:hotel_id>/reviews/", views.hotel_reviews, name="hotel_reviews"),
    path("hotels/<int:hotel_id>/reviews/create/", views.create_review, name="create_review"),
    path('api/hotels/<int:pk>/predict-reputation/', views.predict_hotel_reputation_api, name='predict_hotel_reputation_api'),
 
    # OU si vous voulez l'URL plus courte :
    path('hotels/<int:pk>/predict-reputation/', views.predict_hotel_reputation_api, name='predict_hotel_reputation_api'),
    # Rooms & Reservations
    path("rooms/", views.room_list, name="room_list"),
    path("rooms/new/", views.room_create, name="room_create"),
    path("reservations/new/", views.reservation_create, name="reservation_create"),
    path("reservations/new/<int:room_id>/", views.reservation_create_for_room, name="reservation_create_for_room"),
    path("hotels/<int:hotel_id>/reserve-cheapest/", views.reserve_cheapest, name="reserve_cheapest"),
    path("reputation-analysis/", views.reputation_analysis, name="reputation_analysis"),
    path('api/generate-hotel-description/', views.api_generate_hotel_description, name='api_generate_hotel_description'),
    # Public search/filter APIs
    path('api/hotels', views.api_hotels, name='api_hotels'),
    path('api/rooms', views.api_rooms, name='api_rooms'),
    path('api/reservations', views.api_reservations, name='api_reservations'),
    # Admin-only actions
    path('api/admin/reviews/<int:pk>/delete', views.admin_delete_review, name='admin_delete_review'),
    
]# Ajoutez cette URL temporaire pour debug
