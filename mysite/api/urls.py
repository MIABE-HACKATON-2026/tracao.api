from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from .views.auth import (
    RegisterView,
    LoginView,
    UserProfileView,
    KYCRecordViewSet,
    RequestOTPView,
    VerifyOTPView,
    CheckRoleView,
    RequestMagicLinkView,
    VerifyMagicLinkView,
    RequestPasswordResetView,
    InviteOperatorView,
    SetPasswordView,
)
from .views.production import ParcelViewSet, BatchViewSet, HarvestViewSet
from .views.stores import StoreViewSet, StoreMemberViewSet, StoreAgentViewSet
from .views.system import (
    SyncQueueViewSet,
    NotificationViewSet,
    TraceabilityViewSet,
    FraudAlertViewSet,
    BlockchainRecordViewSet,
    ReportViewSet,
)
from .views.commerce import TransactionViewSet
from .views.logistics import TransportViewSet, TransformationViewSet, TransporterRegistryViewSet
from .views.admin import (
    AdminUserViewSet,
    AdminKYCViewSet,
    AdminStoreViewSet,
    AdminBatchViewSet,
    AdminTransactionViewSet,
    GovDashboardView,
    GovProductionStatsView,
    GovEUDRView,
    GovAuditView,
    CertDashboardView,
    CertBatchViewSet,
    CertParcelViewSet,
    CertBlockchainView,
    SuperAdminDashboardView
)

router = DefaultRouter()
router.register(r"auth/kyc", KYCRecordViewSet, basename="kyc")
router.register(r"parcels", ParcelViewSet, basename="parcel")
router.register(r"batches", BatchViewSet, basename="batch")
router.register(r"harvests", HarvestViewSet, basename="harvest")
router.register(r"stores", StoreViewSet, basename="store")
router.register(r"store-members", StoreMemberViewSet, basename="store-member")
router.register(r"store-agents", StoreAgentViewSet, basename="store-agent")
router.register(r"sync-queue", SyncQueueViewSet, basename="sync-queue")
router.register(r"notifications", NotificationViewSet, basename="notification")
router.register(r"transactions", TransactionViewSet, basename="transaction")
router.register(r"transports", TransportViewSet, basename="transport")
router.register(r"transporters", TransporterRegistryViewSet, basename="transporter")
router.register(r"transformations", TransformationViewSet, basename="transformation")
router.register(r"traceability", TraceabilityViewSet, basename="traceability")
router.register(r"fraud-alerts", FraudAlertViewSet, basename="fraud-alert")
router.register(r"blockchain", BlockchainRecordViewSet, basename="blockchain")
router.register(r"reports", ReportViewSet, basename="report")

# Admin scoped routers
router.register(r"admin/users", AdminUserViewSet, basename="admin-user")
router.register(r"admin/kyc", AdminKYCViewSet, basename="admin-kyc")
router.register(r"admin/stores", AdminStoreViewSet, basename="admin-store")
router.register(r"admin/batches", AdminBatchViewSet, basename="admin-batch")
router.register(r"admin/transactions", AdminTransactionViewSet, basename="admin-transaction")
router.register(r"cert/batches", CertBatchViewSet, basename="cert-batch")
router.register(r"cert/parcels", CertParcelViewSet, basename="cert-parcel")

urlpatterns = [
    # Auth
    path("auth/register/", RegisterView.as_view(), name="auth_register"),
    path("auth/login/", LoginView.as_view(), name="auth_login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/profile/", UserProfileView.as_view(), name="user_profile"),
    path("auth/send-otp/", RequestOTPView.as_view(), name="auth_send_otp"),
    path("auth/verify-otp/", VerifyOTPView.as_view(), name="auth_verify_otp"),
    path("auth/check-role/", CheckRoleView.as_view(), name="auth_check_role"),
    path(
        "auth/request-magic-link/",
        RequestMagicLinkView.as_view(),
        name="auth_magic_link_request",
    ),
    path(
        "auth/verify-magic-link/",
        VerifyMagicLinkView.as_view(),
        name="auth_magic_link_verify",
    ),
    path("auth/request-password-reset/", RequestPasswordResetView.as_view(), name="auth_password_reset_request"),
    path("auth/invite-operator/", InviteOperatorView.as_view(), name="auth_invite_operator"),
    path("auth/set-password/", SetPasswordView.as_view(), name="auth_set_password"),
    
    # Admin scoped API views
    path("admin/dashboard/", SuperAdminDashboardView.as_view(), name="admin_dashboard"),
    path("gov/dashboard/", GovDashboardView.as_view(), name="gov_dashboard"),
    path("gov/stats/", GovProductionStatsView.as_view(), name="gov_stats"),
    path("gov/eudr/", GovEUDRView.as_view(), name="gov_eudr"),
    path("gov/audit/", GovAuditView.as_view(), name="gov_audit"),
    path("cert/dashboard/", CertDashboardView.as_view(), name="cert_dashboard"),
    path("cert/blockchain/", CertBlockchainView.as_view(), name="cert_blockchain"),
    
    # Router based endpoints
    path("", include(router.urls)),
    # Schema & Documentation
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
