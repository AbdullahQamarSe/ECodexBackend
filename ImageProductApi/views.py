import tempfile
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ImageUploadSerializer
from .models import OnlineProductImage, OfflineProductImage, History
from rest_framework import permissions
import easyocr
from rest_framework.permissions import AllowAny
from accounts.models import User
from .serializers import HistorySerializer
from .models import OnlineProductImage, OfflineProductImage, ProductReview
from .serializers import ProductReviewSerializer, ProductReviewCreateSerializer, OnlineProductImageSerializer, OfflineProductImageSerializer
from rest_framework import status, generics

class ExtractAndMatchAPIView(APIView):
    
    authentication_classes = []  # Disable CSRF-related auth
    permission_classes = [AllowAny]

    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        print("here")
        email = request.data.get('email') 
        
        if email:
            print(f"Email received: {email}")
        else:
            print("No email received.")
        
        serializer = ImageUploadSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Save the uploaded image to a temporary file
                uploaded_image = serializer.validated_data['image']

                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                    for chunk in uploaded_image.chunks():
                        temp_file.write(chunk)
                    temp_file_path = temp_file.name

                # Perform OCR using EasyOCR
                reader = easyocr.Reader(['en'])  # Specify the language(s)
                extracted_text = reader.readtext(temp_file_path, detail=0)

                # Clean up temporary file after OCR
                temp_file.close()

                if not extracted_text:
                    return Response({"message": "No text detected in the image"}, status=status.HTTP_204_NO_CONTENT)

                extracted_words = set(" ".join(extracted_text).split())

                # Query matching products
                online_products = OnlineProductImage.objects.filter(
                    name__iregex=r'\b(' + '|'.join(extracted_words) + r')\b'
                )
                offline_products = OfflineProductImage.objects.filter(
                    name__iregex=r'\b(' + '|'.join(extracted_words) + r')\b'
                )

                # Prepare the results
                results = {
                    "online_products": [
                        {
                            "id": product.id,
                            "name": product.name,
                            "image": product.image.url if product.image else None,
                            "description": product.description,
                            "price": product.price,
                            "storetype": product.storetype,
                            "websitelink": product.websitelink,
                            "storename": product.storename,
                        }
                        for product in online_products
                    ] if online_products.exists() else "No online products found",
                    "offline_products": [
                        {
                            "id": product.id,
                            "name": product.name,
                            "image": product.image.url if product.image else None,
                            "description": product.description,
                            "price": product.price,
                            "storetype": product.storetype,
                            "storelocation": product.storelocation,
                            "storename": product.storename,
                        }
                        for product in offline_products
                    ] if offline_products.exists() else "No offline products found",
                }
                try:
                    if email:
                        user = User.objects.get(email=email) 
                        if online_products.exists() or offline_products.exists():
                                for product in online_products:
                                    History.objects.create(
                                        name=product.name,
                                        image=product.image,
                                        price=product.price,
                                        user=user,
                                        store="Online"
                                    )
                                for product in offline_products:
                                    History.objects.create(
                                        name=product.name,
                                        image=product.image,
                                        price=product.price,
                                        user=user,
                                        store="Offline"
                                    )

                    print(results)
                except Exception as e:
                    print(e)

                return Response(results, status=status.HTTP_200_OK)
            except Exception as e:
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