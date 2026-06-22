"""
Constantes del sistema.
"""

# Departamentos del Perú (Regiones)
class DepartamentosPeru:
    AMAZONAS = 'AMAZONAS'
    ANCASH = 'ANCASH'
    APURIMAC = 'APURIMAC'
    AREQUIPA = 'AREQUIPA'
    AYACUCHO = 'AYACUCHO'
    CAJAMARCA = 'CAJAMARCA'
    CALLAO = 'CALLAO'
    CUSCO = 'CUSCO'
    HUANCAVELICA = 'HUANCAVELICA'
    HUANUCO = 'HUANUCO'
    ICA = 'ICA'
    JUNIN = 'JUNIN'
    LA_LIBERTAD = 'LA_LIBERTAD'
    LAMBAYEQUE = 'LAMBAYEQUE'
    LIMA = 'LIMA'
    LORETO = 'LORETO'
    MADRE_DE_DIOS = 'MADRE_DE_DIOS'
    MOQUEGUA = 'MOQUEGUA'
    PASCO = 'PASCO'
    PIURA = 'PIURA'
    PUNO = 'PUNO'
    SAN_MARTIN = 'SAN_MARTIN'
    TACNA = 'TACNA'
    TUMBES = 'TUMBES'
    UCAYALI = 'UCAYALI'
    
    CHOICES = [
        (AMAZONAS, 'Amazonas'),
        (ANCASH, 'Áncash'),
        (APURIMAC, 'Apurímac'),
        (AREQUIPA, 'Arequipa'),
        (AYACUCHO, 'Ayacucho'),
        (CAJAMARCA, 'Cajamarca'),
        (CALLAO, 'Callao'),
        (CUSCO, 'Cusco'),
        (HUANCAVELICA, 'Huancavelica'),
        (HUANUCO, 'Huánuco'),
        (ICA, 'Ica'),
        (JUNIN, 'Junín'),
        (LA_LIBERTAD, 'La Libertad'),
        (LAMBAYEQUE, 'Lambayeque'),
        (LIMA, 'Lima'),
        (LORETO, 'Loreto'),
        (MADRE_DE_DIOS, 'Madre de Dios'),
        (MOQUEGUA, 'Moquegua'),
        (PASCO, 'Pasco'),
        (PIURA, 'Piura'),
        (PUNO, 'Puno'),
        (SAN_MARTIN, 'San Martín'),
        (TACNA, 'Tacna'),
        (TUMBES, 'Tumbes'),
        (UCAYALI, 'Ucayali'),
    ]


# Roles de usuario
class Roles:
    ADMIN_SISTEMA = 'ADMIN_SISTEMA'
    MESA_PARTES = 'MESA_PARTES'
    ESPECIALISTA_TECNICO = 'ESPECIALISTA_TECNICO'
    ASESORIA_LEGAL = 'ASESORIA_LEGAL'
    DIRECTOR_GENERAL = 'DIRECTOR_GENERAL'
    DIRECTOR_ADMINISTRATIVO = 'DIRECTOR_ADMINISTRATIVO'
    CONSULTA_INTERNA = 'CONSULTA_INTERNA'
    CONSULTA_INSPECTOR = 'CONSULTA_INSPECTOR'
    CONTROL_CALIDAD = 'CONTROL_CALIDAD'
    
    CHOICES = [
        (ADMIN_SISTEMA, 'Administrador del Sistema'),
        (MESA_PARTES, 'Mesa de Partes'),
        (ESPECIALISTA_TECNICO, 'Especialista Técnico'),
        (ASESORIA_LEGAL, 'Asesoría Legal'),
        (DIRECTOR_GENERAL, 'Director General'),
        (DIRECTOR_ADMINISTRATIVO, 'Director Administrativo'),
        (CONSULTA_INTERNA, 'Consulta Interna'),
        (CONSULTA_INSPECTOR, 'Consulta Inspector'),
        (CONTROL_CALIDAD, 'Control de Calidad'),
    ]


# Estados de Empresa
class EstadoEmpresa:
    ACTIVA = 'ACTIVA'
    INACTIVA = 'INACTIVA'
    
    CHOICES = [
        (ACTIVA, 'Activa'),
        (INACTIVA, 'Inactiva'),
    ]


# Estados de Autorización
class EstadoAutorizacion:
    VIGENTE = 'VIGENTE'
    VENCIDA = 'VENCIDA'
    SUSPENDIDA = 'SUSPENDIDA'
    CANCELADA = 'CANCELADA'
    
    CHOICES = [
        (VIGENTE, 'Vigente'),
        (VENCIDA, 'Vencida'),
        (SUSPENDIDA, 'Suspendida'),
        (CANCELADA, 'Cancelada'),
    ]


