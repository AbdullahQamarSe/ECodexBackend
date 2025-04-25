from rest_framework import serializers
from .models import History
from .models import OnlineProductImage, OfflineProductImage, ProductReview

class ImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()

class HistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = History
        fields = ['id', 'name', 'image', 'price', 'store']

class OnlineProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnlineProductImage
        fields = '__all__'


class OfflineProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfflineProductImage
        fields = '__all__'

class ProductReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductReview
        fields = ['id', 'user', 'rating', 'comment', 'online_product', 'offline_product', 'created_at','email']


class ProductReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductReview
        fields = ['rating', 'comment']