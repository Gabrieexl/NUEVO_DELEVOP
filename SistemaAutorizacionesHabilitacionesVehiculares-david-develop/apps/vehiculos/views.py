"""
Vistas para la app vehiculos.
"""

from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils import timezone

from .models import Vehiculo, HabilitacionVehicular
from .forms import VehiculoForm, VehiculoBusquedaForm
from apps.usuarios.mixins import RolRequeridoMixin
from utils.constants import Roles
from utils.exports import ExcelExporter

# Roles por acción en vehículos (según matriz acordada).
VEHICULOS_VER_ROLES = [
    Roles.ADMIN_SISTEMA,
    Roles.MESA_PARTES,
    Roles.ESPECIALISTA_TECNICO,
    Roles.ASESORIA_LEGAL,
    Roles.CONSULTA_INTERNA,
    Roles.DIRECTOR_GENERAL,
    Roles.DIRECTOR_ADMINISTRATIVO,
    Roles.CONTROL_CALIDAD,
]
VEHICULOS_EDIT_ROLES = [
    Roles.ADMIN_SISTEMA,
    Roles.ESPECIALISTA_TECNICO,
]
VEHICULOS_EXPORT_ROLES = [
    Roles.ADMIN_SISTEMA,
    Roles.ESPECIALISTA_TECNICO,
    Roles.ASESORIA_LEGAL,
]


class VehiculoListView(RolRequeridoMixin, ListView):
    """Lista de vehículos."""
    model = Vehiculo
    template_name = 'vehiculos/vehiculo_list.html'
    context_object_name = 'vehiculos'
    paginate_by = 20
    roles_permitidos = VEHICULOS_VER_ROLES
    
    def get_queryset(self):
        queryset = Vehiculo.objects.select_related(
            'empresa_propietaria', 'autorizacion_principal'
        ).order_by('-fecha_creacion')
        
        # Filtros de búsqueda
        q = self.request.GET.get('q')
        estado = self.request.GET.get('estado')
        categoria = self.request.GET.get('categoria')
        carroceria = self.request.GET.get('carroceria')
        empresa = self.request.GET.get('empresa')
        
        if q:
            queryset = queryset.filter(
                Q(placa__icontains=q) |
                Q(marca__icontains=q) |
                Q(modelo__icontains=q)
            )
        
        if estado:
            queryset = queryset.filter(estado=estado)
        
        if categoria:
            queryset = queryset.filter(categoria_id=categoria)
        
        if carroceria:
            queryset = queryset.filter(carroceria_id=carroceria)
        
        if empresa:
            queryset = queryset.filter(empresa_propietaria_id=empresa)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Vehículos'
        context['form_busqueda'] = VehiculoBusquedaForm(self.request.GET)
        context['total_vehiculos'] = Vehiculo.objects.count()
        context['habilitados'] = Vehiculo.objects.filter(estado='HABILITADO').count()
        
        # Alertas de documentos por vencer
        hoy = timezone.now().date()
        proximos_30_dias = hoy + timezone.timedelta(days=30)
        context['soat_por_vencer'] = Vehiculo.objects.filter(
            fecha_venc_soat__range=[hoy, proximos_30_dias],
            estado='HABILITADO'
        ).count()
        context['citv_por_vencer'] = Vehiculo.objects.filter(
            fecha_venc_citv__range=[hoy, proximos_30_dias],
            estado='HABILITADO'
        ).count()
        
        # Preparar query_params excluyendo 'page' para paginación correcta
        query_params = self.request.GET.copy()
        query_params.pop('page', None)
        context['query_params'] = query_params.urlencode()
        
        return context