# Tipos de Servicio (DEPRECADO: ahora es modelo TipoServicio en configuracion)
# Se mantiene por compatibilidad temporal durante migración
class TipoServicio:
    REGULAR = 'REGULAR'
    ESPECIAL = 'ESPECIAL'
    TURISTICO = 'TURISTICO'
    TRABAJADORES = 'TRABAJADORES'
    
    CHOICES = [
        (REGULAR, 'Regular'),
        (ESPECIAL, 'Especial'),
        (TURISTICO, 'Turístico'),
        (TRABAJADORES, 'Trabajadores'),
    ]


# Estados de Vehículo
class EstadoVehiculo:
    PROPUESTO = 'PROPUESTO'
    HABILITADO = 'HABILITADO'
    BAJA = 'BAJA'
    NO_HABILITADO = 'NO_HABILITADO'
    
    CHOICES = [
        (PROPUESTO, 'Propuesto'),
        (HABILITADO, 'Habilitado'),
        (BAJA, 'Baja'),
        (NO_HABILITADO, 'No Habilitado'),
    ]


# Tipos de Vehículo (DEPRECADO: ahora es modelo TipoVehiculo en configuracion)
# Se mantiene por compatibilidad temporal durante migración
class TipoVehiculo:
    AUTO = 'AUTO'
    MINIVAN = 'MINIVAN'
    VAN = 'VAN'
    MICROBUS = 'MICROBUS'
    OMNIBUS = 'OMNIBUS'
    MULTIPROPOSITO = 'MULTIPROPOSITO'
    
    CHOICES = [
        (AUTO, 'Auto'),
        (MINIVAN, 'Minivan'),
        (VAN, 'Van'),
        (MICROBUS, 'Microbús'),
        (OMNIBUS, 'Ómnibus'),
        (MULTIPROPOSITO, 'Multipropósito'),
    ]


# Estados de Conductor
class EstadoConductor:
    ACTIVO = 'ACTIVO'
    INACTIVO = 'INACTIVO'
    
    CHOICES = [
        (ACTIVO, 'Activo'),
        (INACTIVO, 'Inactivo'),
    ]


# Categorías de Licencia
class CategoriaLicencia:
    AI = 'AI'
    AII_A = 'AII-A'
    AII_B = 'AII-B'
    AIII_A = 'AIII-A'
    AIII_B = 'AIII-B'
    AIII_C = 'AIII-C'
    
    CHOICES = [
        (AI, 'A-I'),
        (AII_A, 'A-II-A'),
        (AII_B, 'A-II-B'),
        (AIII_A, 'A-III-A'),
        (AIII_B, 'A-III-B'),
        (AIII_C, 'A-III-C'),
    ]


# Estados de Habilitación (vehicular y conductor)
class EstadoHabilitacion:
    VIGENTE = 'VIGENTE'
    BAJA = 'BAJA'
    SUSPENDIDA = 'SUSPENDIDA'
    CANCELADA = 'CANCELADA'
    
    CHOICES = [
        (VIGENTE, 'Vigente'),
        (BAJA, 'Baja'),
        (SUSPENDIDA, 'Suspendida'),
        (CANCELADA, 'Cancelada'),
    ]


# Tipos de Trámite
class TipoTramite:
    AUTORIZACION_INICIAL = 'AUTORIZACION_INICIAL'
    AUTORIZACION_RUTA = 'AUTORIZACION_RUTA'
    MODIFICACION_AUTORIZACION = 'MODIFICACION_AUTORIZACION'
    RENOVACION_AUTORIZACION = 'RENOVACION_AUTORIZACION'
    RENOVACION_TUC = 'RENOVACION_TUC'
    BAJA_AUTORIZACION = 'BAJA_AUTORIZACION'
    SUSPENSION_AUTORIZACION = 'SUSPENSION_AUTORIZACION'
    INCREMENTO_FLOTA = 'INCREMENTO_FLOTA'
    SUSTITUCION_VEHICULO = 'SUSTITUCION_VEHICULO'
    BAJA_VEHICULO = 'BAJA_VEHICULO'
    HABILITACION_CONDUCTOR = 'HABILITACION_CONDUCTOR'
    BAJA_CONDUCTOR = 'BAJA_CONDUCTOR'
    
    CHOICES = [
        (AUTORIZACION_INICIAL, 'Autorización Inicial'),
        (AUTORIZACION_RUTA, 'Autorización de Ruta'),
        (MODIFICACION_AUTORIZACION, 'Actualización de Empresa y Autorización'),
        (RENOVACION_AUTORIZACION, 'Renovación de Autorización'),
        (RENOVACION_TUC, 'Renovación de TUC'),
        (BAJA_AUTORIZACION, 'Baja de Autorización (Voluntaria)'),
        (SUSPENSION_AUTORIZACION, 'Suspensión de Autorización (Sanción)'),
        (INCREMENTO_FLOTA, 'Incremento de Flota'),
        (SUSTITUCION_VEHICULO, 'Sustitución de Vehículo'),
        (BAJA_VEHICULO, 'Baja de Vehículo'),
        (HABILITACION_CONDUCTOR, 'Habilitación de Conductor'),
        (BAJA_CONDUCTOR, 'Baja de Conductor'),
    ]


