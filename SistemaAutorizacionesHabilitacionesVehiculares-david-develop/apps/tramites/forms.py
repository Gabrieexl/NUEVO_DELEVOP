"""
Formularios para la app tramites.
"""

from django import forms
from django.utils import timezone
from datetime import timedelta

from .models import Tramite, ReciboPago, VehiculoTramite, ConductorTramite, ExpedienteHojaRuta
from apps.empresas.models import EmpresaTransporte
from apps.autorizaciones.models import Autorizacion
from apps.vehiculos.models import Vehiculo
from apps.conductores.models import Conductor
from apps.documentos.models import DocumentoAdjunto
from apps.configuracion.models import Ruta, Frecuencia, Carroceria, CategoriaVehiculo, TipoServicio as TipoServicioModel
from utils.constants import (
    TipoTramite, TipoVehiculo, CategoriaLicencia, DepartamentosPeru,
    EstadoHabilitacion, EstadoVehiculo, EstadoConductor
)
from utils.validators import validar_dni


class TramiteForm(forms.ModelForm):
    """Formulario para crear trámites."""
    
    class Meta:
        model = Tramite
        fields = [
            'tipo_tramite', 'expediente_externo', 'empresa', 'autorizacion',
            'vehiculo', 'conductor', 'descripcion_solicitud',
            # Datos del solicitante
            'solicitante_dni', 'solicitante_nombres', 'solicitante_telefono', 'solicitante_email'
        ]
        widgets = {
            'tipo_tramite': forms.Select(attrs={
                'class': 'form-select',
                'id': 'tipo_tramite'
            }),
            'expediente_externo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nro. Expediente para hojas de ruta'
            }),
            'empresa': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_empresa'
            }),
            'autorizacion': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_autorizacion'
            }),
            'vehiculo': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_vehiculo'
            }),
            'conductor': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_conductor'
            }),
            'descripcion_solicitud': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describa el motivo y detalles del trámite'
            }),
            # Widgets para datos del solicitante
            'solicitante_dni': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'DNI del solicitante',
                'maxlength': '8',
                'inputmode': 'numeric',
                'pattern': '[0-9]{8}'
            }),
            'solicitante_nombres': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombres completos del solicitante'
            }),
            'solicitante_telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono de contacto',
                'inputmode': 'numeric',
                'pattern': '[0-9]*',
                'maxlength': '20'
            }),
            'solicitante_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['empresa'].queryset = EmpresaTransporte.objects.filter(
            estado='ACTIVA'
        ).order_by('razon_social')
        
        # Inicializar querysets vacíos para dependientes
        self.fields['autorizacion'].queryset = Autorizacion.objects.none()
        self.fields['vehiculo'].queryset = Vehiculo.objects.none()
        self.fields['conductor'].queryset = Conductor.objects.none()

        # Logica para filtrar si hay datos
        empresa_id = None
        if 'empresa' in self.data:
            try:
                empresa_id = int(self.data.get('empresa'))
            except (ValueError, TypeError):
                pass
        elif self.initial.get('empresa'):
            try:
                empresa_id = int(self.initial.get('empresa'))
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.empresa:
            empresa_id = self.instance.empresa.id

        if empresa_id:
            self.fields['autorizacion'].queryset = Autorizacion.objects.filter(
                empresa_id=empresa_id,
                estado='VIGENTE'
            ).order_by('numero_resolucion')
            
            self.fields['vehiculo'].queryset = Vehiculo.objects.filter(
                empresa_propietaria_id=empresa_id
            ).order_by('placa')
            
            self.fields['conductor'].queryset = Conductor.objects.filter(
                empresa_id=empresa_id,
                estado='ACTIVO'
            ).order_by('apellido_paterno')
        
        # Campos opcionales inicialmente (se validan en clean según tipo)
        self.fields['empresa'].required = False
        self.fields['autorizacion'].required = False
        self.fields['vehiculo'].required = False
        self.fields['conductor'].required = False
        self.fields['expediente_externo'].required = False
        # Datos del solicitante siempre obligatorios
        self.fields['solicitante_dni'].required = True
        self.fields['solicitante_nombres'].required = True
    
    def clean(self):
        """Validar campos obligatorios según tipo de trámite."""
        cleaned_data = super().clean()
        tipo_tramite = cleaned_data.get('tipo_tramite')
        empresa = cleaned_data.get('empresa')
        autorizacion = cleaned_data.get('autorizacion')
        vehiculo = cleaned_data.get('vehiculo')
        
        # Definir campos requeridos por tipo de trámite
        if tipo_tramite in [TipoTramite.AUTORIZACION_INICIAL, TipoTramite.AUTORIZACION_RUTA]:
            if not empresa:
                self.add_error('empresa', 'La empresa es obligatoria para este tipo de trámite.')
        
        elif tipo_tramite == TipoTramite.MODIFICACION_AUTORIZACION:
            if not empresa:
                self.add_error('empresa', 'La empresa es obligatoria para este tipo de trámite.')
            if not autorizacion:
                self.add_error('autorizacion', 'La autorización es obligatoria para este tipo de trámite.')
        
        elif tipo_tramite == TipoTramite.INCREMENTO_FLOTA:
            if not empresa:
                self.add_error('empresa', 'La empresa es obligatoria para este tipo de trámite.')
            if not autorizacion:
                self.add_error('autorizacion', 'La autorización es obligatoria para este tipo de trámite.')

        elif tipo_tramite == TipoTramite.RENOVACION_TUC:
            if not empresa:
                self.add_error('empresa', 'La empresa es obligatoria para este tipo de trámite.')
            if not autorizacion:
                self.add_error('autorizacion', 'La autorización es obligatoria para este tipo de trámite.')
        
        elif tipo_tramite == TipoTramite.SUSTITUCION_VEHICULO:
            if not empresa:
                self.add_error('empresa', 'La empresa es obligatoria para este tipo de trámite.')
            if not autorizacion:
                self.add_error('autorizacion', 'La autorización es obligatoria para este tipo de trámite.')
            if not vehiculo:
                self.add_error('vehiculo', 'El vehículo a sustituir es obligatorio para este tipo de trámite.')
        
        elif tipo_tramite == TipoTramite.BAJA_VEHICULO:
            if not empresa:
                self.add_error('empresa', 'La empresa es obligatoria para este tipo de trámite.')
            if not autorizacion:
                self.add_error('autorizacion', 'La autorización es obligatoria para este tipo de trámite.')
            if not vehiculo:
                self.add_error('vehiculo', 'El vehículo es obligatorio para este tipo de trámite.')
        
        elif tipo_tramite == TipoTramite.HABILITACION_CONDUCTOR:
            if not empresa:
                self.add_error('empresa', 'La empresa es obligatoria para este tipo de trámite.')
            if not autorizacion:
                self.add_error('autorizacion', 'La autorización es obligatoria para este tipo de trámite.')
        
        elif tipo_tramite == TipoTramite.BAJA_CONDUCTOR:
            if not empresa:
                self.add_error('empresa', 'La empresa es obligatoria para este tipo de trámite.')
            if not autorizacion:
                self.add_error('autorizacion', 'La autorización es obligatoria para este tipo de trámite.')
        
        return cleaned_data

    def clean_solicitante_dni(self):
        dni = (self.cleaned_data.get('solicitante_dni') or '').strip()
        if not dni:
            raise forms.ValidationError('Este campo es requerido.')

        if not dni.isdigit() or len(dni) != 8:
            raise forms.ValidationError('El DNI del solicitante debe tener exactamente 8 digitos numericos.')

        return dni


# ============================================================================
# FORMULARIOS PARA RECIBO DE PAGO
# ============================================================================

