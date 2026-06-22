"""
Vistas para el módulo de notificaciones.
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views import View
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone

from .models import Notificacion
from .services import NotificacionService


class NotificacionesListView(LoginRequiredMixin, ListView):
    """Vista para listar todas las notificaciones del usuario."""
    model = Notificacion
    template_name = 'notificaciones/notificaciones_list.html'
    context_object_name = 'notificaciones'
    paginate_by = 20
    
    def get_queryset(self):
        return Notificacion.objects.filter(
            usuario=self.request.user
        ).order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Mis Notificaciones'
        context['no_leidas'] = NotificacionService.contar_no_leidas(self.request.user)
        return context


class NotificacionesNoLeidasAPI(LoginRequiredMixin, View):
    """API para obtener notificaciones no leídas (para la campanita)."""
    
    def get(self, request):
        notificaciones = NotificacionService.obtener_notificaciones_no_leidas(
            request.user,
            limite=10
        )
        
        data = {
            'count': NotificacionService.contar_no_leidas(request.user),
            'notificaciones': [
                {
                    'id': n.id,
                    'tipo': n.tipo,
                    'titulo': n.titulo,
                    'mensaje': n.mensaje[:100] + '...' if len(n.mensaje) > 100 else n.mensaje,
                    'prioridad': n.prioridad,
                    'url': n.url,
                    'fecha': n.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
                    'tiempo_relativo': NotificacionesNoLeidasAPI.tiempo_relativo(n.fecha_creacion),
                }
                for n in notificaciones
            ]
        }
        
        return JsonResponse(data)
    
    @staticmethod
    def tiempo_relativo(fecha):
        """Calcula tiempo relativo desde la fecha."""
        ahora = timezone.now()
        diff = ahora - fecha
        
        if diff.days > 30:
            return fecha.strftime('%d/%m/%Y')
        elif diff.days > 0:
            return f"hace {diff.days} día{'s' if diff.days > 1 else ''}"
        elif diff.seconds > 3600:
            horas = diff.seconds // 3600
            return f"hace {horas} hora{'s' if horas > 1 else ''}"
        elif diff.seconds > 60:
            minutos = diff.seconds // 60
            return f"hace {minutos} minuto{'s' if minutos > 1 else ''}"
        else:
            return "hace un momento"


class MarcarNotificacionLeidaAPI(LoginRequiredMixin, View):
    """API para marcar una notificación como leída."""
    
    def post(self, request, pk):
        notificacion = get_object_or_404(
            Notificacion,
            pk=pk,
            usuario=request.user
        )
        notificacion.marcar_leida()
        
        return JsonResponse({
            'success': True,
            'message': 'Notificación marcada como leída'
        })


class MarcarTodasLeidasAPI(LoginRequiredMixin, View):
    """API para marcar todas las notificaciones como leídas."""
    
    def post(self, request):
        count = NotificacionService.marcar_todas_leidas(request.user)
        
        return JsonResponse({
            'success': True,
            'message': f'{count} notificaciones marcadas como leídas',
            'count': count
        })
