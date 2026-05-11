from rest_framework import generics, status, permissions, viewsets
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
from django.conf import settings
from datetime import timedelta
import random

from ..serializers.auth import UserSerializer, RegisterSerializer, KYCRecordSerializer
from ..models.auth import KYCRecord, OTPRecord
from ..utils.email_service import EmailService

User = get_user_model()


class RequestOTPView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response(
                {"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Générer OTP à 6 chiffres
        otp_code = str(random.randint(100000, 999999))
        expires_at = timezone.now() + timedelta(minutes=10)

        OTPRecord.objects.create(email=email, code=otp_code, expires_at=expires_at)

        # Envoyer l'email
        EmailService.send_html_email(
            subject="Votre code de vérification",
            template_name="emails/notification_email.html",
            context={
                "name": "Cher utilisateur",
                "message": f"Votre code de vérification pour la création de compte est : {otp_code}. Ce code expirera dans 10 minutes.",
            },
            recipient_list=[email],
        )

        return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)


class RequestMagicLinkView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        identifier = request.data.get("identifier")  # email or phone
        if not identifier:
            return Response(
                {"error": "Email or Phone is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            if "@" in identifier:
                user = User.objects.get(email=identifier)
            else:
                user = User.objects.get(phone=identifier)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Créer un magic link token
        signer = TimestampSigner()
        token = signer.sign(str(user.id))

        # Construire l'URL (votre page frontend)
        frontend_base_url = getattr(
            settings, "FRONTEND_URL", "http://localhost:3000"
        ).rstrip("/")
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
            return Response(
                {"message": "Magic link sent to email"}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"error": "User has no email associated"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class VerifyMagicLinkView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        token = request.data.get("token")
        password = request.data.get("password")

        if not token or not password:
            return Response(
                {"error": "Token and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        signer = TimestampSigner()
        try:
            # Token valide pendant 15 minutes
            user_id = signer.unsign(token, max_age=900)
            user = User.objects.get(id=user_id)
        except (SignatureExpired, BadSignature, User.DoesNotExist):
            return Response(
                {"error": "Invalid or expired token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Vérifier le mot de passe
        if not user.check_password(password):
            return Response(
                {"error": "Invalid password"}, status=status.HTTP_401_UNAUTHORIZED
            )

        # Login réussi -> Retourner JWT
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class VerifyOTPView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")

        if not email or not code:
            return Response(
                {"error": "Email and code are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        print(f"DEBUG: Tentative de vérification pour email={email} et code={code}")

        # Chercher le dernier OTP non utilisé pour cet email
        otp = (
            OTPRecord.objects.filter(email=email, code=code, is_used=False)
            .order_by("-created_at")
            .first()
        )

        if not otp:
            print(f"DEBUG: Aucun OTP trouvé en base pour {email} avec ce code.")
            return Response(
                {"error": "Code invalide ou expiré"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not otp.is_valid():
            from django.utils import timezone
            print(f"DEBUG: OTP trouvé mais invalide. Expire à: {otp.expires_at}, Heure actuelle: {timezone.now()}")
            return Response(
                {"error": "Code invalide ou expiré"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Marquer comme utilisé
        otp.is_used = True
        otp.save()

        try:
            user = User.objects.get(email=email)
            # Générer les tokens JWT pour connecter l'utilisateur immédiatement
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "message": "Compte vérifié avec succès",
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user": UserSerializer(user).data,
                },
                status=status.HTTP_200_OK,
            )
        except User.DoesNotExist:
            return Response(
                {"message": "Code vérifié, mais utilisateur introuvable"},
                status=status.HTTP_200_OK,
            )


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        
        # Générer un OTP à 6 chiffres
        otp_code = str(random.randint(100000, 999999))
        expires_at = timezone.now() + timedelta(minutes=10)
        
        # Enregistrer l'OTP en base
        OTPRecord.objects.create(email=user.email, code=otp_code, expires_at=expires_at)

        # Envoyer l'email via le service dédié
        try:
            EmailService.send_html_email(
                subject="Votre code de vérification - Tracao",
                template_name="emails/notification_email.html",
                context={
                    "name": f"{user.first_name} {user.last_name}",
                    "message": f"Merci de vous être inscrit sur Tracao. Votre code de vérification est : {otp_code}. Ce code expirera dans 10 minutes.",
                },
                recipient_list=[user.email],
            )
            print(f"DEBUG: Email envoyé avec succès à {user.email} avec le code {otp_code}")
        except Exception as e:
            print(f"ERROR: Échec de l'envoi de l'email à {user.email}: {str(e)}")
            # On ne bloque pas l'inscription si l'email échoue, mais on le log


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
        self.request.user.kyc_status = "pending"
        self.request.user.save()
