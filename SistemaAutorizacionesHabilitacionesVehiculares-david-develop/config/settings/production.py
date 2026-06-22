"""
Configuración de producción para Coolify/VPS.
"""

import dj_database_url
from .base import *

DEBUG = config('DEBUG', default=False, cast=bool)

# HARDCODED: Permitir todo para evitar conflictos con variables de entorno desactualizadas en Coolify
ALLOWED_HOSTS = ['*']

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'SAMEORIGIN'

# Desactivado temporalmente para acceso HTTP (sin SSL)
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS', 
    default='http://tkksw0oks844wwg4wgk0cs4s.45.85.147.190.sslip.io,http://45.85.147.190:3000', 
    cast=Csv()
)

# Confianza en el Proxy (Vital para Coolify/Traefik/Nginx)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Database - Usando DATABASE_URL de Coolify
DATABASE_URL = config('DATABASE_URL', default=None)

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=60,
            conn_health_checks=True,
        )
    }
else:
    # Fallback a configuración manual
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='postgres'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
            'CONN_MAX_AGE': 60,
        }
    }

# Static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Email - SMTP en producción
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Logging - Menos verboso en producción
LOGGING['loggers']['django']['level'] = 'WARNING'
LOGGING['loggers']['apps']['level'] = 'INFO'

# Celery - Usar REDIS_URL si está disponible
REDIS_URL = config('REDIS_URL', default=None)
if REDIS_URL:
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
