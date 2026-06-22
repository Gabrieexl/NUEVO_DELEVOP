"""
Vistas para la app autorizaciones.
"""

from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q

from .models import Autorizacion, HistorialAutorizacion
from .forms import AutorizacionForm, AutorizacionBusquedaForm
from apps.usuarios.mixins import RolRequeridoMixin
from utils.constants import Roles
from utils.exports import ExcelExporter

# Roles por acción en autorizaciones (según matriz acordada).
AUTORIZACIONES_VER_ROLES = [
    Roles.ADMIN_SISTEMA,
    Roles.MESA_PARTES,
    Roles.ESPECIALISTA_TECNICO,
    Roles.ASESORIA_LEGAL,
    Roles.CONSULTA_INTERNA,
    Roles.DIRECTOR_GENERAL,
    Roles.DIRECTOR_ADMINISTRATIVO,
    Roles.CONTROL_CALIDAD,
]
AUTORIZACIONES_EDIT_ROLES = [
    Roles.ADMIN_SISTEMA,
]
AUTORIZACIONES_EXPORT_ROLES = [
    Roles.ADMIN_SISTEMA,
    Roles.ESPECIALISTA_TECNICO,
    Roles.ASESORIA_LEGAL,
]


class AutorizacionListView(RolRequeridoMixin, ListView):
    """Lista de autorizaciones."""
    model = Autorizacion
    template_name = 'autorizaciones/autorizacion_list.html'
    context_object_name = 'autorizaciones'
    paginate_by = 20
    roles_permitidos = AUTORIZACIONES_VER_ROLES
    
    def get_queryset(self):
        queryset = Autorizacion.objects.select_related('empresa').order_by('-fecha_creacion')
        
        # Filtros de búsqueda
        q = self.request.GET.get('q')
        estado = self.request.GET.get('estado')
        tipo_servicio = self.request.GET.get('tipo_servicio')
        
        if q:
            queryset = queryset.filter(
                Q(numero_resolucion__icontains=q) |
                Q(empresa__razon_social__icontains=q) |
                Q(empresa__ruc__icontains=q) |
                Q(ambito__icontains=q)
            )
        
        if estado:
            queryset = queryset.filter(estado=estado)
        
        if tipo_servicio:
            queryset = queryset.filter(tipo_servicio=tipo_servicio)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Autorizaciones'
        context['form_busqueda'] = AutorizacionBusquedaForm(self.request.GET)
        context['total_autorizaciones'] = Autorizacion.objects.count()
        context['vigentes'] = Autorizacion.objects.filter(estado='VIGENTE').count()
        # Preparar query_params excluyendo 'page' para paginación correcta
        query_params = self.request.GET.copy()
        query_params.pop('page', None)
        context['query_params'] = query_params.urlencode()
        return context


class AutorizacionDetailView(RolRequeridoMixin, DetailView):
    """Detalle de una autorización."""
    model = Autorizacion
    template_name = 'autorizaciones/autorizacion_detail.html'
    context_object_name = 'autorizacion'
    roles_permitidos = AUTORIZACIONES_VER_ROLES
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        autorizacion = self.object
        context['titulo'] = f'Autorización: {autorizacion.numero_resolucion}'

        # Mostrar una única fila por vehículo (la habilitación más reciente)
        # para evitar duplicados visuales cuando hay historial de cambios
        # de estado (p. ej. VIGENTE -> BAJA -> VIGENTE).

        habilitaciones_por_placa = {}
        habilitaciones_qs = autorizacion.habilitaciones_vehiculares.select_related(
            'vehiculo'
        ).order_by('vehiculo__placa', '-fecha_creacion', '-fecha_inicio', '-id')

        for habilitacion in habilitaciones_qs:
            placa = (habilitacion.vehiculo.placa or '').upper().replace('-', '').replace(' ', '')
            if placa not in habilitaciones_por_placa:
                habilitaciones_por_placa[placa] = habilitacion

        context['habilitaciones_vehiculares'] = list(habilitaciones_por_placa.values())
        context['habilitaciones_conductores'] = autorizacion.habilitaciones_conductores.all()[:20]
        context['historial'] = HistorialAutorizacion.objects.filter(
            autorizacion=autorizacion
        ).order_by('-fecha')[:20]
        
        # Historial de Trámites Completo
        from apps.tramites.models import Tramite
        context['historial_tramites'] = Tramite.objects.filter(
            autorizacion=autorizacion
        ).order_by('-fecha_creacion')
        
        return context


