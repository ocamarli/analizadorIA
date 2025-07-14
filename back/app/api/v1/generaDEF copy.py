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
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4"),
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15"),
    openai_api_key=os.getenv("AZURE_OPENAI_API_KEY", "6076ii7OpLiuTEKYsEVvWyt57RYjzb8d4hDwZRqKuokBi1WTuKZ9JQQJ99AJACYeBjFXJ3w3AAABACOGfwuS"),
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
Eres un analista de sistemas experto en definición de requerimientos funcionales. Tu tarea es analizar el documento proporcionado y generar un Documento de Definición de Requerimientos Funcionales (DEF) usando TODA la información disponible en el documento.

DOCUMENTO A ANALIZAR:
{documento}

INSTRUCCIONES IMPORTANTES:
1. SIEMPRE genera un DEF completo usando toda la información disponible
2. Para información que SÍ está en el documento, úsala completamente
3. Para información que NO está en el documento, incluye la sección pero marca como "FALTA DEFINIR" seguido de sugerencias entre paréntesis
4. No omitas ninguna sección del DEF
5. Extrae y utiliza toda la información relevante que encuentres

FORMATO DEL DOCUMENTO DEF:

# DOCUMENTO DE DEFINICIÓN DE REQUERIMIENTOS FUNCIONALES (DEF)

## 1. INFORMACIÓN GENERAL DEL PROYECTO
- **Nombre del Proyecto:** [Si está en el documento usar esa información, si no: FALTA DEFINIR (Ejemplo: Sistema de Gestión de Inventarios)]
- **Fecha de Elaboración:** {fecha}
- **Versión:** 1.0
- **Elaborado por:** Sistema de Análisis Automatizado
- **Patrocinador:** [Si está en el documento usar esa información, si no: FALTA DEFINIR (Ejemplo: Gerencia de Operaciones)]
- **Líder del Proyecto:** [Si está en el documento usar esa información, si no: FALTA DEFINIR (Ejemplo: Juan Pérez - Analista Senior)]

## 2. RESUMEN EJECUTIVO
[Si hay información en el documento, incluirla aquí. Si no hay suficiente información: FALTA DEFINIR - Incluir descripción general del problema a resolver, objetivos principales y beneficios esperados (Ejemplo: Automatizar el proceso manual de control de inventarios para reducir errores y mejorar eficiencia operativa)]

## 3. ALCANCE DEL PROYECTO
### 3.1 Objetivos del Sistema
[Usar información del documento si está disponible, si no: FALTA DEFINIR (Ejemplos: Reducir tiempo de consultas en 80%, Eliminar errores de inventario, Generar reportes automáticos)]

### 3.2 Límites del Sistema
**Incluido:**
[Usar información del documento si está disponible, si no: FALTA DEFINIR (Ejemplos: Módulo de registro de productos, Consultas de stock, Reportes básicos)]

**Excluido:**
[Usar información del documento si está disponible, si no: FALTA DEFINIR (Ejemplos: Integración con sistemas contables, Módulo de compras, Control de acceso biométrico)]

## 4. DESCRIPCIÓN DEL DOMINIO DE NEGOCIO
[Usar información del documento si está disponible, si no: FALTA DEFINIR - Incluir descripción detallada del giro del negocio, modelo operativo actual, principales procesos y problemática a resolver (Ejemplo: Empresa comercializadora con 50 empleados que maneja inventario manual generando errores frecuentes)]

## 5. STAKEHOLDERS IDENTIFICADOS
[Crear tabla con información del documento si está disponible, si no usar formato:]

| Stakeholder | Rol | Responsabilidades | Estado |
|-------------|-----|-------------------|---------|
| [Nombre o FALTA DEFINIR] | [Rol específico] | [Responsabilidades] | [Encontrado/Falta Definir] |
| FALTA DEFINIR | Usuarios Finales | Operar el sistema diariamente | Falta Definir |
| FALTA DEFINIR | Administrador de Sistema | Gestionar usuarios y configuraciones | Falta Definir |

## 6. PROCESOS DE NEGOCIO
### 6.1 Procesos Actuales (AS-IS)
[Usar información del documento si está disponible, si no: FALTA DEFINIR - Documentar procesos manuales actuales, puntos de dolor y ineficiencias (Ejemplo: Registro manual en Excel, conteos físicos semanales, reportes manuales)]

### 6.2 Procesos Propuestos (TO-BE)
[Usar información del documento si está disponible, si no: FALTA DEFINIR - Describir procesos automatizados propuestos y mejoras esperadas (Ejemplo: Registro digital en tiempo real, alertas automáticas de stock bajo, reportes automáticos)]

## 7. REQUERIMIENTOS FUNCIONALES

