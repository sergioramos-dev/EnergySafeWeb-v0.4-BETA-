import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from main.models import ApplianceAutoShutdown, ApplianceControlState, ConnectedAppliance

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('auto_shutdown_debug.log')
    ]
)
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Procesa las configuraciones de auto-apagado y cambia el estado de los dispositivos'

    def handle(self, *args, **options):
        logger.info("\n" + "=" * 50)
        logger.info("INICIANDO PROCESO DE AUTO-SHUTDOWN")
        logger.info("=" * 50)
        
        now = timezone.now()
        logger.info(f"Hora actual: {now}")
        
        # Obtener todas las configuraciones de auto-apagado activas
        configs = ApplianceAutoShutdown.objects.filter(enabled=True)
        logger.info(f"Configuraciones activas encontradas: {configs.count()}")
        
        for config in configs:
            try:
                logger.info("\n" + "-" * 40)
                logger.info(f"Procesando configuración para: {config.appliance.nombre}")
                logger.info(f"ID de configuración: {config.id}")
                logger.info(f"Estado actual: {'Encendido' if config.current_state else 'Apagado'}")
                logger.info(f"Próximo cambio programado: {config.next_switch}")
                
                # Verificar si es tiempo de cambiar el estado
                if now >= config.next_switch:
                    logger.info("⚡ ES HORA DE CAMBIAR EL ESTADO ⚡")
                    
                    # Obtener o crear el estado de control del dispositivo
                    control_state, created = ApplianceControlState.objects.get_or_create(
                        appliance=config.appliance,
                        defaults={'state': True}
                    )
                    
                    if created:
                        logger.info("Creado nuevo estado de control para el dispositivo")
                    
                    # Cambiar el estado
                    new_state = not control_state.state
                    control_state.state = new_state
                    control_state.save()
                    
                    logger.info(f"Estado anterior: {'Encendido' if not new_state else 'Apagado'}")
                    logger.info(f"Nuevo estado: {'Encendido' if new_state else 'Apagado'}")
                    
                    # Actualizar la configuración de auto-apagado
                    config.current_state = new_state
                    config.last_switch = now
                    
                    # Calcular el próximo cambio
                    if new_state:  # Si ahora está encendido
                        config.next_switch = now + timezone.timedelta(
                            hours=config.hours_on, 
                            minutes=config.minutes_on
                        )
                        logger.info(f"Próximo cambio a APAGADO en: {config.hours_on}h {config.minutes_on}m")
                    else:  # Si ahora está apagado
                        config.next_switch = now + timezone.timedelta(
                            hours=config.hours_off, 
                            minutes=config.minutes_off
                        )
                        logger.info(f"Próximo cambio a ENCENDIDO en: {config.hours_off}h {config.minutes_off}m")
                    
                    config.save()
                    
                    logger.info(f"Próximo cambio programado para: {config.next_switch}")
                else:
                    logger.info("No es hora de cambiar el estado")
                    
                    # Calcular tiempo restante
                    time_remaining = config.next_switch - now
                    logger.info(f"Tiempo restante para próximo cambio: {time_remaining}")
                
            except Exception as e:
                logger.error(f"Error procesando configuración {config.id}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
        
        logger.info("\n" + "=" * 50)
        logger.info("PROCESAMIENTO DE AUTO-SHUTDOWN COMPLETADO")
        logger.info("=" * 50)