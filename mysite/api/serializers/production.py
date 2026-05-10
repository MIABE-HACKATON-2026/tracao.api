from rest_framework import serializers
from ..models.parcels import Parcel, ParcelValidation
from ..models.batches import Batch, BatchValidation, Harvest
from .auth import UserSerializer

class ParcelSerializer(serializers.ModelSerializer):
    farmer_id = serializers.PrimaryKeyRelatedField(source='farmer', read_only=True)
    validated_by_id = serializers.PrimaryKeyRelatedField(source='validated_by', read_only=True)
    farmer_details = UserSerializer(source='farmer', read_only=True)
    
    class Meta:
        model = Parcel
        fields = (
            'id', 'farmer_id', 'farmer_details', 'name', 
            'gps_coordinates', 'area', 'status', 
            'created_at', 'updated_at', 'validated_by_id'
        )
        read_only_fields = ('id', 'farmer_id', 'area', 'status', 'created_at', 'updated_at', 'validated_by_id')

class ParcelValidationSerializer(serializers.ModelSerializer):
    parcel_id = serializers.PrimaryKeyRelatedField(source='parcel', read_only=True)
    inspector_id = serializers.PrimaryKeyRelatedField(source='inspector', read_only=True)

    class Meta:
        model = ParcelValidation
        fields = ('id', 'parcel_id', 'inspector_id', 'comment', 'status', 'created_at')
        read_only_fields = ('id', 'inspector_id', 'created_at')

class HarvestSerializer(serializers.ModelSerializer):
    batch_id = serializers.PrimaryKeyRelatedField(source='batch', read_only=True)

    class Meta:
        model = Harvest
        fields = ('id', 'batch_id', 'quantity', 'harvest_date', 'created_at')
        read_only_fields = ('id', 'created_at')

class BatchSerializer(serializers.ModelSerializer):
    farmer_id = serializers.PrimaryKeyRelatedField(source='farmer', read_only=True)
    parcel_id = serializers.PrimaryKeyRelatedField(source='parcel', read_only=True)
    validated_by_id = serializers.PrimaryKeyRelatedField(source='validated_by', read_only=True)
    harvests = HarvestSerializer(many=True, read_only=True)
    total_harvested = serializers.SerializerMethodField()

    class Meta:
        model = Batch
        fields = (
            'id', 'farmer_id', 'parcel_id', 'season', 'crop_type', 
            'estimated_quantity', 'status', 'unique_code', 
            'created_at', 'updated_at', 'validated_by_id', 
            'harvests', 'total_harvested'
        )
        read_only_fields = ('id', 'farmer_id', 'status', 'unique_code', 'created_at', 'updated_at', 'validated_by_id')

    def get_total_harvested(self, obj):
        return sum(h.quantity for h in obj.harvests.all())

class BatchValidationSerializer(serializers.ModelSerializer):
    batch_id = serializers.PrimaryKeyRelatedField(source='batch', read_only=True)
    validator_id = serializers.PrimaryKeyRelatedField(source='validator', read_only=True)

    class Meta:
        model = BatchValidation
        fields = ('id', 'batch_id', 'validator_id', 'comment', 'status', 'created_at')
        read_only_fields = ('id', 'validator_id', 'created_at')
