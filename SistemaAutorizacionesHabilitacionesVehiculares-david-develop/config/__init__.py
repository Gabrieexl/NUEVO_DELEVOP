"""
Configuración del proyecto Django.
"""

# Importar Celery al iniciar Django para que se registre correctamente
from .celery import app as celery_app

__all__ = ('celery_app',)
