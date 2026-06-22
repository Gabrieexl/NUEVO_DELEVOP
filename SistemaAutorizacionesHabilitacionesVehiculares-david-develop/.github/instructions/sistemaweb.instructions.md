---
applyTo: '**'
---
Quiero que construyas un sistema web usando Django + PostgreSQL para gestionar autorizaciones y habilitaciones de transporte en una entidad pública regional del Perú (Dirección Regional de Transportes y Comunicaciones).
1. Stack tecnológico y lineamientos generales
•	Backend: Django (última versión LTS estable).
•	Lenguaje: Python 3.x.
•	Base de datos: PostgreSQL.
•	Frontend: plantillas Django (HTML + Bootstrap o Tailwind básico, nada complejo).
•	Idioma de la interfaz: español.
•	Arquitectura:
o	Una sola app principal (ej. transporte) o varias si lo ves conveniente.
o	Separar lógica en: models.py, views.py, forms.py, urls.py, templates/.
•	Manejo de archivos:
o	Usar FileField/ImageField con almacenamiento local (MEDIA_ROOT).
o	Solo aceptar PDF para documentos oficiales.
________________________________________
2. Contexto y objetivo del sistema
El sistema debe permitir a la Dirección de Transporte Terrestre:
•	Registrar y administrar:
o	Empresas de transporte.
o	Autorizaciones de servicio (servicio de transporte público regular de personas en ámbito regional).
o	Vehículos y su habilitación vehicular.
o	Conductores y su habilitación como conductores de la empresa.
•	Gestionar trámites internos asociados a estos temas:
o	Autorización inicial de empresas.
o	Modificación de autorizaciones (rutas, frecuencias, etc.).
o	Incremento de flota.
o	Sustitución/baja de vehículos.
o	Habilitación de conductores.
o	Baja/suspensión de conductores.
•	Generar y adjuntar documentos:
o	Solicitudes, informes técnicos, proyectos de resolución, resoluciones, TUC, constancias, etc.
•	Llevar trazabilidad:
o	Estados de cada trámite.
o	Historial de cambios.
o	Quién hizo qué y cuándo.
•	Exponer un módulo de consulta externa (web/API) para inspección/fiscalización:
o	Consulta por placa de vehículo.
o	Retornar situación de la empresa, autorización, vehículo y conductores habilitados.
________________________________________
3. Roles de usuario y permisos
Implementar un sistema de usuarios con roles (puede ser Group + Permission de Django):
Roles principales:
1.	ADMIN_SISTEMA
o	Todo acceso. Configuración, usuarios, roles, etc.
2.	MESA_PARTES
o	Registrar nuevos trámites.
o	Subir documentos de entrada (solicitudes, anexos).
o	Ver el estado de los trámites.
3.	ESPECIALISTA_TECNICO
o	Ver trámites asignados y en estado de evaluación técnica.
o	Registrar resultados de evaluación técnica.
o	Generar observaciones.
o	Cargar informes técnicos.
4.	ASESORIA_LEGAL
o	Ver trámites en revisión legal.
o	Registrar comentarios legales.
o	Cargar proyectos de resolución.
o	Enviar a firma.
5.	DIRECTOR
o	Ver trámites pendientes de firma.
o	Registrar resultado (aprobado/denegado).
o	Adjuntar resolución firmada.
o	Activar efectos en base de datos (crear/actualizar autorizaciones, flota, habilitaciones).
6.	CONSULTA_INTERNA
o	Solo lectura en casi todo (autorizaciones, empresas, vehículos, conductores, trámites).
7.	CONSULTA_SUTRAN
o	Solo acceso al módulo de consulta externa (por placa).
o	No puede modificar nada.
________________________________________
4. Modelo de datos (mínimo necesario)
Define los siguientes modelos principales en models.py.
No es obligatorio que los nombres de campos sean exactamente estos, pero sí que cubras esta información.
4.1. EmpresaTransporte
•	id
•	ruc (CharField, 11)
•	razon_social (CharField)
•	nombre_comercial (CharField, opcional)
•	domicilio_fiscal (CharField)
•	representante_legal (CharField)
•	dni_representante (CharField)
•	telefono, email (opcionales)
•	estado (choices: ACTIVA / INACTIVA)
•	fecha_creacion, fecha_actualizacion
•	creado_por (FK User)
4.2. Autorizacion
•	id
•	empresa (FK a EmpresaTransporte)
•	numero_resolucion (CharField)
•	fecha_resolucion (DateField)
•	fecha_inicio_vigencia (DateField)
•	fecha_fin_vigencia (DateField)
•	ambito (CharField, ej. “regional Madre de Dios”)
•	tipo_servicio (CharField: REGULAR / ESPECIAL / etc.)
•	estado (VIGENTE / VENCIDA / SUSPENDIDA / CANCELADA)
•	descripcion_rutas (TextField)
•	frecuencias (TextField o modelo aparte si quieres más normalización)
•	observaciones (TextField, opcional)
•	creado_por, fecha_creacion, fecha_actualizacion
4.3. Vehiculo
•	id
•	placa (CharField, único)
•	empresa_propietaria (FK a EmpresaTransporte, opcional si hay leasing)
•	marca, modelo (CharField)
•	anio_fabricacion (IntegerField)
•	capacidad_sentados (IntegerField)
•	tipo_vehiculo (CharField: AUTO, MINIVAN, etc.)
•	estado (choices: PROPUESTO / HABILITADO / BAJA / NO_HABILITADO)
•	Datos administrativos:
o	numero_tiv
o	fecha_venc_soat
o	fecha_venc_citv
•	Relación con la autorización actual principal (FK autorizacion_principal, opcional).
•	Campo opcional vehiculo_sustituido (FK a Vehiculo) para registrar sustituciones.
•	Timestamps y usuario creador.
4.4. Conductor
•	id
•	dni (CharField, único)
•	nombres, apellido_paterno, apellido_materno
•	fecha_nacimiento
•	licencia_numero (CharField)
•	licencia_categoria (CharField, ej. AII, AIII, etc.)
•	licencia_fecha_emision, licencia_fecha_vencimiento
•	estado (ACTIVO / INACTIVO)
•	Timestamps y usuario creador.
4.5. HabilitacionVehicular
Registro histórico de habilitaciones de un vehículo para una autorización:
•	id
•	vehiculo (FK Vehiculo)
•	autorizacion (FK Autorizacion)
•	fecha_inicio
•	fecha_fin (nullable)
•	estado (VIGENTE / BAJA / SUSPENDIDA / CANCELADA)
•	motivo (TextField)
•	tramite_origen (FK a Tramite, opcional)
4.6. HabilitacionConductor
Registro histórico de habilitación de un conductor para una empresa/autorización:
•	id
•	conductor (FK Conductor)
•	empresa (FK EmpresaTransporte)
•	autorizacion (FK Autorizacion)
•	fecha_inicio
•	fecha_fin (nullable)
•	estado (VIGENTE / BAJA / SUSPENDIDA / CANCELADA)
•	motivo
•	tramite_origen (FK Tramite, opcional)
4.7. Tramite
Este modelo es el núcleo de los procesos:
•	id
•	tipo_tramite (choices):
o	AUTORIZACION_INICIAL
o	MODIFICACION_AUTORIZACION
o	INCREMENTO_FLOTA
o	SUSTITUCION_VEHICULO
o	BAJA_VEHICULO
o	HABILITACION_CONDUCTOR
o	BAJA_CONDUCTOR
•	estado (choices):
o	RECIBIDO
o	EN_EVAL_TECNICA
o	EN_REVISION_LEGAL
o	PENDIENTE_FIRMA
o	APROBADO
o	DENEGADO
o	OBSERVADO
o	CERRADO
•	empresa (FK EmpresaTransporte, nullable)
•	autorizacion (FK Autorizacion, nullable)
•	descripcion_solicitud (TextField)
•	plazo_subsanacion (DateField, opcional)
•	usuario_creador (FK User)
•	fecha_creacion, fecha_actualizacion
4.8. HistorialTramite
•	id
•	tramite (FK Tramite)
•	estado_anterior
•	estado_nuevo
•	usuario (FK User)
•	fecha
•	comentario (TextField opcional)
4.9. DocumentoAdjunto
•	id
•	tramite (FK Tramite)
•	tipo_documento (CharField: SOLICITUD, INFORME_TECNICO, PROYECTO_RESOLUCION, RESOLUCION, TIV, SOAT, CITV, etc.)
•	archivo (FileField)
•	vehiculo (FK opcional a Vehiculo)
•	conductor (FK opcional a Conductor)
•	subido_por (FK User)
•	fecha_subida
(Si lo consideras útil, puedes agregar modelos específicos para informes técnicos, pero no es obligatorio en esta primera versión.)
________________________________________
5. Procesos clave y flujo de estados (resumen para implementar lógica)
Implementa lógica de negocio (views + forms) para manejar estos trámites: NO hace falta que generes diagramas, solo la lógica.
5.1. Flujo genérico de un trámite
Todos los trámites comparten un patrón:
1.	RECIBIDO (Mesa de Partes crea el trámite y adjunta documentos de entrada).
2.	EN_EVAL_TECNICA (Especialista revisa y emite evaluación).
3.	OBSERVADO (si faltan requisitos; se registran observaciones y se espera subsanación).
4.	EN_REVISION_LEGAL (Asesoría legal revisa y crea proyecto de resolución).
5.	PENDIENTE_FIRMA (en despacho de Dirección).
6.	APROBADO o DENEGADO ( Dirección registra decisión y adjunta resolución firmada ).
7.	CERRADO (cuando ya se aplicaron los efectos en la base de datos).
Cada cambio de estado debe:
•	Validarse según el rol del usuario.
•	Registrar una entrada en HistorialTramite.
•	En algunos casos, ejecutar lógica adicional (crear/actualizar Autorizacion, HabilitacionVehicular, HabilitacionConductor).
5.2. Proceso: AUTORIZACION_INICIAL
Efectos cuando un trámite AUTORIZACION_INICIAL pasa a APROBADO:
•	Crear registro en Autorizacion con:
o	empresa, número de resolución, fechas, ámbito, rutas, etc.
•	Opcionalmente permitir registrar:
o	flota inicial (vehículos) como HabilitacionVehicular VIGENTE.
o	conductores iniciales como HabilitacionConductor VIGENTE.
5.3. Proceso: MODIFICACION_AUTORIZACION
Efectos al aprobar:
•	Actualizar campos de la Autorizacion (rutas, frecuencias, etc.).
•	Registrar en un modelo HistorialAutorizacion o similar los cambios (opcional pero recomendable).
5.4. Proceso: INCREMENTO_FLOTA
Efectos al aprobar:
•	Para cada vehículo marcado como “CUMPLE” en la evaluación:
o	Crear (o actualizar) Vehiculo.
o	Crear registro de HabilitacionVehicular (estado = VIGENTE).
5.5. Proceso: SUSTITUCION_VEHICULO / BAJA_VEHICULO
Efectos al aprobar:
•	SUSTITUCION_VEHICULO:
o	HabilitacionVehicular del vehículo saliente → estado = BAJA (con fecha_fin).
o	Crear habilitación para el vehículo nuevo (estado = VIGENTE).
o	Registrar relación vehiculo_nuevo.vehiculo_sustituido = vehiculo_saliente.
•	BAJA_VEHICULO:
o	Habilitación del vehículo → estado = BAJA con fecha_fin.
5.6. Proceso: HABILITACION_CONDUCTOR
Efectos al aprobar:
•	Crear HabilitacionConductor para cada conductor apto:
o	estado = VIGENTE.
o	Fechas de inicio/fin de vigencia.
5.7. Proceso: BAJA_CONDUCTOR
Efectos al aprobar o por proceso automático:
•	Actualizar HabilitacionConductor a estado = BAJA/SUSPENDIDO/CANCELADO, con fecha_fin.
________________________________________
6. Módulo de consulta externa (web/API)
Implementar un módulo de consulta por placa.
Requisitos mínimos:
•	Endpoint web: /consulta/placa/
o	Formulario donde el usuario (rol CONSULTA_SUTRAN o público si se decide) ingresa una placa.
o	Resultado:
	Datos básicos del vehículo.
	Empresa titular y su estado.
	Autorización vigente asociada al vehículo (si existe).
	Estado de la habilitación vehicular.
	Lista de conductores habilitados asociados a esa autorización/empresa (si corresponde).
