from django.apps import AppConfig

class AutorizacionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.autorizaciones'
    verbose_name = 'Gestión de Autorizaciones'
    def ready(self):
        from . import signals  # noqa