"""
Vistas para la app configuracion.
"""

from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, View
)
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q
from django.template.loader import render_to_string

from apps.usuarios.mixins import RolRequeridoMixin
from utils.constants import Roles
from .models import Ruta, Frecuencia, TipoServicio, Carroceria, CategoriaVehiculo
from .forms import RutaForm, FrecuenciaForm, TipoServicioForm, CarroceriaForm
from django.http import JsonResponse

# Roles para endpoints de configuración usados en formularios.
CONFIGURACION_CARROCERIA_ROLES = [
    Roles.ADMIN_SISTEMA,
    Roles.ESPECIALISTA_TECNICO,
]


class GetCarroceriasView(View):
    """Retorna carrocerías filtradas por categoría en formato JSON (sin restricción de roles para uso en formularios)."""
    def get(self, request, *args, **kwargs):
        categoria_id = request.GET.get('categoria_id')
        if not categoria_id:
            return JsonResponse([], safe=False)
        
        carrocerias = Carroceria.objects.filter(
            categoria_id=categoria_id, 
            activo=True
        ).values('id', 'nombre')
        
        return JsonResponse(list(carrocerias), safe=False)


class ConfiguracionHomeView(RolRequeridoMixin, TemplateView):
    """Vista principal de configuración."""
    template_name = 'configuracion/home.html'
    roles_permitidos = [Roles.ADMIN_SISTEMA]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Configuración del Sistema'
        context['total_rutas'] = Ruta.objects.count()
        context['rutas_activas'] = Ruta.objects.filter(activo=True).count()
        context['total_frecuencias'] = Frecuencia.objects.count()
        context['frecuencias_activas'] = Frecuencia.objects.filter(activo=True).count()
        context['total_tipos_servicio'] = TipoServicio.objects.count()
        context['tipos_servicio_activos'] = TipoServicio.objects.filter(activo=True).count()
        context['total_carrocerias'] = Carroceria.objects.count()
        context['carrocerias_activas'] = Carroceria.objects.filter(activo=True).count()
        return context


# ============== TIPOS DE SERVICIO ==============

class TipoServicioListView(RolRequeridoMixin, ListView):
    """Lista de tipos de servicio."""
    model = TipoServicio
    template_name = 'configuracion/tiposervicio_list.html'
    context_object_name = 'tipos_servicio'
    paginate_by = 20
    roles_permitidos = [Roles.ADMIN_SISTEMA]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q', '')
        activo = self.request.GET.get('activo', '')
        
        if q:
            queryset = queryset.filter(
                Q(codigo__icontains=q) |
                Q(nombre__icontains=q)
            )
        if activo:
            queryset = queryset.filter(activo=(activo == 'true'))
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Tipos de Servicio'
        context['q'] = self.request.GET.get('q', '')
        context['activo'] = self.request.GET.get('activo', '')
        return context


class TipoServicioCreateView(RolRequeridoMixin, CreateView):
    """Crear tipo de servicio."""
    model = TipoServicio
    form_class = TipoServicioForm
    template_name = 'configuracion/tiposervicio_form.html'
    success_url = reverse_lazy('configuracion:tiposervicio_lista')
    roles_permitidos = [Roles.ADMIN_SISTEMA]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Nuevo Tipo de Servicio'
        context['accion'] = 'Crear'
        return context
    
    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        messages.success(self.request, 'Tipo de servicio creado exitosamente.')
        return super().form_valid(form)


class TipoServicioUpdateView(RolRequeridoMixin, UpdateView):
    """Editar tipo de servicio."""
    model = TipoServicio
    form_class = TipoServicioForm
    template_name = 'configuracion/tiposervicio_form.html'
    roles_permitidos = [Roles.ADMIN_SISTEMA]
    
    def get_success_url(self):
        return reverse_lazy('configuracion:tiposervicio_lista')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Tipo de Servicio: {self.object.nombre}'
        context['accion'] = 'Actualizar'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Tipo de servicio actualizado exitosamente.')
        return super().form_valid(form)


class TipoServicioDeleteView(RolRequeridoMixin, DeleteView):
    """Eliminar tipo de servicio."""
    model = TipoServicio
    template_name = 'configuracion/tiposervicio_confirm_delete.html'
    success_url = reverse_lazy('configuracion:tiposervicio_lista')
    roles_permitidos = [Roles.ADMIN_SISTEMA]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Tipo de Servicio: {self.object.nombre}'
        return context
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Tipo de servicio eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)


# ============== CARROCERÍAS ==============

