"""
Formularios para la app vehiculos.
"""
from utils.constants import EstadoVehiculo
from django import forms
from django.utils import timezone
from .models import Vehiculo, HabilitacionVehicular
from apps.empresas.models import EmpresaTransporte
from apps.autorizaciones.models import Autorizacion
from apps.configuracion.models import Carroceria, CategoriaVehiculo
from utils.constants import EstadoVehiculo


class VehiculoForm(forms.ModelForm):
    """Formulario para crear/editar vehículos."""
    
    numero_tuc = forms.CharField(
        max_length=50,
        required=False,
        label='Número TUC',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Número de TUC'
        })
    )
    
    fecha_expedicion_tuc = forms.DateField(
        required=False,
        label='Fecha Expedición TUC',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }, format='%Y-%m-%d')
    )
    
    fecha_autorizacion_transportista = forms.DateField(
        required=False,
        label='Fecha Autorización Transportista',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }, format='%Y-%m-%d')
    )
    
    fecha_expiracion_transportista = forms.DateField(
        required=False,
        label='Fecha Expiración Transportista',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }, format='%Y-%m-%d')
    )

    class Meta:
        model = Vehiculo
        fields = [
            'placa', 'empresa_propietaria', 'autorizacion_principal',
            'marca', 'modelo', 'anio_fabricacion', 'color',
            'numero_serie', 'numero_motor',
            'capacidad_sentados', 'peso_bruto', 'categoria', 'carroceria', 'estado',
            'numero_tiv', 'fecha_venc_soat', 'fecha_venc_citv',
            'numero_resolucion', 'fecha_resolucion', 'archivo_resolucion'
        ]
        widgets = {
            'placa': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: ABC-123',
                'style': 'text-transform: uppercase;'
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
            'numero_resolucion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'N° Resolución'
            }),
            'fecha_resolucion': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }, format='%Y-%m-%d'),
            'archivo_resolucion': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf'
            }),
            'empresa_propietaria': forms.Select(attrs={
                'class': 'form-select'
            }),
            'autorizacion_principal': forms.Select(attrs={
                'class': 'form-select'
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
                'min': 1990,
                'max': 2030
            }),
            'capacidad_sentados': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 60
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
            'estado': forms.Select(attrs={
                'class': 'form-select'
            }),
            'numero_tiv': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de TIV'
            }),
            'fecha_venc_soat': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }, format='%Y-%m-%d'),
            'fecha_venc_citv': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }, format='%Y-%m-%d'),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['empresa_propietaria'].queryset = EmpresaTransporte.objects.filter(
            estado='ACTIVA'
        ).order_by('razon_social')
        
        # Inicializar queryset vacío para autorización
        self.fields['autorizacion_principal'].queryset = Autorizacion.objects.none()
        
        # Guardar autorización inicial para detectar cambios
        self._initial_autorizacion = self.instance.autorizacion_principal if self.instance.pk else None

        # Cargar TUC si existe habilitación vigente
        if self.instance.pk:
            habilitacion = self.instance.habilitacion_vigente
            if habilitacion:
                self.fields['numero_tuc'].initial = habilitacion.numero_tuc
                self.fields['fecha_expedicion_tuc'].initial = habilitacion.fecha_expedicion_tuc
                self.fields['fecha_autorizacion_transportista'].initial = habilitacion.fecha_autorizacion_transportista
                self.fields['fecha_expiracion_transportista'].initial = habilitacion.fecha_expiracion_transportista

        # Si hay datos POST, filtrar por la empresa seleccionada
        if 'empresa_propietaria' in self.data:
            try:
                empresa_id = int(self.data.get('empresa_propietaria'))
                self.fields['autorizacion_principal'].queryset = Autorizacion.objects.filter(
                    empresa_id=empresa_id,
                    estado='VIGENTE'
                ).order_by('numero_resolucion')
            except (ValueError, TypeError):
                pass
        # Si es edición y tiene empresa, filtrar por esa empresa
        elif self.instance.pk and self.instance.empresa_propietaria:
            self.fields['autorizacion_principal'].queryset = Autorizacion.objects.filter(
                empresa=self.instance.empresa_propietaria,
                estado='VIGENTE'
            ).order_by('numero_resolucion')
            
        self.fields['autorizacion_principal'].required = False
    


    def clean_placa(self):
        placa = self.cleaned_data.get('placa')
        if not placa:
            return placa

        placa = placa.replace('-', '').replace(' ', '').upper()

        qs = Vehiculo.objects.select_related('empresa_propietaria').filter(placa=placa)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        # Si todos son BAJA, se permite registrar de nuevo
        bloqueante = qs.exclude(estado=EstadoVehiculo.BAJA).first()
        if not bloqueante:
            return placa

        empresa = (
            bloqueante.empresa_propietaria.razon_social
            if bloqueante.empresa_propietaria else 'SIN EMPRESA'
        )

        if bloqueante.estado == EstadoVehiculo.NO_HABILITADO:
            raise forms.ValidationError(
                f"⚠️ BLOQUEADO: El vehículo placa {placa} ya se encuentra NO HABILITADO "
                f"en la empresa '{empresa}'.\n"
                f"No puede ser registrado en una nueva empresa si ya está REGISTRADO."
            )

        if bloqueante.estado == EstadoVehiculo.PROPUESTO:
            raise forms.ValidationError(
                f"⚠️ BLOQUEADO: El vehículo placa {placa} ya se encuentra PROPUESTO "
                f"en la empresa '{empresa}'.\n"
                f"No puede ser registrado en otra empresa mientras mantenga ese estado."
            )

        if bloqueante.estado == EstadoVehiculo.HABILITADO:
            raise forms.ValidationError(
                f"⚠️ BLOQUEADO: El vehículo placa {placa} ya se encuentra HABILITADO "
                f"en la empresa '{empresa}'.\n"
                f"No puede ser registrado en una nueva empresa si ya está activo."
            )

        # Fallback por seguridad
        raise forms.ValidationError(
            f"⚠️ BLOQUEADO: El vehículo placa {placa} ya está registrado en la empresa '{empresa}'."
        )

    def save(self, commit=True):
        vehiculo = super().save(commit=False)
        
        if commit:
            vehiculo.save()
            self.save_m2m()
            
            autorizacion = self.cleaned_data.get('autorizacion_principal')
            numero_tuc = self.cleaned_data.get('numero_tuc')
            fecha_expedicion_tuc = self.cleaned_data.get('fecha_expedicion_tuc')
            fecha_autorizacion_transportista = self.cleaned_data.get('fecha_autorizacion_transportista')
            fecha_expiracion_transportista = self.cleaned_data.get('fecha_expiracion_transportista')
            
            # Si cambió la autorización, dar de baja la habilitación anterior
            if self._initial_autorizacion and self._initial_autorizacion != autorizacion:
                old_hab = HabilitacionVehicular.objects.filter(
                    vehiculo=vehiculo,
                    autorizacion=self._initial_autorizacion,
                    estado='VIGENTE'
                ).first()
                if old_hab:
                    old_hab.estado = 'BAJA'
                    old_hab.fecha_fin = timezone.now().date()
                    old_hab.motivo = 'Cambio manual de autorización'
                    old_hab.save()
            
            if autorizacion and vehiculo.estado == EstadoVehiculo.HABILITADO:
                # Buscar habilitación vigente para esta autorización y vehículo
                habilitacion = HabilitacionVehicular.objects.filter(
                    vehiculo=vehiculo,
                    autorizacion=autorizacion,
                    estado='VIGENTE'
                ).first()
                
                if habilitacion:
                    # Actualizar datos TUC si existe habilitación
                    updated = False
                    if numero_tuc is not None and numero_tuc != habilitacion.numero_tuc:
                        habilitacion.numero_tuc = numero_tuc
                        updated = True
                    if fecha_expedicion_tuc != habilitacion.fecha_expedicion_tuc:
                        habilitacion.fecha_expedicion_tuc = fecha_expedicion_tuc
                        updated = True
                    if fecha_autorizacion_transportista != habilitacion.fecha_autorizacion_transportista:
                        habilitacion.fecha_autorizacion_transportista = fecha_autorizacion_transportista
                        updated = True
                    if fecha_expiracion_transportista != habilitacion.fecha_expiracion_transportista:
                        habilitacion.fecha_expiracion_transportista = fecha_expiracion_transportista
                        updated = True
                    
                    if updated:
                        habilitacion.save()
                else:
                    # Crear nueva habilitación si no existe
                    HabilitacionVehicular.objects.create(
                        vehiculo=vehiculo,
                        autorizacion=autorizacion,
                        numero_tuc=numero_tuc or '',
                        fecha_expedicion_tuc=fecha_expedicion_tuc,
                        fecha_autorizacion_transportista=fecha_autorizacion_transportista,
                        fecha_expiracion_transportista=fecha_expiracion_transportista,
                        fecha_inicio=timezone.now().date(),
                        estado='VIGENTE',
                        motivo='Registro manual de vehículo'
                    )
        
        return vehiculo


