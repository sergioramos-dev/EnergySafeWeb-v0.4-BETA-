from django.apps import AppConfig

class MainConfig(AppConfig):
    name = 'main'

    def ready(self):
        # Importamos las señales para que se registren cuando se inicie la app
        import main.signals
