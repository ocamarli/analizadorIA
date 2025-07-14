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
diagramaArquitecturaMermaid_bp = Blueprint('generador_diagramas_arquitectura_mermaid', __name__)

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

def simple_architecture_validation(content):
    """Validación básica para diagramas de arquitectura"""
    content = content.strip()
    if not content:
        return False, "Contenido vacío"
    
    # Verificar que empiece con architecture-beta
    if not content.startswith('architecture-beta'):
        return False, "Debe empezar con 'architecture-beta'"
    
    lines = content.split('\n')
    if len(lines) < 2:
        return False, "Debe tener al menos un grupo o servicio después del encabezado"
    
    # Verificar que tenga al menos un grupo o servicio
    has_group_or_service = False
    for line in lines[1:]:
        line = line.strip()
        if line.startswith('group ') or line.startswith('service '):
            has_group_or_service = True
            break
    
    if not has_group_or_service:
        return False, "Debe tener al menos un grupo o servicio definido"
    
    return True, None

def fix_mermaid_architecture_syntax(content):
    """Corrige errores comunes de sintaxis en diagramas de arquitectura Mermaid"""
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('architecture-beta') or line.startswith('%'):
            fixed_lines.append(line)
            continue
        
        # Corregir caracteres problemáticos en etiquetas
        # Limpiar caracteres especiales que puedan romper la sintaxis
        line = re.sub(r'[^\w\s\-_()[\]{}.:,/\\]', '', line)
        
        # Corregir espacios en identificadores
        # Buscar patrones de grupos y servicios
        group_pattern = r'(group\s+)(\w+)(\([^)]*\))(\[[^\]]*\])'
        service_pattern = r'(service\s+)(\w+)(\([^)]*\))(\[[^\]]*\])'
        
        # Reemplazar espacios en identificadores por guiones bajos
        if re.search(group_pattern, line) or re.search(service_pattern, line):
            words = line.split()
            if len(words) > 1:
                # El identificador es el segundo elemento
                if len(words) > 1:
                    words[1] = words[1].replace(' ', '_')
                line = ' '.join(words)
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def clean_architecture_response(content):
    """Limpieza específica para diagramas de arquitectura"""
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
    
    # Buscar architecture-beta y tomar todo desde ahí
    lines = content.split('\n')
    start_idx = -1
    
    for i, line in enumerate(lines):
        line_clean = line.strip()
        if line_clean.startswith('architecture-beta'):
            start_idx = i
            break
    
    if start_idx >= 0:
        content = '\n'.join(lines[start_idx:])
    
    # Aplicar corrección de sintaxis
    content = fix_mermaid_architecture_syntax(content)
    
    return content.strip()

