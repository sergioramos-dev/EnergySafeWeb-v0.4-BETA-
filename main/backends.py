from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailOrUsernameModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(email=username)  # Si ingresó un correo
        except User.DoesNotExist:
            try:
                user = User.objects.get(username=username)  # Si ingresó un usuario
            except User.DoesNotExist:
                return None
        
        if user.check_password(password):
            return user
        return None
