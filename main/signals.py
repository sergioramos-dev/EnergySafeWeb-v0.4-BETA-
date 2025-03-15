from allauth.socialaccount.signals import pre_social_login
from django.dispatch import receiver
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()

@receiver(pre_social_login)
def social_login_handler(sender, request, sociallogin, **kwargs):
    try:
        social_account = SocialAccount.objects.get(
            provider=sociallogin.account.provider, 
            uid=sociallogin.account.uid
        )
        
        sociallogin.user = social_account.user
        
        social_account.extra_data = sociallogin.account.extra_data
        social_account.save()
        
    except SocialAccount.DoesNotExist:
        email = sociallogin.account.extra_data.get('email')
        if email:
            try:
                existing_user = User.objects.get(email=email)
                
                sociallogin.user = existing_user
                
            except User.DoesNotExist:
                pass