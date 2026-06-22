"""
Formularios para la app configuracion.
"""

from django import forms
from .models import Ruta, Frecuencia, TipoServicio, Carroceria


class TipoServicioForm(forms.ModelForm):
    """Formulario para crear/editar tipos de servicio."""
    
    class Meta:
        model = TipoServicio
        fields = ['codigo', 'nombre', 'descripcion', 'activo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: REGULAR'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre descriptivo'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CarroceriaForm(forms.ModelForm):
    """Formulario para crear/editar carrocerías."""
    
    class Meta:
        model = Carroceria
        fields = ['categoria', 'codigo', 'nombre', 'descripcion', 'activo']
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: SEDAN'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre descriptivo'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class RutaForm(forms.ModelForm):
    """Formulario para crear/editar rutas."""
    
    class Meta:
        model = Ruta
        fields = [
            'codigo', 'nombre', 'origen', 'destino', 'puntos_intermedios',
            'distancia_km', 'tiempo_estimado_minutos', 'ambito', 'activo', 'observaciones'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: R001'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre descriptivo'}),
            'origen': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ciudad de origen'}),
            'destino': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ciudad de destino'}),
            'puntos_intermedios': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2,
                'placeholder': 'Puntos intermedios separados por coma'
            }),
            'distancia_km': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tiempo_estimado_minutos': forms.NumberInput(attrs={'class': 'form-control'}),
            'ambito': forms.Select(attrs={'class': 'form-select'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class FrecuenciaForm(forms.ModelForm):
    """Formulario para crear/editar frecuencias."""
    
    DIAS_CHOICES = [
        ('LU', 'Lunes'),
        ('MA', 'Martes'),
        ('MI', 'Miércoles'),
        ('JU', 'Jueves'),
        ('VI', 'Viernes'),
        ('SA', 'Sábado'),
        ('DO', 'Domingo'),
    ]
    
    dias_operacion_lista = forms.MultipleChoiceField(
        choices=DIAS_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True,
        label='Días de Operación'
    )
    
    class Meta:
        model = Frecuencia
        fields = [
            'codigo', 'nombre', 'descripcion', 'hora_salida', 
            'hora_llegada_estimada', 'activo', 'observaciones'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: F001'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre descriptivo'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'hora_salida': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'hora_llegada_estimada': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si hay instancia, cargar los días seleccionados
        if self.instance and self.instance.pk:
            self.fields['dias_operacion_lista'].initial = self.instance.dias_operacion_lista
    
    def clean(self):
        cleaned_data = super().clean()
        dias = cleaned_data.get('dias_operacion_lista', [])
        cleaned_data['dias_operacion'] = ','.join(dias)
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.dias_operacion = self.cleaned_data.get('dias_operacion', '')
        if commit:
            instance.save()
        return instance
