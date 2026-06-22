# MANUAL DE USUARIO

## Sistema de Gestión de Autorizaciones y Habilitaciones de Transporte Terrestre
### Dirección Regional de Transportes y Comunicaciones (DRTC)

---

**Documento:** Manual de Usuario Final
**Versión:** 1.0
**Fecha de emisión:** 22 de junio de 2026
**Plataforma:** Aplicación web (Django + PostgreSQL)
**Ámbito:** Dirección Regional de Transportes y Comunicaciones

---

## Índice

1. [Introducción](#1-introducción)
2. [Objetivo del Manual](#2-objetivo-del-manual)
3. [Alcance del Sistema](#3-alcance-del-sistema)
4. [Público Objetivo](#4-público-objetivo)
5. [Requisitos para usar el sistema](#5-requisitos-para-usar-el-sistema)
6. [Acceso al sistema](#6-acceso-al-sistema)
7. [Inicio de sesión](#7-inicio-de-sesión)
8. [Descripción general de la interfaz](#8-descripción-general-de-la-interfaz)
9. [Roles y permisos](#9-roles-y-permisos)
10. [Módulos del sistema](#10-módulos-del-sistema)
    - 10.1 [Dashboard / Panel de Control](#101-dashboard--panel-de-control)
    - 10.2 [Módulo de Empresas](#102-módulo-de-empresas)
    - 10.3 [Módulo de Autorizaciones](#103-módulo-de-autorizaciones)
    - 10.4 [Módulo de Vehículos](#104-módulo-de-vehículos)
    - 10.5 [Módulo de Conductores](#105-módulo-de-conductores)
    - 10.6 [Módulo de Trámites (Expedientes)](#106-módulo-de-trámites-expedientes)
    - 10.7 [Módulo de Consultas](#107-módulo-de-consultas)
    - 10.8 [Módulo de Reportes](#108-módulo-de-reportes)
    - 10.9 [Módulo de Notificaciones](#109-módulo-de-notificaciones)
    - 10.10 [Módulo de Configuración](#1010-módulo-de-configuración)
    - 10.11 [Módulo de Gestión de Usuarios](#1011-módulo-de-gestión-de-usuarios)
    - 10.12 [Módulo de Documentación / Manuales](#1012-módulo-de-documentación--manuales)
11. [Procedimientos paso a paso](#11-procedimientos-paso-a-paso)
12. [Mensajes de error frecuentes y solución](#12-mensajes-de-error-frecuentes-y-solución)
13. [Recomendaciones para el usuario](#13-recomendaciones-para-el-usuario)
14. [Glosario de términos](#14-glosario-de-términos)
15. [Anexos](#15-anexos)

---

## 1. Introducción

El **Sistema de Gestión de Autorizaciones y Habilitaciones de Transporte Terrestre** es una plataforma web institucional diseñada para la **Dirección Regional de Transportes y Comunicaciones (DRTC)**. Su finalidad es **modernizar, digitalizar y agilizar** la gestión administrativa de los expedientes vinculados al servicio de transporte terrestre de personas y carga ligera en el ámbito regional.

El sistema centraliza el padrón oficial de **empresas de transporte, parque automotor y conductores**, y administra el ciclo de vida completo de los expedientes administrativos desde su recepción en **Mesa de Partes** hasta la emisión de **Resoluciones Directorales** y **Tarjetas Únicas de Circulación (TUC)**.

La aplicación funciona en navegador web, es responsiva (apta para computadora, tableta y celular) y ofrece módulos diferenciados según el rol del usuario.

---

## 2. Objetivo del Manual

El presente Manual tiene por objetivo proporcionar al **usuario final** una guía clara, ordenada y detallada para el correcto uso de las funcionalidades del sistema, de modo que pueda:

- Comprender la estructura general de la plataforma.
- Acceder con su usuario y contraseña institucional.
- Operar los módulos correspondientes a su rol.
- Registrar, consultar, modificar y dar seguimiento a expedientes administrativos.
- Generar reportes y documentos oficiales.
- Identificar y resolver los mensajes de error más frecuentes.

---

## 3. Alcance del Sistema

El sistema cubre las siguientes operaciones:

| Categoría | Funcionalidades |
|---|---|
| Padrón Institucional | Registro y mantenimiento de empresas, vehículos y conductores |
| Autorizaciones | Emisión, vigencia y control de resoluciones de autorización |
| Habilitaciones | Generación y control de TUC y habilitaciones de conductores |
| Trámites | Flujo administrativo completo con máquina de estados (workflow) |
| Documentos | Carga, descarga y verificación de archivos PDF |
| Consultas | Consulta pública por expediente y consulta interna por placa/DNI |
| Reportes | Listados PDF, exportación a Excel y dashboards estadísticos |
| Seguridad | Autenticación, control de acceso por rol, auditoría y notificaciones |

**No está incluido en el alcance del sistema:** la cobranza directa en línea (los pagos se registran como recibos posteriores a la cancelación en banca), la integración con SUNAT en línea ni la fiscalización en vía pública con dispositivos móviles externos.

---

## 4. Público Objetivo

Este manual está dirigido a:

- **Personal administrativo de la DRTC**, sin necesidad de conocimientos técnicos avanzados de informática.
- **Funcionarios de Mesa de Partes, Evaluación Técnica, Asesoría Legal, Dirección Administrativa y Dirección General.**
- **Inspectores y consultores externos** autorizados a verificar habilitaciones.
- **Administradores del sistema**, encargados de la configuración y mantenimiento.

---

## 5. Requisitos para usar el sistema

| Recurso | Requisito mínimo recomendado |
|---|---|
| Equipo | Computadora, laptop, tableta o smartphone |
| Sistema operativo | Windows 10, macOS, Linux, Android o iOS |
| Navegador web | Google Chrome, Microsoft Edge, Mozilla Firefox o Safari (última versión estable) |
| Conexión a internet | Banda ancha estable (mínimo 5 Mbps) |
| Resolución de pantalla | 1280 × 720 píxeles o superior |
| Cuenta de usuario | Usuario y contraseña proporcionados por el Administrador del sistema |
| Software adicional | Lector de PDF (Adobe Acrobat Reader o equivalente) |

> ⚠️ **Importante:** No se requiere instalación de software adicional. El sistema funciona íntegramente en el navegador.

---

## 6. Acceso al sistema

1. Abrir el navegador web.
2. Ingresar la dirección URL del sistema, proporcionada por la oficina de Tecnologías de la Información de la DRTC. Por ejemplo:
   - `https://autorizaciones.drtc.gob.pe/`
3. El sistema mostrará automáticamente la pantalla de **Inicio de Sesión**.

> 💡 Se recomienda guardar la dirección como favorita en el navegador para acceder más rápido en sesiones posteriores.

---

## 7. Inicio de sesión

### Pantalla de Login

La pantalla de inicio de sesión contiene los siguientes elementos:

| Elemento | Descripción |
|---|---|
| Logo DRTC | Identificación visual del sistema |
| Campo **Usuario** | Nombre de usuario asignado por el Administrador |
| Campo **Contraseña** | Contraseña personal (mínimo 8 caracteres) |
| Botón **Iniciar Sesión** | Inicia la autenticación |
| Mensaje de error | Aparece si los datos son incorrectos |

### Procedimiento

1. Ingrese su **usuario** en el primer campo.
2. Ingrese su **contraseña** en el segundo campo.
3. Pulse el botón **“Iniciar Sesión”**.
4. Si los datos son correctos, el sistema lo redirige al **Dashboard**.
5. Si los datos son incorrectos, aparece el mensaje *“Usuario o contraseña incorrectos.”*

### Cierre de sesión

1. Desplegar el menú superior derecho (donde aparece el nombre del usuario).
2. Hacer clic en **“Cerrar Sesión”**.
3. El sistema mostrará el mensaje: *“Ha cerrado sesión exitosamente.”*

### Cambio de contraseña

1. Hacer clic en el nombre del usuario en la esquina superior derecha.
2. Seleccionar **“Cambiar Contraseña”**.
3. Ingresar la contraseña actual.
4. Ingresar la nueva contraseña (dos veces).
5. Pulsar **“Guardar”**.

> 🔐 La contraseña debe cumplir con los lineamientos de seguridad: mínimo 8 caracteres, evitar datos personales y no compartirla.

---

## 8. Descripción general de la interfaz

Tras iniciar sesión, la pantalla principal presenta tres zonas:

### 8.1 Barra lateral izquierda (menú principal)

Contiene los accesos a los módulos disponibles según el rol del usuario. Está organizada en secciones:

- **Menú Principal:** Dashboard.
- **Gestión:** Empresas, Autorizaciones, Vehículos, Conductores.
- **Trámites:** Todos los Trámites, Nuevo Trámite.
- **Consultas:** Consulta por Placa, Consulta de Conductor.
- **Reportes:** Reportes, Estadísticas.
- **Administración:** Configuración, Usuarios, Admin Django (solo Administrador).
- **Ayuda:** Manuales de Usuario.

### 8.2 Barra superior (cabecera)

| Elemento | Función |
|---|---|
| Logotipo / nombre del sistema | Identificación |
| Campana 🔔 | Acceso a notificaciones no leídas |
| Etiqueta de Rol | Muestra el rol del usuario activo |
| Menú de usuario | Mi Perfil, Cambiar Contraseña, Cerrar Sesión |

### 8.3 Área central de trabajo

Es el espacio donde se cargan los listados, formularios, detalles y reportes según la opción seleccionada en el menú lateral.

> 📱 En tabletas y celulares, el menú lateral se oculta y se accede a él mediante el botón ☰ ubicado en la esquina superior izquierda.

---

## 9. Roles y permisos

El sistema implementa un modelo **RBAC (Role Based Access Control)**. Cada usuario tiene asignado un rol que define qué puede ver y hacer.

| Rol | Permisos principales |
|---|---|
| **ADMIN_SISTEMA** (Administrador del Sistema) | Acceso total. Configura usuarios, catálogos y todos los módulos. |
| **MESA_PARTES** (Mesa de Partes) | Recibe trámites nuevos, registra solicitudes, sube documentos iniciales y deriva expedientes. |
| **ESPECIALISTA_TECNICO** (Especialista Técnico) | Evalúa el cumplimiento técnico de la flota y conductores. Puede observar, aprobar y derivar. |
| **ASESORIA_LEGAL** (Asesoría Legal) | Revisa el sustento legal del expediente. Emite dictamen y puede observar o aprobar. |
| **DIRECTOR_GENERAL** (Director General) | Firma y aprueba las resoluciones finales. |
| **DIRECTOR_ADMINISTRATIVO** (Director Administrativo) | Revisa, deriva y firma según el tipo de trámite. |
| **CONTROL_CALIDAD** (Control de Calidad) | Verifica la calidad de la información antes de la firma (renovaciones TUC, bajas de vehículo). |
| **CONSULTA_INTERNA** (Consulta Interna) | Solo lectura, sin modificar datos. |
| **CONSULTA_INSPECTOR** (Inspector) | Consultas de campo por placa y por conductor. |

### Tabla resumen de capacidades

| Capacidad | ADMIN | MESA | TECNICO | LEGAL | DIRECTOR | CC | C. INTERNA | INSPECTOR |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Ver Dashboard | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Crear/editar empresas | ✅ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ |
| Crear/editar autorizaciones | ✅ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ |
| Crear/editar vehículos | ✅ | ✅ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ |
| Crear/editar conductores | ✅ | ✅ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ |
| Crear trámites | ✅ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ |
| Evaluar técnicamente | ✅ | ⛔ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ |
| Evaluar legalmente | ✅ | ⛔ | ⛔ | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |
| Firmar / aprobar | ✅ | ⛔ | ⛔ | ⛔ | ✅ | ⛔ | ⛔ | ⛔ |
| Consultas | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Reportes | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⛔ |
| Configuración del sistema | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ |
| Gestión de usuarios | ✅ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ |

> ℹ️ La aplicación oculta automáticamente las opciones del menú a las que el rol no tiene acceso.

---

## 10. Módulos del sistema

### 10.1 Dashboard / Panel de Control

Es la **pantalla principal** del usuario tras iniciar sesión. Muestra **indicadores clave** y **accesos rápidos** según el rol.

#### Indicadores generales (todos los roles)

| Indicador | Descripción |
|---|---|
| Trámites pendientes | Expedientes que aún no han sido aprobados, denegados ni cerrados. |
| Trámites del día | Expedientes registrados hoy. |
| Empresas activas | Empresas en estado “Activa” en el padrón. |
| Vehículos habilitados | Vehículos con habilitación vigente. |

#### Bloques específicos por rol

- **Administrador / Director:** Trámites recientes, totales de usuarios activos.
- **Mesa de Partes:** Trámites por recibir.
- **Especialista Técnico:** Trámites en evaluación técnica.
- **Asesoría Legal:** Trámites en revisión legal.
- **Director:** Trámites pendientes de firma.
- **Inspector / Consulta interna:** Accesos directos a consultas y reportes.

---

### 10.2 Módulo de Empresas

Administra el **padrón oficial** de empresas autorizadas para prestar el servicio de transporte.

#### Ruta de acceso
Menú lateral → **Gestión → Empresas**

#### Listado de empresas

Muestra una tabla con:
- RUC
- Razón Social
- Representante Legal
- Provincia / Distrito
- Estado (Activa / Inactiva)
- Acciones (Ver, Editar)

Sobre la lista hay:
- Buscador (por RUC, razón social o representante).
- Filtros por estado.
- Botón **“+ Nueva Empresa”** (solo roles autorizados).
- Botón **“Exportar Excel”**.

#### Campos del formulario de Empresa

| Campo | Descripción | Validación |
|---|---|---|
| RUC | Registro Único de Contribuyentes | 11 dígitos, debe comenzar con 10, 15, 17 o 20 |
| Razón Social | Nombre oficial registrado en SUNAT | Obligatorio, hasta 255 caracteres |
| Nombre Comercial | Nombre con el que opera | Opcional |
| Domicilio Fiscal | Dirección registrada | Obligatorio |
| Departamento | Por defecto: Madre de Dios | Obligatorio |
| Provincia | Provincia del domicilio fiscal | Obligatorio |
| Distrito | Distrito del domicilio fiscal | Obligatorio |
| Representante Legal | Nombre completo | Obligatorio |
| DNI del Representante | 8 dígitos numéricos | Obligatorio |
| Teléfono | Fijo o celular | Opcional |
| Correo Electrónico | Email institucional | Opcional, formato válido |
| Estado | Activa / Inactiva | Por defecto Activa |
| Observaciones | Notas adicionales | Opcional |

> ⚠️ **Importante:** Si una empresa pasa a estado **Inactiva**, todas sus autorizaciones quedan suspendidas automáticamente, y sus habilitaciones de vehículos y conductores se marcan como “No habilitado” hasta su reactivación.

---

### 10.3 Módulo de Autorizaciones

Permite registrar las **resoluciones administrativas** que autorizan a una empresa a prestar el servicio.

#### Ruta de acceso
Menú lateral → **Gestión → Autorizaciones**

#### Funcionalidades

- Listado con filtro por empresa, estado y rango de fechas.
- Detalle con historial de modificaciones.
- Asociación a **rutas** y **frecuencias** configuradas en el catálogo.
- Carga del archivo PDF de la resolución.

#### Campos del formulario

| Campo | Descripción | Validación |
|---|---|---|
| Empresa | Empresa beneficiaria | Obligatorio (debe estar activa) |
| Número de Resolución | Identificador único de la resolución | Obligatorio, único |
| Fecha de Resolución | Fecha de emisión | Obligatorio |
| Archivo de Resolución | PDF firmado | Opcional |
| Fecha Inicio de Vigencia | Inicio del período de autorización | Obligatorio |
| Fecha Fin de Vigencia | Vencimiento del período | Obligatorio (mayor a inicio) |
| Ámbito Regional | Departamento donde opera | Obligatorio |
| Tipo de Servicio | Servicio autorizado (catálogo) | Obligatorio |
| Modalidad | Texto descriptivo | Opcional |
| Rutas Autorizadas | Selección múltiple | Opcional |
| Frecuencias Asignadas | Selección múltiple | Opcional |
| Descripción de Rutas | Texto libre | Opcional |
| Estado | Vigente / Vencida / Suspendida / Cancelada | Por defecto Vigente |

#### Estados de la Autorización

| Estado | Significado |
|---|---|
| **VIGENTE** | Autorización activa dentro del período permitido. |
| **VENCIDA** | Fecha fin pasada o estado modificado. |
| **SUSPENDIDA** | Suspensión por sanción o empresa inactiva. |
| **CANCELADA** | Anulada definitivamente. |

---

### 10.4 Módulo de Vehículos

Administra la **ficha técnica** y el ciclo de vida del parque automotor habilitado.

#### Ruta de acceso
Menú lateral → **Gestión → Vehículos**

#### Funcionalidades

- Listado con filtro por empresa, placa, marca, estado y autorización.
- Ficha técnica detallada del vehículo.
- Pestaña de **Habilitaciones** (historial de altas/bajas/TUC).
- Carga de archivo de resolución.
- Exportación a Excel.

#### Campos del formulario

| Campo | Descripción | Validación |
|---|---|---|
| Placa | Placa del vehículo (ABC-123) | Obligatorio, formato válido |
| Empresa Propietaria | Empresa registrada | Obligatorio |
| Marca | Marca del vehículo | Obligatorio |
| Modelo | Modelo del vehículo | Obligatorio |
| Año de Fabricación | Año del vehículo | Obligatorio, **mínimo 1995** |
| Color | Color del vehículo | Opcional |
| Número de Resolución | Resolución de habilitación | Opcional |
| Fecha de Resolución | Fecha de la resolución | Opcional |
| Número de Serie / Chasis | Identificador | Opcional |
| Número de Motor | Identificador | Opcional |
| Capacidad de Pasajeros Sentados | Cantidad | Obligatorio |
| Peso Bruto (kg) | Peso vehicular | Opcional |
| Categoría | M1, M2, M3, etc. | Opcional |
| Carrocería | Tipo según categoría | Opcional |
| Estado | Propuesto / Habilitado / Baja / No Habilitado | Por defecto Propuesto |
| Número TIV | Tarjeta de Identificación Vehicular | Opcional |
| Fecha Venc. SOAT | Vencimiento del SOAT | Opcional |
| Fecha Venc. CITV | Vencimiento de la Inspección Técnica | Opcional |
| Autorización Principal | Resolución vinculada | Opcional |
| Vehículo Sustituido | Vehículo previo (para sustituciones) | Opcional |
| Observaciones | Notas | Opcional |

#### Estados del vehículo

| Estado | Significado |
|---|---|
| **PROPUESTO** | Aún no habilitado, en proceso. |
| **HABILITADO** | Habilitado con TUC vigente. |
| **BAJA** | Dado de baja definitivamente. |
| **NO_HABILITADO** | Suspendido temporalmente por causa externa. |

#### Habilitación Vehicular (TUC)

Cada vez que un vehículo es habilitado, se genera un registro con:
- Número de Habilitación.
- **Número de TUC** (Tarjeta Única de Circulación).
- Fecha de Inicio y Fin.
- Estado de habilitación: VIGENTE, BAJA, SUSPENDIDA o CANCELADA.
- Fecha de expedición de TUC y de autorización del transportista.
- Trámite de origen (vínculo trazable).

---

### 10.5 Módulo de Conductores

Gestiona el padrón de conductores autorizados y sus licencias.

#### Ruta de acceso
Menú lateral → **Gestión → Conductores**

#### Campos del formulario

| Campo | Descripción | Validación |
|---|---|---|
| Empresa | Empresa a la que pertenece | Obligatorio |
| DNI | Documento Nacional de Identidad | 8 dígitos, único |
| Nombres | Nombres completos | Obligatorio |
| Apellido Paterno | — | Obligatorio |
| Apellido Materno | — | Obligatorio |
| Fecha de Nacimiento | — | Obligatorio, **mínimo año 1930** |
| Número de Resolución | Resolución de habilitación | Opcional |
| Fecha de Resolución | — | Opcional |
| Archivo de Resolución | PDF | Opcional |
| Dirección | Dirección del conductor | Opcional |
| Teléfono | Contacto | Opcional |
| Correo Electrónico | Email | Opcional |
| Número de Licencia | Número de licencia de conducir | Obligatorio |
| Categoría de Licencia | A-I, A-II-A, A-II-B, A-III-A, A-III-B, A-III-C | Obligatorio |
| Fecha de Emisión de Licencia | — | Obligatorio |
| Fecha de Vencimiento de Licencia | — | Obligatorio |
| Estado | Activo / Inactivo | Por defecto Activo |
| Observaciones | Notas | Opcional |

> ⚠️ **Restricción importante:** un mismo conductor **no puede tener habilitaciones vigentes en dos empresas simultáneamente**. El sistema bloqueará el registro si detecta duplicidad.

#### Habilitación de Conductor

Cada habilitación incluye:
- Empresa habilitadora.
- Autorización vinculada.
- Número de Habilitación.
- Fechas de inicio y fin.
- Estado (Vigente, Baja, Suspendida, Cancelada).
- Trámite de origen.

---

### 10.6 Módulo de Trámites (Expedientes)

Es el **núcleo operativo del sistema**. Permite registrar, derivar, observar, aprobar o denegar los expedientes administrativos siguiendo un flujo de estados controlado.

#### Ruta de acceso
Menú lateral → **Trámites → Todos los Trámites / Nuevo Trámite**

#### Tipos de Trámite soportados

| Código | Tipo |
|---|---|
| AUTORIZACION_INICIAL | Autorización Inicial |
| AUTORIZACION_RUTA | Autorización de Ruta |
| MODIFICACION_AUTORIZACION | Actualización de Empresa y Autorización |
| RENOVACION_AUTORIZACION | Renovación de Autorización |
| RENOVACION_TUC | Renovación de TUC |
| BAJA_AUTORIZACION | Baja Voluntaria de Autorización |
| SUSPENSION_AUTORIZACION | Suspensión por Sanción |
| INCREMENTO_FLOTA | Incremento de Flota |
| SUSTITUCION_VEHICULO | Sustitución de Vehículo |
| BAJA_VEHICULO | Baja de Vehículo |
| HABILITACION_CONDUCTOR | Habilitación de Conductor |
| BAJA_CONDUCTOR | Baja de Conductor |

#### Estados del Trámite (Flujo FSM)

| Estado | Significado |
|---|---|
| **RECIBIDO** | Trámite ingresado en Mesa de Partes. |
| **EN_CONTROL_CALIDAD** | En verificación previa (bajas, renovaciones). |
| **EN_EVAL_TECNICA** | En evaluación del especialista técnico. |
| **EN_DIRECCION_ADMINISTRATIVA** | En revisión y derivación administrativa. |
| **EN_DIRECCION_GENERAL** | En despacho de Dirección General. |
| **OBSERVADO** | Presenta observaciones (técnicas o legales) por subsanar. |
| **EN_REVISION_LEGAL** | En Asesoría Legal. |
| **PENDIENTE_FIRMA** | Listo para firma del Director. |
| **APROBADO** | Aprobado y emitido. |
| **DENEGADO** | Denegado de forma definitiva. |
| **CERRADO** | Archivado tras conclusión. |

#### Identificación del expediente

El sistema **genera automáticamente** un número de expediente con el formato:

```
EXP-YYYY-NNNNN
Ejemplo: EXP-2026-00045
```

Adicionalmente se puede registrar un **N° de Expediente Hoja de Ruta** ingresado por el usuario.

#### Subsecciones del trámite

Dentro del detalle del trámite el usuario puede gestionar:

| Subsección | Contenido |
|---|---|
| **Documentos** | Adjuntar PDFs (solicitud, informes técnicos, resoluciones, SOAT, CITV, licencia, DNI, contrato, etc.). |
| **Recibos de Pago** | Registrar los recibos de tasa administrativa. |
| **Vehículos en Trámite** | Listar vehículos involucrados. |
| **Conductores en Trámite** | Listar conductores involucrados. |
| **Historial** | Trazabilidad inmutable de cada cambio de estado, observador y comentarios. |

#### Acciones del trámite (según el estado y rol)

| Acción | Quién la realiza | Estado origen | Estado destino |
|---|---|---|---|
| Enviar a Evaluación Técnica | Mesa de Partes | RECIBIDO | EN_EVAL_TECNICA |
| Enviar a Control de Calidad (baja vehículo / TUC) | Mesa de Partes | RECIBIDO | EN_CONTROL_CALIDAD / PENDIENTE_FIRMA |
| Observar (técnico) | Especialista Técnico | EN_EVAL_TECNICA | OBSERVADO |
| Subsanar observaciones | Mesa de Partes / responsable | OBSERVADO | EN_EVAL_TECNICA |
| Aprobar evaluación técnica | Especialista Técnico | EN_EVAL_TECNICA | EN_REVISION_LEGAL / PENDIENTE_FIRMA |
| Enviar a Dirección Administrativa | Especialista Técnico | EN_EVAL_TECNICA | EN_DIRECCION_ADMINISTRATIVA |
| Enviar a Dirección General | Director Administrativo | EN_DIRECCION_ADMINISTRATIVA | EN_DIRECCION_GENERAL |
| Observar (legal) | Asesoría Legal | EN_REVISION_LEGAL | OBSERVADO |
| Aprobar (legal) | Asesoría Legal | EN_REVISION_LEGAL | PENDIENTE_FIRMA |
| Firmar / Aprobar | Director General | PENDIENTE_FIRMA | APROBADO |
| Denegar | Director | * | DENEGADO |
| Cerrar | Mesa de Partes / Admin | APROBADO | CERRADO |

> 🔒 Las transiciones están protegidas: solo el rol autorizado puede ejecutar cada acción y siempre quedan registradas en el **Historial del Trámite**.

---

### 10.7 Módulo de Consultas

Permite verificar información rápidamente. Se divide en tres tipos:

#### 10.7.1 Consulta pública de Trámite (sin login)

- Acceso por URL: `/consulta-tramite/`
- El ciudadano ingresa el **número de expediente** (formato `EXP-YYYY-NNNNN`).
- El sistema muestra:
  - Tipo y estado del trámite.
  - Empresa y solicitante.
  - Última observación pendiente (si la hay), área y fecha.
  - Datos básicos sin información reservada.

#### 10.7.2 Consulta por Placa (interna, inspectores)

- Menú: **Consultas → Consulta por Placa**.
- El usuario ingresa la placa del vehículo.
- El sistema retorna:
  - Datos del vehículo (marca, modelo, año, color).
  - Empresa propietaria.
  - Estado de habilitación / TUC vigente.
  - Vigencia del SOAT y CITV.
  - Autorización principal vinculada.

#### 10.7.3 Consulta de Conductor (por DNI)

- Menú: **Consultas → Consulta de Conductor**.
- El usuario ingresa el DNI.
- El sistema retorna:
  - Datos personales del conductor.
  - Empresa donde está habilitado.
  - Categoría y vigencia de la licencia.
  - Estado de habilitación.

#### 10.7.4 API REST

El sistema expone endpoints para integraciones externas autenticadas por **API Key**:

| Endpoint | Función |
|---|---|
| `GET /api/consulta/placa/{placa}/` | Consulta por placa |
| `GET /api/consulta/conductor/{dni}/` | Consulta por DNI de conductor |
| `POST /api/consulta/verificar-key/` | Verifica validez de la API Key |

> 🔑 La gestión de API Keys es responsabilidad del Administrador del sistema.

---

### 10.8 Módulo de Reportes

Disponible para todos los roles, excepto Inspector (limitado por configuración).

#### Ruta de acceso
Menú lateral → **Reportes**

#### Tipos de reportes disponibles

##### Reportes en PDF

| Reporte | Contenido |
|---|---|
| Reporte de Empresas | Listado oficial de empresas registradas |
| Reporte de Autorizaciones | Resoluciones vigentes, vencidas, suspendidas |
| Reporte de Vehículos | Parque automotor por empresa o estado |
| Reporte de Conductores | Padrón de conductores habilitados |
| Reporte de Trámites | Expedientes por período y estado |
| Reporte de Resoluciones | Resoluciones emitidas |
| Reporte de Vencimientos | SOAT, CITV, licencias y autorizaciones próximas a vencer |
| Ficha completa de Empresa | Documento integral por empresa: datos, flota, conductores y autorizaciones |

##### Exportación a Excel

- Empresas
- Autorizaciones
- Vehículos
- Conductores
- Trámites

##### Estadísticas

Menú: **Reportes → Estadísticas**
Muestra gráficos:
- Trámites por estado.
- Trámites por tipo.
- Vehículos por tipo de servicio.
- Vencimientos próximos.

---

### 10.9 Módulo de Notificaciones

#### ¿Dónde verlo?

- **Campana 🔔** en la barra superior: notificaciones no leídas.
- Menú: **Notificaciones → Lista completa**.

#### Tipos de Notificación

| Tipo | Descripción |
|---|---|
| Trámite Recibido | Nuevo expediente en mi bandeja |
| Trámite en Evaluación Técnica | Pasa a evaluación |
| Trámite Observado | Hay observaciones pendientes |
| Trámite Subsanado | El solicitante respondió a las observaciones |
| Trámite en Revisión Legal | Pasa a Asesoría Legal |
| Trámite Pendiente de Firma | Espera firma del Director |
| Trámite Aprobado | Cierre favorable |
| Trámite Denegado | Cierre desfavorable |
| Vencimiento de Autorización | Alerta de vencimiento próximo |
| Vencimiento de SOAT | Alerta de SOAT |
| Vencimiento de CITV | Alerta de CITV |
| Vencimiento de Licencia | Alerta de licencia |
| Vencimiento de Habilitación | Alerta de habilitación |
| Plazo de Subsanación | Aviso por plazo próximo a vencer |
| Sistema | Notificaciones administrativas |

#### Prioridades

| Color | Prioridad |
|---|---|
| 🔴 Rojo | Urgente |
| 🟡 Amarillo | Alta |
| 🔵 Azul | Media |
| ⚪ Gris | Baja |

#### Acciones disponibles

- Marcar una notificación como leída (al hacer clic).
- Marcar todas como leídas.
- Ir a la página relacionada (al hacer clic se redirige al expediente o registro).

---

### 10.10 Módulo de Configuración

**Acceso restringido al Administrador del Sistema.**

#### Ruta de acceso
Menú lateral → **Administración → Configuración**

#### Catálogos administrables

| Catálogo | Descripción |
|---|---|
| **Tipos de Servicio** | REGULAR, ESPECIAL, TURISTICO, TRABAJADORES, etc. |
| **Categorías de Vehículo** | M1, M2, M3 (con capacidad y peso máximo). |
| **Carrocerías** | Tipos de carrocería vinculadas a una categoría. |
| **Rutas** | Origen, destino, puntos intermedios, distancia, tiempo, ámbito. |
| **Frecuencias** | Horarios, días de operación. |

Cada catálogo permite crear, editar, activar/desactivar y eliminar registros.

---

### 10.11 Módulo de Gestión de Usuarios

**Acceso restringido al Administrador del Sistema.**

#### Ruta de acceso
Menú lateral → **Administración → Usuarios**

#### Funcionalidades

- Listado de usuarios del sistema con búsqueda y filtro por rol y estado.
- Crear un nuevo usuario.
- Editar datos del usuario.
- Activar/desactivar cuentas.
- Resetear contraseña.

#### Campos del usuario

| Campo | Descripción |
|---|---|
| Usuario (username) | Único, sin espacios |
| DNI | 8 dígitos, único |
| Nombres | Nombres del usuario |
| Apellidos | Apellidos |
| Correo electrónico | Email institucional |
| Teléfono | Contacto |
| Área / Oficina | Área de trabajo |
| Cargo | Cargo o puesto |
| Rol | Rol del sistema (ver sección 9) |
| Estado | Activo / Inactivo |
| Contraseña | Mínimo 8 caracteres |

---

### 10.12 Módulo de Documentación / Manuales

#### Ruta de acceso
Menú lateral → **Ayuda → Manuales de Usuario**

Contiene manuales específicos:
- Manual de Usuarios.
- Manual de Configuración.
- Manual de Reportes.
- Manual Operativo.

Cada manual es accesible directamente desde el sistema sin necesidad de descargar archivos externos.

---

## 11. Procedimientos paso a paso

### 11.1 Registrar una Empresa

1. Ingresar al sistema con un usuario con permiso (Administrador o Mesa de Partes).
2. Ir al menú **Gestión → Empresas**.
3. Pulsar **“+ Nueva Empresa”**.
4. Completar todos los campos obligatorios (RUC, Razón Social, Domicilio, Provincia, Distrito, Representante Legal, DNI).
5. Pulsar **“Guardar”**.
6. El sistema mostrará un mensaje verde de confirmación.
7. La empresa aparecerá en la lista con estado **Activa**.

### 11.2 Crear una Autorización

1. Verificar que la **empresa ya esté registrada y activa**.
2. Ir a **Gestión → Autorizaciones → + Nueva Autorización**.
3. Seleccionar la empresa.
4. Ingresar Número y Fecha de Resolución.
5. Definir Fecha de Inicio y Fecha de Fin de Vigencia.
6. Seleccionar Tipo de Servicio, Modalidad, Rutas y Frecuencias.
7. (Opcional) Adjuntar archivo PDF de la resolución.
8. Pulsar **“Guardar”**.

### 11.3 Registrar un Vehículo

1. Ir a **Gestión → Vehículos → + Nuevo Vehículo**.
2. Seleccionar la **empresa propietaria**.
3. Completar placa, marca, modelo, año, capacidad y peso.
4. Seleccionar Categoría y Carrocería.
5. Indicar fechas de SOAT y CITV.
6. Seleccionar la **Autorización Principal** (lista filtrada por la empresa).
7. Pulsar **“Guardar”**.

### 11.4 Registrar un Conductor

1. Ir a **Gestión → Conductores → + Nuevo Conductor**.
2. Seleccionar la empresa.
3. Ingresar DNI, nombres y apellidos, fecha de nacimiento.
4. Completar datos de licencia (número, categoría, fechas).
5. Pulsar **“Guardar”**.

Si el conductor ya está habilitado en otra empresa, el sistema mostrará una advertencia y no permitirá registrarlo nuevamente.

### 11.5 Iniciar un Trámite (Mesa de Partes)

1. Ir a **Trámites → Nuevo Trámite**.
2. Seleccionar el **Tipo de Trámite** (ej. Autorización Inicial).
3. Seleccionar la empresa (y, si corresponde, autorización, vehículo o conductor).
4. Completar los datos del solicitante (DNI, nombres, teléfono, email).
5. Escribir la descripción de la solicitud.
6. Pulsar **“Guardar”**.
7. El sistema asigna el número de expediente automático (EXP-YYYY-NNNNN).
8. En la pantalla de detalle, adjuntar los documentos PDF requeridos.
9. Registrar los recibos de pago.
10. Pulsar **“Enviar a Evaluación Técnica”** (o la acción que corresponda según el tipo de trámite).

### 11.6 Evaluar un trámite (Especialista Técnico)

1. Ir a **Trámites → Pendientes** y abrir el expediente.
2. Revisar documentos, vehículos y conductores asociados.
3. Si todo está correcto, pulsar **“Aprobar Evaluación”**.
4. Si hay observaciones, pulsar **“Observar”**, indicar el motivo y el **Plazo de Subsanación**.
5. El sistema notifica automáticamente al solicitante y a Mesa de Partes.

### 11.7 Revisión Legal (Asesoría Legal)

1. Abrir el expediente desde **Trámites**.
2. Verificar la documentación.
3. Si procede, pulsar **“Aprobar Legal”** → pasa a **Pendiente de Firma**.
4. Si hay observaciones, pulsar **“Observar (Legal)”**.

### 11.8 Firma del Director

1. Abrir el expediente en estado **Pendiente de Firma**.
2. Revisar el proyecto de resolución.
3. Adjuntar la resolución firmada (PDF).
4. Pulsar **“Aprobar / Firmar”**.
5. El trámite pasa a **APROBADO**. El sistema genera automáticamente la **habilitación vehicular o de conductor** según corresponda.

### 11.9 Buscar un registro

1. Ingresar al módulo (Empresas, Vehículos, Conductores, Trámites).
2. Usar la **caja de búsqueda** superior (por número de expediente, placa, RUC, DNI, nombre, etc.).
3. Aplicar **filtros** de estado, fechas o empresa.
4. Pulsar el ícono 🔍 para buscar.
5. Hacer clic en la fila para abrir el detalle.

### 11.10 Editar un registro

1. Localizar el registro a editar.
2. Pulsar el botón **“Editar”** (ícono ✏️).
3. Modificar los campos necesarios.
4. Pulsar **“Guardar”**.
5. Se registra en el **historial** quién hizo el cambio y cuándo.

### 11.11 Eliminar o anular información

> ⚠️ El sistema **no permite eliminar** empresas, autorizaciones, vehículos ni conductores con datos asociados. En su lugar:
- Cambiar el **estado** a Inactiva, Cancelada, Baja, Suspendida según corresponda.
- Adjuntar la resolución administrativa que respalda la decisión.

Para catálogos de configuración (rutas, frecuencias, carrocerías) sí se puede eliminar si **no están en uso**.

### 11.12 Generar un Reporte PDF

1. Ir a **Reportes**.
2. Seleccionar el reporte deseado (Empresas, Vehículos, Vencimientos, etc.).
3. Aplicar filtros (período, empresa, estado).
4. Pulsar **“Generar PDF”**.
5. El navegador abre el PDF en una nueva pestaña; se puede imprimir o descargar.

### 11.13 Exportar a Excel

1. Ir a la lista del módulo deseado.
2. Aplicar filtros si fuese necesario.
3. Pulsar **“Exportar Excel”**.
4. El archivo `.xlsx` se descargará automáticamente.

### 11.14 Consultar un trámite (público)

1. Ingresar a `https://[dominio]/consulta-tramite/`.
2. Escribir el número de expediente (ej. `EXP-2026-00045`).
3. Pulsar **“Consultar”**.
4. El sistema muestra el estado actual y la última observación (si existe).

---

## 12. Mensajes de error frecuentes y solución

| Mensaje | Causa | Solución |
|---|---|---|
| “Usuario o contraseña incorrectos.” | Datos mal ingresados o usuario inactivo. | Verifique mayúsculas/minúsculas y solicite reseteo al Administrador. |
| “El RUC debe tener exactamente 11 dígitos numéricos.” | RUC inválido. | Ingrese solo números, sin guiones. Debe iniciar con 10, 15, 17 o 20. |
| “El DNI debe tener exactamente 8 dígitos numéricos.” | DNI inválido. | Ingrese solo números, sin guiones. |
| “Formato de placa inválido.” | Placa no cumple patrón. | Use formato `ABC-123` o `ABC-1234`. |
| “El año de fabricación debe ser 1995 o mayor.” | Año fuera de rango. | Verifique tarjeta de propiedad del vehículo. |
| “La fecha de nacimiento debe ser desde 1930 en adelante.” | Fecha inválida. | Revise el documento de identidad del conductor. |
| “Solo se permiten archivos PDF.” | Archivo de tipo distinto. | Convierta el documento a PDF (Word → Guardar como PDF). |
| “El archivo no debe superar los 10 MB.” | Archivo muy grande. | Comprima el PDF antes de subirlo. |
| “El conductor ya está habilitado en otra empresa.” | Duplicidad de habilitación. | Dar de baja la habilitación anterior antes de crear la nueva. |
| “No se puede eliminar: existe información asociada.” | Tiene registros vinculados. | Cambie el estado a Inactiva/Cancelada en lugar de eliminar. |
| “No tiene permisos para realizar esta acción.” | El rol no permite la operación. | Solicite la acción al rol correspondiente. |
| “La sesión ha expirado.” | Inactividad prolongada. | Vuelva a iniciar sesión. |
| “Error 404 – Página no encontrada.” | URL inexistente. | Verifique el enlace o regrese al Dashboard. |
| “Error 500 – Error interno del servidor.” | Falla del servidor. | Reportar al Administrador con la hora y la acción que realizó. |
| “La fecha fin debe ser mayor a la fecha de inicio.” | Inconsistencia de fechas. | Revise los valores ingresados. |
| “Número de resolución ya existe.” | Resolución duplicada. | Verifique el número correcto o consulte el registro existente. |

---

## 13. Recomendaciones para el usuario

1. **Cambie su contraseña** la primera vez que ingrese y luego cada 3 meses.
2. **No comparta su usuario** ni contraseña. El historial registra todas sus acciones.
3. **Cierre la sesión** al terminar de trabajar, especialmente en computadoras compartidas.
4. **Guarde con frecuencia**. Use el botón **Guardar** después de cada bloque importante.
5. **Adjunte documentos en PDF** legibles, escaneados a 200 dpi mínimo.
6. **Verifique los datos** antes de derivar un expediente: una vez derivado, solo el siguiente rol puede modificarlo.
7. **Use los filtros** y la caja de búsqueda para localizar registros rápidamente.
8. **Revise la campana de notificaciones** al inicio de cada jornada.
9. **Genere reportes mensuales** para llevar control estadístico.
10. Reporte cualquier **falla o sugerencia** al Administrador del sistema o al área de TI.

---

## 14. Glosario de términos

| Término | Significado |
|---|---|
| **DRTC** | Dirección Regional de Transportes y Comunicaciones. |
| **RUC** | Registro Único de Contribuyentes (SUNAT), 11 dígitos. |
| **DNI** | Documento Nacional de Identidad, 8 dígitos. |
| **SOAT** | Seguro Obligatorio de Accidentes de Tránsito. |
| **CITV** | Certificado de Inspección Técnica Vehicular. |
| **TUC** | Tarjeta Única de Circulación. |
| **TIV** | Tarjeta de Identificación Vehicular. |
| **Autorización** | Resolución administrativa que habilita a una empresa a prestar el servicio. |
| **Habilitación** | Registro que vincula un vehículo o conductor a una autorización vigente. |
| **Expediente** | Documento administrativo identificado por el número EXP-YYYY-NNNNN. |
| **FSM** | *Finite State Machine* – Máquina de Estados Finitos. Gobierna el flujo del trámite. |
| **Mesa de Partes** | Oficina de recepción de documentos y expedientes. |
| **RBAC** | *Role Based Access Control* – Control de acceso basado en roles. |
| **Dashboard** | Panel principal con indicadores. |
| **Workflow** | Flujo de trabajo entre áreas. |
| **Rol** | Perfil que determina permisos del usuario. |
| **Subsanar** | Corregir las observaciones planteadas a un trámite. |
| **Baja** | Cese definitivo de la habilitación. |
| **Vigente** | Estado activo dentro del período válido. |
| **Vencido** | Estado fuera del período válido. |
| **Suspendido** | Estado pausado por sanción o causa administrativa. |
| **Ámbito** | Departamento donde opera la autorización. |

---

## 15. Anexos

### Anexo A — Tabla de Módulos y Rutas

| Módulo | URL | Acceso |
|---|---|---|
| Login | `/usuarios/login/` | Público |
| Dashboard | `/usuarios/dashboard/` | Autenticado |
| Empresas | `/empresas/` | Autenticado |
| Autorizaciones | `/autorizaciones/` | Autenticado |
| Vehículos | `/vehiculos/` | Autenticado |
| Conductores | `/conductores/` | Autenticado |
| Trámites | `/tramites/` | Roles autorizados |
| Consulta por Placa | `/consulta/placa/` | Autenticado |
| Consulta por Conductor | `/consulta/conductor/` | Autenticado |
| Consulta pública | `/consulta-tramite/` | Público |
| Reportes | `/reportes/` | Autenticado |
| Configuración | `/configuracion/` | Administrador |
| Gestión de Usuarios | `/usuarios/usuarios/` | Administrador |
| Notificaciones | `/notificaciones/` | Autenticado |
| Documentación | `/documentacion/manuales/` | Autenticado |
| Admin Django | `/admin/` | Administrador |

### Anexo B — Botones y su función

| Botón / Ícono | Función |
|---|---|
| 🔍 | Buscar registros |
| ➕ | Crear nuevo registro |
| 👁 | Ver detalle |
| ✏️ | Editar registro |
| 🗑 | Eliminar (solo si no tiene registros asociados) |
| ⬇️ | Descargar documento |
| 📤 | Exportar (Excel / PDF) |
| 🔔 | Notificaciones |
| ☰ | Mostrar/ocultar menú lateral |
| 🔒 | Cerrar sesión |

### Anexo C — Tabla de Categorías de Licencia

| Categoría | Vehículos permitidos |
|---|---|
| A-I | Vehículos particulares (autos, camionetas). |
| A-II-A | Transporte de personas en categoría M2 (mínimo profesional). |
| A-II-B | Transporte de personas en categoría M2/M3 hasta cierto peso. |
| A-III-A | Transporte de personas/carga categoría M3, N2, N3. |
| A-III-B | Vehículos articulados, transporte interprovincial. |
| A-III-C | Transporte de materiales peligrosos. |

### Anexo D — Tabla de Categorías Vehiculares (clasificación general)

| Categoría | Descripción |
|---|---|
| M1 | Vehículos de hasta 8 asientos (autos, minivans). |
| M2 | Vehículos de más de 8 asientos y peso ≤ 5 t (microbuses). |
| M3 | Vehículos de más de 8 asientos y peso > 5 t (ómnibus). |

### Anexo E — Soporte y contacto

| Canal | Dato |
|---|---|
| Mesa de ayuda interna | Oficina de Tecnologías de la Información — DRTC |
| Correo institucional | soporte@drtc.gob.pe *(pendiente de confirmar)* |
| Horario de atención | Lunes a Viernes, 08:00 — 16:30 |

---

**Fin del Manual de Usuario.**
