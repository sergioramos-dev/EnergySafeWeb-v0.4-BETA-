# main/rest_api.py

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
import json
from .models import CustomUser, Device, UserDevice, ConnectedAppliance, ApplianceConsumption, ApplianceAlert
import random
from datetime import datetime, timedelta

@csrf_exempt
@require_http_methods(["POST"])
def api_login(request):
    """API endpoint for user login"""
    try:
        data = json.loads(request.body)
        username_or_email = data.get('username_or_email')
        password = data.get('password')
        
        user = authenticate(request, username=username_or_email, password=password)
        
        if user is not None:
            login(request, user)
            token = "auth_token_" + user.id  # Simple token generation - in production use proper tokens
            
            return JsonResponse({
                'token': token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'date_joined': user.date_joined.isoformat(),
                    'is_active': user.is_active
                }
            })
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def api_register(request):
    """API endpoint for user registration"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if CustomUser.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)
        
        if CustomUser.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Email already exists'}, status=400)
        
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        token = "auth_token_" + user.id  # Simple token generation
        
        return JsonResponse({
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'date_joined': user.date_joined.isoformat(),
                'is_active': user.is_active
            }
        }, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def api_logout(request):
    """API endpoint for user logout"""
    logout(request)
    return JsonResponse({'success': True})

@csrf_exempt
@require_http_methods(["GET"])
def api_get_devices(request):
    """API endpoint to get user devices"""
    try:
        user_id = _get_user_id_from_request(request)
        
        user_devices = UserDevice.objects.filter(usuario_id=user_id, activo=True)
        devices_data = []
        
        for user_device in user_devices:
            try:
                device = Device.objects.get(id=user_device.dispositivo_id)
                devices_data.append({
                    'id': user_device.id,
                    'usuario_id': user_device.usuario_id,
                    'dispositivo_id': user_device.dispositivo_id,
                    'nombre_personalizado': user_device.nombre_personalizado,
                    'ubicacion': user_device.ubicacion,
                    'fecha_adquisicion': user_device.fecha_adquisicion.isoformat(),
                    'activo': user_device.activo,
                    'dispositivo': {
                        'id': device.id,
                        'nombre': device.nombre,
                        'numero_serie': device.numero_serie,
                        'descripcion': device.descripcion,
                        'fecha_fabricacion': device.fecha_fabricacion.isoformat(),
                        'disponible': device.disponible
                    }
                })
            except Device.DoesNotExist:
                devices_data.append({
                    'id': user_device.id,
                    'usuario_id': user_device.usuario_id,
                    'dispositivo_id': user_device.dispositivo_id,
                    'nombre_personalizado': user_device.nombre_personalizado,
                    'ubicacion': user_device.ubicacion,
                    'fecha_adquisicion': user_device.fecha_adquisicion.isoformat(),
                    'activo': user_device.activo,
                    'dispositivo': None
                })
        
        return JsonResponse(devices_data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def api_get_appliances(request):
    """API endpoint to get all appliances of a user"""
    try:
        user_id = _get_user_id_from_request(request)
        
        # Get user devices
        user_devices = UserDevice.objects.filter(usuario_id=user_id, activo=True)
        appliances_data = []
        
        for user_device in user_devices:
            appliances = ConnectedAppliance.objects.filter(user_device=user_device, activo=True)
            
            for appliance in appliances:
                appliances_data.append({
                    'id': appliance.id,
                    'user_device_id': str(appliance.user_device.id),
                    'nombre': appliance.nombre,
                    'tipo': appliance.tipo,
                    'icono': appliance.icono,
                    'voltaje': appliance.voltaje,
                    'fecha_conexion': appliance.fecha_conexion.isoformat(),
                    'activo': appliance.activo,
                    'apagado_periodico': appliance.apagado_periodico
                })
        
        return JsonResponse(appliances_data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def api_get_appliance(request, appliance_id):
    """API endpoint to get details of a specific appliance"""
    try:
        appliance = ConnectedAppliance.objects.get(id=appliance_id)
        
        # Verify user has access to this appliance
        user_id = _get_user_id_from_request(request)
        if appliance.user_device.usuario_id != user_id:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        appliance_data = {
            'id': appliance.id,
            'user_device_id': str(appliance.user_device.id),
            'nombre': appliance.nombre,
            'tipo': appliance.tipo,
            'icono': appliance.icono,
            'voltaje': appliance.voltaje,
            'fecha_conexion': appliance.fecha_conexion.isoformat(),
            'activo': appliance.activo,
            'apagado_periodico': appliance.apagado_periodico,
            'user_device': {
                'id': appliance.user_device.id,
                'nombre_personalizado': appliance.user_device.nombre_personalizado,
                'ubicacion': appliance.user_device.ubicacion
            }
        }
        
        return JsonResponse({'appliance': appliance_data})
    except ConnectedAppliance.DoesNotExist:
        return JsonResponse({'error': 'Appliance not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def api_verify_device(request, numero_serie):
    """API endpoint to verify an EnergySafe device by serial number"""
    try:
        try:
            device = Device.objects.get(numero_serie=numero_serie)
        except Device.DoesNotExist:
            return JsonResponse({
                'exists': False,
                'message': 'No se encontró ningún dispositivo con ese número de serie'
            })
        
        user_id = _get_user_id_from_request(request)
        
        # Check if already registered to this user
        user_device = UserDevice.objects.filter(
            dispositivo_id=device.id,
            usuario_id=user_id,
            activo=True
        ).first()
        
        if user_device:
            return JsonResponse({
                'exists': True,
                'available': False,
                'message': 'Ya tienes registrado este dispositivo EnergySafe'
            })
        
        # Device exists and is available
        return JsonResponse({
            'exists': True,
            'available': True,
            'device_name': device.nombre,
            'message': 'Dispositivo verificado correctamente'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def api_register_device(request):
    """API endpoint to register an EnergySafe device"""
    try:
        data = json.loads(request.body)
        numero_serie = data.get('numero_serie')
        nombre = data.get('nombre')
        ubicacion = data.get('ubicacion')
        
        try:
            device = Device.objects.get(numero_serie=numero_serie)
        except Device.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'No se encontró ningún dispositivo con ese número de serie'
            }, status=404)
        
        user_id = _get_user_id_from_request(request)
        
        # Check if already registered to this user
        user_device = UserDevice.objects.filter(
            dispositivo_id=device.id,
            usuario_id=user_id,
            activo=True
        ).first()
        
        if user_device:
            return JsonResponse({
                'success': False,
                'message': 'Ya tienes registrado este dispositivo EnergySafe'
            })
        
        # Register device
        user_device = UserDevice(
            usuario_id=user_id,
            dispositivo_id=device.id,
            nombre_personalizado=nombre or device.nombre,
            ubicacion=ubicacion,
            activo=True
        )
        user_device.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Dispositivo registrado correctamente',
            'id': user_device.id
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def api_add_appliance(request):
    """API endpoint to add an appliance"""
    try:
        data = json.loads(request.body)
        nombre = data.get('nombre-dispositivo', data.get('nombre'))
        tipo = data.get('icono', 'electrodomestico')
        icono = data.get('icono')
        voltaje_str = data.get('voltaje', '110')
        
        # Clean up voltage value
        voltaje = ''.join(c for c in str(voltaje_str) if c.isdigit())
        if not voltaje:
            voltaje = '110'
        
        try:
            voltaje_int = int(voltaje)
        except:
            voltaje_int = 110
        
        user_id = _get_user_id_from_request(request)
        
        # Get user device
        user_device = UserDevice.objects.filter(
            usuario_id=user_id,
            activo=True
        ).first()
        
        if not user_device:
            return JsonResponse({
                'success': False,
                'message': 'No se encontró un dispositivo EnergySafe activo para este usuario.'
            }, status=404)
        
        # Create appliance
        appliance = ConnectedAppliance(
            user_device=user_device,
            nombre=nombre,
            tipo=tipo,
            icono=icono,
            voltaje=voltaje_int,
            activo=True
        )
        appliance.save()
        
        # Generate some initial consumption data
        _generate_sample_consumption_data(appliance)
        
        return JsonResponse({
            'success': True,
            'message': 'Electrodoméstico agregado correctamente',
            'id': appliance.id
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def api_get_appliance_consumption(request, appliance_id):
    """API endpoint to get consumption data for an appliance"""
    try:
        appliance = ConnectedAppliance.objects.get(id=appliance_id)
        
        # Verify user has access to this appliance
        user_id = _get_user_id_from_request(request)
        if appliance.user_device.usuario_id != user_id:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        # Get consumption data
        consumption_data = ApplianceConsumption.objects.filter(
            appliance=appliance
        )