from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class ManualesListView(LoginRequiredMixin, TemplateView):
    template_name = 'documentacion/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Centro de Documentación'
        return context

class ManualUsuariosView(LoginRequiredMixin, TemplateView):
    template_name = 'documentacion/manual_usuarios.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Manual del Módulo de Usuarios'
        return context

class ManualConfiguracionView(LoginRequiredMixin, TemplateView):
    template_name = 'documentacion/manual_configuracion.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Manual del Módulo de Configuración'
        return context

class ManualReportesView(LoginRequiredMixin, TemplateView):
    template_name = 'documentacion/manual_reportes.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Manual de Reportes y Tablas'
        return context

class ManualOperativoView(LoginRequiredMixin, TemplateView):
    template_name = 'documentacion/manual_operativo.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Manual Operativo (Empresas, Vehículos, Conductores)'
        return context
