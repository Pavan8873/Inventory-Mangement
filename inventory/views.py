from rest_framework import viewsets, permissions
from .models import InventoryItem
from .serializers import InventoryItemSerializer
from rest_framework.response import Response
from rest_framework import status
import redis
from django.conf import settings
import logging

# Configure Redis
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

# Configure Logging
logger = logging.getLogger(__name__)

class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, pk=None):
        # Check Redis cache
        cached_item = redis_client.get(f"item:{pk}")
        if cached_item:
            logger.info(f"Item {pk} retrieved from cache.")
            return Response(cached_item, status=status.HTTP_200_OK)

        # If not in cache, fetch from DB
        try:
            item = self.get_object()
            redis_client.set(f"item:{pk}", self.get_serializer(item).data)
            logger.info(f"Item {pk} retrieved from database and cached.")
            return Response(self.get_serializer(item).data, status=status.HTTP_200_OK)
        except InventoryItem.DoesNotExist:
            logger.error(f"Item {pk} not found.")
            return Response({"detail": "Item not found."}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info("Item created successfully.")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error("Item creation failed.")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        try:
            item = self.get_object()
            serializer = self.get_serializer(item, data=request.data)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Item {pk} updated successfully.")
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except InventoryItem.DoesNotExist:
            logger.error(f"Item {pk} not found for update.")
            return Response({"detail": "Item not found."}, status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, pk=None):
        try:
            item = self.get_object()
            item.delete()
            logger.info(f"Item {pk} deleted successfully.")
            return Response({"detail": "Item deleted."}, status=status.HTTP_204_NO_CONTENT)
        except InventoryItem.DoesNotExist:
            logger.error(f"Item {pk} not found for deletion.")
            return Response({"detail": "Item not found."}, status=status.HTTP_404_NOT_FOUND)
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework import status

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token = RefreshToken.for_user(user)
            return Response({
                'user': serializer.data,
                'token': {
                    'refresh': str(token),
                    'access': str(token.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            token = RefreshToken.for_user(user)
            return Response({
                'token': {
                    'refresh': str(token),
                    'access': str(token.access_token),
                }
            })
        return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
