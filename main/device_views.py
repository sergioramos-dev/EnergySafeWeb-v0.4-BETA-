# main/device_views.py - Versión mínima
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json

@login_required
def devices_dashboard(request):
    """Vista principal para dispositivos"""
    from main.models import UserDevice, ConnectedAppliance, Device
    
    # Obtener dispositivos del usuario
    user_devices = list(UserDevice.objects.filter(usuario_id=request.user.id))
    user_device = user_devices[0] if user_devices else None
    
    # Si hay un dispositivo del usuario, obtener datos completos
    device_info = None
    if user_device:
        try:
            # Obtener la información del dispositivo directamente
            device = Device.objects.get(id=user_device.dispositivo_id)
            device_info = {
                'nombre': device.nombre,
                'numero_serie': device.numero_serie,
                'descripcion': device.descripcion
            }
        except Device.DoesNotExist:
            device_info = {
                'nombre': 'Dispositivo',
                'numero_serie': 'No disponible',
                'descripcion': ''
            }
    
    # Obtener electrodomésticos
    appliances = []
    if user_device:
        appliances = list(ConnectedAppliance.objects.filter(user_device=user_device))
        appliances = [a for a in appliances if a.activo]
    
    context = {
        'user_device': user_device,
        'device_info': device_info,
        'appliances': appliances
    }
    
    return render(request, 'devices.html', context)

@login_required
@csrf_exempt
def verify_energy_safe(request, numero_serie):
    """Verifica si existe un dispositivo EnergySafe"""
    from main.models import Device, UserDevice
    
    try:
        device = Device.objects.get(numero_serie=numero_serie)
        
        # Verificar si ya está asignado a este usuario
        user_devices = list(UserDevice.objects.filter(dispositivo=device, usuario=request.user))
        already_assigned = any(d.activo for d in user_devices)
        
        if already_assigned:
            return JsonResponse({
                'exists': True,
                'available': False,
                'message': 'Ya tienes registrado este dispositivo EnergySafe'
            })
        
        # El dispositivo existe y está disponible
        return JsonResponse({
            'exists': True,
            'available': True,
            'device_name': device.nombre,
            'message': 'Dispositivo verificado correctamente'
        })
        
    except Device.DoesNotExist:
        return JsonResponse({
            'exists': False,
            'message': 'No se encontró ningún dispositivo con ese número de serie'
        })

@login_required
@csrf_exempt
def register_energy_safe(request):
    """Registra un dispositivo EnergySafe"""
    from main.models import Device, UserDevice
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            numero_serie = request.POST.get('numero_serie')
            nombre = request.POST.get('nombre')
            ubicacion = request.POST.get('ubicacion', '')
            
            # Verificar que el dispositivo existe
            try:
                device = Device.objects.get(numero_serie=numero_serie)
                
                # Crear dispositivo para el usuario usando IDs directamente
                user_device = UserDevice(
                    usuario_id=request.user.id,
                    dispositivo_id=device.id,
                    nombre_personalizado=nombre,
                    ubicacion=ubicacion,
                    activo=True
                )
                user_device.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Dispositivo registrado correctamente'
                })
                
            except Device.DoesNotExist:
                # Para pruebas - si eres admin
                if request.user.is_staff:
                    device = Device(
                        nombre='EnergySafe Device',
                        numero_serie=numero_serie,
                        descripcion='Dispositivo registrado automáticamente',
                        disponible=True
                    )
                    device.save()
                    
                    user_device = UserDevice(
                        usuario_id=request.user.id,
                        dispositivo_id=device.id,
                        nombre_personalizado=nombre or 'Mi EnergySafe',
                        ubicacion=ubicacion,
                        activo=True
                    )
                    user_device.save()
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Dispositivo creado y registrado correctamente'
                    })
                    
                return JsonResponse({
                    'success': False,
                    'message': 'No se encontró ningún dispositivo con ese número de serie'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return redirect('devices')

@login_required
@csrf_exempt
def add_appliance(request):
    """Añade un electrodoméstico"""
    from main.models import UserDevice, ConnectedAppliance
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    if request.method == 'POST':
        try:
            # Obtener todos los datos POST para depuración
            print(f"POST data: {request.POST}")
            
            # Obtener datos del formulario
            nombre = request.POST.get('nombre-dispositivo', '')
            if not nombre:
                nombre = request.POST.get('tv', 'Televisor')
            
            tipo = request.POST.get('icono', 'television')
            icono = request.POST.get('icono', 'television')
            voltaje_str = request.POST.get('voltaje', '110 V')
            
            # Limpiar el valor de voltaje (quitar "V" y espacios)
            voltaje = ''.join(c for c in voltaje_str if c.isdigit())
            if not voltaje:
                voltaje = '110'
            
            try:
                voltaje_int = int(voltaje)
            except:
                voltaje_int = 110
            
            # Obtener usuario y dispositivo manualmente, evitando consultas complejas
            user_id = request.user.id
            print(f"User ID: {user_id}")
            
            # Verificar si hay dispositivos para este usuario directamente por ID
            # Esta es una solución alternativa que evita el problema de Djongo
            try:
                # Obtener el primer dispositivo activo del usuario por ID
                user_device = None
                all_devices = UserDevice.objects.all()
                for device in all_devices:
                    if device.usuario_id == user_id and device.activo:
                        user_device = device
                        break
                
                if not user_device:
                    return JsonResponse({
                        'success': False,
                        'message': 'No se encontró un dispositivo EnergySafe activo para este usuario.'
                    })
                
                # Crear el electrodoméstico
                appliance = ConnectedAppliance(
                    user_device=user_device,
                    nombre=nombre,
                    tipo=tipo,
                    icono=icono,
                    voltaje=voltaje_int,
                    activo=True
                )
                appliance.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Electrodoméstico agregado correctamente',
                    'id': appliance.id
                })
                
            except Exception as inner_e:
                print(f"Error interno: {str(inner_e)}")
                import traceback
                print(traceback.format_exc())
                return JsonResponse({
                    'success': False,
                    'message': f'Error al buscar o crear dispositivo: {str(inner_e)}'
                })
            
        except Exception as e:
            import traceback
            print(f"Error al agregar electrodoméstico: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

@login_required
def appliance_details(request, appliance_id):
    """Detalles de un electrodoméstico - Función mínima para evitar errores"""
    return redirect('devices')