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
        Envoie un email HTML en utilisant un template Django, de manière asynchrone.
        """
        import threading
        
        def _send():
            try:
                # Rendu du template HTML
                html_content = render_to_string(template_name, context)
                # Création de la version texte brute
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
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de l'email HTML à {recipient_list}: {str(e)}")

        thread = threading.Thread(target=_send)
        thread.start()
        return True

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
