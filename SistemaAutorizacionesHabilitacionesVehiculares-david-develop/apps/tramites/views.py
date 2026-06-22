"""
Vistas para la app tramites.
"""
from decimal import Decimal
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, View, FormView, DeleteView
)
from django.contrib import messages
from urllib.parse import urlencode
from django.urls import reverse_lazy, reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse, FileResponse, Http404
from django.db import transaction
from decimal import Decimal
import os

from .models import Tramite, HistorialTramite, DatosTramite, ReciboPago, VehiculoTramite, ConductorTramite
from .forms import (
    TramiteForm, TramiteEditForm, TramiteBusquedaForm,
    TransicionForm, SubsanacionForm, ObservacionForm, AprobacionForm,
    DenegacionForm, DocumentoAdjuntoForm,
    AutorizacionInicialForm, AutorizacionRutaForm, IncrementoFlotaForm, SustitucionVehiculoForm,
    HabilitacionConductorForm, ModificacionAutorizacionForm,
    BajaVehiculoForm, BajaConductorForm,
    RenovacionAutorizacionForm, BajaAutorizacionForm, SuspensionAutorizacionForm,
    RenovacionTUCForm, RenovacionTUCFormSet,
    ReciboPagoForm, VehiculoTramiteForm, ConductorTramiteForm,
    VehiculoTUCFormSet, IncrementoFlotaVehiculoFormSet,
    IncrementoFlotaConductorFormSet
)
from apps.usuarios.mixins import RolRequeridoMixin, rol_requerido
from apps.documentos.models import DocumentoAdjunto
from apps.autorizaciones.models import Autorizacion
from apps.vehiculos.models import Vehiculo, HabilitacionVehicular
from apps.conductores.models import Conductor, HabilitacionConductor
from apps.empresas.models import EmpresaTransporte
from apps.configuracion.models import Carroceria, TipoServicio
from utils.constants import (
    Roles, EstadoTramite, TipoTramite, EstadoVehiculo, 
    EstadoHabilitacion, EstadoConductor, DepartamentosPeru
)
from utils.exports import ExcelExporter
from django.utils import timezone

