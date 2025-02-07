from django.db import models

class OnlineProductImage(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='product_images/')
    description = models.TextField(blank=True)
    price = models.TextField(blank=True)
    storetype = models.TextField(default="Online")
    websitelink = models.TextField(blank=True)
    storename = models.TextField(blank=True)

class OfflineProductImage(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='product_images/')
    description = models.TextField(blank=True)
    price = models.TextField(blank=True)
    storetype = models.TextField(default="Local")
    storelocation = models.TextField(blank=True)
    storename = models.TextField(blank=True)
