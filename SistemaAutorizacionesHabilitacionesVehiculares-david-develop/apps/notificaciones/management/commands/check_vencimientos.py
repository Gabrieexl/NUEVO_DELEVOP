"""
Management command para verificar vencimientos y enviar alertas.
Ejecutar diariamente vía Task Scheduler o cron.

Uso:
    python manage.py check_vencimientos
    python manage.py check_vencimientos --dias 30
    python manage.py check_vencimientos --tipo soat
    python manage.py check_vencimientos --dry-run
"""

import logging
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone

from apps.notificaciones.models import TipoNotificacion, PrioridadNotificacion
from apps.notificaciones.services import NotificacionService
from apps.autorizaciones.models import Autorizacion
from apps.vehiculos.models import Vehiculo, HabilitacionVehicular
from apps.conductores.models import Conductor, HabilitacionConductor
from apps.usuarios.models import Usuario
from apps.tramites.models import Tramite, EstadoTramite
from apps.tramites.services import desactivar_autorizacion_cascada
from utils.constants import EstadoAutorizacion, Roles

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Verifica vencimientos y envía alertas por email y notificaciones in-app'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dias',
            type=int,
            default=30,
            help='Días de anticipación para alertas (default: 30)'
        )
        parser.add_argument(
            '--tipo',
            type=str,
            choices=['autorizacion', 'soat', 'citv', 'licencia', 'habilitacion', 'plazo', 'todos'],
            default='todos',
            help='Tipo de vencimiento a verificar (default: todos)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo mostrar qué se enviaría, sin enviar realmente'
        )
    
    def handle(self, *args, **options):
        dias = options['dias']
        tipo = options['tipo']
        dry_run = options['dry_run']
        
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"VERIFICACIÓN DE VENCIMIENTOS - {date.today()}")
        self.stdout.write(f"{'='*60}")
        self.stdout.write(f"Días de anticipación: {dias}")
        self.stdout.write(f"Tipo: {tipo}")
        self.stdout.write(f"Modo prueba: {'Sí' if dry_run else 'No'}\n")
        
        total_alertas = 0
        
        if tipo in ['autorizacion', 'todos']:
            total_alertas += self.check_autorizaciones(dias, dry_run)
            # Procesar las que ya vencieron hoy o antes
            if not dry_run:
                self.process_expired_autorizaciones()
        
        if tipo in ['soat', 'todos']:
            total_alertas += self.check_soat(dias, dry_run)
        
        if tipo in ['citv', 'todos']:
            total_alertas += self.check_citv(dias, dry_run)
        
        if tipo in ['licencia', 'todos']:
            total_alertas += self.check_licencias(dias, dry_run)
        
        if tipo in ['habilitacion', 'todos']:
            total_alertas += self.check_habilitaciones(dias, dry_run)
        
        if tipo in ['plazo', 'todos']:
            total_alertas += self.check_plazos_subsanacion(dry_run)
        
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(self.style.SUCCESS(f"Total de alertas generadas: {total_alertas}"))
        self.stdout.write(f"{'='*60}\n")
    
    def check_autorizaciones(self, dias: int, dry_run: bool) -> int:
        """Verifica autorizaciones próximas a vencer."""
        self.stdout.write("\n📋 Verificando AUTORIZACIONES...")
        
        fecha_limite = date.today() + timedelta(days=dias)
        
        autorizaciones = Autorizacion.objects.filter(
            estado='VIGENTE',
            fecha_fin_vigencia__lte=fecha_limite,
            fecha_fin_vigencia__gte=date.today()
        ).select_related('empresa')
        
        count = 0
        for aut in autorizaciones:
            dias_restantes = (aut.fecha_fin_vigencia - date.today()).days
            prioridad = self._get_prioridad_por_dias(dias_restantes)
            
            self.stdout.write(
                f"  - {aut.empresa.razon_social}: Res. {aut.numero_resolucion} "
                f"vence en {dias_restantes} días ({aut.fecha_fin_vigencia})"
            )
            
            if not dry_run:
                self._enviar_alerta_vencimiento(
                    tipo=TipoNotificacion.VENC_AUTORIZACION,
                    empresa=aut.empresa,
                    descripcion=f"Autorización N° {aut.numero_resolucion}",
                    fecha_vencimiento=aut.fecha_fin_vigencia,
                    dias_restantes=dias_restantes,
                    prioridad=prioridad
                )
            count += 1
        
        self.stdout.write(f"  Total: {count} autorizaciones próximas a vencer\n")
        return count
    
    def process_expired_autorizaciones(self):
        """Busca autorizaciones vencidas y aplica desactivación en cascada."""
        self.stdout.write("\n🛑 Procesando AUTORIZACIONES VENCIDAS...")
        
        hoy = date.today()
        vencidas = Autorizacion.objects.filter(
            estado=EstadoAutorizacion.VIGENTE,
            fecha_fin_vigencia__lt=hoy
        ).select_related('empresa')
        
        count = 0
        for aut in vencidas:
            self.stdout.write(self.style.WARNING(
                f"  - VENCIDA: {aut.empresa.razon_social} (Res. {aut.numero_resolucion}) "
                f"venció el {aut.fecha_fin_vigencia}"
            ))
            
            # Aplicar cascada
            resultado = desactivar_autorizacion_cascada(
                autorizacion=aut,
                nuevo_estado=EstadoAutorizacion.VENCIDA,
                motivo=f"Expiración automática de vigencia ({aut.fecha_fin_vigencia})"
            )
            
            # Notificar a administradores y directores
            usuarios_notificar = Usuario.objects.filter(
                rol__in=[Roles.ADMIN_SISTEMA, Roles.DIRECTOR_GENERAL, Roles.DIRECTOR_ADMINISTRATIVO],
                is_active=True
            )
            
            mensaje_notif = (
                f"La autorización N° {aut.numero_resolucion} de la empresa {aut.empresa.razon_social} "
                f"ha expirado. Se desactivaron {resultado['vehiculos_count']} vehículos y "
                f"{resultado['conductores_count']} conductores asociados."
            )
            
            for user in usuarios_notificar:
                NotificacionService.crear_notificacion_inapp(
                    usuario=user,
                    tipo=TipoNotificacion.VENC_AUTORIZACION,
                    titulo="Autorización Expirada (Automático)",
                    mensaje=mensaje_notif,
                    prioridad=PrioridadNotificacion.URGENTE,
                    empresa_id=aut.empresa.id
                )
            
            count += 1
            
        if count > 0:
            self.stdout.write(self.style.SUCCESS(f"  Se procesaron {count} autorizaciones vencidas."))
        else:
            self.stdout.write("  No se encontraron nuevas autorizaciones vencidas para procesar.")

    def check_soat(self, dias: int, dry_run: bool) -> int:
        """Verifica SOATs próximos a vencer."""
        self.stdout.write("\n🛡️ Verificando SOAT...")
        
        fecha_limite = date.today() + timedelta(days=dias)
        
        vehiculos = Vehiculo.objects.filter(
            estado='HABILITADO',
            fecha_venc_soat__lte=fecha_limite,
            fecha_venc_soat__gte=date.today()
        ).select_related('empresa_propietaria')
        
        count = 0
        for v in vehiculos:
            dias_restantes = (v.fecha_venc_soat - date.today()).days
            prioridad = self._get_prioridad_por_dias(dias_restantes)
            
            self.stdout.write(
                f"  - Placa {v.placa}: SOAT vence en {dias_restantes} días ({v.fecha_venc_soat})"
            )
            
            if not dry_run and v.empresa_propietaria:
                self._enviar_alerta_vencimiento(
                    tipo=TipoNotificacion.VENC_SOAT,
                    empresa=v.empresa_propietaria,
                    descripcion=f"SOAT del vehículo {v.placa}",
                    fecha_vencimiento=v.fecha_venc_soat,
                    dias_restantes=dias_restantes,
                    prioridad=prioridad,
                    placa=v.placa
                )
            count += 1
        
        self.stdout.write(f"  Total: {count} SOATs próximos a vencer\n")
        return count
    
    def check_citv(self, dias: int, dry_run: bool) -> int:
        """Verifica CITVs próximas a vencer."""
        self.stdout.write("\n🚗 Verificando CITV...")
        
        fecha_limite = date.today() + timedelta(days=dias)
        
        vehiculos = Vehiculo.objects.filter(
            estado='HABILITADO',
            fecha_venc_citv__lte=fecha_limite,
            fecha_venc_citv__gte=date.today()
        ).select_related('empresa_propietaria')
        
        count = 0
        for v in vehiculos:
            dias_restantes = (v.fecha_venc_citv - date.today()).days
            prioridad = self._get_prioridad_por_dias(dias_restantes)
            
            self.stdout.write(
                f"  - Placa {v.placa}: CITV vence en {dias_restantes} días ({v.fecha_venc_citv})"
            )
            
            if not dry_run and v.empresa_propietaria:
                self._enviar_alerta_vencimiento(
                    tipo=TipoNotificacion.VENC_CITV,
                    empresa=v.empresa_propietaria,
                    descripcion=f"CITV del vehículo {v.placa}",
                    fecha_vencimiento=v.fecha_venc_citv,
                    dias_restantes=dias_restantes,
                    prioridad=prioridad,
                    placa=v.placa
                )
            count += 1
        
        self.stdout.write(f"  Total: {count} CITVs próximas a vencer\n")
        return count
    
    def check_licencias(self, dias: int, dry_run: bool) -> int:
        """Verifica licencias de conducir próximas a vencer."""
        self.stdout.write("\n🪪 Verificando LICENCIAS DE CONDUCIR...")
        
        fecha_limite = date.today() + timedelta(days=dias)
        
        conductores = Conductor.objects.filter(
            estado='ACTIVO',
            licencia_fecha_vencimiento__lte=fecha_limite,
            licencia_fecha_vencimiento__gte=date.today()
        )
        
        count = 0
        for c in conductores:
            dias_restantes = (c.licencia_fecha_vencimiento - date.today()).days
            prioridad = self._get_prioridad_por_dias(dias_restantes)
            
            self.stdout.write(
                f"  - {c.nombre_completo} (DNI: {c.dni}): Licencia vence en "
                f"{dias_restantes} días ({c.licencia_fecha_vencimiento})"
            )
            
            if not dry_run:
                # Buscar empresas asociadas al conductor
                habilitaciones = HabilitacionConductor.objects.filter(
                    conductor=c,
                    estado='VIGENTE'
                ).select_related('empresa')
                
                for hab in habilitaciones:
                    self._enviar_alerta_vencimiento(
                        tipo=TipoNotificacion.VENC_LICENCIA,
                        empresa=hab.empresa,
                        descripcion=f"Licencia del conductor {c.nombre_completo}",
                        fecha_vencimiento=c.licencia_fecha_vencimiento,
                        dias_restantes=dias_restantes,
                        prioridad=prioridad,
                        conductor=c.nombre_completo
                    )
            count += 1
        
        self.stdout.write(f"  Total: {count} licencias próximas a vencer\n")
        return count
    
    def check_habilitaciones(self, dias: int, dry_run: bool) -> int:
        """Verifica habilitaciones vehiculares y de conductores próximas a vencer."""
        self.stdout.write("\n📝 Verificando HABILITACIONES...")
        
        fecha_limite = date.today() + timedelta(days=dias)
        count = 0
        
        # Habilitaciones vehiculares
        hab_vehiculos = HabilitacionVehicular.objects.filter(
            estado='VIGENTE',
            fecha_fin__lte=fecha_limite,
            fecha_fin__gte=date.today()
        ).select_related('vehiculo', 'vehiculo__empresa_propietaria')
        
        for hab in hab_vehiculos:
            dias_restantes = (hab.fecha_fin - date.today()).days
            prioridad = self._get_prioridad_por_dias(dias_restantes)
            
            self.stdout.write(
                f"  - Vehículo {hab.vehiculo.placa}: Habilitación vence en "
                f"{dias_restantes} días ({hab.fecha_fin})"
            )
            
            if not dry_run and hab.vehiculo.empresa_propietaria:
                self._enviar_alerta_vencimiento(
                    tipo=TipoNotificacion.VENC_HABILITACION,
                    empresa=hab.vehiculo.empresa_propietaria,
                    descripcion=f"Habilitación vehicular - {hab.vehiculo.placa}",
                    fecha_vencimiento=hab.fecha_fin,
                    dias_restantes=dias_restantes,
                    prioridad=prioridad,
                    placa=hab.vehiculo.placa
                )
            count += 1
        
        # Habilitaciones de conductores
        hab_conductores = HabilitacionConductor.objects.filter(
            estado='VIGENTE',
            fecha_fin__lte=fecha_limite,
            fecha_fin__gte=date.today()
        ).select_related('conductor', 'empresa')
        
        for hab in hab_conductores:
            dias_restantes = (hab.fecha_fin - date.today()).days
            prioridad = self._get_prioridad_por_dias(dias_restantes)
            
            self.stdout.write(
                f"  - Conductor {hab.conductor.nombre_completo}: Habilitación vence en "
                f"{dias_restantes} días ({hab.fecha_fin})"
            )
            
            if not dry_run:
                self._enviar_alerta_vencimiento(
                    tipo=TipoNotificacion.VENC_HABILITACION,
                    empresa=hab.empresa,
                    descripcion=f"Habilitación conductor - {hab.conductor.nombre_completo}",
                    fecha_vencimiento=hab.fecha_fin,
                    dias_restantes=dias_restantes,
                    prioridad=prioridad,
                    conductor=hab.conductor.nombre_completo
                )
            count += 1
        
        self.stdout.write(f"  Total: {count} habilitaciones próximas a vencer\n")
        return count
    
    def check_plazos_subsanacion(self, dry_run: bool) -> int:
        """Verifica trámites con plazo de subsanación próximo a vencer."""
        self.stdout.write("\n⏰ Verificando PLAZOS DE SUBSANACIÓN...")
        
        # Alertar para plazos que vencen en 5 días o menos
        fecha_limite = date.today() + timedelta(days=5)
        
        tramites = Tramite.objects.filter(
            estado=EstadoTramite.OBSERVADO,
            plazo_subsanacion__lte=fecha_limite,
            plazo_subsanacion__gte=date.today()
        ).select_related('empresa')
        
        count = 0
        for t in tramites:
            dias_restantes = (t.plazo_subsanacion - date.today()).days
            prioridad = PrioridadNotificacion.URGENTE if dias_restantes <= 2 else PrioridadNotificacion.ALTA
            
            self.stdout.write(
                f"  - Exp. {t.numero_expediente}: Plazo vence en "
                f"{dias_restantes} días ({t.plazo_subsanacion})"
            )
            
            if not dry_run:
                # Enviar al solicitante
                email = t.solicitante_email or (t.empresa.email if t.empresa else None)
                nombre = t.solicitante_nombres or (t.empresa.razon_social if t.empresa else '')
                
                if email:
                    context = {
                        'nombre_destinatario': nombre,
                        'numero_expediente': t.numero_expediente,
                        'tipo_tramite': t.get_tipo_tramite_display(),
                        'plazo_subsanacion': t.plazo_subsanacion.strftime('%d/%m/%Y'),
                        'dias_restantes': dias_restantes,
                    }
                    
                    NotificacionService.enviar_email(
                        email_destino=email,
                        asunto=f"URGENTE: Plazo de subsanación próximo a vencer - {t.numero_expediente}",
                        template='emails/alerta_plazo_subsanacion',
                        context=context,
                        tipo=TipoNotificacion.PLAZO_SUBSANACION,
                        nombre_destino=nombre,
                        tramite_id=t.pk,
                        empresa_id=t.empresa_id,
                        prioridad='high'
                    )
            count += 1
        
        self.stdout.write(f"  Total: {count} plazos próximos a vencer\n")
        return count
    
    def _get_prioridad_por_dias(self, dias: int) -> str:
        """Determina la prioridad según los días restantes."""
        if dias <= 7:
            return PrioridadNotificacion.URGENTE
        elif dias <= 15:
            return PrioridadNotificacion.ALTA
        elif dias <= 30:
            return PrioridadNotificacion.MEDIA
        else:
            return PrioridadNotificacion.BAJA
    
    def _enviar_alerta_vencimiento(
        self,
        tipo: str,
        empresa,
        descripcion: str,
        fecha_vencimiento,
        dias_restantes: int,
        prioridad: str,
        placa: str = None,
        conductor: str = None
    ):
        """Envía alerta de vencimiento por email y notificación in-app a usuarios internos."""
        
        # Determinar tipo de vencimiento para la plantilla
        tipo_vencimiento_map = {
            TipoNotificacion.VENC_AUTORIZACION: 'Autorización',
            TipoNotificacion.VENC_SOAT: 'SOAT',
            TipoNotificacion.VENC_CITV: 'CITV',
            TipoNotificacion.VENC_LICENCIA: 'Licencia de Conducir',
            TipoNotificacion.VENC_HABILITACION: 'Habilitación',
        }
        tipo_vencimiento = tipo_vencimiento_map.get(tipo, 'Documento')
        
        # 1. Enviar email a la empresa
        if empresa and empresa.email:
            context = {
                'nombre_destinatario': empresa.razon_social,
                'tipo_vencimiento': tipo_vencimiento,
                'empresa': empresa.razon_social,
                'placa': placa,
                'conductor': conductor,
                'fecha_vencimiento': fecha_vencimiento.strftime('%d/%m/%Y'),
                'dias_restantes': dias_restantes,
            }
            
            NotificacionService.enviar_email(
                email_destino=empresa.email,
                asunto=f"DRTC - Alerta de Vencimiento: {descripcion}",
                template='emails/alerta_vencimiento',
                context=context,
                tipo=tipo,
                nombre_destino=empresa.razon_social,
                empresa_id=empresa.pk,
                prioridad='high' if dias_restantes <= 7 else 'medium'
            )
        
        # 2. Crear notificación in-app para usuarios especialistas
        usuarios_admin = Usuario.objects.filter(
            Q(rol='ADMIN_SISTEMA') | Q(rol='ESPECIALISTA_TECNICO'),
            is_active=True
        )
        
        for usuario in usuarios_admin:
            NotificacionService.crear_notificacion_inapp(
                usuario=usuario,
                tipo=tipo,
                titulo=f"Vencimiento próximo: {descripcion}",
                mensaje=f"{descripcion} de {empresa.razon_social if empresa else 'N/A'} "
                        f"vence el {fecha_vencimiento.strftime('%d/%m/%Y')} ({dias_restantes} días)",
                prioridad=prioridad,
                empresa_id=empresa.pk if empresa else None
            )