def _get_safe_return_url(request, default):
    next_url = request.GET.get('next') or request.POST.get('next')
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url

    referer = request.META.get('HTTP_REFERER')
    if referer and url_has_allowed_host_and_scheme(
        referer,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return referer

    return default

# Roles por acción en trámites (según matriz acordada).
TRAMITES_VER_ROLES = [
    Roles.ADMIN_SISTEMA,
    Roles.MESA_PARTES,
    Roles.ESPECIALISTA_TECNICO,
    Roles.ASESORIA_LEGAL,
    Roles.DIRECTOR_GENERAL,
    Roles.DIRECTOR_ADMINISTRATIVO,
    Roles.CONTROL_CALIDAD,
]
TRAMITES_CREAR_EDITAR_ROLES = [
    Roles.ADMIN_SISTEMA,
    Roles.MESA_PARTES,
]
TRAMITES_VEHICULO_EDIT_ROLES = [
    Roles.ADMIN_SISTEMA,
    Roles.MESA_PARTES,
]
TRAMITES_EXPORTAR_ROLES = [
    Roles.ADMIN_SISTEMA,
    Roles.MESA_PARTES,
    Roles.ESPECIALISTA_TECNICO,
    Roles.ASESORIA_LEGAL,
]
TRAMITES_DOCUMENTOS_ROLES = [
    Roles.ADMIN_SISTEMA,
    Roles.MESA_PARTES,
    Roles.ESPECIALISTA_TECNICO,
    Roles.ASESORIA_LEGAL,
    Roles.DIRECTOR_GENERAL,
    Roles.DIRECTOR_ADMINISTRATIVO,
]


class TramiteListView(RolRequeridoMixin, ListView):
    """Lista de todos los trámites."""
    model = Tramite
    template_name = 'tramites/tramite_list.html'
    context_object_name = 'tramites'
    paginate_by = 20
    roles_permitidos = TRAMITES_VER_ROLES
    
    def get_queryset(self):
        queryset = Tramite.objects.select_related(
            'empresa', 'autorizacion', 'creado_por'
        ).order_by('-fecha_creacion')
        
        # Filtros de búsqueda
        q = self.request.GET.get('q')
        estado = self.request.GET.get('estado')
        tipo_tramite = self.request.GET.get('tipo_tramite')
        
        if q:
            queryset = queryset.filter(
                Q(numero_expediente__icontains=q) |
                Q(empresa__razon_social__icontains=q) |
                Q(empresa__ruc__icontains=q)
            )
        
        if estado:
            queryset = queryset.filter(estado=estado)
        
        if tipo_tramite:
            queryset = queryset.filter(tipo_tramite=tipo_tramite)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Trámites'
        context['form_busqueda'] = TramiteBusquedaForm(self.request.GET)
        context['total_tramites'] = Tramite.objects.count()
        context['pendientes'] = Tramite.objects.exclude(
            estado__in=[EstadoTramite.APROBADO, EstadoTramite.DENEGADO, EstadoTramite.CERRADO]
        ).count()
        query_params = self.request.GET.copy()
        query_params.pop('page', None)
        # Variables para filtros en template (evitar DEBUG exceptions)
        context['q'] = self.request.GET.get('q', '')
        context['estado'] = self.request.GET.get('estado', '')
        context['tipo_tramite'] = self.request.GET.get('tipo_tramite', '')
        context['query_params'] = query_params.urlencode()
        return context


class MisTramitesView(RolRequeridoMixin, ListView):
    """Lista de trámites creados por el usuario actual."""
    model = Tramite
    template_name = 'tramites/mis_tramites.html'
    context_object_name = 'tramites'
    paginate_by = 20
    roles_permitidos = TRAMITES_VER_ROLES
    
    def get_queryset(self):
        return Tramite.objects.filter(
            creado_por=self.request.user
        ).order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Mis Trámites'
        return context


class TramitesPendientesView(RolRequeridoMixin, ListView):
    """Lista de trámites pendientes según el rol del usuario."""
    model = Tramite
    template_name = 'tramites/tramites_pendientes.html'
    context_object_name = 'tramites'
    paginate_by = 20
    roles_permitidos = TRAMITES_VER_ROLES
    
    def get_queryset(self):
        user = self.request.user
        queryset = Tramite.objects.select_related('empresa').order_by('-fecha_creacion')
        
        # Filtrar según el rol del usuario
        if user.rol == Roles.ESPECIALISTA_TECNICO:
            queryset = queryset.filter(estado=EstadoTramite.EN_EVAL_TECNICA)
        elif user.rol == Roles.ASESORIA_LEGAL:
            # ASESORIA_LEGAL solo ve trámites en EN_REVISION_LEGAL, excluyendo RENOVACION_TUC
            # (RENOVACION_TUC va directo de EN_EVAL_TECNICA a PENDIENTE_FIRMA)
            queryset = queryset.filter(
                estado=EstadoTramite.EN_REVISION_LEGAL
            ).exclude(
                tipo_tramite=TipoTramite.RENOVACION_TUC
            )
        elif user.rol == Roles.DIRECTOR_GENERAL:
            queryset = queryset.filter(
                Q(estado=EstadoTramite.PENDIENTE_FIRMA) & ~Q(tipo_tramite=TipoTramite.RENOVACION_TUC) |
                Q(
                    tipo_tramite=TipoTramite.INCREMENTO_FLOTA,
                    estado=EstadoTramite.EN_DIRECCION_GENERAL
                ) |
                Q(
                    tipo_tramite=TipoTramite.AUTORIZACION_INICIAL,
                    estado=EstadoTramite.EN_DIRECCION_GENERAL
                ) |
                Q(
                    tipo_tramite=TipoTramite.AUTORIZACION_RUTA,
                    estado=EstadoTramite.EN_DIRECCION_GENERAL
                )
            )
        elif user.rol == Roles.DIRECTOR_ADMINISTRATIVO:
            queryset = queryset.filter(
                Q(
                    estado=EstadoTramite.PENDIENTE_FIRMA,
                    tipo_tramite=TipoTramite.HABILITACION_CONDUCTOR
                ) |
                Q(
                    estado=EstadoTramite.EN_DIRECCION_ADMINISTRATIVA,
                    tipo_tramite=TipoTramite.INCREMENTO_FLOTA
                ) |
                Q(
                    estado=EstadoTramite.EN_DIRECCION_ADMINISTRATIVA,
                    tipo_tramite=TipoTramite.AUTORIZACION_INICIAL
                ) |
                Q(
                    estado=EstadoTramite.EN_DIRECCION_ADMINISTRATIVA,
                    tipo_tramite=TipoTramite.AUTORIZACION_RUTA
                ) |
                Q(
                    estado=EstadoTramite.EN_DIRECCION_ADMINISTRATIVA,
                    tipo_tramite=TipoTramite.RENOVACION_TUC
                )
            )
        elif user.rol == Roles.CONTROL_CALIDAD:
            # CONTROL_CALIDAD ve todos los trámites (supervisión general)
            pass
        else:
            # Para otros roles, mostrar todos los pendientes
            queryset = queryset.exclude(
                estado__in=[EstadoTramite.APROBADO, EstadoTramite.DENEGADO, EstadoTramite.CERRADO]
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Trámites Pendientes'
        return context


class TramiteDetailView(RolRequeridoMixin, DetailView):
    """Detalle de un trámite."""
    model = Tramite
    template_name = 'tramites/tramite_detail.html'
    context_object_name = 'tramite'
    roles_permitidos = TRAMITES_VER_ROLES
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tramite = self.object
        context['titulo'] = f'Expediente: {tramite.numero_expediente}'
        context['return_url'] = _get_safe_return_url(self.request, reverse('tramites:lista'))
        context['documentos'] = tramite.documentos.all().order_by('-fecha_subida')
        context['historial'] = HistorialTramite.objects.filter(
            tramite=tramite
        ).select_related('usuario').order_by('-fecha')
        
        # Determinar acciones disponibles según rol y estado
        context['acciones'] = self._get_acciones_disponibles(tramite)
        context['autorizacion_inicial_retorno_legal'] = tramite.retorno_legal_a_direccion_general()
        context['observado_desde_legal'] = tramite.ultima_observacion_desde_legal()
        
        # Agregar datos específicos del trámite si existen
        # Inicializar con estructura vacía para evitar errores en template
        datos_tramite = {
            'autorizacion': None,
            'vehiculo': None,
            'vehiculo_nuevo': None,
            'conductor': None,
            'modificacion': None,
            'baja_vehiculo': None,
            'baja_conductor': None,
        }
        if hasattr(tramite, 'datos') and tramite.datos and tramite.datos.datos_json:
            # Actualizar con datos reales si existen
            datos_tramite.update(tramite.datos.datos_json)
            
            # Corregir visualización de códigos a nombres legibles
            dept_dict = dict(DepartamentosPeru.CHOICES)
            serv_dict = {}
            for tipo in TipoServicio.objects.all():
                serv_dict[tipo.id] = tipo.nombre
                serv_dict[tipo.codigo] = tipo.nombre
                serv_dict[tipo.nombre] = tipo.nombre
            
            # Obtener tipos de vehículo (Carrocería) del modelo de configuración
            tipos_veh = Carroceria.objects.all()
            veh_dict = {t.codigo: t.nombre for t in tipos_veh}
            veh_dict.update({t.nombre: t.nombre for t in tipos_veh})
            veh_dict.update({t.id: t.nombre for t in tipos_veh})
            
            for section in ['autorizacion', 'modificacion', 'renovacion', 'vehiculo']:
                if datos_tramite.get(section):
                    data = datos_tramite[section]
                    if data.get('ambito'):
                        data['ambito_display'] = dept_dict.get(data['ambito'], data['ambito'])
                    if data.get('tipo_servicio'):
                        data['tipo_servicio_display'] = serv_dict.get(data['tipo_servicio'], data['tipo_servicio'])
                    if data.get('carroceria'):
                        data['tipo_vehiculo_display'] = veh_dict.get(data['carroceria'], data['carroceria'])
                    elif data.get('tipo_vehiculo'):
                        data['tipo_vehiculo_display'] = veh_dict.get(data['tipo_vehiculo'], data['tipo_vehiculo'])
        context['datos_tramite'] = datos_tramite
        
        # Recibos de pago
        context['recibos'] = tramite.recibos_pago.all().order_by('-fecha_pago')
        
        # Vehículos del trámite (para incremento, sustitución, baja)
        context['vehiculos_tramite'] = tramite.vehiculos_tramite.all().order_by('id')
        context['puede_gestionar_vehiculos'] = (
            tramite.tipo_tramite != TipoTramite.RENOVACION_TUC
            or self.request.user.is_superuser
            or self.request.user.rol in TRAMITES_VEHICULO_EDIT_ROLES
        )
        
        # Conductores del trámite (para habilitación, baja)
        context['conductores_tramite'] = tramite.conductores_tramite.all().order_by('id')
        
        return context
    
    def _get_acciones_disponibles(self, tramite):
        """Determina qué acciones puede realizar el usuario."""
        user = self.request.user
        acciones = []
        
        if user.rol == Roles.ADMIN_SISTEMA:
            # Admin puede hacer todo
            acciones = ['editar', 'agregar_documento']
            if tramite.estado == EstadoTramite.RECIBIDO:
                acciones.append('enviar_evaluacion')
            elif (
                tramite.tipo_tramite == TipoTramite.BAJA_VEHICULO and
                tramite.estado == EstadoTramite.EN_CONTROL_CALIDAD
            ):
                acciones.extend(['aprobar_evaluacion', 'observar'])
            elif tramite.estado == EstadoTramite.EN_EVAL_TECNICA:
                acciones.extend(['aprobar_evaluacion', 'observar'])
            elif tramite.estado == EstadoTramite.OBSERVADO:
                acciones.append('subsanar')
            elif (
                tramite.tipo_tramite == TipoTramite.RENOVACION_TUC and
                tramite.estado == EstadoTramite.PENDIENTE_FIRMA
            ):
                acciones.extend(['enviar_direccion_administrativa', 'observar'])
            elif (
                tramite.tipo_tramite == TipoTramite.RENOVACION_TUC and
                tramite.estado == EstadoTramite.EN_DIRECCION_ADMINISTRATIVA
            ):
                acciones.append('firmar_derivar_tecnico')
            elif (
                tramite.tipo_tramite in [
                    TipoTramite.AUTORIZACION_INICIAL,
                    TipoTramite.AUTORIZACION_RUTA,
                    TipoTramite.INCREMENTO_FLOTA,
                ] and
                tramite.estado == EstadoTramite.EN_DIRECCION_ADMINISTRATIVA
            ):
                acciones.append('enviar_direccion_general')
            elif (
                tramite.tipo_tramite in [
                    TipoTramite.AUTORIZACION_INICIAL,
                    TipoTramite.AUTORIZACION_RUTA,
                    TipoTramite.INCREMENTO_FLOTA,
                ] and
                tramite.estado == EstadoTramite.EN_DIRECCION_GENERAL
            ):
                if (
                    tramite.tipo_tramite in [
                        TipoTramite.AUTORIZACION_INICIAL,
                        TipoTramite.AUTORIZACION_RUTA,
                    ] and
                    tramite.retorno_legal_a_direccion_general()
                ):
                    acciones.append('aprobar')
                else:
                    acciones.append('enviar_legal')
            elif tramite.estado == EstadoTramite.EN_REVISION_LEGAL:
                acciones.extend(['aprobar_legal', 'observar_legal'])
            elif tramite.estado == EstadoTramite.PENDIENTE_FIRMA:
                acciones.extend(['aprobar', 'denegar'])
            elif tramite.estado == EstadoTramite.APROBADO:
                acciones.append('cerrar')
        
        elif user.rol == Roles.MESA_PARTES:
            acciones = ['agregar_documento']
            if tramite.estado in [EstadoTramite.RECIBIDO, EstadoTramite.OBSERVADO]:
                acciones.append('editar')
            
            if tramite.estado == EstadoTramite.RECIBIDO:
                acciones.append('enviar_evaluacion')
            elif tramite.estado == EstadoTramite.OBSERVADO:
                acciones.append('subsanar')
            elif tramite.estado == EstadoTramite.DENEGADO:
                acciones.append('cerrar')
            elif (
                tramite.estado == EstadoTramite.APROBADO and
                tramite.tipo_tramite not in [
                    TipoTramite.AUTORIZACION_INICIAL,
                    TipoTramite.INCREMENTO_FLOTA,
                    TipoTramite.RENOVACION_TUC,
                ]
            ):
                acciones.append('cerrar')
        
        elif user.rol == Roles.ESPECIALISTA_TECNICO:
            acciones = ['agregar_documento']
            if tramite.estado == EstadoTramite.EN_EVAL_TECNICA:
                acciones.extend(['aprobar_evaluacion', 'observar'])
            elif tramite.estado == EstadoTramite.OBSERVADO:
                acciones.extend(['subsanar', 'editar'])
        
        elif user.rol == Roles.ASESORIA_LEGAL:
            acciones = ['agregar_documento']
            # ASESORIA_LEGAL no puede ver ni actuar sobre RENOVACION_TUC
            if tramite.tipo_tramite != TipoTramite.RENOVACION_TUC:
                if tramite.estado == EstadoTramite.EN_REVISION_LEGAL:
                    acciones.extend(['aprobar_legal', 'observar_legal'])
            elif tramite.estado == EstadoTramite.OBSERVADO:
                acciones.extend(['subsanar', 'editar'])
        
        elif user.rol == Roles.DIRECTOR_GENERAL:
            acciones = ['agregar_documento']
            if (
                tramite.tipo_tramite in [
                    TipoTramite.AUTORIZACION_INICIAL,
                    TipoTramite.AUTORIZACION_RUTA,
                    TipoTramite.INCREMENTO_FLOTA,
                ] and
                tramite.estado == EstadoTramite.EN_DIRECCION_GENERAL
            ):
                if (
                    tramite.tipo_tramite in [
                        TipoTramite.AUTORIZACION_INICIAL,
                        TipoTramite.AUTORIZACION_RUTA,
                    ] and
                    tramite.retorno_legal_a_direccion_general()
                ):
                    acciones.append('aprobar')
                else:
                    acciones.append('enviar_legal')
            elif tramite.estado == EstadoTramite.PENDIENTE_FIRMA:
                acciones.extend(['aprobar', 'denegar'])
            elif (
                tramite.estado == EstadoTramite.APROBADO and
                tramite.tipo_tramite not in [
                    TipoTramite.AUTORIZACION_INICIAL,
                    TipoTramite.INCREMENTO_FLOTA,
                ]
            ):
                acciones.append('cerrar')
        
        elif user.rol == Roles.DIRECTOR_ADMINISTRATIVO:
            acciones = ['agregar_documento']
            if (
                tramite.tipo_tramite in [
                    TipoTramite.AUTORIZACION_INICIAL,
                    TipoTramite.AUTORIZACION_RUTA,
                    TipoTramite.INCREMENTO_FLOTA,
                ] and
                tramite.estado == EstadoTramite.EN_DIRECCION_ADMINISTRATIVA
            ):
                acciones.append('enviar_direccion_general')
            elif (
                tramite.tipo_tramite == TipoTramite.RENOVACION_TUC and
                tramite.estado == EstadoTramite.EN_DIRECCION_ADMINISTRATIVA
            ):
                acciones.append('firmar_derivar_tecnico')
            elif tramite.tipo_tramite == TipoTramite.HABILITACION_CONDUCTOR:
                if tramite.estado == EstadoTramite.PENDIENTE_FIRMA:
                    acciones.extend(['aprobar', 'denegar'])
                elif tramite.estado == EstadoTramite.APROBADO:
                    acciones.append('cerrar')
        
        elif user.rol == Roles.CONTROL_CALIDAD:
            acciones = ['agregar_documento']
            if (
                tramite.tipo_tramite == TipoTramite.BAJA_VEHICULO and
                tramite.estado == EstadoTramite.EN_CONTROL_CALIDAD
            ):
                acciones.extend(['aprobar_evaluacion', 'observar'])
            # Solo puede actuar sobre RENOVACION_TUC
            elif tramite.tipo_tramite == TipoTramite.RENOVACION_TUC:
                if tramite.estado == EstadoTramite.PENDIENTE_FIRMA:
                    acciones.extend(['enviar_direccion_administrativa', 'observar'])
                elif tramite.estado == EstadoTramite.APROBADO:
                    acciones.append('cerrar')
            elif (
                tramite.tipo_tramite in [
                    TipoTramite.AUTORIZACION_INICIAL,
                    TipoTramite.INCREMENTO_FLOTA,
                ] and
                tramite.estado == EstadoTramite.APROBADO
            ):
                acciones.append('cerrar')
        
        return acciones


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def get_valid_id(value):
    """
    Retorna el ID como entero si es válido, None si no lo es.
    Útil para manejar valores de formularios que pueden ser 'None', '', etc.
    """
    if value and value != 'None' and value != '':
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    return None


# ============================================================================
# MAPEO DE FORMULARIOS POR TIPO DE TRÁMITE
# ============================================================================

FORMULARIOS_POR_TIPO = {
    TipoTramite.AUTORIZACION_INICIAL: AutorizacionInicialForm,
    TipoTramite.AUTORIZACION_RUTA: AutorizacionRutaForm,
    TipoTramite.MODIFICACION_AUTORIZACION: ModificacionAutorizacionForm,
    TipoTramite.RENOVACION_AUTORIZACION: RenovacionAutorizacionForm,
    TipoTramite.RENOVACION_TUC: RenovacionTUCForm,
    TipoTramite.BAJA_AUTORIZACION: BajaAutorizacionForm,
    TipoTramite.SUSPENSION_AUTORIZACION: SuspensionAutorizacionForm,
    TipoTramite.INCREMENTO_FLOTA: IncrementoFlotaForm,
    TipoTramite.SUSTITUCION_VEHICULO: SustitucionVehiculoForm,
    TipoTramite.BAJA_VEHICULO: BajaVehiculoForm,
    TipoTramite.HABILITACION_CONDUCTOR: HabilitacionConductorForm,
    TipoTramite.BAJA_CONDUCTOR: BajaConductorForm,
}


class TramiteCreateView(RolRequeridoMixin, View):
    """
    Crear nuevo trámite con formularios dinámicos según el tipo.
    Paso 1: Formulario básico del trámite
    Paso 2: Formulario específico según el tipo de trámite
    """
    template_name = 'tramites/tramite_form.html'
    roles_permitidos = TRAMITES_CREAR_EDITAR_ROLES
    session_key = 'tramites_creacion_borrador'

    def _get_borrador(self, request):
        borrador = request.session.get(self.session_key)
        return borrador if isinstance(borrador, dict) else None

    def _guardar_borrador(self, request, form, return_url):
        cleaned_data = form.cleaned_data
        empresa = cleaned_data.get('empresa')
        autorizacion = cleaned_data.get('autorizacion')
        vehiculo = cleaned_data.get('vehiculo')
        conductor = cleaned_data.get('conductor')

        borrador = {
            'tipo_tramite': cleaned_data.get('tipo_tramite'),
            'empresa': empresa.id if empresa else None,
            'empresa_nombre': empresa.razon_social if empresa else '',
            'autorizacion': autorizacion.id if autorizacion else None,
            'vehiculo': vehiculo.id if vehiculo else None,
            'conductor': conductor.id if conductor else None,
            'descripcion': cleaned_data.get('descripcion_solicitud', ''),
            'expediente_externo': cleaned_data.get('expediente_externo', ''),
            'solicitante_dni': cleaned_data.get('solicitante_dni', ''),
            'solicitante_nombres': cleaned_data.get('solicitante_nombres', ''),
            'solicitante_telefono': cleaned_data.get('solicitante_telefono', ''),
            'solicitante_email': cleaned_data.get('solicitante_email', ''),
            'return_url': return_url,
        }
        request.session[self.session_key] = borrador
        request.session.modified = True
        return borrador

    def _limpiar_borrador(self, request):
        if self.session_key in request.session:
            del request.session[self.session_key]
            request.session.modified = True

    def _get_return_url(self, request, borrador=None):
        default = reverse('tramites:lista')
        next_url = request.GET.get('next') or request.POST.get('next')
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return next_url

        if borrador and borrador.get('return_url'):
            return borrador['return_url']

        referer = request.META.get('HTTP_REFERER')
        if referer and url_has_allowed_host_and_scheme(
            referer,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return referer

        return default

    def _build_initial_from_borrador(self, borrador):
        if not borrador:
            return {}

        return {
            'tipo_tramite': borrador.get('tipo_tramite') or None,
            'empresa': borrador.get('empresa') or None,
            'autorizacion': borrador.get('autorizacion') or None,
            'vehiculo': borrador.get('vehiculo') or None,
            'conductor': borrador.get('conductor') or None,
            'expediente_externo': borrador.get('expediente_externo') or '',
            'descripcion_solicitud': borrador.get('descripcion') or '',
            'solicitante_dni': borrador.get('solicitante_dni') or '',
            'solicitante_nombres': borrador.get('solicitante_nombres') or '',
            'solicitante_telefono': borrador.get('solicitante_telefono') or '',
            'solicitante_email': borrador.get('solicitante_email') or '',
        }

    def _get_entidades_borrador(self, borrador):
        from apps.empresas.models import EmpresaTransporte

        empresa = None
        autorizacion = None
        vehiculo = None
        conductor = None
        errores = []

        empresa_id = get_valid_id(borrador.get('empresa'))
        autorizacion_id = get_valid_id(borrador.get('autorizacion'))
        vehiculo_id = get_valid_id(borrador.get('vehiculo'))
        conductor_id = get_valid_id(borrador.get('conductor'))

        if empresa_id:
            empresa = EmpresaTransporte.objects.filter(id=empresa_id).first()
            if not empresa:
                errores.append('La empresa seleccionada ya no existe o no está disponible.')

        if autorizacion_id:
            autorizacion = Autorizacion.objects.filter(id=autorizacion_id).first()
            if not autorizacion:
                errores.append('La autorización seleccionada ya no existe o no está disponible.')

        if vehiculo_id:
            vehiculo = Vehiculo.objects.filter(id=vehiculo_id).first()
            if not vehiculo:
                errores.append('El vehículo seleccionado ya no existe o no está disponible.')

        if conductor_id:
            conductor = Conductor.objects.filter(id=conductor_id).first()
            if not conductor:
                errores.append('El conductor seleccionado ya no existe o no está disponible.')

        if empresa and autorizacion and autorizacion.empresa_id != empresa.id:
            errores.append('La autorización no pertenece a la empresa seleccionada.')

        if empresa and vehiculo and vehiculo.empresa_propietaria_id != empresa.id:
            errores.append('El vehículo no pertenece a la empresa seleccionada.')

        if empresa and conductor and conductor.empresa_id != empresa.id:
            errores.append('El conductor no pertenece a la empresa seleccionada.')

        return {
            'empresa': empresa,
            'autorizacion': autorizacion,
            'vehiculo': vehiculo,
            'conductor': conductor,
            'errores': errores,
        }

    def _build_form_especifico(self, tipo_tramite, *, data=None, empresa=None, autorizacion=None):
        form_class = FORMULARIOS_POR_TIPO.get(tipo_tramite)
        if not form_class:
            return None

        kwargs = {}
        if data is not None:
            kwargs['data'] = data

        if tipo_tramite == TipoTramite.SUSTITUCION_VEHICULO and empresa:
            kwargs['empresa'] = empresa
        elif tipo_tramite == TipoTramite.MODIFICACION_AUTORIZACION and autorizacion:
            kwargs['autorizacion'] = autorizacion
        elif tipo_tramite == TipoTramite.BAJA_AUTORIZACION and autorizacion:
            kwargs['autorizacion'] = autorizacion
        elif tipo_tramite == TipoTramite.RENOVACION_TUC:
            kwargs['autorizacion'] = autorizacion
            kwargs['empresa'] = empresa

        return form_class(**kwargs)

    def _build_incremento_formsets(self, data=None):
        kwargs = {'prefix': 'vehiculos'}
        if data is not None:
            kwargs['data'] = data
        vehiculo_formset = IncrementoFlotaVehiculoFormSet(**kwargs)

        conductor_kwargs = {
            'prefix': 'conductores',
            'form_kwargs': {'tramite': None},
        }
        if data is not None:
            conductor_kwargs['data'] = data
        conductor_formset = IncrementoFlotaConductorFormSet(**conductor_kwargs)

        return vehiculo_formset, conductor_formset

    def _build_renovacion_tuc_formset(self, data=None, autorizacion=None, empresa=None):
        kwargs = {
            'prefix': 'renovacion_tuc',
            'form_kwargs': {
                'autorizacion': autorizacion,
                'empresa': empresa,
            },
        }
        if data is not None:
            kwargs['data'] = data
        return RenovacionTUCFormSet(**kwargs)

    def _cleaned_formset_data(self, formset):
        return [
            form.cleaned_data
            for form in formset.forms
            if form.cleaned_data and not form.cleaned_data.get('DELETE')
        ]

    def _serializar_valor_json(self, value):
        if value is None:
            return None
        if isinstance(value, Decimal):
            return float(value)
        if hasattr(value, 'isoformat'):
            return value.isoformat()
        if hasattr(value, 'pk'):
            return value.pk
        if hasattr(value, '__iter__') and not isinstance(value, str):
            return [item.pk if hasattr(item, 'pk') else item for item in value]
        return value

    def _serializar_cleaned_data(self, cleaned_data):
        return {
            key: self._serializar_valor_json(value)
            for key, value in cleaned_data.items()
            if key != 'DELETE'
        }

    def _preparar_datos_incremento_formsets(self, vehiculos_data, conductores_data):
        vehiculos = [self._serializar_cleaned_data(data) for data in vehiculos_data]
        conductores = [self._serializar_cleaned_data(data) for data in conductores_data]
        return {
            'vehiculos': vehiculos,
            'conductores': conductores,
            'vehiculo': vehiculos[0] if vehiculos else {},
        }

    def _preparar_datos_renovacion_tuc_formset(self, vehiculos_data):
        vehiculos = []
        for data in vehiculos_data:
            serializado = self._serializar_cleaned_data(data)
            vehiculo = data.get('vehiculo')
            if vehiculo:
                serializado.update({
                    'vehiculo_id': vehiculo.pk,
                    'placa': vehiculo.placa,
                    'marca': vehiculo.marca,
                    'modelo': vehiculo.modelo,
                })
            vehiculos.append(serializado)

        return {
            'renovacion_tuc': {
                'vehiculos': vehiculos,
                'vehiculo': vehiculos[0] if vehiculos else {},
            }
        }

    def _build_datos_basicos(self, borrador, empresa=None):
        return {
            'empresa': borrador.get('empresa'),
            'empresa_nombre': empresa.razon_social if empresa else borrador.get('empresa_nombre'),
            'autorizacion': borrador.get('autorizacion'),
            'vehiculo': borrador.get('vehiculo'),
            'conductor': borrador.get('conductor'),
            'descripcion': borrador.get('descripcion'),
            'expediente_externo': borrador.get('expediente_externo'),
            'solicitante_dni': borrador.get('solicitante_dni'),
            'solicitante_nombres': borrador.get('solicitante_nombres'),
            'solicitante_telefono': borrador.get('solicitante_telefono'),
            'solicitante_email': borrador.get('solicitante_email'),
        }
    
    def get(self, request, *args, **kwargs):
        paso = request.GET.get('paso', '1')
        borrador = self._get_borrador(request)
        tipo_tramite = borrador.get('tipo_tramite') if borrador else None

        context = {
            'titulo': 'Nuevo Trámite',
            'accion': 'Crear',
            'paso': paso,
            'return_url': self._get_return_url(request, borrador),
        }

        if paso == '1' or not tipo_tramite:
            context['form'] = TramiteForm(initial=self._build_initial_from_borrador(borrador))
            context['paso'] = '1'
        else:
            # Paso 2: Formulario específico
            form_class = FORMULARIOS_POR_TIPO.get(tipo_tramite)
            entidades = self._get_entidades_borrador(borrador)
            empresa = entidades['empresa']
            autorizacion = entidades['autorizacion']
            empresa_id = borrador.get('empresa')
            
            if form_class:
                if tipo_tramite in [TipoTramite.AUTORIZACION_INICIAL, TipoTramite.INCREMENTO_FLOTA]:
                    context['form_especifico'] = form_class()
                    (
                        context['incremento_vehiculo_formset'],
                        context['incremento_conductor_formset'],
                    ) = self._build_incremento_formsets()
                elif tipo_tramite == TipoTramite.RENOVACION_TUC:
                    context['form_especifico'] = form_class(
                        autorizacion=autorizacion,
                        empresa=empresa,
                    )
                    context['renovacion_tuc_formset'] = self._build_renovacion_tuc_formset(
                        autorizacion=autorizacion,
                        empresa=empresa,
                    )
                    context['autorizacion'] = autorizacion
                    context['empresa'] = autorizacion.empresa if autorizacion else empresa
                elif tipo_tramite == TipoTramite.SUSTITUCION_VEHICULO and empresa_id:
                    context['form_especifico'] = form_class(empresa=empresa)
                elif tipo_tramite in [TipoTramite.BAJA_AUTORIZACION, TipoTramite.MODIFICACION_AUTORIZACION]:
                    context['form_especifico'] = form_class()
                    # Pasar la autorización y empresa al contexto para que el template pueda acceder a los datos
                    context['autorizacion'] = autorizacion
                    context['empresa'] = autorizacion.empresa if autorizacion else None
                elif tipo_tramite == TipoTramite.HABILITACION_CONDUCTOR and empresa_id:
                    context['form_especifico'] = form_class()
                else:
                    context['form_especifico'] = form_class()
                    
            context['tipo_tramite'] = tipo_tramite
            context['tipo_tramite_display'] = dict(TipoTramite.CHOICES).get(tipo_tramite, tipo_tramite)
            context['datos_basicos'] = self._build_datos_basicos(borrador, empresa=empresa)
            
            # Obtener el número de resolución de la autorización si existe
            if context['datos_basicos']['autorizacion']:
                try:
                    autorizacion = Autorizacion.objects.get(pk=context['datos_basicos']['autorizacion'])
                    context['datos_basicos']['autorizacion_numero_resolucion'] = autorizacion.numero_resolucion
                except Autorizacion.DoesNotExist:
                    pass
            
            context['paso'] = '2'
            # URL para volver al Paso 1 conservando datos
            params = {k: v for k, v in context['datos_basicos'].items() if v}
            next_param = request.GET.get('next')
            if next_param and url_has_allowed_host_and_scheme(
                next_param,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                params['next'] = next_param
            if params:
                params['paso'] = '1'
                context['volver_paso1_url'] = f"{reverse('tramites:crear')}?{urlencode(params)}"
            else:
                context['volver_paso1_url'] = reverse('tramites:crear')
        
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        paso = request.POST.get('paso', '1')
        
        if paso == '1':
            form = TramiteForm(request.POST)
            if form.is_valid():
                tipo_tramite = form.cleaned_data['tipo_tramite']
                self._guardar_borrador(
                    request,
                    form,
                    self._get_return_url(request),
                )

                if tipo_tramite in FORMULARIOS_POR_TIPO:
                    return redirect(f"{reverse('tramites:crear')}?paso=2")

                self._limpiar_borrador(request)
                return self._crear_tramite_simple(request, form)

            context = {
                'titulo': 'Nuevo Trámite',
                'accion': 'Crear',
                'form': form,
                'paso': '1',
                'return_url': self._get_return_url(request, self._get_borrador(request)),
            }
            return render(request, self.template_name, context)

        if paso == '2':
            return self._crear_tramite_completo(request)

        messages.error(request, 'Paso de formulario no válido.')
        return redirect('tramites:crear')
    
    def _crear_tramite_simple(self, request, form):
        """Crear trámite sin datos específicos adicionales."""
        with transaction.atomic():
            tramite = form.save(commit=False)
            tramite.creado_por = request.user
            tramite.save()
            
            messages.success(request, f'Trámite {tramite.numero_expediente} creado exitosamente.')
            return redirect('tramites:detalle', pk=tramite.pk)
    
    def _crear_tramite_completo(self, request):
        """Crear trámite con datos específicos según el tipo."""
        borrador = self._get_borrador(request)
        if not borrador:
            messages.error(request, 'La sesión del formulario expiró. Complete nuevamente el paso 1.')
            return redirect('tramites:crear')

        tipo_tramite = borrador.get('tipo_tramite')
        form_class = FORMULARIOS_POR_TIPO.get(tipo_tramite)
        
        if not form_class:
            self._limpiar_borrador(request)
            messages.error(request, 'Tipo de trámite no válido.')
            return redirect('tramites:crear')
        
        entidades = self._get_entidades_borrador(borrador)
        if entidades['errores']:
            self._limpiar_borrador(request)
            for error in entidades['errores']:
                messages.error(request, error)
            messages.warning(request, 'Se reinició el formulario porque los datos básicos ya no eran válidos.')
            return redirect('tramites:crear')

        empresa = entidades['empresa']
        autorizacion = entidades['autorizacion']
        vehiculo = entidades['vehiculo']
        conductor = entidades['conductor']
        form_especifico = self._build_form_especifico(
            tipo_tramite,
            data=request.POST,
            empresa=empresa,
            autorizacion=autorizacion,
        )

        incremento_vehiculo_formset = None
        incremento_conductor_formset = None
        incremento_vehiculos_data = []
        incremento_conductores_data = []
        renovacion_tuc_formset = None
        renovacion_tuc_vehiculos_data = []

        if tipo_tramite in [TipoTramite.AUTORIZACION_INICIAL, TipoTramite.INCREMENTO_FLOTA]:
            (
                incremento_vehiculo_formset,
                incremento_conductor_formset,
            ) = self._build_incremento_formsets(data=request.POST)

            form_especifico_valido = (
                True if tipo_tramite == TipoTramite.INCREMENTO_FLOTA else form_especifico.is_valid()
            )
            vehiculo_formset_valido = incremento_vehiculo_formset.is_valid()
            conductor_formset_valido = incremento_conductor_formset.is_valid()

            if (
                not form_especifico_valido or
                not vehiculo_formset_valido or
                not conductor_formset_valido
            ):
                datos_basicos_dict = self._build_datos_basicos(borrador, empresa=empresa)
                if autorizacion:
                    datos_basicos_dict['autorizacion_numero_resolucion'] = autorizacion.numero_resolucion

                context = {
                    'titulo': 'Nuevo Trámite',
                    'accion': 'Crear',
                    'form_especifico': form_especifico if tipo_tramite == TipoTramite.AUTORIZACION_INICIAL else FORMULARIOS_POR_TIPO[tipo_tramite](),
                    'incremento_vehiculo_formset': incremento_vehiculo_formset,
                    'incremento_conductor_formset': incremento_conductor_formset,
                    'tipo_tramite': tipo_tramite,
                    'tipo_tramite_display': dict(TipoTramite.CHOICES).get(tipo_tramite, tipo_tramite),
                    'datos_basicos': datos_basicos_dict,
                    'paso': '2',
                    'return_url': self._get_return_url(request, borrador),
                    'volver_paso1_url': reverse('tramites:crear'),
                }
                return render(request, self.template_name, context)

            incremento_vehiculos_data = self._cleaned_formset_data(incremento_vehiculo_formset)
            incremento_conductores_data = self._cleaned_formset_data(incremento_conductor_formset)
            if tipo_tramite == TipoTramite.INCREMENTO_FLOTA:
                form_especifico = FORMULARIOS_POR_TIPO[tipo_tramite]()
        elif tipo_tramite == TipoTramite.RENOVACION_TUC:
            renovacion_tuc_formset = self._build_renovacion_tuc_formset(
                data=request.POST,
                autorizacion=autorizacion,
                empresa=empresa,
            )

            if not renovacion_tuc_formset.is_valid():
                datos_basicos_dict = self._build_datos_basicos(borrador, empresa=empresa)
                if autorizacion:
                    datos_basicos_dict['autorizacion_numero_resolucion'] = autorizacion.numero_resolucion

                context = {
                    'titulo': 'Nuevo Trámite',
                    'accion': 'Crear',
                    'form_especifico': self._build_form_especifico(
                        tipo_tramite,
                        empresa=empresa,
                        autorizacion=autorizacion,
                    ),
                    'renovacion_tuc_formset': renovacion_tuc_formset,
                    'tipo_tramite': tipo_tramite,
                    'tipo_tramite_display': dict(TipoTramite.CHOICES).get(tipo_tramite, tipo_tramite),
                    'datos_basicos': datos_basicos_dict,
                    'autorizacion': autorizacion,
                    'empresa': empresa,
                    'paso': '2',
                    'return_url': self._get_return_url(request, borrador),
                    'volver_paso1_url': reverse('tramites:crear'),
                }
                return render(request, self.template_name, context)

            renovacion_tuc_vehiculos_data = self._cleaned_formset_data(renovacion_tuc_formset)
            form_especifico = FORMULARIOS_POR_TIPO[tipo_tramite](
                autorizacion=autorizacion,
                empresa=empresa,
            )
        
        if tipo_tramite not in [
            TipoTramite.AUTORIZACION_INICIAL,
            TipoTramite.INCREMENTO_FLOTA,
            TipoTramite.RENOVACION_TUC,
        ] and not form_especifico.is_valid():
            datos_basicos_dict = {
                'empresa': request.POST.get('empresa_id', ''),
                'empresa_nombre': request.POST.get('empresa_nombre', ''),
                'autorizacion': request.POST.get('autorizacion_id', ''),
                'vehiculo': request.POST.get('vehiculo_id', ''),
                'conductor': request.POST.get('conductor_id', ''),
                'descripcion': request.POST.get('descripcion', ''),
                'expediente_externo': request.POST.get('expediente_externo', ''),
                # Datos del solicitante
                'solicitante_dni': request.POST.get('solicitante_dni', ''),
                'solicitante_nombres': request.POST.get('solicitante_nombres', ''),
                'solicitante_telefono': request.POST.get('solicitante_telefono', ''),
                'solicitante_email': request.POST.get('solicitante_email', ''),
            }
            
            # Obtener el número de resolución de la autorización si existe
            if datos_basicos_dict['autorizacion']:
                try:
                    autorizacion = Autorizacion.objects.get(pk=datos_basicos_dict['autorizacion'])
                    datos_basicos_dict['autorizacion_numero_resolucion'] = autorizacion.numero_resolucion
                except Autorizacion.DoesNotExist:
                    pass
            
            context = {
                'titulo': 'Nuevo Trámite',
                'accion': 'Crear',
                'form_especifico': form_especifico,
                'tipo_tramite': tipo_tramite,
                'tipo_tramite_display': dict(TipoTramite.CHOICES).get(tipo_tramite, tipo_tramite),
                'datos_basicos': datos_basicos_dict,
                'paso': '2',
                'return_url': self._get_return_url(request, borrador),
                'volver_paso1_url': reverse('tramites:crear'),
            }
            return render(request, self.template_name, context)
        
        # Crear el trámite con todos los datos
        with transaction.atomic():
            # Crear el trámite
            tramite = Tramite.objects.create(
                tipo_tramite=tipo_tramite,
                empresa=empresa,
                autorizacion=autorizacion,
                vehiculo=vehiculo,
                conductor=conductor,
                descripcion_solicitud=borrador.get('descripcion', ''),
                expediente_externo=borrador.get('expediente_externo', ''),
                # Datos del solicitante
                solicitante_dni=borrador.get('solicitante_dni', ''),
                solicitante_nombres=borrador.get('solicitante_nombres', ''),
                solicitante_telefono=borrador.get('solicitante_telefono', ''),
                solicitante_email=borrador.get('solicitante_email', ''),
                creado_por=request.user,
            )
            
            # Si hay vehículo seleccionado y es trámite de vehículos, crear VehiculoTramite
            if vehiculo and tipo_tramite in [TipoTramite.SUSTITUCION_VEHICULO, TipoTramite.BAJA_VEHICULO]:
                VehiculoTramite.objects.create(
                    tramite=tramite,
                    vehiculo_existente=vehiculo,
                    placa_nueva=vehiculo.placa,
                    marca=vehiculo.marca,
                    modelo=vehiculo.modelo,
                    anio_fabricacion=vehiculo.anio_fabricacion,
                    capacidad_pasajeros=vehiculo.capacidad_sentados,
                    carroceria=vehiculo.carroceria,
                    observaciones=f'Vehículo seleccionado al crear trámite de {tramite.get_tipo_tramite_display()}'
                )
            
            # Si hay conductor seleccionado y es trámite de conductores, crear ConductorTramite
            if conductor and tipo_tramite == TipoTramite.BAJA_CONDUCTOR:
                ConductorTramite.objects.create(
                    tramite=tramite,
                    conductor_existente=conductor,
                    dni=conductor.dni,
                    nombres=conductor.nombres,
                    apellido_paterno=conductor.apellido_paterno,
                    apellido_materno=conductor.apellido_materno,
                    licencia_numero=conductor.licencia_numero,
                    licencia_categoria=conductor.licencia_categoria,
                    observaciones=f'Conductor seleccionado al crear trámite de {tramite.get_tipo_tramite_display()}'
                )
            
            # Preparar datos específicos para guardar
            if tipo_tramite == TipoTramite.AUTORIZACION_INICIAL:
                datos_json = self._preparar_datos_json(tipo_tramite, form_especifico.cleaned_data)
                datos_json.update(
                    self._preparar_datos_incremento_formsets(
                        incremento_vehiculos_data,
                        incremento_conductores_data,
                    )
                )
            elif tipo_tramite == TipoTramite.INCREMENTO_FLOTA:
                datos_json = self._preparar_datos_incremento_formsets(
                    incremento_vehiculos_data,
                    incremento_conductores_data,
                )
            elif tipo_tramite == TipoTramite.RENOVACION_TUC:
                datos_json = self._preparar_datos_renovacion_tuc_formset(
                    renovacion_tuc_vehiculos_data,
                )
            else:
                datos_json = self._preparar_datos_json(tipo_tramite, form_especifico.cleaned_data)
            
            # Guardar los datos específicos del trámite
            DatosTramite.objects.create(
                tramite=tramite,
                datos_json=datos_json
            )
            
            # Para autorizacion inicial e incremento de flota, crear flota/conductores del tramite
            if tipo_tramite in [TipoTramite.AUTORIZACION_INICIAL, TipoTramite.INCREMENTO_FLOTA]:
                observacion_vehiculo = (
                    'Vehiculo registrado desde formulario de autorizacion inicial'
                    if tipo_tramite == TipoTramite.AUTORIZACION_INICIAL
                    else 'Vehículo registrado desde formulario de incremento de flota'
                )
                observacion_conductor = (
                    'Conductor registrado desde formulario de autorizacion inicial'
                    if tipo_tramite == TipoTramite.AUTORIZACION_INICIAL
                    else 'Conductor registrado desde formulario de incremento de flota'
                )
                for cleaned in incremento_vehiculos_data:
                    VehiculoTramite.objects.create(
                        tramite=tramite,
                        placa_nueva=cleaned.get('placa', ''),
                        marca=cleaned.get('marca', ''),
                        modelo=cleaned.get('modelo', ''),
                        anio_fabricacion=cleaned.get('anio_fabricacion'),
                        capacidad_pasajeros=cleaned.get('capacidad_sentados'),
                        peso_bruto=cleaned.get('peso_bruto'),
                        categoria=cleaned.get('categoria'),
                        carroceria=cleaned.get('carroceria'),
                        fecha_venc_soat=cleaned.get('fecha_venc_soat'),
                        observaciones=observacion_vehiculo
                    )

                for cleaned in incremento_conductores_data:
                    ConductorTramite.objects.create(
                        tramite=tramite,
                        dni=cleaned.get('dni', ''),
                        nombres=cleaned.get('nombres', ''),
                        apellido_paterno=cleaned.get('apellido_paterno', ''),
                        apellido_materno=cleaned.get('apellido_materno', ''),
                        fecha_nacimiento=cleaned.get('fecha_nacimiento'),
                        licencia_numero=cleaned.get('licencia_numero', ''),
                        licencia_categoria=cleaned.get('licencia_categoria', ''),
                        licencia_fecha_emision=cleaned.get('licencia_fecha_emision'),
                        licencia_fecha_vencimiento=cleaned.get('licencia_fecha_vencimiento'),
                        observaciones=observacion_conductor
                    )

            # Para renovacion TUC, crear VehiculoTramite por cada vehiculo seleccionado
            if tipo_tramite == TipoTramite.RENOVACION_TUC:
                for cleaned in renovacion_tuc_vehiculos_data:
                    vehiculo_sel = cleaned.get('vehiculo')
                    if not vehiculo_sel:
                        continue

                    habilitaciones = HabilitacionVehicular.objects.filter(
                        vehiculo=vehiculo_sel,
                        estado=EstadoHabilitacion.VIGENTE,
                    )
                    if autorizacion:
                        habilitaciones = habilitaciones.filter(autorizacion=autorizacion)
                    habilitacion = (
                        habilitaciones
                        .order_by('-fecha_inicio', '-id')
                        .first()
                    )

                    VehiculoTramite.objects.create(
                        tramite=tramite,
                        vehiculo_existente=vehiculo_sel,
                        placa_nueva=vehiculo_sel.placa,
                        marca=vehiculo_sel.marca,
                        modelo=vehiculo_sel.modelo,
                        anio_fabricacion=vehiculo_sel.anio_fabricacion,
                        color=vehiculo_sel.color,
                        numero_serie=vehiculo_sel.numero_serie,
                        numero_motor=vehiculo_sel.numero_motor,
                        capacidad_pasajeros=vehiculo_sel.capacidad_sentados,
                        categoria=vehiculo_sel.categoria,
                        carroceria=vehiculo_sel.carroceria,
                        numero_tarjeta_propiedad=vehiculo_sel.numero_tiv,
                        fecha_venc_soat=vehiculo_sel.fecha_venc_soat,
                        fecha_venc_citv=vehiculo_sel.fecha_venc_citv,
                        numero_tuc=cleaned.get('numero_tuc') or (habilitacion.numero_tuc if habilitacion else ''),
                        fecha_expedicion_tuc=(
                            cleaned.get('fecha_expedicion_tuc') or
                            (habilitacion.fecha_expedicion_tuc if habilitacion else None)
                        ),
                        fecha_autorizacion_transportista=(
                            habilitacion.fecha_autorizacion_transportista if habilitacion else None
                        ),
                        fecha_expiracion_transportista=(
                            habilitacion.fecha_expiracion_transportista if habilitacion else None
                        ),
                        observaciones='Vehiculo seleccionado para renovacion de TUC'
                    )
            
            # Para habilitación de conductor, crear ConductorTramite con datos del formulario específico
            if tipo_tramite == TipoTramite.HABILITACION_CONDUCTOR:
                cleaned = form_especifico.cleaned_data
                usar_existente = cleaned.get('usar_conductor_existente')
                conductor_existente = cleaned.get('conductor_existente')

                if usar_existente and conductor_existente:
                    ConductorTramite.objects.create(
                        tramite=tramite,
                        conductor_existente=conductor_existente,
                        dni=conductor_existente.dni,
                        nombres=conductor_existente.nombres,
                        apellido_paterno=conductor_existente.apellido_paterno,
                        apellido_materno=conductor_existente.apellido_materno,
                        fecha_nacimiento=conductor_existente.fecha_nacimiento,
                        direccion=conductor_existente.direccion,
                        telefono=conductor_existente.telefono,
                        email=conductor_existente.email,
                        licencia_numero=conductor_existente.licencia_numero,
                        licencia_categoria=conductor_existente.licencia_categoria,
                        licencia_fecha_emision=conductor_existente.licencia_fecha_emision,
                        licencia_fecha_vencimiento=conductor_existente.licencia_fecha_vencimiento,
                        observaciones='Conductor existente seleccionado en habilitación'
                    )
                else:
                    ConductorTramite.objects.create(
                        tramite=tramite,
                        dni=cleaned.get('dni', ''),
                        nombres=cleaned.get('nombres', ''),
                        apellido_paterno=cleaned.get('apellido_paterno', ''),
                        apellido_materno=cleaned.get('apellido_materno', ''),
                        fecha_nacimiento=cleaned.get('fecha_nacimiento'),
                        direccion=cleaned.get('direccion', ''),
                        telefono=cleaned.get('telefono', ''),
                        email=cleaned.get('email', ''),
                        licencia_numero=cleaned.get('licencia_numero', ''),
                        licencia_categoria=cleaned.get('licencia_categoria', ''),
                        licencia_fecha_emision=cleaned.get('licencia_fecha_emision'),
                        licencia_fecha_vencimiento=cleaned.get('licencia_fecha_vencimiento'),
                        observaciones='Conductor registrado desde formulario de habilitación'
                    )

            self._limpiar_borrador(request)
            
            messages.success(
                request, 
                f'Trámite {tramite.numero_expediente} creado exitosamente. '
                f'Los datos serán procesados al aprobar el trámite.'
            )
            return redirect('tramites:detalle', pk=tramite.pk)
    
    def _preparar_datos_json(self, tipo_tramite, cleaned_data):
        """Prepara los datos del formulario para guardar como JSON."""
        datos = {}
        
        # Convertir fechas a string para JSON
        for key, value in cleaned_data.items():
            if value is None:
                # Manejar valores None
                datos[key] = None
            elif isinstance(value, Decimal):
                # Convertir Decimal a float para JSON serialization
                datos[key] = float(value)
            elif hasattr(value, 'isoformat'):  # Es una fecha
                datos[key] = value.isoformat()
            elif hasattr(value, 'pk'):  # Es un modelo
                datos[key] = value.pk
            elif hasattr(value, '__iter__') and not isinstance(value, str):
                # Es una lista (ej: rutas, frecuencias)
                datos[key] = [item.pk if hasattr(item, 'pk') else item for item in value]
            else:
                datos[key] = value

        # Organizar por tipo de trámite
        if tipo_tramite in [TipoTramite.AUTORIZACION_INICIAL, TipoTramite.AUTORIZACION_RUTA]:
            return {'autorizacion': datos}
        elif tipo_tramite == TipoTramite.MODIFICACION_AUTORIZACION:
            return {'modificacion': datos}
        elif tipo_tramite == TipoTramite.RENOVACION_AUTORIZACION:
            return {'renovacion': datos}
        elif tipo_tramite == TipoTramite.RENOVACION_TUC:
            return {'renovacion_tuc': datos}
        elif tipo_tramite == TipoTramite.BAJA_AUTORIZACION:
            return {'baja': datos}
        elif tipo_tramite == TipoTramite.SUSPENSION_AUTORIZACION:
            return {'suspension': datos}
        elif tipo_tramite in [TipoTramite.INCREMENTO_FLOTA, TipoTramite.SUSTITUCION_VEHICULO]:
            return {'vehiculo': datos}
        elif tipo_tramite == TipoTramite.HABILITACION_CONDUCTOR:
            # Si se eligió conductor existente, completar datos para visualización
            if cleaned_data.get('usar_conductor_existente') and cleaned_data.get('conductor_existente'):
                conductor = cleaned_data.get('conductor_existente')
                datos.update({
                    'dni': conductor.dni,
                    'nombres': conductor.nombres,
                    'apellido_paterno': conductor.apellido_paterno,
                    'apellido_materno': conductor.apellido_materno,
                    'fecha_nacimiento': conductor.fecha_nacimiento.isoformat() if conductor.fecha_nacimiento else None,
                    'direccion': conductor.direccion,
                    'telefono': conductor.telefono,
                    'email': conductor.email,
                    'licencia_numero': conductor.licencia_numero,
                    'licencia_categoria': conductor.licencia_categoria,
                    'licencia_fecha_emision': conductor.licencia_fecha_emision.isoformat() if conductor.licencia_fecha_emision else None,
                    'licencia_fecha_vencimiento': conductor.licencia_fecha_vencimiento.isoformat() if conductor.licencia_fecha_vencimiento else None,
                })
            return {'conductor': datos}
        elif tipo_tramite == TipoTramite.BAJA_VEHICULO:
            return {'baja_vehiculo': datos}
        elif tipo_tramite == TipoTramite.BAJA_CONDUCTOR:
            return {'baja_conductor': datos}
        
        return datos


class TramiteUpdateView(RolRequeridoMixin, UpdateView):
    """Editar trámite."""
    model = Tramite
    form_class = TramiteEditForm
    template_name = 'tramites/tramite_form.html'
    roles_permitidos = TRAMITES_CREAR_EDITAR_ROLES
    
    def get_success_url(self):
        return reverse('tramites:detalle', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar: {self.object.numero_expediente}'
        context['accion'] = 'Actualizar'
        context['return_url'] = _get_safe_return_url(
            self.request,
            reverse('tramites:detalle', kwargs={'pk': self.object.pk}),
        )
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Trámite actualizado.')
        return super().form_valid(form)


# Vistas de transición de estado
class TransicionBaseView(RolRequeridoMixin, FormView):
    """Vista base para transiciones de estado."""
    template_name = 'tramites/transicion_form.html'
    form_class = TransicionForm
    
    def get_tramite(self):
        return get_object_or_404(Tramite, pk=self.kwargs['pk'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tramite = self.get_tramite()
        context['tramite'] = tramite
        context['tipo_tramite'] = tramite.tipo_tramite  # Pasar el tipo de trámite
        return context
    
    def get_success_url(self):
        return reverse('tramites:detalle', kwargs={'pk': self.kwargs['pk']})


class EnviarEvaluacionView(TransicionBaseView):
    """Enviar trámite a evaluación técnica."""
    roles_permitidos = [Roles.ADMIN_SISTEMA, Roles.MESA_PARTES]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tramite = self.get_tramite()
        if tramite.tipo_tramite in [TipoTramite.RENOVACION_TUC, TipoTramite.BAJA_VEHICULO]:
            context['titulo'] = 'Enviar a Control de Calidad'
        else:
            context['titulo'] = 'Enviar a Evaluación Técnica'
        context['accion'] = 'Enviar'
        return context
    
    def form_valid(self, form):
        tramite = self.get_tramite()
        try:
            if tramite.tipo_tramite == TipoTramite.BAJA_VEHICULO:
                tramite.enviar_a_control_calidad_baja_vehiculo(usuario=self.request.user)
                tramite.save()
                messages.success(self.request, 'Trámite enviado a Control de Calidad.')
            elif tramite.tipo_tramite == TipoTramite.RENOVACION_TUC:
                tramite.enviar_a_control_calidad_renovacion_tuc(usuario=self.request.user)
                tramite.save()
                messages.success(self.request, 'Trámite enviado a Control de Calidad.')
            else:
                tramite.enviar_a_evaluacion_tecnica(usuario=self.request.user)
                tramite.save()
                messages.success(self.request, 'Trámite enviado a evaluación técnica.')
        except Exception as e:
            messages.error(self.request, f'Error: {str(e)}')
        return HttpResponseRedirect(self.get_success_url())


class EnviarDireccionAdministrativaView(TransicionBaseView):
    """Derivar Renovacion de TUC a Direccion Administrativa."""
    roles_permitidos = [Roles.ADMIN_SISTEMA, Roles.CONTROL_CALIDAD]

    def dispatch(self, request, *args, **kwargs):
        tramite = self.get_tramite()
        if tramite.tipo_tramite != TipoTramite.RENOVACION_TUC:
            messages.error(request, 'Esta acción solo aplica al trámite Renovación de TUC.')
            return redirect('tramites:detalle', pk=tramite.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Derivar a Dirección Administrativa'
        context['accion'] = 'Derivar'
        return context

    def form_valid(self, form):
        tramite = self.get_tramite()
        try:
            comentario = form.cleaned_data.get('comentario', '').strip()
            tramite.enviar_a_direccion_administrativa_renovacion_tuc(
                observaciones=comentario,
                usuario=self.request.user
            )
            tramite.save()
            messages.success(self.request, 'Trámite derivado a Dirección Administrativa.')
        except Exception as e:
            messages.error(self.request, f'Error: {str(e)}')
        return HttpResponseRedirect(self.get_success_url())


class FirmarDerivarTecnicoView(TransicionBaseView):
    """Firma de Director Administrativo y derivacion a Especialista Tecnico."""
    roles_permitidos = [Roles.ADMIN_SISTEMA, Roles.DIRECTOR_ADMINISTRATIVO]

    def dispatch(self, request, *args, **kwargs):
        tramite = self.get_tramite()
        if tramite.tipo_tramite != TipoTramite.RENOVACION_TUC:
            messages.error(request, 'Esta acción solo aplica al trámite Renovación de TUC.')
            return redirect('tramites:detalle', pk=tramite.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Firmar y Derivar a Especialista Técnico'
        context['accion'] = 'Firmar y Derivar'
        return context

    def form_valid(self, form):
        tramite = self.get_tramite()
        try:
            comentario = form.cleaned_data.get('comentario', '').strip()
            tramite.firmar_y_derivar_a_tecnico_renovacion_tuc(
                observaciones=comentario,
                usuario=self.request.user
            )
            tramite.save()
            messages.success(self.request, 'Trámite firmado y derivado a Especialista Técnico.')
        except Exception as e:
            messages.error(self.request, f'Error: {str(e)}')
        return HttpResponseRedirect(self.get_success_url())


class AprobarEvaluacionView(TransicionBaseView):
    """Aprobar evaluación técnica."""
    roles_permitidos = [Roles.ADMIN_SISTEMA, Roles.ESPECIALISTA_TECNICO, Roles.CONTROL_CALIDAD]

    def dispatch(self, request, *args, **kwargs):
        tramite = self.get_tramite()
        if request.user.rol == Roles.CONTROL_CALIDAD and not (
            tramite.tipo_tramite == TipoTramite.BAJA_VEHICULO and
            tramite.estado == EstadoTramite.EN_CONTROL_CALIDAD
        ):
            messages.error(request, 'Control de Calidad solo puede derivar trámites de Baja Vehicular en su etapa de revisión.')
            return redirect('tramites:detalle', pk=tramite.pk)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tramite = self.get_tramite()
        if (
            tramite.tipo_tramite == TipoTramite.BAJA_VEHICULO and
            tramite.estado == EstadoTramite.EN_CONTROL_CALIDAD
        ):
            context['titulo'] = 'Derivar a Evaluación Técnica'
        # Para RENOVACION_TUC, el especialista deriva a Control de Calidad
        elif tramite.tipo_tramite == TipoTramite.RENOVACION_TUC:
            context['titulo'] = 'Derivar a Control de Calidad'
        elif tramite.tipo_tramite in [
            TipoTramite.AUTORIZACION_INICIAL,
            TipoTramite.AUTORIZACION_RUTA,
            TipoTramite.INCREMENTO_FLOTA,
        ]:
            context['titulo'] = 'Derivar a Dirección Administrativa'
        else:
            context['titulo'] = 'Aprobar Evaluación Técnica'
        context['accion'] = 'Derivar' if tramite.tipo_tramite in [
            TipoTramite.AUTORIZACION_INICIAL,
            TipoTramite.AUTORIZACION_RUTA,
            TipoTramite.INCREMENTO_FLOTA,
            TipoTramite.RENOVACION_TUC,
        ] or (
            tramite.tipo_tramite == TipoTramite.BAJA_VEHICULO and
            tramite.estado == EstadoTramite.EN_CONTROL_CALIDAD
        ) else 'Aprobar'
        return context
    
    def form_valid(self, form):
        tramite = self.get_tramite()
        try:
            comentario = form.cleaned_data.get('comentario', '').strip()
            if tramite.estado == EstadoTramite.EN_REVISION_LEGAL:
                messages.info(self.request, 'El trámite ya fue enviado a revisión legal.')
                return HttpResponseRedirect(self.get_success_url())
            
            if (
                tramite.tipo_tramite == TipoTramite.BAJA_VEHICULO and
                tramite.estado == EstadoTramite.EN_CONTROL_CALIDAD
            ):
                tramite.derivar_baja_vehiculo_a_evaluacion_tecnica(
                    observaciones=comentario,
                    usuario=self.request.user
                )
                tramite.save()
                messages.success(self.request, 'Trámite derivado a Evaluación Técnica.')
            # Para RENOVACION_TUC, derivar a Control de Calidad para renovar/cerrar TUC
            elif tramite.tipo_tramite == TipoTramite.RENOVACION_TUC:
                tramite.enviar_a_control_calidad_final_renovacion_tuc(
                    observaciones=comentario,
                    usuario=self.request.user
                )
                tramite.save()
                messages.success(self.request, 'Evaluación técnica aprobada. Derivado a Control de Calidad para renovar TUC.')
            elif tramite.tipo_tramite in [
                TipoTramite.AUTORIZACION_INICIAL,
                TipoTramite.AUTORIZACION_RUTA,
                TipoTramite.INCREMENTO_FLOTA,
            ]:
                tramite.enviar_a_direccion_administrativa(
                    observaciones=comentario,
                    usuario=self.request.user
                )
                tramite.save()
                messages.success(self.request, 'Evaluación técnica aprobada. Enviado a Dirección Administrativa.')
            else:
                # Para otros trámites, enviar a revisión legal
                tramite.aprobar_tecnico(observaciones=comentario, usuario=self.request.user)
                tramite.save()
                messages.success(self.request, 'Evaluación técnica aprobada. Enviado a revisión legal.')
        except Exception as e:
            messages.error(self.request, f'Error: {str(e)}')
        return HttpResponseRedirect(self.get_success_url())


class EnviarDireccionGeneralView(TransicionBaseView):
    """Derivar a Direccion General."""
    roles_permitidos = [Roles.ADMIN_SISTEMA, Roles.DIRECTOR_ADMINISTRATIVO]

    def dispatch(self, request, *args, **kwargs):
        tramite = self.get_tramite()
        if tramite.tipo_tramite not in [
            TipoTramite.AUTORIZACION_INICIAL,
            TipoTramite.AUTORIZACION_RUTA,
            TipoTramite.INCREMENTO_FLOTA,
        ]:
            messages.error(request, 'Esta acción solo aplica a Autorización Inicial, Autorización de Ruta o Incremento de Flota.')
            return redirect('tramites:detalle', pk=tramite.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Derivar a Dirección General'
        context['accion'] = 'Derivar'
        return context

    def form_valid(self, form):
        tramite = self.get_tramite()
        try:
            comentario = form.cleaned_data.get('comentario', '').strip()
            tramite.enviar_a_direccion_general(
                observaciones=comentario,
                usuario=self.request.user
            )
            tramite.save()
            messages.success(self.request, 'Trámite derivado a Dirección General.')
        except Exception as e:
            messages.error(self.request, f'Error: {str(e)}')
        return HttpResponseRedirect(self.get_success_url())


class ObservarTramiteView(TransicionBaseView):
    """Observar trámite."""
    form_class = ObservacionForm
    roles_permitidos = [Roles.ADMIN_SISTEMA, Roles.ESPECIALISTA_TECNICO, Roles.CONTROL_CALIDAD]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Observar Trámite'
        context['accion'] = 'Observar'
        context['es_observacion'] = True  # Flag para mostrar el campo de rol en la plantilla
        return context
    
    def form_valid(self, form):
        tramite = self.get_tramite()
        try:
            observaciones = form.cleaned_data.get('observaciones', '').strip()
            plazo = form.cleaned_data.get('plazo_subsanacion')
            rol_asignado = form.cleaned_data.get('rol_proximo_responsable', '')
            
            # Agregar el rol a las observaciones en el formato especificado
            if rol_asignado:
                if observaciones:
                    observaciones += f"\n\n[PRÓXIMO ROL RESPONSABLE: {rol_asignado}]"
                else:
                    observaciones = f"[PRÓXIMO ROL RESPONSABLE: {rol_asignado}]"
            
            tramite._comentario_transicion = observaciones
            if (
                tramite.tipo_tramite == TipoTramite.BAJA_VEHICULO and
                tramite.estado == EstadoTramite.EN_CONTROL_CALIDAD
            ):
                tramite.observar_control_calidad_baja_vehiculo(
                    observaciones=observaciones,
                    plazo_subsanacion=plazo,
                    usuario=self.request.user
                )
            elif (
                tramite.tipo_tramite == TipoTramite.RENOVACION_TUC and
                tramite.estado == EstadoTramite.PENDIENTE_FIRMA
            ):
                tramite.observar_control_calidad_renovacion_tuc(
                    observaciones=observaciones,
                    plazo_subsanacion=plazo,
                    usuario=self.request.user
                )
            else:
                tramite.observar_tecnico(
                    observaciones=observaciones,
                    plazo_subsanacion=plazo,
                    usuario=self.request.user
                )
            tramite.save()
            
            messages.success(self.request, 'Trámite observado. Se notificará al administrado.')
        except Exception as e:
            messages.error(self.request, f'Error: {str(e)}')
        return HttpResponseRedirect(self.get_success_url())


class SubsanarTramiteView(TransicionBaseView):
    """Subsanar observaciones."""
    roles_permitidos = [Roles.ADMIN_SISTEMA, Roles.MESA_PARTES, Roles.ESPECIALISTA_TECNICO, Roles.ASESORIA_LEGAL]
    form_class = SubsanacionForm  # Usar el formulario específico de subsanación
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Subsanar Observaciones'
        context['accion'] = 'Subsanar'
        context['es_subsanacion'] = True  # Flag para mostrar el campo de rol en la plantilla
        return context
    
    def form_valid(self, form):
        tramite = self.get_tramite()
        try:
            # Capturar el comentario del formulario
            comentario = form.cleaned_data.get('comentario', '').strip()
            
            # Pasar el comentario/observaciones a la transición
            tramite._comentario_transicion = comentario
            ultima_observacion = (
                HistorialTramite.objects
                .filter(tramite=tramite, estado_nuevo=EstadoTramite.OBSERVADO)
                .order_by('-fecha', '-id')
                .first()
            )
            if (
                tramite.tipo_tramite == TipoTramite.RENOVACION_TUC and
                ultima_observacion and
                ultima_observacion.estado_anterior == EstadoTramite.PENDIENTE_FIRMA
            ):
                tramite.subsanar_observacion_control_calidad_renovacion_tuc(
                    usuario=self.request.user,
                    observaciones=comentario
                )
            elif (
                tramite.tipo_tramite == TipoTramite.BAJA_VEHICULO and
                ultima_observacion and
                ultima_observacion.estado_anterior == EstadoTramite.EN_CONTROL_CALIDAD
            ):
                tramite.subsanar_observacion_control_calidad_baja_vehiculo(
                    usuario=self.request.user,
                    observaciones=comentario
                )
            elif (
                tramite.tipo_tramite in [
                    TipoTramite.AUTORIZACION_INICIAL,
                    TipoTramite.AUTORIZACION_RUTA,
                ] and
                ultima_observacion and
                ultima_observacion.estado_anterior == EstadoTramite.EN_REVISION_LEGAL
            ):
                tramite.subsanar_observacion_legal_autorizacion_inicial(
                    usuario=self.request.user,
                    observaciones=comentario
                )
            else:
                tramite.subsanar_observaciones(usuario=self.request.user, observaciones=comentario)
            tramite.save()
            messages.success(self.request, 'Observaciones subsanadas. Trámite retornado para revisión.')
        except Exception as e:
            messages.error(self.request, f'Error: {str(e)}')
        return HttpResponseRedirect(self.get_success_url())


class EnviarLegalView(TransicionBaseView):
    """Enviar a revisión legal (desde evaluación técnica)."""
    roles_permitidos = [Roles.ADMIN_SISTEMA, Roles.ESPECIALISTA_TECNICO, Roles.DIRECTOR_GENERAL]

    def dispatch(self, request, *args, **kwargs):
        tramite = self.get_tramite()
        if (
            tramite.tipo_tramite in [
                TipoTramite.AUTORIZACION_INICIAL,
                TipoTramite.AUTORIZACION_RUTA,
                TipoTramite.INCREMENTO_FLOTA,
            ] and
            request.user.rol not in [Roles.ADMIN_SISTEMA, Roles.DIRECTOR_GENERAL]
        ):
            messages.error(request, 'Solo Dirección General puede derivar este trámite a Asesoría Legal.')
            return redirect('tramites:detalle', pk=tramite.pk)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tramite = self.get_tramite()
        # Para RENOVACION_TUC, el especialista deriva a Control de Calidad
        if tramite.tipo_tramite == TipoTramite.RENOVACION_TUC:
            context['titulo'] = 'Derivar a Control de Calidad'
        elif tramite.tipo_tramite in [
            TipoTramite.AUTORIZACION_INICIAL,
            TipoTramite.AUTORIZACION_RUTA,
            TipoTramite.INCREMENTO_FLOTA,
        ]:
            context['titulo'] = 'Derivar a Asesoría Legal'
        else:
            context['titulo'] = 'Enviar a Revisión Legal'
        context['accion'] = 'Enviar'
        return context
    
    def form_valid(self, form):
        tramite = self.get_tramite()
        try:
            comentario = form.cleaned_data.get('comentario', '').strip()
            # Para RENOVACION_TUC, enviar directamente a firma sin pasar por revisión legal
            if tramite.tipo_tramite == TipoTramite.RENOVACION_TUC:
                tramite.aprobar_tecnico_sin_revision_legal(usuario=self.request.user)
                tramite.save()
                messages.success(self.request, 'Trámite derivado a Control de Calidad.')
            elif tramite.tipo_tramite in [
                TipoTramite.AUTORIZACION_INICIAL,
                TipoTramite.AUTORIZACION_RUTA,
                TipoTramite.INCREMENTO_FLOTA,
            ]:
                if tramite.estado != EstadoTramite.EN_DIRECCION_GENERAL:
                    messages.error(self.request, 'El trámite debe pasar por Dirección Administrativa y Dirección General antes de Asesoría Legal.')
                    return HttpResponseRedirect(self.get_success_url())
                tramite.enviar_a_revision_legal_desde_direccion_general(
                    observaciones=comentario,
                    usuario=self.request.user
                )
                tramite.save()
                messages.success(self.request, 'Trámite derivado a Asesoría Legal.')
            else:
                # Para otros trámites, enviar a revisión legal
                tramite.aprobar_tecnico(observaciones=comentario, usuario=self.request.user)
                tramite.save()
                messages.success(self.request, 'Trámite enviado a revisión legal.')
        except Exception as e:
            messages.error(self.request, f'Error: {str(e)}')
        return HttpResponseRedirect(self.get_success_url())


class AprobarLegalView(TransicionBaseView):
    """Aprobar revisión legal."""
    roles_permitidos = [Roles.ADMIN_SISTEMA, Roles.ASESORIA_LEGAL]
    
    def dispatch(self, request, *args, **kwargs):
        """Validar que ASESORIA_LEGAL no acceda a RENOVACION_TUC."""
        tramite = self.get_tramite()
        user = request.user
        
        # ASESORIA_LEGAL no puede aprobar RENOVACION_TUC
        if user.rol == Roles.ASESORIA_LEGAL and tramite.tipo_tramite == TipoTramite.RENOVACION_TUC:
            messages.error(request, 'No tienes permiso para actuar sobre Renovación de TUC. Este trámite va directo a firma.')
            return redirect('tramites:detalle', pk=tramite.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tramite = self.get_tramite()
        if tramite.tipo_tramite in [TipoTramite.AUTORIZACION_INICIAL, TipoTramite.AUTORIZACION_RUTA]:
            context['titulo'] = 'Derivar a Dirección General'
            context['accion'] = 'Derivar'
        else:
            context['titulo'] = 'Aprobar Revisión Legal'
            context['accion'] = 'Aprobar'
        return context
    
    def form_valid(self, form):
        tramite = self.get_tramite()
        try:
            comentario = form.cleaned_data.get('comentario', '').strip()
            if tramite.tipo_tramite in [TipoTramite.AUTORIZACION_INICIAL, TipoTramite.AUTORIZACION_RUTA]:
                tramite.derivar_legal_a_direccion_general_autorizacion_inicial(
                    observaciones=comentario,
                    usuario=self.request.user
                )
            else:
                tramite.aprobar_legal(observaciones=comentario, usuario=self.request.user)
            tramite.save()
            if tramite.tipo_tramite in [TipoTramite.AUTORIZACION_INICIAL, TipoTramite.AUTORIZACION_RUTA]:
                messages.success(self.request, 'Revisión legal derivada a Dirección General para aprobación con resolución.')
            elif tramite.tipo_tramite == TipoTramite.INCREMENTO_FLOTA:
                messages.success(self.request, 'Revisión legal aprobada. Devuelto a Dirección General para registrar la resolución.')
            else:
                messages.success(self.request, 'Revisión legal aprobada. Enviado a firma de Director.')
        except Exception as e:
            messages.error(self.request, f'Error: {str(e)}')
        return HttpResponseRedirect(self.get_success_url())


class AprobarTramiteView(TransicionBaseView):
    """Aprobar trámite (firma de Director)."""
    form_class = AprobacionForm
    roles_permitidos = [Roles.ADMIN_SISTEMA, Roles.DIRECTOR_GENERAL, Roles.DIRECTOR_ADMINISTRATIVO, Roles.CONTROL_CALIDAD]

    def dispatch(self, request, *args, **kwargs):
        """Validar permisos a nivel de acceso a la URL."""
        tramite = self.get_tramite()
        user = request.user
        
        # RENOVACION_TUC no usa aprobacion con resolucion; Direccion Administrativa solo firma y deriva.
        if tramite.tipo_tramite == TipoTramite.RENOVACION_TUC:
            messages.error(request, 'Renovación de TUC no se aprueba con resolución. Debe seguir el flujo de firma y derivación.')
            return redirect('tramites:detalle', pk=tramite.pk)

        if tramite.tipo_tramite == TipoTramite.INCREMENTO_FLOTA:
            if user.rol not in [Roles.ADMIN_SISTEMA, Roles.DIRECTOR_GENERAL]:
                messages.error(request, 'Solo Dirección General puede aprobar Incremento de Flota antes de enviarlo a Control de Calidad.')
                return redirect('tramites:detalle', pk=tramite.pk)

        if tramite.tipo_tramite == TipoTramite.AUTORIZACION_INICIAL:
            if user.rol not in [Roles.ADMIN_SISTEMA, Roles.DIRECTOR_GENERAL]:
                messages.error(request, 'Solo Dirección General puede aprobar Autorización Inicial.')
                return redirect('tramites:detalle', pk=tramite.pk)
            if (
                tramite.estado != EstadoTramite.EN_DIRECCION_GENERAL or
                not tramite.retorno_legal_a_direccion_general()
            ):
                messages.error(request, 'Autorización Inicial debe retornar de Asesoría Legal a Dirección General antes de aprobarse.')
                return redirect('tramites:detalle', pk=tramite.pk)

        if tramite.tipo_tramite == TipoTramite.AUTORIZACION_RUTA:
            if user.rol not in [Roles.ADMIN_SISTEMA, Roles.DIRECTOR_GENERAL]:
                messages.error(request, 'Solo Dirección General puede aprobar Autorización de Ruta.')
                return redirect('tramites:detalle', pk=tramite.pk)
            if (
                tramite.estado != EstadoTramite.EN_DIRECCION_GENERAL or
                not tramite.retorno_legal_a_direccion_general()
            ):
                messages.error(request, 'Autorización de Ruta debe retornar de Asesoría Legal a Dirección General antes de aprobarse.')
                return redirect('tramites:detalle', pk=tramite.pk)
        
        # Si es DIRECTOR_ADMINISTRATIVO, solo puede aprobar HABILITACION_CONDUCTOR (no RENOVACION_TUC)
        if user.rol == Roles.DIRECTOR_ADMINISTRATIVO:
            if tramite.tipo_tramite != TipoTramite.HABILITACION_CONDUCTOR:
                messages.error(request, 'No tienes permiso para aprobar este trámite.')
                return redirect('tramites:detalle', pk=tramite.pk)
        
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tramite'] = self.get_tramite()
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        tramite = self.get_tramite()

        if tramite.tipo_tramite == TipoTramite.RENOVACION_TUC and not initial.get('numero_resolucion'):
            vehiculo_tramite = (
                tramite.vehiculos_tramite
                .select_related(
                    'vehiculo_existente__autorizacion_principal',
                    'vehiculo_existente',
                )
                .filter(vehiculo_existente__isnull=False)
                .first()
            )

            numero_resolucion = ''
            if vehiculo_tramite and vehiculo_tramite.vehiculo_existente:
                vehiculo = vehiculo_tramite.vehiculo_existente
                numero_resolucion = vehiculo.numero_resolucion or ''

                if not numero_resolucion and vehiculo.habilitacion_vigente and vehiculo.habilitacion_vigente.autorizacion_id:
                    numero_resolucion = vehiculo.habilitacion_vigente.autorizacion.numero_resolucion or ''

                if not numero_resolucion and vehiculo.autorizacion_principal_id:
                    numero_resolucion = vehiculo.autorizacion_principal.numero_resolucion or ''

            if not numero_resolucion and tramite.autorizacion_id:
                numero_resolucion = tramite.autorizacion.numero_resolucion or ''

            if numero_resolucion:
                initial['numero_resolucion'] = numero_resolucion

        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tramite = self.get_tramite()
        if tramite.tipo_tramite in [TipoTramite.AUTORIZACION_INICIAL, TipoTramite.AUTORIZACION_RUTA]:
            context['titulo'] = 'Aprobar con Resolución'
        else:
            context['titulo'] = 'Aprobar Trámite'
        context['accion'] = 'Aprobar'
        
        # Mostrar datos que se crearán al aprobar
        if hasattr(tramite, 'datos') and tramite.datos:
            context['datos_tramite'] = tramite.datos.datos_json
            context['tipo_tramite_display'] = dict(TipoTramite.CHOICES).get(
                tramite.tipo_tramite, tramite.tipo_tramite
            )
        
        return context
    
    def form_valid(self, form):
        tramite = self.get_tramite()
        user = self.request.user
        
        # Si es RENOVACION_TUC, solo CONTROL_CALIDAD (y ADMIN_SISTEMA) pueden aprobar
        if tramite.tipo_tramite == TipoTramite.RENOVACION_TUC:
            if user.rol not in [Roles.ADMIN_SISTEMA, Roles.CONTROL_CALIDAD]:
                messages.error(self.request, 'No tienes permiso para firmar este trámite.')
                return HttpResponseRedirect(self.get_success_url())

        if tramite.tipo_tramite == TipoTramite.INCREMENTO_FLOTA:
            if user.rol not in [Roles.ADMIN_SISTEMA, Roles.DIRECTOR_GENERAL]:
                messages.error(self.request, 'Solo Dirección General puede aprobar Incremento de Flota antes de Control de Calidad.')
                return HttpResponseRedirect(self.get_success_url())

        if tramite.tipo_tramite == TipoTramite.AUTORIZACION_INICIAL:
            if user.rol not in [Roles.ADMIN_SISTEMA, Roles.DIRECTOR_GENERAL]:
                messages.error(self.request, 'Solo Dirección General puede aprobar Autorización Inicial.')
                return HttpResponseRedirect(self.get_success_url())
            if (
                tramite.estado != EstadoTramite.EN_DIRECCION_GENERAL or
                not tramite.retorno_legal_a_direccion_general()
            ):
                messages.error(self.request, 'Autorización Inicial debe retornar de Asesoría Legal a Dirección General antes de aprobarse.')
                return HttpResponseRedirect(self.get_success_url())

        if tramite.tipo_tramite == TipoTramite.AUTORIZACION_RUTA:
            if user.rol not in [Roles.ADMIN_SISTEMA, Roles.DIRECTOR_GENERAL]:
                messages.error(self.request, 'Solo Dirección General puede aprobar Autorización de Ruta.')
                return HttpResponseRedirect(self.get_success_url())
            if (
                tramite.estado != EstadoTramite.EN_DIRECCION_GENERAL or
                not tramite.retorno_legal_a_direccion_general()
            ):
                messages.error(self.request, 'Autorización de Ruta debe retornar de Asesoría Legal a Dirección General antes de aprobarse.')
                return HttpResponseRedirect(self.get_success_url())
        
        # Si es DIRECTOR_ADMINISTRATIVO, solo puede aprobar HABILITACION_CONDUCTOR (no RENOVACION_TUC)
        if user.rol == Roles.DIRECTOR_ADMINISTRATIVO:
            if tramite.tipo_tramite != TipoTramite.HABILITACION_CONDUCTOR:
                messages.error(self.request, 'No tienes permiso para firmar este trámite.')
                return HttpResponseRedirect(self.get_success_url())
        
        try:
            with transaction.atomic():
                numero_res = form.cleaned_data.get('numero_resolucion', '')
                fecha_res = form.cleaned_data.get('fecha_resolucion')
                archivo_res = form.cleaned_data.get('archivo_resolucion')
                
                # Actualizar campos de resolución en el trámite
                tramite.numero_resolucion = numero_res
                tramite.fecha_resolucion = fecha_res
                if archivo_res:
                    tramite.archivo_resolucion = archivo_res
                
                tramite.aprobar(
                    numero_resolucion=numero_res, 
                    fecha_resolucion=fecha_res,
                    usuario=self.request.user
                )
                tramite.save()

                if tramite.tipo_tramite == TipoTramite.AUTORIZACION_RUTA:
                    from .services import procesar_tramite_aprobado

                    resultado = procesar_tramite_aprobado(tramite, self.request.user)
                    if not resultado['exito']:
                        raise Exception(resultado['mensaje'])

                    tramite.cerrar(usuario=self.request.user)
                    tramite.save()

                    mensaje = f'Trámite APROBADO y CERRADO exitosamente. {resultado["mensaje"]}'
                    if resultado['entidades_creadas']:
                        mensaje += '<br><strong>Entidades creadas:</strong><ul>'
                        for entidad in resultado['entidades_creadas']:
                            mensaje += f'<li>{entidad["tipo"]}: {entidad["descripcion"]}</li>'
                        mensaje += '</ul>'
                    messages.success(self.request, mensaje, extra_tags='safe')
                else:
                    messages.success(self.request, 'Trámite APROBADO exitosamente. Pendiente de cierre y emisión de TUCs.')
            
        except Exception as e:
            messages.error(self.request, f'Error: {str(e)}')
            return self.form_invalid(form)
            
        return HttpResponseRedirect(self.get_success_url())


class DenegarTramiteView(TransicionBaseView):
    """Denegar trámite."""
    form_class = DenegacionForm
    roles_permitidos = [Roles.ADMIN_SISTEMA, Roles.DIRECTOR_GENERAL, Roles.DIRECTOR_ADMINISTRATIVO, Roles.CONTROL_CALIDAD]
    
    def dispatch(self, request, *args, **kwargs):
        """Validar permisos a nivel de acceso a la URL."""
        tramite = self.get_tramite()
        user = request.user
        
        # Si es RENOVACION_TUC, solo CONTROL_CALIDAD (y ADMIN_SISTEMA) pueden denegar
        if tramite.tipo_tramite == TipoTramite.RENOVACION_TUC:
            if user.rol not in [Roles.ADMIN_SISTEMA, Roles.CONTROL_CALIDAD]:
                messages.error(request, 'No tienes permiso para denegar este trámite.')
                return redirect('tramites:detalle', pk=tramite.pk)

        if tramite.tipo_tramite == TipoTramite.INCREMENTO_FLOTA:
            if user.rol not in [Roles.ADMIN_SISTEMA, Roles.DIRECTOR_GENERAL]:
                messages.error(request, 'Solo Dirección General puede denegar Incremento de Flota en la etapa final.')
                return redirect('tramites:detalle', pk=tramite.pk)
        
        # Si es DIRECTOR_ADMINISTRATIVO, solo puede denegar HABILITACION_CONDUCTOR (no RENOVACION_TUC)
        if user.rol == Roles.DIRECTOR_ADMINISTRATIVO:
            if tramite.tipo_tramite != TipoTramite.HABILITACION_CONDUCTOR:
                messages.error(request, 'No tienes permiso para denegar este trámite.')
                return redirect('tramites:detalle', pk=tramite.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Denegar Trámite'
        context['accion'] = 'Denegar'
        return context
    
    def form_valid(self, form):
        tramite = self.get_tramite()
        user = self.request.user
        
        # Si es RENOVACION_TUC, solo CONTROL_CALIDAD (y ADMIN_SISTEMA) pueden denegar
        if tramite.tipo_tramite == TipoTramite.RENOVACION_TUC:
            if user.rol not in [Roles.ADMIN_SISTEMA, Roles.CONTROL_CALIDAD]:
                messages.error(self.request, 'No tienes permiso para denegar este trámite.')
                return HttpResponseRedirect(self.get_success_url())

        if tramite.tipo_tramite == TipoTramite.INCREMENTO_FLOTA:
            if user.rol not in [Roles.ADMIN_SISTEMA, Roles.DIRECTOR_GENERAL]:
                messages.error(self.request, 'Solo Dirección General puede denegar Incremento de Flota en la etapa final.')
                return HttpResponseRedirect(self.get_success_url())
        
        # Si es DIRECTOR_ADMINISTRATIVO, solo puede denegar HABILITACION_CONDUCTOR (no RENOVACION_TUC)
        if user.rol == Roles.DIRECTOR_ADMINISTRATIVO:
            if tramite.tipo_tramite != TipoTramite.HABILITACION_CONDUCTOR:
                messages.error(self.request, 'No tienes permiso para denegar este trámite.')
                return HttpResponseRedirect(self.get_success_url())
        
        try:
            numero_res = form.cleaned_data.get('numero_resolucion', '')
            fecha_res = form.cleaned_data.get('fecha_resolucion')
            motivo = form.cleaned_data.get('motivo_denegacion', '')
            
            # Establecer comentario para la notificación y el historial
            tramite._comentario_transicion = f"DENEGADO. Resolución: {numero_res}. Motivo: {motivo}"
            
            tramite.denegar(
                numero_resolucion=numero_res, 
                fecha_resolucion=fecha_res,
                usuario=self.request.user
            )
            tramite.save()
            
            messages.warning(self.request, 'Trámite DENEGADO.')
        except Exception as e:
            messages.error(self.request, f'Error: {str(e)}')
        return HttpResponseRedirect(self.get_success_url())


class CerrarTramiteView(TransicionBaseView):
    """Cerrar trámite aprobado."""
    roles_permitidos = [Roles.ADMIN_SISTEMA, Roles.DIRECTOR_GENERAL, Roles.DIRECTOR_ADMINISTRATIVO, Roles.CONTROL_CALIDAD]
    
    def dispatch(self, request, *args, **kwargs):
        """Validar permisos a nivel de acceso a la URL."""
        tramite = self.get_tramite()
        user = request.user
        
        # Si es RENOVACION_TUC, solo CONTROL_CALIDAD (y ADMIN_SISTEMA) pueden cerrar
        if tramite.tipo_tramite == TipoTramite.RENOVACION_TUC:
            if user.rol not in [Roles.ADMIN_SISTEMA, Roles.CONTROL_CALIDAD]:
                messages.error(request, 'Solo Control de Calidad puede cerrar trámites de Renovación de TUC.')
                return redirect('tramites:detalle', pk=tramite.pk)

        if tramite.tipo_tramite in [TipoTramite.AUTORIZACION_INICIAL, TipoTramite.INCREMENTO_FLOTA]:
            if user.rol not in [Roles.ADMIN_SISTEMA, Roles.CONTROL_CALIDAD]:
                messages.error(request, 'Solo Control de Calidad puede cerrar este trámite después de la aprobación final.')
                return redirect('tramites:detalle', pk=tramite.pk)
        
        # Si es DIRECTOR_ADMINISTRATIVO, solo puede cerrar HABILITACION_CONDUCTOR (no RENOVACION_TUC)
        if user.rol == Roles.DIRECTOR_ADMINISTRATIVO:
            if tramite.tipo_tramite != TipoTramite.HABILITACION_CONDUCTOR:
                messages.error(request, 'No tienes permiso para cerrar este trámite.')
                return redirect('tramites:detalle', pk=tramite.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Cerrar Trámite'
        context['accion'] = 'Cerrar'
        
        tramite = self.get_tramite()
        # Formset para TUCs si es trámite de vehículos (excepto baja)
        if tramite.tipo_tramite in [
            TipoTramite.AUTORIZACION_INICIAL,
            TipoTramite.INCREMENTO_FLOTA,
            TipoTramite.SUSTITUCION_VEHICULO,
            TipoTramite.RENOVACION_TUC,
        ]:
            if self.request.POST:
                context['tuc_formset'] = VehiculoTUCFormSet(
                    self.request.POST,
                    queryset=tramite.vehiculos_tramite.all(),
                    prefix='tucs'
                )
            else:
                context['tuc_formset'] = VehiculoTUCFormSet(
                    queryset=tramite.vehiculos_tramite.all(),
                    prefix='tucs'
                )
        
        return context
    
    def form_valid(self, form):
        from .services import procesar_tramite_aprobado
        
        tramite = self.get_tramite()
        user = self.request.user
        
        # Si es DIRECTOR_ADMINISTRATIVO, solo puede cerrar HABILITACION_CONDUCTOR y RENOVACION_TUC
        if user.rol == Roles.DIRECTOR_ADMINISTRATIVO:
            if tramite.tipo_tramite not in [TipoTramite.HABILITACION_CONDUCTOR, TipoTramite.RENOVACION_TUC]:
                messages.error(self.request, 'No tienes permiso para cerrar este trámite.')
                return HttpResponseRedirect(self.get_success_url())

        if tramite.tipo_tramite in [TipoTramite.AUTORIZACION_INICIAL, TipoTramite.INCREMENTO_FLOTA]:
            if user.rol not in [Roles.ADMIN_SISTEMA, Roles.CONTROL_CALIDAD]:
                messages.error(self.request, 'Solo Control de Calidad puede cerrar este trámite.')
                return HttpResponseRedirect(self.get_success_url())
        
        # Validar formset de TUCs si aplica
        tuc_formset = None
        if tramite.tipo_tramite in [
            TipoTramite.AUTORIZACION_INICIAL,
            TipoTramite.INCREMENTO_FLOTA,
            TipoTramite.SUSTITUCION_VEHICULO,
            TipoTramite.RENOVACION_TUC,
        ]:
            tuc_formset = VehiculoTUCFormSet(
                self.request.POST,
                queryset=tramite.vehiculos_tramite.all(),
                prefix='tucs'
            )
            if not tuc_formset.is_valid():
                return self.form_invalid(form)
        
        try:
            with transaction.atomic():
                # Guardar TUCs primero
                if tuc_formset:
                    tuc_formset.save()
                
                tramite.cerrar(usuario=self.request.user)
                tramite.save()
                
                # ========== PROCESAR Y CREAR ENTIDADES ==========
                # Ahora se procesa al cerrar
                resultado = procesar_tramite_aprobado(tramite, self.request.user)
                
                if resultado['exito']:
                    # Mostrar mensaje con las entidades creadas
                    mensaje = f'Trámite CERRADO exitosamente. {resultado["mensaje"]}'
                    if resultado['entidades_creadas']:
                        mensaje += '<br><strong>Entidades creadas:</strong><ul>'
                        for entidad in resultado['entidades_creadas']:
                            mensaje += f'<li>{entidad["tipo"]}: {entidad["descripcion"]}</li>'
                        mensaje += '</ul>'
                    messages.success(self.request, mensaje, extra_tags='safe')
                else:
                    # Si falla el procesamiento, lanzamos excepción para hacer rollback
                    raise Exception(resultado['mensaje'])
                    
        except Exception as e:
            messages.error(self.request, f'Error: {str(e)}')
            return self.form_invalid(form)
            
        return HttpResponseRedirect(self.get_success_url())


class ObservarLegalView(TransicionBaseView):
    """Observar trámite desde revisión legal."""
    form_class = ObservacionForm
    roles_permitidos = [Roles.ADMIN_SISTEMA, Roles.ASESORIA_LEGAL]
    
    def dispatch(self, request, *args, **kwargs):
        """Validar que ASESORIA_LEGAL no acceda a RENOVACION_TUC."""
        tramite = self.get_tramite()
        user = request.user
        
        # ASESORIA_LEGAL no puede observar RENOVACION_TUC
        if user.rol == Roles.ASESORIA_LEGAL and tramite.tipo_tramite == TipoTramite.RENOVACION_TUC:
            messages.error(request, 'No tienes permiso para actuar sobre Renovación de TUC. Este trámite va directo a firma.')
            return redirect('tramites:detalle', pk=tramite.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Observar Trámite (Legal)'
        context['accion'] = 'Observar'
        context['es_observacion'] = True  # Flag para mostrar el campo de rol en la plantilla
        return context
    
    def form_valid(self, form):
        tramite = self.get_tramite()
        try:
            observaciones = form.cleaned_data.get('observaciones', '').strip()
            plazo = form.cleaned_data.get('plazo_subsanacion')
            rol_asignado = form.cleaned_data.get('rol_proximo_responsable', '')
            
            # Agregar el rol a las observaciones en el formato especificado
            if rol_asignado:
                if observaciones:
                    observaciones += f"\n\n[PRÓXIMO ROL RESPONSABLE: {rol_asignado}]"
                else:
                    observaciones = f"[PRÓXIMO ROL RESPONSABLE: {rol_asignado}]"
            
            tramite._comentario_transicion = observaciones
            tramite.observar_legal(
                observaciones=observaciones, 
                plazo_subsanacion=plazo,
                usuario=self.request.user
            )
            tramite.save()
            
            messages.success(self.request, 'Trámite observado desde revisión legal.')
        except Exception as e:
            messages.error(self.request, f'Error: {str(e)}')
        return HttpResponseRedirect(self.get_success_url())


class AgregarDocumentoView(RolRequeridoMixin, CreateView):
    """Agregar documento a un trámite."""
    model = DocumentoAdjunto
    form_class = DocumentoAdjuntoForm
    template_name = 'tramites/agregar_documento.html'
    roles_permitidos = TRAMITES_DOCUMENTOS_ROLES
    
    def get_tramite(self):
        return get_object_or_404(Tramite, pk=self.kwargs['pk'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tramite'] = self.get_tramite()
        context['titulo'] = 'Agregar Documento'
        return context
    
    def form_valid(self, form):
        form.instance.tramite = self.get_tramite()
        form.instance.subido_por = self.request.user
        messages.success(self.request, 'Documento agregado exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('tramites:detalle', kwargs={'pk': self.kwargs['pk']})


class DocumentoDownloadView(RolRequeridoMixin, View):
    """Descarga segura de documentos adjuntos por rol."""
    roles_permitidos = TRAMITES_DOCUMENTOS_ROLES

    def get(self, request, pk, doc_id):
        documento = get_object_or_404(DocumentoAdjunto, pk=doc_id, tramite_id=pk)
        if not documento.archivo:
            messages.error(request, 'Documento no disponible.')
            return redirect('tramites:detalle', pk=pk)
        try:
            file_path = documento.archivo.path
        except Exception:
            messages.error(request, 'No se pudo acceder al archivo.')
            return redirect('tramites:detalle', pk=pk)
        if not os.path.exists(file_path):
            messages.error(request, 'Archivo no encontrado en el servidor.')
            return redirect('tramites:detalle', pk=pk)
        filename = os.path.basename(file_path)
        return FileResponse(
            open(file_path, 'rb'),
            as_attachment=True,
            filename=filename,
        )


class DocumentoDeleteView(DeleteView):
    """Eliminar documento adjunto de un trámite."""
    model = DocumentoAdjunto
    template_name = 'tramites/documento_confirm_delete.html'
    pk_url_kwarg = 'doc_id'
    
    def get_object(self, queryset=None):
        """Obtener el documento asegurando que pertenece al trámite correcto."""
        return get_object_or_404(
            DocumentoAdjunto,
            pk=self.kwargs['doc_id'],
            tramite_id=self.kwargs['pk']
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tramite'] = get_object_or_404(Tramite, pk=self.kwargs['pk'])
        return context
    
    def delete(self, request, *args, **kwargs):
        """Guardar información y eliminar."""
        tramite_id = self.kwargs['pk']
        response = super().delete(request, *args, **kwargs)
        messages.success(request, 'Documento eliminado exitosamente.')
        return redirect('tramites:detalle', pk=tramite_id)
    
    def get_success_url(self):
        """Redirigir al detalle del trámite después de eliminar."""
        return reverse_lazy('tramites:detalle', kwargs={'pk': self.kwargs['pk']})


class TramiteExportView(RolRequeridoMixin, View):
    """Exportar trámites a Excel."""
    
    roles_permitidos = TRAMITES_EXPORTAR_ROLES

    def get(self, request):
        queryset = Tramite.objects.select_related(
            'empresa', 'creado_por'
        ).order_by('-fecha_creacion')
        
        # Aplicar filtros
        q = request.GET.get('q')
        estado = request.GET.get('estado')
        tipo = request.GET.get('tipo_tramite')
        
        if q:
            queryset = queryset.filter(
                Q(numero_expediente__icontains=q) |
                Q(empresa__razon_social__icontains=q)
            )
        if estado:
            queryset = queryset.filter(estado=estado)
        if tipo:
            queryset = queryset.filter(tipo_tramite=tipo)
        
        # Preparar datos
        headers = ['Nº Expediente', 'Tipo', 'Empresa', 'Estado',
                   'Fecha Creación', 'Usuario Creador', 'Descripción']
        
        data = []
        for t in queryset:
            data.append([
                t.numero_expediente,
                t.get_tipo_tramite_display(),
                t.empresa.razon_social if t.empresa else '',
                t.get_estado_display(),
                t.fecha_creacion.strftime('%d/%m/%Y %H:%M') if t.fecha_creacion else '',
                str(t.creado_por) if t.creado_por else '',
                t.descripcion_solicitud[:100] + '...' if len(t.descripcion_solicitud) > 100 else t.descripcion_solicitud
            ])
        
        exporter = ExcelExporter('Trámites', headers)
        return exporter.export_to_response(data, 'tramites')


# ============================================================================
# VISTAS PARA RECIBOS DE PAGO
# ============================================================================

class ReciboPagoListView(RolRequeridoMixin, ListView):
    """Lista de recibos de pago de un trámite."""
    model = ReciboPago
    template_name = 'tramites/recibo_list.html'
    context_object_name = 'recibos'
    roles_permitidos = TRAMITES_VER_ROLES
    
    def get_queryset(self):
        self.tramite = get_object_or_404(Tramite, pk=self.kwargs['pk'])
        return ReciboPago.objects.filter(tramite=self.tramite)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tramite'] = self.tramite
        context['titulo'] = f'Recibos de Pago - {self.tramite.numero_expediente}'
        return context


class ReciboPagoCreateView(RolRequeridoMixin, CreateView):
    """Agregar recibo de pago a un trámite."""
    model = ReciboPago
    form_class = ReciboPagoForm
    template_name = 'tramites/recibo_form.html'
    roles_permitidos = TRAMITES_CREAR_EDITAR_ROLES
    
    def dispatch(self, request, *args, **kwargs):
        self.tramite = get_object_or_404(Tramite, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tramite'] = self.tramite
        context['titulo'] = 'Agregar Recibo de Pago'
        return context
    
    def form_valid(self, form):
        form.instance.tramite = self.tramite
        form.instance.registrado_por = self.request.user
        messages.success(self.request, 'Recibo de pago agregado exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('tramites:detalle', kwargs={'pk': self.tramite.pk})


class ReciboPagoDeleteView(RolRequeridoMixin, DeleteView):
    """Eliminar recibo de pago."""
    model = ReciboPago
    template_name = 'tramites/recibo_confirm_delete.html'
    roles_permitidos = TRAMITES_CREAR_EDITAR_ROLES
    
    def get_success_url(self):
        return reverse('tramites:detalle', kwargs={'pk': self.object.tramite.pk})
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Recibo de pago eliminado.')
        return super().delete(request, *args, **kwargs)


# ============================================================================
# VISTAS PARA VEHÍCULOS EN TRÁMITE
# ============================================================================

class VehiculoTramiteListView(RolRequeridoMixin, ListView):
    """Lista de vehículos de un trámite."""
    model = VehiculoTramite
    template_name = 'tramites/vehiculo_tramite_list.html'
    context_object_name = 'vehiculos'
    roles_permitidos = TRAMITES_VER_ROLES
    
    def get_queryset(self):
        self.tramite = get_object_or_404(Tramite, pk=self.kwargs['pk'])
        return VehiculoTramite.objects.filter(tramite=self.tramite)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tramite'] = self.tramite
        context['titulo'] = f'Vehículos - {self.tramite.numero_expediente}'
        return context


class VehiculoTramiteCreateView(RolRequeridoMixin, CreateView):
    """Agregar vehículo a un trámite."""
    model = VehiculoTramite
    form_class = VehiculoTramiteForm
    template_name = 'tramites/vehiculo_tramite_form.html'
    roles_permitidos = TRAMITES_VEHICULO_EDIT_ROLES
    
    def dispatch(self, request, *args, **kwargs):
        self.tramite = get_object_or_404(Tramite, pk=kwargs['pk'])
        # Verificar que el trámite no esté cerrado
        if self.tramite.estado == 'CERRADO':
            messages.error(request, 'No se puede agregar vehículos a un trámite cerrado.')
            return redirect('tramites:detalle', pk=self.tramite.pk)
        # Verificar que el trámite permita vehículos
        tipos_con_vehiculos = [
            TipoTramite.AUTORIZACION_INICIAL,
            TipoTramite.INCREMENTO_FLOTA,
            TipoTramite.SUSTITUCION_VEHICULO,
            TipoTramite.BAJA_VEHICULO,
            TipoTramite.RENOVACION_TUC,
        ]
        if self.tramite.tipo_tramite not in tipos_con_vehiculos:
            messages.error(request, 'Este tipo de trámite no permite agregar vehículos.')
            return redirect('tramites:detalle', pk=self.tramite.pk)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tramite'] = self.tramite
        context['titulo'] = 'Agregar Vehículo al Trámite'
        context['solo_lectura_renovacion_tuc'] = (
            self.tramite.tipo_tramite == TipoTramite.RENOVACION_TUC
            and not self.request.user.is_superuser
            and self.request.user.rol != Roles.DIRECTOR
        )
        # Para sustitución/baja, mostrar vehículos existentes
        if self.tramite.tipo_tramite in [
            TipoTramite.SUSTITUCION_VEHICULO,
            TipoTramite.BAJA_VEHICULO,
            TipoTramite.RENOVACION_TUC,
        ]:
            if self.tramite.autorizacion:
                habilitaciones_vigentes = HabilitacionVehicular.objects.filter(
                    autorizacion=self.tramite.autorizacion,
                    estado='VIGENTE'
                ).select_related('vehiculo')
                vehiculos_ids = habilitaciones_vigentes.values_list('vehiculo_id', flat=True)
                context['vehiculos_existentes'] = Vehiculo.objects.filter(id__in=vehiculos_ids)
                if self.tramite.tipo_tramite == TipoTramite.RENOVACION_TUC:
                    context['vehiculos_renovacion'] = [
                        {
                            'placa': hv.vehiculo.placa,
                            'marca': hv.vehiculo.marca,
                            'modelo': hv.vehiculo.modelo,
                            'numero_tuc': hv.numero_tuc or '',
                            'fecha_expedicion_tuc': hv.fecha_expedicion_tuc.isoformat() if hv.fecha_expedicion_tuc else '',
                            'fecha_expiracion_transportista': hv.fecha_expiracion_transportista.isoformat() if hv.fecha_expiracion_transportista else '',
                        }
                        for hv in habilitaciones_vigentes
                    ]
        
        # Obtener placas ya registradas en este trámite para validación en frontend
        context['placas_en_tramite'] = list(self.tramite.vehiculos_tramite.values_list('placa_nueva', flat=True))
        
        return context
    
    def form_valid(self, form):
        form.instance.tramite = self.tramite
        messages.success(self.request, 'Vehículo agregado al trámite.')
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tramite'] = self.tramite
        return kwargs
    
    def get_success_url(self):
        return reverse('tramites:detalle', kwargs={'pk': self.tramite.pk})


class VehiculoTramiteUpdateView(RolRequeridoMixin, UpdateView):
    """Editar vehículo del trámite."""
    model = VehiculoTramite
    form_class = VehiculoTramiteForm
    template_name = 'tramites/vehiculo_tramite_form.html'
    roles_permitidos = TRAMITES_VEHICULO_EDIT_ROLES
    
    def dispatch(self, request, *args, **kwargs):
        # Verificar que el trámite no esté cerrado
        vehiculo_tramite = self.get_object()
        if vehiculo_tramite.tramite.estado == 'CERRADO':
            messages.error(request, 'No se puede editar vehículos en un trámite cerrado.')
            return redirect('tramites:detalle', pk=vehiculo_tramite.tramite.pk)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tramite = self.object.tramite
        context['tramite'] = tramite
        context['titulo'] = 'Editar Vehículo'
        # Para sustitución/baja, mostrar vehículos existentes
        if tramite.tipo_tramite in [
            TipoTramite.SUSTITUCION_VEHICULO,
            TipoTramite.BAJA_VEHICULO,
            TipoTramite.RENOVACION_TUC,
        ]:
            if tramite.autorizacion:
                habilitaciones_vigentes = HabilitacionVehicular.objects.filter(
                    autorizacion=tramite.autorizacion,
                    estado='VIGENTE'
                ).select_related('vehiculo')
                vehiculos_ids = habilitaciones_vigentes.values_list('vehiculo_id', flat=True)
                context['vehiculos_existentes'] = Vehiculo.objects.filter(id__in=vehiculos_ids)
                if tramite.tipo_tramite == TipoTramite.RENOVACION_TUC:
                    context['vehiculos_renovacion'] = [
                        {
                            'placa': hv.vehiculo.placa,
                            'marca': hv.vehiculo.marca,
                            'modelo': hv.vehiculo.modelo,
                            'numero_tuc': hv.numero_tuc or '',
                            'fecha_expedicion_tuc': hv.fecha_expedicion_tuc.isoformat() if hv.fecha_expedicion_tuc else '',
                            'fecha_expiracion_transportista': hv.fecha_expiracion_transportista.isoformat() if hv.fecha_expiracion_transportista else '',
                        }
                        for hv in habilitaciones_vigentes
                    ]
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Vehículo actualizado.')
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tramite'] = self.object.tramite
        return kwargs
    
    def get_success_url(self):
        return reverse('tramites:detalle', kwargs={'pk': self.object.tramite.pk})


class VehiculoTramiteDeleteView(RolRequeridoMixin, DeleteView):
    """Eliminar vehículo del trámite."""
    model = VehiculoTramite
    template_name = 'tramites/vehiculo_tramite_confirm_delete.html'
    roles_permitidos = TRAMITES_VEHICULO_EDIT_ROLES
    
    def dispatch(self, request, *args, **kwargs):
        # Verificar que el trámite no esté cerrado
        vehiculo_tramite = self.get_object()
        if vehiculo_tramite.tramite.estado == 'CERRADO':
            messages.error(request, 'No se puede eliminar vehículos en un trámite cerrado.')
            return redirect('tramites:detalle', pk=vehiculo_tramite.tramite.pk)
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('tramites:detalle', kwargs={'pk': self.object.tramite.pk})
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Vehículo eliminado del trámite.')
        return super().delete(request, *args, **kwargs)


# ============================================================================
# VISTAS PARA CONDUCTORES EN TRÁMITE
# ============================================================================

class ConductorTramiteListView(RolRequeridoMixin, ListView):
    """Lista de conductores de un trámite."""
    model = ConductorTramite
    template_name = 'tramites/conductor_tramite_list.html'
    context_object_name = 'conductores'
    roles_permitidos = TRAMITES_VER_ROLES
    
    def get_queryset(self):
        self.tramite = get_object_or_404(Tramite, pk=self.kwargs['pk'])
        return ConductorTramite.objects.filter(tramite=self.tramite)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tramite'] = self.tramite
        context['titulo'] = f'Conductores - {self.tramite.numero_expediente}'
        return context


class ConductorTramiteCreateView(RolRequeridoMixin, CreateView):
    """Agregar conductor a un trámite."""
    model = ConductorTramite
    form_class = ConductorTramiteForm
    template_name = 'tramites/conductor_tramite_form.html'
    roles_permitidos = TRAMITES_CREAR_EDITAR_ROLES
    
    def dispatch(self, request, *args, **kwargs):
        self.tramite = get_object_or_404(Tramite, pk=kwargs['pk'])
        # Verificar que el trámite no esté cerrado
        if self.tramite.estado == 'CERRADO':
            messages.error(request, 'No se puede agregar conductores a un trámite cerrado.')
            return redirect('tramites:detalle', pk=self.tramite.pk)
        # Verificar que el trámite permita conductores
        tipos_con_conductores = [
            TipoTramite.AUTORIZACION_INICIAL,
            TipoTramite.INCREMENTO_FLOTA,
            TipoTramite.HABILITACION_CONDUCTOR,
            TipoTramite.BAJA_CONDUCTOR
        ]
        if self.tramite.tipo_tramite not in tipos_con_conductores:
            messages.error(request, 'Este tipo de trámite no permite agregar conductores.')
            return redirect('tramites:detalle', pk=self.tramite.pk)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tramite'] = self.tramite
        context['titulo'] = 'Agregar Conductor al Trámite'
        # Para baja, mostrar conductores existentes
        if self.tramite.tipo_tramite == TipoTramite.BAJA_CONDUCTOR:
            if self.tramite.autorizacion:
                conductores_ids = HabilitacionConductor.objects.filter(
                    autorizacion=self.tramite.autorizacion,
                    estado='VIGENTE'
                ).values_list('conductor_id', flat=True)
                context['conductores_existentes'] = Conductor.objects.filter(id__in=conductores_ids)
        return context
    
    def form_valid(self, form):
        form.instance.tramite = self.tramite
        messages.success(self.request, 'Conductor agregado al trámite.')
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tramite'] = self.tramite
        return kwargs
    
    def get_success_url(self):
        return reverse('tramites:detalle', kwargs={'pk': self.tramite.pk})


class ConductorTramiteUpdateView(RolRequeridoMixin, UpdateView):
    """Editar conductor del trámite."""
    model = ConductorTramite
    form_class = ConductorTramiteForm
    template_name = 'tramites/conductor_tramite_form.html'
    roles_permitidos = TRAMITES_CREAR_EDITAR_ROLES
    
    def dispatch(self, request, *args, **kwargs):
        # Verificar que el trámite no esté cerrado
        conductor_tramite = self.get_object()
        if conductor_tramite.tramite.estado == 'CERRADO':
            messages.error(request, 'No se puede editar conductores en un trámite cerrado.')
            return redirect('tramites:detalle', pk=conductor_tramite.tramite.pk)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tramite'] = self.object.tramite
        context['titulo'] = 'Editar Conductor'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Conductor actualizado.')
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tramite'] = self.object.tramite
        return kwargs
    
    def get_success_url(self):
        return reverse('tramites:detalle', kwargs={'pk': self.object.tramite.pk})


class ConductorTramiteDeleteView(RolRequeridoMixin, DeleteView):
    """Eliminar conductor del trámite."""
    model = ConductorTramite
    template_name = 'tramites/conductor_tramite_confirm_delete.html'
    roles_permitidos = TRAMITES_CREAR_EDITAR_ROLES
    
    def dispatch(self, request, *args, **kwargs):
        # Verificar que el trámite no esté cerrado
        conductor_tramite = self.get_object()
        if conductor_tramite.tramite.estado == 'CERRADO':
            messages.error(request, 'No se puede eliminar conductores en un trámite cerrado.')
            return redirect('tramites:detalle', pk=conductor_tramite.tramite.pk)
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('tramites:detalle', kwargs={'pk': self.object.tramite.pk})
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Conductor eliminado del trámite.')
        return super().delete(request, *args, **kwargs)


# ============================================================================
# VISTAS AJAX PARA FILTROS EN CASCADA
# ============================================================================

from apps.empresas.models import EmpresaTransporte

@rol_requerido(TRAMITES_CREAR_EDITAR_ROLES)
def get_autorizacion_por_empresa(request, empresa_id):
    """
    Retorna las autorizaciones de una empresa.
    """
    try:
        autorizaciones = Autorizacion.objects.filter(
            empresa_id=empresa_id
        ).order_by('-estado', '-fecha_creacion')
        
        data = []
        for auth in autorizaciones:
            label = f"{auth.numero_resolucion}"
            if auth.estado != 'VIGENTE':
                label += f" ({auth.estado})"
            if auth.fecha_fin_vigencia:
                label += f" - Vence: {auth.fecha_fin_vigencia.strftime('%d/%m/%Y')}"
                
            data.append({
                'id': auth.id,
                'numero_resolucion': auth.numero_resolucion,
                'fecha_fin_vigencia': auth.fecha_fin_vigencia.strftime('%d/%m/%Y') if auth.fecha_fin_vigencia else '',
                'text': label,
                'estado': auth.estado
            })
            
        return JsonResponse({
            'success': True,
            'autorizaciones': data
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@rol_requerido(TRAMITES_CREAR_EDITAR_ROLES)
def get_vehiculos_por_empresa(request, empresa_id):
    """
    Retorna los vehículos de una empresa.
    """
    try:
        vehiculos = Vehiculo.objects.filter(
            empresa_propietaria_id=empresa_id
        ).values('id', 'placa', 'marca', 'modelo', 'estado')
        
        vehiculos_list = [
            {
                'id': v['id'],
                'text': f"{v['placa']} - {v['marca']} {v['modelo']} ({v['estado']})"
            }
            for v in vehiculos
        ]
        
        return JsonResponse({
            'success': True,
            'vehiculos': vehiculos_list
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@rol_requerido(TRAMITES_CREAR_EDITAR_ROLES)
def get_conductores_por_empresa(request, empresa_id):
    """
    Retorna los conductores habilitados para una empresa.
    """
    try:
        # Obtener conductores que tienen habilitación vigente con la empresa
        habilitaciones = HabilitacionConductor.objects.filter(
            empresa_id=empresa_id,
            estado='VIGENTE'
        ).select_related('conductor')
        
        conductores_list = [
            {
                'id': h.conductor.id,
                'text': f"{h.conductor.dni} - {h.conductor.nombre_completo}"
            }
            for h in habilitaciones
        ]
        
        # Si no hay habilitaciones, buscar conductores asociados a la empresa directamente
        if not conductores_list:
            conductores = Conductor.objects.filter(
                empresa_id=empresa_id,
                estado='ACTIVO'
            )
            conductores_list = [
                {
                    'id': c.id,
                    'text': f"{c.dni} - {c.nombre_completo}"
                }
                for c in conductores
            ]
        
        return JsonResponse({
            'success': True,
            'conductores': conductores_list
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})




