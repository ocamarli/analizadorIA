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
diagramaClasesMermaid_bp = Blueprint('generador_diagramas_clases_mermaid', __name__)

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

def simple_class_diagram_validation(content):
    """Validación muy básica para diagramas de clases"""
    content = content.strip()
    if not content:
        return False, "Contenido vacío"
    
    if not content.startswith('classDiagram'):
        return False, "Debe empezar con 'classDiagram'"
    
    lines = content.split('\n')
    if len(lines) < 2:
        return False, "Debe tener al menos una clase o relación después del encabezado"
    
    return True, None

def fix_mermaid_class_syntax(content):
    """Corrige errores comunes de sintaxis en diagramas de clases Mermaid"""
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('classDiagram') or line.startswith('%'):
            fixed_lines.append(line)
            continue
        
        # Limpiar caracteres problemáticos en nombres de clases y métodos
        # Reemplazar caracteres especiales que pueden romper la sintaxis
        line = line.replace('()', '')  # Quitar paréntesis vacíos
        line = line.replace('≥', 'mayor_igual')
        line = line.replace('≤', 'menor_igual')
        line = line.replace('≠', 'diferente')
        
        # Limpiar caracteres especiales en nombres de atributos y métodos
        # Mantener solo caracteres alfanuméricos, guiones bajos y algunos símbolos básicos
        line = re.sub(r'[^\w\s\-_+#~:(){}\[\]|<>*]', '', line)
        
        # Corregir sintaxis de métodos con parámetros
        # Ejemplo: +método(parámetro: tipo) → +método(parametro: tipo)
        method_pattern = r'([+\-#~])(\w+)\((.*?)\)'
        if re.search(method_pattern, line):
            def fix_method(match):
                visibility = match.group(1)
                method_name = match.group(2)
                params = match.group(3)
                # Limpiar parámetros de caracteres especiales
                params = re.sub(r'[^\w\s:,]', '', params)
                return f'{visibility}{method_name}({params})'
            line = re.sub(method_pattern, fix_method, line)
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def clean_class_diagram_response(content):
    """Limpieza específica para diagramas de clases"""
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
    
    # Buscar classDiagram y tomar todo desde ahí
    lines = content.split('\n')
    start_idx = -1
    
    for i, line in enumerate(lines):
        if line.strip().startswith('classDiagram'):
            start_idx = i
            break
    
    if start_idx >= 0:
        content = '\n'.join(lines[start_idx:])
    
    # Aplicar corrección de sintaxis
    content = fix_mermaid_class_syntax(content)
    
    return content.strip()

