# lms/forms.py
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from django import forms

class CustomSocialSignupForm(SocialSignupForm):
    """
    Custom form for social signup that doesn't require username
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Remove username field if it exists
        if 'username' in self.fields:
            self.fields.pop('username')
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Ensure email is set
        if not cleaned_data.get('email'):
            raise forms.ValidationError("Email is required")
        
        return cleaned_data
    
    def save(self, request):
        # Call parent save
        user = super().save(request)
        
        # Set username from email if not set
        if not user.username and user.email:
            user.username = user.email.split('@')[0]
            user.save()
        
        return user


        from django import forms
from .models import ContactMessage

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
