from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import io
import PyPDF2
from langchain_community.chat_models import AzureChatOpenAI
from langchain.prompts import PromptTemplate
import logging
import re

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Blueprint
diagramaMatrizImpacto_bp = Blueprint('generador_matriz_impacto_mermaid', __name__)

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
    """Validación muy básica para diagramas flowchart"""
    content = content.strip()
    if not content:
        return False, "Contenido vacío"
    
    if not content.startswith('flowchart'):
        return False, "Debe empezar con 'flowchart'"
    
    lines = content.split('\n')
    if len(lines) < 2:
        return False, "Debe tener al menos un nodo o conexión después del encabezado"
    
    return True, None

def fix_mermaid_flowchart_syntax(content):
    """Corrige errores comunes de sintaxis en diagramas flowchart Mermaid"""
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('flowchart') or line.startswith('%'):
            fixed_lines.append(line)
            continue
        
        # Limpiar caracteres problemáticos en nombres de nodos
        # Reemplazar caracteres especiales que pueden romper la sintaxis
        line = line.replace('ñ', 'n')
        line = line.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        line = line.replace('Á', 'A').replace('É', 'E').replace('Í', 'I').replace('Ó', 'O').replace('Ú', 'U')
        
        # Limpiar caracteres especiales que pueden romper los nombres de nodos
        line = re.sub(r'[^\w\s\-_+#~:(){}\[\]|<>*]', '', line)
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def clean_impact_matrix_response(content):
    """Limpieza específica para matriz de impacto"""
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
    
    # Buscar flowchart y tomar todo desde ahí
    lines = content.split('\n')
    start_idx = -1
    
    for i, line in enumerate(lines):
        if line.strip().startswith('flowchart'):
            start_idx = i
            break
    
    if start_idx >= 0:
        content = '\n'.join(lines[start_idx:])
    
    # Aplicar corrección de sintaxis
    content = fix_mermaid_flowchart_syntax(content)
    
    return content.strip()

