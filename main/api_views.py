# main/api_views.py

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime
from main.models import ConnectedAppliance, ApplianceConsumption

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
        factor_potencia = data.get('factor_potencia', 0)
        
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
        
        # Crear el registro de consumo
        consumption = ApplianceConsumption.objects.create(
            appliance=appliance,
            fecha=datetime.now(),
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
        response = JsonResponse({'error': str(e)}, status=500)
        return response