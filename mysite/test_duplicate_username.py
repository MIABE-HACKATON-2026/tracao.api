import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from rest_framework.test import APIClient
client = APIClient()

print("Creating user 1...")
res1 = client.post('/api/auth/register/', {
    "role": "farmer",
    "first_name": "First1",
    "last_name": "Last1",
    "email": "user1@example.com",
    "phone": "+22500000001",
    "password": "password123"
}, format='json')
print("User 1 status:", res1.status_code)

print("Creating user 2...")
res2 = client.post('/api/auth/register/', {
    "role": "farmer",
    "first_name": "First2",
    "last_name": "Last2",
    "email": "user2@example.com",
    "phone": "+22500000002",
    "password": "password123"
}, format='json')
print("User 2 status:", res2.status_code)
if res2.status_code == 500:
    print("User 2 failed with 500!")
