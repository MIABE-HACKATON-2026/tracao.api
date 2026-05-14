import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from api.models.auth import User

def check_user():
    email = "mrkondoibrahim@gmail.com"
    try:
        user = User.objects.get(email=email)
        print(f"User found: {user.email}")
        print(f"Is active: {user.is_active}")
        print(f"Role: {user.role}")
        print(f"Status: {user.status}")
        print(f"Has usable password: {user.has_usable_password()}")
    except User.DoesNotExist:
        print(f"User {email} not found")

if __name__ == "__main__":
    check_user()
