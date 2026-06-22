"""Genera el Manual de Usuario en formato Word (.docx) con estilos profesionales."""

from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml.ns import qn, nsmap
from docx.oxml import OxmlElement
from docx.shared import Cm, Pt, RGBColor, Inches


PRIMARY = RGBColor(0x0D, 0x47, 0xA1)      # azul institucional
ACCENT = RGBColor(0x15, 0x65, 0xC0)
DARK = RGBColor(0x21, 0x25, 0x29)
LIGHT_BG = RGBColor(0xE3, 0xF2, 0xFD)
HEADER_BG = "1565C0"
ALT_ROW = "F5F9FF"


def set_cell_shading(cell, color_hex):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color_hex)
    tc_pr.append(shd)


def set_cell_borders(cell, color="BFBFBF", size="4"):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        b = OxmlElement(f"w:{edge}")
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), size)
        b.set(qn("w:space"), "0")
        b.set(qn("w:color"), color)
        tc_borders.append(b)
    tc_pr.append(tc_borders)


def add_horizontal_rule(paragraph, color="1565C0"):
    p_pr = paragraph._p.get_or_add_pPr()
    p_bdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "12")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), color)
    p_bdr.append(bottom)
    p_pr.append(p_bdr)


def add_page_break(doc):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def style_run(run, *, bold=False, italic=False, size=None, color=None, font="Calibri"):
    run.font.name = font
    if size is not None:
        run.font.size = Pt(size)
    if color is not None:
        run.font.color.rgb = color
    run.bold = bold
    run.italic = italic


def add_paragraph(doc, text, *, size=11, bold=False, italic=False, color=None,
                  align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=4, indent=None):
    p = doc.add_paragraph()
    p.alignment = align
    if indent is not None:
        p.paragraph_format.left_indent = Cm(indent)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.25
    run = p.add_run(text)
    style_run(run, bold=bold, italic=italic, size=size, color=color)
    return p


def add_heading(doc, text, level=1, *, color=None):
    color = color or PRIMARY
    sizes = {1: 20, 2: 15, 3: 12, 4: 11}
    spaces = {1: 14, 2: 10, 3: 6, 4: 4}
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(18 if level == 1 else 12)
    p.paragraph_format.space_after = Pt(spaces[level])
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    style_run(run, bold=True, size=sizes[level], color=color)
    if level == 1:
        add_horizontal_rule(p)
    return p


def add_bullet(doc, text, *, level=0, bold_prefix=None):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.left_indent = Cm(0.75 + level * 0.75)
    p.paragraph_format.space_after = Pt(2)
    if bold_prefix:
        r1 = p.add_run(bold_prefix + " ")
        style_run(r1, bold=True, size=11)
        r2 = p.add_run(text)
        style_run(r2, size=11)
    else:
        r = p.add_run(text)
        style_run(r, size=11)
    return p


def add_numbered(doc, text):
    p = doc.add_paragraph(style="List Number")
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(text)
    style_run(r, size=11)
    return p


def add_callout(doc, text, *, kind="info"):
    palettes = {
        "info":    ("E3F2FD", "0D47A1", "INFO"),
        "warn":    ("FFF8E1", "F57F17", "IMPORTANTE"),
        "danger":  ("FFEBEE", "B71C1C", "ATENCION"),
        "tip":     ("E8F5E9", "1B5E20", "RECOMENDACION"),
    }
    bg, fg, label = palettes[kind]
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.rows[0].cells[0]
    set_cell_shading(cell, bg)
    set_cell_borders(cell, color=fg, size="6")
    cell.paragraphs[0].text = ""
    p = cell.paragraphs[0]
    r1 = p.add_run(f"{label}: ")
    style_run(r1, bold=True, size=10, color=RGBColor.from_string(fg))
    r2 = p.add_run(text)
    style_run(r2, size=10, color=DARK)
    p.paragraph_format.space_after = Pt(0)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def add_table(doc, headers, rows, *, col_widths=None, first_col_bold=False):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    if col_widths:
        for i, w in enumerate(col_widths):
            for cell in table.columns[i].cells:
                cell.width = Cm(w)

    header_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        cell = header_cells[i]
        cell.text = ""
        set_cell_shading(cell, HEADER_BG)
        set_cell_borders(cell, color="0D47A1", size="6")
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        style_run(r, bold=True, size=10, color=RGBColor(0xFF, 0xFF, 0xFF))

    for ri, row in enumerate(rows):
        cells = table.rows[ri + 1].cells
        for ci, val in enumerate(row):
            cell = cells[ci]
            cell.text = ""
            if ri % 2 == 1:
                set_cell_shading(cell, ALT_ROW)
            set_cell_borders(cell)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(str(val))
            bold = (first_col_bold and ci == 0)
            style_run(r, size=10, bold=bold, color=DARK)

    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


def add_field(doc, label, value):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    r1 = p.add_run(f"{label}: ")
    style_run(r1, bold=True, size=11, color=PRIMARY)
    r2 = p.add_run(value)
    style_run(r2, size=11, color=DARK)


def configure_styles(doc):
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    for s in ("List Bullet", "List Number"):
        if s in doc.styles:
            doc.styles[s].font.name = "Calibri"
            doc.styles[s].font.size = Pt(11)

    section = doc.sections[0]
    section.top_margin = Cm(2.2)
    section.bottom_margin = Cm(2.2)
    section.left_margin = Cm(2.4)
    section.right_margin = Cm(2.4)

    footer = section.footer
    f_par = footer.paragraphs[0]
    f_par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fr = f_par.add_run("Sistema de Autorizaciones y Habilitaciones Vehiculares - DRTC | Manual de Usuario v1.0")
    style_run(fr, size=8, italic=True, color=RGBColor(0x55, 0x55, 0x55))


