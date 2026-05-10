from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
import uuid

from ..models.parcels import Parcel, ParcelValidation
from ..models.batches import Batch, BatchValidation, Harvest
from ..serializers.production import (
    ParcelSerializer, ParcelValidationSerializer, 
    BatchSerializer, BatchValidationSerializer, HarvestSerializer
)
from ..services.gis_service import GISService

class ParcelViewSet(viewsets.ModelViewSet):
    serializer_class = ParcelSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        if user.role == 'farmer':
            return Parcel.objects.filter(farmer=user)
        elif user.role == 'coop':
            return Parcel.objects.filter(farmer__coop_members__cooperative__manager=user)
        return Parcel.objects.all()

    def perform_create(self, serializer):
        gps_coords = self.request.data.get('gps_coordinates')
        area = GISService.calculate_area(gps_coords)
        serializer.save(farmer=self.request.user, area=area, status='pending')

    @action(detail=False, methods=['post'], url_path='check-overlap')
    def check_overlap(self, request):
        new_coords = request.data.get('gps_coordinates')
        if not new_coords:
            return Response({"error": "Missing gps_coordinates"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get all approved parcels to check against
        existing_coords = Parcel.objects.filter(status='approved').values_list('gps_coordinates', flat=True)
        
        has_overlap = GISService.check_overlap(new_coords, existing_coords)
        return Response({"has_overlap": has_overlap})

    @action(detail=True, methods=['post'], url_path='validate')
    def validate_parcel(self, request, pk=None):
        parcel = self.get_object()
        v_status = request.data.get('status') # 'approved' or 'rejected'
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
        if user.role == 'farmer':
            return Batch.objects.filter(farmer=user)
        return Batch.objects.all()

    def perform_create(self, serializer):
        # Generate unique code TRC-YYYY-XXXX
        year = 2026 # Should be dynamic
        count = Batch.objects.filter(created_at__year=year).count() + 1
        unique_code = f"TRC-{year}-{count:04d}"
        serializer.save(farmer=self.request.user, unique_code=unique_code)

    @action(detail=True, methods=['post'], url_path='lock')
    def lock_batch(self, request, pk=None):
        batch = self.get_object()
        if batch.status != 'approved':
            return Response({"error": "Only approved batches can be locked"}, status=status.HTTP_400_BAD_REQUEST)
        
        batch.status = 'locked'
        batch.save()
        return Response(BatchSerializer(batch).data)

class HarvestViewSet(viewsets.ModelViewSet):
    serializer_class = HarvestSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Harvest.objects.filter(batch__farmer=self.request.user)
