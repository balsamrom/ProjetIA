from django.contrib import admin
from .models import Contact, register_table, updatemail, Activity, Reservation, Review
# Register your models here.

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
	list_display = ('name' , 'subject' , 'message') 
	ordering = ('name' ,) 
	search_fields = ('name' , 'subject')

admin.site.register(updatemail)

admin.site.register(register_table)


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "location", "price", "is_available")
    list_filter = ("type", "location", "is_available")
    search_fields = ("name", "description", "location")


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("activity", "user", "date", "status")
    list_filter = ("status", "date")
    search_fields = ("activity__name", "user__username")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("activity", "user", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("activity__name", "user__username", "comment")