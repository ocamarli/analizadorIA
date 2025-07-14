from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import io
import PyPDF2
from langchain_community.chat_models import AzureChatOpenAI
from langchain.prompts import PromptTemplate

# Blueprint
refinamientoTecnico_bp = Blueprint('refinamientoTecnico', __name__)

# Configuración de LangChain
llm = AzureChatOpenAI(
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4"),
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15"),
    openai_api_key=os.getenv("AZURE_OPENAI_API_KEY", "6076ii7OpLiuTEKYsEVvWyt57RYjzb8d4hDwZRqKuokBi1WTuKZ9JQQJ99AJACYeBjFXJ3w3AAABACOGfwuS"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://openaidemobside.openai.azure.com"),
    temperature=0.3  # Menor temperatura para más precisión en refinamiento
)


@refinamientoTecnico_bp.route('/refinamiento-tecnico', methods=['POST'])
def refinamiento_tecnico():
    try:
        # Obtener archivos y texto adicional
        files = request.files.getlist('files') if 'files' in request.files else []
        additional_text = request.form.get('additional_text', '').strip()
        version_actual = request.form.get('version_actual', '1.0').strip()
        stack_tecnico = request.form.get('stack_tecnico', '').strip()  # Opcional: stack tecnológico actual
        
        # Validar que haya al menos archivos o texto adicional
        if not files and not additional_text:
            return jsonify({"error": "Debe proporcionar al menos archivos o texto adicional"}), 400
        
        # Extraer texto de todos los archivos
        texto_completo = ""
        archivos_procesados = 0
        
        for file in files:
            if file.filename == '':
                continue
                     
            if file.filename.lower().endswith('.pdf'):
                texto_archivo = extraer_texto_pdf(file)
                if texto_archivo.strip():
                    texto_completo += texto_archivo + "\n\n"
                    archivos_procesados += 1
            elif file.filename.lower().endswith(('.md', '.markdown', '.txt')):
                file.seek(0)
                texto_archivo = file.read().decode('utf-8')
                if texto_archivo.strip():
                    texto_completo += texto_archivo + "\n\n"
                    archivos_procesados += 1
            else:
                if files and any(f.filename for f in files):
                    return jsonify({"error": f"Tipo de archivo no soportado: {file.filename}"}), 400
        
        # Agregar texto adicional si existe
        if additional_text:
            if texto_completo:
                texto_completo += "\n=== INFORMACIÓN TÉCNICA ADICIONAL ===\n"
            texto_completo += additional_text + "\n\n"
        
        # Validar contenido
        if not texto_completo.strip():
            return jsonify({"error": "No se pudo extraer texto válido para análisis técnico"}), 400
        
        # Generar refinamiento técnico con IA
        respuesta_ia = generar_refinamiento_tecnico_ia(texto_completo, version_actual, stack_tecnico)
        
        return jsonify({
            "success": True,
            "respuesta": respuesta_ia,
            "archivos_procesados": archivos_procesados,
            "texto_adicional_incluido": bool(additional_text),
            "version_actual": version_actual,
            "stack_tecnico_considerado": bool(stack_tecnico)
        })
        
    except Exception as e:
        print(f"Error en refinamiento técnico: {str(e)}")
        return jsonify({"error": f"Error en análisis técnico: {str(e)}"}), 500

def generar_refinamiento_tecnico_ia(texto_documento, version_actual, stack_tecnico):
    """Genera un documento de refinamiento técnico especializado"""
    
    fecha_actual = datetime.now().strftime('%d/%m/%Y')
    nueva_version = f"{float(version_actual) + 0.1:.1f}"
    
    prompt_template = PromptTemplate(
        input_variables=["documento", "fecha", "version_actual", "nueva_version", "stack_tecnico"],
        template="""
Eres un arquitecto de software experto en refinamiento técnico. Analiza el documento proporcionado y genera un informe de refinamiento técnico enfocado en:

1. Optimización de arquitectura
2. Mejoras de implementación
3. Consideraciones técnicas críticas
4. Riesgos tecnológicos

DOCUMENTO ACTUAL:
{documento}

STACK TECNOLÓGICO ACTUAL: {stack_tecnico or 'No especificado'}

INSTRUCCIONES:
1. Enfócate exclusivamente en aspectos técnicos
2. Evalúa la coherencia técnica de los requerimientos
3. Identifica posibles problemas de implementación
4. Propone alternativas técnicas mejoradas
5. Considera escalabilidad, seguridad y mantenibilidad

FORMATO DE SALIDA:

# INFORME DE REFINAMIENTO TÉCNICO

## DATOS BÁSICOS
- Versión Analizada: {version_actual}
- Nueva Versión Propuesta: {nueva_version}
- Fecha de Análisis: {fecha}
- Stack Tecnológico: {stack_tecnico or 'Por definir'}

## ANÁLISIS TÉCNICO DETALLADO

### 1. ARQUITECTURA DEL SISTEMA
**Hallazgos Actuales:**
- [Patrones arquitectónicos identificados o faltantes]
- [Posibles cuellos de botella]
- [Componentes críticos no documentados]

**Recomendaciones:**
- [PROPUESTA TÉCNICA]: [Mejora específica con justificación]
- [ALTERNATIVA ARQUITECTÓNICA]: [Opciones técnicas viables]

### 2. TECNOLOGÍAS Y HERRAMIENTAS
**Evaluación:**
- [Tecnologías recomendadas vs. usadas]
- [Herramientas faltantes en el stack]
- [Posibles obsolescencias]

**Propuestas:**
- [ACTUALIZACIÓN TECNOLÓGICA]: [Tecnología/versión sugerida]
- [HERRAMIENTA ADICIONAL]: [Justificación técnica]

### 3. CONSIDERACIONES DE IMPLEMENTACIÓN
**Puntos Críticos:**
- [Interfaces complejas no documentadas]
- [Dependencias externas no consideradas]
- [Requerimientos no implementables]

**Plan de Acción:**
- [PROTOCOLO DE IMPLEMENTACIÓN]: [Pasos técnicos detallados]
- [PRUEBAS TÉCNICAS NECESARIAS]: [Tipos de pruebas recomendadas]

### 4. RIESGOS TECNOLÓGICOS
| Riesgo | Probabilidad | Impacto | Mitigación Propuesta |
|--------|--------------|---------|----------------------|
| [Ej: Compatibilidad] | Alta/Media/Baja | Alto/Medio/Bajo | [Solución técnica] |
| [Ej: Escalabilidad] | [ ] | [ ] | [ ] |

### 5. OPTIMIZACIONES SUGERIDAS
- [ÁREA TÉCNICA]: [Descripción de optimización]
  - Beneficio esperado: [Mejora de performance/costo/etc]
  - Esfuerzo estimado: [Alto/Medio/Bajo]

## CHECKLIST DE VALIDACIÓN TÉCNICA
- [ ] Revisión de patrones de diseño
- [ ] Análisis de seguridad aplicado
- [ ] Evaluación de escalabilidad
- [ ] Plan de despliegue definido

**Nota Técnica:** 
Este documento debe ser revisado por el equipo de arquitectura y desarrollo antes de su implementación.
Las propuestas deben evaluarse considerando el contexto técnico actual del proyecto.
"""
    )
    
    try:
        chain = prompt_template | llm
        resultado = chain.invoke({
            "documento": texto_documento,
            "fecha": fecha_actual,
            "version_actual": version_actual,
            "nueva_version": nueva_version,
            "stack_tecnico": stack_tecnico
        })
        
        return resultado.content if hasattr(resultado, 'content') else str(resultado)
        
    except Exception as e:
        return f"Error generando refinamiento técnico: {str(e)}"