# Estados de Trámite (FSM)
class EstadoTramite:
    RECIBIDO = 'RECIBIDO'
    EN_CONTROL_CALIDAD = 'EN_CONTROL_CALIDAD'
    EN_EVAL_TECNICA = 'EN_EVAL_TECNICA'
    EN_DIRECCION_ADMINISTRATIVA = 'EN_DIRECCION_ADMINISTRATIVA'
    EN_DIRECCION_GENERAL = 'EN_DIRECCION_GENERAL'
    OBSERVADO = 'OBSERVADO'
    EN_REVISION_LEGAL = 'EN_REVISION_LEGAL'
    PENDIENTE_FIRMA = 'PENDIENTE_FIRMA'
    APROBADO = 'APROBADO'
    DENEGADO = 'DENEGADO'
    CERRADO = 'CERRADO'
    
    CHOICES = [
        (RECIBIDO, 'Recibido'),
        (EN_CONTROL_CALIDAD, 'En Control de Calidad'),
        (EN_EVAL_TECNICA, 'En Evaluación Técnica'),
        (EN_DIRECCION_ADMINISTRATIVA, 'En Dirección Administrativa'),
        (EN_DIRECCION_GENERAL, 'En Dirección General'),
        (OBSERVADO, 'Observado'),
        (EN_REVISION_LEGAL, 'En Revisión Legal'),
        (PENDIENTE_FIRMA, 'Pendiente de Firma'),
        (APROBADO, 'Aprobado'),
        (DENEGADO, 'Denegado'),
        (CERRADO, 'Cerrado'),
    ]


# Tags técnicos para identificar BAJAS automáticas reversibles
class TagsBajaAutomatica:
    NO_HABILITADO_POR_AUTORIZACION_VENCIDA = "[CAUSA:NO_HABILITADO_POR_AUTORIZACION_VENCIDA]"
    NO_HABILITADO_POR_AUTORIZACION_SUSPENDIDA = "[CAUSA:NO_HABILITADO_POR_AUTORIZACION_SUSPENDIDA]"
    NO_HABILITADO_POR_EMPRESA_INACTIVA = "[CAUSA:NO_HABILITADO_POR_EMPRESA_INACTIVA]"
    BAJA_POR_CANCELACION_AUTORIZACION = "[CAUSA:BAJA_POR_CANCELACION_AUTORIZACION]"
    AUT_SUSPENDIDA_POR_EMPRESA_INACTIVA = "[CAUSA:AUT_SUSPENDIDA_POR_EMPRESA_INACTIVA]"

    # Alias legados para compatibilidad con datos históricos
    VENCIMIENTO_AUTORIZACION = NO_HABILITADO_POR_AUTORIZACION_VENCIDA
    SUSPENSION_AUTORIZACION = NO_HABILITADO_POR_AUTORIZACION_SUSPENDIDA
    EMPRESA_INACTIVA = NO_HABILITADO_POR_EMPRESA_INACTIVA
    CANCELACION_AUTORIZACION = BAJA_POR_CANCELACION_AUTORIZACION
    AUT_CANCELADA_POR_EMPRESA_INACTIVA = AUT_SUSPENDIDA_POR_EMPRESA_INACTIVA

# Tipos de Documento Adjunto
class TipoDocumento:
    SOLICITUD = 'SOLICITUD'
    INFORME_TECNICO = 'INFORME_TECNICO'
    PROYECTO_RESOLUCION = 'PROYECTO_RESOLUCION'
    RESOLUCION = 'RESOLUCION'
    TIV = 'TIV'
    SOAT = 'SOAT'
    CITV = 'CITV'
    LICENCIA = 'LICENCIA'
    DNI = 'DNI'
    CONTRATO = 'CONTRATO'
    OTRO = 'OTRO'
    
    CHOICES = [
        (SOLICITUD, 'Solicitud'),
        (INFORME_TECNICO, 'Informe Técnico'),
        (PROYECTO_RESOLUCION, 'Proyecto de Resolución'),
        (RESOLUCION, 'Resolución'),
        (TIV, 'Tarjeta de Identificación Vehicular'),
        (SOAT, 'SOAT'),
        (CITV, 'CITV'),
        (LICENCIA, 'Licencia de Conducir'),
        (DNI, 'DNI'),
        (CONTRATO, 'Contrato'),
        (OTRO, 'Otro'),
    ]

#Restricciones año conductor - vehiculo
ANIO_MINIMO_FABRICACION_VEHICULO = 1995
ANIO_MINIMO_NACIMIENTO_CONDUCTOR = 1930
