"""
Formularios para la app autorizaciones.
"""

from django import forms
from django.forms import inlineformset_factory
from .models import Autorizacion
from apps.empresas.models import EmpresaTransporte
from apps.configuracion.models import Ruta, Frecuencia, TipoServicio


class AutorizacionForm(forms.ModelForm):
    """Formulario para crear/editar autorizaciones."""
    
    rutas = forms.ModelMultipleChoiceField(
        queryset=Ruta.objects.filter(activo=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label='Rutas Autorizadas'
    )
    
    frecuencias_asignadas = forms.ModelMultipleChoiceField(
        queryset=Frecuencia.objects.filter(activo=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label='Frecuencias Asignadas'
    )
    
    class Meta:
        model = Autorizacion
        fields = [
            'empresa', 'numero_resolucion', 'fecha_resolucion', 'archivo_resolucion',
            'fecha_inicio_vigencia', 'fecha_fin_vigencia',
            'ambito', 'tipo_servicio', 'estado', 'rutas', 'frecuencias_asignadas',
            'descripcion_rutas', 'frecuencias', 'observaciones'
        ]
        widgets = {
            'empresa': forms.Select(attrs={
                'class': 'form-select'
            }),
            'numero_resolucion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 001-2025-GR-MDD'
            }),
            'fecha_resolucion': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }, format='%Y-%m-%d'),
            'archivo_resolucion': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf'
            }),
            'fecha_inicio_vigencia': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }, format='%Y-%m-%d'),
            'fecha_fin_vigencia': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }, format='%Y-%m-%d'),
            'ambito': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tipo_servicio': forms.Select(attrs={
                'class': 'form-select'
            }),
            'estado': forms.Select(attrs={
                'class': 'form-select'
            }),
            'descripcion_rutas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción adicional de rutas (opcional)'
            }),
            'frecuencias': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Descripción adicional de frecuencias (opcional)'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones adicionales'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['empresa'].queryset = EmpresaTransporte.objects.filter(
            estado='ACTIVA'
        ).order_by('razon_social')
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio_vigencia')
        fecha_fin = cleaned_data.get('fecha_fin_vigencia')
        
        if fecha_inicio and fecha_fin and fecha_fin <= fecha_inicio:
            raise forms.ValidationError(
                'La fecha de fin de vigencia debe ser posterior a la fecha de inicio.'
            )
        
        return cleaned_data


class AutorizacionBusquedaForm(forms.Form):
    """Formulario de búsqueda de autorizaciones."""
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por Nº resolución, empresa...'
        })
    )
    estado = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos los estados')] + list(Autorizacion._meta.get_field('estado').choices),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    tipo_servicio = forms.ModelChoiceField(
        required=False,
        queryset=TipoServicio.objects.filter(activo=True),
        empty_label='Todos los tipos',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
