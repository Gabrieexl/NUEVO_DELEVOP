"""
Configuración de desarrollo local.
"""

from .base import *
import dj_database_url

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Database - Cloud PostgreSQL
DATABASE_URL = config('DATABASE_URL', default=None)

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Email - Console backend para desarrollo
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Celery - Ejecutar síncronamente en desarrollo (opcional)
# CELERY_TASK_ALWAYS_EAGER = True
# CELERY_TASK_EAGER_PROPAGATES = True

# Debug Toolbar (opcional - descomentar si se instala)
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
# INTERNAL_IPS = ['127.0.0.1']

# Logging más verboso en desarrollo (pero no DEBUG completo que muestra SQL queries)
LOGGING['loggers']['apps']['level'] = 'DEBUG'
LOGGING['loggers']['django']['level'] = 'INFO'  # INFO en vez de DEBUG para evitar SQL queries
LOGGING['loggers']['django.db.backends'] = {
    'handlers': ['console'],
    'level': 'WARNING',  # Solo errores de DB, no todas las queries
    'propagate': False,
}
LOGGING['loggers']['django.template'] = {
    'handlers': ['console'],
    'level': 'WARNING',  # Solo errores de template importantes
    'propagate': False,
}
