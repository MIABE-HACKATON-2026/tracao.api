import uuid
from django.db import models
from .auth import User

class Parcel(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='parcels')
    name = models.CharField(max_length=255)
    gps_coordinates = models.JSONField(help_text="JSON polygon — minimum 3 points")
    area = models.FloatField(help_text="Calculé automatiquement en hectares", null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    validated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='validated_parcels')

    class Meta:
        indexes = [
            models.Index(fields=['farmer'], name='idx_parcels_farmer'),
            models.Index(fields=['status'], name='idx_parcels_status'),
        ]

    def __str__(self):
        return f"{self.name} ({self.farmer.phone})"

class ParcelValidation(models.Model):
    STATUS_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE, related_name='validations')
    inspector = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inspected_parcels')
    comment = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['parcel'], name='idx_parcel_val_parcel'),
        ]
