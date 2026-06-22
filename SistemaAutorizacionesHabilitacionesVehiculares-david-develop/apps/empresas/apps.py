from django.apps import AppConfig


class EmpresasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.empresas'
    verbose_name = 'Gestión de Empresas'

    def ready(self):
        from . import signals  # noqa