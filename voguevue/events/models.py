from django.db import models
from django.contrib.auth.models import User


class Event(models.Model):
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=120)
    location = models.CharField(max_length=255, blank=True)
    date_start = models.DateTimeField()
    date_end = models.DateTimeField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='events/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.city}"

    class Meta:
        ordering = ['-date_start']
        db_table = 'voguevue_events_event'


class TicketBooking(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ticket_bookings')
    quantity = models.PositiveIntegerField(default=1)
    booking_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.event.name} ({self.quantity} tickets)"

    class Meta:
        ordering = ['-booking_date']
        db_table = 'voguevue_events_ticketbooking'


class EventReview(models.Model):
    RATING_CHOICES = [
        (1, '1★'),
        (2, '2★'),
        (3, '3★'),
        (4, '4★'),
        (5, '5★'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_reviews')
    rating = models.IntegerField(choices=RATING_CHOICES)
    review_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} for {self.event.name}"

    class Meta:
        ordering = ['-created_at']
        db_table = 'voguevue_events_eventreview'