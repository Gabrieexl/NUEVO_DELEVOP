"""
Filtros personalizados para plantillas de trámites.
"""

from django import template
from django.utils.html import mark_safe
import re

register = template.Library()


def _traducir_rol(codigo_rol):
    """
    Traduce códigos de rol a etiquetas legibles en español.
    """
    mapeo_roles = {
        'ADMIN_SISTEMA': 'Administrador del Sistema',
        'MESA_PARTES': 'Mesa de Partes',
        'ESPECIALISTA_TECNICO': 'Especialista Técnico',
        'ASESORIA_LEGAL': 'Asesoría Legal',
        'DIRECTOR': 'Director',
        'CONSULTA_INTERNA': 'Consulta Interna',
        'CONSULTA_SUTRAN': 'Consulta SUTRAN',
    }
    return mapeo_roles.get(codigo_rol.strip(), codigo_rol.strip())


@register.filter(name='format_comentario_rol')
def format_comentario_rol(value):
    """
    Extrae el rol responsable del comentario y lo muestra en negrita (sin corchetes).
    Traduce códigos de rol a etiquetas legibles.
    
    Formato esperado:
    "Texto del comentario...\n\n[PRÓXIMO ROL RESPONSABLE: MESA_PARTES]"
    
    Resultado:
    "Texto del comentario...<br><br><strong>PRÓXIMO ROL RESPONSABLE: Mesa de Partes</strong>"
    """
    if not value:
        return ""
    
    value = str(value)
    
    # Buscar el patrón [PRÓXIMO ROL RESPONSABLE: ...]
    patron = r'\[PRÓXIMO ROL RESPONSABLE:([^\]]+)\]'
    
    # Buscar el match
    match = re.search(patron, value)
    
    if match:
        # Obtener las partes
        inicio = 0
        fin = match.start()
        
        # Texto antes del rol
        texto_antes = value[inicio:fin].strip()
        
        # El rol (sin corchetes, solo el contenido)
        rol_content = match.group(1).strip()
        rol_traducido = _traducir_rol(rol_content)
        rol_texto = f"PRÓXIMO ROL RESPONSABLE: {rol_traducido}"
        
        # Convertir saltos de línea en <br>
        if texto_antes:
            texto_antes = texto_antes.replace('\n', '<br>')
            resultado = f"{texto_antes}<br><br><strong>{rol_texto}</strong>"
        else:
            resultado = f"<strong>{rol_texto}</strong>"
        
        return mark_safe(resultado)
    else:
        # Si no hay rol, solo convertir saltos de línea a <br>
        return mark_safe(value.replace('\n', '<br>'))
