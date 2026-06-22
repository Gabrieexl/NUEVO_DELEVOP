"""
Configuración de Celery para tareas asíncronas.
"""

import os
from celery import Celery

# Establecer el módulo de configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')

app = Celery('config')

# Usar configuración de Django con prefijo CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks en todas las apps instaladas
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Tarea de prueba para verificar que Celery funciona."""
    print(f'Request: {self.request!r}')
