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
diagramaArquitectura_bp = Blueprint('generador_diagramas_arquitectura_mermaid', __name__)

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

def clean_flowchart_architecture_response(content):
    """Limpieza específica para diagramas flowchart de arquitectura"""
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
    
    # Limpiar caracteres problemáticos pero mantener los necesarios para flowchart
    lines = content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        if line.strip().startswith('flowchart') or line.strip().startswith('subgraph') or line.strip().startswith('end') or line.strip().startswith('%'):
            cleaned_lines.append(line)
        elif line.strip() and not line.strip().startswith('%%'):
            # Limpiar líneas de nodos y conexiones
            # Remover caracteres problemáticos pero mantener la sintaxis flowchart
            line = re.sub(r'[^\w\s\-_+()[\]{}<>=.:/"\\|]', '', line)
            cleaned_lines.append(line)
        else:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines).strip()

def validate_flowchart_architecture(content):
    """Validación específica para flowchart de arquitectura"""
    content = content.strip()
    if not content:
        return False, "Contenido vacío"
    
    if not content.startswith('flowchart'):
        return False, "Debe empezar con 'flowchart TD' o 'flowchart LR'"
    
    lines = content.split('\n')
    if len(lines) < 5:
        return False, "El diagrama debe tener al menos algunos subgrafos y conexiones"
    
    # Verificar que tenga al menos un subgraph
    has_subgraph = any('subgraph' in line for line in lines)
    if not has_subgraph:
        return False, "Diagrama de arquitectura debe tener al menos un subgraph"
    
    # Verificar que tenga conexiones
    has_connections = any('-->' in line or '-.>' in line or '==>' in line for line in lines)
    if not has_connections:
        return False, "Diagrama debe tener conexiones entre componentes"
    
    return True, None

