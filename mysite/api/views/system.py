from django.db import models
from django.db.models import Sum
from django.db.models.functions import TruncMonth
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

class TraceabilityViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TraceabilityLogSerializer

    def get_queryset(self):
        return TraceabilityLog.objects.select_related('performed_by', 'batch').order_by('-created_at')[:100]

    @action(detail=False, methods=['get'], url_path='scan/(?P<qr_data>[^/.]+)', permission_classes=[permissions.AllowAny])
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
        user = self.request.user
        queryset = FraudAlert.objects.select_related('user', 'resolved_by', 'batch', 'parcel').order_by('-created_at')
        if user.role == 'admin':
            if user.sub_role in ['super_admin', None]:
                return queryset
            elif user.sub_role == 'gouvernement':
                return queryset
            elif user.sub_role == 'certificateur':
                return queryset.filter(batch__status__in=['approved', 'locked'])
            return queryset.none()
            
        if user.role == 'store':
            return queryset.filter(
                models.Q(batch__store__user=user) | 
                models.Q(parcel__store__user=user) |
                models.Q(user=user)
            ).distinct()
        return queryset.filter(user=user)

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
        user = self.request.user
        qs = BlockchainRecord.objects.all().order_by('-created_at')
        
        if user.role == 'admin':
            if user.sub_role == 'certificateur':
                return qs.filter(entity_type='batch')
                
        return qs

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

    @action(detail=False, methods=['get'], url_path='store-dashboard-stats')
    def store_dashboard(self, request):
        try:
            from django.utils import timezone
            from datetime import timedelta
            from ..models.stores import StoreMember
            from ..models.supply_chain import Transport

            user = request.user
            if user.role != 'store' and user.role != 'admin':
                return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

            # Get the store associated with the user
            membership = StoreMember.objects.filter(user=user).first()
            if not membership and user.role == 'store':
                return Response({"error": "No store membership found"}, status=status.HTTP_404_NOT_FOUND)
            
            store_id = membership.store_id if membership else None
            
            # Base querysets filtered by store
            parcels_qs = Parcel.objects.all()
            batches_qs = Batch.objects.all()
            transports_qs = Transport.objects.all()
            alerts_qs = FraudAlert.objects.all()
            
            if store_id:
                parcels_qs = parcels_qs.filter(store_id=store_id)
                batches_qs = batches_qs.filter(store_id=store_id)
                # Transports are linked to batches
                transports_qs = transports_qs.filter(batch__store_id=store_id)
                # Alerts are linked to batches or parcels
                alerts_qs = alerts_qs.filter(
                    models.Q(batch__store_id=store_id) | models.Q(parcel__store_id=store_id)
                )

            # 1. Monthly Evolution (last 6 months)
            six_months_ago = timezone.now() - timedelta(days=180)
            evolution = (
                batches_qs.filter(created_at__gte=six_months_ago)
                .annotate(month=TruncMonth('created_at'))
                .values('month')
                .annotate(value=Sum('estimated_quantity'))
                .order_by('month')
            )
            
            # Format evolution data for charts
            formatted_evolution = [
                {"name": item['month'].strftime('%b'), "value": item['value'] or 0}
                for item in evolution if item['month']
            ]

            # 2. Activity by Zone (City)
            zone_activity = (
                batches_qs.values('farmer__city')
                .annotate(value=Sum('estimated_quantity'))
                .order_by('-value')[:5]
            )
            
            formatted_zones = [
                {"name": item['farmer__city'] or "Inconnue", "value": item['value'] or 0}
                for item in zone_activity
            ]

            # 3. Production by Crop
            production_by_crop = (
                batches_qs.values('crop_type')
                .annotate(value=Sum('estimated_quantity'))
            )
            formatted_crops = {item['crop_type']: item['value'] or 0 for item in production_by_crop}

            # 4. Total Area
            total_area = parcels_qs.filter(status='approved').aggregate(total=Sum('area'))['total'] or 0

            # 5. Summary Counts
            stats = {
                "evolution": formatted_evolution,
                "zones": formatted_zones,
                "production_by_crop": formatted_crops,
                "total_area": total_area,
                "total_volume": batches_qs.aggregate(total=Sum('estimated_quantity'))['total'] or 0,
                "counts": {
                    "active_members": StoreMember.objects.filter(store_id=store_id, status='active').count() if store_id else 0,
                    "pending_validations": parcels_qs.filter(status='pending').count() + batches_qs.filter(status='pending').count(),
                    "active_transports": transports_qs.filter(status='in_progress').count(),
                    "open_alerts": alerts_qs.filter(status='open').count()
                }
            }
            
            return Response(stats)
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

