"""
Admin views — scopées par sub_role.
  - SuperAdmin   : accès total
  - Gouvernement : lecture nationale + exports réglementaires
  - Certificateur: lots assignés uniquement
"""
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models.auth import User, KYCRecord, Session
from ..models.stores import Store
from ..models.batches import Batch, Harvest, Transaction
from ..models.parcels import Parcel
from ..models.system import FraudAlert, BlockchainRecord, TraceabilityLog
from ..serializers.auth import UserSerializer, KYCRecordSerializer
from ..serializers.production import BatchSerializer
from ..serializers.commerce import TransactionSerializer
from ..serializers.system import (
    FraudAlertSerializer, BlockchainRecordSerializer, TraceabilityLogSerializer
)
from ..permissions import IsSuperAdmin, IsGouvernement, IsCertificateur, IsAnyAdmin


# ─── Super Admin ──────────────────────────────────────────────────────────────

class SuperAdminDashboardView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        user_stats = User.objects.values('role', 'status').annotate(count=Count('id'))
        batch_stats = Batch.objects.values('status').annotate(count=Count('id'))
        tx_today = Transaction.objects.filter(created_at__gte=today_start).aggregate(
            count=Count('id'), total=Sum('price')
        )
        tx_month = Transaction.objects.filter(created_at__gte=month_start).aggregate(
            count=Count('id'), total=Sum('price')
        )
        critical_alerts = FraudAlert.objects.filter(status='open', score__gt=70).count()
        blockchain_by_type = BlockchainRecord.objects.values('entity_type').annotate(count=Count('id'))

        return Response({
            'users': list(user_stats),
            'batches': list(batch_stats),
            'transactions': {
                'today': {'count': tx_today['count'] or 0, 'total': tx_today['total'] or 0},
                'month': {'count': tx_month['count'] or 0, 'total': tx_month['total'] or 0},
            },
            'critical_alerts': critical_alerts,
            'blockchain': list(blockchain_by_type),
        })


class AdminUserViewSet(viewsets.ModelViewSet):
    """Super Admin: gestion totale des utilisateurs."""
    permission_classes = [IsSuperAdmin]
    serializer_class = UserSerializer

    def get_queryset(self):
        qs = User.objects.select_related().order_by('-date_joined')
        role = self.request.query_params.get('role')
        status_filter = self.request.query_params.get('status')
        if role:
            qs = qs.filter(role=role)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def perform_create(self, serializer):
        password = self.request.data.get('password', 'Tracao2026!')
        user = serializer.save()
        user.set_password(password)
        user.kyc_status = 'approved'  # Les admins/utilisateurs créés par admin sont approuvés par défaut
        user.save()

    @action(detail=True, methods=['post'], url_path='suspend')
    def suspend(self, request, pk=None):
        user = self.get_object()
        user.status = 'suspended'
        user.is_active = False
        user.save()
        return Response({'message': 'Compte suspendu', 'status': 'suspended', 'is_active': False})

    @action(detail=True, methods=['post'], url_path='reactivate')
    def reactivate(self, request, pk=None):
        user = self.get_object()
        user.status = 'active'
        user.is_active = True
        user.save()
        return Response({'message': 'Compte réactivé', 'status': 'active', 'is_active': True})


class AdminStoreViewSet(viewsets.ModelViewSet):
    """Super Admin: gestion des magasins (coopératives)."""
    permission_classes = [IsSuperAdmin]
    serializer_class = UserSerializer # Initialement on peut utiliser UserSerializer si on gère les utilisateurs de type store

    def get_queryset(self):
        # On peut filtrer les utilisateurs ayant le rôle 'store'
        return User.objects.filter(role='store').order_by('-date_joined')

    @action(detail=True, methods=['post'], url_path='suspend')
    def suspend(self, request, pk=None):
        user = self.get_object()
        user.status = 'suspended'
        user.is_active = False
        user.save()
        return Response({'message': 'Magasin suspendu', 'status': 'suspended'})

    @action(detail=True, methods=['post'], url_path='reactivate')
    def reactivate(self, request, pk=None):
        user = self.get_object()
        user.status = 'active'
        user.is_active = True
        user.save()
        return Response({'message': 'Magasin réactivé', 'status': 'active'})


class AdminKYCViewSet(viewsets.ReadOnlyModelViewSet):
    """Super Admin: validation KYC."""
    permission_classes = [IsSuperAdmin]
    serializer_class = KYCRecordSerializer

    def get_queryset(self):
        status_filter = self.request.query_params.get('status', 'pending')
        return KYCRecord.objects.filter(status=status_filter).select_related('user').order_by('-submitted_at')

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        kyc = self.get_object()
        kyc.status = 'approved'
        kyc.validated_by = request.user
        kyc.validated_at = timezone.now()
        kyc.save()
        kyc.user.kyc_status = 'approved'
        kyc.user.save()
        return Response({'message': 'KYC approuvé'})

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        reason = request.data.get('reason')
        if not reason:
            return Response({'error': 'Un motif de rejet est obligatoire'}, status=status.HTTP_400_BAD_REQUEST)
        kyc = self.get_object()
        kyc.status = 'rejected'
        kyc.rejection_reason = reason
        kyc.validated_by = request.user
        kyc.validated_at = timezone.now()
        kyc.save()
        kyc.user.kyc_status = 'rejected'
        kyc.user.save()
        return Response({'message': 'KYC rejeté'})


