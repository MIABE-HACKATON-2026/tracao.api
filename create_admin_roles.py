import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

admins = [
    {
        "email": "superadmin@tracao.io",
        "password": "Admin2026!",
        "role": "admin",
        "sub_role": "super_admin",
        "first_name": "Super",
        "last_name": "Admin",
        "phone": "+225000000001"
    },
    {
        "email": "gov@tracao.io",
        "password": "Gov2026!",
        "role": "admin",
        "sub_role": "gouvernement",
        "first_name": "Min",
        "last_name": "Agriculture",
        "phone": "+225000000002"
    },
    {
        "email": "cert@tracao.io",
        "password": "Cert2026!",
        "role": "admin",
        "sub_role": "certificateur",
        "first_name": "Org",
        "last_name": "Certification",
        "phone": "+225000000003"
    }
]

for admin_data in admins:
    user, created = User.objects.get_or_create(
        email=admin_data["email"],
        defaults=admin_data
    )
    if created:
        user.set_password(admin_data["password"])
        user.save()
        print(f"Created: {user.email}")
    else:
        # Update sub_role just in case they existed
        user.sub_role = admin_data["sub_role"]
        user.set_password(admin_data["password"])
        user.save()
        print(f"Updated: {user.email}")
