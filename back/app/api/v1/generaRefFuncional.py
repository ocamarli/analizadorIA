from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import io
import PyPDF2
from langchain_community.chat_models import AzureChatOpenAI
from langchain.prompts import PromptTemplate

# Blueprint
refinamiento_bp = Blueprint('refinamiento_requerimientos_funcionales', __name__)

# Configuración de LangChain
llm = AzureChatOpenAI(
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4"),
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15"),
    openai_api_key=os.getenv("AZURE_OPENAI_API_KEY", "6076ii7OpLiuTEKYsEVvWyt57RYjzb8d4hDwZRqKuokBi1WTuKZ9JQQJ99AJACYeBjFXJ3w3AAABACOGfwuS"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://openaidemobside.openai.azure.com"),
    temperature=0.3  # Menor temperatura para más precisión en refinamiento
)

@refinamiento_bp.route('/refinamiento-funcional', methods=['POST'])
def refinamiento_funcional():
    try:
        # Obtener archivos y texto adicional
        files = request.files.getlist('files') if 'files' in request.files else []
        additional_text = request.form.get('additional_text', '').strip()
        version_actual = request.form.get('version_actual', '1.0').strip()
        
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
            else:
                # Solo validar tipo si hay archivos
                if files and any(f.filename for f in files):
                    return jsonify({"error": f"Tipo de archivo no soportado: {file.filename}"}), 400
        
        # Agregar texto adicional si existe
        if additional_text:
            if texto_completo:
                texto_completo += "\n=== INFORMACIÓN ADICIONAL PARA REFINAMIENTO ===\n"
            texto_completo += additional_text + "\n\n"
        
        # Validar que se haya extraído algún contenido
        if not texto_completo.strip():
            return jsonify({"error": "No se pudo extraer texto de los archivos y no se proporcionó texto adicional"}), 400
        
        # Generar refinamiento con IA
        respuesta_ia = generar_refinamiento_con_ia(texto_completo, version_actual)
        
        return jsonify({
            "success": True,
            "respuesta": respuesta_ia,
            "archivos_procesados": archivos_procesados,
            "texto_adicional_incluido": bool(additional_text),
            "version_actual": version_actual
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

def generar_refinamiento_con_ia(texto_documento, version_actual):
    """Genera un documento de refinamiento funcional basado en la versión actual"""
    
    fecha_actual = datetime.now().strftime('%d/%m/%Y')
    nueva_version = f"{float(version_actual) + 0.1:.1f}"
    
    prompt_template = PromptTemplate(
        input_variables=["documento", "fecha", "version_actual", "nueva_version"],
        template="""
Eres un analista de sistemas experto en refinamiento de requerimientos funcionales. Tu tarea es analizar el documento proporcionado (que contiene una versión actual de requerimientos) y generar un documento de refinamiento funcional que:

1. Identifique ambigüedades o inconsistencias en los requerimientos actuales
2. Proponga mejoras específicas
3. Sugiera requerimientos adicionales basados en el análisis
4. Actualice la versión del documento

DOCUMENTO ACTUAL A ANALIZAR:
{documento}

INSTRUCCIONES IMPORTANTES:
1. Analiza críticamente cada sección del documento actual
2. Identifica puntos que necesitan clarificación o mayor detalle
3. Propone mejoras concretas marcadas como "PROPUESTA DE REFINAMIENTO"
4. Mantén lo que ya está bien definido
5. Sugiere nuevos requerimientos solo si son evidentemente necesarios

FORMATO DEL DOCUMENTO DE REFINAMIENTO:

# DOCUMENTO DE REFINAMIENTO FUNCIONAL

## INFORMACIÓN BÁSICA
- **Versión Actual:** {version_actual}
- **Nueva Versión Propuesta:** {nueva_version}
- **Fecha de Refinamiento:** {fecha}
- **Responsable de Refinamiento:** Sistema Automatizado de Análisis

## ANÁLISIS POR SECCIÓN

### 1. INFORMACIÓN GENERAL DEL PROYECTO
[Identificar si falta claridad en objetivos generales o stakeholders clave]

### 2. ALCANCE DEL PROYECTO
**Hallazgos:**
- [Listar ambigüedades encontradas en el alcance actual]
- [Identificar posibles scope creeps o omisiones]

**Propuestas:**
- [PROPUESTA DE REFINAMIENTO]: [Descripción clara de la mejora sugerida]

### 3. REQUERIMIENTOS FUNCIONALES
**Análisis Crítico:**
- [Listar requerimientos ambiguos o poco medibles]
- [Identificar dependencias no documentadas]
- [Señalar criterios de aceptación faltantes]

**Mejoras Propuestas:**
- [PROPUESTA DE REFINAMIENTO para RF-XXX]: [Descripción detallada de la mejora]
- [NUEVO RF-YYY SUGERIDO]: [Descripción del nuevo requerimiento si aplica]

### 4. REGLAS DE NEGOCIO
[Identificar reglas contradictorias o incompletas]

### 5. CRITERIOS DE ÉXITO
[Evaluar si los criterios son medibles y realistas]

## RESUMEN DE CAMBIOS PROPUESTOS
| Sección | Tipo de Cambio | Descripción | Justificación |
|---------|----------------|-------------|---------------|
| [Ej: Alcance] | Clarificación | [Descripción] | [Razón del cambio] |
| [Ej: RF-001] | Modificación | [Detalle] | [Beneficio esperado] |

## RECOMENDACIONES PARA LA SIGUIENTE ITERACIÓN
1. [Prioridad 1]: [Acción recomendada]
2. [Prioridad 2]: [Acción recomendada]
3. [Prioridad 3]: [Acción recomendada]

**Nota:** Este documento debe ser revisado y validado por los stakeholders clave antes de actualizar la versión oficial.
"""
    )
    
    try:
        chain = prompt_template | llm
        resultado = chain.invoke({
            "documento": texto_documento,
            "fecha": fecha_actual,
            "version_actual": version_actual,
            "nueva_version": nueva_version
        })
        
        return resultado.content if hasattr(resultado, 'content') else str(resultado)
        
    except Exception as e:
        return f"Error generando documento de refinamiento: {str(e)}"