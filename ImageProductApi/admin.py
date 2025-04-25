from django.contrib import admin
from .models import OnlineProductImage, OfflineProductImage , History , ProductReview

@admin.register(OnlineProductImage)
class OnlineProductImageAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'storetype', 'storename', 'websitelink')
    search_fields = ('name', 'description', 'storename', 'websitelink')

@admin.register(OfflineProductImage)
class OfflineProductImageAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'storetype', 'storename', 'storelocation')
    search_fields = ('name', 'description', 'storename', 'storelocation')

class HistoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'image','price', 'user', 'store')
    search_fields = ('name', 'user__username', 'store')
    list_filter = ('user', 'store')

admin.site.register(History, HistoryAdmin)

admin.site.register(ProductReview)