from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import io
import PyPDF2
from langchain_community.chat_models import AzureChatOpenAI
from langchain.prompts import PromptTemplate

# Blueprint
def_bp = Blueprint('generador_def_requerimientos', __name__)

# Configuración de LangChain
llm = AzureChatOpenAI(
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1"),
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
    openai_api_key=os.getenv("AZURE_OPENAI_API_KEY", "6076ii7OpLiuTEKYsEVvWyt57RYjzb8d4hDwZRqKuokBi1WTuKz9JQQJ99AJACYeBjFXJ3w3AAABACOGfwuS"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://openaidemobside.openai.azure.com"),
    temperature=0.7
)

@def_bp.route('/generar-def-requerimientos', methods=['POST'])
@def_bp.route('/generar-def-requerimientos', methods=['POST'])
def generar_def_requerimientos():
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
        
        # Generar documento DEF con IA
        respuesta_ia = generar_def_con_ia(texto_completo)
        
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


def generar_def_con_ia(texto_documento):
    """Genera documento DEF de requerimientos funcionales usando IA con información encontrada y sugerencias para faltante"""
    
    fecha_actual = datetime.now().strftime('%d/%m/%Y')
    
    prompt_template = PromptTemplate(
        input_variables=["documento", "fecha"],
      template="""
Eres un analista de sistemas experto en definición de requerimientos funcionales. Tu tarea es analizar minuciosamente el documento proporcionado y generar un Documento de Especificación Funcional (DEF) extrayendo TODA la información disponible.

DOCUMENTO A ANALIZAR:
{documento}

INSTRUCCIONES CRÍTICAS:
1. LEE COMPLETAMENTE el documento antes de generar el DEF
2. EXTRAE toda la información explícita disponible en el documento
3. IDENTIFICA stakeholders, procesos, roles, responsabilidades mencionados
4. BUSCA información sobre: objetivos, beneficios, restricciones, riesgos, supuestos
5. ENCUENTRA requerimientos funcionales implícitos en los procesos descritos
6. Para información NO disponible, marca como "FALTA DEFINIR" con sugerencias específicas
7. CONSERVA la estructura exacta del formato DEF del documento de referencia

FORMATO EXACTO DEL DOCUMENTO DEF:

![Logo/Header del proyecto]

---

**Documento de Especificación Funcional**

**Proyecto:** [Extraer del documento el nombre del proyecto]

Revisión [Extraer versión o usar 1.0]

**Control de Cambios**

| **Fecha** | **Revisión** | **Autor** | **Comentarios / Cambios** |
|-----------|--------------|-----------|----------------------------|
| {fecha}   | 1.0          | [Extraer del documento] | [Extraer comentarios o usar "Documento inicial generado por análisis automatizado"] |

Documento validado por las partes en fecha: [Fecha]

| Por el cliente | Sistemas |
|----------------|----------|
| Nombre: [Extraer del documento] | Nombre: [Extraer del documento] |

**Contenido**

[**1 Introducción**](#introducción)

> [**1.1 Situación Actual**](#situación-actual)
>
> [**1.2 Situación Deseada**](#situación-deseada)
>
> [**1.3 Datos Generales**](#datos-generales)
>
> [**1.4 Beneficio Esperado**](#beneficio-esperado)
>
> [**1.5 Definiciones, acrónimos y abreviaturas**](#definiciones-acrónimos-y-abreviaturas)
>
> [**1.6 Referencias**](#referencias)

[**2 Descripción general**](#descripción-general)

> [**2.1 Alcance**](#alcance)
>
> [**2.2 Personal involucrado**](#personal-involucrado)
>
> [**2.2.1 Matriz de Escalación**](#matriz-de-escalación)
>
> [**2.3 Perspectiva del producto**](#perspectiva-del-producto)
>
> [**2.4 Mapa de Impacto / Dependencias**](#mapa-de-impacto-dependencias)
>
> [**2.5 Fuera de alcance**](#fuera-de-alcance)
>
> [**2.6 Funcionalidad del producto**](#funcionalidad-del-producto)
>
> [**2.7 Reglas de negocio definidas o a impactar**](#reglas-de-negocio-definidas-o-a-impactar)
>
> [**2.8 Requisitos no funcionales**](#requisitos-no-funcionales)
>
> [**2.8.1 Requisitos de rendimiento**](#requisitos-de-rendimiento)
>
> [**2.8.2 Seguridad**](#seguridad)
>
> [**2.8.3 Disponibilidad**](#disponibilidad)
>
> [**2.8.4 Manejo de Errores y Excepciones**](#manejo-de-errores-y-excepciones)
>
> [**2.9 Restricciones**](#restricciones)
>
> [**2.10 Supuestos**](#supuestos)
>
> [**2.11 Riesgos**](#riesgos)
>
> [**2.12 Evolución previsible del sistema**](#evolución-previsible-del-sistema)
>
> [**2.13 Decisiones impactadas con los cambios solicitados**](#decisiones-impactadas-con-los-cambios-solicitados)
>
> [**2.14 Estrategia de liberación**](#estrategia-de-liberación)

# **Introducción**

[Extraer de secciones como "Introducción", "Descripción del proyecto", crear introducción basada en la información del documento. Describir el sistema, su propósito y contexto general]

## **Situación Actual**

[Extraer de secciones "Situación Actual", "AS-IS", "Problemática actual", procesos manuales descritos, sistemas legados mencionados. Describir el estado actual del proceso/sistema antes de la implementación]

## **Situación Deseada**

[Extraer de secciones "Situación Deseada", "TO-BE", "Objetivos", "Visión". Describir el estado objetivo después de la implementación]

## **Datos Generales**

| **Campo** | **Valor** |
|-----------|-----------|
| **Nombre del Solicitante** | [Extraer del documento] |
| **Número de Empleado del Solicitante** | [Extraer del documento] |
| **Nombre de la Iniciativa / Producto / Cambio** | [Extraer del documento] |
| **Área de Negocio Solicitante** | [Extraer del documento] |
| **Proceso de Negocio a Modificar** | [Extraer del documento] |
| **Área Dueña del Proceso de Negocio a Modificar** | [Extraer del documento] |
| **Nombre del Patrocinador del Proyecto** | [Extraer del documento] |

## **Beneficio Esperado**

[Extraer de sección "Beneficio Esperado", "ROI", "Valor del negocio". Incluir:]

**¿De qué manera mejorará la vida de nuestros Clientes?**

[Extraer del documento]

**¿Qué problema resolverá la solución?**

[Extraer del documento]

**¿Cómo evaluará que la solución le genera el resultado deseado?**

[Extraer del documento]

**¿Que beneficios o afectaciones por gasto acompañarán la implementación de tu proyecto?**

[Extraer del documento]

### **Análisis Económico (si está disponible)**

**Inversión Inicial**

| **Inversión** | **¿Por qué se estarían gastando en estos conceptos previos a la implementación?** | **Cálculo de los Importes** | **$ Con Proyecto '000** |
|---------------|-----------------------------------------------------------------------------------|----------------------------|-------------------------|
| [Extraer conceptos de inversión del documento] | [Extraer justificación] | [Extraer cálculos] | [Extraer montos] |

**Ingresos Por Proyecto**

| **Diferencial en Ingresos Anuales Esperado** | **¿De qué manera el proyecto ayuda a la mejora en ingresos?** | **Cálculo de los importes** | **$Sin Proyecto '000** | **$Con Proyecto '000** |
|-----------------------------------------------|---------------------------------------------------------------|----------------------------|------------------------|------------------------|
| [Extraer información económica del documento] | [Extraer justificación] | [Extraer cálculos] | [Extraer montos] | [Extraer montos] |

**Afectación por Gasto**

| **Diferencial en Gasto Anuales Esperado** | **¿De qué manera el proyecto ayuda a la disminución del gasto?** | **Cálculo de los importes** | **$Sin Proyecto '000** | **$Con Proyecto '000** |
|--------------------------------------------|------------------------------------------------------------------|----------------------------|------------------------|------------------------|
| [Extraer información de reducción de gastos] | [Extraer justificación] | [Extraer cálculos] | [Extraer montos] | [Extraer montos] |

**Otros Beneficios**

[Extraer beneficios intangibles o adicionales mencionados en el documento]

## **Definiciones, acrónimos y abreviaturas**

| **Término** | **Significado** |
|-------------|-----------------|
| [Extraer términos del documento] | [Extraer definiciones] |

## **Referencias**

| **Título** | **Ruta** | **Fecha** | **Autor** |
|------------|----------|-----------|-----------|
| [Extraer referencias del documento] | [Extraer rutas] | [Extraer fechas] | [Extraer autores] |

# **Descripción general**

## **Alcance**

[Extraer de sección "Alcance", listar los componentes/módulos incluidos en el proyecto]

- [Componente 1: Extraer del documento]
- [Componente 2: Extraer del documento]
- [Componente N: Extraer del documento]

## **Personal involucrado**

| **Nombre** | **Área** | **Posición** | **Rol** | **Info. Contacto (email)** |
|------------|----------|--------------|---------|----------------------------|
| [Extraer nombres del documento] | [Extraer áreas] | [Extraer posiciones] | [Extraer roles] | [Extraer emails] |

## **Matriz de Escalación**

| **Nombre** | **Área** | **Capa** | **Posición** | **Info. Contacto (Cel/Email)** | **Nivel de Escalación** |
|------------|----------|----------|--------------|-------------------------------|-------------------------|
| [Extraer información de escalación del documento] | [Extraer datos] | [Extraer datos] | [Extraer datos] | [Extraer contactos] | [Extraer niveles] |

## **Perspectiva del producto**

[Extraer descripción de la perspectiva del producto, diagramas de contexto si están disponibles]

[Si hay diagramas, describirlos o referenciarlos]

## **Mapa de Impacto / Dependencias**

[Extraer información de dependencias, impact mapping si está disponible]

**Impact Mapping**

| **Objetivo** | **¿A quién Impacta?** | **¿Cómo Impacta?** | **Acciones** |
|--------------|----------------------|-------------------|--------------|
| [Extraer objetivos del documento] | [Extraer stakeholders afectados] | [Extraer tipos de impacto] | [Extraer acciones específicas] |

## **Fuera de alcance**

[Extraer de sección "Fuera de alcance", "Exclusiones", listar lo que NO está incluido]

- [Exclusión 1: Extraer del documento]
- [Exclusión 2: Extraer del documento]

## **Funcionalidad del producto**

[Extraer funcionalidades principales del documento, épicas, features, historias de usuario]

| **EPICA** | **FEATURE** | **HU** |
|-----------|-------------|--------|
| [Extraer épicas del documento] | [Extraer features] | [Extraer historias de usuario] |

**Descripción de Funcionalidades:**

[Extraer descripciones detalladas de las funcionalidades principales]

**Criterios de éxito para el entregable después del cambio:**

[Extraer criterios de éxito específicos mencionados en el documento]

## **Reglas de negocio definidas o a impactar**

[Extraer reglas de negocio específicas del documento]

- [Regla 1: Extraer del documento]
- [Regla 2: Extraer del documento]

## **Requisitos no funcionales**

## **Requisitos de rendimiento**

[Extraer información sobre volúmenes, tiempos de respuesta, capacidad]

## **Seguridad**

[Extraer requisitos de seguridad, autenticación, autorización]

## **Disponibilidad**

[Extraer requisitos de disponibilidad, horarios de operación]

## **Manejo de Errores y Excepciones**

[Extraer información sobre manejo de errores, mensajes específicos]

- Mensajes en modales:
  - [Extraer mensajes específicos del documento]

- Mensajes de error:
  - [Extraer mensajes de error específicos]

- Mensajes informativos:
  - [Extraer mensajes informativos específicos]

## **Restricciones**

[Extraer restricciones técnicas, de negocio, limitaciones]

- [Restricción 1: Extraer del documento]
- [Restricción 2: Extraer del documento]

## **Supuestos**

[Extraer supuestos del proyecto, condiciones asumidas]

- [Supuesto 1: Extraer del documento]
- [Supuesto 2: Extraer del documento]

## **Riesgos**

[Extraer riesgos identificados en el documento]

- [Riesgo 1: Extraer del documento]
- [Riesgo 2: Extraer del documento]

## **Evolución previsible del sistema**

[Extraer información sobre futuras funcionalidades, roadmap]

- [Evolución 1: Extraer del documento]
- [Evolución 2: Extraer del documento]

## **Decisiones impactadas con los cambios solicitados**

[Extraer decisiones empresariales, manuales, políticas afectadas]

**Decisiones**

- [Decisión 1: Extraer del documento]
- [Decisión 2: Extraer del documento]

**Manuales**

- [Manual 1: Extraer del documento]
- [Manual 2: Extraer del documento]

## **Estrategia de liberación**

[Extraer estrategia de implementación, fases, rollout]

**Anexo**

[Incluir anexos adicionales mencionados en el documento]

---

**NOTAS DE ANÁLISIS:**
- Información extraída directamente del documento: [Listar las secciones principales de donde se extrajo información]
- Secciones que requieren información adicional: [Listar lo que falta definir]
- Recomendaciones para completar el DEF: [Sugerir próximos pasos específicos]

**REGLAS DE EXTRACCIÓN:**
- Prioriza información explícita sobre inferencias
- Mantén la terminología del documento original
- Conserva nombres, roles y datos específicos tal como aparecen
- Para procesos complejos, desglosa en pasos específicos
- Identifica todos los stakeholders mencionados directa o indirectamente
- Extrae todos los requerimientos implícitos en los procesos descritos
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
        return f"Error generando documento DEF: {str(e)}"