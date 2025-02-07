from django.contrib import admin
from .models import OnlineProductImage, OfflineProductImage

@admin.register(OnlineProductImage)
class OnlineProductImageAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'storetype', 'storename', 'websitelink')
    search_fields = ('name', 'description', 'storename', 'websitelink')

@admin.register(OfflineProductImage)
class OfflineProductImageAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'storetype', 'storename', 'storelocation')
    search_fields = ('name', 'description', 'storename', 'storelocation')
