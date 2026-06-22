from django.apps import AppConfig


class ConductoresConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.conductores'
    verbose_name = 'Gestión de Conductores'
    
    def ready(self):
        # Importar signals cuando la app esté lista
        try:
            from . import signals  # noqa
        except ImportError:
            pass
