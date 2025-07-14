from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import io
import PyPDF2
from langchain_community.chat_models import AzureChatOpenAI
from langchain.prompts import PromptTemplate

# Blueprint
refinamientoNoFuncional_bp = Blueprint('refinamientoNoFuncional', __name__)

# Configuración de LangChain
llm = AzureChatOpenAI(
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4"),
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15"),
    openai_api_key=os.getenv("AZURE_OPENAI_API_KEY", "6076ii7OpLiuTEKYsEVvWyt57RYjzb8d4hDwZRqKuokBi1WTuKZ9JQQJ99AJACYeBjFXJ3w3AAABACOGfwuS"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://openaidemobside.openai.azure.com"),
    temperature=0.3  # Menor temperatura para más precisión en refinamiento
)



@refinamientoNoFuncional_bp.route('/refinamiento-no-funcional', methods=['POST'])
def refinamiento_no_funcional():
    try:
        # Obtener archivos y texto adicional
        files = request.files.getlist('files') if 'files' in request.files else []
        additional_text = request.form.get('additional_text', '').strip()
        version_actual = request.form.get('version_actual', '1.0').strip()
        contexto_operacional = request.form.get('contexto_operacional', '').strip()  # Ej: "Entorno médico regulado HIPAA"
        
        # Validación básica
        if not files and not additional_text:
            return jsonify({"error": "Se requieren archivos o texto con los RNF actuales"}), 400

        # Procesamiento de archivos
        texto_completo = ""
        archivos_procesados = 0
        
        for file in files:
            if not file.filename:
                continue
                
            try:
                if file.filename.lower().endswith('.pdf'):
                    texto_archivo = extraer_texto_pdf(file)
                elif file.filename.lower().endswith(('.md', '.txt', '.yaml', '.json')):
                    file.seek(0)
                    texto_archivo = file.read().decode('utf-8')
                else:
                    continue
                    
                if texto_archivo.strip():
                    texto_completo += f"=== CONTENIDO DE {file.filename} ===\n{texto_archivo}\n\n"
                    archivos_procesados += 1
            except Exception as e:
                print(f"Error procesando {file.filename}: {str(e)}")
                continue

        # Combinar con texto adicional
        if additional_text:
            texto_completo += f"\n=== ENTRADA ADICIONAL ===\n{additional_text}\n\n"

        if not texto_completo.strip():
            return jsonify({"error": "No se extrajo contenido válido para análisis"}), 400

        # Generar refinamiento
        respuesta_ia = generar_refinamiento_rnf_ia(
            texto_documento=texto_completo,
            version_actual=version_actual,
            contexto_operacional=contexto_operacional
        )

        return jsonify({
            "success": True,
            "refinamiento": respuesta_ia,
            "metadata": {
                "archivos_procesados": archivos_procesados,
                "version_anterior": version_actual,
                "contexto_considerado": bool(contexto_operacional)
            }
        })

    except Exception as e:
        print(f"Error en refinamiento RNF: {str(e)}")
        return jsonify({"error": f"Fallo en el análisis no funcional: {str(e)}"}), 500

def generar_refinamiento_rnf_ia(texto_documento, version_actual, contexto_operacional):
    """Genera un refinamiento especializado para requerimientos no funcionales"""
    
    fecha_actual = datetime.now().strftime('%Y-%m-%d')
    nueva_version = f"{float(version_actual) + 0.1:.1f}"

    prompt_template = PromptTemplate(
        input_variables=["documento", "fecha", "version_actual", "nueva_version", "contexto_operacional"],
        template="""
Eres un experto en ingeniería de requisitos no funcionales (RNF) con especialización en calidad de sistemas. 
Analiza el siguiente documento y genera un refinamiento técnico-profesional de los atributos de calidad.

CONTEXTO OPERACIONAL: {contexto_operacional or 'No especificado'}
DOCUMENTO ACTUAL:
{documento}

INSTRUCCIONES:
1. Enfócate exclusivamente en aspectos NO funcionales
2. Evalúa la completitud y medibilidad de los RNF
3. Propone mejoras basadas en estándares ISO 25010
4. Considera el contexto operacional proporcionado
5. Sé específico con métricas y criterios verificables

FORMATO DE SALIDA:

# REFINAMIENTO DE REQUERIMIENTOS NO FUNCIONALES

## METADATOS
- **Versión analizada**: {version_actual}
- **Versión propuesta**: {nueva_version}
- **Fecha análisis**: {fecha}
- **Contexto operacional**: {contexto_operacional or 'Por especificar'}

## EVALUACIÓN POR CATEGORÍA (ISO 25010)

### 1. DESEMPEÑO
**Estado Actual:**
- [Evaluación de métricas existentes: throughput, latencia, etc.]
- [Problemas identificados]

**Recomendaciones:**
- [RNF-PERF-001]: [Propuesta específica con métricas]
  - Ej: "El sistema debe soportar 1000 transacciones/min con latencia <2s en percentil 95"

### 2. SEGURIDAD
**Hallazgos:**
- [Gaps de seguridad identificados]
- [Cumplimiento normativo]

**Mejoras:**
- [RNF-SEC-001]: [Control de seguridad mejorado]
  - Ej: "Autenticación multifactor obligatoria para acceso a datos sensibles"

### 3. COMPATIBILIDAD
**Análisis:**
- [Interoperabilidad requerida]
- [Dependencias críticas]

### 4. USABILIDAD
**Evaluación:**
- [Cumplimiento de heurísticas]
- [Accesibilidad]

### 5. FIABILIDAD
**Propuestas:**
- [RNF-REL-001]: [Objetivos de disponibilidad]
  - Ej: "SLA de 99.99% para componentes críticos"

### 6. MANTENIBILIDAD
**Recomendaciones:**
- [RNF-MNT-001]: [Estándares de documentación]
  - Ej: "Documentación técnica actualizada automáticamente en cada release"

### 7. PORTABILIDAD
**Consideraciones:**
- [Requerimientos de despliegue]
- [Dependencias de infraestructura]

## MATRIZ DE TRAZABILIDAD
| ID RNF | Tipo | Métrica Objetivo | Técnica de Verificación | Prioridad |
|--------|------|------------------|-------------------------|-----------|
| [Ej: RNF-PERF-001] | Rendimiento | 1000 tpm | Test de carga | Alta |

## PLAN DE VALIDACIÓN
1. **Pruebas de estrés**: [Requisitos y herramientas]
2. **Auditoría de seguridad**: [Alcance y frecuencia]
3. **Monitoreo continuo**: [Métricas clave]

**Nota Técnica:**
Los RNF propuestos deben cumplir con el principio SMART (Específicos, Medibles, Alcanzables, Relevantes, Temporales).
Priorizar según impacto en la calidad percibida por el usuario final.
"""
    )

    try:
        chain = prompt_template | llm
        resultado = chain.invoke({
            "documento": texto_documento,
            "fecha": fecha_actual,
            "version_actual": version_actual,
            "nueva_version": nueva_version,
            "contexto_operacional": contexto_operacional
        })
        
        return resultado.content if hasattr(resultado, 'content') else str(resultado)
        
    except Exception as e:
        return f"Error generando refinamiento RNF: {str(e)}"