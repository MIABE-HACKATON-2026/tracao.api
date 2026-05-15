from rest_framework import serializers
from ..models.supply_chain import (
    TransporterRegistry, Transport, Transformation, 
    TransformationInput, TransformationOutput
)
from .auth import UserSerializer
from .production import BatchSerializer

class TransporterRegistrySerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    class Meta:
        model = TransporterRegistry
        fields = ('id', 'phone', 'user', 'user_details', 'created_by', 'status', 'created_at')
        read_only_fields = ('id', 'created_by', 'created_at')

class TransportSerializer(serializers.ModelSerializer):
    batch_details = BatchSerializer(source='batch', read_only=True)
    transporter_registry_details = TransporterRegistrySerializer(source='transporter_registry', read_only=True)
    
    class Meta:
        model = Transport
        fields = (
            'id', 'batch', 'batch_details', 'transporter_registry', 
            'transporter_registry_details',
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
