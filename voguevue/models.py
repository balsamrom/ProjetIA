from django.db import models
from django.contrib.auth.models import User


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
class Destination(models.Model):
    destination = models.CharField(max_length=120)
    region = models.CharField(max_length=120, blank=True, null=True)
    country = models.CharField(max_length=80)
    category = models.CharField(max_length=80, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    annual_tourists = models.CharField(max_length=80, blank=True, null=True)
    currency = models.CharField(max_length=50, blank=True, null=True)
    majority_religion = models.CharField(max_length=100, blank=True, null=True)
    famous_foods = models.CharField(max_length=250, blank=True, null=True)
    language = models.CharField(max_length=80, blank=True, null=True)
    best_time = models.CharField(max_length=120, blank=True, null=True)
    cost_of_living = models.CharField(max_length=80, blank=True, null=True)
    safety = models.CharField(max_length=250, blank=True, null=True)
    cultural_significance = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    # AJOUTEZ CE CHAMP POUR L'IMAGE
    image = models.ImageField(upload_to='destinations/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.destination} ({self.country})"