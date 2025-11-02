from django.contrib import admin
from django.urls import path
from voguevue import views

urlpatterns = [
    # Pages principales
    path("", views.index, name='home'),
    path("about", views.about, name='about'),
    path("services", views.travels, name='services'),
    path("contact", views.contact, name='contact'),
    path("travels", views.travels, name="travels"),
    path("blog", views.blog, name="blog"),
    
    # Authentification
    path("signin", views.signin, name="signin"),
    path("signup", views.signup, name="signup"),
    path("logout", views.logout, name="logout"),
    path("profile", views.profile, name="profile"),
    
    # 🆕 APIs IA
    path("api/recommendations", views.get_recommendations_api, name="recommendations_api"),
    path("api/chat", views.get_ai_chat, name="ai_chat"),  # 🤖 Chatbot Gemini
]