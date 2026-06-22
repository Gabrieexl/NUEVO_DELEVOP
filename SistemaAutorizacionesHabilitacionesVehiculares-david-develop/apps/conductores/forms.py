"""
Formularios para la app conductores.
"""

from django import forms
from .models import Conductor, HabilitacionConductor
from apps.empresas.models import EmpresaTransporte
from apps.autorizaciones.models import Autorizacion
from utils.validators import validar_dni


class ConductorForm(forms.ModelForm):
    """Formulario para crear/editar conductores."""
    
    empresa = forms.ModelChoiceField(
        queryset=EmpresaTransporte.objects.filter(estado='ACTIVA').order_by('razon_social'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Empresa de Transporte'
    )
    
    autorizacion = forms.ModelChoiceField(
        queryset=Autorizacion.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Autorización Principal',
        required=False
    )
    
    class Meta:
        model = Conductor
        fields = [
            'empresa', 'dni', 'nombres', 'apellido_paterno', 'apellido_materno',
            'fecha_nacimiento', 'licencia_numero', 'licencia_categoria',
            'licencia_fecha_emision', 'licencia_fecha_vencimiento',
            'telefono', 'email', 'direccion', 'estado',
            'numero_resolucion', 'fecha_resolucion', 'archivo_resolucion'
        ]
        widgets = {
            'dni': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'DNI (8 digitos)',
                'maxlength': '8',
                'inputmode': 'numeric',
                'pattern': '[0-9]{8}'
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
            'fecha_nacimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }, format='%Y-%m-%d'),
            'licencia_numero': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de licencia'
            }),
            'licencia_categoria': forms.Select(attrs={
                'class': 'form-select'
            }),
            'licencia_fecha_emision': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }, format='%Y-%m-%d'),
            'licencia_fecha_vencimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }, format='%Y-%m-%d'),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección'
            }),
            'estado': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si estamos editando, cargar la autorización vigente actual
        if self.instance.pk:
            hab_vigente = self.instance.habilitacion_vigente
            if hab_vigente:
                self.fields['autorizacion'].initial = hab_vigente.autorizacion_id
                self.fields['autorizacion'].queryset = Autorizacion.objects.filter(
                    empresa=self.instance.empresa,
                    estado='VIGENTE'
                ).order_by('numero_resolucion')

        # Lógica para filtrar si hay datos POST (cascada)
        if 'empresa' in self.data:
            try:
                empresa_id = int(self.data.get('empresa'))
                self.fields['autorizacion'].queryset = Autorizacion.objects.filter(
                    empresa_id=empresa_id,
                    estado='VIGENTE'
                ).order_by('numero_resolucion')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and not self.fields['autorizacion'].queryset.exists():
             self.fields['autorizacion'].queryset = Autorizacion.objects.filter(
                empresa=self.instance.empresa,
                estado='VIGENTE'
            ).order_by('numero_resolucion')

    def clean_dni(self):
        dni = self.cleaned_data.get('dni')
        if dni:
            validar_dni(dni)
        return dni

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Pasar la autorización seleccionada al signal
        autorizacion = self.cleaned_data.get('autorizacion')
        if autorizacion:
            instance._autorizacion_id = autorizacion.id
        
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class ConductorBusquedaForm(forms.Form):
    """Formulario de búsqueda de conductores."""
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por DNI, nombres, licencia...'
        })
    )
    estado = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos los estados')] + list(Conductor._meta.get_field('estado').choices),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    licencia_categoria = forms.ChoiceField(
        required=False,
        choices=[('', 'Todas las categorías')] + list(Conductor._meta.get_field('licencia_categoria').choices),
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class HabilitacionConductorForm(forms.ModelForm):
    """Formulario para habilitación de conductor."""
    
    class Meta:
        model = HabilitacionConductor
        fields = ['conductor', 'empresa', 'autorizacion', 'fecha_inicio', 'fecha_fin', 'motivo']
        widgets = {
            'conductor': forms.Select(attrs={'class': 'form-select'}),
            'empresa': forms.Select(attrs={'class': 'form-select'}),
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
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['empresa'].queryset = EmpresaTransporte.objects.filter(
            estado='ACTIVA'
        ).order_by('razon_social')
        self.fields['autorizacion'].queryset = Autorizacion.objects.filter(
            estado='VIGENTE'
        ).select_related('empresa')

