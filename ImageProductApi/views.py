import tempfile
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ImageUploadSerializer
from .models import OnlineProductImage, OfflineProductImage, History
from rest_framework import permissions
import easyocr
import torch.nn.functional as F
from rest_framework.permissions import AllowAny
from accounts.models import User
from .serializers import HistorySerializer
from .models import OnlineProductImage, OfflineProductImage, ProductReview
from .serializers import ProductReviewSerializer, ProductReviewCreateSerializer, OnlineProductImageSerializer, OfflineProductImageSerializer
from rest_framework import status, generics
import os
import torch
import torchvision.transforms as transforms
from torchvision import models
from PIL import Image
import tempfile
import os  
import torch
import clip
from PIL import Image

class ExtractAndMatchAPIView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    SIMILARITY_THRESHOLD = 0.75

    def load_clip_model(self):
        try:
            self.clip_model, self.preprocess = clip.load("ViT-B/32")
            self.clip_model.eval()
        except Exception as e:
            print("Error loading CLIP model:", e)

    def get_image_embedding(self, image_path):
        try:
            image = self.preprocess(Image.open(image_path).convert("RGB")).unsqueeze(0)
            with torch.no_grad():
                embedding = self.clip_model.encode_image(image)
            return embedding.squeeze()
        except Exception as e:
            print("Error creating embedding:", e)

    def compute_similarity(self, emb1, emb2):
        # Cosine similarity returns a tensor, get the scalar float with .item()
        return F.cosine_similarity(emb1.unsqueeze(0), emb2.unsqueeze(0)).item()

    def post(self, request, *args, **kwargs):
        self.load_clip_model()

        email = request.data.get('email')
        serializer = ImageUploadSerializer(data=request.data)

        if serializer.is_valid():
            uploaded_image = serializer.validated_data['image']

            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                for chunk in uploaded_image.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name

            try:
                try:
                    uploaded_embedding = self.get_image_embedding(temp_file_path)
                except Exception as e:
                    print(e)
                matched_online = []
                matched_offline = []

                for product in OnlineProductImage.objects.all():
                    if not product.image:
                        print("image not found")
                        continue
                    db_embedding = self.get_image_embedding(product.image.path)
                    similarity = self.compute_similarity(uploaded_embedding, db_embedding)
                    print("similarity online",similarity)
                    if similarity > self.SIMILARITY_THRESHOLD:
                        matched_online.append((similarity, product))

                for product in OfflineProductImage.objects.all():
                    if not product.image:
                        print("image not found")
                        continue
                    db_embedding = self.get_image_embedding(product.image.path)
                    similarity = self.compute_similarity(uploaded_embedding, db_embedding)
                    print("similarity",similarity)
                    if similarity > self.SIMILARITY_THRESHOLD:
                        matched_offline.append((similarity, product))

                # Sort descending by similarity
                matched_online.sort(key=lambda x: x[0], reverse=True)
                matched_offline.sort(key=lambda x: x[0], reverse=True)

                results = {}

                if matched_online:
                    results["online_products"] = [
                        {
                            "id": product.id,
                            "name": product.name,
                            "image": product.image.url if product.image else None,
                            "description": product.description,
                            "price": product.price,
                            "storetype": product.storetype,
                            "websitelink": product.websitelink,
                            "storename": product.storename,
                            "similarity": round(sim, 2)
                        }
                        for sim, product in matched_online
                    ]

                if matched_offline:
                    results["offline_products"] = [
                        {
                            "id": product.id,
                            "name": product.name,
                            "image": product.image.url if product.image else None,
                            "description": product.description,
                            "price": product.price,
                            "storetype": product.storetype,
                            "storelocation": product.storelocation,
                            "storename": product.storename,
                            "similarity": round(sim, 2)
                        }
                        for sim, product in matched_offline
                    ]

                if not results:
                    results["message"] = "No matching products found."

                # Save history for user if email provided
                if email:
                    try:
                        user = User.objects.get(email=email)
                        for _, product in matched_online:
                            History.objects.create(
                                name=product.name,
                                image=product.image,
                                price=product.price,
                                user=user,
                                store="Online"
                            )
                        for _, product in matched_offline:
                            History.objects.create(
                                name=product.name,
                                image=product.image,
                                price=product.price,
                                user=user,
                                store="Offline"
                            )
                    except Exception as e:
                        print("Error saving history:", e)

                os.remove(temp_file_path)
                return Response(results, status=status.HTTP_200_OK)

            except Exception as e:
                os.remove(temp_file_path)
                print(e)
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class HistoryByEmailAPIView(APIView):
    authentication_classes = []  # Disable CSRF-related auth
    permission_classes = [AllowAny]

    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        history = History.objects.filter(user=user)
        serializer = HistorySerializer(history, many=True)
        return Response(serializer.data)
    

class ProductDetailView(generics.GenericAPIView):
    authentication_classes = []  # Disable CSRF-related auth
    permission_classes = [AllowAny]
    def get(self, request, product_id, storetype):
        print(storetype)

        if storetype == "Online":

            online_product = OnlineProductImage.objects.get(id=product_id)
            product_type = 'Online'
            reviews = ProductReview.objects.filter(online_product=online_product)
        
        else:

            offline_product = OfflineProductImage.objects.get(id=product_id)
            product_type = 'Offline'
            reviews = ProductReview.objects.filter(offline_product=offline_product)
            
        print("reviews",reviews)
        # Serialize the reviews
        reviews_serializer = ProductReviewSerializer(reviews, many=True)
        product_data = {
            'product_type': product_type,
            'reviews': reviews_serializer.data
        }
        print(product_data)
        return Response(product_data, status=status.HTTP_200_OK)


class AddProductReviewView(generics.CreateAPIView):
    authentication_classes = []  # Disable CSRF-related auth
    permission_classes = [AllowAny]

    def post(self, request, product_id):
        # Add a review for a product
        review_data = request.data
        print(review_data)

        email = review_data['email']
        rating = review_data['rating']
        comment = review_data['comment']
        
        user = User.objects.get(email=email)

        # Check if the user has already reviewed this product
        if review_data['storetype'] == "Online":
            online_product = OnlineProductImage.objects.get(id=product_id)
            
            # Check if the user has already reviewed the online product
            existing_review = ProductReview.objects.filter(
                online_product=online_product, user=user
            ).first()

            if existing_review:
                print("online product")
                return Response({"error": "You have already rated this product."}, status=status.HTTP_400_BAD_REQUEST)

            # Create a new ProductReview for online product
            product_review = ProductReview.objects.create(
                online_product=online_product,
                user=user,
                rating=rating,
                comment=comment,
                email=email,
            )
        else:
            offline_product = OfflineProductImage.objects.get(id=product_id)
            
            # Check if the user has already reviewed the offline product
            existing_review = ProductReview.objects.filter(
                offline_product=offline_product, user=user
            ).first()

            if existing_review:
                print("offline product")
                return Response({"error": "You have already rated this product."}, status=status.HTTP_400_BAD_REQUEST)

            # Create a new ProductReview for offline product
            product_review = ProductReview.objects.create(
                offline_product=offline_product,
                user=user,
                rating=rating,
                comment=comment,
                email=email,
            )

        print(product_review)
        if product_review:
            serializer = ProductReviewSerializer(product_review)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response({"error": "Failed to Add Review"}, status=status.HTTP_400_BAD_REQUEST)