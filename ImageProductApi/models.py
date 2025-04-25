from django.db import models
from accounts.models import User

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


class ProductReview(models.Model):
    online_product = models.ForeignKey(OnlineProductImage, null=True, blank=True, on_delete=models.CASCADE)
    offline_product = models.ForeignKey(OfflineProductImage, null=True, blank=True, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], default=1)  # Rating scale from 1 to 5
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    email = models.CharField(max_length=100,null=True, blank=True)

    class Meta:
        unique_together = ('user', 'online_product')  # Can change to ('user', 'offline_product') if needed

    def __str__(self):
        return f"Review for {self.online_product.name if self.online_product else self.offline_product.name} by {self.user}"
    
class History(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='product_images/')
    price = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    store = models.TextField(blank=True)

    def __str__(self):
        return self.name