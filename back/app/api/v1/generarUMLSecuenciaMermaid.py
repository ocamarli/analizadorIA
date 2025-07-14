
from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import io
import PyPDF2
from langchain_community.chat_models import AzureChatOpenAI
from langchain.prompts import PromptTemplate
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Blueprint
diagramaSecuenciaMermaid_bp = Blueprint('generador_diagramas_secuencia_mermaid', __name__)

# Configuración LangChain
try:
    llm = AzureChatOpenAI(
        deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1"),
        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        openai_api_key=os.getenv("AZURE_OPENAI_API_KEY", "6076ii7OpLiuTEKYsEVvWyt57RYjzb8d4hDwZRqKuokBi1WTuKz9JQQJ99AJACYeBjFXJ3w3AAABACOGfwuS"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://openaidemobside.openai.azure.com"),
        temperature=0.3  # Menos creatividad, más precisión
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

def simple_mermaid_validation(content):
    """Validación muy básica - solo verifica que empiece con sequenceDiagram"""
    content = content.strip()
    if not content:
        return False, "Contenido vacío"
    
    if not content.startswith('sequenceDiagram'):
        return False, "Debe empezar con 'sequenceDiagram'"
    
    lines = content.split('\n')
    if len(lines) < 2:
        return False, "Debe tener al menos una línea después del encabezado"
    
    return True, None

def clean_mermaid_response(content):
    """Limpieza mínima del contenido"""
    # Remover bloques de código markdown
    if '```' in content:
        # Encontrar el contenido entre ```
        start_markers = ['```mermaid', '```', '```text']
        for marker in start_markers:
            if marker in content:
                parts = content.split(marker)
                if len(parts) > 1:
                    # Tomar la parte después del primer marcador
                    content = parts[1]
                    # Si hay un ``` de cierre, tomar solo hasta ahí
                    if '```' in content:
                        content = content.split('```')[0]
                    break
    
    # Buscar sequenceDiagram y tomar todo desde ahí
    lines = content.split('\n')
    start_idx = -1
    
    for i, line in enumerate(lines):
        if line.strip().startswith('sequenceDiagram'):
            start_idx = i
            break
    
    if start_idx >= 0:
        content = '\n'.join(lines[start_idx:])
    
    return content.strip()

# Template mejorado para evitar errores de activación
sequence_diagram_prompt = PromptTemplate(
    input_variables=["contenido_archivo", "contexto_adicional"],
    template="""
Eres un experto en diagramas Mermaid. Analiza el contenido y genera ÚNICAMENTE un diagrama de secuencia válido en sintaxis Mermaid.

CONTENIDO A ANALIZAR:
{contenido_archivo}

CONTEXTO ADICIONAL:
{contexto_adicional}

REGLAS ESTRICTAS:
1. Inicia SIEMPRE con "sequenceDiagram"
2. Usa participant para definir actores si es necesario
3. Sintaxis de mensajes (IMPORTANTE - MANEJO DE ACTIVACIÓN):
   - A->>B: mensaje simple (SIN activación)
   - A-->>B: respuesta simple (SIN activación)
   - A->>+B: mensaje que ACTIVA a B (usar solo cuando B necesite estar activo)
   - B-->>-A: respuesta que DESACTIVA a B (solo si B fue activado antes)
   
4. REGLA CRÍTICA DE ACTIVACIÓN:
   - Solo usa "+" para activar cuando el participante vaya a procesar algo
   - Solo usa "-" para desactivar si previamente usaste "+"
   - Si no estás seguro, NO uses +/- (usa solo -> o -->>)
   
5. Para condicionales usa: alt/else/end y opt/end
6. NO agregues explicaciones, comentarios o texto adicional
7. NO uses bloques de código (```)

EJEMPLO SEGURO (sin activación compleja):
sequenceDiagram
    participant U as Usuario
    participant S as Sistema
    participant D as Database
    
    U->>S: 1. Solicitar datos
    S->>D: 2. Consultar información
    D-->>S: 3. Retornar resultados
    S-->>U: 4. Mostrar datos

EJEMPLO CON ACTIVACIÓN CORRECTA:
sequenceDiagram
    participant U as Usuario
    participant S as Sistema
    participant D as Database
    
    U->>+S: 1. Solicitar procesamiento
    S->>+D: 2. Consultar datos
    D-->>-S: 3. Retornar información
    S-->>-U: 4. Entregar resultado

IMPORTANTE: Si tienes dudas sobre activación/desactivación, usa mensajes simples (-> o -->) sin +/-

Ahora genera SOLO el diagrama Mermaid basado en el contenido:
"""
)

@diagramaSecuenciaMermaid_bp.route('/diagramaSecuenciaMermaid/generate', methods=['POST'])
def generate_sequence_diagram():
    """Genera diagrama de secuencia en formato Mermaid - Versión Lite"""
    try:
        logger.info("=== GENERANDO DIAGRAMA MERMAID (VERSIÓN LITE) ===")
        
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
                        contenido_archivo += f"\n--- {file.filename} ---\n{texto_extraido}\n"
                    
                    elif file.filename.lower().endswith(('.md', '.markdown', '.txt')):
                        texto_extraido = extract_text_from_markdown(file_content)
                        contenido_archivo += f"\n--- {file.filename} ---\n{texto_extraido}\n"
                    
                    else:
                        return jsonify({
                            'success': False,
                            'error': f'Formato no soportado: {file.filename}'
                        }), 400
                        
                except Exception as e:
                    return jsonify({
                        'success': False,
                        'error': f'Error procesando {file.filename}: {str(e)}'
                    }), 400
        
        if not contenido_archivo and contexto_adicional:
            contenido_archivo = "Información proporcionada por el usuario."
        
        # Generar con IA
        logger.info("Generando diagrama con IA...")
        chain = sequence_diagram_prompt | llm
        
        response = chain.invoke({
            'contenido_archivo': contenido_archivo,
            'contexto_adicional': contexto_adicional or "Sin contexto adicional."
        })
        
        # Limpieza mínima
        mermaid_content = clean_mermaid_response(response.content)
        
        logger.info(f"Contenido generado: {mermaid_content[:200]}...")
        
        # Validación súper básica
        is_valid, error_msg = simple_mermaid_validation(mermaid_content)
        
        if not is_valid:
            logger.warning(f"Validación básica falló: {error_msg}")
            # Si falla, intentamos una vez más con prompt más específico
            retry_response = chain.invoke({
                'contenido_archivo': contenido_archivo,
                'contexto_adicional': f"{contexto_adicional}\n\nIMPORTANTE: Responde ÚNICAMENTE con código Mermaid válido comenzando con 'sequenceDiagram'"
            })
            
            mermaid_content = clean_mermaid_response(retry_response.content)
            is_valid, error_msg = simple_mermaid_validation(mermaid_content)
            
            # Si aún falla, lo enviamos igual (confiamos en la IA)
            if not is_valid:
                logger.warning("Validación falló pero enviando resultado de IA")
        
        logger.info("=== DIAGRAMA GENERADO EXITOSAMENTE ===")
        
        return jsonify({
            'success': True,
            'mermaid_content': mermaid_content,
            'diagram_type': 'sequence',
            'message': 'Diagrama de secuencia Mermaid generado exitosamente',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@diagramaSecuenciaMermaid_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint de salud"""
    return jsonify({
        'status': 'healthy',
        'service': 'sequence_diagram_mermaid_lite',
        'timestamp': datetime.now().isoformat(),
        'llm_configured': llm is not None
    })