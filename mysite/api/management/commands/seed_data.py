from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from api.models import Parcel, Batch, Harvest, Transaction, Store, StoreMember, StoreAgent
import uuid
import random
from datetime import datetime, timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed database with mock data for all roles'

    def handle(self, *args, **options):
        self.stdout.write('Creating mock data...')
        
        # Create Admin
        admin, created = User.objects.get_or_create(
            email='admin@tracao.com',
            defaults={
                'first_name': 'Admin',
                'last_name': 'System',
                'phone': '+22500000000',
                'role': 'admin',
                'status': 'active',
                'kyc_status': 'approved',
                'is_staff': True,
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS(f'Created admin: admin@tracao.com / admin123'))

        # Create Store (Cooperative)
        store_user, created = User.objects.get_or_create(
            email='coop@fako.com',
            defaults={
                'first_name': 'Coopérative',
                'last_name': 'Fako',
                'phone': '+22501000001',
                'role': 'store',
                'status': 'active',
                'kyc_status': 'approved',
            }
        )
        if created:
            store_user.set_password('coop123')
            store_user.save()
        
        store, created = Store.objects.get_or_create(
            name='Coopérative Fako',
            defaults={
                'user': store_user,
                'status': 'approved',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created store: Coopérative Fako'))

        # Create Store Members (Farmers)
        farmers_data = [
            {'email': 'kouadio@tracao.com', 'first_name': 'Kouadio', 'last_name': 'Antoine', 'phone': '+22507000001'},
            {'email': 'diaby@tracao.com', 'first_name': 'Diaby', 'last_name': 'Mamadou', 'phone': '+22507000002'},
            {'email': 'konan@tracao.com', 'first_name': 'Konan', 'last_name': 'Ibrahim', 'phone': '+22507000003'},
            {'email': 'traore@tracao.com', 'first_name': 'Traoré', 'last_name': 'Fatou', 'phone': '+22507000004'},
            {'email': 'coulibaly@tracao.com', 'first_name': 'Coulibaly', 'last_name': 'Moussa', 'phone': '+22507000005'},
        ]

        farmers = []
        for data in farmers_data:
            farmer, created = User.objects.get_or_create(
                email=data['email'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'phone': data['phone'],
                    'role': 'farmer',
                    'status': 'active',
                    'kyc_status': 'approved',
                }
            )
            if created:
                farmer.set_password('farmer123')
                farmer.save()
            
            farmers.append(farmer)
            
            # Add as store member
            StoreMember.objects.get_or_create(
                store=store,
                user=farmer,
                defaults={'role': 'membre', 'status': 'active'}
            )
            
            # Create parcels for farmer
            for i in range(2):
                parcel, created = Parcel.objects.get_or_create(
                    id=uuid.uuid4(),
                    farmer=farmer,
                    name=f"Parcelle {i+1} - {data['last_name']}",
                    defaults={
                        'gps_coordinates': {
                            'type': 'Polygon',
                            'coordinates': [[
                                [random.uniform(-5, -4), random.uniform(6, 7)],
                                [random.uniform(-5, -4), random.uniform(6, 7)],
                                [random.uniform(-5, -4), random.uniform(6, 7)],
                                [random.uniform(-5, -4), random.uniform(6, 7)],
                            ]]
                        },
                        'area': random.uniform(5, 25),
                        'status': 'approved',
                    }
                )
                
                # Create batch for parcel
                batch, created = Batch.objects.get_or_create(
                    id=uuid.uuid4(),
                    farmer=farmer,
                    parcel=parcel,
                    season='2025-2026',
                    defaults={
                        'crop_type': 'cacao',
                        'estimated_quantity': random.uniform(500, 2000),
                        'status': 'approved',
                        'unique_code': f'TRC-2025-{random.randint(1000, 9999)}',
                    }
                )
                
                # Create harvests
                for j in range(3):
                    Harvest.objects.get_or_create(
                        batch=batch,
                        harvest_date=datetime.now().date() - timedelta(days=random.randint(30, 90)),
                        defaults={
                            'quantity': random.uniform(100, 500),
                        }
                    )

        self.stdout.write(self.style.SUCCESS(f'Created {len(farmers)} farmers with parcels and batches'))

        # Create Buyers
        buyers_data = [
            {'email': 'buyer1@tracao.com', 'first_name': 'Jean', 'last_name': 'Dubois', 'phone': '+22508000001', 'sub_role': 'exportateur'},
            {'email': 'buyer2@tracao.com', 'first_name': 'Marie', 'last_name': 'Laurent', 'phone': '+22508000002', 'sub_role': 'importateur'},
            {'email': 'buyer3@tracao.com', 'first_name': 'Pierre', 'last_name': 'Martin', 'phone': '+22508000003', 'sub_role': 'transformateur'},
        ]

        for data in buyers_data:
            buyer, created = User.objects.get_or_create(
                email=data['email'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'phone': data['phone'],
                    'role': 'buyer',
                    'sub_role': data['sub_role'],
                    'status': 'active',
                    'kyc_status': 'approved',
                }
            )
            if created:
                buyer.set_password('buyer123')
                buyer.save()

        self.stdout.write(self.style.SUCCESS(f'Created {len(buyers_data)} buyers'))

        # Create Agents
        agents_data = [
            {'email': 'agent1@tracao.com', 'first_name': 'Agent', 'last_name': 'Kone', 'phone': '+22509000001'},
            {'email': 'agent2@tracao.com', 'first_name': 'Agent', 'last_name': 'Soro', 'phone': '+22509000002'},
        ]

        for data in agents_data:
            agent, created = User.objects.get_or_create(
                email=data['email'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'phone': data['phone'],
                    'role': 'agent',
                    'status': 'active',
                    'kyc_status': 'approved',
                }
            )
            if created:
                agent.set_password('agent123')
                agent.save()
            
            StoreAgent.objects.get_or_create(
                store=store,
                user=agent,
                defaults={'role': 'agent_terrain', 'status': 'active'}
            )

        self.stdout.write(self.style.SUCCESS(f'Created {len(agents_data)} agents'))

        # Create Transporters
        transporters_data = [
            {'email': 'transport1@tracao.com', 'first_name': 'Transport', 'last_name': 'Cisse', 'phone': '+22505000001'},
            {'email': 'transport2@tracao.com', 'first_name': 'Transport', 'last_name': 'Bamba', 'phone': '+22505000002'},
        ]

        for data in transporters_data:
            transporter, created = User.objects.get_or_create(
                email=data['email'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'phone': data['phone'],
                    'role': 'transporter',
                    'status': 'active',
                    'kyc_status': 'approved',
                }
            )
            if created:
                transporter.set_password('transport123')
                transporter.save()

        self.stdout.write(self.style.SUCCESS(f'Created {len(transporters_data)} transporters'))

        # Create Processors
        processors_data = [
            {'email': 'processor1@tracao.com', 'first_name': 'Transform', 'last_name': 'Doumbia', 'phone': '+22506000001'},
        ]

        for data in processors_data:
            processor, created = User.objects.get_or_create(
                email=data['email'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'phone': data['phone'],
                    'role': 'processor',
                    'status': 'active',
                    'kyc_status': 'approved',
                }
            )
            if created:
                processor.set_password('processor123')
                processor.save()

        self.stdout.write(self.style.SUCCESS(f'Created {len(processors_data)} processors'))

        self.stdout.write(self.style.SUCCESS('\n=== Mock Data Created Successfully ==='))
        self.stdout.write('\nCredentials for testing:')
        self.stdout.write('  Admin: admin@tracao.com / admin123')
        self.stdout.write('  Coop:  coop@fako.com / coop123')
        self.stdout.write('  Farmer: kouadio@tracao.com / farmer123')
        self.stdout.write('  Buyer:  buyer1@tracao.com / buyer123')
        self.stdout.write('  Agent:  agent1@tracao.com / agent123')
        self.stdout.write('  Transport: transport1@tracao.com / transport123')
        self.stdout.write('  Processor: processor1@tracao.com / processor123')