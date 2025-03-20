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
    
    # Obtener dispositivos del usuario - usando una consulta más simple
    # En vez de filtrar por usuario_id y activo juntos, hacemos las consultas por separado
    try:
        # Primero obtenemos todos los UserDevice
        all_user_devices = UserDevice.objects.all()
        
        # Luego filtramos manualmente 
        user_devices = []
        for device in all_user_devices:
            if device.usuario_id == str(request.user.id) and device.activo:
                user_devices.append(device)
        
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
            try:
                # Obtener todos los electrodomésticos
                all_appliances = ConnectedAppliance.objects.all()
                
                # Filtrar manualmente
                for appliance in all_appliances:
                    if str(appliance.user_device.id) == str(user_device.id) and appliance.activo:
                        appliances.append(appliance)
            except Exception as e:
                print(f"Error al obtener electrodomésticos: {e}")
        
        context = {
            'user_device': user_device,
            'device_info': device_info,
            'appliances': appliances
        }
        
        return render(request, 'devices.html', context)
    
    except Exception as e:
        import traceback
        print(f"Error en devices_dashboard: {e}")
        print(traceback.format_exc())
        
        # Contexto vacío como fallback
        context = {
            'user_device': None,
            'device_info': None,
            'appliances': []
        }
        
        return render(request, 'devices.html', context)


@login_required
@csrf_exempt
def verify_energy_safe(request, numero_serie):
    """Verifica si existe un dispositivo EnergySafe"""
    from main.models import Device, UserDevice
    import traceback
    
    try:
        try:
            # Buscar el dispositivo por número de serie
            device = Device.objects.get(numero_serie=numero_serie)
        except Device.DoesNotExist:
            return JsonResponse({
                'exists': False,
                'message': 'No se encontró ningún dispositivo con ese número de serie'
            })
        
        # Verificar si ya está asignado a este usuario
        try:
            # Obtener todos los dispositivos de usuario
            all_devices = UserDevice.objects.all()
            
            # Filtrar manualmente para evitar problemas con Djongo
            for existing in all_devices:
                if existing.dispositivo_id == str(device.id):
                    if existing.usuario_id == str(request.user.id) and existing.activo:
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
        except Exception as e:
            print(f"Error al verificar asignación: {e}")
            print(traceback.format_exc())
            
            # En caso de error, asumir que está disponible (pero registrarlo)
            return JsonResponse({
                'exists': True,
                'available': True,
                'device_name': device.nombre,
                'message': 'Dispositivo verificado correctamente (con advertencia)'
            })
    
    except Exception as e:
        print(f"Error global en verify_energy_safe: {e}")
        print(traceback.format_exc())
        
        return JsonResponse({
            'exists': False,
            'message': f'Error al verificar el dispositivo: {str(e)}'
        })    

