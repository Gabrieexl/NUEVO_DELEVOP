from django.apps import AppConfig


class NotificacionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notificaciones'
    verbose_name = 'Notificaciones'
    
    def ready(self):
        # Importar signals cuando la app esté lista
        import apps.notificaciones.signals  # noqa
