"""
Settings package.
Usa producción si hay DATABASE_URL (Coolify), sino usa local.
"""

import os

if os.environ.get('DATABASE_URL') or os.environ.get('DJANGO_ENV') == 'production':
    from .production import *
else:
    from .local import *