class AdminBatchViewSet(viewsets.ModelViewSet):
    """Super Admin: gestion de tous les lots."""
    permission_classes = [IsSuperAdmin]
    serializer_class = BatchSerializer

    def get_queryset(self):
        return Batch.objects.select_related('farmer', 'parcel', 'store').order_by('-created_at')

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        batch = self.get_object()
        batch.status = 'approved'
        batch.save()
        return Response({'message': 'Lot approuvé', 'status': 'approved'})

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        batch = self.get_object()
        batch.status = 'rejected'
        batch.save()
        return Response({'message': 'Lot rejeté', 'status': 'rejected'})


class AdminTransactionViewSet(viewsets.ModelViewSet):
    """Super Admin: gestion de toutes les transactions."""
    permission_classes = [IsSuperAdmin]
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return Transaction.objects.select_related('batch', 'buyer', 'seller').order_by('-created_at')

    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.status == 'completed':
            raise serializers.ValidationError("Impossible de modifier une transaction validée.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.status == 'completed':
            raise serializers.ValidationError("Impossible de supprimer une transaction validée.")
        instance.delete()

    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        tx = self.get_object()
        if tx.status != 'pending':
            return Response({'error': 'Seules les transactions en attente peuvent être validées.'}, status=400)
        tx.status = 'completed'
        tx.save()
        return Response({'message': 'Transaction validée', 'status': 'completed'})


# ─── Gouvernement ─────────────────────────────────────────────────────────────

class GovDashboardView(APIView):
    permission_classes = [IsGouvernement]

    def get(self, request):
        production = (
            Batch.objects.values('crop_type', 'parcel__city')
            .annotate(count=Count('id'), total_qty=Sum('estimated_quantity'))
        )
        surfaces = Parcel.objects.filter(status='approved').aggregate(total=Sum('area'))
        coop_count = User.objects.filter(role='store', status='active').count()
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        export_volume = Transaction.objects.filter(
            created_at__gte=month_start, status='completed'
        ).aggregate(total=Sum('price'))

        return Response({
            'production': list(production),
            'total_surface_ha': surfaces['total'] or 0,
            'active_cooperatives': coop_count,
            'monthly_export_volume': export_volume['total'] or 0,
        })


class GovProductionStatsView(APIView):
    permission_classes = [IsGouvernement]

    def get(self, request):
        season = request.query_params.get('season')
        crop_type = request.query_params.get('crop_type')
        region = request.query_params.get('region')

        harvests_qs = Harvest.objects.select_related('batch__parcel')
        batches_qs = Batch.objects.select_related('parcel')

        if season:
            harvests_qs = harvests_qs.filter(batch__season=season)
            batches_qs = batches_qs.filter(season=season)
        if crop_type:
            harvests_qs = harvests_qs.filter(batch__crop_type=crop_type)
            batches_qs = batches_qs.filter(crop_type=crop_type)

        real_by_crop = harvests_qs.values('batch__crop_type').annotate(total=Sum('quantity'))
        estimated_by_crop = batches_qs.values('crop_type').annotate(total=Sum('estimated_quantity'))
        surface_by_region = (
            Parcel.objects.values('city', 'country')
            .annotate(total_area=Sum('area'))
            .order_by('-total_area')
        )
        farmers_by_city = (
            User.objects.filter(role='farmer')
            .values('city')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        return Response({
            'real_production': list(real_by_crop),
            'estimated_production': list(estimated_by_crop),
            'surface_by_region': list(surface_by_region),
            'farmers_density': list(farmers_by_city),
        })


class GovEUDRView(APIView):
    permission_classes = [IsGouvernement]

    def get(self, request):
        certifiable = Batch.objects.filter(status__in=['approved', 'locked']).select_related('parcel')
        results = []
        for batch in certifiable[:100]:
            has_gps = bool(batch.parcel and batch.parcel.gps_coordinates)
            bc = BlockchainRecord.objects.filter(entity_id=batch.id, entity_type='batch').first()
            log_count = batch.traceability_logs.count()
            results.append({
                'batch_code': batch.unique_code,
                'crop_type': batch.crop_type,
                'has_gps': has_gps,
                'blockchain_anchored': bool(bc),
                'blockchain_hash': bc.hash if bc else None,
                'anchored_at': bc.anchored_at if bc else None,
                'traceability_events': log_count,
                'eudr_ready': has_gps and bool(bc) and log_count >= 2,
            })
        return Response({'lots': results, 'total': certifiable.count()})


class GovAuditView(APIView):
    permission_classes = [IsGouvernement]

    def get(self, request):
        alerts = FraudAlert.objects.select_related('user', 'batch', 'parcel').order_by('-created_at')[:200]
        logs = TraceabilityLog.objects.filter(
            action_type='fraud_alert'
        ).select_related('performed_by', 'batch').order_by('-created_at')[:100]
        return Response({
            'fraud_alerts': FraudAlertSerializer(alerts, many=True).data,
            'fraud_logs': TraceabilityLogSerializer(logs, many=True).data,
        })


# ─── Certificateur ────────────────────────────────────────────────────────────

class CertDashboardView(APIView):
    permission_classes = [IsCertificateur]

    def get(self, request):
        certifiable_batches = Batch.objects.filter(status__in=['approved', 'locked'])
        certified_count = BlockchainRecord.objects.filter(entity_type='batch').count()
        certified_parcels = Parcel.objects.filter(status='approved').count()

        return Response({
            'certifiable_batches': certifiable_batches.count(),
            'certified_blockchain': certified_count,
            'certified_parcels': certified_parcels,
            'by_crop': list(
                certifiable_batches.values('crop_type').annotate(count=Count('id'))
            ),
        })


class CertBatchViewSet(viewsets.ReadOnlyModelViewSet):
    """Certificateur: lots à certifier (approuvés ou verrouillés)."""
    permission_classes = [IsCertificateur]

    def get_queryset(self):
        return (
            Batch.objects.filter(status__in=['approved', 'locked'])
            .select_related('farmer', 'parcel', 'store')
            .order_by('-created_at')
        )

    def list(self, request):
        qs = self.get_queryset()
        crop = request.query_params.get('crop_type')
        if crop:
            qs = qs.filter(crop_type=crop)

        results = []
        for batch in qs[:200]:
            bc = BlockchainRecord.objects.filter(entity_id=batch.id, entity_type='batch').first()
            total_harvested = batch.harvests.aggregate(total=Sum('quantity'))['total'] or 0
            results.append({
                'id': str(batch.id),
                'unique_code': batch.unique_code,
                'crop_type': batch.crop_type,
                'season': batch.season,
                'status': batch.status,
                'estimated_quantity': batch.estimated_quantity,
                'total_harvested': total_harvested,
                'farmer': f"{batch.farmer.first_name} {batch.farmer.last_name}",
                'parcel_name': batch.parcel.name if batch.parcel else None,
                'blockchain_hash': bc.hash if bc else None,
                'tx_hash': bc.tx_hash if bc else None,
                'anchored_at': bc.anchored_at if bc else None,
                'is_blockchain_certified': bool(bc),
            })
        return Response({'results': results, 'count': qs.count()})

    @action(detail=True, methods=['post'], url_path='certify')
    def certify(self, request, pk=None):
        batch = self.get_object()
        batch.status = 'locked'
        batch.validated_by = request.user
        batch.save()
        TraceabilityLog.objects.create(
            batch=batch,
            action_type='validate',
            performed_by=request.user,
            metadata={'action': 'certification', 'certifier': str(request.user.id)}
        )
        return Response({'message': f'Lot {batch.unique_code} certifié', 'status': 'locked'})

    @action(detail=True, methods=['post'], url_path='reject')
    def reject_batch(self, request, pk=None):
        reason = request.data.get('reason')
        if not reason:
            return Response({'error': 'Un motif est obligatoire'}, status=status.HTTP_400_BAD_REQUEST)
        batch = self.get_object()
        batch.status = 'rejected'
        batch.save()
        TraceabilityLog.objects.create(
            batch=batch,
            action_type='reject',
            performed_by=request.user,
            metadata={'reason': reason}
        )
        return Response({'message': f'Lot {batch.unique_code} rejeté'})


class CertParcelViewSet(viewsets.ReadOnlyModelViewSet):
    """Certificateur: parcelles approuvées."""
    permission_classes = [IsCertificateur]

    def get_queryset(self):
        return (
            Parcel.objects.filter(status='approved')
            .select_related('farmer', 'store')
            .order_by('-updated_at')
        )

    def list(self, request):
        qs = self.get_queryset()
        results = []
        for parcel in qs[:200]:
            results.append({
                'id': str(parcel.id),
                'name': parcel.name,
                'area': parcel.area,
                'gps_coordinates': parcel.gps_coordinates,
                'status': parcel.status,
                'farmer': f"{parcel.farmer.first_name} {parcel.farmer.last_name}",
                'farmer_city': parcel.farmer.city,
                'created_at': parcel.created_at,
            })
        return Response({'results': results, 'count': qs.count()})


class CertBlockchainView(APIView):
    """Certificateur: vérification blockchain d'un lot."""
    permission_classes = [IsCertificateur]

    def get(self, request):
        entity_type = request.query_params.get('entity_type', 'batch')
        records = BlockchainRecord.objects.filter(entity_type=entity_type).order_by('-anchored_at')[:100]
        return Response(BlockchainRecordSerializer(records, many=True).data)