class VehiculoBusquedaForm(forms.Form):
    """Formulario de búsqueda de vehículos."""
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por placa, marca, modelo...'
        })
    )
    estado = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos los estados')] + list(Vehiculo._meta.get_field('estado').choices),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    categoria = forms.ModelChoiceField(
        required=False,
        queryset=CategoriaVehiculo.objects.all(),
        empty_label='Todas las categorías',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    carroceria = forms.ModelChoiceField(
        required=False,
        queryset=Carroceria.objects.filter(activo=True),
        empty_label='Todas las carrocerías',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    empresa = forms.ModelChoiceField(
        required=False,
        queryset=EmpresaTransporte.objects.filter(estado='ACTIVA'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='Todas las empresas'
    )


class HabilitacionVehicularForm(forms.ModelForm):
    """Formulario para habilitación vehicular."""
    
    class Meta:
        model = HabilitacionVehicular
        fields = [
            'vehiculo', 'autorizacion', 'fecha_inicio', 'fecha_fin', 'motivo',
            'numero_tuc', 'fecha_expedicion_tuc', 
            'fecha_autorizacion_transportista', 'fecha_expiracion_transportista'
        ]
        widgets = {
            'vehiculo': forms.Select(attrs={'class': 'form-select'}),
            'autorizacion': forms.Select(attrs={'class': 'form-select'}),
            'fecha_inicio': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }, format='%Y-%m-%d'),
            'fecha_fin': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }, format='%Y-%m-%d'),
            'motivo': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'numero_tuc': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de TUC'
            }),
            'fecha_expedicion_tuc': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }, format='%Y-%m-%d'),
            'fecha_autorizacion_transportista': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }, format='%Y-%m-%d'),
            'fecha_expiracion_transportista': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }, format='%Y-%m-%d'),
        }
