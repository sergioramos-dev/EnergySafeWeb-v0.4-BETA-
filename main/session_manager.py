from django.utils import timezone
import json

def get_client_ip(request):
    """Obtiene la dirección IP del cliente."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def create_user_session(request, user):
    """
    Crea un registro de sesión de usuario.
    Debe ser llamado después de que el usuario haya iniciado sesión.
    """
    from main.models import UserSession
    
    if not hasattr(request, 'session') or not request.session.session_key:
        request.session.create()
    
    session_key = request.session.session_key
    
    # Datos a guardar en la sesión
    user_data = {
        'username': user.username,
        'email': user.email,
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        'ip_address': get_client_ip(request),
        'login_time': timezone.now().isoformat()
    }
    
    # Crear o actualizar sesión
    try:
        session = UserSession.objects.get(session_key=session_key)
        session.user = user
        session.last_activity = timezone.now()
        session.is_active = True
        session.session_data = json.dumps(user_data)
        session.save()
    except UserSession.DoesNotExist:
        UserSession.objects.create(
            user=user,
            session_key=session_key,
            session_data=json.dumps(user_data),
            created_at=timezone.now(),
            last_activity=timezone.now(),
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            is_active=True
        )
    
    return True

def update_session_activity(request):
    """
    Actualiza la actividad de la sesión actual.
    """
    from main.models import UserSession
    
    if not request.user.is_authenticated or not hasattr(request, 'session'):
        return False
    
    session_key = request.session.session_key
    if not session_key:
        return False
    
    try:
        session = UserSession.objects.get(
            user=request.user,
            session_key=session_key,
            is_active=True
        )
        session.last_activity = timezone.now()
        session.save(update_fields=['last_activity'])
        return True
    except UserSession.DoesNotExist:
        return False

def end_session(session_id, user=None):
    """
    Finaliza una sesión específica.
    """
    from main.models import UserSession
    
    try:
        if user:
            session = UserSession.objects.get(id=session_id, user=user)
        else:
            session = UserSession.objects.get(id=session_id)
        
        session.is_active = False
        session.save(update_fields=['is_active'])
        return True
    except UserSession.DoesNotExist:
        return False

def get_user_active_sessions(user):
    """
    Obtiene todas las sesiones activas de un usuario.
    """
    from main.models import UserSession
    
    return UserSession.objects.filter(
        user=user,
        is_active=True
    ).order_by('-last_activity')

def end_all_sessions(user, current_session_key=None):
    """
    Finaliza todas las sesiones de un usuario, excepto la actual si se especifica.
    """
    from main.models import UserSession
    
    sessions = UserSession.objects.filter(user=user, is_active=True)
    
    if current_session_key:
        sessions = sessions.exclude(session_key=current_session_key)
    
    return sessions.update(is_active=False)