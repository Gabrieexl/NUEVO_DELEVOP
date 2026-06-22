"""
Formularios para la app empresas.
"""

from django import forms
from .models import EmpresaTransporte
from utils.validators import validar_ruc, validar_dni


class EmpresaTransporteForm(forms.ModelForm):
    """Formulario para crear/editar empresas de transporte."""
    
    class Meta:
        model = EmpresaTransporte
        fields = [
            'ruc', 'razon_social', 'nombre_comercial',
            'domicilio_fiscal', 'representante_legal', 'dni_representante',
            'telefono', 'email', 'estado'
        ]
        widgets = {
            'ruc': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese RUC (11 dígitos)',
                'maxlength': '11',
                'inputmode': 'numeric',
                'pattern': '[0-9]{11}'
            }),
            'razon_social': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Razón Social'
            }),
            'nombre_comercial': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre Comercial (opcional)'
            }),
            'domicilio_fiscal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección completa'
            }),
            'representante_legal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo del representante'
            }),
            'dni_representante': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'DNI (8 digitos)',
                'maxlength': '8',
                'inputmode': 'numeric',
                'pattern': '[0-9]{8}'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono de contacto',
                'inputmode': 'numeric',
                'pattern': '[0-9]*',
                'maxlength': '20'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
            'estado': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
    
    def clean_ruc(self):
        ruc = self.cleaned_data.get('ruc')
        if ruc:
            validar_ruc(ruc)
        return ruc
    
    def clean_dni_representante(self):
        dni = self.cleaned_data.get('dni_representante')
        if dni:
            validar_dni(dni)
        return dni


class EmpresaBusquedaForm(forms.Form):
    """Formulario de búsqueda de empresas."""
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por RUC, razón social...'
        })
    )
    estado = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos los estados')] + list(EmpresaTransporte._meta.get_field('estado').choices),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