[Para cada requerimiento identificado en el documento, usar este formato. Si no hay requerimientos explícitos, generar ejemplos marcados como FALTA DEFINIR:]

### RF-001: [Nombre del Requerimiento o FALTA DEFINIR]
- **Descripción:** [Usar información del documento o FALTA DEFINIR (Ejemplo: El sistema debe permitir registrar productos con código, nombre, precio y stock)]
- **Fuente:** [Stakeholder que lo solicitó o FALTA DEFINIR]
- **Prioridad:** [Alta/Media/Baja o FALTA DEFINIR]
- **Criterios de Aceptación:**
  - [Criterio específico o FALTA DEFINIR (Ejemplo: Validar que el código sea único)]
  - [Criterio específico o FALTA DEFINIR (Ejemplo: Campos obligatorios no pueden estar vacíos)]
- **Dependencias:** [Si las hay o FALTA DEFINIR]

### RF-002: FALTA DEFINIR (Gestión de Usuarios)
- **Descripción:** FALTA DEFINIR (Ejemplo: El sistema debe permitir crear, modificar y eliminar usuarios con diferentes roles)
- **Fuente:** FALTA DEFINIR
- **Prioridad:** FALTA DEFINIR
- **Criterios de Aceptación:**
  - FALTA DEFINIR (Ejemplo: Solo administradores pueden crear usuarios)
  - FALTA DEFINIR (Ejemplo: Contraseñas deben tener mínimo 8 caracteres)
- **Dependencias:** FALTA DEFINIR

## 8. REGLAS DE NEGOCIO
[Usar información del documento si está disponible, si no usar formato:]

### RN-001: [Nombre de la Regla o FALTA DEFINIR]
[Descripción específica o FALTA DEFINIR (Ejemplo: No se pueden registrar productos con stock negativo)]

### RN-002: FALTA DEFINIR (Validación de Datos)
FALTA DEFINIR (Ejemplo: Todos los precios deben ser mayores a cero)

## 9. RESTRICCIONES DEL SISTEMA
### 9.1 Restricciones Técnicas
[Usar información del documento si está disponible, si no:]
- FALTA DEFINIR (Ejemplo: Desarrollar en tecnología web compatible con Chrome, Firefox)
- FALTA DEFINIR (Ejemplo: Base de datos SQL Server o MySQL)
- FALTA DEFINIR (Ejemplo: Presupuesto máximo $20,000 USD)

### 9.2 Restricciones de Negocio
[Usar información del documento si está disponible, si no:]
- FALTA DEFINIR (Ejemplo: Implementación en horario no laboral)
- FALTA DEFINIR (Ejemplo: Capacitación máxima 2 horas por usuario)
- FALTA DEFINIR (Ejemplo: Go-live en fecha específica)

## 10. SUPUESTOS Y DEPENDENCIAS
[Usar información del documento si está disponible, si no:]
- FALTA DEFINIR (Ejemplo: Todos los usuarios tienen acceso a computadora)
- FALTA DEFINIR (Ejemplo: Red de internet estable durante horario laboral)
- FALTA DEFINIR (Ejemplo: Disponibilidad del equipo de TI para soporte)

## 11. CRITERIOS DE ÉXITO
[Usar información del documento si está disponible, si no:]
- FALTA DEFINIR (Ejemplo: Reducir tiempo de consultas en 70%)
- FALTA DEFINIR (Ejemplo: Disminuir errores de inventario en 90%)
- FALTA DEFINIR (Ejemplo: ROI positivo en 12 meses)
- FALTA DEFINIR (Ejemplo: Satisfacción de usuarios mayor a 80%)

## 12. RIESGOS IDENTIFICADOS

| Riesgo | Probabilidad | Impacto | Mitigación | Estado |
|--------|--------------|---------|------------|---------|
| [Riesgo del documento o FALTA DEFINIR] | [Alta/Media/Baja] | [Alto/Medio/Bajo] | [Estrategia] | [Encontrado/Falta Definir] |
| FALTA DEFINIR (Resistencia al cambio) | Media | Alto | Capacitación y comunicación | Falta Definir |
| FALTA DEFINIR (Retrasos en desarrollo) | Media | Medio | Seguimiento semanal de avances | Falta Definir |

---

**NOTAS IMPORTANTES:**
- Todas las secciones marcadas como "FALTA DEFINIR" requieren información adicional de los stakeholders
- Los ejemplos entre paréntesis son sugerencias para guiar la recopilación de información
- Se recomienda realizar entrevistas con usuarios clave para completar la información faltante

REGLAS DE FORMATO:
- Usa únicamente términos en español
- Mantén el formato Markdown exacto
- Para cada sección, usa primero la información del documento, después marca lo faltante
- Los ejemplos entre paréntesis deben ser específicos y útiles
- No omitas ninguna sección del formato
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