class AutorizacionCreateView(RolRequeridoMixin, CreateView):
    """Crear nueva autorización."""
    model = Autorizacion
    form_class = AutorizacionForm
    template_name = 'autorizaciones/autorizacion_form.html'
    success_url = reverse_lazy('autorizaciones:lista')
    roles_permitidos = AUTORIZACIONES_EDIT_ROLES
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Nueva Autorización'
        context['accion'] = 'Crear'
        return context
    
    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        messages.success(self.request, 'Autorización creada exitosamente.')
        return super().form_valid(form)


class AutorizacionUpdateView(RolRequeridoMixin, UpdateView):
    """Editar autorización existente."""
    model = Autorizacion
    form_class = AutorizacionForm
    template_name = 'autorizaciones/autorizacion_form.html'
    roles_permitidos = AUTORIZACIONES_EDIT_ROLES
    
    def get_success_url(self):
        return reverse_lazy('autorizaciones:detalle', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar: {self.object.numero_resolucion}'
        context['accion'] = 'Actualizar'
        return context
    
    def form_valid(self, form):
        # Registrar en historial si hay cambios importantes
        autorizacion = self.get_object()
        cambios = []
        
        for field in form.changed_data:
            valor_anterior = getattr(autorizacion, field)
            valor_nuevo = form.cleaned_data.get(field)
            if str(valor_anterior) != str(valor_nuevo):
                cambios.append(f"{field}: {valor_anterior} -> {valor_nuevo}")
        
        if cambios:
            HistorialAutorizacion.objects.create(
                autorizacion=autorizacion,
                campo_modificado=', '.join(form.changed_data),
                valor_anterior=str(cambios),
                valor_nuevo='Ver formulario',
                usuario=self.request.user,
                motivo='Actualización desde formulario'
            )
        
        messages.success(self.request, 'Autorización actualizada exitosamente.')
        return super().form_valid(form)


class AutorizacionExportView(RolRequeridoMixin, View):
    """Exportar autorizaciones a Excel."""
    roles_permitidos = AUTORIZACIONES_EXPORT_ROLES
    
    def get(self, request):
        queryset = Autorizacion.objects.select_related('empresa').order_by('-fecha_resolucion')
        
        # Aplicar filtros
        q = request.GET.get('q')
        estado = request.GET.get('estado')
        
        if q:
            queryset = queryset.filter(
                Q(numero_resolucion__icontains=q) |
                Q(empresa__razon_social__icontains=q)
            )
        if estado:
            queryset = queryset.filter(estado=estado)
        
        # Preparar datos
        headers = ['Nº Resolución', 'Fecha Resolución', 'Empresa', 'RUC',
                   'Tipo Servicio', 'Ámbito', 'Fecha Inicio', 'Fecha Fin',
                   'Estado', 'Rutas']
        
        data = []
        for aut in queryset:
            data.append([
                aut.numero_resolucion,
                aut.fecha_resolucion.strftime('%d/%m/%Y') if aut.fecha_resolucion else '',
                aut.empresa.razon_social if aut.empresa else '',
                aut.empresa.ruc if aut.empresa else '',
                aut.tipo_servicio.nombre if aut.tipo_servicio else '',
                aut.get_ambito_display(),
                aut.fecha_inicio_vigencia.strftime('%d/%m/%Y') if aut.fecha_inicio_vigencia else '',
                aut.fecha_fin_vigencia.strftime('%d/%m/%Y') if aut.fecha_fin_vigencia else '',
                aut.get_estado_display(),
                aut.descripcion_rutas[:100] + '...' if len(aut.descripcion_rutas) > 100 else aut.descripcion_rutas
            ])
        
        exporter = ExcelExporter('Autorizaciones', headers)
        return exporter.export_to_response(data, 'autorizaciones')
