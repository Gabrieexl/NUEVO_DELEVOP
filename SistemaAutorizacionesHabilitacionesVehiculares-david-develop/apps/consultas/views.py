"""
Vistas web para consultas.
"""
import logging
import time
import random
import string
import re
from django.views.generic import FormView, TemplateView, View
from django.http import JsonResponse
from apps.usuarios.mixins import RolRequeridoMixin
from django import forms
from apps.vehiculos.models import Vehiculo
from apps.conductores.models import Conductor
from apps.tramites.models import Tramite, HistorialTramite
from .services import ConsultaPlacaService, ConsultaConductorService
from .models import RegistroConsulta
from .authentication import get_client_ip
from utils.constants import Roles, EstadoTramite
from utils.validators import validar_dni

logger = logging.getLogger(__name__)


def _limpiar_comentario_observacion(comentario):
    """Oculta marcadores internos y deja solo el texto visible para el administrado."""
    if not comentario:
        return ''
    comentario = re.sub(
        r'\s*\[PR[^\]]*ROL RESPONSABLE:[^\]]+\]\s*',
        '\n',
        str(comentario),
        flags=re.IGNORECASE,
    )
    return comentario.strip()


def _get_observacion_publica(tramite):
    ultima_observacion = (
        HistorialTramite.objects
        .select_related('usuario')
        .filter(tramite=tramite, estado_nuevo=EstadoTramite.OBSERVADO)
        .order_by('-fecha', '-id')
        .first()
    )
    if not ultima_observacion:
        return None

    detalle = _limpiar_comentario_observacion(ultima_observacion.comentario)
    estado_observacion = (
        'pendiente' if tramite.estado == EstadoTramite.OBSERVADO else 'levantada'
    )
    usuario = ultima_observacion.usuario

    return {
        'estado': estado_observacion,
        'detalle': detalle or 'No se registró detalle de la observación.',
        'fecha': ultima_observacion.fecha,
        'area': usuario.get_rol_display() if usuario else 'Área evaluadora',
    }

# Roles para vistas de consulta (según matriz acordada).
CONSULTA_GENERAL_ROLES = [
    Roles.ADMIN_SISTEMA,
    Roles.MESA_PARTES,
    Roles.ESPECIALISTA_TECNICO,
    Roles.ASESORIA_LEGAL,
    Roles.DIRECTOR_GENERAL,
    Roles.DIRECTOR_ADMINISTRATIVO,
    Roles.CONSULTA_INTERNA,
    Roles.CONSULTA_INSPECTOR,
    Roles.CONTROL_CALIDAD,
]
CONSULTA_INTERNA_ROLES = [
    Roles.ADMIN_SISTEMA,
    Roles.MESA_PARTES,
    Roles.ESPECIALISTA_TECNICO,
    Roles.ASESORIA_LEGAL,
    Roles.DIRECTOR_GENERAL,
    Roles.DIRECTOR_ADMINISTRATIVO,
    Roles.CONSULTA_INTERNA,
    Roles.CONTROL_CALIDAD,
]

class ConsultaPlacaForm(forms.Form):
    """Formulario para consulta por placa."""
    placa = forms.CharField(
        max_length=10,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Ingrese la placa (ej: ABC-123)',
            'autofocus': True,
            'style': 'text-transform: uppercase;'
        }),
        help_text="Ingrese la placa del vehículo a consultar"
    )
    
    def clean_placa(self):
        placa = self.cleaned_data['placa']
        # Normalizar: quitar guiones y espacios, convertir a mayúsculas
        placa = placa.replace('-', '').replace(' ', '').upper()
        return placa


class ConsultaPlacaView(RolRequeridoMixin, TemplateView):
    """
    Vista para consulta por placa - REQUIERE LOGIN.
    Solo para inspectores y usuarios autorizados.
    """
    template_name = 'consultas/consulta_placa.html'
    roles_permitidos = CONSULTA_GENERAL_ROLES
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ConsultaPlacaForm()
        context['titulo'] = 'Consulta de Habilitaciónes Vehiculares'
        return context
    
    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        form = ConsultaPlacaForm(request.POST)
        context['form'] = form
        
        if form.is_valid():
            inicio = time.time()
            placa = form.cleaned_data['placa']
            
            resultado = ConsultaPlacaService.consultar_placa(placa)
            tiempo_ms = int((time.time() - inicio) * 1000)
            
            # Registrar consulta
            RegistroConsulta.objects.create(
                placa_consultada=placa,
                ip_origen=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                resultado_exitoso=resultado is not None,
                mensaje_error='' if resultado else 'Vehículo no encontrado',
                tiempo_respuesta_ms=tiempo_ms
            )
            
            if resultado:
                context['resultado'] = resultado
            else:
                context['error'] = f'No se encontró información para la placa: {placa}'
        
        return self.render_to_response(context)