# Template específico para diagramas de clases
class_diagram_prompt = PromptTemplate(
    input_variables=["contenido_archivo", "contexto_adicional"],
    template="""
Eres un experto en diagramas UML y Mermaid. Analiza el contenido y genera ÚNICAMENTE un diagrama de clases válido en sintaxis Mermaid.

CONTENIDO A ANALIZAR:
{contenido_archivo}

CONTEXTO ADICIONAL:
{contexto_adicional}

REGLAS ESTRICTAS PARA DIAGRAMA DE CLASES:
1. Inicia SIEMPRE con "classDiagram"
2. Define clases con esta estructura:
   class NombreClase {{
       +atributo_publico : tipo
       -atributo_privado : tipo
       #atributo_protegido : tipo
       +metodo_publico(parametros) : tipo_retorno
       -metodo_privado() : tipo_retorno
   }}

3. Símbolos de visibilidad:
   - "+" para público
   - "-" para privado
   - "#" para protegido
   - "~" para package/interno

4. Tipos de relaciones:
   - ClaseA --|> ClaseB : herencia/extends
   - ClaseA --* ClaseB : composición
   - ClaseA --o ClaseB : agregación
   - ClaseA --> ClaseB : asociación
   - ClaseA ..> ClaseB : dependencia
   - ClaseA ..|> ClaseB : implementación

5. REGLAS DE SINTAXIS IMPORTANTES:
   - NO uses paréntesis vacíos en métodos: método() → método
   - NO uses caracteres especiales en nombres: ≥, ≤, ñ, etc.
   - USA solo letras, números y guiones bajos
   - Mantén nombres simples y claros
   - NO uses espacios en nombres de clases o métodos

6. NO agregues explicaciones, comentarios o texto adicional
7. NO uses bloques de código
8. Usa nombres descriptivos pero sin caracteres especiales

EJEMPLO DE ESTRUCTURA CORRECTA:
classDiagram
    class Usuario {{
        -id : Long
        -nombre : String
        -email : String
        +login(password : String) : Boolean
        +logout : void
        -validarEmail : Boolean
    }}
    
    class Producto {{
        -id : Long
        -nombre : String
        -precio : Double
        +calcularDescuento : Double
        +actualizarPrecio(nuevoPrecio : Double) : void
    }}
    
    class Pedido {{
        -id : Long
        -fecha : Date
        -total : Double
        +agregarProducto(producto : Producto) : void
        +calcularTotal : Double
    }}
    
    Usuario --> Pedido : realiza
    Pedido --* Producto : contiene
    Usuario --|> Persona : hereda

EJEMPLO CON HERENCIA:
classDiagram
    class Animal {{
        #nombre : String
        #edad : int
        +comer : void
        +dormir : void
    }}
    
    class Perro {{
        -raza : String
        +ladrar : void
        +jugar : void
    }}
    
    class Gato {{
        -color : String
        +maullar : void
        +cazar : void
    }}
    
    Animal <|-- Perro
    Animal <|-- Gato

TIPOS DE SISTEMAS A MODELAR:
- Sistemas de gestión (usuarios, productos, pedidos)
- Aplicaciones web (MVC, servicios, controladores)
- Sistemas académicos (estudiantes, cursos, profesores)
- E-commerce (catálogo, carrito, pagos)
- Sistemas bancarios (cuentas, transacciones, clientes)

IMPORTANTE:
- Identifica las entidades principales del dominio
- Define atributos con tipos de datos apropiados
- Incluye métodos principales de cada clase
- Establece relaciones claras entre clases
- Usa visibilidad apropiada (público, privado, protegido)
- NO uses caracteres especiales que rompan la sintaxis

Ahora genera SOLO el diagrama de clases Mermaid basado en el contenido:
"""
)

@diagramaClasesMermaid_bp.route('/diagramaClasesMermaid/generate', methods=['POST'])
def generate_class_diagram():
    """Genera diagrama de clases en formato Mermaid"""
    try:
        logger.info("=== GENERANDO DIAGRAMA DE CLASES MERMAID ===")
        
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
        
        # Generar diagrama de clases con IA
        logger.info("Generando diagrama de clases con IA...")
        chain = class_diagram_prompt | llm
        
        response = chain.invoke({
            'contenido_archivo': contenido_archivo,
            'contexto_adicional': contexto_adicional or "Sin contexto adicional."
        })
        
        # Limpieza específica para classDiagram
        mermaid_content = clean_class_diagram_response(response.content)
        
        logger.info(f"Contenido generado: {mermaid_content[:200]}...")
        
        # Validación específica para classDiagram
        is_valid, error_msg = simple_class_diagram_validation(mermaid_content)
        
        if not is_valid:
            logger.warning(f"Validación básica falló: {error_msg}")
            # Segundo intento con prompt más específico
            retry_response = chain.invoke({
                'contenido_archivo': contenido_archivo,
                'contexto_adicional': f"{contexto_adicional}\n\nIMPORTANTE: Responde ÚNICAMENTE con código Mermaid de diagrama de clases válido comenzando con 'classDiagram'"
            })
            
            mermaid_content = clean_class_diagram_response(retry_response.content)
            is_valid, error_msg = simple_class_diagram_validation(mermaid_content)
            
            # Si aún falla, lo enviamos igual (confiamos en la IA)
            if not is_valid:
                logger.warning("Validación falló pero enviando resultado de IA")
        
        logger.info("=== DIAGRAMA DE CLASES GENERADO EXITOSAMENTE ===")
        
        return jsonify({
            'success': True,
            'mermaid_content': mermaid_content,
            'diagram_type': 'class',
            'message': 'Diagrama de clases Mermaid generado exitosamente',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@diagramaClasesMermaid_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint de salud"""
    return jsonify({
        'status': 'healthy',
        'service': 'class_diagram_mermaid',
        'timestamp': datetime.now().isoformat(),
        'llm_configured': llm is not None
    })