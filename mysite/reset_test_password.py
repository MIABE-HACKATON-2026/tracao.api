import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from api.models.auth import User

def reset_password():
    email = "mrkondoibrahim@gmail.com"
    try:
        user = User.objects.get(email=email)
        user.set_password("password123")
        user.save()
        print(f"Password reset for {email} to 'password123'")
    except User.DoesNotExist:
        print(f"User {email} not found")

if __name__ == "__main__":
    reset_password()
