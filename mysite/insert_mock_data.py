import os
import django
import uuid
import random
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from api.models.auth import User
from api.models.stores import Store, StoreMember
from api.models.batches import Batch
from api.models.parcels import Parcel
from api.models.supply_chain import Transport

def create_mock_data():
    # 1. Get or create a store user
    user, created = User.objects.get_or_create(
        email='store@tracao.com',
        defaults={
            'username': 'store_manager',
            'first_name': 'Jean',
            'last_name': 'Dupont',
            'role': 'store',
            'phone': '+2250102030405',
            'city': 'Abidjan',
            'country': 'Côte d\'Ivoire'
        }
    )
    if not created:
        user.set_password('password123')
        user.save()
    else:
        user.set_password('password123')
        user.save()

    # 2. Create a Store
    store, _ = Store.objects.get_or_create(
        user=user,
        defaults={
            'name': 'Magasin Principal Abidjan',
            'status': 'approved'
        }
    )

    # 3. Create Store Membership
    StoreMember.objects.get_or_create(
        store=store,
        user=user,
        defaults={'role': 'manager', 'status': 'active'}
    )

    # 4. Create a Farmer for data
    farmer, _ = User.objects.get_or_create(
        email='farmer@tracao.com',
        defaults={
            'username': 'farmer_test',
            'first_name': 'Moussa',
            'last_name': 'Kone',
            'role': 'farmer',
            'phone': '+2250707070707',
            'city': 'Soubré',
            'country': 'Côte d\'Ivoire'
        }
    )

    # 5. Create Parcels and Batches
    crops = ['Cacao', 'Café']
    cities = ['Soubré', 'Daloa', 'Gagnoa', 'Man', 'San Pedro']
    
    for i in range(10):
        parcel = Parcel.objects.create(
            farmer=farmer,
            store=store,
            name=f"Parcelle {i+1}",
            area=random.uniform(1.0, 5.0),
            gps_coordinates={
                "type": "Polygon",
                "coordinates": [[[random.uniform(-7.0, -4.0), random.uniform(5.0, 7.0)] for _ in range(4)]]
            },
            status='approved'
        )
        
        # Create batches for the last 6 months (one per crop type)
        for crop in [c.lower() for c in crops]:
            created_at = timezone.now() - timedelta(days=random.randint(0, 180))
            batch = Batch.objects.create(
                farmer=farmer,
                parcel=parcel,
                store=store,
                season="2025-2026",
                unique_code=f"TRC-2025-{random.randint(100000, 999999)}",
                crop_type=crop,
                estimated_quantity=random.uniform(100, 1000),
                status='approved'
            )
            # Override created_at
            Batch.objects.filter(id=batch.id).update(created_at=created_at)

    print("Mock data created successfully!")

if __name__ == '__main__':
    create_mock_data()
