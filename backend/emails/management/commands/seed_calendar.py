from django.core.management.base import BaseCommand
from emails.models import seed_sample_data, create_indexes

class Command(BaseCommand):
    help = 'Seed calendar with sample events for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--google-id',
            type=str,
            default='test_user_001',
            help='Google ID for the test user (default: test_user_001)'
        )

    def handle(self, *args, **options):
        google_id = options['google_id']
        
        # Create indexes first
        create_indexes()
        self.stdout.write(self.style.SUCCESS('✅ Database indexes created'))
        
        # Seed sample data
        count = seed_sample_data(google_id)
        self.stdout.write(
            self.style.SUCCESS(f'✅ Seeded {count} sample calendar events for user {google_id}')
        )