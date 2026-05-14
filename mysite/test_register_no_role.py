import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from rest_framework.test import APIClient
client = APIClient()
response = client.post('/api/auth/register/', {
    "email": "norole@test.com",
    "phone": "+2250102030407",
    "password": "password123",
    "first_name": "Farmer",
    "last_name": "Test"
}, format='json')

print("Status:", response.status_code)
print("Data:", response.data)
