from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from ..models.auth import KYCRecord, Session

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    latest_kyc = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "phone",
            "first_name",
            "last_name",
            "email",
            "role",
            "sub_role",
            "profile_photo",
            "import_license",
            "export_license",
            "country",
            "city",
            "address",
            "latitude",
            "longitude",
            "status",
            "kyc_status",
            "is_active",
            "created_at",
            "latest_kyc",
        )
        read_only_fields = ("id", "created_at", "status", "kyc_status")

    def get_latest_kyc(self, obj):
        kyc = obj.kyc_records.order_by("-submitted_at").first()
        if kyc:
            return KYCRecordSerializer(kyc, context=self.context).data
        return None


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("email", "phone", "first_name", "last_name", "role", "password", "city", "country")

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_phone(self, value):
        if not value:
            raise serializers.ValidationError("Phone number is required.")
        if not value.startswith('+'):
            raise serializers.ValidationError("Phone number must start with country code (e.g., +225).")
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        return value

    def validate_role(self, value):
        valid_roles = ['farmer', 'buyer', 'store', 'admin', 'agent', 'transporter', 'processor']
        if value not in valid_roles:
            raise serializers.ValidationError(f"Role must be one of: {', '.join(valid_roles)}")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            phone=validated_data.get("phone"),
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            role=validated_data["role"],
            city=validated_data.get("city"),
            country=validated_data.get("country"),
        )
        return user


class KYCRecordSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(source="user", read_only=True)
    validated_by_id = serializers.PrimaryKeyRelatedField(
        source="validated_by", read_only=True
    )

    class Meta:
        model = KYCRecord
        fields = (
            "id",
            "user_id",
            "cni_front_image",
            "cni_back_image",
            "status",
            "rejection_reason",
            "submitted_at",
            "validated_at",
            "validated_by_id",
        )
        read_only_fields = (
            "id",
            "user_id",
            "status",
            "submitted_at",
            "validated_at",
            "validated_by_id",
        )

class CustomTokenObtainPairSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        from django.contrib.auth import authenticate
        user = authenticate(email=attrs['email'], password=attrs['password'])
        if not user:
            raise serializers.ValidationError("Identifiants incorrects")
        
        refresh = RefreshToken.for_user(user)
        request = self.context.get('request')
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user, context={'request': request}).data
        }
