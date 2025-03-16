# main/session_views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.utils import timezone
import json

@login_required
def user_sessions(request):
    """Vista para mostrar las sesiones activas del usuario."""
    from main.models import UserSession
    
    active_sessions = UserSession.objects.filter(
        user=request.user, 
        is_active=True
    ).order_by('-last_activity')
    
    context = {
        'active_sessions': active_sessions,
        'current_session_key': request.session.session_key
    }
    
    return render(request, 'user_sessions.html', context)

@login_required
def end_session(request, session_id):
    """Vista para finalizar una sesión específica."""
    from main.models import UserSession
    from main.session_manager import end_session as end_user_session
    
    try:
        session = UserSession.objects.get(id=session_id, user=request.user)
        is_current = session.session_key == request.session.session_key
        
        end_user_session(session_id, request.user)
        
        if is_current:
            logout(request)
            return redirect('login')
        
        return redirect('user_sessions')
    except UserSession.DoesNotExist:
        return redirect('user_sessions')

@login_required
def end_all_sessions(request):
    """Vista para finalizar todas las sesiones excepto la actual."""
    from main.session_manager import end_all_sessions
    
    end_all_sessions(request.user, request.session.session_key)
    return redirect('user_sessions')

@login_required
def api_sessions(request):
    """API para obtener información de sesiones en formato JSON."""
    from main.models import UserSession
    
    active_sessions = UserSession.objects.filter(
        user=request.user, 
        is_active=True
    ).order_by('-last_activity')
    
    sessions_data = []
    for session in active_sessions:
        try:
            session_data = json.loads(session.session_data) if session.session_data else {}
        except:
            session_data = {}
        
        sessions_data.append({
            'id': session.id,
            'created_at': session.created_at.isoformat(),
            'last_activity': session.last_activity.isoformat(),
            'is_current': session.session_key == request.session.session_key,
            'ip_address': session.ip_address,
            'user_agent': session.user_agent,
            'data': session_data
        })
    
    return JsonResponse({'sessions': sessions_data})