class ReciboPagoForm(forms.ModelForm):
    """Formulario para registrar recibos de pago."""
    
    class Meta:
        model = ReciboPago
        fields = [
            'numero_serie', 'numero_documento', 'fecha_pago',
            'descripcion_tarifa', 'cantidad', 'precio_unitario'
        ]
        widgets = {
            'numero_serie': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'N° Serie'
            }),
            'numero_documento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'N° Documento'
            }),
            'fecha_pago': forms.DateInput(format='%Y-%m-%d', attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'descripcion_tarifa': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción/Tarifa'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1'
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha_pago'].initial = timezone.now().date()


# ============================================================================
# FORMULARIOS PARA VEHÍCULOS EN TRÁMITE
# ============================================================================

class VehiculoTramiteForm(forms.ModelForm):
    """Formulario para registrar vehículos en un trámite."""
    
    class Meta:
        model = VehiculoTramite
        fields = [
            'placa_nueva', 'marca', 'modelo', 'anio_fabricacion',
            'color', 'numero_serie', 'numero_motor', 'capacidad_pasajeros',
            'peso_bruto', 'categoria', 'carroceria', 'numero_tarjeta_propiedad',
            'fecha_venc_soat', 'fecha_venc_citv', 'observaciones',
            'numero_tuc', 'fecha_expedicion_tuc',
            'fecha_autorizacion_transportista', 'fecha_expiracion_transportista'
        ]
        widgets = {
            'placa_nueva': forms.TextInput(attrs={
                'class': 'form-control text-uppercase',
                'placeholder': 'Ej: ABC-123'
            }),
            'marca': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Marca del vehículo'
            }),
            'modelo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Modelo del vehículo'
            }),
            'anio_fabricacion': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1990',
                'max': '2030'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Color'
            }),
            'numero_serie': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de serie/chasis'
            }),
            'numero_motor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de motor'
            }),
            'capacidad_pasajeros': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'peso_bruto': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Peso bruto en kg'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select'
            }),
            'carroceria': forms.Select(attrs={
                'class': 'form-select'
            }),
            'numero_tarjeta_propiedad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'N° Tarjeta de Propiedad'
            }),
            'fecha_venc_soat': forms.DateInput(format='%Y-%m-%d', attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'fecha_venc_citv': forms.DateInput(format='%Y-%m-%d', attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Observaciones'
            }),
            'numero_tuc': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de TUC',
                'style': 'min-width: 100px;'
            }),
            'fecha_expedicion_tuc': forms.DateInput(format='%Y-%m-%d', attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'fecha_autorizacion_transportista': forms.DateInput(format='%Y-%m-%d', attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'fecha_expiracion_transportista': forms.DateInput(format='%Y-%m-%d', attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.tramite = kwargs.pop('tramite', None)
        super().__init__(*args, **kwargs)
        # Hacer campos obligatorios (ajustar para renovación TUC)
        self.fields['placa_nueva'].required = True
        if self.tramite and self.tramite.tipo_tramite == TipoTramite.RENOVACION_TUC:
            self.fields['marca'].required = False
            self.fields['modelo'].required = False
            self.fields['anio_fabricacion'].required = False
            self.fields['categoria'].required = False
            self.fields['carroceria'].required = False
            self.fields['capacidad_pasajeros'].required = False
            self.fields['fecha_expiracion_transportista'].required = False
        else:
            self.fields['marca'].required = True
            self.fields['modelo'].required = True
            self.fields['anio_fabricacion'].required = True
            self.fields['categoria'].required = True
            self.fields['carroceria'].required = True
            self.fields['capacidad_pasajeros'].required = True

        # Cargar tipos de vehículo desde el modelo de configuración
        self.fields['categoria'].queryset = CategoriaVehiculo.objects.filter(
            activo=True
        ).order_by('codigo')
        self.fields['categoria'].empty_label = "-- Seleccionar --"
        self.fields['carroceria'].queryset = Carroceria.objects.filter(activo=True).order_by('nombre')
        self.fields['carroceria'].empty_label = "-- Seleccionar --"

        # Pre-poblar datos si existe vehículo vinculado o por placa, y los campos están vacíos
        if self.instance and self.instance.pk:
            vehiculo = self.instance.vehiculo_existente
            
            # Si no tiene vehículo vinculado, intentar buscar por placa
            if not vehiculo and self.instance.placa_nueva:
                from apps.vehiculos.models import Vehiculo
                vehiculo = (
                    Vehiculo.objects.filter(placa=self.instance.placa_nueva)
                    .order_by('-id')
                    .first()
                )
            
            if vehiculo:
                # Mapeo de campos Formulario -> Modelo Vehiculo
                campos = {
                    'marca': 'marca',
                    'modelo': 'modelo',
                    'anio_fabricacion': 'anio_fabricacion',
                    'color': 'color',
                    'numero_serie': 'numero_serie',
                    'numero_motor': 'numero_motor',
                    'capacidad_pasajeros': 'capacidad_sentados',
                    'numero_tarjeta_propiedad': 'numero_tiv',
                    'fecha_venc_soat': 'fecha_venc_soat',
                    'fecha_venc_citv': 'fecha_venc_citv',
                }
                
                # Poblar campos simples
                for f_form, f_model in campos.items():
                    # Solo si el campo en la instancia actual está vacío/nulo
                    if not getattr(self.instance, f_form):
                        val = getattr(vehiculo, f_model)
                        if val:
                            self.initial[f_form] = val
                            
                # Poblar FKs
                if not self.instance.categoria and vehiculo.categoria:
                    self.initial['categoria'] = vehiculo.categoria
                if not self.instance.carroceria and vehiculo.carroceria:
                    self.initial['carroceria'] = vehiculo.carroceria

                # Poblar datos de TUC si existe habilitación vigente
                if vehiculo.habilitacion_vigente:
                     hv = vehiculo.habilitacion_vigente
                     if not self.instance.numero_tuc:
                         self.initial['numero_tuc'] = hv.numero_tuc
                     if not self.instance.fecha_expedicion_tuc:
                         self.initial['fecha_expedicion_tuc'] = hv.fecha_expedicion_tuc
                     if not self.instance.fecha_autorizacion_transportista:
                         self.initial['fecha_autorizacion_transportista'] = hv.fecha_autorizacion_transportista
                     if not self.instance.fecha_expiracion_transportista:
                         self.initial['fecha_expiracion_transportista'] = hv.fecha_expiracion_transportista

    def clean_placa_nueva(self):
        placa = self.cleaned_data.get('placa_nueva')
        if not placa:
            return placa
        
        placa = placa.upper().strip()
        
        from apps.vehiculos.models import HabilitacionVehicular, Vehiculo
        from .models import VehiculoTramite, EstadoTramite
        
        # 1. Verificar si el vehículo ya está habilitado (VIGENTE) en cualquier empresa
        habilitacion_activa = HabilitacionVehicular.objects.filter(
            vehiculo__placa=placa,
            estado=EstadoHabilitacion.VIGENTE
        ).select_related('autorizacion__empresa').first()
        
        if habilitacion_activa:
            # Permitir renovación TUC solo si pertenece a la misma autorización del trámite
            if self.tramite and self.tramite.tipo_tramite == TipoTramite.RENOVACION_TUC:
                if not self.tramite.autorizacion_id or habilitacion_activa.autorizacion_id != self.tramite.autorizacion_id:
                    empresa = habilitacion_activa.autorizacion.empresa
                    raise forms.ValidationError(
                        f"El vehículo con placa {placa} está habilitado en la empresa "
                        f"'{empresa.razon_social}'. Para renovar TUC debe pertenecer a la autorización seleccionada."
                    )
            else:
                empresa = habilitacion_activa.autorizacion.empresa
                raise forms.ValidationError(
                    f"El vehículo con placa {placa} ya se encuentra HABILITADO y VIGENTE "
                    f"en la empresa '{empresa.razon_social}'. "
                    "Debe realizar primero un trámite de 'Baja de Vehículo' en dicha empresa "
                    "para poder habilitarlo en una nueva."
                )
            
        # 2. Verificar si el vehículo ya está en otro trámite PENDIENTE
        # (No CERRADO ni DENEGADO)
        tramite_pendiente = VehiculoTramite.objects.filter(
            placa_nueva=placa,
            tramite__estado__in=[
                EstadoTramite.RECIBIDO,
                EstadoTramite.EN_CONTROL_CALIDAD,
                EstadoTramite.EN_EVAL_TECNICA,
                EstadoTramite.EN_DIRECCION_ADMINISTRATIVA,
                EstadoTramite.EN_DIRECCION_GENERAL,
                EstadoTramite.OBSERVADO,
                EstadoTramite.EN_REVISION_LEGAL,
                EstadoTramite.PENDIENTE_FIRMA,
                EstadoTramite.APROBADO # Aprobado pero no cerrado aún
            ]
        ).exclude(id=self.instance.id if self.instance else None).first()
        
        if tramite_pendiente:
            raise forms.ValidationError(
                f"El vehículo con placa {placa} ya se encuentra en proceso de evaluación "
                f"en el trámite {tramite_pendiente.tramite.numero_expediente}. "
                "No se puede duplicar la solicitud para la misma placa."
            )
            
        return placa

    def clean(self):
        cleaned_data = super().clean()
        placa = cleaned_data.get('placa_nueva')
        
        # Autocompletar datos si el vehículo ya existe en la BD
        if placa:
            from apps.vehiculos.models import Vehiculo
            vehiculo = (
                Vehiculo.objects.filter(placa=placa)
                .order_by('-id')
                .first()
            )
            if vehiculo:
                self.instance.vehiculo_existente = vehiculo # Link existente para referencia

                # Lista de campos a copiar si están vacíos
                campos_map = {
                    'marca': 'marca',
                    'modelo': 'modelo',
                    'anio_fabricacion': 'anio_fabricacion',
                    'color': 'color',
                    'numero_serie': 'numero_serie',
                    'numero_motor': 'numero_motor',
                    'capacidad_pasajeros': 'capacidad_sentados', # Nota la diferencia de nombre
                    # 'categoria': 'categoria', # Selects son complejos si ID no coincide, pero intentamos
                    # 'carroceria': 'carroceria'
                }
                
                for field_form, field_model in campos_map.items():
                    if not cleaned_data.get(field_form):
                        val = getattr(vehiculo, field_model)
                        if val:
                            cleaned_data[field_form] = val
                            
                # Para FKs (categoria, carroceria)
                if not cleaned_data.get('categoria') and vehiculo.categoria:
                    cleaned_data['categoria'] = vehiculo.categoria
                if not cleaned_data.get('carroceria') and vehiculo.carroceria:
                    cleaned_data['carroceria'] = vehiculo.carroceria
                    
                # Documentos
                if not cleaned_data.get('numero_tarjeta_propiedad'):
                    cleaned_data['numero_tarjeta_propiedad'] = vehiculo.numero_tiv
                if not cleaned_data.get('fecha_venc_soat'):
                    cleaned_data['fecha_venc_soat'] = vehiculo.fecha_venc_soat
                if not cleaned_data.get('fecha_venc_citv'):
                    cleaned_data['fecha_venc_citv'] = vehiculo.fecha_venc_citv

        if self.tramite and self.tramite.tipo_tramite == TipoTramite.RENOVACION_TUC:
            if not cleaned_data.get('numero_tuc'):
                self.add_error('numero_tuc', 'El numero de TUC es obligatorio para renovacion.')
            if not cleaned_data.get('fecha_expedicion_tuc'):
                self.add_error('fecha_expedicion_tuc', 'La fecha de expedicion es obligatoria para renovacion.')

            # En renovación TUC ambas fechas se manejan como el mismo dato en esta pantalla.
            if cleaned_data.get('fecha_expedicion_tuc'):
                cleaned_data['fecha_expiracion_transportista'] = cleaned_data.get('fecha_expedicion_tuc')

            if placa and self.tramite.autorizacion_id:
                from apps.vehiculos.models import HabilitacionVehicular
                existe_en_autorizacion = HabilitacionVehicular.objects.filter(
                    vehiculo__placa=placa,
                    autorizacion_id=self.tramite.autorizacion_id,
                    estado=EstadoHabilitacion.VIGENTE
                ).exists()
                if not existe_en_autorizacion:
                    self.add_error('placa_nueva', 'La placa seleccionada no pertenece a la autorizacion del tramite.')

        if self.tramite and self.tramite.tipo_tramite == TipoTramite.INCREMENTO_FLOTA:
            for campo in [
                'color',
                'numero_serie',
                'numero_motor',
                'numero_tarjeta_propiedad',
                'observaciones',
                'numero_tuc',
            ]:
                cleaned_data[campo] = ''
            for campo in [
                'fecha_venc_citv',
                'fecha_expedicion_tuc',
                'fecha_autorizacion_transportista',
                'fecha_expiracion_transportista',
            ]:
                cleaned_data[campo] = None

        return cleaned_data


class VehiculoBajaSustitucionForm(forms.Form):
    """Formulario para seleccionar vehículo existente (baja/sustitución)."""
    
    vehiculo_existente = forms.ModelChoiceField(
        queryset=Vehiculo.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Vehículo a dar de baja/sustituir'
    )
    
    motivo = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Motivo de la baja/sustitución'
        }),
        label='Motivo'
    )
    
    def __init__(self, *args, autorizacion=None, **kwargs):
        super().__init__(*args, **kwargs)
        if autorizacion:
            # Filtrar vehículos habilitados para esta autorización
            from apps.vehiculos.models import HabilitacionVehicular
            vehiculos_ids = HabilitacionVehicular.objects.filter(
                autorizacion=autorizacion,
                estado='VIGENTE'
            ).values_list('vehiculo_id', flat=True)
            self.fields['vehiculo_existente'].queryset = Vehiculo.objects.filter(
                id__in=vehiculos_ids
            )


