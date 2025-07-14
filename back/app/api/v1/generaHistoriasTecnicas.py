from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import io
import PyPDF2
from langchain_community.chat_models import AzureChatOpenAI
from langchain.prompts import PromptTemplate

# Blueprint
genera_historias_tecnicas_bp = Blueprint('generador_historias_tecnicas', __name__)

# Configuración de LangChain
llm = AzureChatOpenAI(
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4"),
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15"),
    openai_api_key=os.getenv("AZURE_OPENAI_API_KEY", "6076ii7OpLiuTEKYsEVvWyt57RYjzb8d4hDwZRqKuokBi1WTuKZ9JQQJ99AJACYeBjFXJ3w3AAABACOGfwuS"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://openaidemobside.openai.azure.com"),
    temperature=0.7
)

@genera_historias_tecnicas_bp.route('/generar-historias-tecnicas', methods=['POST'])
def generar_historias_tecnicas():
    try:
        # Obtener archivos y texto adicionala
        files = request.files.getlist('files') if 'files' in request.files else []
        additional_text = request.form.get('additional_text', '').strip()
        
        # Validar que haya al menos archivos o texto adicional
        if not files and not additional_text:
            return jsonify({"error": "Debe proporcionar al menos archivos o información técnica adicional"}), 400
        
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
            else:
                # Solo validar tipo si hay archivos
                if files and any(f.filename for f in files):
                    return jsonify({"error": f"Tipo de archivo no soportado: {file.filename}"}), 400
        
        # Agregar texto adicional si existe
        if additional_text:
            if texto_completo:
                texto_completo += "\n=== INFORMACIÓN TÉCNICA ADICIONAL ===\n"
            texto_completo += additional_text + "\n\n"
        
        # Validar que se haya extraído algún contenido
        if not texto_completo.strip():
            return jsonify({"error": "No se pudo extraer texto de los archivos y no se proporcionó información técnica adicional"}), 400
        
        # Generar historias técnicas con IA
        respuesta_ia = generar_con_ia(texto_completo)
        
        return jsonify({
            "success": True,
            "respuesta": respuesta_ia,
            "archivos_procesados": archivos_procesados,
            "informacion_tecnica_adicional": bool(additional_text)
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": f"Error procesando archivos: {str(e)}"}), 500
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


def generar_con_ia(texto_documento):
    """Genera historias técnicas usando IA con validación de información requerida"""
    
    prompt_template = PromptTemplate(
        input_variables=["documento"],
        template="""
Eres un analista técnico experto. Tu tarea es analizar el documento proporcionado y determinar si contiene la información suficiente para generar historias técnicas de calidad.

DOCUMENTO A ANALIZAR:
{documento}

INSTRUCCIONES:
1. Primero, evalúa si el documento contiene información suficiente para generar buenas historias técnicas
2. Busca específicamente:
   - Historias de usuario o requerimientos funcionales claros
   - Descripción de funcionalidades
   - Criterios de aceptación o especificaciones
   - Contexto del proyecto o dominio

SI EL DOCUMENTO TIENE INFORMACIÓN SUFICIENTE:
Genera historias técnicas completas usando el siguiente formato en Markdown:

# HISTORIAS TÉCNICAS

## Historia Técnica [Número]: [Título]

### Historia de Usuario Original
[Copia aquí la historia funcional original del documento]

### Descripción Técnica
[Descripción detallada de la implementación técnica]

### Criterios de Aceptación Técnicos
- [Criterio técnico 1]
- [Criterio técnico 2]
- [Criterio técnico 3]

### Diseño e Implementación
[Detalles específicos sobre cómo implementar]

### Tareas de Desarrollo
1. [Tarea específica 1]
2. [Tarea específica 2]
3. [Tarea específica 3]

### Consideraciones Técnicas
- [Consideración 1]
- [Consideración 2]

### Pruebas Requeridas
- [Tipo de prueba 1]
- [Tipo de prueba 2]

---

SI EL DOCUMENTO NO TIENE INFORMACIÓN SUFICIENTE:
Responde con el siguiente formato:

# INFORMACIÓN REQUERIDA INSUFICIENTE

## Análisis del Documento
El documento proporcionado no contiene la información suficiente para generar historias técnicas de calidad.

## Información Faltante Detectada:
[Lista específica de qué información falta]

## Sugerencias para Mejorar el Documento:

### 1. Historias de Usuario Claras
- Incluir historias en formato: "Como [usuario], quiero [funcionalidad] para [beneficio]"
- Especificar roles de usuario claramente
- Definir el valor de negocio de cada funcionalidad

### 2. Criterios de Aceptación Detallados
- Agregar condiciones específicas de cumplimiento
- Incluir escenarios de éxito y fallo
- Definir validaciones y restricciones

### 3. Contexto del Proyecto
- Describir el dominio del negocio
- Especificar el tipo de aplicación (web, móvil, etc.)
- Incluir restricciones técnicas conocidas

### 4. Especificaciones Funcionales
- Detallar flujos de trabajo
- Describir integraciones necesarias
- Especificar reglas de negocio

### 5. Información Técnica Adicional
- Mencionar tecnologías preferidas o restricciones
- Incluir consideraciones de rendimiento
- Especificar requisitos de seguridad

## Recomendación:
Para obtener historias técnicas de calidad, por favor proporcione un documento que incluya al menos:
- Historias de usuario bien definidas
- Criterios de aceptación específicos
- Contexto del proyecto y dominio de negocio
- Especificaciones funcionales claras

IMPORTANTE:
- Usa únicamente términos en español
- Sé específico en tu análisis
- Mantén el formato Markdown exacto
- No agregues texto adicional fuera del formato especificado
"""
    )
    
    try:
        chain = prompt_template | llm
        resultado = chain.invoke({
            "documento": texto_documento
        })
        
        return resultado.content if hasattr(resultado, 'content') else str(resultado)
        
    except Exception as e:
        return f"Error generando historias técnicas: {str(e)}"