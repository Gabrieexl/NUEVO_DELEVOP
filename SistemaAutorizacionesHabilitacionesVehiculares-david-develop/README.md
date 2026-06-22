# Sistema de Gestión de Autorizaciones y Habilitaciones de Transporte Terrestre
### Dirección Regional de Transportes y Comunicaciones (DRTC)

## 📋 Descripción General
El **Sistema de Autorizaciones y Habilitaciones Vehiculares** es una plataforma web integral desarrollada para modernizar, digitalizar y agilizar la gestión administrativa de la Dirección de Transporte Terrestre. 

El sistema centraliza el padrón de empresas, vehículos y conductores, gestionando el ciclo de vida completo de los expedientes administrativos, desde su ingreso por Mesa de Partes hasta la emisión de Resoluciones y Tarjetas Únicas de Circulación (TUC).

---

## 🚀 Módulos Principales

### 1. 🏢 Módulo de Empresas de Transporte
Gestión del padrón oficial de empresas autorizadas para el servicio de transporte.
*   **Registro detallado:** RUC, Razón Social, Representante Legal, Domicilio Fiscal.
*   **Estado de la empresa:** Control de empresas Activas/Inactivas.
*   **Historial:** Visualización rápida de toda la flota y conductores asociados a una empresa.

### 2. 🚌 Módulo de Parque Automotor (Vehículos)
Control exhaustivo de la flota vehicular autorizada en la región.
*   **Ficha Técnica:** Marca, Modelo, Año, Motor, Serie, Chasis, Peso Bruto.
*   **Clasificación:** Categorización automática (M1, M2, M3) y Tipos de Carrocería (Bus, Minivan, Auto, etc.).
*   **Documentación:** Control de vencimientos de SOAT y CITV.
*   **Habilitación Vehicular:**
    *   Generación y control de **TUC (Tarjeta Única de Circulación)**.
    *   Historial de habilitaciones (Altas y Bajas).
    *   Asociación inteligente con Autorizaciones vigentes.

### 3. 👨‍✈️ Módulo de Conductores
Registro y fiscalización de los conductores habilitados.
*   **Datos Personales:** Validación de DNI y datos de contacto.
*   **Licencias de Conducir:** Control de categorías y fechas de vencimiento.
*   **Alertas:** Notificación automática de licencias próximas a vencer o vencidas.
*   **Habilitación:** Asignación de conductores a empresas específicas con control de duplicidad (un conductor no puede estar activo en dos empresas simultáneamente).

### 4. 📜 Módulo de Autorizaciones (Resoluciones)
El corazón legal del sistema.
*   **Registro de Resoluciones:** Número, fechas de vigencia (Inicio/Fin).
*   **Rutas y Frecuencias:** Definición del ámbito de operación (Regional/Provincial) y trayectos autorizados.
*   **Tipos de Servicio:** Regular, Turístico, Personal, etc.
*   **Control de Vigencia:** Detección automática de autorizaciones vigentes, vencidas o suspendidas.

### 5. 📂 Módulo de Trámites (Expedientes)
Digitalización del flujo administrativo mediante una máquina de estados.
*   **Tipos de Trámite Soportados:**
    *   Autorización Inicial.
    *   Incremento de Flota.
    *   Sustitución de Vehículo.
    *   Habilitación de Conductor.
    *   Renovaciones y Bajas.
*   **Flujo de Trabajo (Workflow):**
    1.  **Mesa de Partes:** Recepción y digitalización de requisitos.
    2.  **Evaluación Técnica:** Revisión de cumplimiento de normas técnicas.
    3.  **Asesoría Legal:** Emisión de dictamen y proyecto de resolución.
    4.  **Dirección:** Firma y aprobación final.
*   **Trazabilidad:** Historial inmutable de quién aprobó, observó o derivó cada expediente y cuándo.

### 6. 🔍 Módulo de Consultas y Fiscalización
Herramientas para inspectores y transparencia al ciudadano.
*   **Consulta por Placa:** Revela instantáneamente si un vehículo tiene TUC vigente, SOAT, CITV y a qué empresa pertenece.
*   **Consulta por Conductor:** Verifica si un conductor está habilitado y si su licencia es válida.
*   **Consulta de Expedientes:** Seguimiento público del estado del trámite mediante número de expediente.

### 7. 📊 Reportes y Exportación
*   Generación de reportes en **Excel** para análisis estadístico.
*   Generación de documentos PDF (Resoluciones, TUCs).

---

## 🛡️ Seguridad y Roles de Usuario
El sistema implementa un estricto control de acceso basado en roles (RBAC):

1.  **ADMINISTRADOR:** Configuración total del sistema.
2.  **DIRECTOR:** Aprobación final y firma de resoluciones.
3.  **MESA DE PARTES:** Ventanilla única, ingreso de expedientes.
4.  **ESPECIALISTA TÉCNICO:** Evaluación de flota y conductores.
5.  **ASESOR LEGAL:** Revisión jurídica y proyectos de resolución.
6.  **INSPECTOR:** Acceso exclusivo a módulos de consulta para operativos en campo.

---

## 💻 Características Técnicas Destacadas
*   **Tecnología:** Desarrollado en **Python (Django)**, un framework de alto nivel conocido por su seguridad y escalabilidad.
*   **Base de Datos:** **PostgreSQL**, garantizando integridad y robustez en los datos.
*   **Interfaz:** Diseño responsivo (adaptable a móviles y tablets) usando **Bootstrap 5**.
*   **Validaciones Inteligentes:**
    *   Selectores en cascada (Empresa -> Autorización) para evitar errores de digitación.
    *   Bloqueo de vehículos/conductores duplicados.
    *   Cálculo automático de fechas de vigencia.

---

## 🌟 Beneficios para la Institución
1.  **Cero Papel:** Digitalización progresiva de los expedientes.
2.  **Transparencia:** El ciudadano puede ver el estado real de su trámite.
3.  **Fiscalización Efectiva:** Los inspectores tienen la información en tiempo real, evitando fraudes con TUCs falsos.
4.  **Orden Administrativo:** Estandarización de los procesos y reducción de la carga laboral manual.
5.  **Seguridad Jurídica:** Historial completo de todas las acciones realizadas sobre una autorización.
