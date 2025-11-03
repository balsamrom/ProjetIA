from django.contrib import admin
from django.urls import path
from voguevue import views
from django.conf.urls.static import static
from django.conf import settings
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
    path("recommendation/", views.recommendation_view, name='recommendation'),
    # CRUD Destinations
    path("destinations/", views.destination_list, name='destination_list'),

    path("destinations/add/", views.add_destination, name='add_destination'),
    path("destinations/<int:id>/edit/", views.edit_destination, name='edit_destination'),
    path("destinations/<int:id>/delete/", views.delete_destination, name='delete_destination'),
    
    # 🤖 NOUVELLE ROUTE - Générateur IA complet
path("destinations/ai-generator/", views.destination_ai_generator, name='destination_ai_generator'),]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)