•	Endpoint API REST (JSON, básico):
o	GET /api/consulta/placa/<placa>/
o	Respuesta JSON ejemplo:
{
  "placa": "ABC123",
  "vehiculo": {
    "marca": "Toyota",
    "modelo": "Hiace",
    "anio_fabricacion": 2018
  },
  "empresa": {
    "ruc": "12345678901",
    "razon_social": "Transporte X S.A.C.",
    "estado": "ACTIVA"
  },
  "autorizacion": {
    "numero_resolucion": "123-2025-GR",
    "estado": "VIGENTE",
    "ambito": "Regional Madre de Dios",
    "fecha_fin_vigencia": "2028-12-31"
  },
  "habilitacion_vehicular": {
    "estado": "VIGENTE",
    "fecha_inicio": "2025-01-01",
    "fecha_fin": null
  },
  "conductores_habilitados": [
    {
      "dni": "12345678",
      "nombre": "Juan Perez",
      "licencia_categoria": "AII",
      "estado_habilitacion": "VIGENTE"
    }
  ]
}
________________________________________
7. Requisitos no funcionales
•	Registrar siempre usuario y fecha en las operaciones críticas.
•	Uso de login_required y control de permisos por rol.
•	Paginación en listas de trámites, empresas, vehículos, conductores.
•	Logs de errores configurados (logging de Django).
•	Estructura limpia de templates (uso de base template, bloques, etc.).
________________________________________
8. Roadmap sugerido (para organizar el trabajo)
1.	Fase 1
o	Crear proyecto Django.
o	Configurar PostgreSQL.
o	Implementar modelos base y migraciones.
o	CRUD de Empresa, Autorizacion, Vehiculo, Conductor.
2.	Fase 2
o	Implementar modelo Tramite, HistorialTramite, DocumentoAdjunto.
o	Implementar flujo genérico de trámites con cambios de estado.
o	Integrar roles y permisos.
3.	Fase 3
o	Implementar procesos específicos:
	Autorización inicial.
	Incremento de flota.
	Habilitación de conductores.
	Sustitución/baja de vehículos.
	Baja de conductores.
4.	Fase 4
o	Módulo de consulta externa (web + API por placa).
o	Reportes y exportación a Excel (no obligatorio en la primera versión).

Further Considerations
¿Usar django-fsm para el flujo de estados o implementación manual? — esta bien usar django-fsm 

¿Separar apps por dominio (recomendado) o una sola app "transporte"? — Múltiples apps por dominio

¿Autenticación API para SUTRAN? API Key con throttling (recomendado para consulta pública).


¿Generar número de expediente automático? — use el formato: EXP-{AÑO}-{SECUENCIAL:05d} generado al crear trámite.

¿Notificaciones por email al cambiar estado de trámite? — Opcional para Fase 2, usando django-celery-beat para tareas asíncronas.

si usalo

¿Exportación a Excel de reportes? — Usar openpyxl para exportar listados de autorizaciones/vehículos habilitados (Fase 4).


si exportar a excel los reportes


¿Usar Docker para desarrollo local? — no.

¿Tests automatizados desde el inicio? — Recomiendo pytest-django con fixtures por app, mínimo tests de modelos y transiciones FSM.

si