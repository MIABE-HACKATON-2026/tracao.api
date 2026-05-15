from rest_framework import serializers
from ..models.parcels import Parcel, ParcelValidation
from ..models.batches import Batch, BatchValidation, Harvest
from .auth import UserSerializer


def validate_gps_coordinates(value):
    if not value or not isinstance(value, list):
        raise serializers.ValidationError("GPS coordinates must be a list of points.")
    if len(value) < 3:
        raise serializers.ValidationError("A polygon requires at least 3 points.")
    for i, point in enumerate(value):
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            raise serializers.ValidationError(f"Point {i} must be [longitude, latitude].")
        lon, lat = point[0], point[1]
        if not (-180 <= lon <= 180) or not (-90 <= lat <= 90):
            raise serializers.ValidationError(f"Point {i} has invalid coordinates.")
    if value[0] != value[-1]:
        value.append(value[0])
    return value


class ParcelSerializer(serializers.ModelSerializer):
    farmer_id = serializers.PrimaryKeyRelatedField(source='farmer', read_only=True)
    validated_by_id = serializers.PrimaryKeyRelatedField(source='validated_by', read_only=True)
    farmer_details = UserSerializer(source='farmer', read_only=True)
    
    class Meta:
        model = Parcel
        fields = (
            'id', 'farmer_id', 'farmer_details', 'name', 
            'gps_coordinates', 'area', 'status', 'store',
            'created_at', 'updated_at', 'validated_by_id'
        )
        read_only_fields = ('id', 'farmer_id', 'area', 'status', 'store', 'created_at', 'updated_at', 'validated_by_id')

    def validate_gps_coordinates(self, value):
        return validate_gps_coordinates(value)

class ParcelValidationSerializer(serializers.ModelSerializer):
    parcel_id = serializers.PrimaryKeyRelatedField(source='parcel', read_only=True)
    inspector_id = serializers.PrimaryKeyRelatedField(source='inspector', read_only=True)

    class Meta:
        model = ParcelValidation
        fields = ('id', 'parcel_id', 'inspector_id', 'comment', 'status', 'created_at')
        read_only_fields = ('id', 'inspector_id', 'created_at')

class HarvestSerializer(serializers.ModelSerializer):
    batch_id = serializers.PrimaryKeyRelatedField(source='batch', queryset=Batch.objects.all())

    class Meta:
        model = Harvest
        fields = ('id', 'batch_id', 'quantity', 'harvest_date', 'created_at')
        read_only_fields = ('id', 'created_at')

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        return value

class BatchSerializer(serializers.ModelSerializer):
    farmer_id = serializers.PrimaryKeyRelatedField(source='farmer', read_only=True)
    parcel = serializers.PrimaryKeyRelatedField(queryset=Parcel.objects.all())
    parcel_name = serializers.ReadOnlyField(source='parcel.name')
    validated_by_id = serializers.PrimaryKeyRelatedField(source='validated_by', read_only=True)
    validated_by_name = serializers.ReadOnlyField(source='validated_by.get_full_name')
    harvests = HarvestSerializer(many=True, read_only=True)
    total_harvested = serializers.SerializerMethodField()
    
    # Traceability fields
    transports_data = serializers.SerializerMethodField()
    transformations_data = serializers.SerializerMethodField()
    transactions_data = serializers.SerializerMethodField()

    class Meta:
        model = Batch
        fields = (
            'id', 'farmer_id', 'parcel', 'parcel_name', 'season', 'crop_type', 
            'estimated_quantity', 'status', 'unique_code', 'store',
            'created_at', 'updated_at', 'validated_by_id', 'validated_by_name',
            'harvests', 'total_harvested',
            'transports_data', 'transformations_data', 'transactions_data'
        )
        read_only_fields = ('id', 'farmer_id', 'status', 'unique_code', 'store', 'created_at', 'updated_at', 'validated_by_id')

    def get_total_harvested(self, obj):
        return sum(h.quantity for h in obj.harvests.all())

    def get_transports_data(self, obj):
        return [{
            'id': t.id,
            'transporter': t.transporter_registry.user.get_full_name() if t.transporter_registry.user else t.transporter_registry.phone,
            'from': t.from_location,
            'to': t.to_location,
            'status': t.status,
            'departure': t.departure_date,
            'arrival': t.arrival_date
        } for t in obj.transports.all()]

    def get_transformations_data(self, obj):
        return [{
            'id': ti.transformation.id,
            'transformer': ti.transformation.transformer.get_full_name(),
            'status': ti.transformation.status,
            'date': ti.transformation.created_at
        } for ti in obj.used_in_transformations.all()]

    def get_transactions_data(self, obj):
        return [{
            'id': tx.id,
            'seller': tx.seller.get_full_name(),
            'buyer': tx.buyer.get_full_name(),
            'quantity': tx.quantity,
            'price': tx.price,
            'status': tx.status,
            'date': tx.created_at
        } for tx in obj.transactions.all()]

class BatchValidationSerializer(serializers.ModelSerializer):
    batch_id = serializers.PrimaryKeyRelatedField(source='batch', read_only=True)
    validator_id = serializers.PrimaryKeyRelatedField(source='validator', read_only=True)

    class Meta:
        model = BatchValidation
        fields = ('id', 'batch_id', 'validator_id', 'comment', 'status', 'created_at')
        read_only_fields = ('id', 'validator_id', 'created_at')