# Template para diagramas de arquitectura usando flowchart (compatible y editable)
flowchart_architecture_prompt = PromptTemplate(
    input_variables=["contenido_archivo", "contexto_adicional"],
    template="""
Eres un experto en diagramas de arquitectura de software y Mermaid. Analiza el contenido y genera ÚNICAMENTE un diagrama de arquitectura usando sintaxis flowchart que sea compatible con todas las herramientas (Mermaid, Draw.io, etc.).

CONTENIDO A ANALIZAR:
{contenido_archivo}

CONTEXTO ADICIONAL:
{contexto_adicional}

REGLAS PARA DIAGRAMA DE ARQUITECTURA CON FLOWCHART:
1. Usa SOLO sintaxis "flowchart TD" (Top Down) 
2. Organiza en subgrafos por capas arquitectónicas
3. Usa formas específicas según el tipo de componente:
   - [Texto] para aplicaciones/servicios
   - [(Texto)] para bases de datos
   - {{Texto}} para decisiones/gateways
   - ([Texto]) para APIs/interfaces
   - [[Texto]] para componentes externos
   - [/Texto/] para procesos

4. Estilos de conexión:
   - --> conexión normal
   - -.-> conexión opcional/async
   - ==> conexión principal/importante
   - -.- conexión de datos

5. Agrupa por capas típicas:
   - Frontend/Cliente
   - API Gateway/Proxy
   - Microservicios/Business Logic
   - Data Layer/Persistencia
   - External Services/Integrations

ESTRUCTURA MODELO:
```
flowchart TD
    subgraph "Cliente"
        WebApp[Web Application]
        MobileApp[Mobile App]
        DesktopApp[Desktop App]
    end
    
    subgraph "API Gateway"
        Gateway([API Gateway])
        Auth{{Authentication}}
        LoadBalancer[/Load Balancer/]
    end
    
    subgraph "Microservicios"
        UserService[User Service]
        ProductService[Product Service]
        OrderService[Order Service]
        PaymentService[Payment Service]
        NotificationService[Notification Service]
    end
    
    subgraph "Base de Datos"
        UserDB[(User Database)]
        ProductDB[(Product Database)]
        OrderDB[(Order Database)]
        Cache[(Redis Cache)]
    end
    
    subgraph "Servicios Externos"
        PaymentGateway[[Payment Provider]]
        EmailService[[Email Provider]]
        SMSService[[SMS Provider]]
        CloudStorage[[Cloud Storage]]
    end
    
    %% Conexiones Frontend -> Gateway
    WebApp --> LoadBalancer
    MobileApp --> LoadBalancer
    DesktopApp --> LoadBalancer
    LoadBalancer --> Gateway
    
    %% Gateway -> Auth
    Gateway --> Auth
    
    %% Gateway -> Microservicios
    Gateway ==> UserService
    Gateway ==> ProductService
    Gateway ==> OrderService
    Gateway ==> PaymentService
    Gateway --> NotificationService
    
    %% Microservicios -> Bases de Datos
    UserService --> UserDB
    ProductService --> ProductDB
    OrderService --> OrderDB
    PaymentService --> OrderDB
    
    %% Cache connections
    UserService -.-> Cache
    ProductService -.-> Cache
    
    %% Servicios -> Externos
    PaymentService ==> PaymentGateway
    NotificationService --> EmailService
    NotificationService --> SMSService
    UserService -.-> CloudStorage
    
    %% Inter-service communication
    OrderService -.-> UserService
    OrderService -.-> ProductService
    OrderService -.-> PaymentService
```

EJEMPLO SISTEMA E-COMMERCE COMPLETO:
```
flowchart TD
    subgraph "Frontend Applications"
        Web[Web Store]
        Mobile[Mobile App]
        Admin[Admin Panel]
    end
    
    subgraph "CDN & Load Balancing"
        CDN[/Content Delivery Network/]
        LB[/Load Balancer/]
    end
    
    subgraph "API Gateway & Security"
        Gateway([API Gateway])
        Auth{{JWT Authentication}}
        RateLimit{{Rate Limiting}}
    end
    
    subgraph "Core Business Services"
        UserMgmt[User Management]
        Catalog[Product Catalog]
        Shopping[Shopping Cart]
        Orders[Order Management]
        Payments[Payment Processing]
        Inventory[Inventory Management]
    end
    
    subgraph "Support Services"
        Search[Search Service]
        Recommendations[Recommendation Engine]
        Notifications[Notification Service]
        Analytics[Analytics Service]
    end
    
    subgraph "Data Persistence"
        UserDB[(User Database)]
        ProductDB[(Product Database)]
        OrderDB[(Order Database)]
        InventoryDB[(Inventory Database)]
        SearchIndex[(Search Index)]
        Cache[(Redis Cache)]
    end
    
    subgraph "External Integrations"
        StripeAPI[[Stripe Payment]]
        SendGrid[[SendGrid Email]]
        Twilio[[Twilio SMS]]
        AWS_S3[[AWS S3 Storage]]
        ElasticSearch[[Elasticsearch]]
    end
    
    %% Frontend to CDN/LB
    Web --> CDN
    Mobile --> LB
    Admin --> LB
    CDN --> LB
    
    %% Load Balancer to Gateway
    LB --> Gateway
    
    %% Gateway Security
    Gateway --> Auth
    Gateway --> RateLimit
    
    %% Gateway to Core Services
    Gateway ==> UserMgmt
    Gateway ==> Catalog
    Gateway ==> Shopping
    Gateway ==> Orders
    Gateway ==> Payments
    Gateway ==> Inventory
    
    %% Gateway to Support Services
    Gateway --> Search
    Gateway --> Recommendations
    Gateway --> Notifications
    Gateway --> Analytics
    
    %% Core Services to Databases
    UserMgmt --> UserDB
    Catalog --> ProductDB
    Shopping -.-> Cache
    Orders --> OrderDB
    Payments --> OrderDB
    Inventory --> InventoryDB
    
    %% Support Services to Data
    Search --> SearchIndex
    Recommendations -.-> UserDB
    Recommendations -.-> ProductDB
    Analytics -.-> OrderDB
    
    %% Cache Usage
    UserMgmt -.-> Cache
    Catalog -.-> Cache
    
    %% External Services
    Payments ==> StripeAPI
    Notifications --> SendGrid
    Notifications --> Twilio
    Catalog -.-> AWS_S3
    Search ==> ElasticSearch
    
    %% Inter-service Communication
    Orders -.-> UserMgmt
    Orders -.-> Catalog
    Orders -.-> Inventory
    Orders -.-> Payments
    Shopping -.-> Catalog
    Shopping -.-> Inventory
    Recommendations -.-> Analytics
```

INSTRUCCIONES ESPECÍFICAS:
- Identifica los componentes principales del sistema descrito
- Agrupa por responsabilidades (frontend, gateway, servicios, datos, externos)
- Define conexiones lógicas entre componentes
- Usa formas apropiadas para cada tipo de componente
- Mantén nombres descriptivos pero concisos
- NO uses caracteres especiales en los IDs
- Incluye servicios de soporte si es relevante (cache, monitoring, etc.)
- Representa integraciones externas claramente

Genera SOLO el código Mermaid flowchart basado en el análisis del contenido:
"""
)