# ============================================================================
# FORMULARIOS PARA CONDUCTORES EN TRÁMITE
# ============================================================================

class ConductorTramiteForm(forms.ModelForm):
    """Formulario para registrar conductores en un trámite de habilitación."""
    
    estado = forms.ChoiceField(
        choices=EstadoConductor.CHOICES,
        initial=EstadoConductor.INACTIVO,
        required=False,
        disabled=True,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Estado'
    )

    class Meta:
        model = ConductorTramite
        fields = [
            'dni', 'nombres', 'apellido_paterno', 'apellido_materno',
            'fecha_nacimiento', 'estado', 'telefono', 'email', 'direccion',
            'licencia_numero', 'licencia_categoria',
            'licencia_fecha_emision', 'licencia_fecha_vencimiento',
            'observaciones'
        ]
        widgets = {
            'dni': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'DNI',
                'maxlength': '8',
                'inputmode': 'numeric',
                'pattern': '[0-9]{8}'
            }),
            'nombres': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombres'
            }),
            'apellido_paterno': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellido Paterno'
            }),
            'apellido_materno': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellido Materno'
            }),
            'fecha_nacimiento': forms.DateInput(format='%Y-%m-%d', attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección'
            }),
            'licencia_numero': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'N° Licencia'
            }),
            'licencia_categoria': forms.Select(attrs={
                'class': 'form-select'
            }, choices=[('', '-- Seleccionar --')] + list(CategoriaLicencia.CHOICES)),
            'licencia_fecha_emision': forms.DateInput(format='%Y-%m-%d', attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'licencia_fecha_vencimiento': forms.DateInput(format='%Y-%m-%d', attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Observaciones'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.tramite = kwargs.pop('tramite', None)
        super().__init__(*args, **kwargs)

        self.fields['estado'].initial = EstadoConductor.INACTIVO
        self.fields['dni'].required = True
        self.fields['nombres'].required = True
        self.fields['apellido_paterno'].required = True
        self.fields['apellido_materno'].required = True
        self.fields['fecha_nacimiento'].required = True
        self.fields['licencia_numero'].required = True
        self.fields['licencia_categoria'].required = True
        self.fields['licencia_fecha_emision'].required = True
        self.fields['licencia_fecha_vencimiento'].required = True

        # Pre-poblar datos si existe conductor vinculado o por DNI, y los campos están vacíos
        if self.instance and self.instance.pk:
            conductor = self.instance.conductor_existente
            
            # Si no tiene conductor vinculado, intentar buscar por DNI
            if not conductor and self.instance.dni:
                from apps.conductores.models import Conductor
                try:
                    conductor = Conductor.objects.get(dni=self.instance.dni)
                except Conductor.DoesNotExist:
                    pass
            
            if conductor:
                # Mapeo de campos Formulario -> Modelo Conductor
                campos = {
                    'nombres': 'nombres',
                    'apellido_paterno': 'apellido_paterno',
                    'apellido_materno': 'apellido_materno',
                    'fecha_nacimiento': 'fecha_nacimiento',
                    'telefono': 'telefono',
                    'direccion': 'direccion',
                    'email': 'email',
                    'licencia_numero': 'licencia_numero',
                    'licencia_categoria': 'licencia_categoria',
                    'licencia_fecha_emision': 'licencia_fecha_emision',
                    'licencia_fecha_vencimiento': 'licencia_fecha_vencimiento',
                }
                
                # Poblar campos
                for f_form, f_model in campos.items():
                    # Solo si el campo en la instancia actual está vacío/nulo
                    if not getattr(self.instance, f_form):
                        val = getattr(conductor, f_model)
                        if val:
                            self.initial[f_form] = val

    def clean_dni(self):
        dni = (self.cleaned_data.get('dni') or '').strip()
        if not dni:
            return dni

        # Validar formato de DNI (8 dígitos)
        validar_dni(dni)
        
        from apps.conductores.models import Conductor, HabilitacionConductor
        from .models import ConductorTramite, EstadoTramite
        
        # 1. Verificar si ya existe un trámite PENDIENTE para este DNI
        # (No CERRADO ni DENEGADO)
        tramite_pendiente = ConductorTramite.objects.filter(
            dni=dni,
            tramite__estado__in=[
                EstadoTramite.RECIBIDO,
                EstadoTramite.EN_CONTROL_CALIDAD,
                EstadoTramite.EN_EVAL_TECNICA,
                EstadoTramite.EN_DIRECCION_ADMINISTRATIVA,
                EstadoTramite.EN_DIRECCION_GENERAL,
                EstadoTramite.OBSERVADO,
                EstadoTramite.EN_REVISION_LEGAL,
                EstadoTramite.PENDIENTE_FIRMA,
                EstadoTramite.APROBADO
            ]
        ).exclude(id=self.instance.id if self.instance else None).first()
        
        if tramite_pendiente:
            raise forms.ValidationError(
                f"Ya existe un trámite en curso ({tramite_pendiente.tramite.numero_expediente}) "
                f"para el conductor con DNI {dni}."
            )
            
        # 2. Verificar si el conductor ya está habilitado y VIGENTE en otra empresa
        habilitacion_activa = HabilitacionConductor.objects.filter(
            conductor__dni=dni,
            estado=EstadoHabilitacion.VIGENTE
        ).select_related('empresa').first()
        
        if habilitacion_activa:
            raise forms.ValidationError(
                f"El conductor con DNI {dni} ya se encuentra HABILITADO y VIGENTE "
                f"en la empresa '{habilitacion_activa.empresa.razon_social}'. "
                "Debe realizar primero un trámite de 'Baja de Conductor' en dicha empresa "
                "para poder habilitarlo en una nueva."
            )
            
        return dni

    def clean(self):
        cleaned_data = super().clean()
        dni = cleaned_data.get('dni')
        
        # Autocompletar datos si el conductor ya existe en la BD
        if dni:
            from apps.conductores.models import Conductor
            try:
                conductor = Conductor.objects.get(dni=dni)
                self.instance.conductor_existente = conductor # Link existente para referencia

                # Mapeo de campos Form -> Model
                campos_map = {
                    'nombres': 'nombres',
                    'apellido_paterno': 'apellido_paterno',
                    'apellido_materno': 'apellido_materno',
                    'fecha_nacimiento': 'fecha_nacimiento',
                    'telefono': 'telefono',
                    'direccion': 'direccion',
                    'licencia_numero': 'licencia_numero',
                    'licencia_categoria': 'licencia_categoria',
                    'licencia_fecha_emision': 'licencia_fecha_emision',
                    'licencia_fecha_vencimiento': 'licencia_fecha_vencimiento',
                }
                
                for field_form, field_model in campos_map.items():
                    if not cleaned_data.get(field_form):
                        val = getattr(conductor, field_model)
                        if val:
                            cleaned_data[field_form] = val
                            
                # Nota: Conductor model no tiene email, por lo que no se copia.
                
            except Conductor.DoesNotExist:
                pass
                
        return cleaned_data


class ConductorBajaForm(forms.Form):
    """Formulario para seleccionar conductor existente (baja)."""
    
    conductor_existente = forms.ModelChoiceField(
        queryset=Conductor.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Conductor a dar de baja'
    )
    
    motivo = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Motivo de la baja'
        }),
        label='Motivo'
    )
    
    def __init__(self, *args, autorizacion=None, **kwargs):
        super().__init__(*args, **kwargs)
        if autorizacion:
            # Filtrar conductores habilitados para esta autorización
            from apps.conductores.models import HabilitacionConductor
            conductores_ids = HabilitacionConductor.objects.filter(
                autorizacion=autorizacion,
                estado='VIGENTE'
            ).values_list('conductor_id', flat=True)
            self.fields['conductor_existente'].queryset = Conductor.objects.filter(
                id__in=conductores_ids
            )