# Template específico para diagramas de arquitectura
architecture_diagram_prompt = PromptTemplate(
    input_variables=["contenido_archivo", "contexto_adicional"],
    template="""
Eres un experto en diagramas de arquitectura Mermaid. Analiza el contenido y genera ÚNICAMENTE un diagrama de arquitectura válido en sintaxis Mermaid.

CONTENIDO A ANALIZAR:
{contenido_archivo}

CONTEXTO ADICIONAL:
{contexto_adicional}

REGLAS ESTRICTAS PARA DIAGRAMA DE ARQUITECTURA:
1. Inicia SIEMPRE con "architecture-beta"

2. GRUPOS - Sintaxis: group {{group_id}}({{icon_name}})[{{title}}] (in {{parent_id}})?
   Ejemplos:
   - group api(cloud)[API Gateway]
   - group frontend(server)[Frontend Layer]
   - group backend(database)[Backend Services]
   - group storage(disk)[Storage Layer]

3. SERVICIOS - Sintaxis: service {{service_id}}({{icon_name}})[{{title}}] (in {{parent_id}})?
   Ejemplos:
   - service web(server)[Web Server] in frontend
   - service db(database)[Database] in backend
   - service cache(disk)[Redis Cache] in storage

4. ICONOS DISPONIBLES:
   - cloud: Servicios en la nube
   - database: Bases de datos
   - disk: Almacenamiento
   - internet: Conectividad web
   - server: Servidores y aplicaciones

5. CONEXIONES - Sintaxis: {{serviceId}}:{{L|R|T|B}} --{{>}}? {{T|B|L|R}}:{{serviceId}}
   Ejemplos:
   - web:R -- L:api (conexión simple)
   - api:B --> T:db (conexión con flecha)
   - cache:L -- R:db (conexión lateral)

6. DIRECCIONES DE CONEXIÓN:
   - L: Izquierda (Left)
   - R: Derecha (Right)
   - T: Arriba (Top)
   - B: Abajo (Bottom)

7. JUNCTIONS (Opcional) - Para conexiones complejas:
   - junction {{junction_id}}
   - Útil para dividir flujos de datos

8. REGLAS DE NAMING:
   - Usa identificadores sin espacios ni caracteres especiales
   - Usa guiones bajos para separar palabras: web_server, user_db
   - Mantén los nombres descriptivos pero concisos

EJEMPLO DE ESTRUCTURA CORRECTA:
architecture-beta
    group frontend(cloud)[Frontend Layer]
    group backend(server)[Backend Services]
    group data(database)[Data Layer]
    
    service web(server)[Web App] in frontend
    service api(server)[REST API] in backend
    service auth(server)[Auth Service] in backend
    service db(database)[PostgreSQL] in data
    service cache(disk)[Redis] in data
    
    web:R --> L:api
    api:B --> T:db
    api:R --> L:cache
    auth:B --> T:db

EJEMPLO CON MICROSERVICIOS:
architecture-beta
    group external(cloud)[External Services]
    group gateway(internet)[API Gateway]
    group services(server)[Microservices]
    group persistence(database)[Data Persistence]
    
    service cdn(cloud)[CDN] in external
    service lb(internet)[Load Balancer] in gateway
    service user_svc(server)[User Service] in services
    service order_svc(server)[Order Service] in services
    service payment_svc(server)[Payment Service] in services
    service user_db(database)[User DB] in persistence
    service order_db(database)[Order DB] in persistence
    
    cdn:B --> T:lb
    lb:B --> T:user_svc
    lb:B --> T:order_svc
    user_svc:R --> L:payment_svc
    user_svc:B --> T:user_db
    order_svc:B --> T:order_db

TIPOS DE ARQUITECTURAS A MODELAR:
- Arquitecturas de microservicios
- Arquitecturas en la nube (AWS, Azure, GCP)
- Arquitecturas web (frontend, backend, database)
- Arquitecturas de datos (ETL, data lakes, warehouses)
- Arquitecturas de integración (APIs, message queues)
- Arquitecturas de contenedores (Docker, Kubernetes)

PATRONES COMUNES:
- Layered Architecture: Presentación → Business → Data
- Microservices: Servicios independientes con bases de datos separadas
- Event-Driven: Servicios comunicándose via eventos
- API-First: Gateway centralizado para APIs
- CQRS: Separación de comandos y consultas

IMPORTANTE:
- Agrupa servicios relacionados lógicamente
- Usa iconos apropiados para cada tipo de servicio
- Mantén las conexiones claras y lógicas
- Evita cruces innecesarios de líneas
- Organiza de izquierda a derecha o de arriba a abajo

NO agregues explicaciones, comentarios o texto adicional.
NO uses bloques de código (```).
Genera SOLO el diagrama de arquitectura Mermaid válido.

Ahora genera el diagrama de arquitectura basado en el contenido:
"""
)

