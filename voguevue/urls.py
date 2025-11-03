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
    # Multimédia routes (alias of Avis)
    path("multimedia", views.avis_list, name="multimedia_list"),
    path("multimedia/create", views.avis_create, name="multimedia_create"),
    path("multimedia/<int:avis_id>/delete", views.avis_delete, name="multimedia_delete"),
    path("multimedia/<int:avis_id>/edit", views.avis_update, name="multimedia_update"),
    path("multimedia/<int:avis_id>/scan", views.multimedia_scan, name="multimedia_scan"),
    path('analyse/', views.upload_and_analyse, name='upload_and_analyse'),
    path('multimedia/upload_and_analyse/', views.upload_and_analyse, name='upload_and_analyse'),
    path('ai-scanner/', views.ai_scanner, name='ai_scanner'),
    path('clarifai/classify', views.clarifai_classify, name='clarifai_classify'),
]