class CarroceriaListView(RolRequeridoMixin, ListView):
    """Lista de carrocerías."""
    model = Carroceria
    template_name = 'configuracion/carroceria_list.html'
    context_object_name = 'carrocerias'
    paginate_by = 20
    roles_permitidos = [Roles.ADMIN_SISTEMA]
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('categoria')
        q = self.request.GET.get('q', '')
        activo = self.request.GET.get('activo', '')
        categoria = self.request.GET.get('categoria', '')
        
        if q:
            queryset = queryset.filter(
                Q(codigo__icontains=q) |
                Q(nombre__icontains=q)
            )
        if activo:
            queryset = queryset.filter(activo=(activo == 'true'))
        if categoria:
            queryset = queryset.filter(categoria_id=categoria)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Carrocerías'
        context['q'] = self.request.GET.get('q', '')
        context['activo'] = self.request.GET.get('activo', '')
        context['categorias'] = CategoriaVehiculo.objects.filter(activo=True)
        return context


class CarroceriaCreateView(RolRequeridoMixin, CreateView):
    """Crear carrocería."""
    model = Carroceria
    form_class = CarroceriaForm
    template_name = 'configuracion/carroceria_form.html'
    success_url = reverse_lazy('configuracion:carroceria_lista')
    roles_permitidos = [Roles.ADMIN_SISTEMA]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Nueva Carrocería'
        context['accion'] = 'Crear'
        return context
    
    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        messages.success(self.request, 'Carrocería creada exitosamente.')
        return super().form_valid(form)


class CarroceriaUpdateView(RolRequeridoMixin, UpdateView):
    """Editar carrocería."""
    model = Carroceria
    form_class = CarroceriaForm
    template_name = 'configuracion/carroceria_form.html'
    roles_permitidos = [Roles.ADMIN_SISTEMA]
    
    def get_success_url(self):
        return reverse_lazy('configuracion:carroceria_lista')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Carrocería: {self.object.nombre}'
        context['accion'] = 'Actualizar'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Carrocería actualizada exitosamente.')
        return super().form_valid(form)


class CarroceriaDeleteView(RolRequeridoMixin, DeleteView):
    """Eliminar carrocería."""
    model = Carroceria
    template_name = 'configuracion/carroceria_confirm_delete.html'
    success_url = reverse_lazy('configuracion:carroceria_lista')
    roles_permitidos = [Roles.ADMIN_SISTEMA]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Carrocería: {self.object.nombre}'
        return context
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Carrocería eliminada exitosamente.')
        return super().delete(request, *args, **kwargs)


# ============== RUTAS ==============

class RutaListView(RolRequeridoMixin, ListView):
    """Lista de rutas."""
    model = Ruta
    template_name = 'configuracion/ruta_list.html'
    context_object_name = 'rutas'
    paginate_by = 20
    roles_permitidos = [Roles.ADMIN_SISTEMA]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q', '')
        activo = self.request.GET.get('activo', '')
        
        if q:
            queryset = queryset.filter(
                Q(codigo__icontains=q) |
                Q(nombre__icontains=q) |
                Q(origen__icontains=q) |
                Q(destino__icontains=q)
            )
        if activo:
            queryset = queryset.filter(activo=(activo == 'true'))
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Rutas de Transporte'
        query_params = self.request.GET.copy()
        query_params.pop('page', None)
        # Variables para filtros en template (evitar DEBUG exceptions)
        context['q'] = self.request.GET.get('q', '')
        context['activo'] = self.request.GET.get('activo', '')
        context['query_params'] = query_params.urlencode()
        return context


class RutaDetailView(RolRequeridoMixin, DetailView):
    """Detalle de ruta."""
    model = Ruta
    template_name = 'configuracion/ruta_detail.html'
    context_object_name = 'ruta'
    roles_permitidos = [Roles.ADMIN_SISTEMA]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Ruta: {self.object.codigo}'
        # Mostrar autorizaciones que usan esta ruta
        context['autorizaciones'] = self.object.autorizaciones.all()[:10]
        return context


class RutaCreateView(RolRequeridoMixin, CreateView):
    """Crear ruta."""
    model = Ruta
    form_class = RutaForm
    template_name = 'configuracion/ruta_form.html'
    success_url = reverse_lazy('configuracion:rutas_lista')
    roles_permitidos = [Roles.ADMIN_SISTEMA]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Nueva Ruta'
        context['accion'] = 'Crear'
        context['is_modal'] = self.request.headers.get('x-requested-with') == 'XMLHttpRequest'
        return context
    
    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        response = super().form_valid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string(self.template_name, self.get_context_data(form=form), request=self.request)
            return JsonResponse({
                'success': True,
                'message': 'Ruta creada correctamente.',
                'html': html,
                'item': {
                    'id': self.object.pk,
                    'label': f'{self.object.codigo} - {self.object.nombre}',
                    'type': 'ruta',
                    'detail_url': reverse_lazy('configuracion:rutas_detalle', kwargs={'pk': self.object.pk}),
                    'edit_url': reverse_lazy('configuracion:rutas_editar', kwargs={'pk': self.object.pk}),
                },
            })
        messages.success(self.request, 'Ruta creada exitosamente.')
        return response

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string(self.template_name, self.get_context_data(form=form), request=self.request)
            return JsonResponse({'success': False, 'html': html})
        return super().form_invalid(form)


