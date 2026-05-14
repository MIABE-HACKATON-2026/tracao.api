from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from ..models.system import SyncQueue, Notification, TraceabilityLog, FraudAlert, BlockchainRecord, QRCode
from ..models.batches import Batch
from ..models.parcels import Parcel
from ..serializers.system import (
    SyncQueueSerializer, NotificationSerializer, TraceabilityLogSerializer, 
    FraudAlertSerializer, BlockchainRecordSerializer
)
from ..services.traceability_service import TraceabilityService

class SyncQueueViewSet(viewsets.ModelViewSet):
    serializer_class = SyncQueueSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return SyncQueue.objects.filter(agent=self.request.user)

    def perform_create(self, serializer):
        serializer.save(agent=self.request.user)

    @action(detail=False, methods=['post'], url_path='upload-batch')
    def upload_batch(self, request):
        items_data = request.data.get('items', [])
        results = []
        for item in items_data:
            serializer = SyncQueueSerializer(data=item)
            if serializer.is_valid():
                serializer.save(agent=self.request.user)
                results.append({"local_id": item.get('local_id'), "status": "pending"})
            else:
                results.append({"local_id": item.get('local_id'), "status": "error", "errors": serializer.errors})
        
        return Response(results, status=status.HTTP_201_CREATED)

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.read = True
        notif.save()
        return Response(NotificationSerializer(notif).data)

class TraceabilityViewSet(viewsets.ViewSet):
    permission_classes = (permissions.AllowAny,)

    @action(detail=False, methods=['get'], url_path='scan/(?P<qr_data>[^/.]+)')
    def scan(self, request, qr_data=None):
        try:
            qr = QRCode.objects.get(qr_data=qr_data)
            batch = qr.batch
            history = TraceabilityService.get_value_chain(batch)
            return Response(history)
        except QRCode.DoesNotExist:
            return Response({"error": "Invalid QR Code"}, status=status.HTTP_404_NOT_FOUND)

class FraudAlertViewSet(viewsets.ModelViewSet):
    serializer_class = FraudAlertSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return FraudAlert.objects.select_related('user', 'resolved_by').order_by('-created_at')
        return FraudAlert.objects.filter(user=self.request.user).select_related('user', 'resolved_by').order_by('-created_at')

    @action(detail=True, methods=['post'], url_path='resolve')
    def resolve_alert(self, request, pk=None):
        alert = self.get_object()
        alert.status = 'resolved'
        alert.resolution_comment = request.data.get('comment')
        alert.resolved_by = request.user
        from django.utils import timezone
        alert.resolved_at = timezone.now()
        alert.save()
        return Response(FraudAlertSerializer(alert).data)

class BlockchainRecordViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BlockchainRecordSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return BlockchainRecord.objects.all().order_by('-created_at')

class ReportViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    @action(detail=False, methods=['get'], url_path='eudr-compliance/(?P<batch_id>[^/.]+)')
    def eudr_report(self, request, batch_id=None):
        try:
            batch = Batch.objects.select_related('parcel').get(id=batch_id)
            
            transports = batch.transports.count()
            transformations = batch.used_in_transformations.count()
            has_validated_parcel = batch.parcel.status == 'approved'
            
            traceability_score = 0
            if has_validated_parcel:
                traceability_score += 25
            if transports > 0:
                traceability_score += 25
            if transformations > 0:
                traceability_score += 25
            if batch.status in ['locked', 'closed']:
                traceability_score += 25
            
            report = {
                "batch_id": batch.unique_code,
                "origin": batch.parcel.name if batch.parcel else None,
                "gps_polygon": batch.parcel.gps_coordinates if batch.parcel else None,
                "is_forest_free": has_validated_parcel,
                "traceability_score": traceability_score,
                "total_transports": transports,
                "total_transformations": transformations,
                "compliant": traceability_score >= 75
            }
            return Response(report)
        except Batch.DoesNotExist:
            return Response({"error": "Batch not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], url_path='statistics/production')
    def production_stats(self, request):
        # Aggregated stats
        total_batches = Batch.objects.count()
        total_parcels = Parcel.objects.count()
        return Response({
            "total_batches": total_batches,
            "total_parcels": total_parcels
        })
