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
diagramaTecnologia_bp = Blueprint('generador_diagramas_tecnologia_gcp', __name__)

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

def clean_flowchart_tech_response(content):
    """Limpieza específica para diagramas tecnológicos tipo GCP/Cloud"""
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
    
    # Limpiar caracteres problemáticos pero mantener iconos y tecnologías
    lines = content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        if line.strip().startswith('flowchart') or line.strip().startswith('subgraph') or line.strip().startswith('end') or line.strip().startswith('%'):
            cleaned_lines.append(line)
        elif line.strip() and not line.strip().startswith('%%'):
            # Permitir caracteres especiales para iconos y tecnologías cloud
            line = re.sub(r'[^\w\s\-_+()[\]{}<>=.:/"\\|&@]', '', line)
            cleaned_lines.append(line)
        else:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines).strip()

def validate_tech_diagram(content):
    """Validación específica para diagramas tecnológicos"""
    content = content.strip()
    if not content:
        return False, "Contenido vacío"
    
    if not content.startswith('flowchart'):
        return False, "Debe empezar con 'flowchart TD' o 'flowchart LR'"
    
    lines = content.split('\n')
    if len(lines) < 5:
        return False, "El diagrama debe tener componentes tecnológicos suficientes"
    
    # Verificar que tenga subgrafos de capas tecnológicas
    has_subgraph = any('subgraph' in line for line in lines)
    if not has_subgraph:
        return False, "Diagrama tecnológico debe tener subgrafos por capas"
    
    # Verificar que tenga conexiones tecnológicas
    has_connections = any('-->' in line or '-.>' in line or '==>' in line for line in lines)
    if not has_connections:
        return False, "Diagrama debe tener conexiones entre componentes"
    
    return True, None

