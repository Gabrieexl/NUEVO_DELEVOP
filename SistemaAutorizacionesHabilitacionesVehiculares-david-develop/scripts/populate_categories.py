
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.configuracion.models import CategoriaVehiculo, Carroceria

def populate():
    # Categorías
    m1, _ = CategoriaVehiculo.objects.get_or_create(codigo='M1', defaults={'nombre': 'Categoría M1'})
    m2, _ = CategoriaVehiculo.objects.get_or_create(codigo='M2', defaults={'nombre': 'Categoría M2'})
    m3, _ = CategoriaVehiculo.objects.get_or_create(codigo='M3', defaults={'nombre': 'Categoría M3'})

    # Carrocerías M1
    carrocerias_m1 = [
        ('AUTO', 'Automóvil'),
        ('SUV', 'SUV'),
        ('SW', 'Station Wagon'),
        ('SEDAN', 'Sedán'),
    ]
    for cod, nom in carrocerias_m1:
        Carroceria.objects.get_or_create(codigo=f'M1-{cod}', defaults={'nombre': nom, 'categoria': m1})

    # Carrocerías M2
    carrocerias_m2 = [
        ('MINIBUS', 'Minibús'),
        ('MICROBUS', 'Microbús'),
        ('OMNIBUS', 'Ómnibus'),
    ]
    for cod, nom in carrocerias_m2:
        Carroceria.objects.get_or_create(codigo=f'M2-{cod}', defaults={'nombre': nom, 'categoria': m2})

    # Carrocerías M3
    carrocerias_m3 = [
        ('OMNIBUS_GRANDE', 'Ómnibus Grande'),
        ('ARTICULADO', 'Articulado'),
    ]
    for cod, nom in carrocerias_m3:
        Carroceria.objects.get_or_create(codigo=f'M3-{cod}', defaults={'nombre': nom, 'categoria': m3})

    print("Datos de categorías y carrocerías poblados correctamente.")

if __name__ == '__main__':
    populate()
