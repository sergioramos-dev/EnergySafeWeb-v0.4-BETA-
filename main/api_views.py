# main/api_views.py

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime
from main.models import ApplianceAutoShutdown, ConnectedAppliance, ApplianceConsumption, ApplianceAlert, ApplianceControlState
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from datetime import datetime
import json

@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def device_alerts(request):
    """
    Endpoint para recibir alertas de dispositivos ESP32.
    POST /api/device-alerts/
    """
    # Manejar CORS manualmente
    response = JsonResponse({'status': 'ok'})
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type'
    
    # Si es una solicitud OPTIONS (preflight), devolver respuesta vacía con headers CORS
    if request.method == 'OPTIONS':
        return response
    
    try:
        # Decodificar los datos JSON recibidos
        data = json.loads(request.body)
        
        # Extraer los datos de la solicitud
        appliance_id = data.get('appliance_id')
        tipo = data.get('tipo', 'voltaje')
        mensaje = data.get('mensaje', 'Alerta de voltaje anormal')
        
        # Validar datos mínimos requeridos
        if not appliance_id:
            response = JsonResponse({'error': 'Se requiere ID del electrodoméstico'}, status=400)
            return response
        
        # Buscar el electrodoméstico
        try:
            appliance = ConnectedAppliance.objects.get(id=appliance_id)
        except ConnectedAppliance.DoesNotExist:
            response = JsonResponse({'error': f'Electrodoméstico con ID {appliance_id} no encontrado'}, status=404)
            return response
        
        # Usar timezone-aware datetime para evitar warnings
        from django.utils import timezone
        
        # Crear el registro de alerta
        alert = ApplianceAlert(
            appliance=appliance,
            fecha=timezone.now(),
            tipo=tipo,
            mensaje=mensaje,
            atendida=False
        )
        alert.save()
        
        # Generar la respuesta
        response = JsonResponse({
            'success': True,
            'message': 'Alerta recibida y almacenada correctamente',
            'data': {
                'id': alert.id,
                'appliance_id': appliance.id,
                'timestamp': alert.fecha.isoformat()
            }
        })
        return response
        
    except json.JSONDecodeError:
        response = JsonResponse({'error': 'JSON inválido'}, status=400)
        return response
    except Exception as e:
        import traceback
        print(f"Error al procesar alerta: {str(e)}")
        print(traceback.format_exc())
        response = JsonResponse({'error': str(e)}, status=500)
        return response

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from main.models import ApplianceConsumption, ConnectedAppliance
from django.utils.timezone import now
from datetime import timedelta