class ConsultaInternaView(RolRequeridoMixin, TemplateView):
    """
    Vista para consulta interna (usuarios autenticados).
    Permite ver más detalles que la consulta pública.
    """
    template_name = 'consultas/consulta_interna.html'
    roles_permitidos = CONSULTA_INTERNA_ROLES
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ConsultaPlacaForm()
        context['titulo'] = 'Consulta Interna de Vehículos'
        return context
    
    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        form = ConsultaPlacaForm(request.POST)
        context['form'] = form
        
        if form.is_valid():
            placa = form.cleaned_data['placa']
            resultado = ConsultaPlacaService.consultar_placa(placa)
            
            if resultado:
                context['resultado'] = resultado
                # Para consulta interna, también mostramos el historial
                vehiculo = Vehiculo.objects.filter(placa=placa).order_by('-id').first()
                if vehiculo:
                    context['habilitaciones_historico'] = (
                        vehiculo.habilitaciones.all().order_by('-fecha_inicio')[:10]
                    )
            else:
                context['error'] = f'No se encontró información para la placa: {placa}'
        
        return self.render_to_response(context)


# =============================================================================
# CONSULTA DE TRÁMITES (Público)
# =============================================================================

def generar_captcha():
    """Genera un código captcha simple de 5 caracteres."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))


class ConsultaTramiteForm(forms.Form):
    """Formulario para consulta de trámite por DNI o expediente."""
    TIPO_BUSQUEDA_CHOICES = [
        ('dni', 'Por DNI del Solicitante'),
        ('expediente', 'Por Número de Expediente'),
    ]
    
    tipo_busqueda = forms.ChoiceField(
        choices=TIPO_BUSQUEDA_CHOICES,
        initial='dni',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Tipo de Búsqueda'
    )
    
    valor_busqueda = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Ingrese DNI o N° de Expediente',
            'autofocus': True,
            'style': 'text-transform: uppercase;'
        }),
        label='Valor de Búsqueda'
    )
    
    captcha = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese el código',
            'autocomplete': 'off',
            'style': 'text-transform: uppercase;'
        }),
        label='Código de Verificación'
    )
    
    def clean_valor_busqueda(self):
        valor = self.cleaned_data['valor_busqueda']
        return valor.strip()
    
    def clean_captcha(self):
        captcha = self.cleaned_data['captcha']
        return captcha.strip().upper()

    def clean(self):
        cleaned_data = super().clean()
        tipo_busqueda = cleaned_data.get('tipo_busqueda')
        valor = cleaned_data.get('valor_busqueda', '')

        if tipo_busqueda == 'dni':
            dni = ''.join(c for c in valor if c.isdigit())
            if not dni:
                raise forms.ValidationError('Ingrese un DNI válido.')
            validar_dni(dni)
            cleaned_data['valor_busqueda'] = dni
        else:
            cleaned_data['valor_busqueda'] = valor.strip().upper()

        return cleaned_data


class ConsultaTramiteView(TemplateView):
    """
    Vista pública para consulta de estado de trámite.
    Permite buscar por DNI del solicitante o por número de expediente.
    Incluye captcha para seguridad. NO requiere autenticación.
    """
    template_name = 'consultas/consulta_tramite.html'
    
    def get(self, request, *args, **kwargs):
        context = {}
        context['form'] = ConsultaTramiteForm()
        context['titulo'] = 'Consulta de Estado de Trámite'
        
        # Generar nuevo captcha solo en GET
        captcha_code = generar_captcha()
        request.session['captcha_code'] = captcha_code
        context['captcha_code'] = captcha_code
        
        # Verificar si viene un ID de trámite para ver detalle
        tramite_id = request.GET.get('id')
        if tramite_id:
            # Validar que sea un número entero válido
            try:
                tramite_id = int(tramite_id)
                tramite = Tramite.objects.select_related('empresa', 'autorizacion').get(pk=tramite_id)
                context['tramite'] = tramite
                context['historial'] = tramite.historial.all().order_by('-fecha')[:10]
                context['observacion_publica'] = _get_observacion_publica(tramite)
                context['ver_detalle'] = True
            except (ValueError, TypeError):
                # Ignorar IDs no válidos (como UUIDs de VS Code)
                pass
            except Tramite.DoesNotExist:
                context['error'] = 'Trámite no encontrado'
        
        return self.render_to_response(context)
    
    def post(self, request, *args, **kwargs):
        context = {}
        context['titulo'] = 'Consulta de Estado de Trámite'
        form = ConsultaTramiteForm(request.POST)
        context['form'] = form
        
        # Obtener captcha de sesión ANTES de regenerar
        captcha_sesion = request.session.get('captcha_code', '')
        captcha_ingresado = request.POST.get('captcha', '').strip().upper()
        
        # Verificar captcha
        if captcha_sesion != captcha_ingresado:
            context['error'] = 'El código de seguridad es incorrecto. Intente nuevamente.'
            # Generar nuevo captcha después de la validación fallida
            captcha_code = generar_captcha()
            request.session['captcha_code'] = captcha_code
            context['captcha_code'] = captcha_code
            return self.render_to_response(context)
        
        if form.is_valid():
            tipo_busqueda = form.cleaned_data['tipo_busqueda']
            valor = form.cleaned_data['valor_busqueda']
            
            if tipo_busqueda == 'dni':
                # Buscar por DNI del solicitante - retorna lista
                tramites = Tramite.objects.filter(
                    solicitante_dni__iexact=valor
                ).select_related('empresa', 'autorizacion').order_by('-fecha_creacion')
                
                if tramites.exists():
                    tramites_lista = list(tramites)
                    for tramite in tramites_lista:
                        tramite.observacion_publica = _get_observacion_publica(tramite)
                        tramite.historial_publico = tramite.historial.all().order_by('-fecha')[:10]
                    context['tramites_lista'] = tramites_lista
                    context['dni_consultado'] = valor
                else:
                    context['error'] = f'No se encontraron trámites para el DNI: {valor}'
            
            else:  # expediente
                # Buscar por número de expediente - retorna uno
                tramite = Tramite.objects.filter(
                    numero_expediente__iexact=valor
                ).select_related('empresa', 'autorizacion').first()
                
                if not tramite:
                    tramite = Tramite.objects.filter(
                        expediente_externo__iexact=valor
                    ).select_related('empresa', 'autorizacion').first()
                
                if tramite:
                    context['tramite'] = tramite
                    context['historial'] = tramite.historial.all().order_by('-fecha')[:10]
                    context['observacion_publica'] = _get_observacion_publica(tramite)
                else:
                    context['error'] = f'No se encontró ningún trámite con el expediente: {valor}'
        
        # Generar nuevo captcha para siguiente consulta
        captcha_code = generar_captcha()
        request.session['captcha_code'] = captcha_code
        context['captcha_code'] = captcha_code
        
        return self.render_to_response(context)


# =============================================================================
# CONSULTA POR CONDUCTOR (DNI)
# =============================================================================

class ConsultaConductorForm(forms.Form):
    """Formulario para consulta por DNI de conductor."""
    dni = forms.CharField(
        max_length=8,
        min_length=8,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Ingrese el DNI del conductor',
            'autofocus': True,
            'maxlength': '8',
            'inputmode': 'numeric',
            'pattern': '[0-9]{8}',
            'title': 'Ingrese 8 digitos'
        }),
        help_text="Ingrese el DNI del conductor a consultar (8 digitos)"
    )
    
    def clean_dni(self):
        dni = self.cleaned_data['dni']
        # Normalizar: solo números
        dni = ''.join(c for c in dni if c.isdigit())
        if len(dni) != 8:
            raise forms.ValidationError("El DNI debe tener exactamente 8 dígitos")
        return dni


class ConsultaConductorView(RolRequeridoMixin, TemplateView):
    """
    Vista para consulta por DNI de conductor - REQUIERE LOGIN.
    Solo para inspectores y usuarios autorizados.
    """
    template_name = 'consultas/consulta_conductor.html'
    roles_permitidos = CONSULTA_GENERAL_ROLES
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ConsultaConductorForm()
        context['titulo'] = 'Consulta de Habilitación de Conductor'
        return context
    
    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        form = ConsultaConductorForm(request.POST)
        context['form'] = form
        
        if form.is_valid():
            inicio = time.time()
            dni = form.cleaned_data['dni']
            
            resultado = ConsultaConductorService.consultar_conductor(dni)
            tiempo_ms = int((time.time() - inicio) * 1000)
            
            # Registrar consulta (reutilizando RegistroConsulta)
            RegistroConsulta.objects.create(
                placa_consultada=dni,  # Guardamos solo el DNI (8 digitos) que cabe en el campo de 10 chars
                ip_origen=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                resultado_exitoso=resultado is not None,
                mensaje_error='' if resultado else 'Conductor no encontrado',
                tiempo_respuesta_ms=tiempo_ms
            )
            
            if resultado:
                context['resultado'] = resultado
            else:
                context['error'] = f'No se encontró información para el DNI: {dni}'
        
        return self.render_to_response(context)


class ConsultaPlacaInternaView(RolRequeridoMixin, View):
    """
    Vista interna para verificar placa vía AJAX.
    Retorna JSON con el estado del vehículo.
    """
    roles_permitidos = CONSULTA_INTERNA_ROLES
    def get(self, request, placa, *args, **kwargs):
        # Normalizar placa
        placa = placa.replace('-', '').replace(' ', '').upper()
        
        # Extraer ID de autorización si se proporciona
        autorizacion_id = request.GET.get('autorizacion_id')
        if autorizacion_id:
            try:
                autorizacion_id = int(autorizacion_id)
            except (ValueError, TypeError):
                autorizacion_id = None
        
        inicio = time.time()
        try:
            resultado = ConsultaPlacaService.consultar_placa(placa, autorizacion_id=autorizacion_id)
            tiempo_ms = int((time.time() - inicio) * 1000)

            RegistroConsulta.objects.create(
                placa_consultada=placa,
                ip_origen=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                resultado_exitoso=resultado is not None,
                mensaje_error='' if resultado else 'Vehículo no encontrado',
                tiempo_respuesta_ms=tiempo_ms
            )

            if resultado:
                return JsonResponse({
                    'found': True,
                    'data': resultado
                })

            return JsonResponse({
                'found': False,
                'message': 'Vehículo no registrado en el sistema.'
            })
        except Exception as exc:
            tiempo_ms = int((time.time() - inicio) * 1000)
            logger.exception('Error en verificación interna de placa %s', placa)

            RegistroConsulta.objects.create(
                placa_consultada=placa,
                ip_origen=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                resultado_exitoso=False,
                mensaje_error=str(exc)[:250],
                tiempo_respuesta_ms=tiempo_ms
            )

            return JsonResponse({
                'found': False,
                'message': 'Error interno al verificar la placa. Revise logs del servidor.'
            }, status=500)

class ConsultaDNIInternaView(RolRequeridoMixin, View):
    """
    Vista interna para verificar DNI vía AJAX.
    Retorna JSON con los datos del conductor.
    """
    roles_permitidos = CONSULTA_INTERNA_ROLES
    def get(self, request, dni, *args, **kwargs):
        # Normalizar DNI
        dni = ''.join(filter(str.isdigit, dni))
        
        inicio = time.time()
        resultado = ConsultaConductorService.consultar_conductor(dni)
        tiempo_ms = int((time.time() - inicio) * 1000)
        
        # Registrar consulta
        RegistroConsulta.objects.create(
            placa_consultada=dni,
            ip_origen=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            resultado_exitoso=resultado is not None,
            mensaje_error='' if resultado else 'Conductor no encontrado',
            tiempo_respuesta_ms=tiempo_ms
        )
        
        if resultado:
            return JsonResponse({
                'found': True,
                'data': resultado
            })
        else:
            return JsonResponse({
                'found': False,
                'message': 'Conductor no registrado en el sistema.'
            })


