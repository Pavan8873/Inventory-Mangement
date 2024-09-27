from django.urls import path, include
from .views import InventoryItemViewSet, RegisterView, LoginView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'items', InventoryItemViewSet)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('', include(router.urls)),
]
