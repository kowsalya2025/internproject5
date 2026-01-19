# lms/adapters.py
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import perform_login
from allauth.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect
from django.contrib import messages
import uuid

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # This is called just before a social login is processed
        user = sociallogin.user
        
        # Generate a username from email if needed
        if not user.username and user.email:
            # Use email prefix as username
            user.username = user.email.split('@')[0]
        
        # Check if this email already exists
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            existing_user = User.objects.get(email=user.email)
            
            # Connect social account to existing user
            sociallogin.connect(request, existing_user)
            
            # Perform login
            perform_login(request, existing_user, email_verification='none')
            raise ImmediateHttpResponse(redirect('home'))
            
        except User.DoesNotExist:
            pass
    
    def populate_user(self, request, sociallogin, data):
        """
        Populate user instance without username field
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Set email as username if needed
        if not user.username and user.email:
            user.username = user.email.split('@')[0]
        
        # Get name from social account
        extra_data = sociallogin.account.extra_data
        if not user.first_name and 'given_name' in extra_data:
            user.first_name = extra_data.get('given_name', '')
        if not user.last_name and 'family_name' in extra_data:
            user.last_name = extra_data.get('family_name', '')
        
        return user
    
    def save_user(self, request, sociallogin, form=None):
        """
        Save the user without requiring username
        """
        user = sociallogin.user
        
        # Ensure username is set
        if not user.username:
            if user.email:
                user.username = user.email.split('@')[0]
            else:
                # Generate a random username
                user.username = f"user_{uuid.uuid4().hex[:8]}"
        
        # Save the user
        user.save()
        
        # Save the social account
        sociallogin.save(request)
        
        return user