# ============================================================================
# FORMULARIO PARA EXPEDIENTE HOJA DE RUTA
# ============================================================================

class ExpedienteHojaRutaForm(forms.ModelForm):
    """Formulario para registrar expediente de hoja de ruta en transiciones."""
    
    class Meta:
        model = ExpedienteHojaRuta
        fields = ['numero_expediente_externo', 'observaciones']
        widgets = {
            'numero_expediente_externo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nro. Expediente Hoja de Ruta'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Observaciones (opcional)'
            }),
        }


# ============================================================================
# FORMULARIOS ESPECÍFICOS POR TIPO DE TRÁMITE
# ============================================================================

class AutorizacionInicialForm(forms.Form):
    """
    Formulario para trámite de AUTORIZACIÓN INICIAL.
    Solicita todos los datos necesarios para crear una nueva autorización.
    """
    
    # Datos de la autorización
    tipo_servicio = forms.ModelChoiceField(
        queryset=TipoServicioModel.objects.filter(activo=True).order_by('nombre'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Tipo de Servicio'
    )
    
    modalidad = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Transporte regular de personas'
        }),
        label='Modalidad'
    )
    
    ambito = forms.ChoiceField(
        choices=DepartamentosPeru.CHOICES,
        initial=DepartamentosPeru.MADRE_DE_DIOS,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Ámbito Regional'
    )
    
    fecha_inicio_vigencia = forms.DateField(
        widget=forms.DateInput(format='%Y-%m-%d', attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha Inicio de Vigencia'
    )
    
    fecha_fin_vigencia = forms.DateField(
        widget=forms.DateInput(format='%Y-%m-%d', attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha Fin de Vigencia'
    )
    
    rutas = forms.ModelMultipleChoiceField(
        queryset=Ruta.objects.filter(activo=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label='Rutas Autorizadas'
    )
    
    frecuencias = forms.ModelMultipleChoiceField(
        queryset=Frecuencia.objects.filter(activo=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label='Frecuencias de Servicio'
    )
    
    descripcion_rutas = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Descripción adicional de las rutas (opcional)'
        }),
        label='Descripción Adicional de Rutas'
    )
    
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Observaciones adicionales'
        }),
        label='Observaciones'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Establecer fechas predeterminadas
        hoy = timezone.now().date()
        self.fields['fecha_inicio_vigencia'].initial = hoy
        self.fields['fecha_fin_vigencia'].initial = hoy + timedelta(days=365*4)  # 4 años