@login_required
@csrf_exempt
def register_energy_safe(request):
    """Registra un dispositivo EnergySafe"""
    from main.models import Device, UserDevice
    import traceback
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            numero_serie = request.POST.get('numero_serie')
            nombre = request.POST.get('nombre')
            ubicacion = request.POST.get('ubicacion', '')
            
            # Verificar que el dispositivo existe
            try:
                device = Device.objects.get(numero_serie=numero_serie)
            except Device.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'No se encontró ningún dispositivo con ese número de serie'
                })
            
            # Verificar si ya está asociado a este usuario
            try:
                # Obtener todos los dispositivos
                all_devices = UserDevice.objects.all()
                
                # Buscar manualmente
                for existing in all_devices:
                    if (existing.dispositivo_id == str(device.id) and 
                        existing.usuario_id == str(request.user.id) and 
                        existing.activo):
                        return JsonResponse({
                            'success': False,
                            'message': 'Ya tienes registrado este dispositivo EnergySafe'
                        })
                
                # Si llegamos aquí, podemos registrar el dispositivo
                user_device = UserDevice(
                    usuario_id=str(request.user.id),
                    dispositivo_id=str(device.id),
                    nombre_personalizado=nombre or device.nombre,
                    ubicacion=ubicacion,
                    activo=True
                )
                user_device.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Dispositivo registrado correctamente'
                })
            
            except Exception as e:
                print(f"Error al verificar o crear dispositivo: {e}")
                print(traceback.format_exc())
                return JsonResponse({
                    'success': False,
                    'message': f'Error: {str(e)}'
                })
        
        except Exception as e:
            print(f"Error global en register_energy_safe: {e}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    })

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
            
            tipo = request.POST.get('tipo', 'television')
            
            # Get the icon value from the form - this will now be the image identifier
            # instead of just the icon name
            icono = request.POST.get('icono', '')
            
            voltaje_str = request.POST.get('voltaje', '110')
            
            # Limpiar el valor de voltaje (quitar "V" y espacios)
            voltaje = ''.join(c for c in voltaje_str if c.isdigit())
            if not voltaje:
                voltaje = '110'
            
            try:
                voltaje_int = int(voltaje)
            except:
                voltaje_int = 110
            
            # Obtener usuario y dispositivo
            user_id = request.user.id
            print(f"User ID: {user_id}")
            
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
                
                # Crear el electrodoméstico con el icono seleccionado
                appliance = ConnectedAppliance(
                    user_device=user_device,
                    nombre=nombre,
                    tipo=tipo,
                    icono=icono,  # This is now the image identifier, not just the icon name
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

@login_required
def appliance_details(request, appliance_id):
    """Vista detallada para la información y datos de consumo de un electrodoméstico."""
    from main.models import ConnectedAppliance, ApplianceConsumption
    from django.db.models import Avg, Max, Min
    import json
    from datetime import datetime, timedelta
    import traceback
    
    try:
        # Obtener el electrodoméstico
        appliance = ConnectedAppliance.objects.get(id=appliance_id)
        
        # Verificar que el usuario tenga acceso a este electrodoméstico
        if str(appliance.user_device.usuario_id) != str(request.user.id):
            return redirect('devices')
        
        # Obtener el último dato de consumo
        latest_consumption = ApplianceConsumption.objects.filter(
            appliance=appliance
        ).order_by('-fecha').first()
        
        # Si no hay datos de consumo, usar valores predeterminados
        if not latest_consumption:
            latest_consumption = {
                'voltaje': appliance.voltaje,
                'corriente': 0,
                'potencia': 0,
                'consumo': 0,
                'frecuencia': 60,
                'fecha': datetime.now()
            }
        
        # Obtener datos de los últimos 7 días para las gráficas
        seven_days_ago = datetime.now() - timedelta(days=7)
        consumption_data = list(ApplianceConsumption.objects.filter(
            appliance=appliance,
            fecha__gte=seven_days_ago
        ).order_by('fecha'))
        
        # Preparar datos para la gráfica de consumo diario
        days = ['lun', 'mar', 'mir', 'jue', 'vie', 'sab', 'dom']
        daily_consumption = {day: 0 for day in days}
        
        # Si hay datos de consumo, calcular el consumo diario
        if consumption_data:
            for consumption in consumption_data:
                day_name = consumption.fecha.strftime('%a').lower()[:3]
                if day_name in daily_consumption:
                    daily_consumption[day_name] += consumption.consumo
        else:
            # Si no hay datos, usar datos de ejemplo
            daily_consumption = {
                'lun': 2,
                'mar': 10,
                'mir': 8,
                'jue': 12,
                'vie': 13,
                'sab': 17,
                'dom': 9
            }
        
        # Obtener estadísticas de voltaje/corriente
        voltage_stats = {
            'avg': 110,
            'max': 120,
            'min': 100
        }
        current_stats = {
            'avg': 2,
            'max': 5,
            'min': 1
        }
        
        # Si hay datos, calcular estadísticas reales
        if consumption_data:
            voltage_stats = {
                'avg': sum(c.voltaje for c in consumption_data) / len(consumption_data),
                'max': max(c.voltaje for c in consumption_data),
                'min': min(c.voltaje for c in consumption_data)
            }
            current_stats = {
                'avg': sum(c.corriente for c in consumption_data) / len(consumption_data),
                'max': max(c.corriente for c in consumption_data),
                'min': min(c.corriente for c in consumption_data)
            }
        
        # Obtener alertas con manejo de error mejorado
        alerts = []
        try:
            # Intentar importar el modelo de alertas
            from main.models import ApplianceAlert
            
            try:
                # Esta consulta está causando problemas con Djongo - modificada para evitar NOT
                # En lugar de atendida=False, usamos atendida__exact=False que es más compatible
                alerts = list(ApplianceAlert.objects.filter(
                    appliance=appliance
                ).filter(atendida__exact=False).order_by('-fecha')[:5])
            except Exception as e:
                print(f"Error al obtener alertas con el primer método: {e}")
                print(traceback.format_exc())
                
                try:
                    # Segunda opción: obtener todas las alertas y filtrar manualmente
                    all_alerts = list(ApplianceAlert.objects.filter(
                        appliance=appliance
                    ).order_by('-fecha')[:20])  # Obtenemos más para tener suficientes después de filtrar
                    
                    # Filtrar manualmente
                    alerts = [alert for alert in all_alerts if not alert.atendida][:5]
                except Exception as e2:
                    print(f"Error al obtener alertas con el segundo método: {e2}")
                    print(traceback.format_exc())
                    
                    # Si ambos métodos fallan, usar datos de ejemplo
                    alerts = [{
                        'mensaje': 'Se ha detectado un voltaje fuera del rango seguro en tu dispositivo.',
                        'fecha': datetime.now()
                    }]
        except ImportError:
            # Si el modelo no existe, usar datos de ejemplo
            alerts = [{
                'mensaje': 'Se ha detectado un voltaje fuera del rango seguro en tu dispositivo.',
                'fecha': datetime.now()
            }]
        
        # Obtener historial de consumo para la tabla
        consumption_history = list(ApplianceConsumption.objects.filter(
            appliance=appliance
        ).order_by('-fecha')[:10])
        
        # Si no hay historial, crear datos de ejemplo
        if not consumption_history:
            dates = [datetime.now() - timedelta(days=i) for i in range(4)]
            consumption_history = [
                {'id': 1, 'fecha': dates[0], 'voltaje': 110, 'corriente': 5, 'potencia': 540, 'consumo': 1, 'frecuencia': 60},
                {'id': 2, 'fecha': dates[1], 'voltaje': 70, 'corriente': 10, 'potencia': 430, 'consumo': 3, 'frecuencia': 60},
                {'id': 3, 'fecha': dates[2], 'voltaje': 80, 'corriente': 2, 'potencia': 40, 'consumo': 5, 'frecuencia': 60},
                {'id': 4, 'fecha': dates[3], 'voltaje': 10, 'corriente': 5, 'potencia': 426, 'consumo': 6, 'frecuencia': 60}
            ]
        
        # Datos para el gráfico circular (ejemplo de distribución semanal)
        pie_chart_data = [
            {"nombre": "Semana 1", "valor": 20, "color": "#2196F3"},
            {"nombre": "Semana 2", "valor": 15, "color": "#4CAF50"},
            {"nombre": "Semana 3", "valor": 15, "color": "#FFEB3B"},
            {"nombre": "Semana 4", "valor": 25, "color": "#F44336"},
            {"nombre": "Semana 5", "valor": 0, "color": "#E91E63"}
        ]
        
        context = {
            'appliance': appliance,
            'latest_consumption': latest_consumption,
            'daily_consumption': json.dumps(daily_consumption),
            'voltage_stats': voltage_stats,
            'current_stats': current_stats,
            'consumption_history': consumption_history,
            'alerts': alerts,
            'pie_chart_data': json.dumps(pie_chart_data)
        }
        
        return render(request, 'devices-info.html', context)
        
    except ConnectedAppliance.DoesNotExist:
        return redirect('devices')
    except Exception as e:
        print(f"Error general en appliance_details: {e}")
        print(traceback.format_exc())
        return redirect('devices')
    """Vista detallada para la información y datos de consumo de un electrodoméstico."""
    from main.models import ConnectedAppliance, ApplianceConsumption
    from django.db.models import Avg, Max, Min
    import json
    from datetime import datetime, timedelta
    
    try:
        # Obtener el electrodoméstico
        appliance = ConnectedAppliance.objects.get(id=appliance_id)
        
        # Verificar que el usuario tenga acceso a este electrodoméstico
        if appliance.user_device.usuario_id != request.user.id:
            return redirect('devices')
        
        # Obtener el último dato de consumo
        latest_consumption = ApplianceConsumption.objects.filter(
            appliance=appliance
        ).order_by('-fecha').first()
        
        # Si no hay datos de consumo, usar valores predeterminados
        if not latest_consumption:
            latest_consumption = {
                'voltaje': appliance.voltaje,
                'corriente': 0,
                'potencia': 0,
                'consumo': 0,
                'frecuencia': 60,
                'fecha': datetime.now()
            }
        
        # Obtener datos de los últimos 7 días para las gráficas
        seven_days_ago = datetime.now() - timedelta(days=7)
        consumption_data = list(ApplianceConsumption.objects.filter(
            appliance=appliance,
            fecha__gte=seven_days_ago
        ).order_by('fecha'))
        
        # Preparar datos para la gráfica de consumo diario
        days = ['lun', 'mar', 'mir', 'jue', 'vie', 'sab', 'dom']
        daily_consumption = {day: 0 for day in days}
        
        # Si hay datos de consumo, calcular el consumo diario
        if consumption_data:
            for consumption in consumption_data:
                day_name = consumption.fecha.strftime('%a').lower()[:3]
                if day_name in daily_consumption:
                    daily_consumption[day_name] += consumption.consumo
        else:
            # Si no hay datos, usar datos de ejemplo
            daily_consumption = {
                'lun': 2,
                'mar': 10,
                'mir': 8,
                'jue': 12,
                'vie': 13,
                'sab': 17,
                'dom': 9
            }
        
        # Obtener estadísticas de voltaje/corriente
        voltage_stats = {
            'avg': 110,
            'max': 120,
            'min': 100
        }
        current_stats = {
            'avg': 2,
            'max': 5,
            'min': 1
        }
        
        # Si hay datos, calcular estadísticas reales
        if consumption_data:
            voltage_stats = {
                'avg': sum(c.voltaje for c in consumption_data) / len(consumption_data),
                'max': max(c.voltaje for c in consumption_data),
                'min': min(c.voltaje for c in consumption_data)
            }
            current_stats = {
                'avg': sum(c.corriente for c in consumption_data) / len(consumption_data),
                'max': max(c.corriente for c in consumption_data),
                'min': min(c.corriente for c in consumption_data)
            }
        
        # Obtener alertas
        alerts = []
        try:
            # Si el modelo ApplianceAlert existe
            from main.models import ApplianceAlert
            alerts = ApplianceAlert.objects.filter(
                appliance=appliance,
                atendida=False
            ).order_by('-fecha')[:5]
        except ImportError:
            # Si no existe, usar datos de ejemplo
            alerts = [{
                'mensaje': 'Se ha detectado un voltaje fuera del rango seguro en tu dispositivo.',
                'fecha': datetime.now()
            }]
        
        # Obtener historial de consumo para la tabla
        consumption_history = list(ApplianceConsumption.objects.filter(
            appliance=appliance
        ).order_by('-fecha')[:10])
        
        # Si no hay historial, crear datos de ejemplo
        if not consumption_history:
            dates = [datetime.now() - timedelta(days=i) for i in range(4)]
            consumption_history = [
                {'id': 1, 'fecha': dates[0], 'voltaje': 110, 'corriente': 5, 'potencia': 540, 'consumo': 1, 'frecuencia': 60},
                {'id': 2, 'fecha': dates[1], 'voltaje': 70, 'corriente': 10, 'potencia': 430, 'consumo': 3, 'frecuencia': 60},
                {'id': 3, 'fecha': dates[2], 'voltaje': 80, 'corriente': 2, 'potencia': 40, 'consumo': 5, 'frecuencia': 60},
                {'id': 4, 'fecha': dates[3], 'voltaje': 10, 'corriente': 5, 'potencia': 426, 'consumo': 6, 'frecuencia': 60}
            ]
        
        # Datos para el gráfico circular (ejemplo de distribución semanal)
        pie_chart_data = [
            {"nombre": "Semana 1", "valor": 20, "color": "#2196F3"},
            {"nombre": "Semana 2", "valor": 15, "color": "#4CAF50"},
            {"nombre": "Semana 3", "valor": 15, "color": "#FFEB3B"},
            {"nombre": "Semana 4", "valor": 25, "color": "#F44336"},
            {"nombre": "Semana 5", "valor": 0, "color": "#E91E63"}
        ]
        
        context = {
            'appliance': appliance,
            'latest_consumption': latest_consumption,
            'daily_consumption': json.dumps(daily_consumption),
            'voltage_stats': voltage_stats,
            'current_stats': current_stats,
            'consumption_history': consumption_history,
            'alerts': alerts,
            'pie_chart_data': json.dumps(pie_chart_data)
        }
        
        return render(request, 'devices-info.html', context)
        
    except ConnectedAppliance.DoesNotExist:
        return redirect('devices')  