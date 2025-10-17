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

    # Activities & Reservations
    path("activities", views.activities_list, name="activities_list"),
    path("activities/<int:activity_id>/reserve", views.reserve_activity, name="reserve_activity"),
    path("my/reservations", views.my_reservations, name="my_reservations"),

    # Weather
    path("weather", views.weather, name="weather"),
    
    # AI Recommendations
    path("recommendations", views.ai_recommendations, name="ai_recommendations"),
]