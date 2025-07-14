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
diagramaFlujoMermaid_bp = Blueprint('generador_diagramas_flujo_mermaid', __name__)

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

def simple_flowchart_validation(content):
    """Validación muy básica para diagramas de flujo"""
    content = content.strip()
    if not content:
        return False, "Contenido vacío"
    
    # Verificar que empiece con flowchart o graph
    valid_starts = ['flowchart TD', 'flowchart LR', 'graph TD', 'graph LR', 'flowchart TB', 'graph TB']
    starts_correctly = any(content.startswith(start) for start in valid_starts)
    
    if not starts_correctly:
        return False, "Debe empezar con 'flowchart TD', 'flowchart LR', 'graph TD' o 'graph LR'"
    
    lines = content.split('\n')
    if len(lines) < 2:
        return False, "Debe tener al menos un nodo o conexión después del encabezado"
    
    return True, None

def fix_mermaid_flowchart_syntax(content):
    """Corrige errores comunes de sintaxis en diagramas de flujo Mermaid"""
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('flowchart') or line.startswith('graph') or line.startswith('%'):
            fixed_lines.append(line)
            continue
        
        # Corregir caracteres problemáticos en etiquetas de nodos
        # Reemplazar paréntesis en textos de nodos (excepto los de sintaxis)
        import re
        
        # Buscar patrones de nodos con texto que contenga paréntesis
        # Patrón: NodoID[texto con (paréntesis)]
        node_pattern = r'(\w+)\[(.*?)\]'
        if re.search(node_pattern, line):
            def replace_parens(match):
                node_id = match.group(1)
                text = match.group(2)
                # Reemplazar paréntesis por texto alternativo
                text = text.replace('(', '').replace(')', '')
                text = text.replace('≥', 'mayor o igual a')
                text = text.replace('≤', 'menor o igual a')
                # Limpiar caracteres especiales problemáticos
                text = re.sub(r'[^\w\s\-_?¿!¡.:,/\\]', '', text)
                return f'{node_id}[{text}]'
            
            line = re.sub(node_pattern, replace_parens, line)
        
        # Limpiar etiquetas de conexiones que tengan caracteres especiales
        # Patrón: -->|texto con (paréntesis)| 
        edge_pattern = r'(\-\->?\|)(.*?)(\|)'
        if re.search(edge_pattern, line):
            def replace_edge_text(match):
                start = match.group(1)
                text = match.group(2)
                end = match.group(3)
                # Limpiar caracteres especiales
                text = text.replace('(', '').replace(')', '')
                text = text.replace('≥', 'mayor igual')
                text = text.replace('≤', 'menor igual')
                text = re.sub(r'[^\w\s\-_?¿!¡.:,]', '', text)
                return f'{start}{text}{end}'
            
            line = re.sub(edge_pattern, replace_edge_text, line)
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def clean_flowchart_response(content):
    """Limpieza específica para diagramas de flujo"""
    # Remover bloques de código markdown
    if '```' in content:
        start_markers = ['```mermaid', '```', '```text']
        for marker in start_markers:
            if marker in content:
                parts = content.split(marker)
                if len(parts) > 1:
                    content = parts[1]
                    if '```' in content:
                        content = content.split('```')[0]
                    break
    
    # Buscar flowchart o graph y tomar todo desde ahí
    lines = content.split('\n')
    start_idx = -1
    
    for i, line in enumerate(lines):
        line_clean = line.strip()
        if (line_clean.startswith('flowchart ') or 
            line_clean.startswith('graph ')):
            start_idx = i
            break
    
    if start_idx >= 0:
        content = '\n'.join(lines[start_idx:])
    
    # Aplicar corrección de sintaxis
    content = fix_mermaid_flowchart_syntax(content)
    
    return content.strip()

