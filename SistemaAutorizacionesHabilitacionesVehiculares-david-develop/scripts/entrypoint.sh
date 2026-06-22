#!/bin/bash

# Salir inmediatamente si un comando falla
set -e

echo "Esperando a que la base de datos esté lista..."
# Aquí podrías agregar un check de wait-for-it si fuera necesario

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

# Ejecutar el comando pasado al contenedor (por defecto gunicorn)
exec "$@"
