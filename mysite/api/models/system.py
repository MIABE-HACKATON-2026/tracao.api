import uuid
from django.db import models
from .auth import User
from .batches import Batch
from .parcels import Parcel

class TraceabilityLog(models.Model):
    ACTION_TYPE_CHOICES = [
        ('create', 'Create'),
        ('validate', 'Validate'),
        ('reject', 'Reject'),
        ('harvest', 'Harvest'),
        ('transport', 'Transport'),
        ('transform', 'Transform'),
        ('sell', 'Sell'),
        ('fraud_alert', 'Fraud Alert'),
        ('field_activity', 'Field Activity'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='traceability_logs')
    action_type = models.CharField(max_length=50, choices=ACTION_TYPE_CHOICES)
    performed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='actions_performed')
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['batch'], name='idx_trace_batch'),
            models.Index(fields=['action_type'], name='idx_trace_action'),
            models.Index(fields=['performed_by'], name='idx_trace_performer'),
            models.Index(fields=['created_at'], name='idx_trace_created'),
        ]

class QRCode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.OneToOneField(Batch, on_delete=models.CASCADE, related_name='qr_code')
    qr_data = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['batch'], name='idx_qr_batch'),
        ]

class BlockchainRecord(models.Model):
    ENTITY_TYPE_CHOICES = [
        ('batch', 'Batch'),
        ('validation', 'Validation'),
        ('transaction', 'Transaction'),
        ('transformation', 'Transformation'),
        ('transport', 'Transport'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity_type = models.CharField(max_length=50, choices=ENTITY_TYPE_CHOICES)
    entity_id = models.UUIDField(help_text="ID de l'entité concernée")
    hash = models.CharField(max_length=255, help_text="SHA-256 des données de l'entité")
    tx_hash = models.CharField(max_length=255, null=True, blank=True)
    chain = models.CharField(max_length=100, null=True, blank=True)
    block_number = models.BigIntegerField(null=True, blank=True)
    anchored_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['entity_type', 'entity_id'], name='idx_bc_entity'),
            models.Index(fields=['tx_hash'], name='idx_bc_tx_hash'),
            models.Index(fields=['hash'], name='idx_bc_hash'),
        ]

class FraudAlert(models.Model):
    TYPE_CHOICES = [
        ('gps_conflict', 'GPS Conflict'),
        ('duplicate', 'Duplicate'),
        ('anomaly', 'Anomaly'),
        ('multi_account', 'Multi Account'),
        ('production_excess', 'Production Excess'),
        ('transport_anomaly', 'Transport Anomaly'),
        ('transformation_anomaly', 'Transformation Anomaly'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fraud_alerts')
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True, related_name='fraud_alerts')
    parcel = models.ForeignKey(Parcel, on_delete=models.SET_NULL, null=True, blank=True, related_name='fraud_alerts')
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    score = models.FloatField(help_text="0-100 — 70+ = élevé")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    resolution_comment = models.TextField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_frauds')
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user'], name='idx_fraud_user'),
            models.Index(fields=['batch'], name='idx_fraud_batch'),
            models.Index(fields=['parcel'], name='idx_fraud_parcel'),
            models.Index(fields=['status'], name='idx_fraud_status'),
            models.Index(fields=['status', 'score'], name='idx_fraud_status_score'),
        ]

class Notification(models.Model):
    TYPE_CHOICES = [
        ('validation', 'Validation'),
        ('rejection', 'Rejection'),
        ('transaction', 'Transaction'),
        ('transport', 'Transport'),
        ('fraud', 'Fraud'),
        ('transformation', 'Transformation'),
        ('security', 'Security'),
        ('system', 'System'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    message = models.TextField()
    read = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'read'], name='idx_notif_user_unread'),
            models.Index(fields=['created_at'], name='idx_notif_created'),
        ]

class SyncQueue(models.Model):
    ACTION_TYPE_CHOICES = [
        ('create_farmer', 'Create Farmer'),
        ('create_parcel', 'Create Parcel'),
        ('create_batch', 'Create Batch'),
        ('harvest', 'Harvest'),
        ('kyc_capture', 'KYC Capture'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('synced', 'Synced'),
        ('conflict', 'Conflict'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sync_queue_items')
    action_type = models.CharField(max_length=50, choices=ACTION_TYPE_CHOICES)
    payload = models.JSONField()
    local_id = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    conflict_reason = models.TextField(null=True, blank=True)
    created_locally_at = models.DateTimeField()
    synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('agent', 'local_id')
        indexes = [
            models.Index(fields=['agent'], name='idx_sync_agent'),
            models.Index(fields=['status'], name='idx_sync_status'),
        ]
