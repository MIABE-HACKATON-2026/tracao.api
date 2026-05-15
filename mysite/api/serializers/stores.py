from rest_framework import serializers
from ..models.stores import Store, StoreMember, StoreAgent
from .auth import UserSerializer

class StoreSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(source='user', read_only=True)
    user_details = UserSerializer(source='user', read_only=True)
    validated_by_id = serializers.PrimaryKeyRelatedField(source='validated_by', read_only=True)

    class Meta:
        model = Store
        fields = ('id', 'user_id', 'user_details', 'name', 'legal_document', 'status', 'validated_by_id', 'created_at')
        read_only_fields = ('id', 'user_id', 'status', 'validated_by_id', 'created_at')

class StoreMemberSerializer(serializers.ModelSerializer):
    store_id = serializers.PrimaryKeyRelatedField(source='store', read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(source='user', read_only=True)
    user_details = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = StoreMember
        fields = ('id', 'store_id', 'user_id', 'user_details', 'role', 'status', 'created_at')
        read_only_fields = ('id', 'created_at')

class StoreAgentSerializer(serializers.ModelSerializer):
    store_id = serializers.PrimaryKeyRelatedField(source='store', read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(source='user', read_only=True)
    user_details = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = StoreAgent
        fields = ('id', 'store_id', 'user_id', 'user_details', 'role', 'status', 'created_at')
        read_only_fields = ('id', 'created_at')