# Template para diagramas tecnológicos estilo GCP/Cloud
tech_diagram_prompt = PromptTemplate(
    input_variables=["contenido_archivo", "contexto_adicional"],
    template="""
Eres un experto en arquitecturas tecnológicas cloud (GCP, AWS, Azure) y diagramas Mermaid. Analiza el contenido y genera un diagrama tecnológico detallado usando sintaxis flowchart que represente la infraestructura y servicios cloud.

CONTENIDO A ANALIZAR:
{contenido_archivo}

CONTEXTO ADICIONAL:
{contexto_adicional}

REGLAS PARA DIAGRAMA TECNOLÓGICO CLOUD:
1. Usa SOLO sintaxis "flowchart TD" (Top Down)
2. Organiza por capas tecnológicas típicas de cloud:
   - App Layer (Frontend/Cliente)
   - Security Layer (IAM, Auth, Firewall)
   - API Gateway/Load Balancer
   - Compute Layer (GKE, Cloud Run, VMs)
   - Data Layer (Cloud SQL, Firestore, BigQuery)
   - Storage Layer (Cloud Storage, Redis)
   - External Services/Third Party
   - On-Premise (si aplica)

3. Usa formas específicas por tipo de tecnología:
   - [Aplicación Web] para frontend
   - ([API Gateway]) para gateways
   - {{Load Balancer}} para balanceadores
   - [(Base de Datos)] para databases
   - [[Servicio Externo]] para third party
   - [/Kubernetes Pod/] para containers
   - ((Cache)) para sistemas de cache

4. Incluye detalles técnicos:
   - Nombres de servicios específicos (GKE, Cloud SQL, etc.)
   - Versiones de tecnologías (Java 21, SpringBoot, PostgreSQL 15)
   - Puertos y protocolos (HTTPS:443, TCP:5432)
   - IPs y DNS cuando sea relevante

5. Estilos de conexión tecnológica:
   - --> conexión HTTP/HTTPS
   - -.-> conexión asíncrona/opcional
   - ==> conexión principal/crítica
   - -.- conexión de datos/base de datos

ESTRUCTURA MODELO BASADA EN TU DIAGRAMA GCP:
```
flowchart TD
    subgraph "App Layer"
        WebAngular[Web Angular 17<br/>Space Planner]
    end
    
    subgraph "Security Layer"
        CloudArmor[Cloud Armor<br/>Web Application Firewall]
        CloudIAM[Cloud IAM<br/>Identity & Access Management]
    end
    
    subgraph "Load Balancing & Gateway"
        IngressExt[Ingress Externo<br/>0.0.0.0:443]
        LoadBalancer[/Load Balancer<br/>HTTPS:443/]
    end
    
    subgraph "GCP - Google Cloud Platform"
        subgraph "Compute - GKE Clusters"
            GKEProd[GKE prod-01<br/>IP: 0.0.0.0/17]
            GKEApp[GKE gke-app-prod-01<br/>IP: 0.0.0.0/17]
            
            subgraph "Microservices"
                SiteManagement[ds-psm-pslm-SiteManagement<br/>JDK 21 - SpringBoot<br/>REST Service]
                FixturesService[ds-psm-fxm-Fixtures<br/>JDK 21 - SpringBoot<br/>REST Service]
                LayoutUserMgmt[es-psm-LayoutUserManagement<br/>JDK 21 - SpringBoot<br/>REST Service]
                LayoutsService[ds-psm-pslm-Layouts<br/>JDK 21 - SpringBoot<br/>REST Service]
                ReportsService[ps-psm-pslm-GenerateReports<br/>JDK 21 - SpringBoot<br/>REST Service]
                BatchingService[ps-psm-pslm-StoreBatching<br/>JDK 21 - SpringBoot<br/>REST Service]
                PhysicalOps[ps-psm-stope-PhysicalStoreOperations<br/>JDK 21 - SpringBoot<br/>REST Service]
            end
        end
        
        subgraph "Data Layer"
            CloudSpanner[Cloud Spanner<br/>spaceplanner-01]
        end
    end
    
    subgraph "On-Premise"
        PostgresDB[(PostgreSQL 15<br/>sisexhibicionweb<br/>DNS: N/A<br/>0.0.0.0:5432)]
        SpacePlannerDB[(PostgreSQL 15<br/>spaceplanner<br/>DNS: coppel.com<br/>User: sysspaceplanner<br/>Privileges: Lectura y Escritura)]
    end
    
    subgraph "Third Party Integrations"
        ApigeeGW[Apigee Platform<br/>API Management]
        PartyIdentity[Party Identity<br/>External Service]
    end
    
    %% Frontend Flow
    WebAngular --> IngressExt
    
    %% Security Layer
    IngressExt --> CloudArmor
    IngressExt --> CloudIAM
    
    %% Load Balancing
    IngressExt --> LoadBalancer
    LoadBalancer --> GKEProd
    LoadBalancer --> GKEApp
    
    %% Microservices in GKE
    GKEProd --> SiteManagement
    GKEProd --> FixturesService
    GKEProd --> LayoutUserMgmt
    GKEApp --> LayoutsService
    GKEApp --> ReportsService
    GKEApp --> BatchingService
    GKEApp --> PhysicalOps
    
    %% Database Connections
    LayoutsService --> CloudSpanner
    ReportsService --> SpacePlannerDB
    BatchingService --> SpacePlannerDB
    PhysicalOps --> SpacePlannerDB
    SiteManagement --> PostgresDB
    FixturesService --> PostgresDB
    LayoutUserMgmt --> PostgresDB
    
    %% External Integrations
    WebAngular -.-> ApigeeGW
    ApigeeGW --> PartyIdentity
    
    %% Inter-service Communication
    LayoutsService -.-> SiteManagement
    ReportsService -.-> LayoutsService
    BatchingService -.-> PhysicalOps
```

EJEMPLO COMPLETO TECNOLÓGICO GCP:
```
flowchart TD
    subgraph "Client Applications"
        WebApp[Angular 17 SPA<br/>coppel.com<br/>Space Planner]
        MobileApp[React Native App<br/>iOS/Android]
        DesktopApp[Electron Desktop<br/>Windows/Mac/Linux]
    end
    
    subgraph "Security & Edge"
        CloudCDN[Cloud CDN<br/>Global Edge Cache]
        CloudArmor[Cloud Armor<br/>DDoS Protection & WAF]
        CloudIAM[Cloud IAM<br/>Identity Management]
        SSLCerts[SSL Certificates<br/>Let's Encrypt]
    end
    
    subgraph "Load Balancing & Gateway"
        HttpsLB[HTTPS Load Balancer<br/>Global - 0.0.0.0:443]
        IngressGateway[Ingress Gateway<br/>Istio Service Mesh]
        APIGateway([Cloud Endpoints<br/>API Gateway])
    end
    
    subgraph "Google Cloud Platform - Production"
        subgraph "Compute Engine"
            GKECluster[GKE Cluster prod-01<br/>Kubernetes 1.28<br/>10.0.0.0/16]
            
            subgraph "Business Services Pod"
                UserMgmt[User Management<br/>JDK 21 + SpringBoot 3.2<br/>Port: 8080]
                ProductCatalog[Product Catalog<br/>JDK 21 + SpringBoot 3.2<br/>Port: 8081]
                OrderMgmt[Order Management<br/>JDK 21 + SpringBoot 3.2<br/>Port: 8082]
                InventoryMgmt[Inventory Management<br/>JDK 21 + SpringBoot 3.2<br/>Port: 8083]
            end
            
            subgraph "Support Services Pod"
                SearchService[Search Service<br/>Elasticsearch + Spring<br/>Port: 9200]
                NotificationSvc[Notification Service<br/>JDK 21 + Kafka<br/>Port: 8084]
                AnalyticsSvc[Analytics Service<br/>Python + FastAPI<br/>Port: 8000]
            end
        end
        
        subgraph "Data Services"
            CloudSQL[(Cloud SQL PostgreSQL 15<br/>Regional HA<br/>db-prod-01<br/>10.1.0.0/24)]
            CloudFirestore[(Cloud Firestore<br/>Document Database<br/>Native Mode)]
            CloudSpanner[(Cloud Spanner<br/>Global Database<br/>Multi-region)]
            CloudBigQuery[(BigQuery<br/>Data Warehouse<br/>Analytics)]
        end
        
        subgraph "Storage & Cache"
            CloudStorage[[Cloud Storage<br/>Multi-regional Bucket<br/>gs://prod-assets]]
            MemoryStore((Cloud Memorystore<br/>Redis 7.0<br/>6GB - HA))
            PubSub[/Cloud Pub/Sub<br/>Message Queue<br/>Async Processing/]
        end
        
        subgraph "Monitoring & Operations"
            CloudLogging[Cloud Logging<br/>Centralized Logs]
            CloudMonitoring[Cloud Monitoring<br/>Metrics & Alerting]
            CloudTrace[Cloud Trace<br/>Distributed Tracing]
        end
    end
    
    subgraph "External Services"
        StripeAPI[[Stripe Payment API<br/>payments.stripe.com<br/>HTTPS:443]]
        SendGridAPI[[SendGrid Email API<br/>api.sendgrid.com<br/>HTTPS:443]]
        TwilioAPI[[Twilio SMS API<br/>api.twilio.com<br/>HTTPS:443]]
        Auth0[[Auth0 Identity<br/>tenant.auth0.com<br/>OAuth 2.0]]
    end
    
    subgraph "On-Premise Legacy"
        OracleDB[(Oracle Database 19c<br/>legacy-db.company.com<br/>Port: 1521)]
        MainframeAS400[IBM AS/400<br/>Mainframe System<br/>SNA Connection]
        FileServer[Windows File Server<br/>\\fileserver\shared<br/>SMB/CIFS]
    end
    
    %% Client to Edge
    WebApp --> CloudCDN
    MobileApp --> HttpsLB
    DesktopApp --> HttpsLB
    CloudCDN --> HttpsLB
    
    %% Security Layer
    HttpsLB --> CloudArmor
    HttpsLB --> SSLCerts
    CloudArmor --> CloudIAM
    
    %% Gateway Layer
    HttpsLB ==> IngressGateway
    IngressGateway --> APIGateway
    
    %% API Gateway to Services
    APIGateway ==> UserMgmt
    APIGateway ==> ProductCatalog
    APIGateway ==> OrderMgmt
    APIGateway ==> InventoryMgmt
    APIGateway --> SearchService
    APIGateway --> NotificationSvc
    APIGateway --> AnalyticsSvc
    
    %% Services to Databases
    UserMgmt --> CloudSQL
    ProductCatalog --> CloudSQL
    OrderMgmt --> CloudSpanner
    InventoryMgmt --> CloudFirestore
    SearchService --> CloudSQL
    AnalyticsSvc --> CloudBigQuery
    
    %% Cache Connections
    UserMgmt -.-> MemoryStore
    ProductCatalog -.-> MemoryStore
    OrderMgmt -.-> MemoryStore
    
    %% Storage Connections
    ProductCatalog --> CloudStorage
    UserMgmt --> CloudStorage
    
    %% Async Processing
    NotificationSvc --> PubSub
    AnalyticsSvc --> PubSub
    OrderMgmt -.-> PubSub
    
    %% External API Integrations
    OrderMgmt ==> StripeAPI
    NotificationSvc --> SendGridAPI
    NotificationSvc --> TwilioAPI
    UserMgmt ==> Auth0
    
    %% Legacy System Connections
    OrderMgmt -.-> OracleDB
    InventoryMgmt -.-> MainframeAS400
    UserMgmt -.-> FileServer
    
    %% Monitoring
    GKECluster -.-> CloudLogging
    GKECluster -.-> CloudMonitoring
    GKECluster -.-> CloudTrace
    
    %% Inter-service Communication
    OrderMgmt -.-> UserMgmt
    OrderMgmt -.-> ProductCatalog
    OrderMgmt -.-> InventoryMgmt
    AnalyticsSvc -.-> OrderMgmt
    SearchService -.-> ProductCatalog
```

INSTRUCCIONES ESPECÍFICAS:
- Identifica tecnologías específicas mencionadas (GCP, Kubernetes, PostgreSQL, etc.)
- Incluye versiones de software cuando estén disponibles
- Especifica puertos, protocolos y configuraciones de red
- Organiza por capas tecnológicas lógicas
- Incluye servicios de infraestructura (monitoring, logging, etc.)
- Representa integraciones on-premise y cloud
- Usa nombres técnicos reales de servicios cloud
- Incluye detalles de configuración relevantes (IPs, DNS, etc.)
- Representa microservicios con sus tecnologías específicas

Genera SOLO el código Mermaid flowchart tecnológico basado en el análisis del contenido:
"""
)

