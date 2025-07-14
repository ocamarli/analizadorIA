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
analizar_arquitectura_bp = Blueprint('analizador_arquitectura', __name__)

# Configuración de LangChain
llm = AzureChatOpenAI(
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1"),
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
    openai_api_key=os.getenv("AZURE_OPENAI_API_KEY", "6076ii7OpLiuTEKYsEVvWyt57RYjzb8d4hDwZRqKuokBi1WTuKz9JQQJ99AJACYeBjFXJ3w3AAABACOGfwuS"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://openaidemobside.openai.azure.com"),
    temperature=0.7
)

@analizar_arquitectura_bp.route('/analizar-arquitectura', methods=['POST'])
def analizar_arquitectura():
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
            else:
                # Solo validar tipo si hay archivos
                if files and any(f.filename for f in files):
                    return jsonify({"error": f"Tipo de archivo no soportado: {file.filename}"}), 400
        
        # Agregar texto adicional si existe
        if additional_text:
            if texto_completo:
                texto_completo += "\n=== INFORMACIÓN ADICIONAL ===\n"
            texto_completo += additional_text + "\n\n"
        
        # Validar que se haya extraído algún contenido
        if not texto_completo.strip():
            return jsonify({"error": "No se pudo extraer texto de los archivos y no se proporcionó texto adicional"}), 400
        
        # Generar análisis de arquitectura con IA
        respuesta_ia = generar_analisis_arquitectura(texto_completo)
        
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

def generar_analisis_arquitectura(texto_documento):
    """Genera análisis de arquitectura de software usando IA"""
    
    fecha_actual = datetime.now().strftime('%d/%m/%Y')
    
    prompt_template = PromptTemplate(
        input_variables=["documento", "fecha"],
        template="""
Eres un arquitecto de software senior especializado en análisis y diseño de sistemas. Tu tarea es analizar minuciosamente la documentación, diagramas y contexto proporcionado para generar un análisis completo de arquitectura de software en formato Markdown.

DOCUMENTACIÓN Y DIAGRAMAS A ANALIZAR:
{documento}

INSTRUCCIONES CRÍTICAS:
1. ANALIZA completamente toda la documentación, diagramas XML/DrawIO, código Mermaid y contexto proporcionado
2. IDENTIFICA patrones arquitectónicos, componentes, servicios, bases de datos y tecnologías
3. EXTRAE información sobre: integraciones, APIs, flujos de datos, seguridad, escalabilidad
4. DETECTA arquitecturas implícitas en los diagramas y documentación
5. Para información NO disponible, marca como "REQUIERE DEFINICIÓN"
6. MANTÉN formato Markdown estricto y profesional

GENERAR EL SIGUIENTE ANÁLISIS DE ARQUITECTURA EN MARKDOWN:

---

# Análisis de Arquitectura de Software

**Proyecto:** [Extraer nombre del proyecto del documento]

**Fecha del Análisis:** {fecha}

**Versión:** 1.0

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Arquitectura General](#arquitectura-general)
3. [Componentes del Sistema](#componentes-del-sistema)
4. [Tecnologías Identificadas](#tecnologías-identificadas)
5. [Patrones Arquitectónicos](#patrones-arquitectónicos)
6. [Integraciones y APIs](#integraciones-y-apis)
7. [Gestión de Datos](#gestión-de-datos)
8. [Seguridad](#seguridad)
9. [Escalabilidad y Rendimiento](#escalabilidad-y-rendimiento)
10. [Infraestructura y Despliegue](#infraestructura-y-despliegue)
11. [Riesgos y Consideraciones](#riesgos-y-consideraciones)
12. [Recomendaciones](#recomendaciones)

---

## Resumen Ejecutivo

[Extraer el propósito principal del sistema, tipo de arquitectura identificada, tecnologías principales y recomendaciones clave basadas en el análisis]

**Tipo de Arquitectura:** [Monolítica/Microservicios/SOA/Serverless/etc.]

**Tecnologías Principales:**
- Frontend: [Extraer tecnologías frontend]
- Backend: [Extraer tecnologías backend]
- Base de Datos: [Extraer bases de datos]
- Cloud/Infraestructura: [Extraer información cloud]

**Hallazgos Principales:**
[Listar los 3-5 hallazgos más importantes del análisis]

---

## Arquitectura General

### Visión General
[Describir la arquitectura general del sistema basada en los diagramas y documentación]

### Diagrama de Arquitectura
[Si hay diagramas en la documentación, describir su contenido y estructura]

### Capas del Sistema
[Extraer información sobre las capas: presentación, negocio, datos, etc.]

| **Capa** | **Tecnología** | **Responsabilidad** |
|----------|----------------|-------------------|
| [Extraer capas] | [Extraer tecnologías] | [Extraer responsabilidades] |

---

## Componentes del Sistema

### Componentes Principales
[Extraer componentes identificados en los diagramas y documentación]

| **Componente** | **Función** | **Tecnología** | **Dependencias** |
|----------------|-------------|----------------|------------------|
| [Extraer componentes] | [Extraer funciones] | [Extraer tecnologías] | [Extraer dependencias] |

### Servicios Identificados
[Listar servicios o módulos identificados]

---

## Tecnologías Identificadas

### Stack Tecnológico Completo

**Frontend:**
- [Extraer frameworks y librerías frontend]
- [Extraer herramientas de build]

**Backend:**
- [Extraer lenguajes y frameworks backend]
- [Extraer servidores de aplicación]

**Base de Datos:**
- [Extraer sistemas de base de datos]
- [Extraer sistemas de cache]

**DevOps y Herramientas:**
- [Extraer herramientas CI/CD]
- [Extraer contenedores y orquestación]

**Monitoreo:**
- [Extraer herramientas de monitoreo]
- [Extraer sistemas de logging]

---

## Patrones Arquitectónicos

### Patrones Identificados
[Identificar patrones arquitectónicos utilizados]

| **Patrón** | **Aplicación** | **Beneficio** | **Riesgo** |
|------------|----------------|---------------|------------|
| [Extraer patrones] | [Extraer donde se aplican] | [Extraer beneficios] | [Identificar riesgos] |

### Principios de Diseño
[Extraer principios de diseño evidentes en la arquitectura]

---

## Integraciones y APIs

### APIs Internas
[Extraer información sobre APIs internas del sistema]

| **API** | **Protocolo** | **Propósito** | **Seguridad** |
|---------|---------------|---------------|---------------|
| [Extraer APIs] | [REST/GraphQL/gRPC] | [Extraer propósitos] | [Extraer seguridad] |

### Integraciones Externas
[Extraer sistemas externos con los que se integra]

| **Sistema Externo** | **Protocolo** | **Tipo de Integración** | **Datos Intercambiados** |
|-------------------|---------------|------------------------|-------------------------|
| [Extraer sistemas] | [Extraer protocolos] | [Extraer tipos] | [Extraer datos] |

### Comunicación entre Servicios
[Describir cómo se comunican los servicios entre sí]

---

## Gestión de Datos

### Modelo de Datos
[Extraer información sobre el modelo de datos]

**Entidades Principales:**
[Listar entidades principales identificadas]

### Almacenamiento
[Describir estrategias de almacenamiento]

| **Tipo de Dato** | **Sistema de Almacenamiento** | **Justificación** |
|------------------|-------------------------------|-------------------|
| [Extraer tipos] | [Extraer sistemas] | [Extraer justificaciones] |

### Flujo de Datos
[Describir cómo fluyen los datos en el sistema]

---

## Seguridad

### Medidas de Seguridad Identificadas
[Extraer medidas de seguridad del análisis]

**Autenticación:**
- [Extraer métodos de autenticación]

**Autorización:**
- [Extraer métodos de autorización]

**Protección de Datos:**
- [Extraer medidas de protección]

**Seguridad en Comunicaciones:**
- [Extraer protocolos seguros]

### Vulnerabilidades Potenciales
[Identificar posibles vulnerabilidades basadas en el análisis]

---

## Escalabilidad y Rendimiento

### Estrategias de Escalabilidad
[Extraer estrategias de escalabilidad identificadas]

**Escalabilidad Horizontal:**
[Describir capacidades de escalado horizontal]

**Escalabilidad Vertical:**
[Describir capacidades de escalado vertical]

### Optimizaciones de Rendimiento
[Extraer optimizaciones identificadas]

| **Área** | **Optimización** | **Impacto Esperado** |
|----------|------------------|---------------------|
| [Extraer áreas] | [Extraer optimizaciones] | [Extraer impactos] |

---

## Infraestructura y Despliegue

### Arquitectura de Infraestructura
[Extraer información sobre infraestructura]

**Componentes de Infraestructura:**
- [Extraer servidores, balanceadores, etc.]

**Servicios en la Nube:**
- [Extraer servicios cloud utilizados]

### Estrategia de Despliegue
[Extraer información sobre despliegue]

**Ambientes:**
| **Ambiente** | **Propósito** | **Configuración** |
|--------------|---------------|-------------------|
| [Extraer ambientes] | [Extraer propósitos] | [Extraer configuraciones] |

**Pipeline de CI/CD:**
[Describir pipeline de despliegue si está documentado]

---

## Riesgos y Consideraciones

### Riesgos Técnicos Identificados
[Identificar riesgos técnicos del análisis]

| **Riesgo** | **Probabilidad** | **Impacto** | **Mitigación Sugerida** |
|------------|------------------|-------------|-------------------------|
| [Extraer riesgos] | [Evaluar probabilidad] | [Evaluar impacto] | [Sugerir mitigación] |

### Puntos de Fallo
[Identificar puntos únicos de fallo]

### Deuda Técnica
[Identificar posible deuda técnica]

---

## Recomendaciones

### Mejoras Arquitectónicas Prioritarias

1. **[Recomendación 1]:** [Descripción detallada basada en el análisis]
2. **[Recomendación 2]:** [Descripción detallada basada en el análisis]  
3. **[Recomendación 3]:** [Descripción detallada basada en el análisis]

### Optimizaciones Sugeridas

**Rendimiento:**
- [Sugerencia basada en análisis]

**Seguridad:**
- [Sugerencia basada en análisis]

**Mantenibilidad:**
- [Sugerencia basada en análisis]

### Próximos Pasos

**Inmediatos (1-3 meses):**
- [Acción específica basada en hallazgos]

**Mediano Plazo (3-6 meses):**
- [Acción específica basada en hallazgos]

**Largo Plazo (6+ meses):**
- [Acción específica basada en hallazgos]

---

## Anexos

### Información Técnica Adicional
[Incluir detalles técnicos relevantes extraídos del análisis]

### Glosario de Términos
[Definir términos técnicos utilizados en el análisis]

---

**Notas del Análisis:**
- **Fuentes:** [Listar documentos y diagramas analizados]
- **Limitaciones:** [Mencionar limitaciones del análisis]
- **Supuestos:** [Listar supuestos realizados]

---

**REGLAS PARA EL ANÁLISIS:**
- Extrae TODA la información explícita de los documentos
- Identifica patrones implícitos en diagramas y descripciones
- Mantén terminología técnica precisa
- Para información faltante, especifica qué se necesita investigar
- Prioriza recomendaciones basadas en mejores prácticas de la industria
- Asegúrate de que el análisis sea accionable y específico

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
        return f"Error generando análisis de arquitectura: {str(e)}"