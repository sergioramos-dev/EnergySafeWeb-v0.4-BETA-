from allauth.socialaccount.models import SocialAccount
from django.db import IntegrityError

def complete_social_login(request, sociallogin):
    
    try:
        # Verificar si el usuario ya existe 
        SocialAccount.objects.get(
            provider=sociallogin.account.provider, 
            uid=sociallogin.account.uid
        )
        # Si llegamos aquí, la cuenta ya existe y está vinculada a un usuario
        # Solo actualizamos los datos extra
        existing_account = SocialAccount.objects.get(
            provider=sociallogin.account.provider, 
            uid=sociallogin.account.uid
        )
        existing_account.extra_data = sociallogin.account.extra_data
        existing_account.save()
        return
    except SocialAccount.DoesNotExist:
        # La cuenta no existe, intentamos guardarla
        try:
            sociallogin.save(request)
        except IntegrityError:
            # Manejar el error de integridad
            pass