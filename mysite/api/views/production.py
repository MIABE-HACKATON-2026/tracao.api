from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
import uuid

from ..models.parcels import Parcel, ParcelValidation
from ..models.batches import Batch, BatchValidation, Harvest
from ..serializers.production import (
    ParcelSerializer, ParcelValidationSerializer, 
    BatchSerializer, BatchValidationSerializer, HarvestSerializer
)
from ..services.gis_service import GISService
from ..permissions import IsFarmer, IsStoreOrAdmin, IsOwnerOrAdmin

class ParcelViewSet(viewsets.ModelViewSet):
    serializer_class = ParcelSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        queryset = Parcel.objects.select_related('farmer', 'validated_by')
        if user.role == 'farmer':
            return queryset.filter(farmer=user)
        elif user.role == 'store':
            return queryset.filter(farmer__store_memberships__user=user)
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        if self.request.user.role != 'farmer':
            raise permissions.ValidationError("Only farmers can create parcels")
        gps_coords = self.request.data.get('gps_coordinates')
        area = GISService.calculate_area(gps_coords)
        serializer.save(farmer=self.request.user, area=area, status='pending')

    def get_permissions(self):
        if self.action in ['validate_parcel', 'check_overlap']:
            return [permissions.IsAuthenticated(), IsStoreOrAdmin()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['post'], url_path='check-overlap')
    def check_overlap(self, request):
        new_coords = request.data.get('gps_coordinates')
        if not new_coords:
            return Response({"error": "Missing gps_coordinates"}, status=status.HTTP_400_BAD_REQUEST)
        
        existing_coords = Parcel.objects.filter(status='approved').values_list('gps_coordinates', flat=True)
        
        has_overlap = GISService.check_overlap(new_coords, existing_coords)
        return Response({"has_overlap": has_overlap})

    @action(detail=True, methods=['post'], url_path='validate')
    def validate_parcel(self, request, pk=None):
        parcel = self.get_object()
        
        if request.user.role not in ['store', 'admin']:
            return Response({"error": "Unauthorized to validate parcels"}, status=status.HTTP_403_FORBIDDEN)
        
        v_status = request.data.get('status')
        comment = request.data.get('comment', '')
        
        if v_status not in ['approved', 'rejected']:
            return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            parcel.status = v_status
            parcel.validated_by = request.user
            parcel.save()
            
            ParcelValidation.objects.create(
                parcel=parcel,
                inspector=request.user,
                status=v_status,
                comment=comment
            )
            
        return Response(ParcelSerializer(parcel).data)

class BatchViewSet(viewsets.ModelViewSet):
    serializer_class = BatchSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        queryset = Batch.objects.select_related('farmer', 'parcel', 'validated_by').prefetch_related('harvests')
        if user.role == 'farmer':
            return queryset.filter(farmer=user)
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        if self.request.user.role != 'farmer':
            raise permissions.ValidationError("Only farmers can create batches")
        with transaction.atomic():
            year = timezone.now().year
            last_batch = Batch.objects.select_for_update().filter(created_at__year=year).order_by('-created_at').first()
            count = (int(last_batch.unique_code.split('-')[-1]) if last_batch else 0) + 1
            unique_code = f"TRC-{year}-{count:04d}"
            serializer.save(farmer=self.request.user, unique_code=unique_code)

    @action(detail=True, methods=['post'], url_path='lock')
    def lock_batch(self, request, pk=None):
        batch = self.get_object()
        if batch.farmer != request.user and request.user.role != 'admin':
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
        if batch.status != 'approved':
            return Response({"error": "Only approved batches can be locked"}, status=status.HTTP_400_BAD_REQUEST)
        
        batch.status = 'locked'
        batch.save()
        return Response(BatchSerializer(batch).data)

class HarvestViewSet(viewsets.ModelViewSet):
    serializer_class = HarvestSerializer
    permission_classes = (permissions.IsAuthenticated, IsFarmer)

    def get_queryset(self):
        return Harvest.objects.select_related('batch').filter(batch__farmer=self.request.user).order_by('-created_at')
