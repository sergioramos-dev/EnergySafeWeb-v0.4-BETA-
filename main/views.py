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


# Reemplazar la función mobile_login existente en main/views.py


# Reemplaza la función mobile_login actual con esta versión

@csrf_exempt
@require_POST
def mobile_login(request):
    """
    Vista de autenticación para aplicaciones móviles.
    Utiliza autenticación basada en tokens en lugar de sesiones.
    """
    try:
        # Analizar datos JSON
        data = json.loads(request.body)
        username_or_email = data.get('username_or_email')
        password = data.get('password')
        device_info = data.get('device_info', {})  # Información opcional del dispositivo
        
        # Validar entrada
        if not username_or_email or not password:
            return JsonResponse({
                'success': False, 
                'message': 'Se requiere nombre de usuario/correo y contraseña'
            }, status=400)

        # Buscar usuario por email o nombre de usuario
        try:
            # Primero intentar buscar por email
            user = User.objects.get(email=username_or_email)  
        except User.DoesNotExist:
            try:
                # Si no se encuentra por email, intentar por nombre de usuario
                user = User.objects.get(username=username_or_email)  
            except User.DoesNotExist:
                return JsonResponse({
                    'success': False, 
                    'message': 'Usuario no encontrado'
                }, status=404)

        # Autenticar usuario
        auth_user = authenticate(request, username=user.username, password=password)
        
        if auth_user is not None:
            # Crear o obtener token
            from main.models import AuthToken
            
            # Desactivar tokens antiguos - MODIFICACIÓN AQUÍ
            # Usando dos filtros separados para evitar el problema de Djongo
            try:
                user_tokens = AuthToken.objects.filter(user=auth_user)
                for token in user_tokens:
                    if token.is_active:
                        token.is_active = False
                        token.save()
            except Exception as e:
                print(f"Advertencia: No se pudieron desactivar tokens antiguos: {e}")
                # Continuamos aunque haya error en este paso
            
            # Crear nuevo token
            device_info_str = json.dumps(device_info) if device_info else None
            token = AuthToken.objects.create(
                user=auth_user,
                device_info=device_info_str,
                # Establecer expiración si es necesario - p.ej., 30 días desde ahora
                expires_at=timezone.now() + timezone.timedelta(days=30)
            )
            
            # Devolver token y datos de usuario
            return JsonResponse({
                'success': True, 
                'message': 'Inicio de sesión exitoso',
                'token': token.id,
                'user': {
                    'id': auth_user.id,
                    'username': auth_user.username,
                    'email': auth_user.email
                }
            })
        else:
            return JsonResponse({
                'success': False, 
                'message': 'Credenciales inválidas'
            }, status=401)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False, 
            'message': 'JSON inválido'
        }, status=400)
    except Exception as e:
        import traceback
        print(f"Error en mobile_login: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False, 
            'message': f'Error: {str(e)}'
        }, status=500)
            
@csrf_exempt
@require_POST
def mobile_register(request):
    """
    Vista de registro para aplicaciones móviles.
    Crea un nuevo usuario y devuelve un token de autenticación.
    """
    try:
        # Analizar datos JSON
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        device_info = data.get('device_info', {})
        
        # Validar entrada
        if not username or not email or not password:
            return JsonResponse({
                'success': False, 
                'message': 'Se requiere nombre de usuario, correo y contraseña'
            }, status=400)
        
        # Verificar si el nombre de usuario o correo ya existen
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                'success': False, 
                'message': 'El nombre de usuario ya existe'
            }, status=400)
        
        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False, 
                'message': 'El correo electrónico ya existe'
            }, status=400)
        
        # Crear nuevo usuario
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # Crear token para el nuevo usuario
        from main.models import AuthToken
        device_info_str = json.dumps(device_info) if device_info else None
        token = AuthToken.objects.create(
            user=user,
            device_info=device_info_str,
            expires_at=timezone.now() + timezone.timedelta(days=30)
        )
        
        # Devolver respuesta exitosa
        return JsonResponse({
            'success': True, 
            'message': 'Registro exitoso',
            'token': token.id,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False, 
            'message': 'JSON inválido'
        }, status=400)
    except Exception as e:
        import traceback
        print(f"Error en mobile_register: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False, 
            'message': f'Error: {str(e)}'
        }, status=500)
    
# Añadir estas funciones a main/views.py
# Replace the verify_token function in main/views.py with this version

@csrf_exempt
def verify_token(request):
    """
    Verifica si un token es válido.
    GET con Authorization: Token <token>
    """
    from main.models import AuthToken
    
    # Verificar si hay token en el encabezado Authorization
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Token '):
        return JsonResponse({
            'success': False,
            'message': 'Token no proporcionado'
        }, status=401)
    
    token_key = auth_header.split(' ')[1].strip()
    
    # Buscar el token - Modificado para prevenir el error de Djongo
    try:
        # Primero buscar el token sin incluir el is_active en la consulta 
        token = AuthToken.objects.get(id=token_key)
        
        # Luego verificar manualmente si está activo
        if not token.is_active:
            return JsonResponse({
                'success': False,
                'message': 'Token inactivo'
            }, status=401)
        
        # Verificar si el token está expirado
        if token.is_expired:
            return JsonResponse({
                'success': False,
                'message': 'Token expirado'
            }, status=401)
        
        # Token válido
        return JsonResponse({
            'success': True,
            'message': 'Token válido',
            'user': {
                'id': token.user.id,
                'username': token.user.username,
                'email': token.user.email
            }
        })
    except AuthToken.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Token inválido'
        }, status=401)
    except Exception as e:
        import traceback
        print(f"Error en verify_token: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)
    
@csrf_exempt
@require_POST
def mobile_logout(request):
    """
    Cierra la sesión invalida el token actual.
    POST con Authorization: Token <token>
    """
    from main.models import AuthToken
    
    # Verificar si hay token en el encabezado Authorization
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Token '):
        return JsonResponse({
            'success': False,
            'message': 'Token no proporcionado'
        }, status=400)
    
    token_key = auth_header.split(' ')[1].strip()
    
    # Buscar y desactivar el token
    try:
        # Modificado para Djongo - en vez de hacer update()
        token = AuthToken.objects.get(id=token_key)
        token.is_active = False
        token.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Sesión cerrada exitosamente'
        })
    except AuthToken.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Token inválido'
        }, status=400)
    