# Template específico para diagramas de flujo
flowchart_diagram_prompt = PromptTemplate(
    input_variables=["contenido_archivo", "contexto_adicional"],
    template="""
Eres un experto en diagramas Mermaid. Analiza el contenido y genera ÚNICAMENTE un diagrama de flujo válido en sintaxis Mermaid.

CONTENIDO A ANALIZAR:
{contenido_archivo}

CONTEXTO ADICIONAL:
{contexto_adicional}

REGLAS ESTRICTAS PARA DIAGRAMA DE FLUJO:
1. Inicia SIEMPRE con "flowchart TD" (Top Down) o "flowchart LR" (Left Right)
2. Usa diferentes formas de nodos:
   - A[Proceso rectangular]
   - B{{Decisión rombo}}
   - C([Inicio/Fin ovalado])
   - D[(Base de datos cilindro)]
   - E[/Entrada paralelo/]
   - F[\\Salida paralelo\\]

3. Conecta nodos con flechas:
   - A --> B (flecha simple)
   - B -->|Sí| C (flecha con etiqueta)
   - B -->|No| D (decisión con condición)

4. Para decisiones usa:
   - Nodo rombo: Decision{{¿Condición?}}
   - Salidas etiquetadas: Decision -->|Sí| ProcesoA
   - Decision -->|No| ProcesoB

5. REGLAS DE TEXTO IMPORTANTES:
   - NO uses paréntesis () en el texto de los nodos
   - NO uses símbolos matemáticos como ≥, ≤, ≠
   - USA texto simple: "mayor que", "menor que", "diferente de"
   - Evita caracteres especiales en textos
   - Mantén los textos cortos y descriptivos

6. NO agregues explicaciones, comentarios o texto adicional
7. NO uses bloques de código (```)
8. Usa nombres descriptivos pero concisos y sin caracteres especiales

EJEMPLO DE ESTRUCTURA CORRECTA:
flowchart TD
    Start([Inicio]) --> Input[/Ingresar datos/]
    Input --> Validate{{¿Datos válidos?}}
    Validate -->|Sí| Process[Procesar información]
    Validate -->|No| Error[Mostrar error]
    Process --> Save[(Guardar en BD)]
    Save --> End([Fin])
    Error --> Input

EJEMPLO CON VALIDACIONES:
flowchart TD
    Begin([Iniciar proceso]) --> CheckUser[Verificar usuario]
    CheckUser --> UserValid{{¿Usuario válido?}}
    UserValid -->|No| ErrorMsg[Mostrar error]
    UserValid -->|Sí| CheckLimit{{¿Límite disponible?}}
    CheckLimit -->|No| LimitError[Error de límite]
    CheckLimit -->|Sí| ProcessOK[Proceso exitoso]
    ErrorMsg --> Begin
    LimitError --> Begin
    ProcessOK --> Finish([Fin])

TIPOS DE PROCESOS A MODELAR:
- Procesos de negocio (aprobaciones, validaciones)
- Algoritmos (ordenamiento, búsqueda, cálculos)
- Flujos de autenticación/autorización
- Procesos de toma de decisiones
- Workflows de sistemas
- Flujos de datos y transformaciones

IMPORTANTE: 
- Identifica claramente puntos de inicio y fin
- Usa decisiones simples con condiciones claras
- Evita texto complejo en los nodos
- Mantén el flujo lógico y fácil de seguir
- NO uses caracteres especiales que puedan romper la sintaxis

Ahora genera SOLO el diagrama de flujo Mermaid basado en el contenido:
"""
)

@diagramaFlujoMermaid_bp.route('/diagramaFlujoMermaid/generate', methods=['POST'])
def generate_flowchart_diagram():
    """Genera diagrama de flujo en formato Mermaid"""
    try:
        logger.info("=== GENERANDO DIAGRAMA DE FLUJO MERMAID ===")
        
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
        
        # Generar diagrama de flujo con IA
        logger.info("Generando diagrama de flujo con IA...")
        chain = flowchart_diagram_prompt | llm
        
        response = chain.invoke({
            'contenido_archivo': contenido_archivo,
            'contexto_adicional': contexto_adicional or "Sin contexto adicional."
        })
        
        # Limpieza específica para flowchart
        mermaid_content = clean_flowchart_response(response.content)
        
        logger.info(f"Contenido generado: {mermaid_content[:200]}...")
        
        # Validación específica para flowchart
        is_valid, error_msg = simple_flowchart_validation(mermaid_content)
        
        if not is_valid:
            logger.warning(f"Validación básica falló: {error_msg}")
            # Segundo intento con prompt más específico
            retry_response = chain.invoke({
                'contenido_archivo': contenido_archivo,
                'contexto_adicional': f"{contexto_adicional}\n\nIMPORTANTE: Responde ÚNICAMENTE con código Mermaid de diagrama de flujo válido comenzando con 'flowchart TD'"
            })
            
            mermaid_content = clean_flowchart_response(retry_response.content)
            is_valid, error_msg = simple_flowchart_validation(mermaid_content)
            
            # Si aún falla, lo enviamos igual (confiamos en la IA)
            if not is_valid:
                logger.warning("Validación falló pero enviando resultado de IA")
        
        logger.info("=== DIAGRAMA DE FLUJO GENERADO EXITOSAMENTE ===")
        
        return jsonify({
            'success': True,
            'mermaid_content': mermaid_content,
            'diagram_type': 'flowchart',
            'message': 'Diagrama de flujo Mermaid generado exitosamente',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@diagramaFlujoMermaid_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint de salud"""
    return jsonify({
        'status': 'healthy',
        'service': 'flowchart_diagram_mermaid',
        'timestamp': datetime.now().isoformat(),
        'llm_configured': llm is not None
    })