class AutorizacionRutaForm(AutorizacionInicialForm):
    """Formulario para Autorizacion de Ruta sin flota ni conductores."""
    pass


class IncrementoFlotaForm(forms.Form):
    """
    Formulario para trámite de INCREMENTO DE FLOTA.
    Solicita datos del vehículo a agregar.
    """
    
    placa = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control text-uppercase',
            'placeholder': 'Ej: ABC-123'
        }),
        label='Placa del Vehículo'
    )
    
    marca = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Toyota'
        }),
        label='Marca'
    )
    
    modelo = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Hiace'
        }),
        label='Modelo'
    )
    
    anio_fabricacion = forms.IntegerField(
        min_value=1990,
        max_value=timezone.now().year + 1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 2020'
        }),
        label='Año de Fabricación'
    )
    
    color = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Blanco'
        }),
        label='Color'
    )
    
    categoria = forms.ModelChoiceField(
        queryset=CategoriaVehiculo.objects.filter(activo=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Categoría',
        empty_label='-- Seleccionar --'
    )
    
    carroceria = forms.ModelChoiceField(
        queryset=Carroceria.objects.filter(activo=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Carrocería',
        empty_label='-- Seleccionar --'
    )
    
    capacidad_sentados = forms.IntegerField(
        min_value=1,
        max_value=60,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 15'
        }),
        label='Capacidad de Pasajeros'
    )

    peso_bruto = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Peso bruto en kg'
        }),
        label='Peso Bruto (kg)'
    )
    
    numero_serie = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Número de serie/chasis'
        }),
        label='Número de Serie/Chasis'
    )
    
    numero_motor = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Número de motor'
        }),
        label='Número de Motor'
    )
    
    numero_tiv = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tarjeta de Identificación Vehicular'
        }),
        label='Número TIV'
    )
    
    fecha_venc_soat = forms.DateField(
        required=False,
        widget=forms.DateInput(format='%Y-%m-%d', attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha Vencimiento SOAT'
    )
    
    fecha_venc_citv = forms.DateField(
        required=False,
        widget=forms.DateInput(format='%Y-%m-%d', attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha Vencimiento CITV'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].queryset = CategoriaVehiculo.objects.filter(
            activo=True
        ).order_by('codigo')
        self.fields['categoria'].empty_label = '-- Seleccionar --'
        self.fields['carroceria'].queryset = Carroceria.objects.filter(
            activo=True
        ).order_by('nombre')
        self.fields['carroceria'].empty_label = '-- Seleccionar --'


class BaseIncrementoFlotaVehiculoFormSet(forms.BaseFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        placas = set()
        tiene_vehiculo = False
        for form in self.forms:
            cleaned = getattr(form, 'cleaned_data', {})
            if not cleaned or cleaned.get('DELETE'):
                continue

            tiene_vehiculo = True
            placa = (cleaned.get('placa') or '').replace('-', '').replace(' ', '').upper()
            if placa in placas:
                raise forms.ValidationError('No se puede repetir la misma placa en el tramite.')
            placas.add(placa)

        if not tiene_vehiculo:
            raise forms.ValidationError('Debe registrar al menos un vehiculo.')


class BaseIncrementoFlotaConductorFormSet(forms.BaseFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        dnis = set()
        tiene_conductor = False
        for form in self.forms:
            cleaned = getattr(form, 'cleaned_data', {})
            if not cleaned or cleaned.get('DELETE'):
                continue

            tiene_conductor = True
            dni = (cleaned.get('dni') or '').strip()
            if dni in dnis:
                raise forms.ValidationError('No se puede repetir el mismo DNI en el tramite.')
            dnis.add(dni)

        if not tiene_conductor:
            raise forms.ValidationError('Debe registrar al menos un conductor.')


IncrementoFlotaVehiculoFormSet = forms.formset_factory(
    IncrementoFlotaForm,
    formset=BaseIncrementoFlotaVehiculoFormSet,
    can_delete=True,
    extra=1,
    min_num=1,
    validate_min=True,
)

IncrementoFlotaConductorFormSet = forms.formset_factory(
    ConductorTramiteForm,
    formset=BaseIncrementoFlotaConductorFormSet,
    can_delete=True,
    extra=1,
    min_num=1,
    validate_min=True,
)


class SustitucionVehiculoForm(IncrementoFlotaForm):
    """
    Formulario para trámite de SUSTITUCIÓN DE VEHÍCULO.
    Hereda de IncrementoFlotaForm y agrega el vehículo a sustituir.
    """
    
    vehiculo_saliente = forms.ModelChoiceField(
        queryset=Vehiculo.objects.filter(estado='HABILITADO'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Vehículo a Sustituir (Saliente)'
    )
    
    motivo_sustitucion = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Motivo de la sustitución'
        }),
        label='Motivo de Sustitución'
    )
    
    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa:
            self.fields['vehiculo_saliente'].queryset = Vehiculo.objects.filter(
                empresa_propietaria=empresa,
                estado='HABILITADO'
            )


class HabilitacionConductorForm(forms.Form):
    """
    Formulario para trámite de HABILITACIÓN DE CONDUCTOR.
    Permite seleccionar un conductor existente o crear uno nuevo.
    """
    
    usar_conductor_existente = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'usar_conductor_existente'
        }),
        label='¿Usar conductor ya registrado?'
    )
    
    conductor_existente = forms.ModelChoiceField(
        queryset=Conductor.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'conductor_existente_select'
        }),
        label='Seleccionar Conductor Existente'
    )
    
    # Datos del nuevo conductor
    dni = forms.CharField(
        max_length=8,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '12345678',
            'maxlength': '8',
            'inputmode': 'numeric',
            'pattern': '[0-9]{8}'
        }),
        label='DNI'
    )
    
    nombres = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombres completos'
        }),
        label='Nombres'
    )
    
    apellido_paterno = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apellido paterno'
        }),
        label='Apellido Paterno'
    )
    
    apellido_materno = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apellido materno'
        }),
        label='Apellido Materno'
    )
    
    fecha_nacimiento = forms.DateField(
        required=False,
        widget=forms.DateInput(format='%Y-%m-%d', attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha de Nacimiento'
    )
    
    direccion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Dirección de domicilio'
        }),
        label='Dirección'
    )
    
    telefono = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '999999999'
        }),
        label='Teléfono'
    )
    
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com'
        }),
        label='Correo Electrónico'
    )
    
    licencia_numero = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Número de licencia'
        }),
        label='Número de Licencia'
    )
    
    licencia_categoria = forms.ChoiceField(
        choices=[('', '-- Seleccione --')] + list(CategoriaLicencia.CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Categoría de Licencia'
    )
    
    licencia_fecha_emision = forms.DateField(
        required=False,
        widget=forms.DateInput(format='%Y-%m-%d', attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha de Emisión de Licencia'
    )
    
    licencia_fecha_vencimiento = forms.DateField(
        required=False,
        widget=forms.DateInput(format='%Y-%m-%d', attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha de Vencimiento de Licencia'
    )

    def __init__(self, *args, **kwargs):
        empresa_id = kwargs.pop('empresa_id', None)
        super().__init__(*args, **kwargs)

        if empresa_id:
            self.fields['conductor_existente'].queryset = Conductor.objects.filter(
                empresa_id=empresa_id
            ).order_by('apellido_paterno', 'apellido_materno', 'nombres')

    def clean(self):
        cleaned_data = super().clean()
        usar_existente = cleaned_data.get('usar_conductor_existente')
        
        from apps.conductores.models import HabilitacionConductor
        
        if usar_existente:
            conductor = cleaned_data.get('conductor_existente')
            if not conductor:
                raise forms.ValidationError(
                    'Debe seleccionar un conductor existente.'
                )
            
            # Verificar habilitación vigente
            hab_activa = HabilitacionConductor.objects.filter(
                conductor=conductor,
                estado=EstadoHabilitacion.VIGENTE
            ).select_related('empresa').first()
            
            if hab_activa:
                if not hasattr(self, 'warnings'):
                    self.warnings = []
                self.warnings.append(
                    f"ADVERTENCIA: El conductor {conductor.nombre_completo} ya tiene una habilitación VIGENTE "
                    f"en la empresa '{hab_activa.empresa.razon_social}'."
                )
        else:
            # Validar campos requeridos para nuevo conductor
            dni = cleaned_data.get('dni')
            campos_requeridos = [
                'dni', 'nombres', 'apellido_paterno', 'apellido_materno',
                'fecha_nacimiento', 'licencia_numero', 'licencia_categoria',
                'licencia_fecha_emision', 'licencia_fecha_vencimiento'
            ]
            for campo in campos_requeridos:
                if not cleaned_data.get(campo):
                    self.add_error(campo, 'Este campo es requerido para un nuevo conductor.')
            
            if dni:
                # Validar formato de DNI (8 dígitos)
                validar_dni(dni)

                # Verificar habilitación vigente por DNI
                hab_activa = HabilitacionConductor.objects.filter(
                    conductor__dni=dni,
                    estado=EstadoHabilitacion.VIGENTE
                ).select_related('empresa').first()
                
                if hab_activa:
                    if not hasattr(self, 'warnings'):
                        self.warnings = []
                    self.warnings.append(
                        f"ADVERTENCIA: El conductor con DNI {dni} ya tiene una habilitación VIGENTE "
                        f"en la empresa '{hab_activa.empresa.razon_social}'."
                    )
        
        return cleaned_data


class ModificacionAutorizacionForm(forms.Form):
    """
    Formulario para trámite de MODIFICACIÓN DE AUTORIZACIÓN.
    Permite modificar rutas, frecuencias y datos de la autorización y empresa existentes.
    """
    
    # ===== DATOS DE LA AUTORIZACIÓN =====
    tipo_servicio = forms.ModelChoiceField(
        queryset=TipoServicioModel.objects.filter(activo=True).order_by('nombre'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Tipo de Servicio'
    )
    
    modalidad = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Modalidad'
    )
    
    rutas = forms.ModelMultipleChoiceField(
        queryset=Ruta.objects.filter(activo=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label='Nuevas Rutas Autorizadas'
    )
    
    frecuencias = forms.ModelMultipleChoiceField(
        queryset=Frecuencia.objects.filter(activo=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label='Nuevas Frecuencias'
    )
    
    descripcion_rutas = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3
        }),
        label='Descripción de Rutas Modificada'
    )
    
    # ===== DATOS DE LA EMPRESA =====
    razon_social = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Razón Social'
    )
    
    nombre_comercial = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Nombre Comercial'
    )
    
    domicilio_fiscal = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2
        }),
        label='Domicilio Fiscal'
    )
    
    representante_legal = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Representante Legal'
    )
    
    dni_representante = forms.CharField(
        max_length=8,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='DNI del Representante'
    )
    
    telefono = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Teléfono'
    )
    
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        label='Correo Electrónico'
    )
    
    motivo_modificacion = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describa el motivo de la modificación'
        }),
        label='Motivo de la Modificación'
    )
    
    def __init__(self, *args, autorizacion=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Prepoblar con datos de la autorización existente
        if autorizacion:
            self.fields['tipo_servicio'].initial = autorizacion.tipo_servicio
            self.fields['modalidad'].initial = autorizacion.modalidad
            self.fields['descripcion_rutas'].initial = autorizacion.descripcion_rutas
            # Prepoblar las rutas y frecuencias actuales
            self.fields['rutas'].initial = autorizacion.rutas.all()
            self.fields['frecuencias'].initial = autorizacion.frecuencias_asignadas.all()
            
            # Prepoblar con datos de la empresa asociada
            empresa = autorizacion.empresa
            if empresa:
                self.fields['razon_social'].initial = empresa.razon_social
                self.fields['nombre_comercial'].initial = empresa.nombre_comercial
                self.fields['domicilio_fiscal'].initial = empresa.domicilio_fiscal
                self.fields['representante_legal'].initial = empresa.representante_legal
                self.fields['dni_representante'].initial = empresa.dni_representante
                self.fields['telefono'].initial = empresa.telefono
                self.fields['email'].initial = empresa.email


class BajaVehiculoForm(forms.Form):
    """
    Formulario para trámite de BAJA DE VEHÍCULO.
    """
    
    motivo_baja = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Motivo de la baja del vehículo'
        }),
        label='Motivo de la Baja'
    )


