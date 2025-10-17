from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


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
    city = models.CharField(max_length=120, blank=True)

    def __str__(self):
        return self.user.username


class Activity(models.Model):
    TYPE_CHOICES = (
        ('culturelle', 'Culturelle'),
        ('sportive', 'Sportive'),
        ('gastronomique', 'Gastronomique'),
        ('artistique', 'Artistique'),
        ('aventure', 'Aventure'),
        ('autre', 'Autre'),
    )

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='autre')
    location = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_minutes = models.PositiveIntegerField()
    is_available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='activities/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class Reservation(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    )

    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='reservations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_reservations')
    date = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self) -> str:
        return f"{self.user.username} → {self.activity.name} ({self.status})"


class Review(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_reviews')
    comment = models.TextField(blank=True)
    rating = models.PositiveSmallIntegerField()  # 1..5
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('activity', 'user')
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.activity.name} - {self.rating}/5"


# Ensure a profile entry exists for each user
@receiver(post_save, sender=User)
def ensure_user_profile_exists(sender, instance: User, created: bool, **kwargs):
    if created:
        # Create a minimal profile when a new user is created
        try:
            register_table.objects.create(user=instance, contact_number=0, city="")
        except Exception:
            # Avoid breaking user creation if profile creation fails
            pass