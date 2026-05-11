import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("The Email must be set"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    ROLE_CHOICES = [
        ("farmer", "Farmer"),
        ("buyer", "Buyer"),
        ("store", "Store"),
        ("admin", "Admin"),
    ]
    SUB_ROLE_CHOICES = [
        ("exportateur", "Exportateur"),
        ("importateur", "Importateur"),
        ("transformateur", "Transformateur"),
    ]
    STATUS_CHOICES = [
        ("active", "Active"),
        ("suspended", "Suspended"),
        ("pending", "Pending"),
    ]
    KYC_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    sub_role = models.CharField(
        max_length=20, choices=SUB_ROLE_CHOICES, null=True, blank=True
    )

    profile_photo = models.ImageField(upload_to="profiles/", null=True, blank=True)
    import_license = models.FileField(upload_to="licenses/", null=True, blank=True)
    export_license = models.FileField(upload_to="licenses/", null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    kyc_status = models.CharField(
        max_length=20, choices=KYC_STATUS_CHOICES, default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "phone"]

    class Meta:
        indexes = [
            models.Index(fields=["role", "status"], name="idx_users_role_status"),
            models.Index(fields=["phone"], name="idx_users_phone"),
            models.Index(fields=["email"], name="idx_users_email"),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"


class OTPRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["email", "code"], name="idx_otp_email_code"),
        ]

    def is_valid(self):
        from django.utils import timezone

        return not self.is_used and self.expires_at > timezone.now()


class KYCRecord(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="kyc_records")
    cni_front_image = models.ImageField(upload_to="kyc/cni/")
    cni_back_image = models.ImageField(upload_to="kyc/cni/")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    rejection_reason = models.TextField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    validated_at = models.DateTimeField(null=True, blank=True)
    validated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="validated_kycs",
    )

    class Meta:
        indexes = [
            models.Index(fields=["user"], name="idx_kyc_user_id"),
            models.Index(fields=["status"], name="idx_kyc_status"),
        ]


class Session(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")
    device_id = models.CharField(max_length=255, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_active"], name="idx_sessions_user_active"),
            models.Index(fields=["expires_at"], name="idx_sessions_expires"),
        ]
