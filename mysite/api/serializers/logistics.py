from rest_framework import serializers
from ..models.supply_chain import (
    TransporterRegistry, Transport, Transformation, 
    TransformationInput, TransformationOutput
)
from .auth import UserSerializer
from .production import BatchSerializer

class TransporterRegistrySerializer(serializers.ModelSerializer):
    class Meta:
        model = TransporterRegistry
        fields = ('id', 'phone', 'user', 'created_by', 'status', 'created_at')
        read_only_fields = ('id', 'created_by', 'created_at')

class TransportSerializer(serializers.ModelSerializer):
    batch_details = BatchSerializer(source='batch', read_only=True)
    
    class Meta:
        model = Transport
        fields = (
            'id', 'batch', 'batch_details', 'transporter_registry', 
            'assigned_by', 'from_location', 'to_location', 
            'departure_date', 'arrival_date', 'status', 'created_at'
        )
        read_only_fields = ('id', 'assigned_by', 'created_at')

class TransformationInputSerializer(serializers.ModelSerializer):
    batch_details = BatchSerializer(source='batch', read_only=True)
    class Meta:
        model = TransformationInput
        fields = ('id', 'transformation', 'batch', 'batch_details')

class TransformationOutputSerializer(serializers.ModelSerializer):
    batch_details = BatchSerializer(source='batch', read_only=True)
    class Meta:
        model = TransformationOutput
        fields = ('id', 'transformation', 'batch', 'batch_details')

class TransformationSerializer(serializers.ModelSerializer):
    inputs = TransformationInputSerializer(many=True, read_only=True)
    outputs = TransformationOutputSerializer(many=True, read_only=True)
    
    class Meta:
        model = Transformation
        fields = (
            'id', 'created_by', 'transformer', 'execution_type', 
            'status', 'created_at', 'inputs', 'outputs'
        )
        read_only_fields = ('id', 'created_by', 'created_at')
