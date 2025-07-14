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
documentoArquitectura_bp = Blueprint('generador_documentos_arquitectura', __name__)

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

def clean_architecture_document_response(content):
    """Limpieza específica para documentos de arquitectura"""
    # Remover bloques de código markdown si están mal formateados
    if '```' in content:
        # Si hay bloques de código, preservarlos pero limpiar el resto
        parts = content.split('```')
        cleaned_parts = []
        for i, part in enumerate(parts):
            if i % 2 == 0:  # Texto fuera de bloques de código
                cleaned_parts.append(part)
            else:  # Dentro de bloque de código
                cleaned_parts.append(f'```{part}```')
        content = ''.join(cleaned_parts)
    
    # Limpiar caracteres problemáticos pero preservar formato markdown
    # Mantener saltos de línea, asteriscos, guiones, etc.
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

def validate_architecture_document(content):
    """Validación para documentos de arquitectura"""
    content = content.strip()
    if not content:
        return False, "Contenido vacío"
    
    # Verificar que tenga estructura de documento
    has_headers = any(line.strip().startswith('#') for line in content.split('\n'))
    if not has_headers:
        return False, "El documento debe tener al menos un encabezado"
    
    # Verificar longitud mínima
    if len(content) < 500:
        return False, "El documento parece muy corto para ser un documento de arquitectura completo"
    
    return True, None

# Template para documentos de arquitectura
architecture_document_prompt = PromptTemplate(
    input_variables=["contenido_archivo", "contexto_adicional"],
    template="""
Eres un arquitecto de software senior especializado en documentación técnica. Analiza el contenido proporcionado y genera un documento de arquitectura de software completo, detallado y profesional en formato Markdown.

CONTENIDO A ANALIZAR:
{contenido_archivo}

CONTEXTO ADICIONAL:
{contexto_adicional}

ESTRUCTURA REQUERIDA DEL DOCUMENTO:

# [Nombre del Sistema] - Documento de Arquitectura de Software

**Versión:** 1.0.0  
**Fecha:** [Fecha actual]  
**Propietario:** [Área/Equipo responsable]

---

## Índice
1. [Control de cambios](#control-de-cambios)
2. [Información del proceso de negocio](#información-del-proceso-de-negocio)
3. [Arquitectura actual (as-is)](#arquitectura-actual-as-is)
4. [Solución propuesta (to-be)](#solución-propuesta-to-be)
5. [Componentes y dependencias](#componentes-y-dependencias)
6. [Patrones de diseño](#patrones-de-diseño)
7. [Análisis de riesgos](#análisis-de-riesgos)
8. [Glosario](#glosario)

---

## 1. Control de cambios

### 1.1 Descripción de cambios
| Versión | Editor | Fecha | Cambios realizados |
|---------|--------|-------|-------------------|
| 1.0.0 | [Nombre] | [Fecha] | Creación del documento |

### 1.2 Mejora continua
| Autor | Subdominio | Acción |
|-------|------------|--------|
| [Nombre] | [Dominio] | [Descripción de la mejora] |

---

## 2. Información del proceso de negocio

### 2.1 Contexto
[Describir el contexto del negocio, la problemática actual y la necesidad que resuelve el sistema]

### 2.2 Objetivo de la solución
**Objetivos principales:**
- [Objetivo 1]
- [Objetivo 2]
- [Objetivo 3]

**Funcionalidades clave:**
- [Funcionalidad 1]: [Descripción]
- [Funcionalidad 2]: [Descripción]
- [Funcionalidad 3]: [Descripción]

### 2.3 Proceso de negocio to-be
[Describir el proceso de negocio optimizado que soportará el sistema]

### 2.4 Capacidades de negocio
| Vista | Versión | Descripción |
|-------|---------|-------------|
| [Capacidad 1] | 1.0.0 | [Descripción] |
| [Capacidad 2] | 1.0.0 | [Descripción] |

### 2.5 Dominio de negocio afectado
| Dominio | Justificación | Owners |
|---------|---------------|--------|
| [Dominio] | [Justificación] | [Responsable] |

---

## 3. Arquitectura actual (as-is)

### 3.1 Diagrama de arquitectura general as-is
[Si existe sistema actual, describir la arquitectura actual]

### 3.2 Diagrama de arquitectura tecnológica as-is
[Describir la tecnología actual si aplica]

---

## 4. Solución propuesta (to-be)

### 4.1 Arquitectura general to-be

#### 4.1.1 Componentes de seguridad

**Componentes On Premise/IaaS:**
| Dirección IP | Función | Sistema Operativo |
|--------------|---------|-------------------|
| [IP/Hostname] | [Función] | [SO + Versión] |

**Componentes de software:**
| Componente | Tipo | Stack Tecnológico | URL |
|------------|------|-------------------|-----|
| [Nombre] | [Frontend/Backend/DB] | [Tecnología + Versión] | [URL si aplica] |

**Componentes PaaS/SaaS:**
| Componente | Descripción | URL |
|------------|-------------|-----|
| [Servicio] | [Descripción] | [URL] |

#### 4.1.2 Transacciones críticas
| Transacción | Descripción |
|-------------|-------------|
| [Transacción 1] | [Descripción detallada] |
| [Transacción 2] | [Descripción detallada] |

### 4.2 Arquitectura tecnológica to-be

#### 4.2.1 Detalle de componentes
| Componente | Tipo | Objetivo | Owner |
|------------|------|----------|-------|
| [Componente 1] | [Nuevo/Existente] | [Propósito] | [Responsable] |
| [Componente 2] | [Nuevo/Existente] | [Propósito] | [Responsable] |

#### 4.2.2 Dependencias
| Dependencia | Tipo | Owner |
|-------------|------|-------|
| [Dependencia 1] | [Interna/Externa] | [Responsable] |
| [Dependencia 2] | [Interna/Externa] | [Responsable] |

### 4.3 Supuestos, limitaciones y acciones futuras

**Supuestos:**
- [Supuesto 1]
- [Supuesto 2]

**Limitaciones:**
- [Limitación 1]
- [Limitación 2]

**Acciones futuras:**
- [Acción 1]
- [Acción 2]

---

## 5. Componentes y dependencias

### 5.1 Especialistas requeridos
| Rol | Área | Justificación |
|-----|------|---------------|
| [Rol] | [Área] | [Justificación] |

### 5.2 Dominios externos participantes
| Dominio | Justificación | Participantes |
|---------|---------------|---------------|
| [Dominio] | [Justificación] | [Participantes] |

---

## 6. Patrones de diseño

| Patrón | Clasificación | Justificación | Componentes |
|--------|---------------|---------------|-------------|
| [Patrón 1] | [Tipo] | [Justificación] | [Componentes] |
| [Patrón 2] | [Tipo] | [Justificación] | [Componentes] |

---

## 7. Análisis de riesgos

### 7.1 Análisis pre-mortem
| Posible falla | Gravedad | Complejidad | Probabilidad | Acciones |
|---------------|----------|-------------|--------------|----------|
| [Falla 1] | [Alta/Media/Baja] | [Alta/Media/Baja] | [Alta/Media/Baja] | [Acciones preventivas] |
| [Falla 2] | [Alta/Media/Baja] | [Alta/Media/Baja] | [Alta/Media/Baja] | [Acciones preventivas] |

---

## 8. Glosario

| Término | Descripción |
|---------|-------------|
| [Término 1] | [Definición] |
| [Término 2] | [Definición] |

---

## Anexos

### A.1 Diagramas adicionales
[Incluir diagramas complementarios si es necesario]

### A.2 Referencias
- [Referencia 1]
- [Referencia 2]

---

**Documento generado automáticamente - Revisar y ajustar según necesidades específicas del proyecto**

INSTRUCCIONES ESPECÍFICAS:
1. Analiza el contenido proporcionado y extrae información relevante para cada sección
2. Completa las tablas con información específica del sistema
3. Adapta el contenido al contexto del proyecto analizado
4. Mantén un tono profesional y técnico
5. Incluye detalles específicos de tecnologías, componentes y arquitectura
6. Si falta información en alguna sección, indica "[Información pendiente de definir]"
7. Asegúrate de que el documento sea coherente y completo

Genera SOLO el documento de arquitectura en formato Markdown basado en el análisis del contenido:
"""
)

