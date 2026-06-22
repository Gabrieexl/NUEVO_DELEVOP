"""
Vistas para la app empresas.
"""

from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.http import HttpResponse

from .models import EmpresaTransporte
from .forms import EmpresaTransporteForm, EmpresaBusquedaForm
from apps.usuarios.mixins import RolRequeridoMixin
from utils.constants import Roles
from utils.exports import ExcelExporter

# Roles por acción en empresas (según matriz acordada).
EMPRESAS_VER_ROLES = [
    Roles.ADMIN_SISTEMA,
    Roles.MESA_PARTES,
    Roles.ESPECIALISTA_TECNICO,
    Roles.ASESORIA_LEGAL,
    Roles.CONSULTA_INTERNA,
    Roles.DIRECTOR_ADMINISTRATIVO,
    Roles.DIRECTOR_GENERAL,
    Roles.CONTROL_CALIDAD,
]
EMPRESAS_EDIT_ROLES = [
    Roles.ADMIN_SISTEMA,
    Roles.MESA_PARTES,
]
EMPRESAS_EXPORT_ROLES = [
    Roles.ADMIN_SISTEMA,
    Roles.ESPECIALISTA_TECNICO,
    Roles.ASESORIA_LEGAL,
]


class EmpresaListView(RolRequeridoMixin, ListView):
    """Lista de empresas de transporte."""
    model = EmpresaTransporte
    template_name = 'empresas/empresa_list.html'
    context_object_name = 'empresas'
    paginate_by = 20
    roles_permitidos = EMPRESAS_VER_ROLES
    
    def get_queryset(self):
        queryset = EmpresaTransporte.objects.annotate(
            num_autorizaciones=Count('autorizaciones', distinct=True),
            num_vehiculos=Count('vehiculos', distinct=True),
            num_conductores=Count('conductores', distinct=True)
        ).order_by('-fecha_creacion')
        
        # Filtros de búsqueda
        q = self.request.GET.get('q')
        estado = self.request.GET.get('estado')
        
        if q:
            queryset = queryset.filter(
                Q(ruc__icontains=q) |
                Q(razon_social__icontains=q) |
                Q(nombre_comercial__icontains=q)
            )
        
        if estado:
            queryset = queryset.filter(estado=estado)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Empresas de Transporte'
        context['form_busqueda'] = EmpresaBusquedaForm(self.request.GET)
        context['total_empresas'] = EmpresaTransporte.objects.count()
        # Variables para filtros en template (evitar DEBUG exceptions)
        context['q'] = self.request.GET.get('q', '')
        context['estado'] = self.request.GET.get('estado', '')
        # Preparar query_params excluyendo 'page' para paginación correcta
        query_dict = self.request.GET.copy()
        query_dict.pop('page', None)
        context['query_params'] = query_dict.urlencode()
        return context


class EmpresaDetailView(RolRequeridoMixin, DetailView):
    """Detalle de una empresa."""
    model = EmpresaTransporte
    template_name = 'empresas/empresa_detail.html'
    context_object_name = 'empresa'
    roles_permitidos = EMPRESAS_VER_ROLES
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = self.object
        context['titulo'] = f'Empresa: {empresa.razon_social}'
        context['autorizaciones'] = empresa.autorizaciones.all()[:10]
        context['vehiculos'] = empresa.vehiculos.all()[:10]
        context['tramites'] = empresa.tramites.all().order_by('-fecha_creacion')[:10]
        return context


class EmpresaCreateView(RolRequeridoMixin, CreateView):
    """Crear nueva empresa."""
    model = EmpresaTransporte
    form_class = EmpresaTransporteForm
    template_name = 'empresas/empresa_form.html'
    success_url = reverse_lazy('empresas:lista')
    roles_permitidos = EMPRESAS_EDIT_ROLES
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Nueva Empresa de Transporte'
        context['accion'] = 'Crear'
        return context
    
    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        messages.success(self.request, 'Empresa creada exitosamente.')
        return super().form_valid(form)


class EmpresaUpdateView(RolRequeridoMixin, UpdateView):
    """Editar empresa existente."""
    model = EmpresaTransporte
    form_class = EmpresaTransporteForm
    template_name = 'empresas/empresa_form.html'
    roles_permitidos = EMPRESAS_EDIT_ROLES
    
    def get_success_url(self):
        return reverse_lazy('empresas:detalle', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar: {self.object.razon_social}'
        context['accion'] = 'Actualizar'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Empresa actualizada exitosamente.')
        return super().form_valid(form)


class EmpresaExportView(RolRequeridoMixin, View):
    """Exportar empresas a Excel."""
    roles_permitidos = EMPRESAS_EXPORT_ROLES
    
    def get(self, request):
        queryset = EmpresaTransporte.objects.all().order_by('razon_social')
        
        # Aplicar filtros si existen
        q = request.GET.get('q')
        estado = request.GET.get('estado')
        
        if q:
            queryset = queryset.filter(
                Q(ruc__icontains=q) |
                Q(razon_social__icontains=q)
            )
        if estado:
            queryset = queryset.filter(estado=estado)
        
        # Preparar datos
        headers = ['RUC', 'Razón Social', 'Nombre Comercial', 'Domicilio', 
                   'Representante Legal', 'DNI Representante', 'Teléfono', 
                   'Email', 'Estado', 'Fecha Registro']
        
        data = []
        for empresa in queryset:
            data.append([
                empresa.ruc,
                empresa.razon_social,
                empresa.nombre_comercial or '',
                empresa.domicilio_fiscal,
                empresa.representante_legal,
                empresa.dni_representante,
                empresa.telefono or '',
                empresa.email or '',
                empresa.get_estado_display(),
                empresa.fecha_creacion.strftime('%d/%m/%Y') if empresa.fecha_creacion else ''
            ])
        
        exporter = ExcelExporter('Empresas de Transporte', headers)
        return exporter.export_to_response(data, 'empresas_transporte')
