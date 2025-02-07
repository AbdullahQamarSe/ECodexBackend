from django.urls import path
from .views import ExtractAndMatchAPIView

urlpatterns = [
    path('api/extract-and-match/', ExtractAndMatchAPIView.as_view(), name='extract-and-match'),
]
