from rest_framework import generics, status, permissions, viewsets
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from ..serializers.auth import UserSerializer, RegisterSerializer, KYCRecordSerializer
from ..models.auth import KYCRecord

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

class KYCRecordViewSet(viewsets.ModelViewSet):
    serializer_class = KYCRecordSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return KYCRecord.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        # Update user kyc_status to pending
        self.request.user.kyc_status = 'pending'
        self.request.user.save()
