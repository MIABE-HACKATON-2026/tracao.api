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
        queryset = Parcel.objects.select_related('farmer', 'validated_by', 'store').order_by('-created_at')
        if user.role == 'farmer':
            return queryset.filter(farmer=user)
        elif user.role == 'store':
            # Filter by the store the user belongs to
            return queryset.filter(store__members__user=user)
        return queryset

    def perform_create(self, serializer):
        if self.request.user.role != 'farmer':
            raise permissions.ValidationError("Only farmers can create parcels")
        gps_coords = self.request.data.get('gps_coordinates', [])
        area = 0.0
        if gps_coords and len(gps_coords) > 0:
            area = GISService.calculate_area(gps_coords)
            
        farmer = self.request.user
        
        from ..models.stores import Store, StoreMember
        from ..models.system import Notification

        closest_store = None
        # Try to find store by existing membership
        membership = StoreMember.objects.filter(user=farmer).first()
        if membership:
            closest_store = membership.store
        else:
            # If no membership, find closest store and create membership
            lon, lat = None, None
            if gps_coords and len(gps_coords) > 0:
                lon, lat = gps_coords[0][0], gps_coords[0][1]
            elif farmer.longitude and farmer.latitude:
                lon, lat = farmer.longitude, farmer.latitude
                
            if lon is not None and lat is not None:
                closest_store = GISService.find_closest_store(lon, lat)
                
            if not closest_store:
                closest_store = Store.objects.first()
                
            if closest_store:
                StoreMember.objects.create(
                    store=closest_store,
                    user=farmer,
                    role='farmer',
                    status='active'
                )
        
        parcel = serializer.save(farmer=farmer, area=area, status='pending', store=closest_store)
        
        # Notify store manager
        if closest_store and closest_store.user:
            Notification.objects.create(
                user=closest_store.user,
                type='validation',
                message=f"Nouvelle parcelle « {parcel.name} » soumise par {farmer.get_full_name() or farmer.phone} pour validation."
            )

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
            
            # Notify farmer
            status_text = "validée" if v_status == 'approved' else "rejetée"
            Notification.objects.create(
                user=parcel.farmer,
                type='validation' if v_status == 'approved' else 'rejection',
                message=f"Votre parcelle « {parcel.name} » a été {status_text}."
            )
            
        return Response(ParcelSerializer(parcel).data)

class BatchViewSet(viewsets.ModelViewSet):
    serializer_class = BatchSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        queryset = Batch.objects.select_related('farmer', 'parcel', 'validated_by', 'store').prefetch_related('harvests').order_by('-created_at')
        if user.role == 'farmer':
            return queryset.filter(farmer=user)
        elif user.role == 'store':
            return queryset.filter(store__members__user=user)
        return queryset

    def perform_create(self, serializer):
        if self.request.user.role != 'farmer':
            raise permissions.ValidationError("Only farmers can create batches")
            
        farmer = self.request.user
        
        from ..models.stores import Store, StoreMember
        from ..models.system import Notification

        closest_store = None
        membership = StoreMember.objects.filter(user=farmer).first()
        if membership:
            closest_store = membership.store
        else:
            if farmer.longitude and farmer.latitude:
                closest_store = GISService.find_closest_store(farmer.longitude, farmer.latitude)
            if not closest_store:
                closest_store = Store.objects.first()
            if closest_store:
                StoreMember.objects.create(
                    store=closest_store,
                    user=farmer,
                    role='farmer',
                    status='active'
                )
                
        with transaction.atomic():
            year = timezone.now().year
            last_batch = Batch.objects.select_for_update().filter(created_at__year=year).order_by('-created_at').first()
            count = (int(last_batch.unique_code.split('-')[-1]) if last_batch else 0) + 1
            unique_code = f"TRC-{year}-{count:04d}"
            batch = serializer.save(farmer=farmer, unique_code=unique_code, status='pending', store=closest_store)

            # Notify store manager
            if closest_store and closest_store.user:
                Notification.objects.create(
                    user=closest_store.user,
                    type='validation',
                    message=f"Nouveau lot « {batch.unique_code} » soumis par {farmer.get_full_name() or farmer.phone}."
                )

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

    @action(detail=True, methods=['post'], url_path='validate')
    def validate_batch(self, request, pk=None):
        batch = self.get_object()

        if request.user.role not in ['agent', 'store', 'admin']:
            return Response({"error": "Unauthorized to validate batches"}, status=status.HTTP_403_FORBIDDEN)

        v_status = request.data.get('status')
        comment = request.data.get('comment', '')

        if v_status not in ['approved', 'rejected']:
            return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            batch.status = v_status
            batch.validated_by = request.user
            batch.save()

            BatchValidation.objects.create(
                batch=batch,
                inspector=request.user,
                status=v_status,
                comment=comment
            )

            # Notify farmer
            status_text = "validé" if v_status == 'approved' else "rejeté"
            Notification.objects.create(
                user=batch.farmer,
                type='validation' if v_status == 'approved' else 'rejection',
                message=f"Votre lot « {batch.unique_code} » a été {status_text}."
            )

        return Response(BatchSerializer(batch).data)

class HarvestViewSet(viewsets.ModelViewSet):
    serializer_class = HarvestSerializer
    permission_classes = (permissions.IsAuthenticated, IsFarmer)

    def get_queryset(self):
        return Harvest.objects.select_related('batch').filter(batch__farmer=self.request.user).order_by('-created_at')
