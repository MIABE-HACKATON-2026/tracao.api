import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from api.utils.email_service import EmailService

EmailService.send_html_email(
    subject="Votre code de vérification - Tracao",
    template_name="emails/notification_email.html",
    context={
        "name": f"Test Name",
        "message": f"Merci de vous être inscrit sur Tracao. Votre code de vérification est : 123456. Ce code expirera dans 10 minutes.",
    },
    recipient_list=["test@test.com"],
)
print("Email sent!")
