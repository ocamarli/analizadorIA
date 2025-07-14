from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import io
import PyPDF2
import xml.etree.ElementTree as ET
import re
from langchain_community.chat_models import AzureChatOpenAI
from langchain.prompts import PromptTemplate

# Blueprint
generar_arquitectura_tobe_bp = Blueprint('generador_arquitectura_tobe', __name__)

# Configuración de LangChain
llm = AzureChatOpenAI(
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1"),
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
    openai_api_key=os.getenv("AZURE_OPENAI_API_KEY", "6076ii7OpLiuTEKYsEVvWyt57RYjzb8d4hDwZRqKuokBi1WTuKz9JQQJ99AJACYeBjFXJ3w3AAABACOGfwuS"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://openaidemobside.openai.azure.com"),
    temperature=0.7
)

@generar_arquitectura_tobe_bp.route('/generar-arquitectura-tobe', methods=['POST'])
def generar_arquitectura_tobe():
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
            elif file.filename.lower().endswith(('.xml', '.drawio')):
                file.seek(0)
                texto_archivo = file.read().decode('utf-8')
                drawio_info = extraer_info_drawio(texto_archivo)
                if drawio_info.strip():
                    texto_completo += drawio_info + "\n\n"
                    archivos_procesados += 1
            elif file.filename.lower().endswith('.mmd'):
                file.seek(0)
                texto_archivo = file.read().decode('utf-8')
                if texto_archivo.strip():
                    texto_completo += f"=== DIAGRAMA MERMAID ===\n{texto_archivo}\n\n"
                    archivos_procesados += 1
            elif file.filename.lower().endswith('.txt'):
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
                texto_completo += "\n=== ESPECIFICACIONES PARA ARQUITECTURA TO BE ===\n"
            texto_completo += additional_text + "\n\n"
        
        # Validar que se haya extraído algún contenido
        if not texto_completo.strip():
            return jsonify({"error": "No se pudo extraer texto de los archivos y no se proporcionó texto adicional"}), 400
        
        # Generar arquitectura TO BE con IA
        respuesta_ia = generar_arquitectura_tobe(texto_completo)
        
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

def extraer_info_drawio(xml_content):
    """Extrae información relevante de un archivo Draw.io XML"""
    try:
        root = ET.fromstring(xml_content)
        
        info_extraida = "=== INFORMACIÓN DE DIAGRAMA DRAW.IO ===\n"
        
        # Buscar elementos con texto
        elementos_texto = []
        for elem in root.iter():
            if elem.get('value'):
                texto = elem.get('value')
                if texto and texto.strip():
                    elementos_texto.append(texto.strip())
        
        if elementos_texto:
            info_extraida += "\nElementos y etiquetas del diagrama:\n"
            for texto in elementos_texto:
                info_extraida += f"- {texto}\n"
        
        return info_extraida
        
    except Exception as e:
        return f"Error procesando Draw.io XML: {str(e)}"

def generar_arquitectura_tobe(texto_documento):
    """Genera arquitectura TO BE de software usando IA"""
    
    fecha_actual = datetime.now().strftime('%d/%m/%Y')
    
    prompt_template = PromptTemplate(
        input_variables=["documento", "fecha"],
        template="""
Eres un arquitecto de software senior especializado en diseño de arquitecturas objetivo (TO BE). Tu tarea es analizar la documentación proporcionada (que puede incluir análisis AS IS previos) y las especificaciones de migración/nuevas tecnologías para generar un diseño completo de arquitectura TO BE en formato Markdown.

DOCUMENTACIÓN Y ESPECIFICACIONES PROPORCIONADAS:
{documento}

INSTRUCCIONES CRÍTICAS:
1. ANALIZA completamente la documentación AS IS si está disponible
2. IDENTIFICA las especificaciones de tecnologías objetivo en el texto adicional
3. DISEÑA una arquitectura TO BE basada en las mejores prácticas y tecnologías especificadas
4. MANTÉN la funcionalidad existente mientras migras a las nuevas tecnologías
5. PROPÓN mejoras arquitectónicas aprovechando las nuevas tecnologías
6. INCLUYE plan de migración del AS IS al TO BE
7. MANTÉN formato Markdown estricto y profesional

GENERAR EL SIGUIENTE DISEÑO DE ARQUITECTURA TO BE EN MARKDOWN:

---

# Arquitectura TO BE - Diseño de Arquitectura Objetivo

**Proyecto:** [Extraer nombre del proyecto del documento]

**Fecha del Diseño:** {fecha}

**Versión:** 1.0

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Arquitectura TO BE General](#arquitectura-to-be-general)
3. [Componentes del Sistema TO BE](#componentes-del-sistema-to-be)
4. [Stack Tecnológico TO BE](#stack-tecnológico-to-be)
5. [Patrones Arquitectónicos TO BE](#patrones-arquitectónicos-to-be)
6. [Integraciones y APIs TO BE](#integraciones-y-apis-to-be)
7. [Gestión de Datos TO BE](#gestión-de-datos-to-be)
8. [Seguridad TO BE](#seguridad-to-be)
9. [Escalabilidad y Rendimiento TO BE](#escalabilidad-y-rendimiento-to-be)
10. [Infraestructura y Despliegue TO BE](#infraestructura-y-despliegue-to-be)
11. [Plan de Migración AS IS → TO BE](#plan-de-migración-as-is--to-be)
12. [Recomendaciones de Implementación](#recomendaciones-de-implementación)

---

## Resumen Ejecutivo

[Describir el objetivo de la arquitectura TO BE, tecnologías objetivo, mejoras esperadas y beneficios de la migración]

**Tipo de Arquitectura TO BE:** [Monolítica/Microservicios/SOA/Serverless/etc.]

**Tecnologías Objetivo:**
- Frontend: [Especificar tecnologías TO BE]
- Backend: [Especificar tecnologías TO BE]
- Base de Datos: [Especificar bases de datos TO BE]
- Cloud/Infraestructura: [Especificar infraestructura TO BE]

**Mejoras Principales del TO BE:**
[Listar las 3-5 mejoras más importantes que aporta la nueva arquitectura]

**Beneficios Esperados:**
- [Beneficio 1: mejora en rendimiento, escalabilidad, etc.]
- [Beneficio 2: reducción de costos, mantenimiento, etc.]
- [Beneficio 3: nuevas capacidades, integración, etc.]

---

## Arquitectura TO BE General

### Visión General de la Arquitectura Objetivo
[Describir la nueva arquitectura propuesta, sus características principales y cómo difiere del AS IS]

### Principios de Diseño TO BE
[Listar principios que guían la nueva arquitectura]

1. **[Principio 1]:** [Descripción y justificación]
2. **[Principio 2]:** [Descripción y justificación]
3. **[Principio 3]:** [Descripción y justificación]

### Capas del Sistema TO BE
[Definir las capas de la nueva arquitectura]

| **Capa** | **Tecnología TO BE** | **Responsabilidad** | **Mejora vs AS IS** |
|----------|---------------------|-------------------|-----------------|
| [Definir capas TO BE] | [Especificar tecnologías] | [Definir responsabilidades] | [Explicar mejoras] |

---

## Componentes del Sistema TO BE

### Componentes Principales TO BE
[Definir componentes de la nueva arquitectura]

| **Componente TO BE** | **Función** | **Tecnología** | **Nuevas Capacidades** |
|---------------------|-------------|----------------|----------------------|
| [Definir componentes] | [Especificar funciones] | [Especificar tecnologías] | [Listar capacidades nuevas] |

### Servicios TO BE
[Definir servicios en la nueva arquitectura]

### Microservicios/Módulos TO BE
[Si aplica, definir microservicios o módulos específicos]

| **Servicio** | **Responsabilidad** | **API** | **Base de Datos** |
|--------------|-------------------|---------|------------------|
| [Definir servicios] | [Especificar responsabilidades] | [Definir APIs] | [Especificar BD] |

---

## Stack Tecnológico TO BE

### Stack Completo de la Arquitectura Objetivo

**Frontend TO BE:**
- [Framework/librería principal: React, Angular, Vue, etc.]
- [Herramientas de build: Vite, Webpack, etc.]
- [Librerías de UI: Material-UI, Ant Design, etc.]
- [Estado: Redux, Zustand, Context API, etc.]

**Backend TO BE:**
- [Lenguaje: Node.js, Python, Java, .NET, etc.]
- [Framework: Express, FastAPI, Spring Boot, etc.]
- [API: REST, GraphQL, gRPC, etc.]
- [Servidor: Nginx, Apache, IIS, etc.]

**Base de Datos TO BE:**
- [BD Principal: PostgreSQL, MySQL, MongoDB, etc.]
- [Cache: Redis, Memcached, etc.]
- [Search Engine: Elasticsearch, Solr, etc.]
- [Data Warehouse: si aplica]

**DevOps y Herramientas TO BE:**
- [Contenedores: Docker, Podman, etc.]
- [Orquestación: Kubernetes, Docker Swarm, etc.]
- [CI/CD: Jenkins, GitHub Actions, GitLab CI, etc.]
- [IaC: Terraform, CloudFormation, etc.]

**Cloud TO BE:**
- [Proveedor: AWS, Azure, GCP, etc.]
- [Servicios específicos utilizados]
- [Servicios managed vs self-hosted]

**Monitoreo TO BE:**
- [APM: New Relic, Datadog, Dynatrace, etc.]
- [Logging: ELK Stack, Fluentd, etc.]
- [Métricas: Prometheus, Grafana, etc.]

---

## Patrones Arquitectónicos TO BE

### Patrones Implementados en TO BE
[Definir patrones arquitectónicos para la nueva arquitectura]

| **Patrón TO BE** | **Implementación** | **Beneficio** | **Herramientas** |
|-----------------|-------------------|---------------|------------------|
| [Especificar patrones] | [Describir implementación] | [Explicar beneficios] | [Listar herramientas] |

### Mejores Prácticas TO BE
[Listar mejores prácticas implementadas]

---

## Integraciones y APIs TO BE

### APIs TO BE
[Definir APIs de la nueva arquitectura]

| **API TO BE** | **Protocolo** | **Propósito** | **Seguridad** | **Versionado** |
|--------------|---------------|---------------|---------------|----------------|
| [Definir APIs] | [REST/GraphQL/gRPC] | [Especificar propósitos] | [Definir seguridad] | [Estrategia versioning] |

### Integraciones Externas TO BE
[Definir integraciones con sistemas externos]

| **Sistema Externo** | **Protocolo TO BE** | **Tipo de Integración** | **Datos** | **Autenticación** |
|-------------------|-------------------|------------------------|-----------|------------------|
| [Listar sistemas] | [Especificar protocolos] | [Definir tipos] | [Especificar datos] | [Definir auth] |

### Event-Driven Architecture (si aplica)
[Si la arquitectura TO BE incluye eventos, definir la estrategia]

---

## Gestión de Datos TO BE

### Modelo de Datos TO BE
[Definir modelo de datos de la nueva arquitectura]

**Entidades Principales TO BE:**
[Listar entidades principales con sus mejoras]

### Estrategia de Almacenamiento TO BE
[Definir estrategias de almacenamiento]

| **Tipo de Dato** | **Almacenamiento TO BE** | **Justificación** | **Backup/Recovery** |
|------------------|-------------------------|-------------------|-------------------|
| [Especificar tipos] | [Definir almacenamiento] | [Explicar decisión] | [Definir estrategia] |

### Migración de Datos
[Definir estrategia de migración de datos del AS IS al TO BE]

**Plan de Migración de Datos:**
1. **[Fase 1]:** [Descripción de migración]
2. **[Fase 2]:** [Descripción de migración]
3. **[Fase 3]:** [Descripción de migración]

---

## Seguridad TO BE

### Arquitectura de Seguridad TO BE
[Definir arquitectura de seguridad mejorada]

**Autenticación TO BE:**
- [Método: OAuth 2.0, SAML, JWT, etc.]
- [Proveedor: Auth0, Cognito, KeyCloak, etc.]

**Autorización TO BE:**
- [Modelo: RBAC, ABAC, etc.]
- [Implementación específica]

**Seguridad en Datos TO BE:**
- [Encryption at rest y in transit]
- [Data masking/anonymization]

**Seguridad en APIs TO BE:**
- [Rate limiting, API Gateway, etc.]
- [Monitoreo de seguridad]

### Compliance y Regulaciones
[Si aplica, definir cumplimiento regulatorio]

---

## Escalabilidad y Rendimiento TO BE

### Estrategias de Escalabilidad TO BE
[Definir mejoras en escalabilidad]

**Auto-scaling TO BE:**
- [Horizontal Pod Autoscaler en K8s]
- [Auto Scaling Groups en AWS]
- [Métricas para escalado]

**Optimizaciones de Rendimiento TO BE:**
| **Área** | **Optimización TO BE** | **Impacto Esperado** | **Implementación** |
|----------|----------------------|---------------------|-------------------|
| [Especificar áreas] | [Definir optimizaciones] | [Cuantificar impacto] | [Detallar implementación] |

### Caching Strategy TO BE
[Definir estrategia de caché mejorada]

---

## Infraestructura y Despliegue TO BE

### Arquitectura de Infraestructura TO BE
[Definir nueva infraestructura]

**Componentes de Infraestructura TO BE:**
- [Load Balancers: ALB, NLB, etc.]
- [Container Orchestration: EKS, AKS, GKE]
- [Networking: VPC, subnets, security groups]
- [Storage: EBS, EFS, etc.]

**Ambientes TO BE:**
| **Ambiente** | **Propósito** | **Infraestructura** | **Configuración** |
|--------------|---------------|-------------------|-------------------|
| [Definir ambientes] | [Especificar propósitos] | [Detallar infra] | [Definir config] |

### Pipeline CI/CD TO BE
[Definir pipeline mejorado]

**Stages del Pipeline TO BE:**
1. **Source:** [Git triggers, webhooks]
2. **Build:** [Compilación, testing]
3. **Test:** [Unit, integration, e2e tests]
4. **Security Scan:** [SAST, DAST, dependency check]
5. **Deploy:** [Blue-green, canary, rolling]
6. **Monitor:** [Health checks, alerting]

---

## Plan de Migración AS IS → TO BE

### Estrategia de Migración
[Definir estrategia general de migración]

**Enfoque de Migración:** [Strangler Fig, Big Bang, Parallel Run, etc.]

### Fases de Migración
[Definir fases específicas]

| **Fase** | **Duración** | **Componentes** | **Riesgos** | **Rollback** |
|----------|--------------|-----------------|-------------|--------------|
| [Fase 1] | [Tiempo estimado] | [Componentes a migrar] | [Riesgos identificados] | [Plan de rollback] |
| [Fase 2] | [Tiempo estimado] | [Componentes a migrar] | [Riesgos identificados] | [Plan de rollback] |
| [Fase 3] | [Tiempo estimado] | [Componentes a migrar] | [Riesgos identificados] | [Plan de rollback] |

### Criteria de Éxito por Fase
[Definir criterios de éxito para cada fase]

**Fase 1 - Criterios:**
- [Criterio 1: métrica específica]
- [Criterio 2: funcionalidad verificada]

**Fase 2 - Criterios:**
- [Criterio 1: métrica específica]
- [Criterio 2: funcionalidad verificada]

---

## Recomendaciones de Implementación

### Recomendaciones Técnicas

**Desarrollo:**
1. **[Recomendación 1]:** [Descripción detallada]
2. **[Recomendación 2]:** [Descripción detallada]
3. **[Recomendación 3]:** [Descripción detallada]

**DevOps:**
1. **[Recomendación 1]:** [Descripción detallada]
2. **[Recomendación 2]:** [Descripción detallada]

**Seguridad:**
1. **[Recomendación 1]:** [Descripción detallada]
2. **[Recomendación 2]:** [Descripción detallada]

### Cronograma de Implementación

**Trimestre 1:**
- [Actividad específica con timeline]

**Trimestre 2:**
- [Actividad específica con timeline]

**Trimestre 3:**
- [Actividad específica con timeline]

**Trimestre 4:**
- [Actividad específica con timeline]

### Recursos Necesarios

| **Tipo de Recurso** | **Cantidad** | **Perfil** | **Duración** |
|-------------------|--------------|------------|--------------|
| [Desarrolladores] | [Número] | [Frontend/Backend/FullStack] | [Meses] |
| [DevOps] | [Número] | [Cloud/K8s/CI-CD] | [Meses] |
| [Arquitectos] | [Número] | [Software/Cloud/Security] | [Meses] |

---

## Anexos

### Comparación AS IS vs TO BE
[Tabla comparativa si hay información AS IS disponible]

| **Aspecto** | **AS IS** | **TO BE** | **Beneficio** |
|-------------|-----------|-----------|---------------|
| [Tecnología] | [Tech actual] | [Tech objetivo] | [Mejora esperada] |
| [Performance] | [Métricas actuales] | [Métricas objetivo] | [Mejora esperada] |
| [Escalabilidad] | [Capacidad actual] | [Capacidad objetivo] | [Mejora esperada] |

### Glosario Técnico TO BE
[Definir términos técnicos específicos de la nueva arquitectura]

### Referencias y Documentación
[Listar documentación técnica y referencias utilizadas]

---

**Notas del Diseño TO BE:**
- **Fuentes:** [Documentos AS IS y especificaciones utilizadas]
- **Supuestos:** [Supuestos realizados en el diseño]
- **Consideraciones:** [Consideraciones especiales tomadas en cuenta]

---

**REGLAS PARA EL DISEÑO TO BE:**
- Basar el diseño en las especificaciones de tecnologías objetivo proporcionadas
- Mantener la funcionalidad existente mientras se mejora la arquitectura
- Proponer mejoras realistas y alcanzables
- Incluir consideraciones de migración y plan de implementación
- Asegurar que el diseño sea escalable, seguro y mantenible
- Especificar tecnologías concretas y justificar su selección

---
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
        return f"Error generando arquitectura TO BE: {str(e)}"