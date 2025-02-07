import tempfile
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ImageUploadSerializer
from .models import OnlineProductImage, OfflineProductImage
import easyocr

class ExtractAndMatchAPIView(APIView):
    def post(self, request, *args, **kwargs):
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
                print(results)
                return Response(results, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