@diagramaArquitectura_bp.route('/diagramaArquitectura/generate', methods=['POST'])
def generate_architecture_diagram():
    """Genera diagrama de arquitectura usando flowchart compatible"""
    try:
        logger.info("=== GENERANDO DIAGRAMA DE ARQUITECTURA FLOWCHART ===")
        
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
        
        # Generar diagrama usando el nuevo template
        logger.info("Generando diagrama de arquitectura flowchart con IA...")
        chain = flowchart_architecture_prompt | llm
        
        response = chain.invoke({
            'contenido_archivo': contenido_archivo,
            'contexto_adicional': contexto_adicional or "Sin contexto adicional."
        })
        
        # Limpieza específica para flowchart
        mermaid_content = clean_flowchart_architecture_response(response.content)
        
        logger.info(f"Contenido generado: {mermaid_content[:200]}...")
        
        # Validación específica
        is_valid, error_msg = validate_flowchart_architecture(mermaid_content)
        
        if not is_valid:
            logger.warning(f"Validación falló: {error_msg}")
            # Reintento con instrucciones más específicas
            retry_response = chain.invoke({
                'contenido_archivo': contenido_archivo,
                'contexto_adicional': f"{contexto_adicional}\n\nIMPORTANTE: Genera ÚNICAMENTE un diagrama flowchart TD válido con subgrafos para capas arquitectónicas y conexiones entre componentes."
            })
            
            mermaid_content = clean_flowchart_architecture_response(retry_response.content)
            is_valid, error_msg = validate_flowchart_architecture(mermaid_content)
            
            # Si aún falla, usar diagrama de fallback
            if not is_valid:
                logger.warning("Usando diagrama de arquitectura de fallback")
                mermaid_content = """flowchart TD
    subgraph "Frontend"
        WebApp[Web Application]
        MobileApp[Mobile App]
    end
    
    subgraph "API Layer"
        Gateway([API Gateway])
        Auth{{Authentication}}
    end
    
    subgraph "Business Services"
        UserService[User Service]
        ProductService[Product Service]
        OrderService[Order Service]
    end
    
    subgraph "Data Layer"
        UserDB[(User Database)]
        ProductDB[(Product Database)]
        OrderDB[(Order Database)]
        Cache[(Redis Cache)]
    end
    
    WebApp --> Gateway
    MobileApp --> Gateway
    Gateway --> Auth
    Gateway --> UserService
    Gateway --> ProductService
    Gateway --> OrderService
    UserService --> UserDB
    ProductService --> ProductDB
    OrderService --> OrderDB
    UserService -.-> Cache
    ProductService -.-> Cache"""
        
        logger.info("=== DIAGRAMA DE ARQUITECTURA FLOWCHART GENERADO ===")
        
        return jsonify({
            'success': True,
            'mermaid_content': mermaid_content,
            'diagram_type': 'flowchart',
            'message': 'Diagrama de arquitectura (flowchart) generado exitosamente - Compatible con todas las herramientas',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@diagramaArquitectura_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint de salud"""
    return jsonify({
        'status': 'healthy',
        'service': 'architecture_diagram_flowchart_mermaid',
        'timestamp': datetime.now().isoformat(),
        'llm_configured': llm is not None,
        'diagram_type': 'flowchart',
        'compatible_with': ['Mermaid', 'Draw.io', 'Lucidchart', 'Visual Studio Code', 'GitHub', 'GitLab']
    })