class BajaConductorForm(forms.Form):
    """
    Formulario para trámite de BAJA DE CONDUCTOR.
    """
    
    motivo_baja = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Motivo de la baja del conductor'
        }),
        label='Motivo de la Baja'
    )


class TramiteEditForm(forms.ModelForm):
    """Formulario para editar trámites (campos limitados)."""
    
    class Meta:
        model = Tramite
        fields = ['descripcion_solicitud', 'plazo_subsanacion']
        widgets = {
            'descripcion_solicitud': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),
            'plazo_subsanacion': forms.DateInput(format='%Y-%m-%d', attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }


class TramiteBusquedaForm(forms.Form):
    """Formulario de búsqueda de trámites."""
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por expediente, empresa...'
        })
    )
    estado = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos los estados')] + list(Tramite._meta.get_field('estado').choices),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    tipo_tramite = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos los tipos')] + list(Tramite._meta.get_field('tipo_tramite').choices),
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class TransicionForm(forms.Form):
    """Formulario base para transiciones de estado."""
    comentario = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Comentario sobre la transición (opcional)'
        })
    )


class SubsanacionForm(TransicionForm):
    """Formulario para subsanación de observaciones."""
    # Solo comentario, sin selección de rol


class ObservacionForm(forms.Form):
    """Formulario para observar un trámite."""
    from utils.constants import Roles
    
    ROL_CHOICES = [
        ('', '--- Seleccionar rol responsable ---'),
        (Roles.MESA_PARTES, 'Mesa de Partes'),
        (Roles.ESPECIALISTA_TECNICO, 'Especialista Técnico'),
        (Roles.ASESORIA_LEGAL, 'Asesoría Legal'),
    ]
    
    observaciones = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Detalle las observaciones encontradas'
        }),
        help_text='Indique claramente qué debe subsanar el administrado'
    )
    plazo_subsanacion = forms.DateField(
        widget=forms.DateInput(format='%Y-%m-%d', attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        help_text='Fecha límite para subsanar observaciones'
    )
    rol_proximo_responsable = forms.ChoiceField(
        choices=ROL_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        help_text='Especifique a qué rol va dirigida la subsanación después de estas observaciones'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from utils.constants import Roles
        self.fields['rol_proximo_responsable'].choices = [
            ('', '--- Seleccionar rol responsable ---'),
            (Roles.MESA_PARTES, 'Mesa de Partes'),
            (Roles.ESPECIALISTA_TECNICO, 'Especialista Técnico'),
            (Roles.ASESORIA_LEGAL, 'Asesoría Legal'),
        ]


class AprobacionForm(forms.Form):
    """Formulario para aprobación final."""
    numero_resolucion = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 001-2025-GR-MDD'
        }),
        help_text='Número de la resolución que aprueba el trámite'
    )
    fecha_resolucion = forms.DateField(
        widget=forms.DateInput(format='%Y-%m-%d', attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        help_text='Fecha de la resolución',
        initial=timezone.now().date
    )
    archivo_resolucion = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf'
        }),
        help_text='Adjuntar resolución firmada (PDF)'
    )
    comentario = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Comentarios adicionales'
        })
    )

    def clean_numero_resolucion(self):
        numero = (self.cleaned_data.get('numero_resolucion') or '').strip()
        if not numero:
            return numero

        if Autorizacion.objects.filter(numero_resolucion=numero).exists():
            raise forms.ValidationError(
                'Este número de resolución ya existe. Debe ingresar uno diferente.'
            )

        return numero


    def __init__(self, *args, **kwargs):
        self.tramite = kwargs.pop('tramite', None)
        super().__init__(*args, **kwargs)

        if self.tramite and self.tramite.tipo_tramite == TipoTramite.RENOVACION_TUC:
            self.fields.pop('numero_resolucion', None)
            return

        if not self.is_bound:
            resolucion_base = self._get_resolucion_base_renovacion_tuc()
            if resolucion_base:
                self.fields['numero_resolucion'].initial = resolucion_base

    def _get_resolucion_base_renovacion_tuc(self):
        """Obtiene la resolución original con la que se habilitó el vehículo."""
        if not self.tramite:
            return ''

        vehiculo_tramite = (
            self.tramite.vehiculos_tramite
            .select_related('vehiculo_existente__autorizacion_principal')
            .first()
        )
        if not vehiculo_tramite or not vehiculo_tramite.vehiculo_existente:
            return self.tramite.autorizacion.numero_resolucion if self.tramite.autorizacion else ''

        vehiculo = vehiculo_tramite.vehiculo_existente
        if vehiculo.numero_resolucion:
            return vehiculo.numero_resolucion

        habilitacion_vigente = vehiculo.habilitacion_vigente
        if habilitacion_vigente and habilitacion_vigente.autorizacion_id:
            return habilitacion_vigente.autorizacion.numero_resolucion

        if vehiculo.autorizacion_principal_id:
            return vehiculo.autorizacion_principal.numero_resolucion

        return self.tramite.autorizacion.numero_resolucion if self.tramite.autorizacion else ''

    def clean_numero_resolucion(self):
        numero = (self.cleaned_data.get('numero_resolucion') or '').strip()
        if not numero:
            return numero

        if self.tramite and self.tramite.tipo_tramite == TipoTramite.RENOVACION_TUC:
            resolucion_base = self._get_resolucion_base_renovacion_tuc()
            if resolucion_base and numero == resolucion_base:
                return numero

        if Autorizacion.objects.filter(numero_resolucion=numero).exists():
            raise forms.ValidationError(
                'Este nÃºmero de resoluciÃ³n ya existe. Debe ingresar uno diferente.'
            )

        return numero


