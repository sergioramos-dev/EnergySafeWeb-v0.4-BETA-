from django.apps import AppConfig
from django.core.management import call_command
from django.utils import timezone
import threading
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MainConfig(AppConfig):
    name = 'main'

    def ready(self):
        # Método simple y directo de auto-apagado
        def auto_shutdown_process():
            while True:
                try:
                    logger.info("Ejecutando proceso de auto-apagado")
                    from main.models import ApplianceAutoShutdown, ApplianceControlState
                    from django.utils import timezone
                    
                    now = timezone.now()
                    configs = ApplianceAutoShutdown.objects.filter(enabled=True)
                    
                    for config in configs:
                        if now >= config.next_switch:
                            # Obtener o crear estado de control
                            control_state, _ = ApplianceControlState.objects.get_or_create(
                                appliance=config.appliance,
                                defaults={'state': True}
                            )
                            
                            # Cambiar estado
                            new_state = not control_state.state
                            control_state.state = new_state
                            control_state.save()
                            
                            # Actualizar configuración
                            config.current_state = new_state
                            config.last_switch = now
                            
                            # Calcular próximo cambio
                            if new_state:  # Si ahora está encendido
                                config.next_switch = now + timezone.timedelta(
                                    hours=config.hours_on, 
                                    minutes=config.minutes_on
                                )
                            else:  # Si ahora está apagado
                                config.next_switch = now + timezone.timedelta(
                                    hours=config.hours_off, 
                                    minutes=config.minutes_off
                                )
                            
                            config.save()
                            
                            logger.info(f"Cambiado: {config.appliance.nombre} a {'ENCENDIDO' if new_state else 'APAGADO'}")
                            logger.info(f"Próximo cambio: {config.next_switch}")
                
                except Exception as e:
                    logger.error(f"Error en auto-shutdown: {e}")
                
                # Esperar 1 minuto
                time.sleep(60)

        # Iniciar en un thread separado
        thread = threading.Thread(target=auto_shutdown_process, daemon=True)
        thread.start()