"""
Modelo del Acta de Fiscalización.

Los nombres de campo coinciden con los `name` del formulario del frontend
(templates/fiscalizacion/index.html) para permitir conexión directa con el
contrato del `ActasService` JS. El controlador puede construirse encima
con DRF (ya está en requirements) sin transformaciones.
"""
from django.db import models


class EstadoActa(models.TextChoices):
    BORRADOR = 'borrador', 'Borrador'
    EMITIDA = 'emitida', 'Emitida'
    NOTIFICADA = 'notificada', 'Notificada'
    SANCIONADA = 'sancionada', 'Sancionada'
    ARCHIVADA = 'archivada', 'Archivada'
    ANULADA = 'anulada', 'Anulada'


class TipoIntervencion(models.TextChoices):
    PUNTO_FIJO = 'Punto fijo', 'Punto fijo'
    TERMINAL = 'Terminal', 'Terminal'
    PUNTO_MOVIL = 'Punto móvil', 'Punto móvil'
    OTRO = 'Otro', 'Otro'


class ModalidadServicio(models.TextChoices):
    MERCANCIAS = 'Mercancías', 'Mercancías'
    PASAJEROS = 'Pasajeros', 'Pasajeros'
    OTRO = 'Otro', 'Otro'


class TipoAdministrado(models.TextChoices):
    TRANSPORTISTA = 'Transportista', 'Transportista'
    GENERADOR = 'Generador de carga', 'Generador de carga'
    CONDUCTOR = 'Conductor', 'Conductor'


class TipoDocumento(models.TextChoices):
    RUC = 'RUC', 'RUC'
    DNI = 'DNI', 'DNI'


class Acta(models.Model):
    # 1. Datos del acta
    numero = models.CharField(max_length=20, unique=True, db_index=True)
    fecha = models.DateField(db_index=True)
    hora = models.TimeField()
    tipoIntervencion = models.CharField(
        max_length=20, choices=TipoIntervencion.choices, blank=True
    )
    lugar = models.CharField(max_length=255, db_index=True)

    # 2. Administrado
    adminTipo = models.CharField(max_length=30, choices=TipoAdministrado.choices, blank=True)
    adminDocTipo = models.CharField(max_length=10, choices=TipoDocumento.choices, blank=True)
    adminDocNum = models.CharField(max_length=15, blank=True, db_index=True)
    adminNombre = models.CharField(max_length=255, blank=True, db_index=True)
    habilitacion = models.CharField(max_length=50, blank=True)

    # 3. Vehículo
    placa = models.CharField(max_length=10, db_index=True)
    modalidad = models.CharField(
        max_length=20, choices=ModalidadServicio.choices, blank=True
    )
    otroServicio = models.CharField(max_length=120, blank=True)
    origen = models.CharField(max_length=120, blank=True)
    destino = models.CharField(max_length=120, blank=True)

    # 4. Conductores
    condVolNombre = models.CharField(max_length=180, blank=True)
    condVolTipoId = models.CharField(max_length=30, blank=True)
    condVolNum = models.CharField(max_length=30, blank=True)
    condVolClase = models.CharField(max_length=20, blank=True)

    condAltNombre = models.CharField(max_length=180, blank=True)
    condAltTipoId = models.CharField(max_length=30, blank=True)
    condAltNum = models.CharField(max_length=30, blank=True)
    condAltClase = models.CharField(max_length=20, blank=True)

    # 5. Resultado
    hechos = models.TextField(blank=True)
    infracciones = models.CharField(max_length=255, blank=True)
    incumplimientos = models.CharField(max_length=255, blank=True)
    manifestacion = models.TextField(blank=True)
    medida = models.TextField(blank=True)
    estado = models.CharField(
        max_length=15,
        choices=EstadoActa.choices,
        default=EstadoActa.BORRADOR,
        db_index=True,
    )

    # 6. Archivo
    archivo = models.FileField(upload_to='fiscalizacion/actas/%Y/%m/', null=True, blank=True)

    # 7. Firmas
    inspectorNombre = models.CharField(max_length=180, blank=True)
    inspectorDni = models.CharField(max_length=15, blank=True)
    intervenidoNombre = models.CharField(max_length=180, blank=True)
    intervenidoDni = models.CharField(max_length=15, blank=True)
    pnpNombre = models.CharField(max_length=180, blank=True)
    pnpCip = models.CharField(max_length=15, blank=True)

    # Trazabilidad
    creadoEn = models.DateTimeField(auto_now_add=True)
    actualizadoEn = models.DateTimeField(auto_now=True)
    creadoPor = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='actas_creadas',
    )

    class Meta:
        ordering = ('-fecha', '-hora')
        verbose_name = 'Acta de fiscalización'
        verbose_name_plural = 'Actas de fiscalización'
        indexes = [
            models.Index(fields=['-fecha', 'estado']),
            models.Index(fields=['placa']),
            models.Index(fields=['adminDocNum']),
        ]

    def __str__(self):
        return f'Acta N° {self.numero} · {self.placa}'

    @property
    def cantidad_infracciones(self) -> int:
        return len([c for c in (self.infracciones or '').split(',') if c.strip()])

    @property
    def cantidad_incumplimientos(self) -> int:
        return len([c for c in (self.incumplimientos or '').split(',') if c.strip()])