class VehiculoTUCForm(forms.ModelForm):
    """Formulario para registrar TUC de un vehículo en trámite."""
    class Meta:
        model = VehiculoTramite
        fields = [
            'numero_tuc', 'fecha_expedicion_tuc',
            'fecha_autorizacion_transportista', 'fecha_expiracion_transportista'
        ]
        widgets = {
            'numero_tuc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'N° TUC', 'style': 'min-width: 100px;', 'readonly': True}),
            'fecha_expedicion_tuc': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date', 'readonly': True}),
            'fecha_autorizacion_transportista': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date', 'data-tuc-inicio': True}),
            'fecha_expiracion_transportista': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date', 'readonly': True, 'data-tuc-vencimiento': True}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tramite = getattr(self.instance, 'tramite', None)
        vehiculo = getattr(self.instance, 'vehiculo_existente', None)

        if tramite and tramite.tipo_tramite == TipoTramite.RENOVACION_TUC:
            self.fields['numero_tuc'].widget.attrs['readonly'] = 'readonly'
            self.fields['fecha_expedicion_tuc'].widget.attrs['readonly'] = 'readonly'
        elif tramite and tramite.tipo_tramite in [
            TipoTramite.AUTORIZACION_INICIAL,
            TipoTramite.INCREMENTO_FLOTA,
        ]:
            self.fields['numero_tuc'].widget.attrs.pop('readonly', None)
            self.fields['fecha_expedicion_tuc'].widget.attrs.pop('readonly', None)

        if vehiculo and vehiculo.habilitacion_vigente:
            habilitacion = vehiculo.habilitacion_vigente
            if not self.instance.numero_tuc and habilitacion.numero_tuc:
                self.initial['numero_tuc'] = habilitacion.numero_tuc
            if not self.instance.fecha_expedicion_tuc and habilitacion.fecha_expedicion_tuc:
                self.initial['fecha_expedicion_tuc'] = habilitacion.fecha_expedicion_tuc
            if not self.instance.fecha_autorizacion_transportista and habilitacion.fecha_autorizacion_transportista:
                self.initial['fecha_autorizacion_transportista'] = habilitacion.fecha_autorizacion_transportista
            if not self.instance.fecha_expiracion_transportista and habilitacion.fecha_expiracion_transportista:
                self.initial['fecha_expiracion_transportista'] = habilitacion.fecha_expiracion_transportista

        tuc_requerido = not (
            tramite and tramite.tipo_tramite in [
                TipoTramite.AUTORIZACION_INICIAL,
                TipoTramite.INCREMENTO_FLOTA,
            ]
        )
        self.fields['numero_tuc'].required = tuc_requerido
        self.fields['fecha_expedicion_tuc'].required = tuc_requerido
        self.fields['fecha_autorizacion_transportista'].required = True
        self.fields['fecha_expiracion_transportista'].required = True


VehiculoTUCFormSet = forms.modelformset_factory(
    VehiculoTramite,
    form=VehiculoTUCForm,
    extra=0,
    can_delete=False
)


class DenegacionForm(forms.Form):
    """Formulario para denegación."""
    motivo_denegacion = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Motivo de la denegación'
        }),
        help_text='Fundamento legal y técnico de la denegación'
    )
    numero_resolucion = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Número de resolución (si aplica)'
        })
    )


class DocumentoAdjuntoForm(forms.ModelForm):
    """Formulario para agregar documentos a un trámite."""
    
    class Meta:
        model = DocumentoAdjunto
        fields = ['tipo_documento', 'nombre', 'descripcion', 'archivo']
        widgets = {
            'tipo_documento': forms.Select(attrs={
                'class': 'form-select'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del documento'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Descripción breve'
            }),
            'archivo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf'
            }),
        }


# ============================================================================
# FORMULARIOS DE DETALLE POR TIPO DE TRÁMITE
# ============================================================================

