from rest_framework import serializers
from ..models.parcels import Parcel, ParcelValidation
from ..models.batches import Batch, BatchValidation, Harvest
from .auth import UserSerializer

class ParcelSerializer(serializers.ModelSerializer):
    farmer_details = UserSerializer(source='farmer', read_only=True)
    
    class Meta:
        model = Parcel
        fields = (
            'id', 'farmer', 'farmer_details', 'name', 
            'gps_coordinates', 'area', 'status', 
            'created_at', 'updated_at', 'validated_by'
        )
        read_only_fields = ('id', 'farmer', 'area', 'status', 'created_at', 'updated_at', 'validated_by')

class ParcelValidationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParcelValidation
        fields = ('id', 'parcel', 'inspector', 'comment', 'status', 'created_at')
        read_only_fields = ('id', 'inspector', 'created_at')

class HarvestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Harvest
        fields = ('id', 'batch', 'quantity', 'harvest_date', 'created_at')
        read_only_fields = ('id', 'created_at')

class BatchSerializer(serializers.ModelSerializer):
    harvests = HarvestSerializer(many=True, read_only=True)
    total_harvested = serializers.SerializerMethodField()

    class Meta:
        model = Batch
        fields = (
            'id', 'farmer', 'parcel', 'season', 'crop_type', 
            'estimated_quantity', 'status', 'unique_code', 
            'created_at', 'updated_at', 'validated_by', 
            'harvests', 'total_harvested'
        )
        read_only_fields = ('id', 'farmer', 'status', 'unique_code', 'created_at', 'updated_at', 'validated_by')

    def get_total_harvested(self, obj):
        return sum(h.quantity for h in obj.harvests.all())

class BatchValidationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BatchValidation
        fields = ('id', 'batch', 'validator', 'comment', 'status', 'created_at')
        read_only_fields = ('id', 'validator', 'created_at')
