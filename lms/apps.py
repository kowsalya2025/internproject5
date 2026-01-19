# apps.py in your lms app
from django.apps import AppConfig

class LmsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lms'
    
    # Remove or comment out the ready method if you don't have signals
    # def ready(self):
    #     import lms.signals
