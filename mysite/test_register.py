import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from rest_framework.test import APIClient
client = APIClient()
response = client.post('/api/auth/register/', {
    "email": "test@test.com",
    "password": "password123",
    "first_name": "Test",
    "last_name": "User",
    "phone": "+1234567890",
    "role": "farmer"
}, format='json')

print("Status:", response.status_code)
print("Data:", response.data)
