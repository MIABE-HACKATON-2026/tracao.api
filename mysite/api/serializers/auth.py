from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models.auth import KYCRecord, Session

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'phone', 'first_name', 'last_name', 'email', 
            'role', 'sub_role', 'profile_photo', 'country', 
            'city', 'address', 'status', 'kyc_status', 'created_at'
        )
        read_only_fields = ('id', 'created_at', 'status', 'kyc_status')

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('phone', 'first_name', 'last_name', 'email', 'role', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            phone=validated_data['phone'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data.get('email', ''),
            role=validated_data['role']
        )
        return user

class KYCRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCRecord
        fields = (
            'id', 'user', 'cni_front_image', 'cni_back_image', 
            'status', 'rejection_reason', 'submitted_at', 'validated_at'
        )
        read_only_fields = ('id', 'user', 'status', 'submitted_at', 'validated_at')
