"""
Vistas del módulo de Fiscalización.

- IndexView renderiza el dashboard SPA (template estático con JS).
- ActaViewSet expone el CRUD REST que consume el `ActasService` JS
  cuando se cambia su flag `useBackend` a true y se define API_BASE.
- estadisticas_api: endpoint que reproduce el contrato de
  `ActasService.stats()` para que el dashboard pueda alimentarse del backend.
"""
from datetime import date, timedelta
from collections import Counter

from django.db.models import Count, Q
from django.http import JsonResponse
from django.views.generic import TemplateView

from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend

from .models import Acta
from .serializers import ActaSerializer


class FiscalizacionIndexView(TemplateView):
    template_name = 'fiscalizacion/index.html'


class ActaViewSet(viewsets.ModelViewSet):
    queryset = Acta.objects.all()
    serializer_class = ActaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'modalidad', 'tipoIntervencion', 'fecha']
    search_fields = ['numero', 'placa', 'adminNombre', 'adminDocNum', 'condVolNombre', 'lugar']
    ordering_fields = ['fecha', 'numero', 'placa', 'estado', 'creadoEn']
    ordering = ['-fecha', '-hora']

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(creadoPor=user)


def estadisticas_api(request):
    """Devuelve estadísticas con el mismo shape que ActasService.stats()."""
    rango = int(request.GET.get('rangeDays', 7))
    hoy = date.today()
    desde = hoy - timedelta(days=rango - 1)

    actas = list(Acta.objects.all().values(
        'fecha', 'modalidad', 'lugar', 'estado', 'infracciones'
    ))

    buckets = {(desde + timedelta(days=i)).isoformat(): 0 for i in range(rango)}
    by_modalidad = Counter()
    by_lugar = Counter()
    infracciones = 0
    notificadas = 0
    semana = 0
    week_ago = hoy - timedelta(days=7)

    for a in actas:
        if a['fecha'] and a['fecha'] >= desde and a['fecha'].isoformat() in buckets:
            buckets[a['fecha'].isoformat()] += 1
        if a['fecha'] and a['fecha'] >= week_ago:
            semana += 1
        if a['estado'] in ('notificada', 'sancionada', 'archivada'):
            notificadas += 1
        infracciones += len([x for x in (a['infracciones'] or '').split(',') if x.strip()])
        by_modalidad[a['modalidad'] or 'Sin especificar'] += 1
        lugar = (a['lugar'] or 'Sin especificar').split(',')[0].strip()
        by_lugar[lugar] += 1

    total = len(actas)
    return JsonResponse({
        'total': total,
        'semana': semana,
        'infracciones': infracciones,
        'promedio': f'{(infracciones / total):.1f}' if total else '0.0',
        'notificadas': notificadas,
        'notifPct': round((notificadas / total) * 100) if total else 0,
        'trend': {'labels': list(buckets.keys()), 'values': list(buckets.values())},
        'modalidad': dict(by_modalidad),
        'topLugares': by_lugar.most_common(5),
    })
