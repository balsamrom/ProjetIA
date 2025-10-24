from django.contrib import admin
from .models import Contact, register_table, updatemail, Destination

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'message') 
    ordering = ('name',) 
    search_fields = ('name', 'subject')

admin.site.register(updatemail)
admin.site.register(register_table)

@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ('destination', 'country', 'category', 'cost_of_living')
    search_fields = ('destination', 'country', 'category')
    list_filter = ('country', 'category')