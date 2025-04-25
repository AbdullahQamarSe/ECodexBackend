from django.urls import path
from .views import ExtractAndMatchAPIView,HistoryByEmailAPIView
from .views import ProductDetailView, AddProductReviewView

urlpatterns = [
    path('extract-and-match/', ExtractAndMatchAPIView.as_view(), name='extract-and-match'),
    path('history-by-email/', HistoryByEmailAPIView.as_view(), name='history-by-email'),
    path('product/<int:product_id>/storetype/<str:storetype>/', ProductDetailView.as_view(), name='product-detail'),
    path('product/<int:product_id>/add-review/', AddProductReviewView.as_view(), name='add-review'),
]
