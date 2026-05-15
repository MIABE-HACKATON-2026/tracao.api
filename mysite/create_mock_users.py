import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

roles = [
    {'phone': '90000010', 'email': 'ibraumodnokpro@gmail.com', 'role': 'agent', 'sub_role': 'inspector', 'password': 'password123', 'first_name': 'Inspecteur', 'last_name': 'Coop'},
    {'phone': '90000011', 'email': 'ibraumodnok2@gmail.com', 'role': 'agent', 'sub_role': None, 'password': 'password123', 'first_name': 'Agent', 'last_name': 'Terrain'},
    {'phone': '90000012', 'email': 'ibraumodnok3@gmail.com', 'role': 'transporter', 'sub_role': None, 'password': 'password123', 'first_name': 'Transporteur', 'last_name': 'Test'},
]

for r in roles:
    user, created = User.objects.get_or_create(
        email=r['email'],
        defaults={
            'phone': r['phone'],
            'role': r['role'],
            'sub_role': r['sub_role'],
            'first_name': r['first_name'],
            'last_name': r['last_name'],
            'is_active': True,
            'kyc_status': 'approved'
        }
    )
    if created:
        user.set_password(r['password'])
        user.save()
        print(f"Créé: {r['role']} (Email: {r['email']} | Téléphone: {r['phone']} | Mot de passe: {r['password']})")
    else:
        user.phone = r['phone']
        user.role = r['role']
        user.sub_role = r['sub_role']
        user.is_active = True
        user.kyc_status = 'approved'
        user.set_password(r['password'])
        user.save()
        print(f"Mis à jour: {r['role']} (Email: {r['email']} | Téléphone: {r['phone']} | Mot de passe: {r['password']})")
