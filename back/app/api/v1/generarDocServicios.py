from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import io
import PyPDF2
from langchain_community.chat_models import AzureChatOpenAI
from langchain.prompts import PromptTemplate
import logging
import re

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Blueprint
documentoServicios_bp = Blueprint('generador_documentos_servicios', __name__)

# Configuración LangChain
try:
    llm = AzureChatOpenAI(
        deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1"),
        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        openai_api_key=os.getenv("AZURE_OPENAI_API_KEY", "6076ii7OpLiuTEKYsEVvWyt57RYjzb8d4hDwZRqKuokBi1WTuKz9JQQJ99AJACYeBjFXJ3w3AAABACOGfwuS"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://openaidemobside.openai.azure.com"),
        temperature=0.3  # Menos creatividad, más precisión técnica
    )
    logger.info("LLM configurado correctamente")
except Exception as e:
    logger.error(f"Error configurando LLM: {str(e)}")
    llm = None

def extract_text_from_pdf(file_content):
    """Extrae texto de un archivo PDF"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"Error al leer PDF: {str(e)}")

def extract_text_from_markdown(file_content):
    """Extrae texto de un archivo Markdown"""
    try:
        return file_content.decode('utf-8').strip()
    except Exception as e:
        raise Exception(f"Error al leer Markdown: {str(e)}")

def clean_service_document_response(content):
    """Limpieza específica para documentos de servicios"""
    # Remover bloques de código markdown si están mal formateados
    if '```' in content:
        parts = content.split('```')
        cleaned_parts = []
        for i, part in enumerate(parts):
            if i % 2 == 0:  # Texto fuera de bloques de código
                cleaned_parts.append(part)
            else:  # Dentro de bloque de código
                cleaned_parts.append(f'```{part}```')
        content = ''.join(cleaned_parts)
    
    # Limpiar caracteres problemáticos pero preservar formato markdown
    lines = content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Preservar líneas de encabezados, listas, tablas, etc.
        if (line.strip().startswith('#') or 
            line.strip().startswith('|') or 
            line.strip().startswith('-') or 
            line.strip().startswith('*') or 
            line.strip().startswith('>')):
            cleaned_lines.append(line)
        else:
            # Para texto normal, hacer limpieza mínima
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines).strip()

def validate_service_document(content):
    """Validación para documentos de servicios"""
    content = content.strip()
    if not content:
        return False, "Contenido vacío"
    
    # Verificar que tenga estructura de documento
    has_headers = any(line.strip().startswith('#') for line in content.split('\n'))
    if not has_headers:
        return False, "El documento debe tener al menos un encabezado"
    
    # Verificar longitud mínima
    if len(content) < 500:
        return False, "El documento parece muy corto para ser un documento de servicio completo"
    
    return True, None

# Template para documentos de servicios
service_document_prompt = PromptTemplate(
    input_variables=["contenido_archivo", "contexto_adicional"],
    template="""
Eres un arquitecto de software senior especializado en documentación técnica de servicios y APIs. Analiza el contenido proporcionado y genera un documento técnico completo y detallado para un servicio/API en formato Markdown.

CONTENIDO A ANALIZAR:
{contenido_archivo}

CONTEXTO ADICIONAL:
{contexto_adicional}

ESTRUCTURA REQUERIDA DEL DOCUMENTO:

# [Nombre del Servicio] - Documentación Técnica

**Nombre del proyecto:** [ID] - [Nombre del Sistema]  
**Nombre del servicio:** [nombre-del-servicio]  
**Propietario del documento:** [Área responsable]  
**Versión:** 1.0.0  
**Fecha:** [Fecha actual]

---

## Contenido

1. [Control de cambios](#control-de-cambios)
2. [Descripción del servicio](#descripción-del-servicio)
3. [Stack tecnológico](#stack-tecnológico)
4. [Repositorios](#repositorios)
5. [Ambientes](#ambientes)
6. [URLs de ambientes](#urls-de-ambientes)
7. [Supuestos](#supuestos)
8. [Limitaciones y acciones futuras](#limitaciones-y-acciones-futuras)
9. [Dependencias](#dependencias)
10. [Configuración de conexiones](#configuración-de-conexiones)
11. [Descripción de las APIs](#descripción-de-las-apis)
12. [Estatus utilizados](#estatus-utilizados)
13. [Timeouts](#timeouts)
14. [Cloud-Native containers](#cloud-native-containers)
15. [Seguridad](#seguridad)
16. [Glosario](#glosario)
17. [Referencias](#referencias)

---

## Control de cambios

| Versión | Nombre del editor | Fecha de actualización | Cambios realizados |
|---------|-------------------|------------------------|-------------------|
| 1.0.0 | [Nombre] | [Fecha] | Creación de documento |

---

## Descripción del servicio

[Describir la función principal del servicio, su propósito dentro del sistema, y las funcionalidades que expone. Explicar si es un servicio de dominio, proxy, o de qué tipo es según la arquitectura.]

**Funcionalidades principales:**
- [Funcionalidad 1]: [Descripción]
- [Funcionalidad 2]: [Descripción]
- [Funcionalidad 3]: [Descripción]

---

## Stack tecnológico

| Función | Tecnología y versión |
|---------|---------------------|
| Lenguaje de desarrollo | [Lenguaje + Versión] |
| Framework | [Framework + Versión] |
| Implementación de repositorio | [ORM/Repository pattern] |
| Servidor | [Servidor de aplicaciones] |
| ORM o DBConnector | [Tecnología de BD] |
| Plataforma | [Cloud/On-premise] |
| Monitoreo | [Herramientas de monitoreo] |
| Exposición | [HTTP/HTTPS] |

---

## Repositorios

| Herramienta | URL |
|-------------|-----|
| GitLab documentación | [URL] |
| Web a la documentación | [URL] |
| GitLab a código fuente | [URL] |

---

## Ambientes

| Herramienta | Desarrollo | Pruebas | Producción |
|-------------|------------|---------|------------|
| [Ambiente 1] | ✓ | ✓ | ✓ |
| [Ambiente 2] | ✓ | ✓ | ✓ |

---

## URLs de ambientes

| Ambiente | URL |
|----------|-----|
| Desarrollo | [URL desarrollo] |
| Pruebas | [URL pruebas] |
| Producción | [URL producción] |

---

## Supuestos

- [Supuesto 1]
- [Supuesto 2]
- [Supuesto 3]

---

## Limitaciones y acciones futuras

**Limitaciones actuales:**
- [Limitación 1]
- [Limitación 2]

**Acciones futuras:**
- [Acción futura 1]
- [Acción futura 2]

---

## Dependencias

### [Nombre de la Dependencia]

| Dependencia | [Nombre] |
|-------------|----------|
| Tipo (Servicios, base de datos) | [Tipo] |
| Tecnología | [Tecnología + Versión] |
| Descripción | [Descripción detallada] |
| Usuario | [Usuario de conexión] |
| Rol y atributo | [Roles] |
| **Variables de entorno** |  |
| [Variable 1] | [Descripción] |
| [Variable 2] | [Descripción] |
| Timeouts | [Tiempo en ms] |
| Permisos requeridos | [Lectura/Escritura] |
| Patrón de reintento | [Patrón] |
| Mensajes de error | [Códigos de error] |

---

## Configuración de conexiones

| Variables de configuración | Valor |
|----------------------------|-------|
| [Variable 1] | [Valor/Placeholder] |
| [Variable 2] | [Valor/Placeholder] |
| [Variable 3] | [Valor/Placeholder] |

---

## Descripción de las APIs

### Enlace a documentación OpenAPI

| Documentación | URL |
|---------------|-----|
| OpenAPI/Swagger | [URL] |
| Diseño de servicio | [URL] |

### Endpoints principales

#### [Endpoint 1] - [Nombre descriptivo]

**Descripción:** [Descripción detallada de la funcionalidad]

**Método:** `[GET/POST/PUT/DELETE]`  
**Ruta:** `[/api/v1/endpoint]`  
**Autenticación:** [Requerida/No requerida]

**Parámetros:**
- `[parametro1]` (tipo): [Descripción]
- `[parametro2]` (tipo): [Descripción]

**Respuesta exitosa (200):**
```json
{{
  "ejemplo": "respuesta"
}}
```

**Respuestas de error:**
- `400`: [Descripción del error]
- `404`: [Descripción del error]
- `500`: [Descripción del error]

#### [Endpoint 2] - [Nombre descriptivo]

[Seguir mismo formato para cada endpoint...]

---

## Estatus utilizados

| Pregunta | Sí | No |
|----------|----|----|
| ¿El servicio implementa el protocolo HTTP? | ✓ |  |
| ¿La respuesta implementa códigos 5XX para errores del servidor? | ✓ |  |
| ¿La respuesta implementa códigos 4XX para errores del cliente? | ✓ |  |
| ¿La respuesta implementa códigos 2XX solo para respuestas exitosas? | ✓ |  |

---

## Timeouts

| Método | Timeout [ms] | Tamaño Request (KB) | Tamaño Response (KB) |
|--------|--------------|-------------------|---------------------|
| [Endpoint 1] | [300] | [1] | [5] |
| [Endpoint 2] | [500] | [2] | [10] |
| [Endpoint 3] | [1000] | [5] | [50] |

---

## Cloud-Native containers

### Configuración del contenedor

| Configuración | Valor |
|---------------|-------|
| memory | [Valor] |
| memory-swap | [Valor] |
| cpus | [Valor] |
| cpu-period | [Valor] |
| cpu-quota | [Valor] |

### Administración del contenedor

| Característica | Sí | No |
|----------------|----|----|
| ¿Administrado con kubernetes/Openshift? | ✓ |  |
| ¿Cuenta con función de Liveness? | ✓ |  |
| ¿Cuenta con función de Readiness? | ✓ |  |

### Configuración de Readiness

| Configuración | Valor |
|---------------|-------|
| initialDelaySeconds | [10] |
| periodSeconds | [10] |

---

## Seguridad

### Seguridad en la API

| Característica | Valor |
|----------------|-------|
| Exposición | [Interno/Externo] |
| Protocolo de comunicación | [HTTPS] |
| Versión de TLS habilitada | [TLS 1.2/1.3] |
| Puerto de comunicación | [443] |
| Mecanismo de autenticación | [JWT/OAuth2/IDC] |
| Mecanismo de autorización | [RBAC/ACL] |
| Límite de solicitudes | [Rate limiting] |
| Restricción por IP | [Sí/No] |
| API Gateway | [Descripción de la arquitectura] |

### Documentación de logs

| Nombre | Descripción | Ubicación |
|--------|-------------|-----------|
| [Nombre del log] | [Descripción] | [Ruta/Sistema] |

### Seguridad en los datos

| Dato | Descripción | Cifrado | Algoritmo | Enmascarado |
|------|-------------|---------|-----------|-------------|
| [Tipo de dato] | [Descripción] | [Sí/No] | [Algoritmo] | [Sí/No] |

---

## Glosario

| Término | Descripción |
|---------|-------------|
| [Término 1] | [Definición] |
| [Término 2] | [Definición] |

---

## Referencias

### Documentación técnica
- [Referencia 1]: [URL]
- [Referencia 2]: [URL]

### Estándares de seguridad
- [Estándar 1]: [URL]
- [Estándar 2]: [URL]

---

**Documento generado automáticamente - Revisar y validar información técnica específica**

INSTRUCCIONES ESPECÍFICAS:
1. Analiza el contenido proporcionado y extrae información relevante para cada sección
2. Completa las tablas con información específica del servicio/API
3. Documenta todos los endpoints identificados siguiendo el formato establecido
4. Incluye detalles específicos de configuración, timeouts y seguridad
5. Adapta el contenido al contexto técnico del servicio analizado
6. Si falta información en alguna sección, indica "[Pendiente de definir]"
7. Mantén un tono técnico y profesional
8. Asegúrate de que el documento sea coherente y completo

Genera SOLO el documento de servicio en formato Markdown basado en el análisis del contenido:
"""
)

@documentoServicios_bp.route('/generar-documento-servicio', methods=['POST'])
def generate_service_document():
    """Genera documento técnico de servicio/API"""
    try:
        logger.info("=== GENERANDO DOCUMENTO DE SERVICIO ===")
        
        if llm is None:
            return jsonify({
                'success': False,
                'error': 'LLM no configurado'
            }), 500
        
        # Obtener datos
        files = request.files.getlist('files')
        contexto_adicional = request.form.get('additional_text', '').strip()
        
        if not files and not contexto_adicional:
            return jsonify({
                'success': False,
                'error': 'Se requiere al menos un archivo o contexto adicional'
            }), 400
        
        contenido_archivo = ""
        
        # Procesar archivos
        if files:
            for file in files:
                try:
                    file_content = file.read()
                    
                    if file.filename.lower().endswith('.pdf'):
                        texto_extraido = extract_text_from_pdf(file_content)
                        contenido_archivo += f"\n--- ARCHIVO: {file.filename} ---\n{texto_extraido}\n"
                    
                    elif file.filename.lower().endswith(('.md', '.markdown', '.txt')):
                        texto_extraido = extract_text_from_markdown(file_content)
                        contenido_archivo += f"\n--- ARCHIVO: {file.filename} ---\n{texto_extraido}\n"
                    
                    else:
                        return jsonify({
                            'success': False,
                            'error': f'Formato no soportado: {file.filename}. Use PDF, Markdown o TXT'
                        }), 400
                        
                except Exception as e:
                    return jsonify({
                        'success': False,
                        'error': f'Error procesando {file.filename}: {str(e)}'
                    }), 400
        
        if not contenido_archivo and contexto_adicional:
            contenido_archivo = "Información proporcionada directamente por el usuario."
        
        # Generar documento con IA
        logger.info("Generando documento de servicio con IA...")
        chain = service_document_prompt | llm
        
        response = chain.invoke({
            'contenido_archivo': contenido_archivo,
            'contexto_adicional': contexto_adicional or "Sin contexto adicional especificado."
        })
        
        # Limpieza del contenido
        document_content = clean_service_document_response(response.content)
        
        logger.info(f"Documento generado exitosamente. Longitud: {len(document_content)} caracteres")
        
        # Validación
        is_valid, error_msg = validate_service_document(document_content)
        
        if not is_valid:
            logger.warning(f"Validación falló: {error_msg}")
            # Reintento con instrucciones más específicas
            retry_response = chain.invoke({
                'contenido_archivo': contenido_archivo,
                'contexto_adicional': f"{contexto_adicional}\n\nIMPORTANTE: Genera un documento técnico completo y detallado de servicio/API con todas las secciones requeridas."
            })
            
            document_content = clean_service_document_response(retry_response.content)
            is_valid, error_msg = validate_service_document(document_content)
            
            if not is_valid:
                logger.warning(f"Segundo intento falló: {error_msg}. Enviando resultado parcial.")
        
        logger.info("=== DOCUMENTO DE SERVICIO GENERADO EXITOSAMENTE ===")
        
        return jsonify({
            'success': True,
            'respuesta': document_content,
            'document_type': 'service_document',
            'message': 'Documento de servicio generado exitosamente',
            'timestamp': datetime.now().isoformat(),
            'word_count': len(document_content.split()),
            'sections_detected': len([line for line in document_content.split('\n') if line.strip().startswith('#')])
        })
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@documentoServicios_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint de salud"""
    return jsonify({
        'status': 'healthy',
        'service': 'service_document_generator',
        'timestamp': datetime.now().isoformat(),
        'llm_configured': llm is not None,
        'supported_formats': ['PDF', 'Markdown', 'TXT'],
        'document_type': 'Service/API Technical Document'
    })