import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from api.models.auth import User

email = 'store@tracao.com'
if not User.objects.filter(email=email).exists():
    User.objects.create_user(
        email=email,
        phone='0707070707',
        role='store',
        password='Password123!',
        first_name='Test',
        last_name='Store'
    )
    print(f"User {email} created successfully.")
else:
    print(f"User {email} already exists.")