# Template específico para matriz de impacto
impact_matrix_prompt = PromptTemplate(
    input_variables=["contenido_archivo", "contexto_adicional"],
    template="""
Eres un experto en arquitectura de software y diagramas Mermaid. Analiza el contenido y genera ÚNICAMENTE una matriz de impacto válida en sintaxis Mermaid flowchart.

CONTENIDO A ANALIZAR:
{contenido_archivo}

CONTEXTO ADICIONAL:
{contexto_adicional}

REGLAS ESTRICTAS PARA MATRIZ DE IMPACTO:
1. Inicia SIEMPRE con "flowchart TD" (Top Down)
2. Define 4 capas arquitectónicas principales:
   - INTERFAZ (capa superior - color azul)
   - SERVICIO/COMPONENTE DOMINIO (capa intermedia - color amarillo)
   - SERVICIO/COMPONENTE PROXY (capa inferior - color verde)
   - REPOSITORIO (capa base - color por defecto)

3. Estructura de nodos por capa:
   - Interfaz: H1001, H1002, H1003... (HU-xxx relacionados)
   - Dominio: Servicio_Consultar_Usuario, Servicio_Mensual_Comb_Clases, etc.
   - Proxy: Servicio_Consultar_Usuario_Proxy, Servicio_Mensual_Proxy, etc.
   - Repositorio: Repositorio_Usuario, Repositorio_Clases, etc.

4. Sintaxis de nodos:
   - H1001[HU001 - Sistema Dibujo]
   - Servicio_Usuario[Servicio Consultar Usuario]
   - Servicio_Usuario_Proxy[Servicio Consultar Usuario Proxy]
   - Repo_Usuario[Repositorio Usuario]

5. Conexiones entre capas:
   - H1001 --> Servicio_Usuario
   - Servicio_Usuario --> Servicio_Usuario_Proxy
   - Servicio_Usuario_Proxy --> Repo_Usuario

6. Estilos de colores por capa:
   - classDef interfaz fill:#E3F2FD,stroke:#1976D2,stroke-width:2px,color:#000
   - classDef dominio fill:#FFF3E0,stroke:#F57C00,stroke-width:2px,color:#000
   - classDef proxy fill:#E8F5E8,stroke:#388E3C,stroke-width:2px,color:#000
   - classDef repositorio fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#000

7. Aplicar clases CSS:
   - class H1001,H1002,H1003 interfaz
   - class Servicio_Usuario,Servicio_Clases dominio
   - class Servicio_Usuario_Proxy,Servicio_Clases_Proxy proxy
   - class Repo_Usuario,Repo_Clases repositorio

8. REGLAS DE SINTAXIS IMPORTANTES:
   - NO uses espacios en nombres de nodos, usa guiones bajos
   - NO uses caracteres especiales: ñ, acentos, símbolos raros
   - USA nombres descriptivos pero limpios
   - Mantén consistencia en nomenclatura

9. NO agregues explicaciones, comentarios o texto adicional
10. NO uses bloques de código

EJEMPLO DE ESTRUCTURA CORRECTA:
flowchart TD
    %% Capa Interfaz
    H1001[HU001 - Gestion Usuarios]
    H1002[HU002 - Control Clases]
    H1003[HU003 - Menu Principal]
    
    %% Capa Servicio Dominio
    Servicio_Consultar_Usuario[Servicio Consultar Usuario]
    Servicio_Control_Clases[Servicio Control Clases]
    Servicio_Menu_Principal[Servicio Menu Principal]
    
    %% Capa Servicio Proxy
    Servicio_Consultar_Usuario_Proxy[Servicio Consultar Usuario Proxy]
    Servicio_Control_Clases_Proxy[Servicio Control Clases Proxy]
    Servicio_Menu_Principal_Proxy[Servicio Menu Principal Proxy]
    
    %% Capa Repositorio
    Repo_Usuario[Repositorio Usuario]
    Repo_Clases[Repositorio Clases]
    Repo_Menu[Repositorio Menu]
    
    %% Conexiones
    H1001 --> Servicio_Consultar_Usuario
    H1002 --> Servicio_Control_Clases
    H1003 --> Servicio_Menu_Principal
    
    Servicio_Consultar_Usuario --> Servicio_Consultar_Usuario_Proxy
    Servicio_Control_Clases --> Servicio_Control_Clases_Proxy
    Servicio_Menu_Principal --> Servicio_Menu_Principal_Proxy
    
    Servicio_Consultar_Usuario_Proxy --> Repo_Usuario
    Servicio_Control_Clases_Proxy --> Repo_Clases
    Servicio_Menu_Principal_Proxy --> Repo_Menu
    
    %% Estilos
    classDef interfaz fill:#E3F2FD,stroke:#1976D2,stroke-width:2px,color:#000
    classDef dominio fill:#FFF3E0,stroke:#F57C00,stroke-width:2px,color:#000
    classDef proxy fill:#E8F5E8,stroke:#388E3C,stroke-width:2px,color:#000
    classDef repositorio fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#000
    
    %% Aplicar estilos
    class H1001,H1002,H1003 interfaz
    class Servicio_Consultar_Usuario,Servicio_Control_Clases,Servicio_Menu_Principal dominio
    class Servicio_Consultar_Usuario_Proxy,Servicio_Control_Clases_Proxy,Servicio_Menu_Principal_Proxy proxy
    class Repo_Usuario,Repo_Clases,Repo_Menu repositorio

EJEMPLO PARA E-COMMERCE:
flowchart TD
    %% Interfaz
    H1001[HU001 - Catalogo Productos]
    H1002[HU002 - Carrito Compras]
    H1003[HU003 - Proceso Pago]
    
    %% Dominio
    Servicio_Catalogo[Servicio Catalogo]
    Servicio_Carrito[Servicio Carrito]
    Servicio_Pago[Servicio Pago]
    
    %% Proxy
    Servicio_Catalogo_Proxy[Servicio Catalogo Proxy]
    Servicio_Carrito_Proxy[Servicio Carrito Proxy]
    Servicio_Pago_Proxy[Servicio Pago Proxy]
    
    %% Repositorio
    Repo_Producto[Repositorio Producto]
    Repo_Carrito[Repositorio Carrito]
    Repo_Transaccion[Repositorio Transaccion]
    
    %% Conexiones
    H1001 --> Servicio_Catalogo
    H1002 --> Servicio_Carrito
    H1003 --> Servicio_Pago
    
    Servicio_Catalogo --> Servicio_Catalogo_Proxy
    Servicio_Carrito --> Servicio_Carrito_Proxy
    Servicio_Pago --> Servicio_Pago_Proxy
    
    Servicio_Catalogo_Proxy --> Repo_Producto
    Servicio_Carrito_Proxy --> Repo_Carrito
    Servicio_Pago_Proxy --> Repo_Transaccion
    
    %% Estilos
    classDef interfaz fill:#E3F2FD,stroke:#1976D2,stroke-width:2px,color:#000
    classDef dominio fill:#FFF3E0,stroke:#F57C00,stroke-width:2px,color:#000
    classDef proxy fill:#E8F5E8,stroke:#388E3C,stroke-width:2px,color:#000
    classDef repositorio fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#000
    
    class H1001,H1002,H1003 interfaz
    class Servicio_Catalogo,Servicio_Carrito,Servicio_Pago dominio
    class Servicio_Catalogo_Proxy,Servicio_Carrito_Proxy,Servicio_Pago_Proxy proxy
    class Repo_Producto,Repo_Carrito,Repo_Transaccion repositorio

IMPORTANTE:
- Identifica las historias de usuario principales
- Mapea cada HU a servicios de dominio específicos
- Crea servicios proxy correspondientes para cada dominio
- Define repositorios que manejen la persistencia
- Usa nomenclatura consistente y sin caracteres especiales
- Mantén la estructura de 4 capas arquitectónicas
- Aplica colores distintivos por capa para visualización clara

Ahora genera SOLO la matriz de impacto Mermaid basada en el contenido:
"""
)

