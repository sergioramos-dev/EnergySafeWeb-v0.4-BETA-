# main/management/commands/process_auto_shutdown.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from main.models import ApplianceAutoShutdown, ApplianceControlState
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Procesa las configuraciones de auto-apagado y cambia el estado de los dispositivos según corresponda'

    def handle(self, *args, **options):
        now = timezone.now()
        logger.info(f"Procesando auto-apagado a las {now.isoformat()}")
        
        # Obtener todas las configuraciones de auto-apagado activas
        configs = ApplianceAutoShutdown.objects.filter(enabled=True)
        
        for config in configs:
            try:
                # Verificar si es tiempo de cambiar el estado
                if now >= config.next_switch:
                    # Obtener el estado actual
                    try:
                        control_state = ApplianceControlState.objects.get(appliance=config.appliance)
                        current_state = control_state.state
                    except ApplianceControlState.DoesNotExist:
                        # Si no existe, crear uno con estado encendido por defecto
                        control_state = ApplianceControlState(
                            appliance=config.appliance,
                            state=True
                        )
                        current_state = True
                        control_state.save()
                    
                    # Cambiar el estado
                    new_state = not current_state
                    control_state.state = new_state
                    control_state.last_updated = now
                    control_state.save()
                    
                    # Actualizar la configuración
                    config.current_state = new_state
                    config.last_switch = now
                    
                    # Calcular el próximo cambio
                    if new_state:  # Si ahora está encendido, el próximo cambio será apagado
                        next_switch = now + timezone.timedelta(hours=config.hours_on, minutes=config.minutes_on)
                    else:  # Si ahora está apagado, el próximo cambio será encendido
                        next_switch = now + timezone.timedelta(hours=config.hours_off, minutes=config.minutes_off)
                    
                    config.next_switch = next_switch
                    config.save()
                    
                    logger.info(f"Dispositivo {config.appliance.id} cambiado a {'ENCENDIDO' if new_state else 'APAGADO'}. Próximo cambio: {next_switch.isoformat()}")
            except Exception as e:
                logger.error(f"Error procesando configuración {config.id}: {str(e)}")
        
        logger.info(f"Procesamiento de auto-apagado completado. {configs.count()} configuraciones procesadas.")