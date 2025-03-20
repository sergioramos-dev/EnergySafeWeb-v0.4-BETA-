# main/api_views.py

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime
from main.models import ConnectedAppliance, ApplianceConsumption
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from main.models import ConnectedAppliance, ApplianceAlert
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
# Add this function to main/api_views.py

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
        seven_days_ago = timezone.now() - timedelta(days=7)
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
            'alerts': alerts
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
            'history': history
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
        
        # Crear el registro de alerta
        alert = ApplianceAlert.objects.create(
            appliance=appliance,
            fecha=datetime.now(),
            tipo=tipo,
            mensaje=mensaje,
            atendida=False
        )
        
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
        response = JsonResponse({'error': str(e)}, status=500)
        return response
    
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