@login_required
def get_latest_consumption(request, appliance_id):
    """
    API endpoint to get the latest consumption data for a specific appliance.
    GET /api/consumption/latest/{appliance_id}/
    """
    try:
        # Verify the user has access to this appliance
        appliance = ConnectedAppliance.objects.get(id=appliance_id)
        
        if str(appliance.user_device.usuario_id) != str(request.user.id):
            return JsonResponse({
                'success': False,
                'message': 'No tienes acceso a este electrodoméstico'
            }, status=403)
        
        # Get the latest consumption data
        latest_consumption = ApplianceConsumption.objects.filter(
            appliance_id=appliance_id
        ).order_by('-fecha').first()
        
        if not latest_consumption:
            return JsonResponse({
                'success': False,
                'message': 'No hay datos de consumo para este electrodoméstico'
            })
        
        # Get consumption data for the last 7 days for the chart
        seven_days_ago = now() - timedelta(days=7)
        consumption_data = list(ApplianceConsumption.objects.filter(
            appliance_id=appliance_id,
            fecha__gte=seven_days_ago
        ).order_by('-fecha')[:30])  # Limit to 30 records
        
        # Calculate daily consumption
        days = ['lun', 'mar', 'mir', 'jue', 'vie', 'sab', 'dom']
        daily_consumption = {day: 0 for day in days}
        
        # Calculate stats
        voltage_values = [c.voltaje for c in consumption_data if c.voltaje is not None]
        current_values = [c.corriente for c in consumption_data if c.corriente is not None]
        
        voltage_stats = {
            'avg': sum(voltage_values) / len(voltage_values) if voltage_values else 0,
            'max': max(voltage_values) if voltage_values else 0,
            'min': min(voltage_values) if voltage_values else 0
        }
        
        current_stats = {
            'avg': sum(current_values) / len(current_values) if current_values else 0,
            'max': max(current_values) if current_values else 0,
            'min': min(current_values) if current_values else 0
        }
        
        # Process the consumption data for the chart
        for consumption in consumption_data:
            if hasattr(consumption, 'fecha') and consumption.fecha:
                day_name = consumption.fecha.strftime('%a').lower()[:3]
                if day_name in daily_consumption:
                    daily_consumption[day_name] += consumption.consumo or 0
        
        # Get recent history for the table
        history = []
        for i, c in enumerate(consumption_data[:10]):  # Limit to 10 most recent records
            history.append({
                'id': i + 1,
                'fecha': c.fecha.strftime('%Y/%m/%d %H:%M:%S') if c.fecha else '',
                'voltaje': c.voltaje or 0,
                'corriente': c.corriente or 0,
                'potencia': c.potencia or 0,
                'consumo': c.consumo or 0,
                'frecuencia': c.frecuencia or 60
            })
        
        # Get active alerts
        alerts = []
        try:
            alert_objects = ApplianceAlert.objects.filter(
                appliance=appliance,
                atendida=False
            ).order_by('-fecha')[:5]
            
            for alert in alert_objects:
                alerts.append({
                    'id': str(alert.id),
                    'fecha': alert.fecha.strftime('%Y/%m/%d %H:%M:%S') if alert.fecha else '',
                    'tipo': alert.tipo,
                    'mensaje': alert.mensaje,
                    'atendida': alert.atendida
                })
        except Exception as e:
            print(f"Error al obtener alertas: {e}")
            import traceback
            print(traceback.format_exc())

        # Get control state
        try:
            control_state, created = ApplianceControlState.objects.get_or_create(
                appliance=appliance,
                defaults={'state': True}
            )
            is_device_on = control_state.state
        except Exception as e:
            is_device_on = True  # Default to ON if there's an error
            print(f"Error al obtener estado de control: {e}")
        
        # Return the processed data
        return JsonResponse({
            'success': True,
            'latest': {
                'fecha': latest_consumption.fecha.strftime('%Y-%m-%d %H:%M:%S') if latest_consumption.fecha else '',
                'voltaje': latest_consumption.voltaje or 0,
                'corriente': latest_consumption.corriente or 0,
                'potencia': latest_consumption.potencia or 0,
                'consumo': latest_consumption.consumo or 0,
                'frecuencia': latest_consumption.frecuencia or 60
            },
            'daily_consumption': daily_consumption,
            'voltage_stats': voltage_stats,
            'current_stats': current_stats,
            'history': history,
            'alerts': alerts,
            'is_device_on': is_device_on
        })
    
    except ConnectedAppliance.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Electrodoméstico no encontrado'
        }, status=404)
    
    except Exception as e:
        import traceback
        print(f"Error in get_latest_consumption: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener datos: {str(e)}'
        }, status=500)
    