class VehiculoDetailView(RolRequeridoMixin, DetailView):
    """Detalle de un vehículo."""
    model = Vehiculo
    template_name = 'vehiculos/vehiculo_detail.html'
    context_object_name = 'vehiculo'
    roles_permitidos = VEHICULOS_VER_ROLES
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vehiculo = self.object
        context['titulo'] = f'Vehículo: {vehiculo.placa}'
        habilitaciones_por_autorizacion = {}
        habilitaciones_qs = vehiculo.habilitaciones.select_related(
            'autorizacion'
        ).order_by('-fecha_fin', '-fecha_inicio', '-id')

        for habilitacion in habilitaciones_qs:
            if habilitacion.autorizacion_id not in habilitaciones_por_autorizacion:
                habilitacion.estado_mostrar = habilitacion.estado
                if vehiculo.estado != 'HABILITADO' and habilitacion.estado == 'VIGENTE':
                    habilitacion.estado_mostrar = 'BAJA'
                habilitaciones_por_autorizacion[habilitacion.autorizacion_id] = habilitacion

        context['habilitaciones'] = list(habilitaciones_por_autorizacion.values())
        context['documentos'] = vehiculo.documentos.all().order_by('-fecha_subida')[:10]
        
        # Historial de Trámites (Búsqueda exhaustiva)
        from apps.tramites.models import Tramite, VehiculoTramite
        
        # Trámites donde es el vehículo principal
        tramites_principales = Tramite.objects.filter(vehiculo=vehiculo)
        
        # Trámites donde aparece en VehiculoTramite (Baja, Sustitución, etc.)
        tramites_secundarios = Tramite.objects.filter(vehiculos_tramite__vehiculo_existente=vehiculo)
        
        # Trámites de incremento donde se creó este vehículo
        tramites_creacion = Tramite.objects.filter(vehiculos_tramite__vehiculo_creado=vehiculo)
        
        # Trámites de incremento donde se usó su placa (por si no se vinculó el objeto directamente)
        tramites_por_placa = Tramite.objects.filter(vehiculos_tramite__placa_nueva=vehiculo.placa)
        
        # Unificar y ordenar
        tramites_ids = set(tramites_principales.values_list('id', flat=True)) | \
                       set(tramites_secundarios.values_list('id', flat=True)) | \
                       set(tramites_creacion.values_list('id', flat=True)) | \
                       set(tramites_por_placa.values_list('id', flat=True))
        
        context['historial_tramites'] = Tramite.objects.filter(id__in=tramites_ids).order_by('-fecha_creacion').distinct()
        
        # Alertas
        hoy = timezone.now().date()
        alertas = []
        if vehiculo.fecha_venc_soat and vehiculo.fecha_venc_soat < hoy:
            alertas.append('SOAT vencido')
        elif vehiculo.fecha_venc_soat and vehiculo.fecha_venc_soat < hoy + timezone.timedelta(days=30):
            alertas.append('SOAT próximo a vencer')
        
        if vehiculo.fecha_venc_citv and vehiculo.fecha_venc_citv < hoy:
            alertas.append('CITV vencida')
        elif vehiculo.fecha_venc_citv and vehiculo.fecha_venc_citv < hoy + timezone.timedelta(days=30):
            alertas.append('CITV próxima a vencer')
        
        context['alertas'] = alertas
        return context


class VehiculoCreateView(RolRequeridoMixin, CreateView):
    """Crear nuevo vehículo."""
    model = Vehiculo
    form_class = VehiculoForm
    template_name = 'vehiculos/vehiculo_form.html'
    success_url = reverse_lazy('vehiculos:lista')
    roles_permitidos = VEHICULOS_EDIT_ROLES
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Nuevo Vehículo'
        context['accion'] = 'Crear'
        return context
    
    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        messages.success(self.request, 'Vehículo registrado exitosamente.')
        return super().form_valid(form)


class VehiculoUpdateView(RolRequeridoMixin, UpdateView):
    """Editar vehículo existente."""
    model = Vehiculo
    form_class = VehiculoForm
    template_name = 'vehiculos/vehiculo_form.html'
    roles_permitidos = VEHICULOS_EDIT_ROLES
    
    def get_success_url(self):
        return reverse_lazy('vehiculos:detalle', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar: {self.object.placa}'
        context['accion'] = 'Actualizar'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Vehículo actualizado exitosamente.')
        return super().form_valid(form)


class HabilitacionVehicularListView(RolRequeridoMixin, ListView):
    """Lista de habilitaciones vehiculares."""
    model = HabilitacionVehicular
    template_name = 'vehiculos/habilitacion_list.html'
    context_object_name = 'habilitaciones'
    paginate_by = 20
    roles_permitidos = VEHICULOS_VER_ROLES
    
    def get_queryset(self):
        queryset = HabilitacionVehicular.objects.select_related(
            'vehiculo', 'autorizacion', 'autorizacion__empresa'
        ).order_by('-fecha_inicio')
        
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Habilitación Vehicular'
        context['vigentes'] = HabilitacionVehicular.objects.filter(estado='VIGENTE').count()
        return context


class VehiculoExportView(RolRequeridoMixin, View):
    """Exportar vehículos a Excel."""
    roles_permitidos = VEHICULOS_EXPORT_ROLES
    
    def get(self, request):
        queryset = Vehiculo.objects.select_related(
            'empresa_propietaria', 'autorizacion_principal'
        ).order_by('placa')
        
        # Aplicar filtros
        q = request.GET.get('q')
        estado = request.GET.get('estado')
        empresa = request.GET.get('empresa')
        
        if q:
            queryset = queryset.filter(
                Q(placa__icontains=q) |
                Q(marca__icontains=q)
            )
        if estado:
            queryset = queryset.filter(estado=estado)
        if empresa:
            queryset = queryset.filter(empresa_propietaria_id=empresa)
        
        # Preparar datos
        headers = ['Placa', 'Marca', 'Modelo', 'Año', 'Tipo', 'Capacidad',
                   'Empresa', 'Estado', 'Nº TUC', 'Nº TIV', 'Venc. SOAT', 'Venc. CITV']
        
        data = []
        for v in queryset:
            data.append([
                v.placa,
                v.marca,
                v.modelo,
                v.anio_fabricacion,
                v.carroceria.nombre if v.carroceria else '',
                v.capacidad_sentados,
                v.empresa_propietaria.razon_social if v.empresa_propietaria else '',
                v.get_estado_display(),
                v.numero_tuc_vigente or '',
                v.numero_tiv or '',
                v.fecha_venc_soat.strftime('%d/%m/%Y') if v.fecha_venc_soat else '',
                v.fecha_venc_citv.strftime('%d/%m/%Y') if v.fecha_venc_citv else ''
            ])
        
        exporter = ExcelExporter('Vehículos', headers)
        return exporter.export_to_response(data, 'vehiculos')

