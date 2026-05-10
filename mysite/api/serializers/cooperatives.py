from rest_framework import serializers
from ..models.cooperatives import Cooperative, CoopMember, CoopAgent
from .auth import UserSerializer

class CooperativeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cooperative
        fields = ('id', 'user', 'name', 'legal_document', 'status', 'validated_by', 'created_at')
        read_only_fields = ('id', 'user', 'status', 'validated_by', 'created_at')

class CoopMemberSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = CoopMember
        fields = ('id', 'cooperative', 'user', 'user_details', 'role', 'status', 'created_at')
        read_only_fields = ('id', 'created_at')

class CoopAgentSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = CoopAgent
        fields = ('id', 'cooperative', 'user', 'user_details', 'role', 'status', 'created_at')
        read_only_fields = ('id', 'created_at')
