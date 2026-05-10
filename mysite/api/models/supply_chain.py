import uuid
from django.db import models
from django.core.exceptions import ValidationError
from .auth import User
from .batches import Batch

class TransporterRegistry(models.Model):
    STATUS_CHOICES = [
        ('invited', 'Invited'),
        ('active', 'Active'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=20, unique=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='transporter_profile')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registered_transporters')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='invited')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['phone'], name='idx_transporter_phone'),
            models.Index(fields=['user'], name='idx_transporter_user'),
        ]

    def __str__(self):
        return self.phone

class Transport(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='transports')
    transporter_registry = models.ForeignKey(TransporterRegistry, on_delete=models.CASCADE, related_name='transports')
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_transports')
    from_location = models.CharField(max_length=255)
    to_location = models.CharField(max_length=255)
    departure_date = models.DateTimeField(null=True, blank=True)
    arrival_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['batch'], name='idx_transports_batch'),
            models.Index(fields=['transporter_registry'], name='idx_transports_transporter'),
            models.Index(fields=['status'], name='idx_transports_status'),
        ]

class Transformation(models.Model):
    EXECUTION_TYPE_CHOICES = [
        ('self', 'Self'),
        ('third_party', 'Third Party'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('locked', 'Locked'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_transformations')
    transformer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='executed_transformations')
    execution_type = models.CharField(max_length=20, choices=EXECUTION_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['created_by'], name='idx_transfo_creator'),
            models.Index(fields=['transformer'], name='idx_transfo_transformer'),
        ]

class TransformationInput(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transformation = models.ForeignKey(Transformation, on_delete=models.CASCADE, related_name='inputs')
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='used_in_transformations')

    class Meta:
        unique_together = ('transformation', 'batch')
        indexes = [
            models.Index(fields=['transformation'], name='idx_transfo_inputs_transfo'),
        ]

class TransformationOutput(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transformation = models.ForeignKey(Transformation, on_delete=models.CASCADE, related_name='outputs')
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='produced_by_transformations')

    class Meta:
        unique_together = ('transformation', 'batch')
        indexes = [
            models.Index(fields=['transformation'], name='idx_transfo_outputs_transfo'),
        ]

class OperatorAssignment(models.Model):
    OPERATOR_TYPE_CHOICES = [
        ('transporteur', 'Transporteur'),
        ('transformateur', 'Transformateur'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    operator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='operator_assignments')
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='made_assignments')
    operator_type = models.CharField(max_length=20, choices=OPERATOR_TYPE_CHOICES)
    transport = models.ForeignKey(Transport, on_delete=models.CASCADE, null=True, blank=True, related_name='operator_assignments')
    transformation = models.ForeignKey(Transformation, on_delete=models.CASCADE, null=True, blank=True, related_name='operator_assignments')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['operator'], name='idx_op_assign_operator'),
            models.Index(fields=['transport'], name='idx_op_assign_transport'),
            models.Index(fields=['transformation'], name='idx_op_assign_transformation'),
        ]

    def clean(self):
        if not self.transport and not self.transformation:
            raise ValidationError("Exactly one of transport or transformation must be set.")
        if self.transport and self.transformation:
            raise ValidationError("Only one of transport or transformation can be set.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
