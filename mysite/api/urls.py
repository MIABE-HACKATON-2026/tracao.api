from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from .views.auth import RegisterView, UserProfileView, KYCRecordViewSet
from .views.production import ParcelViewSet, BatchViewSet, HarvestViewSet
from .views.stores import StoreViewSet, StoreMemberViewSet, StoreAgentViewSet
from .views.system import (
    SyncQueueViewSet, NotificationViewSet, TraceabilityViewSet, 
    FraudAlertViewSet, BlockchainRecordViewSet, ReportViewSet
)
from .views.commerce import TransactionViewSet
from .views.logistics import TransportViewSet, TransformationViewSet

router = DefaultRouter()
router.register(r'auth/kyc', KYCRecordViewSet, basename='kyc')
router.register(r'parcels', ParcelViewSet, basename='parcel')
router.register(r'batches', BatchViewSet, basename='batch')
router.register(r'harvests', HarvestViewSet, basename='harvest')
router.register(r'stores', StoreViewSet, basename='store')
router.register(r'store-members', StoreMemberViewSet, basename='store-member')
router.register(r'store-agents', StoreAgentViewSet, basename='store-agent')
router.register(r'sync-queue', SyncQueueViewSet, basename='sync-queue')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'transports', TransportViewSet, basename='transport')
router.register(r'transformations', TransformationViewSet, basename='transformation')
router.register(r'traceability', TraceabilityViewSet, basename='traceability')
router.register(r'fraud-alerts', FraudAlertViewSet, basename='fraud-alert')
router.register(r'blockchain', BlockchainRecordViewSet, basename='blockchain')
router.register(r'reports', ReportViewSet, basename='report')

urlpatterns = [
    # Auth
    path('auth/register/', RegisterView.as_view(), name='auth_register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', UserProfileView.as_view(), name='user_profile'),
    
    # Router based endpoints
    path('', include(router.urls)),

    # Schema & Documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
