from rest_framework import permissions


# ─── Base roles ──────────────────────────────────────────────────────────────

class IsFarmer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "farmer"


class IsBuyer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "buyer"


class IsStore(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "store"


# ─── Admin sub-role permissions ───────────────────────────────────────────────

class IsAnyAdmin(permissions.BasePermission):
    """Tout utilisateur avec role='admin', quelle que soit la sous-role."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "admin"


class IsSuperAdmin(permissions.BasePermission):
    """Accès contrôle total de la plateforme."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "admin"
            and request.user.sub_role == "super_admin"
        )


class IsGouvernement(permissions.BasePermission):
    """Accès analytique et réglementaire — lecture + exports."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "admin"
            and request.user.sub_role == "gouvernement"
        )


class IsCertificateur(permissions.BasePermission):
    """Accès spécialisé métier — certification de lots assignés."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "admin"
            and request.user.sub_role == "certificateur"
        )


class IsSuperAdminOrGouvernement(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "admin"
            and request.user.sub_role in ["super_admin", "gouvernement"]
        )


class IsAdminReadOnly(permissions.BasePermission):
    """
    Super Admin : accès en lecture + écriture.
    Gouvernement / Certificateur : lecture seule.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated or request.user.role != "admin":
            return False
        if request.user.sub_role == "super_admin":
            return True
        return request.method in permissions.SAFE_METHODS


# ─── Cross-role combinations ──────────────────────────────────────────────────

class IsAdmin(permissions.BasePermission):
    """Rétro-compatibilité — alias de IsSuperAdmin."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "admin"
            and request.user.sub_role in ["super_admin", None]
        )


class IsFarmerOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ["farmer", "admin"]


class IsStoreOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ["store", "admin"]


class IsBuyerOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ["buyer", "admin"]


class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin":
            return True
        if hasattr(obj, "user"):
            return obj.user == request.user
        if hasattr(obj, "farmer"):
            return obj.farmer == request.user
        if hasattr(obj, "buyer"):
            return obj.buyer == request.user
        return False


class ReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS