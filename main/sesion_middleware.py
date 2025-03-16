# Este middleware rastreará las sesiones de usuario

class SessionTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Procesar la solicitud antes de que la vista sea llamada
        response = self.get_response(request)
        
        # Actualizar la actividad de la sesión si el usuario está autenticado
        if request.user.is_authenticated and hasattr(request, 'session'):
            # Importamos aquí para evitar importaciones circulares
            from main.session_manager import update_session_activity
            update_session_activity(request)
        
        return response

    def get_client_ip(self, request):
        """Obtiene la dirección IP del cliente."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip