
"""
Vistas del módulo de reportes.
"""

from datetime import timedelta
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.views.generic import TemplateView
from apps.usuarios.mixins import RolRequeridoMixin
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Count, Q
from django.db.models.functions import ExtractYear

from apps.empresas.models import EmpresaTransporte
from apps.autorizaciones.models import Autorizacion
from apps.vehiculos.models import Vehiculo, HabilitacionVehicular
from apps.conductores.models import Conductor, HabilitacionConductor
from apps.tramites.models import Tramite
from apps.configuracion.models import TipoServicio

from utils.exports import ExcelExporter
from utils.constants import (
    EstadoEmpresa, EstadoAutorizacion, EstadoVehiculo, EstadoConductor, Roles
)

from .pdf_generator import (
    ReporteEmpresasPDF, ReporteAutorizacionesPDF, ReporteVehiculosPDF,
    ReporteConductoresPDF, ReporteTramitesPDF, ReporteResolucionesPDF,
    ReporteVencimientosPDF, FichaEmpresaPDF
)

# Roles para ver y exportar reportes (según matriz acordada).
REPORTES_VER_ROLES = [
    Roles.ADMIN_SISTEMA,
    Roles.MESA_PARTES,
    Roles.ESPECIALISTA_TECNICO,
    Roles.ASESORIA_LEGAL,
    Roles.DIRECTOR_GENERAL,
    Roles.DIRECTOR_ADMINISTRATIVO,
    Roles.CONTROL_CALIDAD,
]
REPORTES_EXPORT_ROLES = [
    Roles.ADMIN_SISTEMA,
    Roles.MESA_PARTES,
    Roles.ESPECIALISTA_TECNICO,
    Roles.ASESORIA_LEGAL,
    Roles.DIRECTOR_GENERAL,
    Roles.DIRECTOR_ADMINISTRATIVO,
    Roles.CONTROL_CALIDAD,
]


class ReportesIndexView(RolRequeridoMixin, TemplateView):
    roles_permitidos = REPORTES_VER_ROLES
    """Vista principal del módulo de reportes."""
    template_name = 'reportes/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Módulo de Reportes'
        
        # Datos para estadísticas rápidas
        hoy = timezone.now().date()
        en_30_dias = hoy + timedelta(days=30)
        
        context['stats'] = {
            'empresas_activas': EmpresaTransporte.objects.filter(estado='ACTIVA').count(),
            'autorizaciones_vigentes': Autorizacion.objects.filter(estado='VIGENTE').count(),
            'vehiculos_habilitados': Vehiculo.objects.filter(estado='HABILITADO').count(),
            'conductores_activos': Conductor.objects.filter(estado='ACTIVO').count(),
            'tramites_pendientes': Tramite.objects.exclude(
                estado__in=['APROBADO', 'DENEGADO', 'CERRADO']
            ).count(),
            'soat_por_vencer': Vehiculo.objects.filter(
                estado='HABILITADO',
                fecha_venc_soat__lte=en_30_dias,
                fecha_venc_soat__gte=hoy
            ).count(),
            'citv_por_vencer': Vehiculo.objects.filter(
                estado='HABILITADO',
                fecha_venc_citv__lte=en_30_dias,
                fecha_venc_citv__gte=hoy
            ).count(),
            'licencias_por_vencer': Conductor.objects.filter(
                estado='ACTIVO',
                licencia_fecha_vencimiento__lte=en_30_dias,
                licencia_fecha_vencimiento__gte=hoy
            ).count(),
            'autorizaciones_por_vencer': Autorizacion.objects.filter(
                estado='VIGENTE',
                fecha_fin_vigencia__lte=en_30_dias,
                fecha_fin_vigencia__gte=hoy
            ).count(),
        }

        # Años dinámicos para filtros
        context['anios_empresas'] = EmpresaTransporte.objects.annotate(
            anio=ExtractYear('fecha_creacion')
        ).values_list('anio', flat=True).distinct().order_by('-anio')

        context['anios_autorizaciones'] = Autorizacion.objects.annotate(
            anio=ExtractYear('fecha_resolucion')
        ).values_list('anio', flat=True).distinct().order_by('-anio')

        context['anios_vehiculos_registro'] = Vehiculo.objects.annotate(
            anio=ExtractYear('fecha_creacion')
        ).values_list('anio', flat=True).distinct().order_by('-anio')

        context['anios_vehiculos_fabricacion'] = Vehiculo.objects.values_list(
            'anio_fabricacion', flat=True
        ).distinct().order_by('-anio_fabricacion')

        context['anios_conductores'] = Conductor.objects.annotate(
            anio=ExtractYear('fecha_creacion')
        ).values_list('anio', flat=True).distinct().order_by('-anio')

        # Estados para los filtros
        context['estados_empresa'] = EstadoEmpresa.CHOICES
        context['estados_autorizacion'] = EstadoAutorizacion.CHOICES
        context['estados_vehiculo'] = EstadoVehiculo.CHOICES
        context['estados_conductor'] = EstadoConductor.CHOICES
        context['tipos_servicio'] = TipoServicio.objects.filter(activo=True).order_by('nombre')
        
        return context


class EstadisticasView(RolRequeridoMixin, TemplateView):
    roles_permitidos = REPORTES_VER_ROLES
    """Vista de estadísticas con gráficos."""
    template_name = 'reportes/estadisticas.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Estadísticas del Sistema'
        
        hoy = timezone.now().date()
        
        # Totales generales
        context['totales'] = {
            'empresas': EmpresaTransporte.objects.count(),
            'autorizaciones': Autorizacion.objects.count(),
            'vehiculos': Vehiculo.objects.count(),
            'conductores': Conductor.objects.count(),
            'tramites': Tramite.objects.count(),
        }
        
        # Datos para gráficos (Serializados a JSON)
        
        # 1. Empresas por estado
        empresas_data = list(
            EmpresaTransporte.objects.values('estado')
            .annotate(total=Count('id'))
            .order_by('estado')
        )
        context['empresas_por_estado'] = json.dumps(empresas_data, cls=DjangoJSONEncoder)
        
        # 2. Autorizaciones por estado
        autorizaciones_data = list(
            Autorizacion.objects.values('estado')
            .annotate(total=Count('id'))
            .order_by('estado')
        )
        context['autorizaciones_por_estado'] = json.dumps(autorizaciones_data, cls=DjangoJSONEncoder)
        
        # 3. Vehículos por tipo (Carrocería)
        vehiculos_tipo_data = list(
            Vehiculo.objects.filter(estado='HABILITADO')
            .values('carroceria__nombre')
            .annotate(total=Count('id'))
            .order_by('carroceria__nombre')
        )
        # Renombrar clave para JS
        vehiculos_tipo_data = [{'tipo_vehiculo': item['carroceria__nombre'] or 'Sin Tipo', 'total': item['total']} for item in vehiculos_tipo_data]
        context['vehiculos_por_tipo'] = json.dumps(vehiculos_tipo_data, cls=DjangoJSONEncoder)
        
        # 4. Vehículos por estado
        vehiculos_estado_data = list(
            Vehiculo.objects.values('estado')
            .annotate(total=Count('id'))
            .order_by('estado')
        )
        context['vehiculos_por_estado'] = json.dumps(vehiculos_estado_data, cls=DjangoJSONEncoder)
        
        # 5. Trámites por tipo (últimos 12 meses)
        tramites_tipo_data = list(
            Tramite.objects.values('tipo_tramite')
            .annotate(total=Count('id'))
            .order_by('-total')
        )
        context['tramites_por_tipo'] = json.dumps(tramites_tipo_data, cls=DjangoJSONEncoder)
        
        # 6. Trámites por estado
        tramites_estado_data = list(
            Tramite.objects.values('estado')
            .annotate(total=Count('id'))
            .order_by('estado')
        )
        context['tramites_por_estado'] = json.dumps(tramites_estado_data, cls=DjangoJSONEncoder)
        
        # 7. Trámites por mes (últimos 6 meses)
        from django.db.models.functions import TruncMonth
        hace_6_meses = hoy - timedelta(days=180)
        tramites_mes_raw = list(
            Tramite.objects.filter(fecha_creacion__gte=hace_6_meses)
            .annotate(mes=TruncMonth('fecha_creacion'))
            .values('mes')
            .annotate(total=Count('id'))
            .order_by('mes')
        )
        tramites_mes_data = [
            {'mes': item['mes'].strftime('%Y-%m-%d') if item['mes'] else None, 'total': item['total']}
            for item in tramites_mes_raw
        ]
        context['tramites_por_mes'] = json.dumps(tramites_mes_data, cls=DjangoJSONEncoder)
        
        # 8. Conductores por categoría de licencia
        conductores_cat_data = list(
            Conductor.objects.filter(estado='ACTIVO')
            .values('licencia_categoria')
            .annotate(total=Count('id'))
            .order_by('licencia_categoria')
        )
        context['conductores_por_categoria'] = json.dumps(conductores_cat_data, cls=DjangoJSONEncoder)
        
        return context


# =============================================================================
# VISTAS DE GENERACIÓN DE REPORTES PDF
# =============================================================================

class ReporteEmpresasPDFView(RolRequeridoMixin, TemplateView):
    roles_permitidos = REPORTES_EXPORT_ROLES
    """Genera reporte PDF de empresas."""
    
    def get(self, request, *args, **kwargs):
        # Filtros
        estado = request.GET.get('estado', '')
        anio = request.GET.get('anio', '')
        tipo_servicio = request.GET.get('tipo_servicio', '')
        
        queryset = EmpresaTransporte.objects.all().order_by('razon_social')
        filtros = []
        
        if estado:
            queryset = queryset.filter(estado=estado)
            filtros.append(f"Estado: {estado}")
        
        if anio:
            queryset = queryset.filter(fecha_creacion__year=anio)
            filtros.append(f"Año Registro: {anio}")
        
        if tipo_servicio:
            queryset = queryset.filter(autorizaciones__tipo_servicio_id=tipo_servicio, autorizaciones__estado=EstadoAutorizacion.VIGENTE)
            tipo = TipoServicio.objects.filter(id=tipo_servicio).first()
            if tipo:
                filtros.append(f"Tipo Servicio: {tipo.nombre}")

        filtro_texto = " | ".join(filtros) if filtros else None
        
        reporte = ReporteEmpresasPDF(queryset, filtro_texto)
        return reporte.generar_contenido()


class ReporteAutorizacionesPDFView(RolRequeridoMixin, TemplateView):
    roles_permitidos = REPORTES_EXPORT_ROLES
    """Genera reporte PDF de autorizaciones."""
    
    def get(self, request, *args, **kwargs):
        estado = request.GET.get('estado', '')
        empresa_id = request.GET.get('empresa', '')
        anio = request.GET.get('anio', '')
        
        queryset = Autorizacion.objects.select_related('empresa').order_by('-fecha_resolucion')
        filtros = []
        
        if estado:
            queryset = queryset.filter(estado=estado)
            filtros.append(f"Estado: {estado}")
        
        if anio:
            queryset = queryset.filter(fecha_resolucion__year=anio)
            filtros.append(f"Año Resolución: {anio}")
        
        if empresa_id:
            queryset = queryset.filter(empresa_id=empresa_id)
            empresa = EmpresaTransporte.objects.filter(id=empresa_id).first()
            if empresa:
                filtros.append(f"Empresa: {empresa.razon_social}")
        
        filtro_texto = " | ".join(filtros) if filtros else None
        
        reporte = ReporteAutorizacionesPDF(queryset, filtro_texto)
        return reporte.generar_contenido()


class ReporteVehiculosPDFView(RolRequeridoMixin, TemplateView):
    roles_permitidos = REPORTES_EXPORT_ROLES
    """Genera reporte PDF de vehículos."""
    
    def get(self, request, *args, **kwargs):
        estado = request.GET.get('estado', '')
        empresa_id = request.GET.get('empresa', '')
        tipo = request.GET.get('tipo', '')
        tipo_servicio = request.GET.get('tipo_servicio', '')
        anio = request.GET.get('anio', '')
        anio_fabricacion = request.GET.get('anio_fabricacion', '')
        estado_autorizacion = request.GET.get('estado_autorizacion', '')
        estado_empresa = request.GET.get('estado_empresa', '')
        
        # queryset = Vehiculo.objects.select_related('empresa_propietaria').order_by('placa')
        queryset = Vehiculo.objects.select_related(
            'empresa_propietaria',
            'autorizacion_principal__tipo_servicio'
        ).order_by('empresa_propietaria__razon_social')
        filtros = []
        
        if estado:
            queryset = queryset.filter(estado=estado)
            filtros.append(f"Estado: {estado}")
        
        if estado_empresa:
            queryset = queryset.filter(empresa_propietaria__estado=estado_empresa)
            filtros.append(f"Estado Empresa: {estado_empresa}")

        if estado_autorizacion:
            queryset = queryset.filter(autorizacion_principal__estado=estado_autorizacion)
            filtros.append(f"Estado Autorización: {estado_autorizacion}")

        if anio:
            queryset = queryset.filter(fecha_creacion__year=anio)
            filtros.append(f"Año Registro: {anio}")
            
        if anio_fabricacion:
            queryset = queryset.filter(anio_fabricacion=anio_fabricacion)
            filtros.append(f"Año Fabricación: {anio_fabricacion}")
        
        if empresa_id:
            queryset = queryset.filter(empresa_propietaria_id=empresa_id)
            empresa = EmpresaTransporte.objects.filter(id=empresa_id).first()
            if empresa:
                filtros.append(f"Empresa: {empresa.razon_social}")
        
        if tipo:
            queryset = queryset.filter(carroceria_id=tipo)
            filtros.append(f"Tipo: {tipo}")
        
        if tipo_servicio:
            queryset = queryset.filter(autorizacion_principal__tipo_servicio_id=tipo_servicio)
            tipo = TipoServicio.objects.filter(id=tipo_servicio).first()
            if tipo:
                filtros.append(f"Tipo Servicio: {tipo.nombre}")
        
        filtro_texto = " | ".join(filtros) if filtros else None

        usuario = request.user.get_full_name() or request.user.username
        reporte = ReporteVehiculosPDF(queryset, filtro_texto, generado_por=usuario)
        #reporte = ReporteVehiculosPDF(queryset, filtro_texto)
        return reporte.generar_contenido()


class ReporteConductoresPDFView(RolRequeridoMixin, TemplateView):
    roles_permitidos = REPORTES_EXPORT_ROLES
    """Genera reporte PDF de conductores."""
    
    def get(self, request, *args, **kwargs):
        estado = request.GET.get('estado', '')
        empresa_id = request.GET.get('empresa', '')
        categoria = request.GET.get('categoria', '')
        anio = request.GET.get('anio', '')
        
        queryset = Conductor.objects.select_related('empresa').order_by('apellido_paterno', 'apellido_materno')
        filtros = []
        
        if estado:
            queryset = queryset.filter(estado=estado)
            filtros.append(f"Estado: {estado}")
        
        if anio:
            queryset = queryset.filter(fecha_creacion__year=anio)
            filtros.append(f"Año Registro: {anio}")
        
        if empresa_id:
            queryset = queryset.filter(empresa_id=empresa_id)
            empresa = EmpresaTransporte.objects.filter(id=empresa_id).first()
            if empresa:
                filtros.append(f"Empresa: {empresa.razon_social}")
        
        if categoria:
            queryset = queryset.filter(licencia_categoria=categoria)
            filtros.append(f"Categoría: {categoria}")
        
        filtro_texto = " | ".join(filtros) if filtros else None
        
        reporte = ReporteConductoresPDF(queryset, filtro_texto)
        return reporte.generar_contenido()


class ReporteTramitesPDFView(RolRequeridoMixin, TemplateView):
    roles_permitidos = REPORTES_EXPORT_ROLES
    """Genera reporte PDF de trámites."""
    
    def get(self, request, *args, **kwargs):
        estado = request.GET.get('estado', '')
        tipo = request.GET.get('tipo', '')
        fecha_desde = request.GET.get('fecha_desde', '')
        fecha_hasta = request.GET.get('fecha_hasta', '')
        
        queryset = Tramite.objects.select_related('empresa').order_by('-fecha_creacion')
        filtros = []
        
        if estado:
            queryset = queryset.filter(estado=estado)
            filtros.append(f"Estado: {estado}")
        
        if tipo:
            queryset = queryset.filter(tipo_tramite=tipo)
            filtros.append(f"Tipo: {tipo}")
        
        if fecha_desde:
            queryset = queryset.filter(fecha_creacion__date__gte=fecha_desde)
            filtros.append(f"Desde: {fecha_desde}")
        
        if fecha_hasta:
            queryset = queryset.filter(fecha_creacion__date__lte=fecha_hasta)
            filtros.append(f"Hasta: {fecha_hasta}")
        
        filtro_texto = " | ".join(filtros) if filtros else None
        
        reporte = ReporteTramitesPDF(queryset, filtro_texto)
        return reporte.generar_contenido()


class ReporteResolucionesPDFView(RolRequeridoMixin, TemplateView):
    roles_permitidos = REPORTES_EXPORT_ROLES
    """Genera reporte PDF de resoluciones emitidas."""
    
    def get(self, request, *args, **kwargs):
        fecha_desde = request.GET.get('fecha_desde', '')
        fecha_hasta = request.GET.get('fecha_hasta', '')
        tipo = request.GET.get('tipo', '')
        
        queryset = Tramite.objects.filter(
            numero_resolucion__isnull=False
        ).exclude(
            numero_resolucion=''
        ).select_related('empresa').order_by('-fecha_resolucion')
        
        filtros = []
        
        if fecha_desde:
            queryset = queryset.filter(fecha_resolucion__gte=fecha_desde)
            filtros.append(f"Desde: {fecha_desde}")
        
        if fecha_hasta:
            queryset = queryset.filter(fecha_resolucion__lte=fecha_hasta)
            filtros.append(f"Hasta: {fecha_hasta}")
        
        if tipo:
            queryset = queryset.filter(tipo_tramite=tipo)
            filtros.append(f"Tipo: {tipo}")
        
        filtro_texto = " | ".join(filtros) if filtros else "Todas las resoluciones"
        
        reporte = ReporteResolucionesPDF(queryset, filtro_texto)
        return reporte.generar_contenido()


class ReporteVencimientosPDFView(RolRequeridoMixin, TemplateView):
    roles_permitidos = REPORTES_EXPORT_ROLES
    """Genera reporte PDF de vencimientos."""
    
    def get(self, request, *args, **kwargs):
        tipo = request.GET.get('tipo', 'soat')  # soat, citv, licencia, autorizacion
        dias = int(request.GET.get('dias', 30))
        empresa_id = request.GET.get('empresa', '')
        
        hoy = timezone.now().date()
        fecha_limite = hoy + timedelta(days=dias)
        
        filtros = []
        
        if tipo == 'soat':
            queryset = Vehiculo.objects.filter(
                estado='HABILITADO',
                fecha_venc_soat__lte=fecha_limite,
                fecha_venc_soat__gte=hoy
            ).select_related('empresa_propietaria').order_by('fecha_venc_soat')
            
            if empresa_id:
                queryset = queryset.filter(empresa_propietaria_id=empresa_id)
                empresa = EmpresaTransporte.objects.filter(id=empresa_id).first()
                if empresa:
                    filtros.append(f"Empresa: {empresa.razon_social}")
                    
        elif tipo == 'citv':
            queryset = Vehiculo.objects.filter(
                estado='HABILITADO',
                fecha_venc_citv__lte=fecha_limite,
                fecha_venc_citv__gte=hoy
            ).select_related('empresa_propietaria').order_by('fecha_venc_citv')
            
            if empresa_id:
                queryset = queryset.filter(empresa_propietaria_id=empresa_id)
                empresa = EmpresaTransporte.objects.filter(id=empresa_id).first()
                if empresa:
                    filtros.append(f"Empresa: {empresa.razon_social}")
                    
        elif tipo == 'licencia':
            queryset = Conductor.objects.filter(
                estado='ACTIVO',
                licencia_fecha_vencimiento__lte=fecha_limite,
                licencia_fecha_vencimiento__gte=hoy
            ).select_related('empresa').order_by('licencia_fecha_vencimiento')
            
            if empresa_id:
                queryset = queryset.filter(empresa_id=empresa_id)
                empresa = EmpresaTransporte.objects.filter(id=empresa_id).first()
                if empresa:
                    filtros.append(f"Empresa: {empresa.razon_social}")
                    
        elif tipo == 'autorizacion':
            queryset = Autorizacion.objects.filter(
                estado='VIGENTE',
                fecha_fin_vigencia__lte=fecha_limite,
                fecha_fin_vigencia__gte=hoy
            ).select_related('empresa').order_by('fecha_fin_vigencia')
            
            if empresa_id:
                queryset = queryset.filter(empresa_id=empresa_id)
                empresa = EmpresaTransporte.objects.filter(id=empresa_id).first()
                if empresa:
                    filtros.append(f"Empresa: {empresa.razon_social}")
        else:
            queryset = Vehiculo.objects.none()
        
        filtro_texto = " | ".join(filtros) if filtros else None
        
        reporte = ReporteVencimientosPDF(tipo, queryset, dias, filtro_texto)
        return reporte.generar_contenido()


# =============================================================================
# VISTAS DE EXPORTACIÓN EXCEL
# =============================================================================

class ExportarEmpresasExcelView(RolRequeridoMixin, TemplateView):
    roles_permitidos = REPORTES_EXPORT_ROLES
    """Exporta empresas a Excel."""
    
    def get(self, request, *args, **kwargs):
        estado = request.GET.get('estado', '')
        anio = request.GET.get('anio', '')
        tipo_servicio = request.GET.get('tipo_servicio', '')
        
        queryset = EmpresaTransporte.objects.all().order_by('razon_social')
        
        if estado:
            queryset = queryset.filter(estado=estado)
        
        if anio:
            queryset = queryset.filter(fecha_creacion__year=anio)

        if tipo_servicio:
            queryset = queryset.filter(autorizaciones__tipo_servicio_id=tipo_servicio, autorizaciones__estado=EstadoAutorizacion.VIGENTE)
        
        queryset = queryset.distinct()
        # Preparar datos
        headers = ['RUC', 'Razón Social', 'Nombre Comercial', 'Representante Legal', 'DNI Representante','Dirección', 'Provincia', 'Distrito', 'Teléfono', 'Email', 'Estado','Fecha Inicio Autorización', 'Fecha Fin Autorización']
        
        datos = []
        for emp in queryset:
            autorizacion = emp.autorizaciones.filter(
                estado=EstadoAutorizacion.VIGENTE
            ).order_by('-fecha_inicio_vigencia').first()
            datos.append([
                emp.ruc,
                emp.razon_social,
                emp.nombre_comercial or '',
                emp.representante_legal or '',
                emp.dni_representante or '',
                emp.domicilio_fiscal or '',
                emp.provincia or '',
                emp.distrito or '',
                emp.telefono or '',
                emp.email or '',
                emp.get_estado_display(),
                autorizacion.fecha_inicio_vigencia.strftime('%d/%m/%Y') if autorizacion else '',
                autorizacion.fecha_fin_vigencia.strftime('%d/%m/%Y') if autorizacion else '',
            ])
        
        exporter = ExcelExporter('Padrón de Empresas', headers)
        return exporter.export_to_response(datos, 'padron_empresas.xlsx')


class ExportarAutorizacionesExcelView(RolRequeridoMixin, TemplateView):
    roles_permitidos = REPORTES_EXPORT_ROLES
    """Exporta autorizaciones a Excel."""
    
    def get(self, request, *args, **kwargs):
        estado = request.GET.get('estado', '')
        empresa_id = request.GET.get('empresa', '')
        anio = request.GET.get('anio', '')
        
        queryset = Autorizacion.objects.select_related('empresa').order_by('-fecha_resolucion')
        
        if estado:
            queryset = queryset.filter(estado=estado)
        if anio:
            queryset = queryset.filter(fecha_resolucion__year=anio)
        if empresa_id:
            queryset = queryset.filter(empresa_id=empresa_id)
        
        headers = ['N° Resolución', 'Fecha Resolución', 'Empresa', 'RUC', 'Tipo Servicio', 'Ámbito', 'Vigencia Desde', 'Vigencia Hasta', 'Estado']
        datos = []
        for aut in queryset:
            datos.append([
                aut.numero_resolucion,
                aut.fecha_resolucion.strftime('%d/%m/%Y') if aut.fecha_resolucion else '',
                aut.empresa.razon_social if aut.empresa else '',
                aut.empresa.ruc if aut.empresa else '',
                aut.tipo_servicio.nombre if aut.tipo_servicio else '',
                aut.get_ambito_display(),
                aut.fecha_inicio_vigencia.strftime('%d/%m/%Y') if aut.fecha_inicio_vigencia else '',
                aut.fecha_fin_vigencia.strftime('%d/%m/%Y') if aut.fecha_fin_vigencia else '',
                aut.get_estado_display(),
            ])
        
        exporter = ExcelExporter('Padrón de Autorizaciones', headers)
        return exporter.export_to_response(datos, 'padron_autorizaciones.xlsx')


class ExportarVehiculosExcelView(RolRequeridoMixin, TemplateView):
    roles_permitidos = REPORTES_EXPORT_ROLES
    """Exporta vehículos a Excel."""
    
    def get(self, request, *args, **kwargs):
        estado = request.GET.get('estado', '')
        empresa_id = request.GET.get('empresa', '')
        anio = request.GET.get('anio', '')
        anio_fabricacion = request.GET.get('anio_fabricacion', '')
        tipo_servicio = request.GET.get('tipo_servicio', '')
        estado_autorizacion = request.GET.get('estado_autorizacion', '')
        estado_empresa = request.GET.get('estado_empresa', '')
        
        #queryset = Vehiculo.objects.select_related('empresa_propietaria').order_by('placa')
        queryset = Vehiculo.objects.select_related(
            'empresa_propietaria',
            'autorizacion_principal__tipo_servicio'
        ).order_by('empresa_propietaria__razon_social')
        
        if estado:
            queryset = queryset.filter(estado=estado)
        
        if estado_empresa:
            queryset = queryset.filter(empresa_propietaria__estado=estado_empresa)
        if anio:
            queryset = queryset.filter(fecha_creacion__year=anio)
        if tipo_servicio:
            queryset = queryset.filter(autorizacion_principal__tipo_servicio_id=tipo_servicio)
        if anio_fabricacion:
            queryset = queryset.filter(anio_fabricacion=anio_fabricacion)
        if empresa_id:
            queryset = queryset.filter(empresa_propietaria_id=empresa_id)
        if estado_autorizacion:
            queryset = queryset.filter(autorizacion_principal__estado=estado_autorizacion)
        
        datos = []
        for veh in queryset:
            datos.append([
                veh.placa,
                veh.empresa_propietaria.razon_social if veh.empresa_propietaria else '',
                veh.empresa_propietaria.ruc if veh.empresa_propietaria else '',
                veh.numero_tuc_vigente or '',
                veh.marca or '',
                veh.modelo or '',
                veh.anio_fabricacion or '',
                veh.color or '',
                veh.carroceria.nombre if veh.carroceria else '',
                veh.capacidad_sentados or '',
                veh.numero_serie or '',
                veh.numero_motor or '',
                veh.fecha_venc_soat.strftime('%d/%m/%Y') if veh.fecha_venc_soat else '',
                veh.fecha_venc_citv.strftime('%d/%m/%Y') if veh.fecha_venc_citv else '',
                veh.get_estado_display(),
            ])
        
        headers = ['Placa', 'Empresa', 'RUC', 'N° TUC', 'Marca', 'Modelo', 'Año', 'Color', 'Tipo Vehículo', 'Capacidad', 'N° Serie', 'N° Motor', 'SOAT Vence', 'CITV Vence', 'Estado']
        exporter = ExcelExporter('Padrón de Vehículos', headers)
        return exporter.export_to_response(datos, 'padron_vehiculos.xlsx')


class ExportarConductoresExcelView(RolRequeridoMixin, TemplateView):
    roles_permitidos = REPORTES_EXPORT_ROLES
    """Exporta conductores a Excel."""
    
    def get(self, request, *args, **kwargs):
        estado = request.GET.get('estado', '')
        empresa_id = request.GET.get('empresa', '')
        anio = request.GET.get('anio', '')
        
        queryset = Conductor.objects.select_related('empresa').order_by('apellido_paterno')
        
        if estado:
            queryset = queryset.filter(estado=estado)
        if anio:
            queryset = queryset.filter(fecha_creacion__year=anio)
        if empresa_id:
            queryset = queryset.filter(empresa_id=empresa_id)
        
        headers = ['DNI', 'Apellido Paterno', 'Apellido Materno', 'Nombres', 'Empresa', 'RUC Empresa', 'Fecha Nacimiento', 'Teléfono', 'Email', 'N° Licencia', 'Categoría', 'Licencia Vence', 'Estado']
        datos = []
        for cond in queryset:
            datos.append([
                cond.dni,
                cond.apellido_paterno,
                cond.apellido_materno,
                cond.nombres,
                cond.empresa.razon_social if cond.empresa else '',
                cond.empresa.ruc if cond.empresa else '',
                cond.fecha_nacimiento.strftime('%d/%m/%Y') if cond.fecha_nacimiento else '',
                cond.telefono or '',
                cond.email or '',
                cond.licencia_numero or '',
                cond.get_licencia_categoria_display() if cond.licencia_categoria else '',
                cond.licencia_fecha_vencimiento.strftime('%d/%m/%Y') if cond.licencia_fecha_vencimiento else '',
                cond.get_estado_display(),
            ])
        
        exporter = ExcelExporter('Padrón de Conductores', headers)
        return exporter.export_to_response(datos, 'padron_conductores.xlsx')


class ExportarTramitesExcelView(RolRequeridoMixin, TemplateView):
    roles_permitidos = REPORTES_EXPORT_ROLES
    """Exporta trámites a Excel."""
    
    def get(self, request, *args, **kwargs):
        estado = request.GET.get('estado', '')
        tipo = request.GET.get('tipo', '')
        fecha_desde = request.GET.get('fecha_desde', '')
        fecha_hasta = request.GET.get('fecha_hasta', '')
        
        queryset = Tramite.objects.select_related('empresa').order_by('-fecha_creacion')
        
        if estado:
            queryset = queryset.filter(estado=estado)
        if tipo:
            queryset = queryset.filter(tipo_tramite=tipo)
        if fecha_desde:
            queryset = queryset.filter(fecha_creacion__date__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_creacion__date__lte=fecha_hasta)
        
        headers = ['N° Expediente', 'Expediente Externo', 'Tipo Trámite', 'Empresa', 'RUC', 'Fecha Presentación', 'Estado', 'N° Resolución', 'Fecha Resolución', 'Descripción']
        datos = []
        for tramite in queryset:
            datos.append([
                tramite.numero_expediente or '',
                tramite.expediente_externo or '',
                tramite.get_tipo_tramite_display(),
                tramite.empresa.razon_social if tramite.empresa else '',
                tramite.empresa.ruc if tramite.empresa else '',
                tramite.fecha_presentacion.strftime('%d/%m/%Y') if tramite.fecha_presentacion else '',
                tramite.get_estado_display(),
                tramite.numero_resolucion or '',
                tramite.fecha_resolucion.strftime('%d/%m/%Y') if tramite.fecha_resolucion else '',
                tramite.descripcion_solicitud or '',
            ])
        
        exporter = ExcelExporter('Reporte de Trámites', headers)
        return exporter.export_to_response(datos, 'reporte_tramites.xlsx')


class FichaEmpresaPDFView(RolRequeridoMixin, TemplateView):
    roles_permitidos = REPORTES_EXPORT_ROLES
    """Genera ficha PDF completa de una empresa."""
    
    def get(self, request, *args, **kwargs):
        empresa_id = kwargs.get('pk')
        
        try:
            empresa = EmpresaTransporte.objects.get(pk=empresa_id)
        except EmpresaTransporte.DoesNotExist:
            return HttpResponse("Empresa no encontrada", status=404)
        
        reporte = FichaEmpresaPDF(empresa)
        return reporte.generar_contenido()


class SeleccionarEmpresaFichaView(RolRequeridoMixin, TemplateView):
    roles_permitidos = REPORTES_VER_ROLES
    """Vista para seleccionar empresa y generar ficha."""
    template_name = 'reportes/seleccionar_empresa_ficha.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Generar Ficha de Empresa'
        context['empresas'] = EmpresaTransporte.objects.filter(
            estado='ACTIVA'
        ).order_by('razon_social')
        return context