# Agregar esta función a api_views.py
@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def device_shutdown(request):
    """
    Endpoint para configurar el auto-apagado de dispositivos.
    POST /api/device-shutdown/
    """
    # Manejar CORS manualmente
    response = JsonResponse({'status': 'ok'})
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    
    # Si es una solicitud OPTIONS (preflight), devolver respuesta con headers CORS
    if request.method == 'OPTIONS':
        return response
    
    try:
        # Decodificar los datos JSON recibidos
        data = json.loads(request.body)
        
        # Extraer los datos de la solicitud
        appliance_id = data.get('appliance_id')
        hours_on = data.get('hours_on', 0)
        minutes_on = data.get('minutes_on', 0)
        hours_off = data.get('hours_off', 0)
        minutes_off = data.get('minutes_off', 0)
        
        # Determinar si se está habilitando (valores > 0) o deshabilitando (todos valores = 0)
        is_enabled = not (hours_on == 0 and minutes_on == 0 and hours_off == 0 and minutes_off == 0)
        
        # Validar datos mínimos requeridos
        if not appliance_id:
            return JsonResponse({'error': 'Se requiere ID del electrodoméstico'}, status=400)
        
        # Buscar el electrodoméstico
        try:
            appliance = ConnectedAppliance.objects.get(id=appliance_id)
        except ConnectedAppliance.DoesNotExist:
            return JsonResponse({'error': f'Electrodoméstico con ID {appliance_id} no encontrado'}, status=404)
        
        # Obtener o crear el estado de control
        from django.utils import timezone
        
        control_state, created = ApplianceControlState.objects.get_or_create(
            appliance=appliance,
            defaults={'state': True}  # Por defecto encendido
        )
        
        # Actualizar configuración de auto-apagado
        control_state.auto_shutdown_enabled = is_enabled
        control_state.hours_on = hours_on
        control_state.minutes_on = minutes_on
        control_state.hours_off = hours_off
        control_state.minutes_off = minutes_off
        
        # Si se está habilitando, también actualizar timestamp
        if is_enabled:
            control_state.last_state_change = timezone.now()
        
        control_state.save()
        
        # Información de depuración
        if is_enabled:
            print(f"Auto-apagado configurado para {appliance.nombre}: ON durante {hours_on}h:{minutes_on}m, OFF durante {hours_off}h:{minutes_off}m")
        else:
            print(f"Auto-apagado desactivado para {appliance.nombre}")
        
        # Generar respuesta
        return JsonResponse({
            'success': True,
            'message': f'Auto-apagado {"configurado" if is_enabled else "desactivado"} correctamente',
            'data': {
                'appliance_id': str(appliance.id),
                'auto_shutdown_enabled': is_enabled,
                'hours_on': hours_on,
                'minutes_on': minutes_on,
                'hours_off': hours_off,
                'minutes_off': minutes_off,
                'timestamp': timezone.now().isoformat()
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        import traceback
        print(f"Error en device_shutdown: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)
    
@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def device_readings(request):
    """
    Endpoint para recibir lecturas de dispositivos ESP32.
    POST /api/device-readings/
    """
    # Manejar CORS manualmente
    response = JsonResponse({'status': 'ok'})
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type'
    
    # Si es una solicitud OPTIONS (preflight), devolver respuesta vacía con headers CORS
    if request.method == 'OPTIONS':
        return response
    
    try:
        # Decodificar los datos JSON recibidos
        data = json.loads(request.body)
        
        # Extraer los datos de la solicitud
        appliance_id = data.get('appliance_id')
        voltaje = data.get('voltaje', 0)
        corriente = data.get('corriente', 0)
        potencia = data.get('potencia', 0)
        consumo = data.get('consumo', 0)
        frecuencia = data.get('frecuencia', 60)
        
        # Validar datos mínimos requeridos
        if not appliance_id:
            response = JsonResponse({'error': 'Se requiere ID del electrodoméstico'}, status=400)
            return response
        
        # Buscar el electrodoméstico
        try:
            appliance = ConnectedAppliance.objects.get(id=appliance_id)
        except ConnectedAppliance.DoesNotExist:
            response = JsonResponse({'error': f'Electrodoméstico con ID {appliance_id} no encontrado'}, status=404)
            return response
        
        # Usar timezone-aware datetime
        from django.utils import timezone
        
        # Crear el registro de consumo
        consumption = ApplianceConsumption.objects.create(
            appliance=appliance,
            fecha=timezone.now(),
            voltaje=voltaje,
            corriente=corriente,
            potencia=potencia,
            consumo=consumo,
            frecuencia=frecuencia
        )
        
        # Generar la respuesta
        response = JsonResponse({
            'success': True,
            'message': 'Datos recibidos y almacenados correctamente',
            'data': {
                'id': consumption.id,
                'appliance_id': appliance.id,
                'timestamp': consumption.fecha.isoformat()
            }
        })
        return response
        
    except json.JSONDecodeError:
        response = JsonResponse({'error': 'JSON inválido'}, status=400)
        return response
    except Exception as e:
        import traceback
        print(f"Error en device_readings: {str(e)}")
        print(traceback.format_exc())
        response = JsonResponse({'error': str(e)}, status=500)
        return response
    
@csrf_exempt
@require_http_methods(["POST"])
def mark_alert_attended(request, alert_id):
    """
    Endpoint para marcar una alerta como atendida.
    POST /api/alerts/attend/{alert_id}/
    """
    try:
        # Buscar la alerta
        alert = ApplianceAlert.objects.get(id=alert_id)
        
        # Marcar como atendida
        alert.atendida = True
        alert.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Alerta marcada como atendida correctamente'
        })
    except ApplianceAlert.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Alerta no encontrada'
        }, status=404)
    except Exception as e:
        import traceback
        print(f"Error al marcar alerta como atendida: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from main.models import UserDevice, ConnectedAppliance

@csrf_exempt
def get_user_appliances(request):
    """
    API endpoint to get the user's appliances for mobile app
    GET /api/mobile/appliances/
    """
    try:
        # Check for authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Token '):
            return JsonResponse({
                'success': False,
                'message': 'No authentication token provided'
            }, status=401)
        
        token_key = auth_header.split(' ')[1].strip()
        
        # Verify token
        from main.models import AuthToken
        try:
            token = AuthToken.objects.get(id=token_key)
            if not token.is_active:
                return JsonResponse({
                    'success': False,
                    'message': 'Token inactive'
                }, status=401)
            
            if token.is_expired:
                return JsonResponse({
                    'success': False,
                    'message': 'Token expired'
                }, status=401)
            
            # Get the user from the token
            user = token.user
            
            # Get the user's devices - Avoid using complex filters with Djongo
            # First get all user devices
            all_user_devices = list(UserDevice.objects.all())
            
            # Then manually filter for this user and active devices
            user_devices = []
            for device in all_user_devices:
                if device.usuario_id == str(user.id) and device.activo:
                    user_devices.append(device)
            
            if not user_devices:
                return JsonResponse({
                    'success': True,
                    'appliances': [],
                    'message': 'No EnergySafe device found for this user'
                })
            
            # Get the appliances for each user device
            all_appliances = []
            for user_device in user_devices:
                # Get all appliances
                all_device_appliances = list(ConnectedAppliance.objects.filter(user_device=user_device))
                
                # Manually filter for active appliances
                for appliance in all_device_appliances:
                    if appliance.activo:
                        all_appliances.append({
                            'id': str(appliance.id),
                            'name': appliance.nombre,
                            'type': appliance.tipo,
                            'icon': appliance.icono,
                            'voltage': appliance.voltaje,
                            'connectionDate': str(appliance.fecha_conexion),
                            'active': appliance.activo
                        })
            
            return JsonResponse({
                'success': True,
                'appliances': all_appliances
            })
            
        except AuthToken.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid token'
            }, status=401)
            
    except Exception as e:
        import traceback
        print(f"Error in get_user_appliances: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)

@csrf_exempt
def get_appliance_data(request, appliance_id):
    """
    API endpoint to get real-time energy data for a specific appliance
    GET /api/mobile/appliance/{appliance_id}/data/
    """
    try:
        # Check for authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Token '):
            return JsonResponse({
                'success': False,
                'message': 'No authentication token provided'
            }, status=401)
        
        token_key = auth_header.split(' ')[1].strip()
        
        # Verify token
        from main.models import AuthToken
        try:
            token = AuthToken.objects.get(id=token_key)
            if not token.is_active or token.is_expired:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid token'
                }, status=401)
            
            # Get the appliance
            from main.models import ConnectedAppliance, ApplianceConsumption
            try:
                appliance = ConnectedAppliance.objects.get(id=appliance_id)
                
                # Verify this appliance belongs to the user - manual check to avoid complex Djongo queries
                if str(appliance.user_device.usuario_id) != str(token.user.id):
                    return JsonResponse({
                        'success': False,
                        'message': 'Unauthorized access to this appliance'
                    }, status=403)
                
                # Get all consumption data and sort manually to find the latest
                all_consumption = list(ApplianceConsumption.objects.filter(appliance=appliance))
                
                # Sort by date (descending)
                all_consumption.sort(key=lambda x: x.fecha, reverse=True)
                
                # Get the first item (latest)
                consumption = all_consumption[0] if all_consumption else None
                
                # Get control state
                try:
                    control_state, created = ApplianceControlState.objects.get_or_create(
                        appliance=appliance,
                        defaults={'state': True}
                    )
                    is_device_on = control_state.state
                except Exception as e:
                    is_device_on = True  # Default to ON if there's an error
                    print(f"Error getting control state: {e}")
                
                # If no consumption data, return default values
                if not consumption:
                    return JsonResponse({
                        'success': True,
                        'data': {
                            'voltage': appliance.voltaje,
                            'current': 0,
                            'power': 0,
                            'energy': 0,
                            'frequency': 60,
                            'timestamp': str(appliance.fecha_conexion),
                            'is_device_on': is_device_on
                        }
                    })
                
                # Return the data
                return JsonResponse({
                    'success': True,
                    'data': {
                        'voltage': consumption.voltaje,
                        'current': consumption.corriente,
                        'power': consumption.potencia,
                        'energy': consumption.consumo,
                        'frequency': consumption.frecuencia,
                        'timestamp': str(consumption.fecha),
                        'is_device_on': is_device_on
                    }
                })
                
            except ConnectedAppliance.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Appliance not found'
                }, status=404)
                
        except AuthToken.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid token'
            }, status=401)
            
    except Exception as e:
        import traceback
        print(f"Error in get_appliance_data: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def device_control(request):
    """
    Endpoint para controlar dispositivos desde la app móvil.
    POST /api/device-control/
    """
    # Manejar CORS manualmente
    response = JsonResponse({'status': 'ok'})
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type'
    
    # Si es una solicitud OPTIONS (preflight), devolver respuesta vacía con headers CORS
    if request.method == 'OPTIONS':
        return response
    
    try:
        # Decodificar los datos JSON recibidos
        data = json.loads(request.body)
        
        # Extraer los datos de la solicitud
        appliance_id = data.get('appliance_id')
        state = data.get('state', False)  # False = OFF, True = ON
        
        # Validar datos mínimos requeridos
        if not appliance_id:
            return JsonResponse({'error': 'Se requiere ID del electrodoméstico'}, status=400)
        
        # Buscar el electrodoméstico
        try:
            appliance = ConnectedAppliance.objects.get(id=appliance_id)
        except ConnectedAppliance.DoesNotExist:
            return JsonResponse({'error': f'Electrodoméstico con ID {appliance_id} no encontrado'}, status=404)
        
        # Crear o actualizar el estado del dispositivo en la base de datos
        from django.utils import timezone
        
        ApplianceControlState.objects.update_or_create(
            appliance=appliance,
            defaults={
                'state': state,
                'last_updated': timezone.now()
            }
        )
        
        # Generar la respuesta
        return JsonResponse({
            'success': True,
            'message': f'Dispositivo {"encendido" if state else "apagado"} correctamente',
            'data': {
                'appliance_id': appliance.id,
                'state': state,
                'timestamp': timezone.now().isoformat()
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        import traceback
        print(f"Error en device_control: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def device_control_state(request):
    """
    Endpoint para que los dispositivos ESP32 obtengan su estado de control actual.
    GET /api/device-control-state/?appliance_id=XXX
    """
    # Manejar CORS manualmente
    response = JsonResponse({'status': 'ok'})
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type'
    
    # Si es una solicitud OPTIONS (preflight), devolver respuesta vacía con headers CORS
    if request.method == 'OPTIONS':
        return response
    
    try:
        # Obtener el ID del electrodoméstico de los parámetros de consulta
        appliance_id = request.GET.get('appliance_id')
        
        # Validar datos mínimos requeridos
        if not appliance_id:
            return JsonResponse({'error': 'Se requiere ID del electrodoméstico'}, status=400)
        
        # Buscar el electrodoméstico
        try:
            appliance = ConnectedAppliance.objects.get(id=appliance_id)
        except ConnectedAppliance.DoesNotExist:
            return JsonResponse({'error': f'Electrodoméstico con ID {appliance_id} no encontrado'}, status=404)
        
        # Obtener el estado de control actual
        try:
            control_state = ApplianceControlState.objects.get(appliance=appliance)
            state = control_state.state
        except ApplianceControlState.DoesNotExist:
            # Si no existe estado de control, crear uno por defecto (encendido)
            state = True
            ApplianceControlState.objects.create(appliance=appliance, state=state)
        
        # Generar la respuesta
        return JsonResponse({
            'success': True,
            'state': state
        })
        
    except Exception as e:
        import traceback
        print(f"Error en device_control_state: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def device_control_state(request):
    """
    Endpoint para que los dispositivos ESP32 obtengan su estado de control actual.
    GET /api/device-control-state/?appliance_id=XXX
    """
    # Manejar CORS manualmente
    response = JsonResponse({'status': 'ok'})
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type'
    
    # Si es una solicitud OPTIONS (preflight), devolver respuesta vacía con headers CORS
    if request.method == 'OPTIONS':
        return response
    
    try:
        # Obtener el ID del electrodoméstico de los parámetros de consulta
        appliance_id = request.GET.get('appliance_id')
        
        # Validar datos mínimos requeridos
        if not appliance_id:
            return JsonResponse({'error': 'Se requiere ID del electrodoméstico'}, status=400)
        
        # Buscar el electrodoméstico
        try:
            appliance = ConnectedAppliance.objects.get(id=appliance_id)
        except ConnectedAppliance.DoesNotExist:
            return JsonResponse({'error': f'Electrodoméstico con ID {appliance_id} no encontrado'}, status=404)
        
        # Obtener el estado de control actual
        try:
            control_state, created = ApplianceControlState.objects.get_or_create(
                appliance=appliance,
                defaults={'state': True}
            )
            state = control_state.state
        except Exception as e:
            # Si no existe estado de control, asumir encendido
            state = True
            print(f"Error: {e}")
        
        # Generar la respuesta
        return JsonResponse({
            'success': True,
            'state': state
        })
        
    except Exception as e:
        import traceback
        print(f"Error en device_control_state: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)
    
# main/api_views.py - Añadir estos métodos

@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def device_auto_shutdown(request):
    """
    Endpoint para configurar el auto-apagado de un dispositivo
    POST /api/device-auto-shutdown/
    """
    # Imprimir información detallada de la solicitud
    print("\n" + "=" * 50)
    print("CONFIGURACIÓN DE AUTO-SHUTDOWN")
    print("=" * 50)
    print(f"Método de solicitud: {request.method}")
    print(f"Contenido de la solicitud: {request.body}")

    # Manejar CORS manualmente
    response = JsonResponse({'status': 'ok'})
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    
    # Si es una solicitud OPTIONS (preflight), devolver respuesta vacía con headers CORS
    if request.method == 'OPTIONS':
        return response
    
    try:
        # Decodificar los datos JSON recibidos
        data = json.loads(request.body)
        
        # Extraer los datos de la solicitud con más información de depuración
        appliance_id = data.get('appliance_id')
        hours_on = data.get('hours_on', 0)
        minutes_on = data.get('minutes_on', 0)
        hours_off = data.get('hours_off', 0)
        minutes_off = data.get('minutes_off', 0)
        enabled = data.get('enabled', False)
        
        # Log detallado de los datos recibidos
        print("Datos recibidos:")
        print(f"Appliance ID: {appliance_id}")
        print(f"Horas encendido: {hours_on}")
        print(f"Minutos encendido: {minutes_on}")
        print(f"Horas apagado: {hours_off}")
        print(f"Minutos apagado: {minutes_off}")
        print(f"Habilitado: {enabled}")
        
        # Validar datos mínimos requeridos
        if not appliance_id:
            print("ERROR: No se proporcionó ID de electrodoméstico")
            return JsonResponse({'error': 'Se requiere ID del electrodoméstico'}, status=400)
        
        # Buscar el electrodoméstico con más información de depuración
        try:
            appliance = ConnectedAppliance.objects.get(id=appliance_id)
            print(f"Electrodoméstico encontrado: {appliance.nombre}")
        except ConnectedAppliance.DoesNotExist:
            print(f"ERROR: Electrodoméstico con ID {appliance_id} no encontrado")
            return JsonResponse({'error': f'Electrodoméstico con ID {appliance_id} no encontrado'}, status=404)
        
        # Usar timezone-aware datetime
        from django.utils import timezone
        now = timezone.now()
        
        # Crear o actualizar la configuración de auto-apagado con más logs
        print("Creando/Actualizando configuración de auto-apagado...")
        auto_shutdown, created = ApplianceAutoShutdown.objects.update_or_create(
            appliance=appliance,
            defaults={
                'hours_on': hours_on,
                'minutes_on': minutes_on,
                'hours_off': hours_off,
                'minutes_off': minutes_off,
                'enabled': enabled,
                'last_switch': now,
                'next_switch': now + timezone.timedelta(hours=hours_on, minutes=minutes_on) if enabled else now,
                'current_state': True if enabled else False  # Si se habilita, comenzar encendido
            }
        )
        
        print(f"Configuración {'creada' if created else 'actualizada'} exitosamente")
        print(f"ID de configuración: {auto_shutdown.id}")
        print(f"Próximo cambio: {auto_shutdown.next_switch}")
        
        # Si se está activando, asegurarse de que el dispositivo esté encendido
        if enabled:
            print("Actualizando estado de control del dispositivo...")
            control_state, control_created = ApplianceControlState.objects.update_or_create(
                appliance=appliance,
                defaults={
                    'state': True,
                    'last_updated': now
                }
            )
            print(f"Estado de control {'creado' if control_created else 'actualizado'}")
        
        # Generar la respuesta
        return JsonResponse({
            'success': True,
            'message': 'Auto-apagado configurado correctamente',
            'data': {
                'id': auto_shutdown.id,
                'appliance_id': appliance.id,
                'enabled': auto_shutdown.enabled,
                'next_switch': auto_shutdown.next_switch.isoformat() if auto_shutdown.enabled else None
            }
        })
        
    except json.JSONDecodeError:
        print("ERROR: JSON inválido")
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        import traceback
        print("ERROR CRÍTICO AL CONFIGURAR AUTO-APAGADO:")
        print(f"Error: {str(e)}")
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def device_auto_shutdown_config(request):
    """
    Endpoint para obtener la configuración de auto-apagado de un dispositivo
    GET /api/device-auto-shutdown-config/?appliance_id=XXX
    """
    # Manejar CORS manualmente
    response = JsonResponse({'status': 'ok'})
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    
    # Si es una solicitud OPTIONS (preflight), devolver respuesta vacía con headers CORS
    if request.method == 'OPTIONS':
        return response
    
    try:
        # Obtener el ID del electrodoméstico de los parámetros de consulta
        appliance_id = request.GET.get('appliance_id')
        
        # Validar datos mínimos requeridos
        if not appliance_id:
            return JsonResponse({'error': 'Se requiere ID del electrodoméstico'}, status=400)
        
        # Buscar el electrodoméstico
        try:
            appliance = ConnectedAppliance.objects.get(id=appliance_id)
        except ConnectedAppliance.DoesNotExist:
            return JsonResponse({'error': f'Electrodoméstico con ID {appliance_id} no encontrado'}, status=404)
        
        # Obtener la configuración de auto-apagado
        try:
            config = ApplianceAutoShutdown.objects.get(appliance=appliance)
            
            # Obtener el estado actual del dispositivo
            try:
                control_state = ApplianceControlState.objects.get(appliance=appliance)
                current_state = control_state.state
            except ApplianceControlState.DoesNotExist:
                current_state = True
            
            # Generar la respuesta
            return JsonResponse({
                'success': True,
                'config': {
                    'id': config.id,
                    'appliance_id': appliance.id,
                    'hours_on': config.hours_on,
                    'minutes_on': config.minutes_on,
                    'hours_off': config.hours_off,
                    'minutes_off': config.minutes_off,
                    'enabled': config.enabled,
                    'current_state': current_state,
                    'next_switch_time': config.next_switch.isoformat() if config.enabled else '',
                    'created_at': config.created_at.isoformat(),
                    'updated_at': config.updated_at.isoformat()
                }
            })
        except ApplianceAutoShutdown.DoesNotExist:
            # No hay configuración, devolver respuesta vacía
            return JsonResponse({
                'success': True,
                'config': None
            })
        
    except Exception as e:
        import traceback
        print(f"Error al obtener configuración de auto-apagado: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)
    
@csrf_exempt
def get_auto_shutdown_status(request, appliance_id):
    try:
        config = ApplianceAutoShutdown.objects.get(appliance_id=appliance_id)
        
        # Obtener estado de control actual
        control_state, _ = ApplianceControlState.objects.get_or_create(
            appliance_id=appliance_id,
            defaults={'state': True}
        )
        
        return JsonResponse({
            'success': True,
            'config': {
                'enabled': config.enabled,
                'hours_on': config.hours_on,
                'minutes_on': config.minutes_on,
                'hours_off': config.hours_off,
                'minutes_off': config.minutes_off,
                'current_state': config.current_state,
                'next_switch': config.next_switch.isoformat(),
                'current_device_state': control_state.state
            }
        })
    except ApplianceAutoShutdown.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'No hay configuración de auto-apagado'
        }, status=404)