def build_cover(doc):
    section = doc.sections[0]

    for _ in range(4):
        doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("DIRECCION REGIONAL DE TRANSPORTES Y COMUNICACIONES")
    style_run(r, bold=True, size=14, color=DARK)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("(DRTC)")
    style_run(r, bold=True, size=12, color=DARK)

    for _ in range(2):
        doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("MANUAL DE USUARIO")
    style_run(r, bold=True, size=32, color=PRIMARY)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_horizontal_rule(p)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Sistema de Gestion de Autorizaciones y\nHabilitaciones de Transporte Terrestre")
    style_run(r, bold=True, size=18, color=ACCENT)
    p.paragraph_format.line_spacing = 1.2

    for _ in range(2):
        doc.add_paragraph()

    # Caja con datos del documento
    tbl = doc.add_table(rows=4, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    info_rows = [
        ("Documento", "Manual de Usuario Final"),
        ("Version", "1.0"),
        ("Fecha de emision", date.today().strftime("%d / %m / %Y")),
        ("Plataforma", "Aplicacion web (Django + PostgreSQL)"),
    ]
    for i, (k, v) in enumerate(info_rows):
        c1, c2 = tbl.rows[i].cells
        c1.text = ""
        c2.text = ""
        set_cell_shading(c1, "1565C0")
        set_cell_shading(c2, "E3F2FD")
        set_cell_borders(c1, color="0D47A1", size="6")
        set_cell_borders(c2, color="90CAF9", size="6")
        r1 = c1.paragraphs[0].add_run(k)
        style_run(r1, bold=True, size=11, color=RGBColor(0xFF, 0xFF, 0xFF))
        r2 = c2.paragraphs[0].add_run(v)
        style_run(r2, size=11, color=DARK)
        for cell in (c1, c2):
            cell.width = Cm(6)

    for _ in range(3):
        doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Dirigido a personal administrativo, tecnico, legal,\ninspectores y administradores del sistema")
    style_run(r, italic=True, size=11, color=DARK)
    p.paragraph_format.line_spacing = 1.3

    add_page_break(doc)


def build_toc(doc):
    add_heading(doc, "Indice", level=1)
    items = [
        "1. Introduccion",
        "2. Objetivo del Manual",
        "3. Alcance del Sistema",
        "4. Publico Objetivo",
        "5. Requisitos para usar el sistema",
        "6. Acceso al sistema",
        "7. Inicio de sesion",
        "8. Descripcion general de la interfaz",
        "9. Roles y permisos",
        "10. Modulos del sistema",
        "     10.1  Dashboard / Panel de Control",
        "     10.2  Modulo de Empresas",
        "     10.3  Modulo de Autorizaciones",
        "     10.4  Modulo de Vehiculos",
        "     10.5  Modulo de Conductores",
        "     10.6  Modulo de Tramites (Expedientes)",
        "     10.7  Modulo de Consultas",
        "     10.8  Modulo de Reportes",
        "     10.9  Modulo de Notificaciones",
        "     10.10 Modulo de Configuracion",
        "     10.11 Modulo de Gestion de Usuarios",
        "     10.12 Modulo de Documentacion / Manuales",
        "11. Procedimientos paso a paso",
        "12. Mensajes de error frecuentes y solucion",
        "13. Recomendaciones para el usuario",
        "14. Glosario de terminos",
        "15. Anexos",
    ]
    for it in items:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        if it.startswith("     "):
            p.paragraph_format.left_indent = Cm(0.9)
            r = p.add_run(it.strip())
            style_run(r, size=11, color=DARK)
        else:
            r = p.add_run(it)
            style_run(r, bold=True, size=11, color=PRIMARY)
    add_page_break(doc)


def section_introduccion(doc):
    add_heading(doc, "1. Introduccion", level=1)
    add_paragraph(
        doc,
        "El Sistema de Gestion de Autorizaciones y Habilitaciones de Transporte Terrestre es una "
        "plataforma web institucional disenada para la Direccion Regional de Transportes y "
        "Comunicaciones (DRTC). Su finalidad es modernizar, digitalizar y agilizar la gestion "
        "administrativa de los expedientes vinculados al servicio de transporte terrestre de "
        "personas y carga ligera en el ambito regional.",
    )
    add_paragraph(
        doc,
        "El sistema centraliza el padron oficial de empresas de transporte, parque automotor y "
        "conductores, y administra el ciclo de vida completo de los expedientes administrativos "
        "desde su recepcion en Mesa de Partes hasta la emision de Resoluciones Directorales y "
        "Tarjetas Unicas de Circulacion (TUC).",
    )
    add_paragraph(
        doc,
        "La aplicacion funciona en navegador web, es responsiva (apta para computadora, tableta y "
        "celular) y ofrece modulos diferenciados segun el rol del usuario.",
    )


def section_objetivo(doc):
    add_heading(doc, "2. Objetivo del Manual", level=1)
    add_paragraph(
        doc,
        "El presente Manual tiene por objetivo proporcionar al usuario final una guia clara, "
        "ordenada y detallada para el correcto uso de las funcionalidades del sistema, de modo "
        "que pueda:",
    )
    for item in [
        "Comprender la estructura general de la plataforma.",
        "Acceder con su usuario y contrasena institucional.",
        "Operar los modulos correspondientes a su rol.",
        "Registrar, consultar, modificar y dar seguimiento a expedientes administrativos.",
        "Generar reportes y documentos oficiales.",
        "Identificar y resolver los mensajes de error mas frecuentes.",
    ]:
        add_bullet(doc, item)


def section_alcance(doc):
    add_heading(doc, "3. Alcance del Sistema", level=1)
    add_paragraph(doc, "El sistema cubre las siguientes operaciones:")
    add_table(
        doc,
        ["Categoria", "Funcionalidades"],
        [
            ("Padron institucional", "Registro y mantenimiento de empresas, vehiculos y conductores"),
            ("Autorizaciones", "Emision, vigencia y control de resoluciones de autorizacion"),
            ("Habilitaciones", "Generacion y control de TUC y habilitaciones de conductores"),
            ("Tramites", "Flujo administrativo completo con maquina de estados (workflow)"),
            ("Documentos", "Carga, descarga y verificacion de archivos PDF"),
            ("Consultas", "Consulta publica por expediente y consulta interna por placa/DNI"),
            ("Reportes", "Listados PDF, exportacion a Excel y dashboards estadisticos"),
            ("Seguridad", "Autenticacion, control de acceso por rol, auditoria y notificaciones"),
        ],
        col_widths=[4.5, 11],
        first_col_bold=True,
    )
    add_callout(
        doc,
        "No esta incluido en el alcance del sistema: la cobranza directa en linea, la integracion "
        "con SUNAT en linea, ni la fiscalizacion en via publica con dispositivos moviles externos.",
        kind="warn",
    )


def section_publico(doc):
    add_heading(doc, "4. Publico Objetivo", level=1)
    add_paragraph(doc, "Este manual esta dirigido a:")
    for item in [
        "Personal administrativo de la DRTC, sin necesidad de conocimientos tecnicos avanzados de informatica.",
        "Funcionarios de Mesa de Partes, Evaluacion Tecnica, Asesoria Legal, Direccion Administrativa y Direccion General.",
        "Inspectores y consultores externos autorizados a verificar habilitaciones.",
        "Administradores del sistema, encargados de la configuracion y mantenimiento.",
    ]:
        add_bullet(doc, item)


def section_requisitos(doc):
    add_heading(doc, "5. Requisitos para usar el sistema", level=1)
    add_table(
        doc,
        ["Recurso", "Requisito minimo recomendado"],
        [
            ("Equipo", "Computadora, laptop, tableta o smartphone"),
            ("Sistema operativo", "Windows 10, macOS, Linux, Android o iOS"),
            ("Navegador web", "Google Chrome, Microsoft Edge, Mozilla Firefox o Safari (ultima version estable)"),
            ("Conexion a internet", "Banda ancha estable (minimo 5 Mbps)"),
            ("Resolucion de pantalla", "1280 x 720 pixeles o superior"),
            ("Cuenta de usuario", "Usuario y contrasena proporcionados por el Administrador del sistema"),
            ("Software adicional", "Lector de PDF (Adobe Acrobat Reader o equivalente)"),
        ],
        col_widths=[5, 10.5],
        first_col_bold=True,
    )
    add_callout(
        doc,
        "No se requiere instalacion de software adicional. El sistema funciona integramente en el navegador.",
        kind="info",
    )


def section_acceso(doc):
    add_heading(doc, "6. Acceso al sistema", level=1)
    for txt in [
        "Abrir el navegador web.",
        "Ingresar la direccion URL del sistema, proporcionada por la Oficina de Tecnologias de la Informacion de la DRTC. Por ejemplo: https://autorizaciones.drtc.gob.pe/",
        "El sistema mostrara automaticamente la pantalla de Inicio de Sesion.",
    ]:
        add_numbered(doc, txt)
    add_callout(
        doc,
        "Se recomienda guardar la direccion como favorita en el navegador para acceder mas rapido en sesiones posteriores.",
        kind="tip",
    )


def section_login(doc):
    add_heading(doc, "7. Inicio de sesion", level=1)

    add_heading(doc, "7.1 Pantalla de Login", level=2)
    add_paragraph(doc, "La pantalla de inicio de sesion contiene los siguientes elementos:")
    add_table(
        doc,
        ["Elemento", "Descripcion"],
        [
            ("Logo DRTC", "Identificacion visual del sistema"),
            ("Campo Usuario", "Nombre de usuario asignado por el Administrador"),
            ("Campo Contrasena", "Contrasena personal (minimo 8 caracteres)"),
            ("Boton Iniciar Sesion", "Inicia la autenticacion"),
            ("Mensaje de error", "Aparece si los datos son incorrectos"),
        ],
        col_widths=[5, 10.5],
        first_col_bold=True,
    )

    add_heading(doc, "7.2 Procedimiento", level=2)
    for t in [
        "Ingrese su usuario en el primer campo.",
        "Ingrese su contrasena en el segundo campo.",
        "Pulse el boton 'Iniciar Sesion'.",
        "Si los datos son correctos, el sistema lo redirige al Dashboard.",
        "Si los datos son incorrectos, aparece el mensaje: 'Usuario o contrasena incorrectos.'",
    ]:
        add_numbered(doc, t)

    add_heading(doc, "7.3 Cierre de sesion", level=2)
    for t in [
        "Desplegar el menu superior derecho (donde aparece el nombre del usuario).",
        "Hacer clic en 'Cerrar Sesion'.",
        "El sistema mostrara el mensaje: 'Ha cerrado sesion exitosamente.'",
    ]:
        add_numbered(doc, t)

    add_heading(doc, "7.4 Cambio de contrasena", level=2)
    for t in [
        "Hacer clic en el nombre del usuario en la esquina superior derecha.",
        "Seleccionar 'Cambiar Contrasena'.",
        "Ingresar la contrasena actual.",
        "Ingresar la nueva contrasena (dos veces).",
        "Pulsar 'Guardar'.",
    ]:
        add_numbered(doc, t)
    add_callout(
        doc,
        "La contrasena debe cumplir con los lineamientos de seguridad: minimo 8 caracteres, "
        "evitar datos personales y no compartirla con terceros.",
        kind="warn",
    )


def section_interfaz(doc):
    add_heading(doc, "8. Descripcion general de la interfaz", level=1)
    add_paragraph(doc, "Tras iniciar sesion, la pantalla principal presenta tres zonas:")

    add_heading(doc, "8.1 Barra lateral izquierda (menu principal)", level=2)
    add_paragraph(doc, "Contiene los accesos a los modulos disponibles segun el rol del usuario. Esta organizada en secciones:")
    for s in [
        "Menu Principal: Dashboard.",
        "Gestion: Empresas, Autorizaciones, Vehiculos, Conductores.",
        "Tramites: Todos los Tramites, Nuevo Tramite.",
        "Consultas: Consulta por Placa, Consulta de Conductor.",
        "Reportes: Reportes, Estadisticas.",
        "Administracion: Configuracion, Usuarios, Admin Django (solo Administrador).",
        "Ayuda: Manuales de Usuario.",
    ]:
        add_bullet(doc, s)

    add_heading(doc, "8.2 Barra superior (cabecera)", level=2)
    add_table(
        doc,
        ["Elemento", "Funcion"],
        [
            ("Logotipo / nombre del sistema", "Identificacion institucional"),
            ("Campana de notificaciones", "Acceso a notificaciones no leidas"),
            ("Etiqueta de Rol", "Muestra el rol del usuario activo"),
            ("Menu de usuario", "Mi Perfil, Cambiar Contrasena, Cerrar Sesion"),
        ],
        col_widths=[6, 9.5],
        first_col_bold=True,
    )

    add_heading(doc, "8.3 Area central de trabajo", level=2)
    add_paragraph(
        doc,
        "Es el espacio donde se cargan los listados, formularios, detalles y reportes segun la "
        "opcion seleccionada en el menu lateral.",
    )
    add_callout(
        doc,
        "En tabletas y celulares el menu lateral se oculta y se accede mediante el boton (menu) "
        "ubicado en la esquina superior izquierda.",
        kind="info",
    )


def section_roles(doc):
    add_heading(doc, "9. Roles y permisos", level=1)
    add_paragraph(
        doc,
        "El sistema implementa un modelo RBAC (Role Based Access Control). Cada usuario tiene "
        "asignado un rol que define que puede ver y hacer.",
    )

    add_heading(doc, "9.1 Roles disponibles", level=2)
    add_table(
        doc,
        ["Rol", "Permisos principales"],
        [
            ("ADMIN_SISTEMA (Administrador)", "Acceso total. Configura usuarios, catalogos y todos los modulos."),
            ("MESA_PARTES (Mesa de Partes)", "Recibe tramites, registra solicitudes, sube documentos y deriva expedientes."),
            ("ESPECIALISTA_TECNICO (Tecnico)", "Evalua cumplimiento tecnico de la flota y conductores. Observa o aprueba."),
            ("ASESORIA_LEGAL (Asesor Legal)", "Revisa el sustento legal. Emite dictamen y puede observar o aprobar."),
            ("DIRECTOR_GENERAL", "Firma y aprueba las resoluciones finales."),
            ("DIRECTOR_ADMINISTRATIVO", "Revisa, deriva y firma segun el tipo de tramite."),
            ("CONTROL_CALIDAD", "Verifica calidad de la informacion antes de la firma."),
            ("CONSULTA_INTERNA", "Solo lectura, sin modificar datos."),
            ("CONSULTA_INSPECTOR (Inspector)", "Consultas de campo por placa y por conductor."),
        ],
        col_widths=[5, 10.5],
        first_col_bold=True,
    )

    add_heading(doc, "9.2 Matriz resumen de capacidades", level=2)
    add_table(
        doc,
        ["Capacidad", "ADMIN", "MESA", "TECNICO", "LEGAL", "DIRECTOR", "CC", "C.INT", "INSPECTOR"],
        [
            ("Ver Dashboard", "SI", "SI", "SI", "SI", "SI", "SI", "SI", "SI"),
            ("Crear/editar empresas", "SI", "SI", "NO", "NO", "NO", "NO", "NO", "NO"),
            ("Crear/editar autorizaciones", "SI", "SI", "NO", "NO", "NO", "NO", "NO", "NO"),
            ("Crear/editar vehiculos", "SI", "SI", "SI", "NO", "NO", "NO", "NO", "NO"),
            ("Crear/editar conductores", "SI", "SI", "SI", "NO", "NO", "NO", "NO", "NO"),
            ("Crear tramites", "SI", "SI", "NO", "NO", "NO", "NO", "NO", "NO"),
            ("Evaluar tecnicamente", "SI", "NO", "SI", "NO", "NO", "NO", "NO", "NO"),
            ("Evaluar legalmente", "SI", "NO", "NO", "SI", "NO", "NO", "NO", "NO"),
            ("Firmar / aprobar", "SI", "NO", "NO", "NO", "SI", "NO", "NO", "NO"),
            ("Consultas", "SI", "SI", "SI", "SI", "SI", "SI", "SI", "SI"),
            ("Reportes", "SI", "SI", "SI", "SI", "SI", "SI", "SI", "NO"),
            ("Configuracion del sistema", "SI", "NO", "NO", "NO", "NO", "NO", "NO", "NO"),
            ("Gestion de usuarios", "SI", "NO", "NO", "NO", "NO", "NO", "NO", "NO"),
        ],
        col_widths=[5.4, 1.4, 1.3, 1.4, 1.3, 1.5, 1.0, 1.2, 1.6],
        first_col_bold=True,
    )
    add_callout(doc, "La aplicacion oculta automaticamente las opciones del menu a las que el rol no tiene acceso.", kind="info")


def section_modulos(doc):
    add_heading(doc, "10. Modulos del sistema", level=1)

    # 10.1 Dashboard
    add_heading(doc, "10.1 Dashboard / Panel de Control", level=2)
    add_paragraph(
        doc,
        "Es la pantalla principal del usuario tras iniciar sesion. Muestra indicadores clave y "
        "accesos rapidos segun el rol.",
    )
    add_heading(doc, "Indicadores generales (todos los roles)", level=3)
    add_table(
        doc,
        ["Indicador", "Descripcion"],
        [
            ("Tramites pendientes", "Expedientes que aun no han sido aprobados, denegados ni cerrados."),
            ("Tramites del dia", "Expedientes registrados hoy."),
            ("Empresas activas", "Empresas en estado 'Activa' en el padron."),
            ("Vehiculos habilitados", "Vehiculos con habilitacion vigente."),
        ],
        col_widths=[5, 10.5],
        first_col_bold=True,
    )
    add_heading(doc, "Bloques especificos por rol", level=3)
    for s in [
        "Administrador / Director: Tramites recientes, totales de usuarios activos.",
        "Mesa de Partes: Tramites por recibir.",
        "Especialista Tecnico: Tramites en evaluacion tecnica.",
        "Asesoria Legal: Tramites en revision legal.",
        "Director: Tramites pendientes de firma.",
        "Inspector / Consulta interna: Accesos directos a consultas y reportes.",
    ]:
        add_bullet(doc, s)

    # 10.2 Empresas
    add_heading(doc, "10.2 Modulo de Empresas", level=2)
    add_field(doc, "Ruta de acceso", "Menu lateral -> Gestion -> Empresas")
    add_paragraph(
        doc,
        "Administra el padron oficial de empresas autorizadas para prestar el servicio de transporte.",
    )
    add_heading(doc, "Listado de empresas", level=3)
    for s in [
        "Tabla con RUC, Razon Social, Representante Legal, Provincia / Distrito, Estado y acciones.",
        "Buscador por RUC, razon social o representante.",
        "Filtros por estado (Activa / Inactiva).",
        "Boton '+ Nueva Empresa' (solo roles autorizados).",
        "Boton 'Exportar Excel'.",
    ]:
        add_bullet(doc, s)
    add_heading(doc, "Campos del formulario de Empresa", level=3)
    add_table(
        doc,
        ["Campo", "Descripcion", "Validacion"],
        [
            ("RUC", "Registro Unico de Contribuyentes", "11 digitos, debe comenzar con 10, 15, 17 o 20"),
            ("Razon Social", "Nombre oficial registrado en SUNAT", "Obligatorio, hasta 255 caracteres"),
            ("Nombre Comercial", "Nombre con el que opera", "Opcional"),
            ("Domicilio Fiscal", "Direccion registrada", "Obligatorio"),
            ("Departamento", "Por defecto: Madre de Dios", "Obligatorio"),
            ("Provincia", "Provincia del domicilio fiscal", "Obligatorio"),
            ("Distrito", "Distrito del domicilio fiscal", "Obligatorio"),
            ("Representante Legal", "Nombre completo", "Obligatorio"),
            ("DNI del Representante", "8 digitos numericos", "Obligatorio"),
            ("Telefono", "Fijo o celular", "Opcional"),
            ("Correo Electronico", "Email institucional", "Opcional, formato valido"),
            ("Estado", "Activa / Inactiva", "Por defecto Activa"),
            ("Observaciones", "Notas adicionales", "Opcional"),
        ],
        col_widths=[4.5, 6, 5],
        first_col_bold=True,
    )
    add_callout(
        doc,
        "Si una empresa pasa a estado 'Inactiva', todas sus autorizaciones quedan suspendidas "
        "automaticamente y sus habilitaciones de vehiculos y conductores se marcan como 'No "
        "habilitado' hasta su reactivacion.",
        kind="warn",
    )

    # 10.3 Autorizaciones
    add_heading(doc, "10.3 Modulo de Autorizaciones", level=2)
    add_field(doc, "Ruta de acceso", "Menu lateral -> Gestion -> Autorizaciones")
    add_paragraph(
        doc,
        "Permite registrar las resoluciones administrativas que autorizan a una empresa a prestar el servicio.",
    )
    add_heading(doc, "Funcionalidades", level=3)
    for s in [
        "Listado con filtro por empresa, estado y rango de fechas.",
        "Detalle con historial de modificaciones.",
        "Asociacion a rutas y frecuencias configuradas en el catalogo.",
        "Carga del archivo PDF de la resolucion.",
    ]:
        add_bullet(doc, s)
    add_heading(doc, "Campos del formulario", level=3)
    add_table(
        doc,
        ["Campo", "Descripcion", "Validacion"],
        [
            ("Empresa", "Empresa beneficiaria", "Obligatorio (debe estar activa)"),
            ("Numero de Resolucion", "Identificador unico", "Obligatorio, unico"),
            ("Fecha de Resolucion", "Fecha de emision", "Obligatorio"),
            ("Archivo de Resolucion", "PDF firmado", "Opcional"),
            ("Fecha Inicio de Vigencia", "Inicio del periodo", "Obligatorio"),
            ("Fecha Fin de Vigencia", "Vencimiento del periodo", "Obligatorio (mayor a inicio)"),
            ("Ambito Regional", "Departamento donde opera", "Obligatorio"),
            ("Tipo de Servicio", "Servicio autorizado (catalogo)", "Obligatorio"),
            ("Modalidad", "Texto descriptivo", "Opcional"),
            ("Rutas Autorizadas", "Seleccion multiple", "Opcional"),
            ("Frecuencias Asignadas", "Seleccion multiple", "Opcional"),
            ("Descripcion de Rutas", "Texto libre", "Opcional"),
            ("Estado", "Vigente / Vencida / Suspendida / Cancelada", "Por defecto Vigente"),
        ],
        col_widths=[4.5, 6, 5],
        first_col_bold=True,
    )
    add_heading(doc, "Estados de la Autorizacion", level=3)
    add_table(
        doc,
        ["Estado", "Significado"],
        [
            ("VIGENTE", "Autorizacion activa dentro del periodo permitido."),
            ("VENCIDA", "Fecha fin pasada o estado modificado."),
            ("SUSPENDIDA", "Suspension por sancion o empresa inactiva."),
            ("CANCELADA", "Anulada definitivamente."),
        ],
        col_widths=[4, 11.5],
        first_col_bold=True,
    )

    # 10.4 Vehiculos
    add_heading(doc, "10.4 Modulo de Vehiculos", level=2)
    add_field(doc, "Ruta de acceso", "Menu lateral -> Gestion -> Vehiculos")
    add_paragraph(doc, "Administra la ficha tecnica y el ciclo de vida del parque automotor habilitado.")
    add_heading(doc, "Campos del formulario", level=3)
    add_table(
        doc,
        ["Campo", "Descripcion", "Validacion"],
        [
            ("Placa", "Placa del vehiculo (ABC-123)", "Obligatorio, formato valido"),
            ("Empresa Propietaria", "Empresa registrada", "Obligatorio"),
            ("Marca", "Marca del vehiculo", "Obligatorio"),
            ("Modelo", "Modelo del vehiculo", "Obligatorio"),
            ("Ano de Fabricacion", "Ano del vehiculo", "Obligatorio, minimo 1995"),
            ("Color", "Color del vehiculo", "Opcional"),
            ("Numero de Serie/Chasis", "Identificador", "Opcional"),
            ("Numero de Motor", "Identificador", "Opcional"),
            ("Capacidad de Pasajeros Sentados", "Cantidad", "Obligatorio"),
            ("Peso Bruto (kg)", "Peso vehicular", "Opcional"),
            ("Categoria", "M1, M2, M3, etc.", "Opcional"),
            ("Carroceria", "Tipo segun categoria", "Opcional"),
            ("Estado", "Propuesto / Habilitado / Baja / No Habilitado", "Por defecto Propuesto"),
            ("Numero TIV", "Tarjeta de Identificacion Vehicular", "Opcional"),
            ("Fecha Venc. SOAT", "Vencimiento del SOAT", "Opcional"),
            ("Fecha Venc. CITV", "Vencimiento de Inspeccion Tecnica", "Opcional"),
            ("Autorizacion Principal", "Resolucion vinculada", "Opcional"),
            ("Vehiculo Sustituido", "Vehiculo previo (sustituciones)", "Opcional"),
            ("Observaciones", "Notas", "Opcional"),
        ],
        col_widths=[5, 6, 4.5],
        first_col_bold=True,
    )
    add_heading(doc, "Estados del vehiculo", level=3)
    add_table(
        doc,
        ["Estado", "Significado"],
        [
            ("PROPUESTO", "Aun no habilitado, en proceso."),
            ("HABILITADO", "Habilitado con TUC vigente."),
            ("BAJA", "Dado de baja definitivamente."),
            ("NO_HABILITADO", "Suspendido temporalmente por causa externa."),
        ],
        col_widths=[4, 11.5],
        first_col_bold=True,
    )
    add_heading(doc, "Habilitacion Vehicular (TUC)", level=3)
    for s in [
        "Numero de Habilitacion.",
        "Numero de TUC (Tarjeta Unica de Circulacion).",
        "Fecha de Inicio y Fecha de Fin.",
        "Estado: VIGENTE, BAJA, SUSPENDIDA o CANCELADA.",
        "Fechas de expedicion de TUC y de autorizacion del transportista.",
        "Tramite de origen (vinculo trazable).",
    ]:
        add_bullet(doc, s)

    # 10.5 Conductores
    add_heading(doc, "10.5 Modulo de Conductores", level=2)
    add_field(doc, "Ruta de acceso", "Menu lateral -> Gestion -> Conductores")
    add_paragraph(doc, "Gestiona el padron de conductores autorizados y sus licencias.")
    add_heading(doc, "Campos del formulario", level=3)
    add_table(
        doc,
        ["Campo", "Descripcion", "Validacion"],
        [
            ("Empresa", "Empresa a la que pertenece", "Obligatorio"),
            ("DNI", "Documento Nacional de Identidad", "8 digitos, unico"),
            ("Nombres", "Nombres completos", "Obligatorio"),
            ("Apellido Paterno", "-", "Obligatorio"),
            ("Apellido Materno", "-", "Obligatorio"),
            ("Fecha de Nacimiento", "-", "Obligatorio, minimo ano 1930"),
            ("Direccion", "Direccion del conductor", "Opcional"),
            ("Telefono", "Contacto", "Opcional"),
            ("Correo Electronico", "Email", "Opcional"),
            ("Numero de Licencia", "Numero de licencia", "Obligatorio"),
            ("Categoria de Licencia", "A-I, A-II-A, A-II-B, A-III-A, A-III-B, A-III-C", "Obligatorio"),
            ("Fecha de Emision de Licencia", "-", "Obligatorio"),
            ("Fecha de Vencimiento de Licencia", "-", "Obligatorio"),
            ("Estado", "Activo / Inactivo", "Por defecto Activo"),
            ("Observaciones", "Notas", "Opcional"),
        ],
        col_widths=[5, 6, 4.5],
        first_col_bold=True,
    )
    add_callout(
        doc,
        "Restriccion importante: un mismo conductor NO puede tener habilitaciones vigentes en dos "
        "empresas simultaneamente. El sistema bloqueara el registro si detecta duplicidad.",
        kind="danger",
    )

    # 10.6 Tramites
    add_heading(doc, "10.6 Modulo de Tramites (Expedientes)", level=2)
    add_field(doc, "Ruta de acceso", "Menu lateral -> Tramites -> Todos los Tramites / Nuevo Tramite")
    add_paragraph(
        doc,
        "Es el nucleo operativo del sistema. Permite registrar, derivar, observar, aprobar o "
        "denegar los expedientes administrativos siguiendo un flujo de estados controlado (FSM).",
    )
    add_heading(doc, "Tipos de Tramite soportados", level=3)
    add_table(
        doc,
        ["Codigo", "Tipo"],
        [
            ("AUTORIZACION_INICIAL", "Autorizacion Inicial"),
            ("AUTORIZACION_RUTA", "Autorizacion de Ruta"),
            ("MODIFICACION_AUTORIZACION", "Actualizacion de Empresa y Autorizacion"),
            ("RENOVACION_AUTORIZACION", "Renovacion de Autorizacion"),
            ("RENOVACION_TUC", "Renovacion de TUC"),
            ("BAJA_AUTORIZACION", "Baja Voluntaria de Autorizacion"),
            ("SUSPENSION_AUTORIZACION", "Suspension por Sancion"),
            ("INCREMENTO_FLOTA", "Incremento de Flota"),
            ("SUSTITUCION_VEHICULO", "Sustitucion de Vehiculo"),
            ("BAJA_VEHICULO", "Baja de Vehiculo"),
            ("HABILITACION_CONDUCTOR", "Habilitacion de Conductor"),
            ("BAJA_CONDUCTOR", "Baja de Conductor"),
        ],
        col_widths=[6, 9.5],
        first_col_bold=True,
    )
    add_heading(doc, "Estados del Tramite (Flujo FSM)", level=3)
    add_table(
        doc,
        ["Estado", "Significado"],
        [
            ("RECIBIDO", "Tramite ingresado en Mesa de Partes."),
            ("EN_CONTROL_CALIDAD", "En verificacion previa (bajas, renovaciones)."),
            ("EN_EVAL_TECNICA", "En evaluacion del especialista tecnico."),
            ("EN_DIRECCION_ADMINISTRATIVA", "En revision y derivacion administrativa."),
            ("EN_DIRECCION_GENERAL", "En despacho de Direccion General."),
            ("OBSERVADO", "Presenta observaciones por subsanar."),
            ("EN_REVISION_LEGAL", "En Asesoria Legal."),
            ("PENDIENTE_FIRMA", "Listo para firma del Director."),
            ("APROBADO", "Aprobado y emitido."),
            ("DENEGADO", "Denegado de forma definitiva."),
            ("CERRADO", "Archivado tras conclusion."),
        ],
        col_widths=[6, 9.5],
        first_col_bold=True,
    )
    add_heading(doc, "Identificacion del expediente", level=3)
    add_paragraph(
        doc,
        "El sistema genera automaticamente un numero de expediente con el formato:",
    )
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("EXP-YYYY-NNNNN     (ejemplo: EXP-2026-00045)")
    style_run(r, bold=True, size=12, color=PRIMARY, font="Consolas")
    add_paragraph(doc, "Adicionalmente se puede registrar un N° de Expediente Hoja de Ruta ingresado por el usuario.")

    add_heading(doc, "Subsecciones dentro del tramite", level=3)
    add_table(
        doc,
        ["Subseccion", "Contenido"],
        [
            ("Documentos", "Adjuntar PDFs: solicitud, informes tecnicos, resoluciones, SOAT, CITV, licencia, DNI, contrato, etc."),
            ("Recibos de Pago", "Registrar los recibos de tasa administrativa."),
            ("Vehiculos en Tramite", "Listar vehiculos involucrados."),
            ("Conductores en Tramite", "Listar conductores involucrados."),
            ("Historial", "Trazabilidad inmutable de cada cambio de estado, observador y comentarios."),
        ],
        col_widths=[5, 10.5],
        first_col_bold=True,
    )
    add_heading(doc, "Acciones del tramite (segun estado y rol)", level=3)
    add_table(
        doc,
        ["Accion", "Quien", "Estado origen", "Estado destino"],
        [
            ("Enviar a Evaluacion Tecnica", "Mesa de Partes", "RECIBIDO", "EN_EVAL_TECNICA"),
            ("Enviar a Control de Calidad", "Mesa de Partes", "RECIBIDO", "EN_CONTROL_CALIDAD / PENDIENTE_FIRMA"),
            ("Observar (tecnico)", "Especialista Tecnico", "EN_EVAL_TECNICA", "OBSERVADO"),
            ("Subsanar observaciones", "Mesa de Partes / responsable", "OBSERVADO", "EN_EVAL_TECNICA"),
            ("Aprobar evaluacion tecnica", "Especialista Tecnico", "EN_EVAL_TECNICA", "EN_REVISION_LEGAL / PENDIENTE_FIRMA"),
            ("Enviar a Direccion Administrativa", "Especialista Tecnico", "EN_EVAL_TECNICA", "EN_DIRECCION_ADMINISTRATIVA"),
            ("Enviar a Direccion General", "Director Administrativo", "EN_DIRECCION_ADMINISTRATIVA", "EN_DIRECCION_GENERAL"),
            ("Observar (legal)", "Asesoria Legal", "EN_REVISION_LEGAL", "OBSERVADO"),
            ("Aprobar (legal)", "Asesoria Legal", "EN_REVISION_LEGAL", "PENDIENTE_FIRMA"),
            ("Firmar / Aprobar", "Director General", "PENDIENTE_FIRMA", "APROBADO"),
            ("Denegar", "Director", "varios", "DENEGADO"),
            ("Cerrar", "Mesa de Partes / Admin", "APROBADO", "CERRADO"),
        ],
        col_widths=[4.8, 3.8, 3.2, 3.7],
        first_col_bold=True,
    )
    add_callout(
        doc,
        "Las transiciones estan protegidas: solo el rol autorizado puede ejecutar cada accion y "
        "siempre quedan registradas en el Historial del Tramite.",
        kind="warn",
    )

    # 10.7 Consultas
    add_heading(doc, "10.7 Modulo de Consultas", level=2)
    add_paragraph(doc, "Permite verificar informacion rapidamente. Se divide en tres tipos:")
    add_heading(doc, "10.7.1 Consulta publica de Tramite (sin login)", level=3)
    for s in [
        "Acceso por URL: /consulta-tramite/",
        "El ciudadano ingresa el numero de expediente (formato EXP-YYYY-NNNNN).",
        "El sistema muestra: tipo y estado, empresa, solicitante, ultima observacion (si existe), area y fecha.",
    ]:
        add_bullet(doc, s)
    add_heading(doc, "10.7.2 Consulta por Placa (interna - inspectores)", level=3)
    for s in [
        "Menu: Consultas -> Consulta por Placa.",
        "Datos del vehiculo (marca, modelo, ano, color).",
        "Empresa propietaria.",
        "Estado de habilitacion / TUC vigente.",
        "Vigencia de SOAT y CITV.",
        "Autorizacion principal vinculada.",
    ]:
        add_bullet(doc, s)
    add_heading(doc, "10.7.3 Consulta de Conductor (por DNI)", level=3)
    for s in [
        "Menu: Consultas -> Consulta de Conductor.",
        "Datos personales del conductor.",
        "Empresa donde esta habilitado.",
        "Categoria y vigencia de la licencia.",
        "Estado de habilitacion.",
    ]:
        add_bullet(doc, s)
    add_heading(doc, "10.7.4 API REST", level=3)
    add_table(
        doc,
        ["Endpoint", "Funcion"],
        [
            ("GET /api/consulta/placa/{placa}/", "Consulta por placa"),
            ("GET /api/consulta/conductor/{dni}/", "Consulta por DNI de conductor"),
            ("POST /api/consulta/verificar-key/", "Verifica validez de la API Key"),
        ],
        col_widths=[7, 8.5],
        first_col_bold=True,
    )
    add_callout(doc, "La gestion de API Keys es responsabilidad del Administrador del sistema.", kind="info")

    # 10.8 Reportes
    add_heading(doc, "10.8 Modulo de Reportes", level=2)
    add_field(doc, "Ruta de acceso", "Menu lateral -> Reportes")
    add_heading(doc, "Reportes en PDF", level=3)
    add_table(
        doc,
        ["Reporte", "Contenido"],
        [
            ("Reporte de Empresas", "Listado oficial de empresas registradas."),
            ("Reporte de Autorizaciones", "Resoluciones vigentes, vencidas, suspendidas."),
            ("Reporte de Vehiculos", "Parque automotor por empresa o estado."),
            ("Reporte de Conductores", "Padron de conductores habilitados."),
            ("Reporte de Tramites", "Expedientes por periodo y estado."),
            ("Reporte de Resoluciones", "Resoluciones emitidas."),
            ("Reporte de Vencimientos", "SOAT, CITV, licencias y autorizaciones proximas a vencer."),
            ("Ficha completa de Empresa", "Datos integrales por empresa: flota, conductores y autorizaciones."),
        ],
        col_widths=[5.5, 10],
        first_col_bold=True,
    )
    add_heading(doc, "Exportacion a Excel", level=3)
    for s in ["Empresas", "Autorizaciones", "Vehiculos", "Conductores", "Tramites"]:
        add_bullet(doc, s)
    add_heading(doc, "Estadisticas", level=3)
    add_paragraph(doc, "Menu: Reportes -> Estadisticas. Graficos:")
    for s in [
        "Tramites por estado.",
        "Tramites por tipo.",
        "Vehiculos por tipo de servicio.",
        "Vencimientos proximos.",
    ]:
        add_bullet(doc, s)

    # 10.9 Notificaciones
    add_heading(doc, "10.9 Modulo de Notificaciones", level=2)
    add_heading(doc, "Donde verlo", level=3)
    for s in [
        "Icono de campana en la barra superior: notificaciones no leidas.",
        "Menu: Notificaciones -> Lista completa.",
    ]:
        add_bullet(doc, s)
    add_heading(doc, "Tipos de notificacion", level=3)
    add_table(
        doc,
        ["Tipo", "Descripcion"],
        [
            ("Tramite Recibido", "Nuevo expediente en mi bandeja."),
            ("Tramite en Evaluacion Tecnica", "Pasa a evaluacion."),
            ("Tramite Observado", "Hay observaciones pendientes."),
            ("Tramite Subsanado", "El solicitante respondio a las observaciones."),
            ("Tramite en Revision Legal", "Pasa a Asesoria Legal."),
            ("Tramite Pendiente de Firma", "Espera firma del Director."),
            ("Tramite Aprobado", "Cierre favorable."),
            ("Tramite Denegado", "Cierre desfavorable."),
            ("Vencimiento de Autorizacion", "Alerta de vencimiento proximo."),
            ("Vencimiento de SOAT", "Alerta de SOAT."),
            ("Vencimiento de CITV", "Alerta de CITV."),
            ("Vencimiento de Licencia", "Alerta de licencia."),
            ("Vencimiento de Habilitacion", "Alerta de habilitacion."),
            ("Plazo de Subsanacion", "Aviso por plazo proximo a vencer."),
            ("Sistema", "Notificaciones administrativas."),
        ],
        col_widths=[5.5, 10],
        first_col_bold=True,
    )
    add_heading(doc, "Prioridades", level=3)
    add_table(
        doc,
        ["Color", "Prioridad"],
        [
            ("Rojo", "Urgente"),
            ("Amarillo", "Alta"),
            ("Azul", "Media"),
            ("Gris", "Baja"),
        ],
        col_widths=[4, 11.5],
        first_col_bold=True,
    )

    # 10.10 Configuracion
    add_heading(doc, "10.10 Modulo de Configuracion", level=2)
    add_callout(doc, "Acceso restringido al Administrador del Sistema.", kind="danger")
    add_field(doc, "Ruta de acceso", "Menu lateral -> Administracion -> Configuracion")
    add_table(
        doc,
        ["Catalogo", "Descripcion"],
        [
            ("Tipos de Servicio", "REGULAR, ESPECIAL, TURISTICO, TRABAJADORES, etc."),
            ("Categorias de Vehiculo", "M1, M2, M3 (con capacidad y peso maximo)."),
            ("Carrocerias", "Tipos de carroceria vinculadas a una categoria."),
            ("Rutas", "Origen, destino, puntos intermedios, distancia, tiempo, ambito."),
            ("Frecuencias", "Horarios, dias de operacion."),
        ],
        col_widths=[5, 10.5],
        first_col_bold=True,
    )
    add_paragraph(doc, "Cada catalogo permite crear, editar, activar/desactivar y eliminar registros.")

    # 10.11 Usuarios
    add_heading(doc, "10.11 Modulo de Gestion de Usuarios", level=2)
    add_callout(doc, "Acceso restringido al Administrador del Sistema.", kind="danger")
    add_field(doc, "Ruta de acceso", "Menu lateral -> Administracion -> Usuarios")
    add_heading(doc, "Funcionalidades", level=3)
    for s in [
        "Listado de usuarios con busqueda y filtro por rol y estado.",
        "Crear un nuevo usuario.",
        "Editar datos del usuario.",
        "Activar / desactivar cuentas.",
        "Resetear contrasena.",
    ]:
        add_bullet(doc, s)
    add_heading(doc, "Campos del usuario", level=3)
    add_table(
        doc,
        ["Campo", "Descripcion"],
        [
            ("Usuario (username)", "Unico, sin espacios."),
            ("DNI", "8 digitos, unico."),
            ("Nombres", "Nombres del usuario."),
            ("Apellidos", "Apellidos."),
            ("Correo electronico", "Email institucional."),
            ("Telefono", "Contacto."),
            ("Area / Oficina", "Area de trabajo."),
            ("Cargo", "Cargo o puesto."),
            ("Rol", "Rol del sistema (ver seccion 9)."),
            ("Estado", "Activo / Inactivo."),
            ("Contrasena", "Minimo 8 caracteres."),
        ],
        col_widths=[5, 10.5],
        first_col_bold=True,
    )

    # 10.12 Documentacion
    add_heading(doc, "10.12 Modulo de Documentacion / Manuales", level=2)
    add_field(doc, "Ruta de acceso", "Menu lateral -> Ayuda -> Manuales de Usuario")
    add_paragraph(doc, "Contiene manuales especificos en linea:")
    for s in [
        "Manual de Usuarios.",
        "Manual de Configuracion.",
        "Manual de Reportes.",
        "Manual Operativo.",
    ]:
        add_bullet(doc, s)


def section_procedimientos(doc):
    add_heading(doc, "11. Procedimientos paso a paso", level=1)

    procedimientos = [
        ("11.1 Registrar una Empresa", [
            "Ingresar al sistema con un usuario con permiso (Administrador o Mesa de Partes).",
            "Ir al menu Gestion -> Empresas.",
            "Pulsar '+ Nueva Empresa'.",
            "Completar todos los campos obligatorios (RUC, Razon Social, Domicilio, Provincia, Distrito, Representante Legal, DNI).",
            "Pulsar 'Guardar'.",
            "El sistema mostrara un mensaje verde de confirmacion.",
            "La empresa aparecera en la lista con estado Activa.",
        ]),
        ("11.2 Crear una Autorizacion", [
            "Verificar que la empresa ya este registrada y activa.",
            "Ir a Gestion -> Autorizaciones -> '+ Nueva Autorizacion'.",
            "Seleccionar la empresa.",
            "Ingresar Numero y Fecha de Resolucion.",
            "Definir Fecha de Inicio y Fecha de Fin de Vigencia.",
            "Seleccionar Tipo de Servicio, Modalidad, Rutas y Frecuencias.",
            "(Opcional) Adjuntar archivo PDF de la resolucion.",
            "Pulsar 'Guardar'.",
        ]),
        ("11.3 Registrar un Vehiculo", [
            "Ir a Gestion -> Vehiculos -> '+ Nuevo Vehiculo'.",
            "Seleccionar la empresa propietaria.",
            "Completar placa, marca, modelo, ano, capacidad y peso.",
            "Seleccionar Categoria y Carroceria.",
            "Indicar fechas de SOAT y CITV.",
            "Seleccionar la Autorizacion Principal (lista filtrada por la empresa).",
            "Pulsar 'Guardar'.",
        ]),
        ("11.4 Registrar un Conductor", [
            "Ir a Gestion -> Conductores -> '+ Nuevo Conductor'.",
            "Seleccionar la empresa.",
            "Ingresar DNI, nombres y apellidos, fecha de nacimiento.",
            "Completar datos de licencia (numero, categoria, fechas).",
            "Pulsar 'Guardar'.",
            "Si el conductor ya esta habilitado en otra empresa, el sistema mostrara una advertencia y no permitira registrarlo nuevamente.",
        ]),
        ("11.5 Iniciar un Tramite (Mesa de Partes)", [
            "Ir a Tramites -> Nuevo Tramite.",
            "Seleccionar el Tipo de Tramite (ej. Autorizacion Inicial).",
            "Seleccionar la empresa (y, si corresponde, autorizacion, vehiculo o conductor).",
            "Completar los datos del solicitante (DNI, nombres, telefono, email).",
            "Escribir la descripcion de la solicitud.",
            "Pulsar 'Guardar'.",
            "El sistema asigna el numero de expediente automatico (EXP-YYYY-NNNNN).",
            "En la pantalla de detalle, adjuntar los documentos PDF requeridos.",
            "Registrar los recibos de pago.",
            "Pulsar 'Enviar a Evaluacion Tecnica' (o la accion que corresponda).",
        ]),
        ("11.6 Evaluar un tramite (Especialista Tecnico)", [
            "Ir a Tramites -> Pendientes y abrir el expediente.",
            "Revisar documentos, vehiculos y conductores asociados.",
            "Si todo esta correcto, pulsar 'Aprobar Evaluacion'.",
            "Si hay observaciones, pulsar 'Observar', indicar el motivo y el Plazo de Subsanacion.",
            "El sistema notifica automaticamente al solicitante y a Mesa de Partes.",
        ]),
        ("11.7 Revision Legal (Asesoria Legal)", [
            "Abrir el expediente desde Tramites.",
            "Verificar la documentacion.",
            "Si procede, pulsar 'Aprobar Legal' -> pasa a Pendiente de Firma.",
            "Si hay observaciones, pulsar 'Observar (Legal)'.",
        ]),
        ("11.8 Firma del Director", [
            "Abrir el expediente en estado Pendiente de Firma.",
            "Revisar el proyecto de resolucion.",
            "Adjuntar la resolucion firmada (PDF).",
            "Pulsar 'Aprobar / Firmar'.",
            "El tramite pasa a APROBADO. El sistema genera automaticamente la habilitacion vehicular o de conductor segun corresponda.",
        ]),
        ("11.9 Buscar un registro", [
            "Ingresar al modulo (Empresas, Vehiculos, Conductores, Tramites).",
            "Usar la caja de busqueda superior (numero de expediente, placa, RUC, DNI, nombre, etc.).",
            "Aplicar filtros de estado, fechas o empresa.",
            "Pulsar el icono de busqueda.",
            "Hacer clic en la fila para abrir el detalle.",
        ]),
        ("11.10 Editar un registro", [
            "Localizar el registro a editar.",
            "Pulsar el boton 'Editar' (icono de lapiz).",
            "Modificar los campos necesarios.",
            "Pulsar 'Guardar'.",
            "Se registra en el historial quien hizo el cambio y cuando.",
        ]),
        ("11.11 Eliminar o anular informacion", [
            "El sistema no permite eliminar empresas, autorizaciones, vehiculos ni conductores con datos asociados.",
            "En su lugar, cambiar el estado a Inactiva, Cancelada, Baja o Suspendida segun corresponda.",
            "Adjuntar la resolucion administrativa que respalda la decision.",
            "Para catalogos (rutas, frecuencias, carrocerias) si se puede eliminar si no estan en uso.",
        ]),
        ("11.12 Generar un Reporte PDF", [
            "Ir a Reportes.",
            "Seleccionar el reporte deseado (Empresas, Vehiculos, Vencimientos, etc.).",
            "Aplicar filtros (periodo, empresa, estado).",
            "Pulsar 'Generar PDF'.",
            "El navegador abre el PDF en una nueva pestana; se puede imprimir o descargar.",
        ]),
        ("11.13 Exportar a Excel", [
            "Ir a la lista del modulo deseado.",
            "Aplicar filtros si fuese necesario.",
            "Pulsar 'Exportar Excel'.",
            "El archivo .xlsx se descargara automaticamente.",
        ]),
        ("11.14 Consultar un tramite (publico)", [
            "Ingresar a https://[dominio]/consulta-tramite/",
            "Escribir el numero de expediente (ej. EXP-2026-00045).",
            "Pulsar 'Consultar'.",
            "El sistema muestra el estado actual y la ultima observacion (si existe).",
        ]),
    ]

    for titulo, pasos in procedimientos:
        add_heading(doc, titulo, level=2)
        for p in pasos:
            add_numbered(doc, p)


def section_errores(doc):
    add_heading(doc, "12. Mensajes de error frecuentes y solucion", level=1)
    errores = [
        ("Usuario o contrasena incorrectos.", "Datos mal ingresados o usuario inactivo.", "Verifique mayusculas/minusculas y solicite reseteo al Administrador."),
        ("El RUC debe tener exactamente 11 digitos numericos.", "RUC invalido.", "Ingrese solo numeros, sin guiones. Debe iniciar con 10, 15, 17 o 20."),
        ("El DNI debe tener exactamente 8 digitos numericos.", "DNI invalido.", "Ingrese solo numeros, sin guiones."),
        ("Formato de placa invalido.", "Placa no cumple patron.", "Use formato ABC-123 o ABC-1234."),
        ("El ano de fabricacion debe ser 1995 o mayor.", "Ano fuera de rango.", "Verifique la tarjeta de propiedad del vehiculo."),
        ("La fecha de nacimiento debe ser desde 1930 en adelante.", "Fecha invalida.", "Revise el documento de identidad del conductor."),
        ("Solo se permiten archivos PDF.", "Archivo de tipo distinto.", "Convierta el documento a PDF antes de subirlo."),
        ("El archivo no debe superar los 10 MB.", "Archivo demasiado grande.", "Comprima el PDF antes de subirlo."),
        ("El conductor ya esta habilitado en otra empresa.", "Duplicidad de habilitacion.", "Dar de baja la habilitacion anterior antes de crear la nueva."),
        ("No se puede eliminar: existe informacion asociada.", "Tiene registros vinculados.", "Cambie el estado a Inactiva/Cancelada en lugar de eliminar."),
        ("No tiene permisos para realizar esta accion.", "El rol no permite la operacion.", "Solicite la accion al rol correspondiente."),
        ("La sesion ha expirado.", "Inactividad prolongada.", "Vuelva a iniciar sesion."),
        ("Error 404 - Pagina no encontrada.", "URL inexistente.", "Verifique el enlace o regrese al Dashboard."),
        ("Error 500 - Error interno del servidor.", "Falla del servidor.", "Reportar al Administrador con la hora y la accion realizada."),
        ("La fecha fin debe ser mayor a la fecha de inicio.", "Inconsistencia de fechas.", "Revise los valores ingresados."),
        ("Numero de resolucion ya existe.", "Resolucion duplicada.", "Verifique el numero correcto o consulte el registro existente."),
    ]
    add_table(
        doc,
        ["Mensaje", "Causa", "Solucion"],
        errores,
        col_widths=[5.5, 4, 6],
    )


def section_recomendaciones(doc):
    add_heading(doc, "13. Recomendaciones para el usuario", level=1)
    for t in [
        "Cambie su contrasena la primera vez que ingrese y luego cada 3 meses.",
        "No comparta su usuario ni contrasena. El historial registra todas sus acciones.",
        "Cierre la sesion al terminar de trabajar, especialmente en computadoras compartidas.",
        "Guarde con frecuencia. Use el boton Guardar despues de cada bloque importante.",
        "Adjunte documentos en PDF legibles, escaneados a 200 dpi minimo.",
        "Verifique los datos antes de derivar un expediente: una vez derivado, solo el siguiente rol puede modificarlo.",
        "Use los filtros y la caja de busqueda para localizar registros rapidamente.",
        "Revise la campana de notificaciones al inicio de cada jornada.",
        "Genere reportes mensuales para llevar control estadistico.",
        "Reporte cualquier falla o sugerencia al Administrador del sistema o al area de TI.",
    ]:
        add_numbered(doc, t)


def section_glosario(doc):
    add_heading(doc, "14. Glosario de terminos", level=1)
    terminos = [
        ("DRTC", "Direccion Regional de Transportes y Comunicaciones."),
        ("RUC", "Registro Unico de Contribuyentes (SUNAT), 11 digitos."),
        ("DNI", "Documento Nacional de Identidad, 8 digitos."),
        ("SOAT", "Seguro Obligatorio de Accidentes de Transito."),
        ("CITV", "Certificado de Inspeccion Tecnica Vehicular."),
        ("TUC", "Tarjeta Unica de Circulacion."),
        ("TIV", "Tarjeta de Identificacion Vehicular."),
        ("Autorizacion", "Resolucion administrativa que habilita a una empresa a prestar el servicio."),
        ("Habilitacion", "Registro que vincula un vehiculo o conductor a una autorizacion vigente."),
        ("Expediente", "Documento administrativo identificado por el numero EXP-YYYY-NNNNN."),
        ("FSM", "Finite State Machine - Maquina de Estados Finitos. Gobierna el flujo del tramite."),
        ("Mesa de Partes", "Oficina de recepcion de documentos y expedientes."),
        ("RBAC", "Role Based Access Control - Control de acceso basado en roles."),
        ("Dashboard", "Panel principal con indicadores."),
        ("Workflow", "Flujo de trabajo entre areas."),
        ("Rol", "Perfil que determina permisos del usuario."),
        ("Subsanar", "Corregir las observaciones planteadas a un tramite."),
        ("Baja", "Cese definitivo de la habilitacion."),
        ("Vigente", "Estado activo dentro del periodo valido."),
        ("Vencido", "Estado fuera del periodo valido."),
        ("Suspendido", "Estado pausado por sancion o causa administrativa."),
        ("Ambito", "Departamento donde opera la autorizacion."),
    ]
    add_table(
        doc,
        ["Termino", "Significado"],
        terminos,
        col_widths=[4, 11.5],
        first_col_bold=True,
    )


def section_anexos(doc):
    add_heading(doc, "15. Anexos", level=1)

    add_heading(doc, "Anexo A. Tabla de Modulos y Rutas", level=2)
    add_table(
        doc,
        ["Modulo", "URL", "Acceso"],
        [
            ("Login", "/usuarios/login/", "Publico"),
            ("Dashboard", "/usuarios/dashboard/", "Autenticado"),
            ("Empresas", "/empresas/", "Autenticado"),
            ("Autorizaciones", "/autorizaciones/", "Autenticado"),
            ("Vehiculos", "/vehiculos/", "Autenticado"),
            ("Conductores", "/conductores/", "Autenticado"),
            ("Tramites", "/tramites/", "Roles autorizados"),
            ("Consulta por Placa", "/consulta/placa/", "Autenticado"),
            ("Consulta por Conductor", "/consulta/conductor/", "Autenticado"),
            ("Consulta publica de tramite", "/consulta-tramite/", "Publico"),
            ("Reportes", "/reportes/", "Autenticado"),
            ("Configuracion", "/configuracion/", "Administrador"),
            ("Gestion de Usuarios", "/usuarios/usuarios/", "Administrador"),
            ("Notificaciones", "/notificaciones/", "Autenticado"),
            ("Documentacion", "/documentacion/manuales/", "Autenticado"),
            ("Admin Django", "/admin/", "Administrador"),
        ],
        col_widths=[5, 6, 4.5],
        first_col_bold=True,
    )

    add_heading(doc, "Anexo B. Botones y su funcion", level=2)
    add_table(
        doc,
        ["Boton / Icono", "Funcion"],
        [
            ("Lupa", "Buscar registros."),
            ("Mas (+)", "Crear nuevo registro."),
            ("Ojo", "Ver detalle."),
            ("Lapiz", "Editar registro."),
            ("Papelera", "Eliminar (solo si no tiene registros asociados)."),
            ("Flecha hacia abajo", "Descargar documento."),
            ("Flecha hacia arriba", "Exportar (Excel / PDF)."),
            ("Campana", "Notificaciones."),
            ("Menu (tres lineas)", "Mostrar / ocultar menu lateral."),
            ("Candado", "Cerrar sesion."),
        ],
        col_widths=[4, 11.5],
        first_col_bold=True,
    )

    add_heading(doc, "Anexo C. Categorias de Licencia de Conducir", level=2)
    add_table(
        doc,
        ["Categoria", "Vehiculos permitidos"],
        [
            ("A-I", "Vehiculos particulares (autos, camionetas)."),
            ("A-II-A", "Transporte de personas en categoria M2 (minimo profesional)."),
            ("A-II-B", "Transporte de personas en categoria M2/M3 hasta cierto peso."),
            ("A-III-A", "Transporte de personas/carga categoria M3, N2, N3."),
            ("A-III-B", "Vehiculos articulados, transporte interprovincial."),
            ("A-III-C", "Transporte de materiales peligrosos."),
        ],
        col_widths=[3, 12.5],
        first_col_bold=True,
    )

    add_heading(doc, "Anexo D. Categorias Vehiculares (clasificacion general)", level=2)
    add_table(
        doc,
        ["Categoria", "Descripcion"],
        [
            ("M1", "Vehiculos de hasta 8 asientos (autos, minivans)."),
            ("M2", "Vehiculos de mas de 8 asientos y peso menor o igual a 5 t (microbuses)."),
            ("M3", "Vehiculos de mas de 8 asientos y peso mayor a 5 t (omnibus)."),
        ],
        col_widths=[3, 12.5],
        first_col_bold=True,
    )

    add_heading(doc, "Anexo E. Soporte y contacto", level=2)
    add_table(
        doc,
        ["Canal", "Dato"],
        [
            ("Mesa de ayuda interna", "Oficina de Tecnologias de la Informacion - DRTC."),
            ("Correo institucional", "soporte@drtc.gob.pe (pendiente de confirmar)."),
            ("Horario de atencion", "Lunes a Viernes, 08:00 - 16:30."),
        ],
        col_widths=[5, 10.5],
        first_col_bold=True,
    )

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_horizontal_rule(p)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("FIN DEL MANUAL DE USUARIO")
    style_run(r, bold=True, size=14, color=PRIMARY)


def main():
    out_path = Path(__file__).resolve().parent / "Manual_de_Usuario_DRTC.docx"
    doc = Document()
    configure_styles(doc)

    build_cover(doc)
    build_toc(doc)
    section_introduccion(doc)
    section_objetivo(doc)
    section_alcance(doc)
    section_publico(doc)
    section_requisitos(doc)
    section_acceso(doc)
    section_login(doc)
    section_interfaz(doc)
    section_roles(doc)
    section_modulos(doc)
    section_procedimientos(doc)
    section_errores(doc)
    section_recomendaciones(doc)
    section_glosario(doc)
    section_anexos(doc)

    doc.save(out_path)
    print(f"OK: {out_path}")


if __name__ == "__main__":
    main()