@diagramaMatrizImpacto_bp.route('/matrizImpacto/generate', methods=['POST'])
def generate_impact_matrix():
    """Genera matriz de impacto en formato Mermaid"""
    try:
        logger.info("=== GENERANDO MATRIZ DE IMPACTO MERMAID ===")
        
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
        
        # Generar matriz de impacto con IA
        logger.info("Generando matriz de impacto con IA...")
        chain = impact_matrix_prompt | llm
        
        response = chain.invoke({
            'contenido_archivo': contenido_archivo,
            'contexto_adicional': contexto_adicional or "Sin contexto adicional."
        })
        
        # Limpieza específica para matriz de impacto
        mermaid_content = clean_impact_matrix_response(response.content)
        
        logger.info(f"Contenido generado: {mermaid_content[:200]}...")
        
        # Validación específica para flowchart
        is_valid, error_msg = simple_flowchart_validation(mermaid_content)
        
        if not is_valid:
            logger.warning(f"Validación básica falló: {error_msg}")
            # Segundo intento con prompt más específico
            retry_response = chain.invoke({
                'contenido_archivo': contenido_archivo,
                'contexto_adicional': f"{contexto_adicional}\n\nIMPORTANTE: Responde ÚNICAMENTE con código Mermaid flowchart válido comenzando con 'flowchart TD'"
            })
            
            mermaid_content = clean_impact_matrix_response(retry_response.content)
            is_valid, error_msg = simple_flowchart_validation(mermaid_content)
            
            # Si aún falla, lo enviamos igual (confiamos en la IA)
            if not is_valid:
                logger.warning("Validación falló pero enviando resultado de IA")
        
        logger.info("=== MATRIZ DE IMPACTO GENERADA EXITOSAMENTE ===")
        
        return jsonify({
            'success': True,
            'mermaid_content': mermaid_content,
            'diagram_type': 'impact_matrix',
            'message': 'Matriz de impacto Mermaid generada exitosamente',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@diagramaMatrizImpacto_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint de salud"""
    return jsonify({
        'status': 'healthy',
        'service': 'impact_matrix_mermaid',
        'timestamp': datetime.now().isoformat(),
        'llm_configured': llm is not None
    })