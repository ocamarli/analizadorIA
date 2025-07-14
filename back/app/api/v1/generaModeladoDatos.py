from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import io
import PyPDF2
import xml.etree.ElementTree as ET
import re
from langchain_community.chat_models import AzureChatOpenAI
from langchain.prompts import PromptTemplate

# Blueprint
generar_modelado_bp = Blueprint('generador_modelado_datos', __name__)

# Configuración de LangChain
llm = AzureChatOpenAI(
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1"),
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
    openai_api_key=os.getenv("AZURE_OPENAI_API_KEY", "6076ii7OpLiuTEKYsEVvWyt57RYjzb8d4hDwZRqKuokBi1WTuKz9JQQJ99AJACYeBjFXJ3w3AAABACOGfwuS"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://openaidemobside.openai.azure.com"),
    temperature=0.7
)

@generar_modelado_bp.route('/generar-modelado-datos', methods=['POST'])
def generar_modelado_datos():
    try:
        # Obtener archivos y texto adicional
        files = request.files.getlist('files') if 'files' in request.files else []
        additional_text = request.form.get('additional_text', '').strip()
        
        # Validar que haya al menos archivos o texto adicional
        if not files and not additional_text:
            return jsonify({"error": "Debe proporcionar al menos archivos o texto adicional"}), 400
        
        # Extraer texto de todos los archivos
        texto_completo = ""
        archivos_procesados = 0
        
        for file in files:
            if file.filename == '':
                continue
                     
            # Leer contenido según tipo de archivo
            if file.filename.lower().endswith('.pdf'):
                texto_archivo = extraer_texto_pdf(file)
                if texto_archivo.strip():
                    texto_completo += texto_archivo + "\n\n"
                    archivos_procesados += 1
            elif file.filename.lower().endswith(('.md', '.markdown')):
                file.seek(0)
                texto_archivo = file.read().decode('utf-8')
                if texto_archivo.strip():
                    texto_completo += texto_archivo + "\n\n"
                    archivos_procesados += 1
            elif file.filename.lower().endswith(('.xml', '.drawio')):
                file.seek(0)
                texto_archivo = file.read().decode('utf-8')
                drawio_info = extraer_info_drawio(texto_archivo)
                if drawio_info.strip():
                    texto_completo += drawio_info + "\n\n"
                    archivos_procesados += 1
            elif file.filename.lower().endswith('.mmd'):
                file.seek(0)
                texto_archivo = file.read().decode('utf-8')
                if texto_archivo.strip():
                    texto_completo += f"=== DIAGRAMA MERMAID ===\n{texto_archivo}\n\n"
                    archivos_procesados += 1
            elif file.filename.lower().endswith('.txt'):
                file.seek(0)
                texto_archivo = file.read().decode('utf-8')
                if texto_archivo.strip():
                    texto_completo += texto_archivo + "\n\n"
                    archivos_procesados += 1
            else:
                # Solo validar tipo si hay archivos
                if files and any(f.filename for f in files):
                    return jsonify({"error": f"Tipo de archivo no soportado: {file.filename}"}), 400
        
        # Agregar texto adicional si existe
        if additional_text:
            if texto_completo:
                texto_completo += "\n=== ESPECIFICACIONES DE MODELADO DE DATOS ===\n"
            texto_completo += additional_text + "\n\n"
        
        # Validar que se haya extraído algún contenido
        if not texto_completo.strip():
            return jsonify({"error": "No se pudo extraer texto de los archivos y no se proporcionó texto adicional"}), 400
        
        # Generar modelado de datos con IA
        respuesta_ia = generar_modelado_datos_ia(texto_completo)
        
        return jsonify({
            "success": True,
            "respuesta": respuesta_ia,
            "archivos_procesados": archivos_procesados,
            "texto_adicional_incluido": bool(additional_text)
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500
    
def extraer_texto_pdf(file):
    """Extrae texto de un archivo PDF"""
    try:
        file.seek(0)
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
        texto = ""
        for page in pdf_reader.pages:
            texto += page.extract_text() + "\n"
        return texto
    except Exception as e:
        raise Exception(f"Error extrayendo PDF: {str(e)}")

def extraer_info_drawio(xml_content):
    """Extrae información relevante de un archivo Draw.io XML"""
    try:
        root = ET.fromstring(xml_content)
        
        info_extraida = "=== INFORMACIÓN DE DIAGRAMA DRAW.IO ===\n"
        
        # Buscar elementos con texto
        elementos_texto = []
        for elem in root.iter():
            if elem.get('value'):
                texto = elem.get('value')
                if texto and texto.strip():
                    elementos_texto.append(texto.strip())
        
        if elementos_texto:
            info_extraida += "\nElementos y etiquetas del diagrama:\n"
            for texto in elementos_texto:
                info_extraida += f"- {texto}\n"
        
        return info_extraida
        
    except Exception as e:
        return f"Error procesando Draw.io XML: {str(e)}"

def generar_modelado_datos_ia(texto_documento):
    """Genera modelado de datos usando IA"""
    
    fecha_actual = datetime.now().strftime('%Y-%m-%d')
    
    prompt_template = PromptTemplate(
        input_variables=["documento", "fecha"],
        template="""
Eres un Arquitecto de Datos senior especializado en modelado de bases de datos. Tu tarea es analizar la documentación proporcionada (historias técnicas, requerimientos, análisis) para generar un documento completo de modelado de datos siguiendo el formato corporativo específico en Markdown.

DOCUMENTACIÓN PROPORCIONADA:
{documento}

INSTRUCCIONES CRÍTICAS:
1. ANALIZA completamente la documentación para identificar entidades, atributos y relaciones
2. EXTRAE información sobre tablas/colecciones, campos, tipos de datos y restricciones
3. DEFINE índices necesarios basados en consultas y rendimiento
4. ESPECIFICA consultas principales (CRUD) que utilizará el sistema
5. INCLUYE estrategias de depuración y consideraciones técnicas
6. MANTÉN el formato EXACTO del documento corporativo proporcionado
7. USA el formato Markdown pero respetando la estructura de tablas específica

GENERAR EL SIGUIENTE DOCUMENTO DE MODELADO DE DATOS EN MARKDOWN:

---

**Nombre de producto:**
[Extraer nombre del proyecto del documento]

**Base de datos:**
[Extraer nombre de BD del documento o definir basado en el proyecto]

**Colección:**
[Extraer nombre de tabla/colección principal del documento]

**Propietario del documento:**
[Extraer responsable del documento o indicar REQUIERE DEFINICIÓN]

*Tabla 1: Datos generales*

---

**Contenido**

**Índice**

1. [Control de cambios](#1-control-de-cambios)
2. [Esquema colección](#2-esquema-colección)
3. [Estrategia de Índices](#3-estrategia-de-índices)
4. [Datos operativos](#4-datos-operativos)
   - 4.1. [Mecanismo de acceso](#41-mecanismo-de-acceso)
   - 4.2. [Análisis Técnico de consultas](#42-análisis-técnico-de-consultas)
   - 4.3. [Integración de componentes](#43-integración-de-componentes)
5. [Estrategia de depuración](#5-estrategia-de-depuración)
6. [Deuda técnica](#6-deuda-técnica)
7. [Referencias](#7-referencias)

---

## 1. Control de cambios

| **Versión** | **Nombre del editor** | **Fecha de actualización** | **Cambios realizados** |
|-------------|----------------------|---------------------------|------------------------|
| 1.0.0 | [Extraer autor del documento o indicar REQUIERE DEFINICIÓN] | {fecha} | [Extraer descripción inicial o usar "Se inicia documento de modelado de datos basado en análisis de requerimientos"] |
| | | | |
| | | | |

*Tabla 2: Control de cambios*

---

## 2. Esquema colección

| **Campo** | **Valor** |
|-----------|-----------|
| **Colección o tabla** | [Extraer nombre de tabla principal del análisis] |
| **Objetivo** | [Transaccional/Analítico - basado en el propósito identificado] |
| **Descripción** | [Extraer descripción funcional de la tabla basada en el documento] |
| **Nombre BD** | [Extraer nombre de base de datos del documento] |
| **Motor BD** | [Extraer motor: PostgreSQL/MySQL/MongoDB/SQL Server según documento] |
| **Arquitecto Owner** | [Extraer responsable del documento] |
| **Arquitecto modificó** | [Extraer responsable del documento] |
| **¿Almacena información biométrica?** | [Sí/No - basado en análisis del documento] |

*Tabla 3: Datos generales de la colección*

---

### Esquema de campos

| **Identificador** | **Tipo** | **Acción** | **Cifrado** | **Descripción del identificador** |
|-------------------|----------|------------|-------------|-----------------------------------|
| [Extraer campos del análisis técnico] | [Definir tipos: Integer PK/VARCHAR/etc.] | **Se agrega** | [Sí/No] | [Extraer descripción funcional del campo] |
| [Campo 2] | [Tipo de dato] | **Se agrega** | [Sí/No] | [Descripción funcional] |
| [Campo 3] | [Tipo de dato] | **Se agrega** | [Sí/No] | [Descripción funcional] |
| [Campo 4] | [Tipo de dato] | **Se agrega** | [Sí/No] | [Descripción funcional] |
| [Campo 5] | [Tipo de dato] | **Se agrega** | [Sí/No] | [Descripción funcional] |

*Tabla 4: Actualización de esquema de la colección*

---

## 3. Estrategia de Índices

| **Índice** | **Acción** | **Justificación** |
|------------|------------|-------------------|
| [Extraer campos que requieren índices basado en consultas] | **Se agrega** | [Justificar basado en performance y consultas frecuentes] |
| [Índice 2] | **Se agrega** | [Justificación técnica] |
| [Índice 3] | **Se agrega** | [Justificación técnica] |

*Tabla 5: Actualización de índices*

---

## 4. Datos operativos

### 4.1. Mecanismo de acceso

| **Mecanismo de Acceso** | **Descripción** |
|------------------------|-----------------|
| **Lectura** | [Extraer tecnología de acceso del documento: ORM/PDO/etc.] |
| **Escritura** | [Extraer tecnología de acceso del documento: ORM/PDO/etc.] |

*Tabla 6: Descripción del mecanismo de acceso*

---

### 4.2. Análisis Técnico de consultas

| **ID** | **Query** | **Acción** | **Índices** |
|--------|-----------|------------|-------------|
| 1 | [Extraer consulta SELECT principal basada en funcionalidades] | **Se agrega** | [Índices requeridos] |
| 2 | [Extraer consulta INSERT basada en operaciones] | **Se agrega** | [Índices requeridos] |
| 3 | [Extraer consulta UPDATE basada en operaciones] | **Se agrega** | [Índices requeridos] |
| 4 | [Extraer consulta DELETE basada en operaciones] | **Se agrega** | [Índices requeridos] |
| 5 | [Consulta específica del dominio extraída del análisis] | **Se agrega** | [Índices requeridos] |

*Tabla 7: Análisis técnico de consultas a BD*

---

### 4.3. Integración de componentes

| **Componente** | **Descripción** | **Queries** |
|----------------|-----------------|-------------|
| [Extraer servicios/componentes del análisis técnico] | [Descripción funcional del componente] | [Referencias a queries de tabla 7] |
| [Componente 2] | [Descripción funcional] | [Referencias a queries] |

*Tabla 8: Integración de componentes*

---

## 5. Estrategia de depuración

| **Nombre** | **Acción** | **Descripción** | **Planificación** |
|------------|------------|-----------------|-------------------|
| [Extraer procesos de limpieza del análisis] | **Se agrega** | [Descripción del proceso de depuración] | [Cuándo y cómo se ejecuta la depuración] |
| [Proceso 2] | **Se agrega** | [Descripción] | [Planificación específica] |

*Tabla 9: Actualización de estrategia de depuración*

---

## 6. Deuda técnica

### 6.1. Análisis Técnico de funciones

| **ID** | **Función** | **Acción** | **Complejidad** | **Repositorio** |
|--------|-------------|------------|-----------------|-----------------|
| [Extraer funciones complejas del análisis] | [Función específica] | **Se agrega** | [Alta/Media/Baja] | [Ubicación del código] |
| [ID 2] | [Función 2] | **Se agrega** | [Complejidad] | [Repositorio] |

*Tabla 10: Análisis técnico de funciones*

---

## 7. Referencias

### Documentos utilizados para el modelado:

- [Extraer referencias de documentos utilizados]
- [Documento 2]
- [Documento 3]

### Estándares aplicados:

- [Extraer estándares de nomenclatura, tipos de datos, etc.]
- [Estándar 2]

---

**NOTAS ADICIONALES:**

### Consideraciones de Performance:
[Extraer consideraciones de rendimiento del análisis]

### Consideraciones de Seguridad:
[Extraer aspectos de seguridad de datos identificados]

### Escalabilidad:
[Extraer consideraciones de escalabilidad]

### Backup y Recovery:
[Extraer estrategias de respaldo si están documentadas]

---

**REGLAS PARA LA GENERACIÓN DEL MODELADO:**
- Extraer TODAS las entidades, atributos y relaciones del análisis técnico
- Definir tipos de datos apropiados según el motor de base de datos especificado
- Justificar índices basándose en consultas y patrones de acceso identificados
- Especificar consultas CRUD principales que soportarán las funcionalidades
- Incluir consideraciones de performance, seguridad y mantenibilidad
- Mantener trazabilidad con requerimientos y historias técnicas originales
- Seguir convenciones de nomenclatura estándar para el motor de BD seleccionado

---
"""
    )
    
    try:
        chain = prompt_template | llm
        resultado = chain.invoke({
            "documento": texto_documento,
            "fecha": fecha_actual
        })
        
        return resultado.content if hasattr(resultado, 'content') else str(resultado)
        
    except Exception as e:
        return f"Error generando modelado de datos: {str(e)}"