import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from rest_framework.test import APIClient
client = APIClient()
response = client.post('/api/auth/register/', {
    "role": "farmer",
    "first_name": "John",
    "last_name": "Doe",
    "city": "Abidjan",
    "country": "Côte d'Ivoire",
    "address": "Some address",
    "latitude": 5.30966,
    "longitude": -4.01266,
    "email": "john2@example.com",
    "phone": "+2250102030499",
    "password": "password123"
}, format='json')

print("Status:", response.status_code)
print("Data:", response.data)
