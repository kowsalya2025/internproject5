from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Creates initial superuser from environment variables'

    def handle(self, *args, **options):
        User = get_user_model()
        
        email = os.getenv('DJANGO_SUPERUSER_EMAIL')
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD')
        
        if not email or not password:
            self.stdout.write(self.style.WARNING(
                'Skipping superuser creation: DJANGO_SUPERUSER_EMAIL or DJANGO_SUPERUSER_PASSWORD not set'
            ))
            return
        
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.SUCCESS(f'Superuser with email {email} already exists'))
            return
        
        try:
            User.objects.create_superuser(
                email=email,
                password=password,
            )
            self.stdout.write(self.style.SUCCESS(f'✅ Superuser created successfully: {email}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating superuser: {str(e)}'))