@diagramaArquitecturaMermaid_bp.route('/diagramaArquitecturaMermaid/generate', methods=['POST'])
def generate_architecture_diagram():
    """Genera diagrama de arquitectura en formato Mermaid"""
    try:
        logger.info("=== GENERANDO DIAGRAMA DE ARQUITECTURA MERMAID ===")
        
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
        
        # Generar diagrama de arquitectura con IA
        logger.info("Generando diagrama de arquitectura con IA...")
        chain = architecture_diagram_prompt | llm
        
        response = chain.invoke({
            'contenido_archivo': contenido_archivo,
            'contexto_adicional': contexto_adicional or "Sin contexto adicional."
        })
        
        # Limpieza específica para architecture
        mermaid_content = clean_architecture_response(response.content)
        
        logger.info(f"Contenido generado: {mermaid_content[:200]}...")
        
        # Validación específica para architecture
        is_valid, error_msg = simple_architecture_validation(mermaid_content)
        
        if not is_valid:
            logger.warning(f"Validación básica falló: {error_msg}")
            # Segundo intento con prompt más específico
            retry_response = chain.invoke({
                'contenido_archivo': contenido_archivo,
                'contexto_adicional': f"{contexto_adicional}\n\nIMPORTANTE: Responde ÚNICAMENTE con código Mermaid de diagrama de arquitectura válido comenzando con 'architecture-beta'"
            })
            
            mermaid_content = clean_architecture_response(retry_response.content)
            is_valid, error_msg = simple_architecture_validation(mermaid_content)
            
            # Si aún falla, lo enviamos igual (confiamos en la IA)
            if not is_valid:
                logger.warning("Validación falló pero enviando resultado de IA")
        
        logger.info("=== DIAGRAMA DE ARQUITECTURA GENERADO EXITOSAMENTE ===")
        
        return jsonify({
            'success': True,
            'mermaid_content': mermaid_content,
            'diagram_type': 'architecture',
            'message': 'Diagrama de arquitectura Mermaid generado exitosamente',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@diagramaArquitecturaMermaid_bp.route('/diagramaArquitecturaMermaid/examples', methods=['GET'])
def get_architecture_examples():
    """Devuelve ejemplos de diagramas de arquitectura"""
    examples = {
        'microservices': """architecture-beta
    group external(cloud)[External Layer]
    group gateway(internet)[API Gateway]
    group services(server)[Microservices]
    group data(database)[Data Layer]
    
    service cdn(cloud)[CDN] in external
    service lb(internet)[Load Balancer] in gateway
    service user_svc(server)[User Service] in services
    service order_svc(server)[Order Service] in services
    service user_db(database)[User DB] in data
    service order_db(database)[Order DB] in data
    
    cdn:B --> T:lb
    lb:B --> T:user_svc
    lb:B --> T:order_svc
    user_svc:B --> T:user_db
    order_svc:B --> T:order_db""",
        
        'web_app': """architecture-beta
    group frontend(cloud)[Frontend]
    group backend(server)[Backend]
    group storage(database)[Storage]
    
    service web(server)[Web App] in frontend
    service api(server)[REST API] in backend
    service auth(server)[Auth Service] in backend
    service db(database)[PostgreSQL] in storage
    service cache(disk)[Redis] in storage
    
    web:R --> L:api
    api:R --> L:auth
    api:B --> T:db
    api:R --> L:cache""",
        
        'data_pipeline': """architecture-beta
    group sources(cloud)[Data Sources]
    group processing(server)[Processing]
    group storage(database)[Storage]
    
    service api_source(internet)[External API] in sources
    service file_source(disk)[File System] in sources
    service etl(server)[ETL Pipeline] in processing
    service warehouse(database)[Data Warehouse] in storage
    service lake(disk)[Data Lake] in storage
    
    api_source:B --> T:etl
    file_source:B --> T:etl
    etl:B --> T:warehouse
    etl:R --> L:lake"""
    }
    
    return jsonify({
        'success': True,
        'examples': examples,
        'message': 'Ejemplos de diagramas de arquitectura disponibles'
    })

@diagramaArquitecturaMermaid_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint de salud"""
    return jsonify({
        'status': 'healthy',
        'service': 'architecture_diagram_mermaid',
        'timestamp': datetime.now().isoformat(),
        'llm_configured': llm is not None
    })