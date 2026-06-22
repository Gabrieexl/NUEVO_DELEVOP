from django.apps import AppConfig


class TramitesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tramites'
    verbose_name = 'Gestión de Trámites'
    
    def ready(self):
        # Importar signals cuando la app esté lista
        try:
            from . import signals  # noqa
        except ImportError:
            pass
