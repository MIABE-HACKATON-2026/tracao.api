from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def send_html_email(subject, template_name, context, recipient_list):
        """
        Envoie un email HTML en utilisant un template Django.
        """
        try:
            # Rendu du template HTML
            html_content = render_to_string(template_name, context)
            # Création de la version texte brute (pour les clients qui ne supportent pas le HTML)
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipient_list
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
            
            logger.info(f"Email HTML envoyé avec succès à {recipient_list} via template {template_name}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email HTML : {str(e)}")
            return False

    @staticmethod
    def send_simple_email(subject, message, recipient_list):
        """
        Garde la compatibilité pour les emails simples.
        """
        return EmailService.send_html_email(
            subject, 
            'emails/notification_email.html', 
            {'name': 'Utilisateur', 'message': message}, 
            recipient_list
        )
