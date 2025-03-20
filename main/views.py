from django.shortcuts import redirect, render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import json

# No importes los modelos aquí para evitar la importación circular
# Importamos los modelos dentro de cada función donde se necesitan

User = get_user_model()


class SocialAccountAdapter:
    """Adaptador para allauth"""
    pass

def aviso_de_privacidad(request):
    return render(request, 'aviso-privacidad.html')

def blog(request):
    return render(request, 'blog.html')

def soporte(request):
    return render(request, 'centroayuda.html')

def index(request):
    return render(request, 'index.html')

def home(request):
    return render(request, 'home.html')

def download(request):
    return render(request, 'download.html')

def aboutus(request):
    return render(request, 'about-us.html')

def productos(request):
    return render(request, 'productos.html')
def devices(request):
    return render(request, 'devices.html')

def device_info(request):
    return render(request, 'devices-info.html')

def optimiza_consumo(request):
    return render(request, 'optimiza-consumo.html')

def conoce_mas(request):
    return render(request, 'conoce-mas.html')

def registerUserManager(request):
    if request.method == "GET":
        return render(request, 'login.html')

    if request.method == "POST":
        email = request.POST.get("email")
        username = request.POST.get("username")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            return HttpResponse("El usuario ya existe")

        try:
            user = User.objects.create_user(username=username, password=password, email=email)
            return redirect('login')
        except Exception as e:
            return HttpResponse(f"Error al crear usuario: {e}")

def loginUserManager(request):
    if request.method == "GET":
        return render(request, 'login.html')

    if request.method == "POST":
        username_or_email = request.POST.get("username_or_email")  
        password = request.POST.get("password")

        user = authenticate(request, username=username_or_email, password=password) 

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'login.html', {'error': 'Credenciales incorrectas'})

@login_required
def logoutUser(request):
    # Implementaremos la lógica de sesiones después de resolver el problema de importación
    logout(request)
    return redirect('login')

from django.http import JsonResponse
from django.middleware.csrf import get_token

def get_csrf_token(request):
    """
    Endpoint to retrieve CSRF token for mobile/frontend applications
    """
    return JsonResponse({
        'csrfToken': get_token(request)
    })

# main/views.py

from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json

@csrf_exempt
@require_POST
def mobile_login(request):
    """
    Custom login view for mobile authentication
    Bypasses CSRF protection for mobile apps
    """
    try:
        # Parse JSON data
        data = json.loads(request.body)
        username_or_email = data.get('username_or_email')
        password = data.get('password')

        # Validate input
        if not username_or_email or not password:
            return JsonResponse({
                'success': False, 
                'message': 'Username/email and password are required'
            }, status=400)

        # Use custom authentication backend
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Try to find user by email or username
        try:
            # First try to find by email
            user = User.objects.get(email=username_or_email)
        except User.DoesNotExist:
            # If not found by email, try by username
            try:
                user = User.objects.get(username=username_or_email)
            except User.DoesNotExist:
                return JsonResponse({
                    'success': False, 
                    'message': 'User not found'
                }, status=404)

        # Authenticate user
        auth_user = authenticate(request, username=user.username, password=password)
        
        if auth_user is not None:
            # Log the user in
            login(request, auth_user)
            
            return JsonResponse({
                'success': True, 
                'message': 'Login successful',
                'user': {
                    'id': auth_user.id,
                    'username': auth_user.username,
                    'email': auth_user.email
                }
            })
        else:
            return JsonResponse({
                'success': False, 
                'message': 'Invalid credentials'
            }, status=401)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False, 
            'message': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': str(e)
        }, status=500)