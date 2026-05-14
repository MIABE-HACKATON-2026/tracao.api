import random
import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.utils import timezone
from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from ..models.auth import KYCRecord, OTPRecord
from ..serializers.auth import (
    CustomTokenObtainPairSerializer,
    KYCRecordSerializer,
    RegisterSerializer,
    UserSerializer,
)
from ..utils.email_service import EmailService

User = get_user_model()


def hash_otp(code: str) -> str:
    return make_password(code)


def verify_otp_hash(code: str, hashed: str) -> bool:
    # Si le code en base fait 6 caractères, c'est un ancien code non haché
    if len(hashed) <= 6:
        return code == hashed
    return check_password(code, hashed)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)

    def perform_create(self, serializer):
        user = serializer.save()
        
        otp_code = str(random.randint(100000, 999999))
        expires_at = timezone.now() + timedelta(minutes=10)
        hashed_code = hash_otp(otp_code)
        
        OTPRecord.objects.create(email=user.email, code=hashed_code, expires_at=expires_at)

        try:
            EmailService.send_html_email(
                subject="Votre code de vérification - Tracao",
                template_name="emails/notification_email.html",
                context={
                    "name": f"{user.first_name} {user.last_name}",
                    "otp_code": otp_code, # On envoie le code en clair par mail
                    "message": f"Merci de vous être inscrit sur Tracao. Votre code de vérification est : {otp_code}. Ce code expirera dans 10 minutes.",
                },
                recipient_list=[user.email],
            )
        except Exception as e:
            print(f"Erreur envoi email: {str(e)}")


class VerifyOTPView(APIView):
    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        request={"application/json": {"type": "object", "properties": {"email": {"type": "string"}, "code": {"type": "string"}}}},
        responses={200: {"type": "object", "properties": {"message": {"type": "string"}, "access": {"type": "string"}, "refresh": {"type": "string"}, "user": {"type": "object"}}}},
    )
    def post(self, request):
        email = request.data.get("email", "").strip()
        code = request.data.get("code", "").strip()

        if not email or not code:
            return Response(
                {"error": "Email et code sont requis"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            # Chercher le dernier OTP non utilisé pour cet email
            otp = (
                OTPRecord.objects.select_for_update()
                .filter(email=email, is_used=False)
                .order_by("-created_at")
                .first()
            )

            if not otp:
                return Response(
                    {"error": "Code invalide ou expiré"}, status=status.HTTP_400_BAD_REQUEST
                )

            if not verify_otp_hash(code, otp.code):
                return Response(
                    {"error": "Code invalide"}, status=status.HTTP_400_BAD_REQUEST
                )

            if not otp.is_valid():
                return Response(
                    {"error": "Code expiré"}, status=status.HTTP_400_BAD_REQUEST
                )

            otp.is_used = True
            otp.save()

        try:
            user = User.objects.get(email=email)
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "message": "Compte vérifié avec succès",
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user": UserSerializer(user, context={"request": request}).data,
                },
                status=status.HTTP_200_OK,
            )
        except User.DoesNotExist:
            return Response(
                {"error": "Utilisateur introuvable"},
                status=status.HTTP_404_NOT_FOUND,
            )


class RequestOTPView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get("email", "").strip()
        if not email:
            return Response(
                {"error": "Email est requis"}, status=status.HTTP_400_BAD_REQUEST
            )

        otp_code = str(random.randint(100000, 999999))
        expires_at = timezone.now() + timedelta(minutes=10)
        hashed_code = hash_otp(otp_code)

        OTPRecord.objects.create(email=email, code=hashed_code, expires_at=expires_at)

        EmailService.send_html_email(
            subject="Votre code de vérification",
            template_name="emails/notification_email.html",
            context={
                "name": "Cher utilisateur",
                "otp_code": otp_code,
                "message": f"Votre code de vérification est : {otp_code}. Ce code expirera dans 10 minutes.",
            },
            recipient_list=[email],
        )
        return Response({"message": "OTP envoyé avec succès"})


class ResendOTPView(RequestOTPView):
    pass


class RequestMagicLinkView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        identifier = request.data.get("identifier", "").strip()
        if not identifier:
            return Response(
                {"error": "Email ou Téléphone est requis"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            if "@" in identifier:
                user = User.objects.get(email=identifier)
            else:
                user = User.objects.get(phone=identifier)
        except User.DoesNotExist:
            return Response(
                {"error": "Utilisateur introuvable"}, status=status.HTTP_404_NOT_FOUND
            )

        signer = TimestampSigner()
        token = signer.sign(str(user.id))

        frontend_base_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000").rstrip("/")
        magic_link = f"{frontend_base_url}/login/as-operator/password?token={token}"

        if user.email:
            EmailService.send_html_email(
                subject="Connexion à votre compte",
                template_name="emails/notification_email.html",
                context={
                    "name": user.first_name,
                    "message": "Cliquez sur le bouton ci-dessous pour accéder à la page de saisie de votre mot de passe.",
                    "action_url": magic_link,
                    "action_text": "Se connecter",
                },
                recipient_list=[user.email],
            )
            return Response({"message": "Lien magique envoyé par email"})
        else:
            return Response(
                {"error": "L'utilisateur n'a pas d'email associé"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class VerifyMagicLinkView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        token = request.data.get("token")
        password = request.data.get("password")

        if not token or not password:
            return Response(
                {"error": "Token et mot de passe sont requis"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        signer = TimestampSigner()
        try:
            user_id = signer.unsign(token, max_age=900)
            user = User.objects.get(id=user_id)
        except (SignatureExpired, BadSignature, User.DoesNotExist):
            return Response(
                {"error": "Lien invalide ou expiré"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.check_password(password):
            return Response(
                {"error": "Mot de passe incorrect"}, status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user, context={"request": request}).data,
            },
            status=status.HTTP_200_OK,
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


class LoginView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class KYCRecordViewSet(viewsets.ModelViewSet):
    serializer_class = KYCRecordSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return KYCRecord.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Save the KYC record
        serializer.save(user=self.request.user)
        
        # Also update user's profile photo if provided in the same request
        profile_photo = self.request.data.get("profile_photo")
        if profile_photo:
            self.request.user.profile_photo = profile_photo
            
        self.request.user.kyc_status = "pending"
        self.request.user.save()


class RequestPasswordResetView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get("email", "").strip()
        try:
            user = User.objects.get(email=email)
            # Logique de reset password ici (ex: envoyer un mail avec token)
            return Response({"message": "Email de réinitialisation envoyé"})
        except User.DoesNotExist:
            return Response({"error": "Utilisateur introuvable"}, status=404)


class ConfirmPasswordResetView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        # Logique de confirmation ici
        return Response({"message": "Mot de passe réinitialisé"})
