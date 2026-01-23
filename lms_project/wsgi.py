import os
from django.core.wsgi import get_wsgi_application

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms_project.settings')

# Initialize Django
application = get_wsgi_application()

# --- Automatic superuser creation start ---
import django
from django.contrib.auth import get_user_model

django.setup()  # Make sure models and DB are ready

User = get_user_model()

# Only create superuser if it doesn't exist
if not User.objects.filter(email=os.environ.get("DJANGO_SUPERUSER_EMAIL")).exists():
    User.objects.create_superuser(
        username=os.environ.get("DJANGO_SUPERUSER_USERNAME"),
        email=os.environ.get("DJANGO_SUPERUSER_EMAIL"),
        password=os.environ.get("DJANGO_SUPERUSER_PASSWORD"),
    )
# --- Automatic superuser creation end ---

