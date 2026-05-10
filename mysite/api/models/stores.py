import uuid
from django.db import models
from .auth import User

class Store(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_stores')
    name = models.CharField(max_length=255)
    legal_document = models.FileField(upload_to='stores/docs/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    validated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='validated_stores')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user'], name='idx_store_user_id'),
            models.Index(fields=['status'], name='idx_store_status'),
        ]

    def __str__(self):
        return self.name

class StoreMember(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='store_memberships')
    role = models.CharField(max_length=50, default='gestionnaire')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('store', 'user')
        indexes = [
            models.Index(fields=['store'], name='idx_store_members_store'),
            models.Index(fields=['user'], name='idx_store_members_user'),
        ]

class StoreAgent(models.Model):
    ROLE_CHOICES = [
        ('inspecteur', 'Inspecteur'),
        ('agent_terrain', 'Agent de terrain'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='agents')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='store_agent_roles')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('store', 'user')
        indexes = [
            models.Index(fields=['store'], name='idx_store_agents_store'),
        ]