class RenovacionAutorizacionForm(forms.Form):
    """Formulario para renovación de autorización."""
    nueva_fecha_fin_vigencia = forms.DateField(
        label='Nueva Fecha de Vencimiento',
        widget=forms.DateInput(format='%Y-%m-%d', attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        help_text='Fecha hasta la cual se extenderá la vigencia'
    )

class BajaAutorizacionForm(forms.Form):
    """Formulario para baja de autorización."""
    motivo = forms.CharField(
        label='Motivo de Baja',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Explique el motivo de la baja voluntaria'
        })
    )

    def __init__(self, *args, **kwargs):
        self.autorizacion = kwargs.pop('autorizacion', None)
        super().__init__(*args, **kwargs)
        self.warning_tramites_pendientes = None
        self.vehiculos_afectados = []
        self.conductores_afectados = []

        if self.autorizacion:
            from .models import Tramite, EstadoTramite
            from apps.vehiculos.models import HabilitacionVehicular
            from apps.conductores.models import HabilitacionConductor

            # 1. Verificar trámites pendientes
            pendientes = Tramite.objects.filter(
                autorizacion=self.autorizacion,
                estado__in=[
                    EstadoTramite.RECIBIDO,
                    EstadoTramite.EN_CONTROL_CALIDAD,
                    EstadoTramite.EN_EVAL_TECNICA,
                    EstadoTramite.EN_DIRECCION_ADMINISTRATIVA,
                    EstadoTramite.EN_DIRECCION_GENERAL,
                    EstadoTramite.OBSERVADO,
                    EstadoTramite.EN_REVISION_LEGAL,
                    EstadoTramite.PENDIENTE_FIRMA
                ]
            ).exclude(tipo_tramite=TipoTramite.BAJA_AUTORIZACION)

            if pendientes.exists():
                self.warning_tramites_pendientes = [
                    f"{t.get_tipo_tramite_display()} ({t.numero_expediente})" 
                    for t in pendientes
                ]

            # 2. Listar vehículos afectados
            self.vehiculos_afectados = HabilitacionVehicular.objects.filter(
                autorizacion=self.autorizacion,
                estado=EstadoHabilitacion.VIGENTE
            ).select_related('vehiculo')

            # 3. Listar conductores afectados
            self.conductores_afectados = HabilitacionConductor.objects.filter(
                autorizacion=self.autorizacion,
                estado=EstadoHabilitacion.VIGENTE
            ).select_related('conductor')

class SuspensionAutorizacionForm(forms.Form):
    """Formulario para suspensión de autorización."""
    motivo = forms.CharField(
        label='Motivo de Suspensión',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Explique el motivo de la suspensión (sanción)'
        })
    )


class RenovacionTUCForm(forms.Form):
    """Formulario para renovación de TUC."""
    placa = forms.CharField(
        label='Placa',
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control text-uppercase',
            'placeholder': 'Ej: VDI307',
        })
    )
    vehiculo = forms.ModelChoiceField(
        queryset=Vehiculo.objects.none(),
        required=False,
        label='Vehiculo',
        widget=forms.HiddenInput()
    )
    numero_tuc = forms.CharField(

        label='Numero de TUC',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Numero de TUC',
            'readonly': True
        })
    )
    fecha_expedicion_tuc = forms.DateField(
        label='Fecha de Expedicion',
        widget=forms.DateInput(format='%Y-%m-%d', attrs={
            'class': 'form-control',
            'type': 'date',
            'readonly': True
        })
    )

    def __init__(self, *args, **kwargs):
        self.autorizacion = kwargs.pop('autorizacion', None)
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        queryset = Vehiculo.objects.filter(estado=EstadoVehiculo.HABILITADO)

        if self.autorizacion:
            queryset = queryset.filter(
                habilitaciones__autorizacion=self.autorizacion,
                habilitaciones__estado=EstadoHabilitacion.VIGENTE,
            )
        elif self.empresa:
            queryset = queryset.filter(empresa_propietaria=self.empresa)

        self.fields['vehiculo'].queryset = queryset.distinct().order_by('placa')

    def clean(self):
        cleaned_data = super().clean()
        placa = (cleaned_data.get('placa') or '').strip().upper().replace('-', '').replace(' ', '')
        vehiculo = None

        if placa:
            from apps.vehiculos.models import HabilitacionVehicular

            candidatos = [placa]
            if len(placa) >= 6:
                candidatos.append(f'{placa[:3]}-{placa[3:]}')

            vehiculo = (
                Vehiculo.objects.filter(
                    placa__in=candidatos,
                    estado=EstadoVehiculo.HABILITADO
                )
                .order_by('-id')
                .first()
            )

            if not vehiculo:
                self.add_error('placa', 'La placa no existe o no esta habilitada.')
                return cleaned_data

            habilitaciones = HabilitacionVehicular.objects.filter(
                vehiculo=vehiculo,
                estado=EstadoHabilitacion.VIGENTE
            )
            if self.autorizacion:
                habilitaciones = habilitaciones.filter(autorizacion=self.autorizacion)

            habilitacion_vigente = (
                habilitaciones
                .order_by('-fecha_inicio', '-id')
                .first()
            )

            if self.autorizacion and not habilitacion_vigente:
                self.add_error(
                    'placa',
                    'La placa no pertenece a la autorizacion seleccionada para esta renovacion TUC.'
                )
                return cleaned_data

            if self.empresa and vehiculo.empresa_propietaria_id != self.empresa.id:
                self.add_error(
                    'placa',
                    'La placa no pertenece a la empresa seleccionada.'
                )
                return cleaned_data

            if habilitacion_vigente:
                if not cleaned_data.get('numero_tuc'):
                    cleaned_data['numero_tuc'] = habilitacion_vigente.numero_tuc or ''
                if not cleaned_data.get('fecha_expedicion_tuc') and habilitacion_vigente.fecha_expedicion_tuc:
                    cleaned_data['fecha_expedicion_tuc'] = habilitacion_vigente.fecha_expedicion_tuc

        if not vehiculo:
            self.add_error('placa', 'No se encontro el vehiculo para la placa ingresada.')
        else:
            cleaned_data['vehiculo'] = vehiculo

        return cleaned_data


class BaseRenovacionTUCFormSet(forms.BaseFormSet):
    """Valida la seleccion multiple de vehiculos para renovar TUC."""

    def clean(self):
        super().clean()
        if any(self.errors):
            return

        vehiculos = set()
        placas = set()
        tiene_vehiculo = False

        for form in self.forms:
            cleaned = form.cleaned_data
            if cleaned.get('DELETE'):
                continue

            vehiculo = cleaned.get('vehiculo')
            placa = (cleaned.get('placa') or '').upper().replace('-', '').replace(' ', '')
            if not vehiculo and not placa:
                continue

            tiene_vehiculo = True
            clave_vehiculo = vehiculo.pk if vehiculo else None
            if clave_vehiculo and clave_vehiculo in vehiculos:
                raise forms.ValidationError('No puede seleccionar el mismo vehiculo mas de una vez.')
            if placa and placa in placas:
                raise forms.ValidationError('No puede ingresar la misma placa mas de una vez.')

            if clave_vehiculo:
                vehiculos.add(clave_vehiculo)
            if placa:
                placas.add(placa)

        if not tiene_vehiculo:
            raise forms.ValidationError('Debe seleccionar al menos un vehiculo para renovar TUC.')


RenovacionTUCFormSet = forms.formset_factory(
    RenovacionTUCForm,
    formset=BaseRenovacionTUCFormSet,
    can_delete=True,
    extra=1,
    min_num=1,
    validate_min=True,
)
