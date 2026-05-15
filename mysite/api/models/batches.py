import uuid
from django.db import models
from .auth import User
from .parcels import Parcel

class Batch(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('locked', 'Locked'),
        ('closed', 'Closed'),
    ]
    CROP_CHOICES = [
        ('cacao', 'Cacao'),
        ('café', 'Café'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='batches')
    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE, related_name='batches')
    season = models.CharField(max_length=50, help_text="ex: 2025-2026")
    crop_type = models.CharField(max_length=20, choices=CROP_CHOICES)
    estimated_quantity = models.FloatField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    unique_code = models.CharField(max_length=50, unique=True, help_text="format TRC-YYYY-XXXX")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    validated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='validated_batches')
    store = models.ForeignKey('api.Store', on_delete=models.SET_NULL, null=True, blank=True, related_name='batches')

    class Meta:
        unique_together = ('parcel', 'season', 'crop_type')
        indexes = [
            models.Index(fields=['farmer'], name='idx_batches_farmer'),
            models.Index(fields=['parcel'], name='idx_batches_parcel'),
            models.Index(fields=['status'], name='idx_batches_status'),
        ]

    def __str__(self):
        return f"{self.unique_code} - {self.crop_type}"

class BatchValidation(models.Model):
    STATUS_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='validations')
    validator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='validated_batch_records')
    comment = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['batch'], name='idx_batch_val_batch'),
        ]

class Harvest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='harvests')
    quantity = models.FloatField()
    harvest_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['batch'], name='idx_harvests_batch'),
            models.Index(fields=['harvest_date'], name='idx_harvests_date'),
        ]

class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='transactions')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales')
    quantity = models.FloatField()
    price = models.FloatField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['batch'], name='idx_transactions_batch'),
            models.Index(fields=['buyer'], name='idx_transactions_buyer'),
            models.Index(fields=['seller'], name='idx_transactions_seller'),
            models.Index(fields=['status'], name='idx_transactions_status'),
        ]
