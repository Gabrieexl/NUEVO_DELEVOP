from django.apps import AppConfig


class VehiculosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.vehiculos'
    verbose_name = 'Gestión de Vehículos'
    
    def ready(self):
        # Importar signals cuando la app esté lista
        try:
            from . import signals  # noqa
        except ImportError:
            pass
