from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import io
import PyPDF2
from langchain_community.chat_models import AzureChatOpenAI
from langchain.prompts import PromptTemplate
import xml.etree.ElementTree as ET

# Blueprint - MANTENEMOS EL NOMBRE ORIGINAL
diagramaSecuencia_bp = Blueprint('generador_diagramas_secuencia', __name__)

# Configuración EXACTA de LangChain - SIN CAMBIOS
# Configuración de LangChain
llm = AzureChatOpenAI(
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1"),
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
    openai_api_key=os.getenv("AZURE_OPENAI_API_KEY", "6076ii7OpLiuTEKYsEVvWyt57RYjzb8d4hDwZRqKuokBi1WTuKz9JQQJ99AJACYeBjFXJ3w3AAABACOGfwuS"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://openaidemobside.openai.azure.com"),
    temperature=0.7
)

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

def validate_xml(xml_content):
    """Valida que el XML sea válido para draw.io"""
    try:
        ET.fromstring(xml_content)
        return True, None
    except ET.ParseError as e:
        return False, str(e)

# Template para diagramas de secuencia
sequence_diagram_prompt = PromptTemplate(
    input_variables=["contenido_archivo", "contexto_adicional"],
    template="""
Eres un arquitecto de software experto en UML. Genera un diagrama de secuencia completo en formato XML para draw.io.

**CONTENIDO:**
{contenido_archivo}

**CONTEXTO:**
{contexto_adicional}

**INSTRUCCIONES:**
1. Genera XML válido que inicie con <mxfile> y termine con </mxfile>
2. Incluye todos los actores, sistemas, APIs, bases de datos identificados
3. Numera secuencialmente todos los mensajes (1, 2, 3...)
4. Por cada llamada, incluye su respuesta correspondiente
5. Usa activation boxes para mostrar cuando cada lifeline está activa
6. Incluye manejo de errores con frames alt/opt cuando sea apropiado
7. Posiciona elementos de manera clara y legible

**ESTRUCTURA XML REQUERIDA:**
<mxfile host="app.diagrams.net">
  <diagram name="Sequence Diagram">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <!-- Lifelines aquí -->
        <!-- Messages aquí -->
        <!-- Activation boxes aquí -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>

Genera SOLO el XML, sin explicaciones adicionales:
"""
)

@diagramaSecuencia_bp.route('/diagramaSecuencia/generate', methods=['POST'])
def generate_sequence_diagram():
    """Genera diagrama de secuencia en formato draw.io"""
    try:
        # Obtener datos del request
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
                            'error': f'Formato no soportado: {file.filename}. Use PDF, MD o TXT'
                        }), 400
                        
                except Exception as e:
                    return jsonify({
                        'success': False,
                        'error': f'Error procesando {file.filename}: {str(e)}'
                    }), 400
        
        if not contenido_archivo and contexto_adicional:
            contenido_archivo = "Información proporcionada por el usuario."
        
        # Generar diagrama con LLM
        chain = sequence_diagram_prompt | llm
        response = chain.invoke({
            'contenido_archivo': contenido_archivo,
            'contexto_adicional': contexto_adicional or "Sin contexto adicional."
        })
        
        # Limpiar y validar XML
        xml_content = response.content.strip()
        
        # Remover bloques de código si existen
        if xml_content.startswith('```'):
            lines = xml_content.split('\n')
            if lines[0].strip().startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            xml_content = '\n'.join(lines).strip()
        
        # Validar XML
        is_valid, error_msg = validate_xml(xml_content)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': f'XML generado no es válido: {error_msg}'
            }), 500
        
        return jsonify({
            'success': True,
            'xml_content': xml_content,
            'diagram_type': 'sequence',
            'message': 'Diagrama de secuencia generado exitosamente',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@diagramaSecuencia_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint de salud para el servicio"""
    return jsonify({
        'status': 'healthy',
        'service': 'sequence_diagram',
        'timestamp': datetime.now().isoformat()
    })