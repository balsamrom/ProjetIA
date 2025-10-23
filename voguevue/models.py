from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# Create your models here.

class Contact(models.Model):
    name = models.CharField(max_length=122)
    email = models.EmailField(max_length=122)
    subject = models.CharField(max_length=50)
    message = models.TextField()
    date = models.DateField()

    def __str__(self):
        return self.name

class updatemail(models.Model):
    emailadd = models.EmailField(max_length=100)

    def __str__(self):
        return self.emailadd

class register_table(models.Model):
    user = models.OneToOneField(User , on_delete=models.CASCADE)
    contact_number = models.IntegerField()

    def __str__(self):
        return self.user.username
    
class Activity(models.Model):
    """Modèle pour les activités touristiques"""
    
    activity_name = models.CharField(max_length=255, verbose_name="Nom de l'activité")
    category = models.CharField(max_length=100, verbose_name="Catégorie")
    location = models.CharField(max_length=200, verbose_name="Ville")
    description = models.TextField(verbose_name="Description")
    weather = models.CharField(
        max_length=50, 
        choices=[
            ('sunny', 'Ensoleillé'),
            ('rainy', 'Pluvieux'),
            ('cloudy', 'Nuageux'),
            ('hot', 'Chaud'),
            ('cold', 'Froid'),
            ('snowy', 'Neigeux'),
            ('windy', 'Venteux'),
        ],
        verbose_name="Météo idéale"
    )
    popularity = models.IntegerField(default=50, verbose_name="Popularité (0-100)")
    duration = models.CharField(max_length=50, blank=True, null=True, verbose_name="Durée")
    price = models.CharField(max_length=50, blank=True, null=True, verbose_name="Prix")
    profile = models.CharField(max_length=100, blank=True, null=True, verbose_name="Profil cible")
    
    # 🆕 CHAMP IMPORTANT pour le système hybride
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        db_table = 'activities'
        verbose_name = 'Activité'
        verbose_name_plural = 'Activités'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.activity_name} - {self.location}"