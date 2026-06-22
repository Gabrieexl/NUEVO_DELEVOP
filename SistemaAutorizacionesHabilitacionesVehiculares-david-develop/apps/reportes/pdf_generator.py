"""
Generador de reportes PDF con ReportLab.
"""

import io
from datetime import datetime
from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, 
    Image, PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


class ReportePDF:
    """Clase base para generar reportes PDF."""
    
    def __init__(self, titulo, subtitulo=None, orientacion='portrait', generado_por=None):
        self.titulo = titulo
        self.subtitulo = subtitulo
        self.generado_por = generado_por
        self.buffer = io.BytesIO()
        
        pagesize = A4 if orientacion == 'portrait' else landscape(A4)
        
        self.doc = SimpleDocTemplate(
            self.buffer,
            pagesize=pagesize,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
            title=self.titulo,
            author='DRTC Madre de Dios',
            subject='Reporte del Sistema de Autorizaciones y Habilitaciones Vehiculares'
        )
        
        self.styles = getSampleStyleSheet()
        self._crear_estilos_personalizados()
        self.elementos = []
        self.pagesize = pagesize
        
    def _crear_estilos_personalizados(self):
        """Crea estilos personalizados para el reporte."""
        # Título principal
        self.styles.add(ParagraphStyle(
            name='TituloReporte',
            parent=self.styles['Heading1'],
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=6,
            textColor=colors.HexColor('#1a5276')
        ))
        
        # Subtítulo
        self.styles.add(ParagraphStyle(
            name='SubtituloReporte',
            parent=self.styles['Normal'],
            fontSize=11,
            alignment=TA_CENTER,
            spaceAfter=12,
            textColor=colors.HexColor('#566573')
        ))
        
        # Encabezado de sección
        self.styles.add(ParagraphStyle(
            name='SeccionTitulo',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceBefore=12,
            spaceAfter=6,
            textColor=colors.HexColor('#2c3e50')
        ))
        
        # Texto normal
        self.styles.add(ParagraphStyle(
            name='TextoNormal',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=6
        ))
        
        # Texto pequeño
        self.styles.add(ParagraphStyle(
            name='TextoPequeno',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#7f8c8d')
        ))
        
        # Texto para tablas
        self.styles.add(ParagraphStyle(
            name='TablaTexto',
            parent=self.styles['Normal'],
            fontSize=8,
            leading=9,
            alignment=TA_LEFT
        ))
        
        # Texto para tablas centrado
        self.styles.add(ParagraphStyle(
            name='TablaTextoCentro',
            parent=self.styles['Normal'],
            fontSize=8,
            leading=9,
            alignment=TA_CENTER
        ))
        
        # Pie de página
        self.styles.add(ParagraphStyle(
            name='PiePagina',
            parent=self.styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#95a5a6')
        ))

        self.styles.add(ParagraphStyle(
            name='PiePaginaDerecha',
            parent=self.styles['Normal'],
            fontSize=8,
            alignment=TA_RIGHT,
            textColor=colors.HexColor('#95a5a6')
        ))
    
    def agregar_encabezado(self, incluir_logo=False):
        """Agrega el encabezado institucional."""
        # Título de la institución
        self.elementos.append(Paragraph(
            "DIRECCIÓN REGIONAL DE TRANSPORTES Y COMUNICACIONES",
            self.styles['TituloReporte']
        ))
        self.elementos.append(Paragraph(
            "MADRE DE DIOS",
            self.styles['SubtituloReporte']
        ))
        
        # Línea separadora
        self.elementos.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor('#3498db'),
            spaceBefore=6,
            spaceAfter=12
        ))
        
        # Título del reporte
        self.elementos.append(Paragraph(
            self.titulo.upper(),
            self.styles['TituloReporte']
        ))
        
        if self.subtitulo:
            self.elementos.append(Paragraph(
                self.subtitulo,
                self.styles['SubtituloReporte']
            ))
        
        # Fecha de generación
        fecha_actual = timezone.localtime(timezone.now()).strftime("%d/%m/%Y %H:%M")
        self.elementos.append(Paragraph(
            f"Fecha de generación: {fecha_actual}",
            self.styles['TextoPequeno']
        ))
        
        self.elementos.append(Spacer(1, 0.5*cm))
    
    def agregar_seccion(self, titulo):
        """Agrega un título de sección."""
        self.elementos.append(Paragraph(titulo, self.styles['SeccionTitulo']))
    
    def agregar_parrafo(self, texto):
        """Agrega un párrafo de texto."""
        self.elementos.append(Paragraph(texto, self.styles['TextoNormal']))
    
    def agregar_tabla(self, datos, anchos_columnas=None, estilo_cabecera=True):
        """
        Agrega una tabla al reporte.
        
        Args:
            datos: Lista de listas con los datos (primera fila = cabeceras)
            anchos_columnas: Lista con anchos de cada columna en cm
            estilo_cabecera: Si True, aplica estilo especial a la primera fila
        """
        if not datos:
            return
        
        # Calcular anchos
        if anchos_columnas:
            col_widths = [w * cm for w in anchos_columnas]
        else:
            # Ancho automático
            page_width = self.pagesize[0] - 3*cm  # Margen total
            col_widths = [page_width / len(datos[0])] * len(datos[0])
        
        tabla = Table(datos, colWidths=col_widths, repeatRows=1)
        
        # Estilos de tabla
        estilos = [
            # Fuente general
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            # Bordes
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
        ]
        
        if estilo_cabecera and len(datos) > 0:
            estilos.extend([
                # Cabecera
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ])
            
            # Alternar colores de filas
            for i in range(1, len(datos)):
                if i % 2 == 0:
                    estilos.append(
                        ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8f9fa'))
                    )
        
        tabla.setStyle(TableStyle(estilos))
        self.elementos.append(tabla)
        self.elementos.append(Spacer(1, 0.3*cm))
    
    def agregar_resumen(self, items):
        """
        Agrega una sección de resumen con pares clave-valor.
        
        Args:
            items: Lista de tuplas (etiqueta, valor)
        """
        datos = [[item[0], str(item[1])] for item in items]
        
        tabla = Table(datos, colWidths=[8*cm, 4*cm])
        tabla.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        self.elementos.append(tabla)
        self.elementos.append(Spacer(1, 0.5*cm))
    
    def agregar_espacio(self, altura_cm=0.5):
        """Agrega un espacio vertical."""
        self.elementos.append(Spacer(1, altura_cm*cm))
    
    def agregar_salto_pagina(self):
        """Agrega un salto de página."""
        self.elementos.append(PageBreak())
    
    def agregar_pie_pagina(self, texto=None):
        """Agrega información de pie de página."""
        if texto is None:
            texto = "Documento generado por el Sistema de Autorizaciones y Habilitaciones Vehiculares - DRTC Madre de Dios"
        
        self.elementos.append(Spacer(1, 1*cm))
        self.elementos.append(HRFlowable(
            width="100%",
            thickness=0.5,
            color=colors.HexColor('#bdc3c7'),
            spaceBefore=6,
            spaceAfter=6
        ))
        self.elementos.append(Paragraph(texto, self.styles['PiePagina']))
        if self.generado_por:
            self.elementos.append(Paragraph(
                f"Generado por: {self.generado_por}",
                self.styles['PiePaginaDerecha']
        ))
    
    def generado_por_primera_pagina(self, canvas, doc):

        """Dibuja 'Generado por' en la esquina inferior derecha SOLO en la primera página."""
        if not self.generado_por:
            return

        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor('#95a5a6'))

        # Esquina inferior derecha, respetando margen derecho
        x = doc.pagesize[0] - doc.rightMargin
        y = doc.bottomMargin - 10  
        canvas.drawRightString(x, y, f"Generado por: {self.generado_por}")
        canvas.restoreState()

    def generar(self):
        """Genera el PDF y retorna el contenido del buffer."""
        self.doc.build(
            self.elementos,
            onFirstPage=self.generado_por_primera_pagina
        )
        self.buffer.seek(0)
        return self.buffer.getvalue()
    
    def get_response(self, filename):
        """Retorna una HttpResponse con el PDF."""
        from django.http import HttpResponse
        
        response = HttpResponse(
            self.generar(),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class ReporteEmpresasPDF(ReportePDF):
    """Reporte de Padrón de Empresas."""
    
    def __init__(self, empresas, filtros=None):
        super().__init__(
            titulo="Padrón de Empresas de Transporte",
            subtitulo=filtros or "Todas las empresas",
            orientacion='landscape'
        )
        self.empresas = empresas
    
    def generar_contenido(self):
        self.agregar_encabezado()
        
        # Resumen
        total = self.empresas.count()
        activas = self.empresas.filter(estado='ACTIVA').count()
        inactivas = total - activas
        
        self.agregar_resumen([
            ('Total de Empresas:', total),
            ('Empresas Activas:', activas),
            ('Empresas Inactivas:', inactivas),
        ])
        
        # Tabla de datos
        datos = [['N°', 'RUC', 'Razón Social', 'Representante Legal', 'DNI Rep.','Estado', 'F. Inicio Aut.', 'F. Fin Aut.', 'Telefono']]
        
        for i, empresa in enumerate(self.empresas, 1):
            autorizacion = empresa.autorizaciones.filter(
                estado='VIGENTE'
            ).order_by('-fecha_inicio_vigencia').first()
            datos.append([
                str(i),
                Paragraph(empresa.ruc, self.styles['TablaTexto']),
                Paragraph(empresa.razon_social, self.styles['TablaTexto']),
                Paragraph(empresa.representante_legal or '-', self.styles['TablaTexto']),
                Paragraph(empresa.dni_representante or '-', self.styles['TablaTexto']),
                empresa.get_estado_display(),
                autorizacion.fecha_inicio_vigencia.strftime('%d/%m/%Y') if autorizacion else '-',
                autorizacion.fecha_fin_vigencia.strftime('%d/%m/%Y') if autorizacion else '-',
                Paragraph(empresa.telefono or '-', self.styles['TablaTexto'])
            ])
        
        self.agregar_tabla(datos, anchos_columnas=[0.8, 2.5, 6.5, 5, 2.2, 2, 2.5])
        self.agregar_pie_pagina()
        
        return self.get_response('padron_empresas.pdf')


class ReporteAutorizacionesPDF(ReportePDF):
    """Reporte de Autorizaciones."""
    
    def __init__(self, autorizaciones, filtros=None):
        super().__init__(
            titulo="Padrón de Autorizaciones de Transporte",
            subtitulo=filtros or "Todas las autorizaciones",
            orientacion='landscape'
        )
        self.autorizaciones = autorizaciones
    
    def generar_contenido(self):
        self.agregar_encabezado()
        
        # Resumen
        total = self.autorizaciones.count()
        vigentes = self.autorizaciones.filter(estado='VIGENTE').count()
        vencidas = self.autorizaciones.filter(estado='VENCIDA').count()
        
        self.agregar_resumen([
            ('Total de Autorizaciones:', total),
            ('Vigentes:', vigentes),
            ('Vencidas:', vencidas),
        ])
        
        # Tabla de datos
        datos = [['N°', 'N° Resolución', 'Empresa', 'Tipo Servicio', 'Ámbito', 'Vigencia Desde', 'Vigencia Hasta', 'Estado']]
        
        for i, aut in enumerate(self.autorizaciones, 1):
            datos.append([
                str(i),
                Paragraph(aut.numero_resolucion, self.styles['TablaTexto']),
                Paragraph(aut.empresa.razon_social if aut.empresa else '-', self.styles['TablaTexto']),
                Paragraph(aut.tipo_servicio.nombre if aut.tipo_servicio else '-', self.styles['TablaTexto']),
                Paragraph(aut.get_ambito_display(), self.styles['TablaTexto']),
                aut.fecha_inicio_vigencia.strftime('%d/%m/%Y') if aut.fecha_inicio_vigencia else '-',
                aut.fecha_fin_vigencia.strftime('%d/%m/%Y') if aut.fecha_fin_vigencia else '-',
                aut.get_estado_display()
            ])
        
        self.agregar_tabla(datos, anchos_columnas=[0.8, 3.5, 5.5, 2.5, 3, 2.5, 2.5, 2])
        self.agregar_pie_pagina()
        
        return self.get_response('padron_autorizaciones.pdf')


class ReporteVehiculosPDF(ReportePDF):
    """Reporte de Flota Vehicular."""
    
    def __init__(self, vehiculos, filtros=None, titulo_custom=None, generado_por=None):
        super().__init__(
            titulo=titulo_custom or "Padrón de Flota Vehicular Habilitada",
            subtitulo=filtros or "Todos los vehículos",
            orientacion='landscape',
            generado_por=generado_por
        )
        self.vehiculos = vehiculos
    
    def generar_contenido(self):
        self.agregar_encabezado()
        
        # Resumen
        total = self.vehiculos.count()
        
        self.agregar_resumen([
            ('Total de Vehículos:', total),
        ])
        
        # Tabla de datos
        datos = [['N°', 'Placa', 'Empresa', 'N° TUC', 'Marca', 'Modelo', 'Año', 'Tipo', 'Capacidad', 'SOAT Vence', 'CITV Vence']]
        
        for i, veh in enumerate(self.vehiculos, 1):
            datos.append([
                str(i),
                Paragraph(veh.placa, self.styles['TablaTexto']),
                Paragraph(veh.empresa_propietaria.razon_social if veh.empresa_propietaria else '-', self.styles['TablaTexto']),
                Paragraph(veh.numero_tuc_vigente or '-', self.styles['TablaTexto']),
                Paragraph(veh.marca if veh.marca else '-', self.styles['TablaTexto']),
                Paragraph(veh.modelo if veh.modelo else '-', self.styles['TablaTexto']),
                str(veh.anio_fabricacion) if veh.anio_fabricacion else '-',
                Paragraph(veh.carroceria.nombre if veh.carroceria else '-', self.styles['TablaTexto']),
                str(veh.capacidad_sentados) if veh.capacidad_sentados else '-',
                veh.fecha_venc_soat.strftime('%d/%m/%Y') if veh.fecha_venc_soat else '-',
                veh.fecha_venc_citv.strftime('%d/%m/%Y') if veh.fecha_venc_citv else '-'
            ])
        
        self.agregar_tabla(datos, anchos_columnas=[0.7, 1.8, 4, 2.5, 1.8, 1.8, 1.2, 1.8, 1.5, 2.2, 2.2])
        self.agregar_pie_pagina()
        
        return self.get_response('padron_vehiculos.pdf')


class ReporteConductoresPDF(ReportePDF):
    """Reporte de Conductores."""
    
    def __init__(self, conductores, filtros=None, titulo_custom=None):
        super().__init__(
            titulo=titulo_custom or "Padrón de Conductores Habilitados",
            subtitulo=filtros or "Todos los conductores",
            orientacion='landscape'
        )
        self.conductores = conductores
    
    def generar_contenido(self):
        self.agregar_encabezado()
        
        # Resumen
        total = self.conductores.count()
        
        self.agregar_resumen([
            ('Total de Conductores:', total),
        ])
        
        # Tabla de datos
        datos = [['N°', 'DNI', 'Apellidos y Nombres', 'Empresa', 'N° Licencia', 'Categoría', 'Vence Licencia', 'Estado']]
        
        for i, cond in enumerate(self.conductores, 1):
            nombre_completo = f"{cond.apellido_paterno} {cond.apellido_materno}, {cond.nombres}"
            datos.append([
                str(i),
                Paragraph(cond.dni, self.styles['TablaTexto']),
                Paragraph(nombre_completo, self.styles['TablaTexto']),
                Paragraph(cond.empresa.razon_social if cond.empresa else '-', self.styles['TablaTexto']),
                Paragraph(cond.licencia_numero or '-', self.styles['TablaTexto']),
                Paragraph(cond.get_licencia_categoria_display() if cond.licencia_categoria else '-', self.styles['TablaTexto']),
                cond.licencia_fecha_vencimiento.strftime('%d/%m/%Y') if cond.licencia_fecha_vencimiento else '-',
                cond.get_estado_display()
            ])
        
        self.agregar_tabla(datos, anchos_columnas=[0.7, 2, 6, 5, 3, 2, 2.5, 2])
        self.agregar_pie_pagina()
        
        return self.get_response('padron_conductores.pdf')


class ReporteTramitesPDF(ReportePDF):
    """Reporte de Trámites."""
    
    def __init__(self, tramites, filtros=None):
        super().__init__(
            titulo="Reporte de Trámites",
            subtitulo=filtros or "Todos los trámites",
            orientacion='landscape'
        )
        self.tramites = tramites
    
    def generar_contenido(self):
        self.agregar_encabezado()
        
        # Resumen
        total = self.tramites.count()
        
        self.agregar_resumen([
            ('Total de Trámites:', total),
        ])
        
        # Tabla de datos
        datos = [['N°', 'N° Expediente', 'Tipo', 'Empresa', 'Fecha Presentación', 'Estado', 'N° Resolución']]
        
        for i, tramite in enumerate(self.tramites, 1):
            datos.append([
                str(i),
                Paragraph(tramite.numero_expediente or '-', self.styles['TablaTexto']),
                Paragraph(tramite.get_tipo_tramite_display(), self.styles['TablaTexto']),
                Paragraph(tramite.empresa.razon_social if tramite.empresa else '-', self.styles['TablaTexto']),
                tramite.fecha_presentacion.strftime('%d/%m/%Y') if tramite.fecha_presentacion else '-',
                tramite.get_estado_display(),
                Paragraph(tramite.numero_resolucion or '-', self.styles['TablaTexto'])
            ])
        
        self.agregar_tabla(datos, anchos_columnas=[0.7, 3.5, 4, 5, 2.5, 3, 3.5])
        self.agregar_pie_pagina()
        
        return self.get_response('reporte_tramites.pdf')


class ReporteResolucionesPDF(ReportePDF):
    """Reporte de Resoluciones Emitidas."""
    
    def __init__(self, tramites, filtros=None):
        super().__init__(
            titulo="Resoluciones Emitidas",
            subtitulo=filtros or "Período no especificado",
            orientacion='landscape'
        )
        self.tramites = tramites
    
    def generar_contenido(self):
        self.agregar_encabezado()
        
        total = self.tramites.count()
        
        self.agregar_resumen([
            ('Total de Resoluciones:', total),
        ])
        
        # Tabla de datos
        datos = [['N°', 'N° Resolución', 'Fecha', 'Tipo Trámite', 'Empresa Beneficiaria', 'N° Expediente']]
        
        for i, tramite in enumerate(self.tramites, 1):
            datos.append([
                str(i),
                Paragraph(tramite.numero_resolucion or '-', self.styles['TablaTexto']),
                tramite.fecha_resolucion.strftime('%d/%m/%Y') if tramite.fecha_resolucion else '-',
                Paragraph(tramite.get_tipo_tramite_display(), self.styles['TablaTexto']),
                Paragraph(tramite.empresa.razon_social if tramite.empresa else '-', self.styles['TablaTexto']),
                Paragraph(tramite.numero_expediente or '-', self.styles['TablaTexto'])
            ])
        
        self.agregar_tabla(datos, anchos_columnas=[0.7, 4, 2.5, 5, 6, 4])
        self.agregar_pie_pagina()
        
        return self.get_response('resoluciones_emitidas.pdf')


class ReporteVencimientosPDF(ReportePDF):
    """Reporte de Vencimientos (SOAT, CITV, Licencias, Autorizaciones)."""
    
    def __init__(self, tipo_vencimiento, items, dias, filtros=None):
        titulos = {
            'soat': 'Vehículos con SOAT por Vencer',
            'citv': 'Vehículos con CITV por Vencer',
            'licencia': 'Conductores con Licencia por Vencer',
            'autorizacion': 'Autorizaciones por Vencer'
        }
        super().__init__(
            titulo=titulos.get(tipo_vencimiento, 'Reporte de Vencimientos'),
            subtitulo=f"Próximos {dias} días" + (f" - {filtros}" if filtros else ""),
            orientacion='landscape'
        )
        self.tipo = tipo_vencimiento
        self.items = items
        self.dias = dias
    
    def generar_contenido(self):
        self.agregar_encabezado()
        
        total = len(self.items) if isinstance(self.items, list) else self.items.count()
        
        self.agregar_resumen([
            ('Total de registros:', total),
            ('Días de anticipación:', self.dias),
        ])
        
        if self.tipo == 'soat':
            datos = [['N°', 'Placa', 'Empresa', 'Marca/Modelo', 'Fecha Venc. SOAT', 'Días Restantes']]
            for i, veh in enumerate(self.items, 1):
                dias_rest = (veh.fecha_venc_soat - timezone.now().date()).days if veh.fecha_venc_soat else 0
                datos.append([
                    str(i),
                    veh.placa,
                    Paragraph(veh.empresa_propietaria.razon_social if veh.empresa_propietaria else '-', self.styles['TablaTexto']),
                    Paragraph(f"{veh.marca} {veh.modelo}", self.styles['TablaTexto']),
                    veh.fecha_venc_soat.strftime('%d/%m/%Y') if veh.fecha_venc_soat else '-',
                    str(dias_rest)
                ])
            self.agregar_tabla(datos, anchos_columnas=[0.7, 2.5, 6, 4, 3, 2.5])
            
        elif self.tipo == 'citv':
            datos = [['N°', 'Placa', 'Empresa', 'Marca/Modelo', 'Fecha Venc. CITV', 'Días Restantes']]
            for i, veh in enumerate(self.items, 1):
                dias_rest = (veh.fecha_venc_citv - timezone.now().date()).days if veh.fecha_venc_citv else 0
                datos.append([
                    str(i),
                    veh.placa,
                    Paragraph(veh.empresa_propietaria.razon_social if veh.empresa_propietaria else '-', self.styles['TablaTexto']),
                    Paragraph(f"{veh.marca} {veh.modelo}", self.styles['TablaTexto']),
                    veh.fecha_venc_citv.strftime('%d/%m/%Y') if veh.fecha_venc_citv else '-',
                    str(dias_rest)
                ])
            self.agregar_tabla(datos, anchos_columnas=[0.7, 2.5, 6, 4, 3, 2.5])
            
        elif self.tipo == 'licencia':
            datos = [['N°', 'DNI', 'Conductor', 'Empresa', 'N° Licencia', 'Categoría', 'Vence', 'Días Rest.']]
            for i, cond in enumerate(self.items, 1):
                dias_rest = (cond.licencia_fecha_vencimiento - timezone.now().date()).days if cond.licencia_fecha_vencimiento else 0
                datos.append([
                    str(i),
                    Paragraph(cond.dni, self.styles['TablaTexto']),
                    Paragraph(cond.nombre_completo, self.styles['TablaTexto']),
                    Paragraph(cond.empresa.razon_social if cond.empresa else '-', self.styles['TablaTexto']),
                    Paragraph(cond.licencia_numero or '-', self.styles['TablaTexto']),
                    Paragraph(cond.licencia_categoria or '-', self.styles['TablaTexto']),
                    cond.licencia_fecha_vencimiento.strftime('%d/%m/%Y') if cond.licencia_fecha_vencimiento else '-',
                    str(dias_rest)
                ])
            self.agregar_tabla(datos, anchos_columnas=[0.7, 2, 4.5, 4.5, 3, 1.5, 2.5, 1.5])
            
        elif self.tipo == 'autorizacion':
            datos = [['N°', 'N° Resolución', 'Empresa', 'Tipo Servicio', 'Vigencia Hasta', 'Días Restantes']]
            for i, aut in enumerate(self.items, 1):
                dias_rest = (aut.fecha_fin_vigencia - timezone.now().date()).days if aut.fecha_fin_vigencia else 0
                datos.append([
                    str(i),
                    Paragraph(aut.numero_resolucion, self.styles['TablaTexto']),
                    Paragraph(aut.empresa.razon_social if aut.empresa else '-', self.styles['TablaTexto']),
                    Paragraph(aut.tipo_servicio.nombre if aut.tipo_servicio else '-', self.styles['TablaTexto']),
                    aut.fecha_fin_vigencia.strftime('%d/%m/%Y') if aut.fecha_fin_vigencia else '-',
                    str(dias_rest)
                ])
            self.agregar_tabla(datos, anchos_columnas=[0.7, 4, 7, 3, 2.5, 2])
        
        self.agregar_pie_pagina()
        return self.get_response(f'vencimientos_{self.tipo}.pdf')


class FichaEmpresaPDF(ReportePDF):
    """Ficha completa de una empresa con todos sus datos."""
    
    def __init__(self, empresa):
        super().__init__(
            titulo=f'FICHA DE EMPRESA DE TRANSPORTE',
            subtitulo=empresa.razon_social,
            orientacion='portrait'
        )
        self.empresa = empresa
    
    def generar_contenido(self):
        self.agregar_encabezado()
        
        # ========== DATOS DE LA EMPRESA ==========
        self.elementos.append(Paragraph(
            '<b>1. DATOS GENERALES DE LA EMPRESA</b>',
            self.styles['SeccionTitulo']
        ))
        
        datos_empresa = [
            ['RUC:', self.empresa.ruc, 'Estado:', self.empresa.get_estado_display()],
            ['Razón Social:', Paragraph(self.empresa.razon_social, self.styles['TablaTexto'])],
            ['Nombre Comercial:', Paragraph(self.empresa.nombre_comercial or '-', self.styles['TablaTexto'])],
            ['Domicilio Fiscal:', Paragraph(self.empresa.domicilio_fiscal or '-', self.styles['TablaTexto'])],
            ['Representante Legal:', Paragraph(self.empresa.representante_legal or '-', self.styles['TablaTexto']), 'DNI:', self.empresa.dni_representante or '-'],
            ['Teléfono:', self.empresa.telefono or '-', 'Email:', self.empresa.email or '-'],
        ]
        
        tabla = Table(datos_empresa, colWidths=[3.5*cm, 7*cm, 2*cm, 4.5*cm])
        tabla.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f4f8')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            # Combinar celdas para filas con datos largos
            ('SPAN', (1, 1), (3, 1)),  # Razón Social
            ('SPAN', (1, 2), (3, 2)),  # Nombre Comercial
            ('SPAN', (1, 3), (3, 3)),  # Domicilio Fiscal
        ]))
        self.elementos.append(tabla)
        self.elementos.append(Spacer(1, 0.5*cm))
        
        # ========== AUTORIZACIONES ==========
        autorizaciones = self.empresa.autorizaciones.all().order_by('-fecha_resolucion')
        
        self.elementos.append(Paragraph(
            f'<b>2. AUTORIZACIONES ({autorizaciones.count()})</b>',
            self.styles['SeccionTitulo']
        ))
        
        if autorizaciones.exists():
            datos_aut = [['N° Resolución', 'Tipo Servicio', 'Ámbito', 'Vigencia', 'Estado']]
            for aut in autorizaciones:
                vigencia = f"{aut.fecha_inicio_vigencia.strftime('%d/%m/%Y') if aut.fecha_inicio_vigencia else '-'} al {aut.fecha_fin_vigencia.strftime('%d/%m/%Y') if aut.fecha_fin_vigencia else '-'}"
                datos_aut.append([
                    Paragraph(aut.numero_resolucion, self.styles['TablaTexto']),
                    Paragraph(aut.tipo_servicio.nombre if aut.tipo_servicio else '-', self.styles['TablaTexto']),
                    Paragraph(aut.get_ambito_display(), self.styles['TablaTexto']),
                    Paragraph(vigencia, self.styles['TablaTexto']),
                    aut.get_estado_display()
                ])
            
            tabla_aut = Table(datos_aut, colWidths=[4*cm, 3*cm, 3.5*cm, 4*cm, 2.5*cm])
            tabla_aut.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ]))
            self.elementos.append(tabla_aut)
            
            # Rutas por autorización
            for aut in autorizaciones.filter(estado='VIGENTE'):
                if aut.rutas.exists():
                    self.elementos.append(Spacer(1, 0.3*cm))
                    self.elementos.append(Paragraph(
                        f'<i>Rutas de {aut.numero_resolucion}:</i>',
                        self.styles['TextoPequeno']
                    ))
                    rutas_texto = ', '.join([f"{r.origen} - {r.destino}" for r in aut.rutas.all()])
                    self.elementos.append(Paragraph(rutas_texto, self.styles['TextoPequeno']))
        else:
            self.elementos.append(Paragraph('No tiene autorizaciones registradas.', self.styles['TextoNormal']))
        
        self.elementos.append(Spacer(1, 0.5*cm))
        
        # ========== VEHÍCULOS ==========
        from apps.vehiculos.models import Vehiculo, HabilitacionVehicular
        vehiculos = Vehiculo.objects.filter(empresa_propietaria=self.empresa).order_by('placa')
        
        self.elementos.append(Paragraph(
            f'<b>3. FLOTA VEHICULAR ({vehiculos.count()})</b>',
            self.styles['SeccionTitulo']
        ))
        
        if vehiculos.exists():
            datos_veh = [['Placa', 'N° TUC', 'Marca/Modelo', 'Año', 'Tipo', 'Cap.', 'SOAT', 'CITV', 'Estado']]
            for veh in vehiculos:
                datos_veh.append([
                    Paragraph(veh.placa, self.styles['TablaTexto']),
                    Paragraph(veh.numero_tuc_vigente or '-', self.styles['TablaTexto']),
                    Paragraph(f"{veh.marca} {veh.modelo}", self.styles['TablaTexto']),
                    str(veh.anio_fabricacion) if veh.anio_fabricacion else '-',
                    Paragraph(veh.carroceria.nombre if veh.carroceria else '-', self.styles['TablaTexto']),
                    str(veh.capacidad_sentados) if veh.capacidad_sentados else '-',
                    veh.fecha_venc_soat.strftime('%d/%m/%y') if veh.fecha_venc_soat else '-',
                    veh.fecha_venc_citv.strftime('%d/%m/%y') if veh.fecha_venc_citv else '-',
                    veh.get_estado_display()
                ])
            
            tabla_veh = Table(datos_veh, colWidths=[1.8*cm, 2.2*cm, 2.5*cm, 1*cm, 1.8*cm, 0.8*cm, 1.8*cm, 1.8*cm, 1.8*cm])
            tabla_veh.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 6.5),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ]))
            self.elementos.append(tabla_veh)
        else:
            self.elementos.append(Paragraph('No tiene vehículos registrados.', self.styles['TextoNormal']))
        
        self.elementos.append(Spacer(1, 0.5*cm))
        
        # ========== CONDUCTORES ==========
        from apps.conductores.models import Conductor, HabilitacionConductor
        conductores = Conductor.objects.filter(empresa=self.empresa).order_by('apellido_paterno')
        
        self.elementos.append(Paragraph(
            f'<b>4. CONDUCTORES ({conductores.count()})</b>',
            self.styles['SeccionTitulo']
        ))
        
        if conductores.exists():
            datos_cond = [['DNI', 'Nombres y Apellidos', 'Licencia', 'Categoría', 'Vence Lic.', 'Estado']]
            for cond in conductores:
                datos_cond.append([
                    Paragraph(cond.dni, self.styles['TablaTexto']),
                    Paragraph(cond.nombre_completo, self.styles['TablaTexto']),
                    Paragraph(cond.licencia_numero or '-', self.styles['TablaTexto']),
                    Paragraph(cond.licencia_categoria or '-', self.styles['TablaTexto']),
                    cond.licencia_fecha_vencimiento.strftime('%d/%m/%y') if cond.licencia_fecha_vencimiento else '-',
                    cond.get_estado_display()
                ])
            
            tabla_cond = Table(datos_cond, colWidths=[2*cm, 5*cm, 2.5*cm, 1.8*cm, 2*cm, 2*cm])
            tabla_cond.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ]))
            self.elementos.append(tabla_cond)
        else:
            self.elementos.append(Paragraph('No tiene conductores registrados.', self.styles['TextoNormal']))
        
        self.elementos.append(Spacer(1, 0.5*cm))
        
        # ========== HABILITACIONES VIGENTES ==========
        self.elementos.append(Paragraph(
            '<b>5. HABILITACIONES VIGENTES</b>',
            self.styles['SeccionTitulo']
        ))
        
        # Habilitaciones vehiculares
        hab_vehiculos = HabilitacionVehicular.objects.filter(
            vehiculo__empresa_propietaria=self.empresa,
            estado='VIGENTE'
        ).select_related('vehiculo', 'autorizacion')
        
        self.elementos.append(Paragraph(
            f'<b>5.1 Habilitaciones Vehiculares ({hab_vehiculos.count()})</b>',
            self.styles['TextoNormal']
        ))
        
        if hab_vehiculos.exists():
            datos_habv = [['Placa', 'Autorización', 'Fecha Inicio', 'Fecha Fin', 'Estado']]
            for h in hab_vehiculos[:15]:  # Limitar a 15 para no exceder el espacio
                datos_habv.append([
                    Paragraph(h.vehiculo.placa, self.styles['TablaTexto']),
                    Paragraph(h.autorizacion.numero_resolucion if h.autorizacion else '-', self.styles['TablaTexto']),
                    h.fecha_inicio.strftime('%d/%m/%Y') if h.fecha_inicio else '-',
                    h.fecha_fin.strftime('%d/%m/%Y') if h.fecha_fin else 'Indefinido',
                    h.get_estado_display()
                ])
            
            tabla_habv = Table(datos_habv, colWidths=[2*cm, 4.5*cm, 2.5*cm, 2.5*cm, 2*cm])
            tabla_habv.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16a085')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ]))
            self.elementos.append(tabla_habv)
        else:
            self.elementos.append(Paragraph('Sin habilitaciones vehiculares vigentes.', self.styles['TextoPequeno']))
        
        self.elementos.append(Spacer(1, 0.3*cm))
        
        # Habilitaciones de conductores
        hab_conductores = HabilitacionConductor.objects.filter(
            empresa=self.empresa,
            estado='VIGENTE'
        ).select_related('conductor', 'autorizacion')
        
        self.elementos.append(Paragraph(
            f'<b>5.2 Habilitaciones de Conductores ({hab_conductores.count()})</b>',
            self.styles['TextoNormal']
        ))
        
        if hab_conductores.exists():
            datos_habc = [['DNI', 'Conductor', 'Autorización', 'Fecha Inicio', 'Estado']]
            for h in hab_conductores[:15]:
                datos_habc.append([
                    Paragraph(h.conductor.dni, self.styles['TablaTexto']),
                    Paragraph(h.conductor.nombre_completo, self.styles['TablaTexto']),
                    Paragraph(h.autorizacion.numero_resolucion if h.autorizacion else '-', self.styles['TablaTexto']),
                    h.fecha_inicio.strftime('%d/%m/%Y') if h.fecha_inicio else '-',
                    h.get_estado_display()
                ])
            
            tabla_habc = Table(datos_habc, colWidths=[2*cm, 4.5*cm, 4*cm, 2.5*cm, 2*cm])
            tabla_habc.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8e44ad')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ]))
            self.elementos.append(tabla_habc)
        else:
            self.elementos.append(Paragraph('Sin habilitaciones de conductores vigentes.', self.styles['TextoPequeno']))
        
        # ========== RESUMEN ESTADÍSTICO ==========
        self.elementos.append(Spacer(1, 0.5*cm))
        self.elementos.append(Paragraph(
            '<b>6. RESUMEN</b>',
            self.styles['SeccionTitulo']
        ))
        
        resumen = [
            ['Concepto', 'Total', 'Vigentes/Activos'],
            ['Autorizaciones', str(autorizaciones.count()), str(autorizaciones.filter(estado='VIGENTE').count())],
            ['Vehículos', str(vehiculos.count()), str(vehiculos.filter(estado='HABILITADO').count())],
            ['Conductores', str(conductores.count()), str(conductores.filter(estado='ACTIVO').count())],
            ['Hab. Vehiculares', str(HabilitacionVehicular.objects.filter(vehiculo__empresa_propietaria=self.empresa).count()), str(hab_vehiculos.count())],
            ['Hab. Conductores', str(HabilitacionConductor.objects.filter(empresa=self.empresa).count()), str(hab_conductores.count())],
        ]
        
        tabla_resumen = Table(resumen, colWidths=[6*cm, 3*cm, 4*cm])
        tabla_resumen.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')]),
        ]))
        self.elementos.append(tabla_resumen)
        
        self.agregar_pie_pagina()
        
        # Generar nombre de archivo
        nombre_archivo = f'ficha_empresa_{self.empresa.ruc}.pdf'
        return self.get_response(nombre_archivo)
