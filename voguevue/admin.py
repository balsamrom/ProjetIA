from django.contrib import admin
from .models import Contact , register_table , updatemail, Hotel, Room, Reservation
# Register your models here.

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
	list_display = ('name' , 'subject' , 'message') 
	ordering = ('name' ,) 
	search_fields = ('name' , 'subject')

admin.site.register(updatemail)

admin.site.register(register_table)

@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'price_per_night', 'is_available')
    list_filter = ('city', 'is_available')
    search_fields = ('name', 'city', 'address')

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'hotel', 'capacity', 'price_per_night', 'is_available')
    list_filter = ('hotel', 'is_available')

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'hotel', 'room', 'check_in', 'check_out', 'created_at')
    list_filter = ('hotel', 'room')