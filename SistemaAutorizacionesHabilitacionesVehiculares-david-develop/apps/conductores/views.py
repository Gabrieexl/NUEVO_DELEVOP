"""
Vistas para la app conductores.
"""

from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils import timezone

from .models import Conductor, HabilitacionConductor
from .forms import ConductorForm, ConductorBusquedaForm
from apps.usuarios.mixins import RolRequeridoMixin
from utils.constants import Roles
from utils.exports import ExcelExporter

# Roles por acción en conductores (según matriz acordada).
CONDUCTORES_VER_ROLES = [
    Roles.ADMIN_SISTEMA,
    Roles.MESA_PARTES,
    Roles.ESPECIALISTA_TECNICO,
    Roles.ASESORIA_LEGAL,
    Roles.CONSULTA_INTERNA,
    Roles.DIRECTOR_GENERAL,
    Roles.DIRECTOR_ADMINISTRATIVO,
    Roles.CONTROL_CALIDAD,
]
CONDUCTORES_EDIT_ROLES = [
    Roles.ADMIN_SISTEMA,
    Roles.ESPECIALISTA_TECNICO,
]
CONDUCTORES_EXPORT_ROLES = [
    Roles.ADMIN_SISTEMA,
    Roles.ESPECIALISTA_TECNICO,
    Roles.ASESORIA_LEGAL,
]


class ConductorListView(RolRequeridoMixin, ListView):
    """Lista de conductores."""
    model = Conductor
    template_name = 'conductores/conductor_list.html'
    context_object_name = 'conductores'
    paginate_by = 20
    roles_permitidos = CONDUCTORES_VER_ROLES
    
    def get_queryset(self):
        queryset = Conductor.objects.select_related('empresa').order_by('apellido_paterno', 'apellido_materno', 'nombres')
        
        # Filtros de búsqueda
        q = self.request.GET.get('q')
        estado = self.request.GET.get('estado')
        licencia_categoria = self.request.GET.get('licencia_categoria')
        
        if q:
            queryset = queryset.filter(
                Q(dni__icontains=q) |
                Q(nombres__icontains=q) |
                Q(apellido_paterno__icontains=q) |
                Q(apellido_materno__icontains=q) |
                Q(licencia_numero__icontains=q)
            )
        
        if estado:
            queryset = queryset.filter(estado=estado)
        
        if licencia_categoria:
            queryset = queryset.filter(licencia_categoria=licencia_categoria)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Conductores'
        context['form_busqueda'] = ConductorBusquedaForm(self.request.GET)
        context['total_conductores'] = Conductor.objects.count()
        context['activos'] = Conductor.objects.filter(estado='ACTIVO').count()
        
        # Variables para filtros en template (evitar DEBUG exceptions)
        context['q'] = self.request.GET.get('q', '')
        context['estado'] = self.request.GET.get('estado', '')
        context['licencia_categoria'] = self.request.GET.get('licencia_categoria', '')
        # Evitar duplicar `page` en los links de paginacion.
        # Si queda `?page=3&page=2`, Django toma el primer valor y la pagina no avanza.
        query_params = self.request.GET.copy()
        query_params.pop('page', None)
        context['query_params'] = query_params.urlencode()
        
        # Alertas de licencias por vencer
        hoy = timezone.now().date()
        proximos_30_dias = hoy + timezone.timedelta(days=30)
        context['licencias_por_vencer'] = Conductor.objects.filter(
            licencia_fecha_vencimiento__range=[hoy, proximos_30_dias],
            estado='ACTIVO'
        ).count()
        
        return context


