from django.core.management.base import BaseCommand
from django.utils import timezone
from api.models.auth import OTPRecord


class Command(BaseCommand):
    help = 'Cleanup expired OTP records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='Delete OTPs older than N days (default: 1)',
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff = timezone.now() - timezone.timedelta(days=days)
        
        deleted_count, _ = OTPRecord.objects.filter(created_at__lt=cutoff).delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {deleted_count} expired OTP records')
        )