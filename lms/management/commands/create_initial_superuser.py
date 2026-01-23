from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = "Creates a superuser if it doesn't exist"

    def handle(self, *args, **options):
        User = get_user_model()
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        if not User.objects.filter(email=email).exists():
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f"Superuser {email} created"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Superuser {email} already exists"))
