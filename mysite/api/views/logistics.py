from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction

from ..models.supply_chain import Transport, Transformation, TransformationInput, TransformationOutput
from ..serializers.logistics import TransportSerializer, TransformationSerializer

class TransportViewSet(viewsets.ModelViewSet):
    serializer_class = TransportSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Transport.objects.all()

    def perform_create(self, serializer):
        serializer.save(assigned_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='confirm-departure')
    def confirm_departure(self, request, pk=None):
        transport = self.get_object()
        transport.status = 'in_progress'
        from django.utils import timezone
        transport.departure_date = timezone.now()
        transport.save()
        return Response(TransportSerializer(transport).data)

    @action(detail=True, methods=['post'], url_path='confirm-delivery')
    def confirm_delivery(self, request, pk=None):
        transport = self.get_object()
        transport.status = 'completed'
        from django.utils import timezone
        transport.arrival_date = timezone.now()
        transport.save()
        return Response(TransportSerializer(transport).data)

class TransformationViewSet(viewsets.ModelViewSet):
    serializer_class = TransformationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Transformation.objects.all()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='add-input')
    def add_input(self, request, pk=None):
        transfo = self.get_object()
        batch_id = request.data.get('batch_id')
        TransformationInput.objects.create(transformation=transfo, batch_id=batch_id)
        return Response(TransformationSerializer(transfo).data)

    @action(detail=True, methods=['post'], url_path='add-output')
    def add_output(self, request, pk=None):
        transfo = self.get_object()
        batch_id = request.data.get('batch_id')
        TransformationOutput.objects.create(transformation=transfo, batch_id=batch_id)
        return Response(TransformationSerializer(transfo).data)

    @action(detail=True, methods=['post'], url_path='lock')
    def lock_transformation(self, request, pk=None):
        transfo = self.get_object()
        transfo.status = 'locked'
        transfo.save()
        return Response(TransformationSerializer(transfo).data)