@documentoArquitectura_bp.route('/generar-documento-arquitectura', methods=['POST'])
def generate_architecture_document():
    """Genera documento de arquitectura de software"""
    try:
        logger.info("=== GENERANDO DOCUMENTO DE ARQUITECTURA ===")
        
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
        logger.info("Generando documento de arquitectura con IA...")
        chain = architecture_document_prompt | llm
        
        response = chain.invoke({
            'contenido_archivo': contenido_archivo,
            'contexto_adicional': contexto_adicional or "Sin contexto adicional especificado."
        })
        
        # Limpieza del contenido
        document_content = clean_architecture_document_response(response.content)
        
        logger.info(f"Documento generado exitosamente. Longitud: {len(document_content)} caracteres")
        
        # Validación
        is_valid, error_msg = validate_architecture_document(document_content)
        
        if not is_valid:
            logger.warning(f"Validación falló: {error_msg}")
            # Reintento con instrucciones más específicas
            retry_response = chain.invoke({
                'contenido_archivo': contenido_archivo,
                'contexto_adicional': f"{contexto_adicional}\n\nIMPORTANTE: Genera un documento de arquitectura completo y detallado con todas las secciones requeridas."
            })
            
            document_content = clean_architecture_document_response(retry_response.content)
            is_valid, error_msg = validate_architecture_document(document_content)
            
            if not is_valid:
                logger.warning(f"Segundo intento falló: {error_msg}. Enviando resultado parcial.")
        
        logger.info("=== DOCUMENTO DE ARQUITECTURA GENERADO EXITOSAMENTE ===")
        
        return jsonify({
            'success': True,
            'respuesta': document_content,
            'document_type': 'architecture_document',
            'message': 'Documento de arquitectura generado exitosamente',
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

@documentoArquitectura_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint de salud"""
    return jsonify({
        'status': 'healthy',
        'service': 'architecture_document_generator',
        'timestamp': datetime.now().isoformat(),
        'llm_configured': llm is not None,
        'supported_formats': ['PDF', 'Markdown', 'TXT'],
        'document_type': 'Software Architecture Document'
    })