@diagramaTecnologia_bp.route('/diagramaTecnologia/generate', methods=['POST'])
def generate_technology_diagram():
    """Genera diagrama tecnológico detallado estilo GCP/Cloud"""
    try:
        logger.info("=== GENERANDO DIAGRAMA TECNOLÓGICO CLOUD ===")
        
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
            contenido_archivo = "Información tecnológica proporcionada por el usuario."
        
        # Generar diagrama tecnológico
        logger.info("Generando diagrama tecnológico cloud con IA...")
        chain = tech_diagram_prompt | llm
        
        response = chain.invoke({
            'contenido_archivo': contenido_archivo,
            'contexto_adicional': contexto_adicional or "Sin contexto adicional tecnológico."
        })
        
        # Limpieza específica para diagramas tecnológicos
        mermaid_content = clean_flowchart_tech_response(response.content)
        
        logger.info(f"Contenido tecnológico generado: {mermaid_content[:200]}...")
        
        # Validación específica
        is_valid, error_msg = validate_tech_diagram(mermaid_content)
        
        if not is_valid:
            logger.warning(f"Validación falló: {error_msg}")
            # Reintento con instrucciones más específicas
            retry_response = chain.invoke({
                'contenido_archivo': contenido_archivo,
                'contexto_adicional': f"{contexto_adicional}\n\nIMPORTANTE: Genera ÚNICAMENTE un diagrama flowchart TD tecnológico válido con capas cloud específicas y tecnologías detalladas."
            })
            
            mermaid_content = clean_flowchart_tech_response(retry_response.content)
            is_valid, error_msg = validate_tech_diagram(mermaid_content)
            
            # Si aún falla, usar diagrama tecnológico de fallback
            if not is_valid:
                logger.warning("Usando diagrama tecnológico de fallback")
                mermaid_content = """flowchart TD
    subgraph "Client Layer"
        WebApp[Angular 17 SPA<br/>Frontend Application]
        MobileApp[React Native<br/>Mobile App]
    end
    
    subgraph "Security & Gateway"
        CloudArmor[Cloud Armor<br/>WAF Protection]
        LoadBalancer[/Load Balancer<br/>HTTPS:443/]
        APIGateway([API Gateway<br/>Traffic Management])
    end
    
    subgraph "Google Cloud Platform"
        subgraph "Compute"
            GKECluster[GKE Cluster<br/>Kubernetes 1.28]
            SpringBootApp[SpringBoot Services<br/>JDK 21]
            NodeJSApp[Node.js Services<br/>v18 LTS]
        end
        
        subgraph "Data Layer"
            CloudSQL[(Cloud SQL<br/>PostgreSQL 15)]
            CloudStorage[[Cloud Storage<br/>File Storage]]
            Redis((Cloud Memorystore<br/>Redis Cache))
        end
    end
    
    subgraph "External Services"
        ThirdPartyAPI[[Third Party APIs<br/>REST/GraphQL]]
    end
    
    WebApp --> LoadBalancer
    MobileApp --> LoadBalancer
    LoadBalancer --> CloudArmor
    LoadBalancer --> APIGateway
    APIGateway --> GKECluster
    GKECluster --> SpringBootApp
    GKECluster --> NodeJSApp
    SpringBootApp --> CloudSQL
    NodeJSApp --> CloudStorage
    SpringBootApp -.-> Redis
    APIGateway -.-> ThirdPartyAPI"""
        
        logger.info("=== DIAGRAMA TECNOLÓGICO CLOUD GENERADO ===")
        
        return jsonify({
            'success': True,
            'mermaid_content': mermaid_content,
            'diagram_type': 'technology_cloud',
            'message': 'Diagrama tecnológico cloud generado exitosamente - Detalle de infraestructura y servicios',
            'timestamp': datetime.now().isoformat(),
            'tech_focus': 'Cloud Infrastructure, Microservices, Data Layer, Security'
        })
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@diagramaTecnologia_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint de salud para diagrama tecnológico"""
    return jsonify({
        'status': 'healthy',
        'service': 'technology_diagram_cloud_mermaid',
        'timestamp': datetime.now().isoformat(),
        'llm_configured': llm is not None,
        'diagram_type': 'technology_cloud',
        'supported_platforms': ['GCP', 'AWS', 'Azure', 'Kubernetes', 'Docker'],
        'tech_components': ['Microservices', 'Databases', 'Cache', 'Load Balancers', 'API Gateways', 'Security'],
        'compatible_with': ['Mermaid', 'Draw.io', 'Lucidchart', 'Visual Studio Code', 'GitHub', 'GitLab']
    })