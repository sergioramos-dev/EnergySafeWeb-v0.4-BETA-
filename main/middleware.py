from django.shortcuts import redirect
from django.urls import reverse
from django.db import DatabaseError
from django.utils import timezone
from allauth.socialaccount.models import SocialAccount
import re
from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from main.models import UserSession
import uuid
import json

class CustomSessionMiddleware(SessionMiddleware):
    def process_request(self, request):
        super().process_request(request)
        
        # Si el usuario está autenticado
        if request.user.is_authenticated:
            session_key = request.session.session_key
            
            if not session_key:
                request.session.create()
                session_key = request.session.session_key
            
            # Actualizar o crear registro de sesión
            try:
                user_session = UserSession.objects.get(
                    user_id=request.user.id,
                    session_key=session_key
                )
                user_session.last_activity = timezone.now()
                user_session.save()
            except UserSession.DoesNotExist:
                user_data = {
                    'username': request.user.username,
                    'email': request.user.email,
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'ip_address': self.get_client_ip(request)
                }
                
                UserSession.objects.create(
                    user_id=request.user.id,
                    session_key=session_key,
                    session_data=json.dumps(user_data),
                    created_at=timezone.now(),
                    last_activity=timezone.now()
                )
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class SocialLoginErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except DatabaseError as e:
            error_msg = str(e)
            if "duplicate key error" in error_msg and "socialaccount_socialaccount" in error_msg:
                match = re.search(r'provider: "([^"]+)", uid: "([^"]+)"', error_msg)
                if match:
                    provider, uid = match.groups()
                    try:
                        social_account = SocialAccount.objects.get(provider=provider, uid=uid)
                        from django.contrib.auth import login
                        login(request, social_account.user)
                        return redirect(reverse('home'))
                    except Exception:
                        pass
            return redirect(reverse('login'))
    
# Añadir a main/middleware.py

class TokenAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # No procesamos para rutas administrativas o de autenticación
        if request.path.startswith('/admin/') or request.path.startswith('/api/mobile/login/') or request.path.startswith('/api/mobile/register/'):
            return self.get_response(request)
            
        # Verificar si hay token en el encabezado Authorization
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Token '):
            token_key = auth_header.split(' ')[1].strip()
            
            # Buscar el token
            from main.models import AuthToken
            try:
                token = AuthToken.objects.get(id=token_key, is_active=True)
                
                # Verificar si el token está expirado
                if token.is_expired:
                    from django.http import JsonResponse
                    return JsonResponse({
                        'success': False,
                        'message': 'Token expirado'
                    }, status=401)
                
                # Establecer el usuario autenticado en la solicitud
                request.user = token.user
                request.auth_token = token
                request.is_token_auth = True
            except AuthToken.DoesNotExist:
                # No hacer nada si el token no existe, seguirá como anonymous user
                pass
        
        # Continuar con la solicitud
        response = self.get_response(request)
        return response