class RutaUpdateView(RolRequeridoMixin, UpdateView):
    """Editar ruta."""
    model = Ruta
    form_class = RutaForm
    template_name = 'configuracion/ruta_form.html'
    roles_permitidos = [Roles.ADMIN_SISTEMA]
    
    def get_success_url(self):
        return reverse_lazy('configuracion:rutas_detalle', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Ruta: {self.object.codigo}'
        context['accion'] = 'Actualizar'
        # Indica si el formulario se renderiza dentro de un modal (AJAX).
        context['is_modal'] = self.request.headers.get('x-requested-with') == 'XMLHttpRequest'
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string(self.template_name, self.get_context_data(form=form), request=self.request)
            return JsonResponse({
                'success': True,
                'message': 'Ruta actualizada correctamente.',
                'html': html,
            })
        messages.success(self.request, 'Ruta actualizada exitosamente.')
        return response

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string(self.template_name, self.get_context_data(form=form), request=self.request)
            return JsonResponse({'success': False, 'html': html})
        return super().form_invalid(form)


class RutaDeleteView(RolRequeridoMixin, DeleteView):
    """Eliminar ruta."""
    model = Ruta
    template_name = 'configuracion/ruta_confirm_delete.html'
    success_url = reverse_lazy('configuracion:rutas_lista')
    roles_permitidos = [Roles.ADMIN_SISTEMA]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Ruta: {self.object.codigo}'
        return context
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Ruta eliminada exitosamente.')
        return super().delete(request, *args, **kwargs)


# ============== FRECUENCIAS ==============

class FrecuenciaListView(RolRequeridoMixin, ListView):
    """Lista de frecuencias."""
    model = Frecuencia
    template_name = 'configuracion/frecuencia_list.html'
    context_object_name = 'frecuencias'
    paginate_by = 20
    roles_permitidos = [Roles.ADMIN_SISTEMA]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q', '')
        activo = self.request.GET.get('activo', '')
        
        if q:
            queryset = queryset.filter(
                Q(codigo__icontains=q) |
                Q(nombre__icontains=q)
            )
        if activo:
            queryset = queryset.filter(activo=(activo == 'true'))
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Frecuencias de Servicio'
        query_params = self.request.GET.copy()
        query_params.pop('page', None)
        # Variables para filtros en template (evitar DEBUG exceptions)
        context['q'] = self.request.GET.get('q', '')
        context['activo'] = self.request.GET.get('activo', '')
        context['query_params'] = query_params.urlencode()
        return context


class FrecuenciaDetailView(RolRequeridoMixin, DetailView):
    """Detalle de frecuencia."""
    model = Frecuencia
    template_name = 'configuracion/frecuencia_detail.html'
    context_object_name = 'frecuencia'
    roles_permitidos = [Roles.ADMIN_SISTEMA]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Frecuencia: {self.object.codigo}'
        context['autorizaciones'] = self.object.autorizaciones.all()[:10]
        return context


class FrecuenciaCreateView(RolRequeridoMixin, CreateView):
    """Crear frecuencia."""
    model = Frecuencia
    form_class = FrecuenciaForm
    template_name = 'configuracion/frecuencia_form.html'
    success_url = reverse_lazy('configuracion:frecuencias_lista')
    roles_permitidos = [Roles.ADMIN_SISTEMA]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Nueva Frecuencia'
        context['accion'] = 'Crear'
        context['is_modal'] = self.request.headers.get('x-requested-with') == 'XMLHttpRequest'
        return context
    
    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        response = super().form_valid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string(self.template_name, self.get_context_data(form=form), request=self.request)
            return JsonResponse({
                'success': True,
                'message': 'Frecuencia creada correctamente.',
                'html': html,
                'item': {
                    'id': self.object.pk,
                    'label': f'{self.object.codigo} - {self.object.nombre}',
                    'type': 'frecuencia',
                    'detail_url': reverse_lazy('configuracion:frecuencias_detalle', kwargs={'pk': self.object.pk}),
                    'edit_url': reverse_lazy('configuracion:frecuencias_editar', kwargs={'pk': self.object.pk}),
                },
            })
        messages.success(self.request, 'Frecuencia creada exitosamente.')
        return response

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string(self.template_name, self.get_context_data(form=form), request=self.request)
            return JsonResponse({'success': False, 'html': html})
        return super().form_invalid(form)


class FrecuenciaUpdateView(RolRequeridoMixin, UpdateView):
    """Editar frecuencia."""
    model = Frecuencia
    form_class = FrecuenciaForm
    template_name = 'configuracion/frecuencia_form.html'
    roles_permitidos = [Roles.ADMIN_SISTEMA]
    
    def get_success_url(self):
        return reverse_lazy('configuracion:frecuencias_detalle', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Frecuencia: {self.object.codigo}'
        context['accion'] = 'Actualizar'
        # Indica si el formulario se renderiza dentro de un modal (AJAX).
        context['is_modal'] = self.request.headers.get('x-requested-with') == 'XMLHttpRequest'
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string(self.template_name, self.get_context_data(form=form), request=self.request)
            return JsonResponse({
                'success': True,
                'message': 'Frecuencia actualizada correctamente.',
                'html': html,
            })
        messages.success(self.request, 'Frecuencia actualizada exitosamente.')
        return response

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string(self.template_name, self.get_context_data(form=form), request=self.request)
            return JsonResponse({'success': False, 'html': html})
        return super().form_invalid(form)


class FrecuenciaDeleteView(RolRequeridoMixin, DeleteView):
    """Eliminar frecuencia."""
    model = Frecuencia
    template_name = 'configuracion/frecuencia_confirm_delete.html'
    success_url = reverse_lazy('configuracion:frecuencias_lista')
    roles_permitidos = [Roles.ADMIN_SISTEMA]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Frecuencia: {self.object.codigo}'
        return context
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Frecuencia eliminada exitosamente.')
        return super().delete(request, *args, **kwargs)


# ============== ENDPOINTS PARA MODAL (AJAX) ==============

class RutaCreateModalView(RolRequeridoMixin, CreateView):
    """Crear ruta desde modal (retorna solo formulario, sin estructura)."""
    model = Ruta
    form_class = RutaForm
    template_name = 'configuracion/ruta_form_modal.html'
    roles_permitidos = [
        Roles.ADMIN_SISTEMA,
        Roles.MESA_PARTES,
        Roles.ESPECIALISTA_TECNICO,
        Roles.ASESORIA_LEGAL,
        Roles.DIRECTOR_GENERAL,
        Roles.DIRECTOR_ADMINISTRATIVO,
    ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['accion'] = 'Crear'
        return context
    
    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        self.object = form.save()  # Guardar directamente sin intentar redirección
        html = render_to_string(self.template_name, self.get_context_data(form=form), request=self.request)
        return JsonResponse({
            'success': True,
            'message': 'Ruta creada correctamente.',
            'html': html,
            'item': {
                'id': self.object.pk,
                'label': f'{self.object.codigo} - {self.object.nombre}',
                'type': 'ruta',
                'detail_url': reverse_lazy('configuracion:rutas_detalle', kwargs={'pk': self.object.pk}),
                'edit_url': reverse_lazy('configuracion:rutas_editar', kwargs={'pk': self.object.pk}),
            },
        })

    def form_invalid(self, form):
        html = render_to_string(self.template_name, self.get_context_data(form=form), request=self.request)
        return JsonResponse({'success': False, 'html': html})


class FrecuenciaCreateModalView(RolRequeridoMixin, CreateView):
    """Crear frecuencia desde modal (retorna solo formulario, sin estructura)."""
    model = Frecuencia
    form_class = FrecuenciaForm
    template_name = 'configuracion/frecuencia_form_modal.html'
    roles_permitidos = [
        Roles.ADMIN_SISTEMA,
        Roles.MESA_PARTES,
        Roles.ESPECIALISTA_TECNICO,
        Roles.ASESORIA_LEGAL,
        Roles.DIRECTOR_GENERAL,
        Roles.DIRECTOR_ADMINISTRATIVO,
    ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['accion'] = 'Crear'
        return context
    
    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        self.object = form.save()  # Guardar directamente sin intentar redirección
        html = render_to_string(self.template_name, self.get_context_data(form=form), request=self.request)
        return JsonResponse({
            'success': True,
            'message': 'Frecuencia creada correctamente.',
            'html': html,
            'item': {
                'id': self.object.pk,
                'label': f'{self.object.codigo} - {self.object.nombre}',
                'type': 'frecuencia',
                'detail_url': reverse_lazy('configuracion:frecuencias_detalle', kwargs={'pk': self.object.pk}),
                'edit_url': reverse_lazy('configuracion:frecuencias_editar', kwargs={'pk': self.object.pk}),
            },
        })

    def form_invalid(self, form):
        html = render_to_string(self.template_name, self.get_context_data(form=form), request=self.request)
        return JsonResponse({'success': False, 'html': html})


class RutaUpdateModalView(RolRequeridoMixin, UpdateView):
    """Editar ruta desde modal (retorna JSON)."""
    model = Ruta
    form_class = RutaForm
    template_name = 'configuracion/ruta_form_modal.html'
    roles_permitidos = [
        Roles.ADMIN_SISTEMA,
        Roles.MESA_PARTES,
        Roles.ESPECIALISTA_TECNICO,
        Roles.ASESORIA_LEGAL,
        Roles.DIRECTOR_GENERAL,
        Roles.DIRECTOR_ADMINISTRATIVO,
    ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['accion'] = 'Actualizar'
        return context
    
    def form_valid(self, form):
        self.object = form.save()  # Guardar directamente sin intentar redirección
        html = render_to_string(self.template_name, self.get_context_data(form=form), request=self.request)
        return JsonResponse({
            'success': True,
            'message': 'Ruta actualizada correctamente.',
            'html': html,
            'item': {
                'id': self.object.pk,
                'label': f'{self.object.codigo} - {self.object.nombre}',
                'type': 'ruta',
                'detail_url': reverse_lazy('configuracion:rutas_detalle', kwargs={'pk': self.object.pk}),
                'edit_url': reverse_lazy('configuracion:rutas_editar', kwargs={'pk': self.object.pk}),
            },
        })

    def form_invalid(self, form):
        html = render_to_string(self.template_name, self.get_context_data(form=form), request=self.request)
        return JsonResponse({'success': False, 'html': html})


class FrecuenciaUpdateModalView(RolRequeridoMixin, UpdateView):
    """Editar frecuencia desde modal (retorna JSON)."""
    model = Frecuencia
    form_class = FrecuenciaForm
    template_name = 'configuracion/frecuencia_form_modal.html'
    roles_permitidos = [
        Roles.ADMIN_SISTEMA,
        Roles.MESA_PARTES,
        Roles.ESPECIALISTA_TECNICO,
        Roles.ASESORIA_LEGAL,
        Roles.DIRECTOR_GENERAL,
        Roles.DIRECTOR_ADMINISTRATIVO,
    ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['accion'] = 'Actualizar'
        return context
    
    def form_valid(self, form):
        self.object = form.save()  # Guardar directamente sin intentar redirección
        html = render_to_string(self.template_name, self.get_context_data(form=form), request=self.request)
        return JsonResponse({
            'success': True,
            'message': 'Frecuencia actualizada correctamente.',
            'html': html,
            'item': {
                'id': self.object.pk,
                'label': f'{self.object.codigo} - {self.object.nombre}',
                'type': 'frecuencia',
                'detail_url': reverse_lazy('configuracion:frecuencias_detalle', kwargs={'pk': self.object.pk}),
                'edit_url': reverse_lazy('configuracion:frecuencias_editar', kwargs={'pk': self.object.pk}),
            },
        })

    def form_invalid(self, form):
        html = render_to_string(self.template_name, self.get_context_data(form=form), request=self.request)
        return JsonResponse({'success': False, 'html': html})


class RutaDetailModalView(RolRequeridoMixin, DetailView):
    """Ver detalles de ruta desde modal."""
    model = Ruta
    template_name = 'configuracion/ruta_detail_modal.html'
    context_object_name = 'ruta'
    roles_permitidos = [
        Roles.ADMIN_SISTEMA,
        Roles.MESA_PARTES,
        Roles.ESPECIALISTA_TECNICO,
        Roles.ASESORIA_LEGAL,
        Roles.DIRECTOR_GENERAL,
        Roles.DIRECTOR_ADMINISTRATIVO,
    ]


class FrecuenciaDetailModalView(RolRequeridoMixin, DetailView):
    """Ver detalles de frecuencia desde modal."""
    model = Frecuencia
    template_name = 'configuracion/frecuencia_detail_modal.html'
    context_object_name = 'frecuencia'
    roles_permitidos = [
        Roles.ADMIN_SISTEMA,
        Roles.MESA_PARTES,
        Roles.ESPECIALISTA_TECNICO,
        Roles.ASESORIA_LEGAL,
        Roles.DIRECTOR_GENERAL,
        Roles.DIRECTOR_ADMINISTRATIVO,
    ]

