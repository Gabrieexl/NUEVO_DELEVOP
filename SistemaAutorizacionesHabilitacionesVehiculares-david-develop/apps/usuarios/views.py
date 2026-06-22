"""
Vistas de usuarios del sistema DRTC.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import Usuario
from .forms import (
    LoginForm, UsuarioCreationForm, UsuarioUpdateForm, 
    UsuarioPerfilForm, CambiarPasswordForm
)
from .mixins import AdminRequeridoMixin, ConsultaInternaRequeridoMixin
from utils.constants import Roles, EstadoTramite, TipoTramite


class CustomLoginView(LoginView):
    """Vista de inicio de sesión personalizada."""
    template_name = 'usuarios/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('usuarios:dashboard')
    
    def form_valid(self, form):
        messages.success(self.request, f'Bienvenido, {form.get_user().get_full_name()}')
        return super().form_valid(form)


class CustomLogoutView(LogoutView):
    """Vista de cierre de sesión personalizada."""
    next_page = 'usuarios:login'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'Ha cerrado sesión exitosamente.')
        return super().dispatch(request, *args, **kwargs)


@login_required
def dashboard(request):
    """
    Vista del dashboard principal.
    Muestra información relevante según el rol del usuario.
    """
    from apps.tramites.models import Tramite
    from apps.empresas.models import EmpresaTransporte
    from apps.vehiculos.models import Vehiculo, HabilitacionVehicular
    from apps.conductores.models import Conductor, HabilitacionConductor
    from apps.autorizaciones.models import Autorizacion
    
    user = request.user
    hoy = timezone.now().date()
    inicio_hoy = timezone.make_aware(timezone.datetime.combine(hoy, timezone.datetime.min.time()))
    
    context = {
        'titulo': 'Panel de Control',
        'usuario': user,
    }
    
    # Estadísticas reales desde la base de datos
    tramites_pendientes = Tramite.objects.exclude(
        estado__in=[EstadoTramite.APROBADO, EstadoTramite.DENEGADO, EstadoTramite.CERRADO]
    ).count()
    
    tramites_hoy = Tramite.objects.filter(
        fecha_creacion__gte=inicio_hoy
    ).count()
    
    empresas_activas = EmpresaTransporte.objects.filter(estado='ACTIVA').count()
    
    vehiculos_habilitados = HabilitacionVehicular.objects.filter(
        estado='VIGENTE'
    ).count()
    
    context['estadisticas'] = {
        'tramites_pendientes': tramites_pendientes,
        'tramites_hoy': tramites_hoy,
        'empresas_activas': empresas_activas,
        'vehiculos_habilitados': vehiculos_habilitados,
    }
    
    # Información específica por rol
    if user.es_admin:
        context['tramites_recientes'] = Tramite.objects.order_by('-fecha_creacion')[:10]
        context['usuarios_activos'] = Usuario.objects.filter(is_active=True).count()
    
    elif user.es_mesa_partes:
        context['tramites_por_recibir'] = Tramite.objects.filter(
            estado=EstadoTramite.RECIBIDO
        ).order_by('-fecha_creacion')[:10]
        context['tramites_creados_hoy'] = tramites_hoy
    
    elif user.es_especialista:
        context['tramites_en_evaluacion'] = Tramite.objects.filter(
            estado=EstadoTramite.EN_EVAL_TECNICA
        ).order_by('-fecha_creacion')[:10]
        context['tramites_asignados'] = Tramite.objects.filter(
            estado=EstadoTramite.EN_EVAL_TECNICA
        ).count()
    
    elif user.es_legal:
        context['tramites_revision_legal'] = Tramite.objects.filter(
            estado=EstadoTramite.EN_REVISION_LEGAL
        ).order_by('-fecha_creacion')[:10]
        context['proyectos_pendientes'] = Tramite.objects.filter(
            estado=EstadoTramite.EN_REVISION_LEGAL
        ).count()
    
    elif user.es_director:
        context['tramites_pendientes_firma'] = Tramite.objects.filter(
            Q(estado=EstadoTramite.PENDIENTE_FIRMA) |
            Q(
                tipo_tramite=TipoTramite.INCREMENTO_FLOTA,
                estado=EstadoTramite.EN_DIRECCION_GENERAL
            ) |
            Q(
                tipo_tramite=TipoTramite.AUTORIZACION_RUTA,
                estado=EstadoTramite.EN_DIRECCION_GENERAL
            )
        ).order_by('-fecha_creacion')[:10]
        # Aprobados este mes
        inicio_mes = hoy.replace(day=1)
        context['aprobados_mes'] = Tramite.objects.filter(
            estado=EstadoTramite.APROBADO,
            fecha_actualizacion__gte=inicio_mes
        ).count()
    
    elif user.es_control_calidad:
        context['tramites_por_cerrar'] = Tramite.objects.filter(
            tipo_tramite__in=[
                TipoTramite.AUTORIZACION_INICIAL,
                TipoTramite.RENOVACION_TUC,
                TipoTramite.INCREMENTO_FLOTA,
            ],
            estado=EstadoTramite.APROBADO
        ).order_by('-fecha_creacion')[:10]
    
    return render(request, 'usuarios/dashboard.html', context)


class UsuarioListView(AdminRequeridoMixin, ListView):
    """Lista de usuarios del sistema."""
    model = Usuario
    template_name = 'usuarios/usuario_list.html'
    context_object_name = 'usuarios'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Usuario.objects.all().order_by('-date_joined')
        
        # Filtros
        rol = self.request.GET.get('rol')
        activo = self.request.GET.get('activo')
        buscar = self.request.GET.get('buscar')
        
        if rol:
            queryset = queryset.filter(rol=rol)
        
        if activo:
            queryset = queryset.filter(is_active=(activo == '1'))
        
        if buscar:
            queryset = queryset.filter(
                Q(username__icontains=buscar) |
                Q(first_name__icontains=buscar) |
                Q(last_name__icontains=buscar) |
                Q(dni__icontains=buscar) |
                Q(email__icontains=buscar)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Gestión de Usuarios'
        context['roles'] = Roles.CHOICES
        context['filtros'] = {
            'rol': self.request.GET.get('rol', ''),
            'activo': self.request.GET.get('activo', ''),
            'buscar': self.request.GET.get('buscar', ''),
        }
        return context


class UsuarioDetailView(AdminRequeridoMixin, DetailView):
    """Detalle de un usuario."""
    model = Usuario
    template_name = 'usuarios/usuario_detail.html'
    context_object_name = 'usuario_detalle'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Usuario: {self.object.get_full_name()}'
        return context


class UsuarioCreateView(AdminRequeridoMixin, CreateView):
    """Crear nuevo usuario."""
    model = Usuario
    form_class = UsuarioCreationForm
    template_name = 'usuarios/usuario_form.html'
    success_url = reverse_lazy('usuarios:usuario_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Usuario'
        context['boton'] = 'Crear'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Usuario creado exitosamente.')
        return super().form_valid(form)


class UsuarioUpdateView(AdminRequeridoMixin, UpdateView):
    """Editar usuario existente."""
    model = Usuario
    form_class = UsuarioUpdateForm
    template_name = 'usuarios/usuario_form.html'
    success_url = reverse_lazy('usuarios:usuario_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Usuario: {self.object.get_full_name()}'
        context['boton'] = 'Guardar Cambios'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Usuario actualizado exitosamente.')
        return super().form_valid(form)


@login_required
def perfil(request):
    """Vista del perfil del usuario actual."""
    if request.method == 'POST':
        form = UsuarioPerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado exitosamente.')
            return redirect('usuarios:perfil')
    else:
        form = UsuarioPerfilForm(instance=request.user)
    
    return render(request, 'usuarios/perfil.html', {
        'titulo': 'Mi Perfil',
        'form': form,
    })


@login_required
def cambiar_password(request):
    """Vista para cambiar la contraseña del usuario actual."""
    if request.method == 'POST':
        form = CambiarPasswordForm(request.POST)
        if form.is_valid():
            if not request.user.check_password(form.cleaned_data['password_actual']):
                messages.error(request, 'La contraseña actual es incorrecta.')
            else:
                request.user.set_password(form.cleaned_data['password_nuevo'])
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Contraseña cambiada exitosamente.')
                return redirect('usuarios:perfil')
    else:
        form = CambiarPasswordForm()
    
    return render(request, 'usuarios/cambiar_password.html', {
        'titulo': 'Cambiar Contraseña',
        'form': form,
    })