class ConductorDetailView(RolRequeridoMixin, DetailView):
    """Detalle de un conductor."""
    model = Conductor
    template_name = 'conductores/conductor_detail.html'
    context_object_name = 'conductor'
    roles_permitidos = CONDUCTORES_VER_ROLES
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conductor = self.object
        context['titulo'] = f'Conductor: {conductor.nombre_completo}'
        context['habilitaciones'] = conductor.habilitaciones.select_related(
            'empresa', 'autorizacion'
        ).order_by('-fecha_inicio')
        context['documentos'] = conductor.documentos.all().order_by('-fecha_subida')[:10]
        
        # Historial de Trámites (Búsqueda exhaustiva)
        from apps.tramites.models import Tramite, ConductorTramite
        
        # Trámites donde es el conductor principal
        tramites_principales = Tramite.objects.filter(conductor=conductor)
        
        # Trámites donde aparece en ConductorTramite (Baja, Habilitación, etc.)
        tramites_secundarios = Tramite.objects.filter(conductores_tramite__conductor_existente=conductor)
        
        # Trámites donde se creó este conductor
        tramites_creacion = Tramite.objects.filter(conductores_tramite__conductor_creado=conductor)
        
        # Trámites por DNI (por si no se vinculó el objeto directamente)
        tramites_por_dni = Tramite.objects.filter(conductores_tramite__dni=conductor.dni)
        
        # Unificar y ordenar
        tramites_ids = set(tramites_principales.values_list('id', flat=True)) | \
                       set(tramites_secundarios.values_list('id', flat=True)) | \
                       set(tramites_creacion.values_list('id', flat=True)) | \
                       set(tramites_por_dni.values_list('id', flat=True))
        
        context['historial_tramites'] = Tramite.objects.filter(id__in=tramites_ids).order_by('-fecha_creacion').distinct()
        
        # Conteo de habilitaciones vigentes
        context['habilitaciones_vigentes_count'] = conductor.habilitaciones.filter(
            estado='VIGENTE'
        ).count()
        
        # Alertas
        hoy = timezone.now().date()
        alertas = []
        if conductor.licencia_fecha_vencimiento:
            if conductor.licencia_fecha_vencimiento < hoy:
                alertas.append('Licencia de conducir vencida')
            elif conductor.licencia_fecha_vencimiento < hoy + timezone.timedelta(days=30):
                alertas.append('Licencia de conducir próxima a vencer')
        
        context['alertas'] = alertas
        return context


class ConductorCreateView(RolRequeridoMixin, CreateView):
    """Crear nuevo conductor."""
    model = Conductor
    form_class = ConductorForm
    template_name = 'conductores/conductor_form.html'
    success_url = reverse_lazy('conductores:lista')
    roles_permitidos = CONDUCTORES_EDIT_ROLES
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Nuevo Conductor'
        context['accion'] = 'Crear'
        return context
    
    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        messages.success(self.request, 'Conductor registrado exitosamente.')
        return super().form_valid(form)


class ConductorUpdateView(RolRequeridoMixin, UpdateView):
    """Editar conductor existente."""
    model = Conductor
    form_class = ConductorForm
    template_name = 'conductores/conductor_form.html'
    roles_permitidos = CONDUCTORES_EDIT_ROLES
    
    def get_success_url(self):
        return reverse_lazy('conductores:detalle', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar: {self.object.nombre_completo}'
        context['accion'] = 'Actualizar'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Conductor actualizado exitosamente.')
        return super().form_valid(form)


class HabilitacionConductorListView(RolRequeridoMixin, ListView):
    """Lista de habilitaciones de conductores."""
    model = HabilitacionConductor
    template_name = 'conductores/habilitacion_list.html'
    context_object_name = 'habilitaciones'
    paginate_by = 20
    roles_permitidos = CONDUCTORES_VER_ROLES
    
    def get_queryset(self):
        queryset = HabilitacionConductor.objects.select_related(
            'conductor', 'empresa', 'autorizacion'
        ).order_by('-fecha_inicio')
        
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Habilitaciones de Conductores'
        context['vigentes'] = HabilitacionConductor.objects.filter(estado='VIGENTE').count()
        return context


class ConductorExportView(RolRequeridoMixin, View):
    """Exportar conductores a Excel."""
    roles_permitidos = CONDUCTORES_EXPORT_ROLES
    
    def get(self, request):
        queryset = Conductor.objects.order_by('apellido_paterno', 'apellido_materno')
        
        # Aplicar filtros
        q = request.GET.get('q')
        estado = request.GET.get('estado')
        
        if q:
            queryset = queryset.filter(
                Q(dni__icontains=q) |
                Q(nombres__icontains=q) |
                Q(apellido_paterno__icontains=q)
            )
        if estado:
            queryset = queryset.filter(estado=estado)
        
        # Preparar datos
        headers = ['DNI', 'Apellido Paterno', 'Apellido Materno', 'Nombres',
                   'Fecha Nacimiento', 'Nº Licencia', 'Categoría',
                   'Fecha Emisión', 'Fecha Vencimiento', 'Estado', 'Teléfono']
        
        data = []
        for c in queryset:
            data.append([
                c.dni,
                c.apellido_paterno,
                c.apellido_materno,
                c.nombres,
                c.fecha_nacimiento.strftime('%d/%m/%Y') if c.fecha_nacimiento else '',
                c.licencia_numero,
                c.get_licencia_categoria_display(),
                c.licencia_fecha_emision.strftime('%d/%m/%Y') if c.licencia_fecha_emision else '',
                c.licencia_fecha_vencimiento.strftime('%d/%m/%Y') if c.licencia_fecha_vencimiento else '',
                c.get_estado_display(),
                c.telefono or ''
            ])
        
        exporter = ExcelExporter('Conductores', headers)
        return exporter.export_to_response(data, 'conductores')
