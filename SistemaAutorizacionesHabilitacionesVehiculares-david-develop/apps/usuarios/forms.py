"""
Formularios de usuarios del sistema DRTC.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django.contrib.auth import get_user_model

from utils.constants import Roles

Usuario = get_user_model()


class LoginForm(AuthenticationForm):
    """Formulario de inicio de sesión personalizado."""
    
    username = forms.CharField(
        label='Usuario',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre de usuario',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña',
        })
    )


class UsuarioCreationForm(UserCreationForm):
    """Formulario para crear nuevos usuarios."""
    
    class Meta:
        model = Usuario
        fields = (
            'username', 'email', 'dni', 'first_name', 'last_name',
            'rol', 'telefono', 'area', 'cargo', 'is_active',
        )
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'dni': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '8', 'inputmode': 'numeric', 'pattern': '[0-9]{8}'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'area': forms.TextInput(attrs={'class': 'form-control'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True


class UsuarioUpdateForm(UserChangeForm):
    """Formulario para editar usuarios existentes."""
    
    password = None  # Remover campo de contraseña del formulario de edición
    
    class Meta:
        model = Usuario
        fields = (
            'username', 'email', 'dni', 'first_name', 'last_name',
            'rol', 'telefono', 'area', 'cargo', 'is_active',
        )
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'dni': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '8', 'inputmode': 'numeric', 'pattern': '[0-9]{8}'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'area': forms.TextInput(attrs={'class': 'form-control'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class UsuarioPerfilForm(forms.ModelForm):
    """Formulario para que el usuario edite su propio perfil."""
    
    class Meta:
        model = Usuario
        fields = ('email', 'telefono', 'first_name', 'last_name')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }


class CambiarPasswordForm(forms.Form):
    """Formulario para cambiar contraseña."""
    
    password_actual = forms.CharField(
        label='Contraseña actual',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password_nuevo = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password_confirmar = forms.CharField(
        label='Confirmar nueva contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password_nuevo = cleaned_data.get('password_nuevo')
        password_confirmar = cleaned_data.get('password_confirmar')
        
        if password_nuevo and password_confirmar:
            if password_nuevo != password_confirmar:
                raise forms.ValidationError(
                    'Las contraseñas nuevas no coinciden.'
                )
        
        return cleaned_data

