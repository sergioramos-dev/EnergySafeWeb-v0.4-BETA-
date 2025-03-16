# main/device_views.py - Versión mínima
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json

@login_required
def devices_dashboard(request):
    """Vista principal para dispositivos"""
    from main.models import UserDevice, ConnectedAppliance
    
    # Obtener dispositivos del usuario
    user_devices = list(UserDevice.objects.filter(usuario=request.user))
    user_device = user_devices[0] if user_devices else None
    
    # Obtener electrodomésticos
    appliances = []
    if user_device:
        appliances = list(ConnectedAppliance.objects.filter(user_device=user_device))
        appliances = [a for a in appliances if a.activo]
    
    context = {
        'user_device': user_device,
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
    
    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre-dispositivo')
            tipo = request.POST.get('tipo') or request.POST.get('icono')
            icono = request.POST.get('icono')
            voltaje = request.POST.get('voltaje')
            
            # Verificar que el usuario tiene un dispositivo
            user_devices = list(UserDevice.objects.filter(usuario=request.user, activo=True))
            
            if not user_devices:
                return JsonResponse({
                    'success': False,
                    'message': 'Primero debes registrar un dispositivo EnergySafe'
                })
            
            user_device = user_devices[0]
            
            # Crear el electrodoméstico
            appliance = ConnectedAppliance(
                user_device=user_device,
                nombre=nombre,
                tipo=tipo or icono,
                icono=icono,
                voltaje=int(voltaje) if voltaje else 120,
                activo=True
            )
            appliance.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Electrodoméstico agregado correctamente',
                'id': appliance.id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return redirect('devices')

@login_required
def appliance_details(request, appliance_id):
    """Detalles de un electrodoméstico - Función mínima para evitar errores"""
    return redirect('devices')