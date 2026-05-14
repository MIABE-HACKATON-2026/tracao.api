import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from api.models.auth import User
for u in User.objects.all():
    print(f"ID: {u.id}, Email: {u.email}, Username: {repr(u.username)}")
