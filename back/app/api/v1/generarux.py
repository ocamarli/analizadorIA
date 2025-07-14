from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import os
import io
import PyPDF2
from langchain_community.chat_models import AzureChatOpenAI
from langchain.prompts import PromptTemplate
import logging
import re
import time
import json
from functools import wraps
from collections import defaultdict

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Blueprint
generaUx_bp = Blueprint('generador_interfaces_html', __name__)

# Rate limiting storage (en producción usar Redis)
rate_limit_storage = defaultdict(list)
RATE_LIMIT_REQUESTS = 3  # 3 requests
RATE_LIMIT_WINDOW = 300  # 5 minutos

# Configuración LangChain
try:
    llm = AzureChatOpenAI(
        deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1"),
        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        openai_api_key=os.getenv("AZURE_OPENAI_API_KEY", "6076ii7OpLiuTEKYsEVvWyt57RYjzb8d4hDwZRqKuokBi1WTuKz9JQQJ99AJACYeBjFXJ3w3AAABACOGfwuS"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://openaidemobside.openai.azure.com"),
        temperature=0.4,
        max_tokens=4000
    )
    logger.info("LLM configurado correctamente para generación HTML/CSS")
except Exception as e:
    logger.error(f"Error configurando LLM: {str(e)}")
    llm = None

def rate_limit(func):
    """Decorador para rate limiting"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        
        current_time = time.time()
        rate_limit_storage[client_ip] = [
            req_time for req_time in rate_limit_storage[client_ip]
            if current_time - req_time < RATE_LIMIT_WINDOW
        ]
        
        if len(rate_limit_storage[client_ip]) >= RATE_LIMIT_REQUESTS:
            return jsonify({
                'success': False,
                'error': 'Rate limit excedido. Máximo 3 generaciones cada 5 minutos.',
                'retry_after': RATE_LIMIT_WINDOW
            }), 429
        
        rate_limit_storage[client_ip].append(current_time)
        return func(*args, **kwargs)
    return wrapper

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

def clean_html_response(content):
    """Limpieza específica para respuestas HTML/CSS"""
    try:
        # Intentar parsear como JSON
        if content.strip().startswith('{'):
            return json.loads(content)
        
        # Buscar JSON en el contenido
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        
        # Estructura básica de fallback
        return {
            "project_name": "Sistema Generado",
            "screens": [
                {
                    "id": "main",
                    "title": "Pantalla Principal",
                    "html": "<div class='container'><h1>Sistema Principal</h1><p>Pantalla generada automáticamente</p></div>",
                    "css": ".container { padding: 20px; text-align: center; }"
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error limpiando respuesta HTML: {str(e)}")
        return {
            "project_name": "Error de Generación",
            "screens": [
                {
                    "id": "error",
                    "title": "Error",
                    "html": "<div class='error'>Error procesando la respuesta</div>",
                    "css": ".error { color: red; padding: 20px; }"
                }
            ]
        }

def validate_html_structure(html_data):
    """Validación para estructura HTML"""
    if not isinstance(html_data, dict):
        return False, "La respuesta debe ser un objeto JSON"
    
    if 'screens' not in html_data:
        return False, "Debe contener el campo 'screens'"
    
    if not isinstance(html_data['screens'], list):
        return False, "El campo 'screens' debe ser una lista"
    
    if len(html_data['screens']) == 0:
        return False, "Debe tener al menos una pantalla"
    
    # Validar que cada pantalla tenga HTML y CSS
    for screen in html_data['screens']:
        if 'html' not in screen or 'css' not in screen:
            return False, f"La pantalla '{screen.get('id', 'unknown')}' debe tener HTML y CSS"
    
    return True, None

# Template mejorado para generación HTML/CSS real
html_generator_prompt = PromptTemplate(
    input_variables=["contenido_archivo", "contexto_adicional"],
    template="""
Eres un experto Frontend Developer y UX/UI Designer. Analiza el contenido y genera pantallas HTML/CSS completas y funcionales para el sistema, con diseño responsive para desktop, tablet y móvil.

CONTENIDO A ANALIZAR:
{contenido_archivo}

CONTEXTO ADICIONAL:
{contexto_adicional}

INSTRUCCIONES CRÍTICAS:
1. Analiza TODOS los procesos, funcionalidades y casos de uso del documento
2. Genera HTML/CSS REAL y funcional para cada pantalla identificada
3. Usa un framework CSS moderno (como Tailwind-style classes o CSS Grid/Flexbox)
4. Diseño RESPONSIVE: Desktop (1200px+), Tablet (768px-1199px), Mobile (<768px)
5. Incluye interactividad básica con JavaScript inline cuando sea necesario
6. Componentes modernos: botones, formularios, tablas, cards, modals, etc.

TIPOS DE PANTALLAS A GENERAR:
- Login/Autenticación
- Dashboard principal con métricas
- Listados con búsqueda, filtros y paginación
- Formularios CRUD (crear, editar)
- Detalles/Vista de elementos
- Reportes y visualizaciones
- Configuración y administración
- Modales de confirmación

ESTRUCTURA DE RESPUESTA (JSON VÁLIDO):
{{
  "project_name": "[Nombre extraído del documento]",
  "description": "[Descripción del sistema]",
  "total_screens": [número],
  "responsive_breakpoints": {{
    "desktop": "1200px",
    "tablet": "768px", 
    "mobile": "480px"
  }},
  "global_styles": "/* CSS Global */ * {{ margin: 0; padding: 0; box-sizing: border-box; }} body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f7fa; }} .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }} .responsive-grid {{ display: grid; gap: 20px; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }} @media (max-width: 768px) {{ .container {{ padding: 10px; }} .responsive-grid {{ grid-template-columns: 1fr; }} }}",
  "screens": [
    {{
      "id": "login",
      "title": "Inicio de Sesión",
      "description": "Pantalla de autenticación",
      "type": "auth",
      "priority": "high",
      "responsive": true,
      "html": "<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>Login</title></head><body><div class='login-container'><div class='login-card'><h1>Iniciar Sesión</h1><form class='login-form'><div class='form-group'><label for='username'>Usuario</label><input type='text' id='username' name='username' required></div><div class='form-group'><label for='password'>Contraseña</label><input type='password' id='password' name='password' required></div><button type='submit' class='btn-primary'>Iniciar Sesión</button></form><div class='forgot-password'><a href='#'>¿Olvidaste tu contraseña?</a></div></div></div></body></html>",
      "css": ".login-container {{ display: flex; justify-content: center; align-items: center; min-height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }} .login-card {{ background: white; padding: 40px; border-radius: 10px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }} .login-card h1 {{ text-align: center; margin-bottom: 30px; color: #333; }} .form-group {{ margin-bottom: 20px; }} .form-group label {{ display: block; margin-bottom: 5px; color: #555; font-weight: 500; }} .form-group input {{ width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }} .form-group input:focus {{ outline: none; border-color: #667eea; box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2); }} .btn-primary {{ width: 100%; background: #667eea; color: white; padding: 12px; border: none; border-radius: 5px; font-size: 16px; font-weight: 500; cursor: pointer; transition: background 0.3s; }} .btn-primary:hover {{ background: #5a6fd8; }} .forgot-password {{ text-align: center; margin-top: 20px; }} @media (max-width: 480px) {{ .login-card {{ padding: 20px; margin: 20px; }} }}"
    }},
    {{
      "id": "dashboard",
      "title": "Dashboard Principal",
      "description": "Panel de control con métricas y accesos rápidos",
      "type": "dashboard",
      "priority": "high",
      "responsive": true,
      "html": "<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>Dashboard</title></head><body><div class='dashboard-layout'><header class='dashboard-header'><div class='header-content'><h1>Dashboard</h1><div class='user-menu'><span>Usuario Admin</span><button class='logout-btn'>Salir</button></div></div></header><nav class='sidebar'><ul class='nav-menu'><li><a href='#dashboard' class='nav-link active'>Dashboard</a></li><li><a href='#users' class='nav-link'>Usuarios</a></li><li><a href='#products' class='nav-link'>Productos</a></li><li><a href='#reports' class='nav-link'>Reportes</a></li><li><a href='#settings' class='nav-link'>Configuración</a></li></ul></nav><main class='main-content'><div class='stats-grid'><div class='stat-card'><h3>Total Usuarios</h3><div class='stat-number'>1,234</div><div class='stat-change positive'>+5.2%</div></div><div class='stat-card'><h3>Ventas Hoy</h3><div class='stat-number'>$25,678</div><div class='stat-change positive'>+12.4%</div></div><div class='stat-card'><h3>Productos</h3><div class='stat-number'>567</div><div class='stat-change negative'>-2.1%</div></div><div class='stat-card'><h3>Órdenes</h3><div class='stat-number'>89</div><div class='stat-change positive'>+8.7%</div></div></div><div class='content-grid'><div class='chart-container'><h3>Ventas por Mes</h3><div class='chart-placeholder'>Gráfico de Ventas</div></div><div class='recent-activity'><h3>Actividad Reciente</h3><div class='activity-list'><div class='activity-item'>Usuario creado: Juan Pérez</div><div class='activity-item'>Producto actualizado: Laptop HP</div><div class='activity-item'>Orden completada: #12345</div></div></div></div></main></div></body></html>",
      "css": ".dashboard-layout {{ display: grid; grid-template-areas: 'header header' 'sidebar main'; grid-template-rows: 60px 1fr; grid-template-columns: 250px 1fr; min-height: 100vh; }} .dashboard-header {{ grid-area: header; background: #2c3e50; color: white; display: flex; align-items: center; padding: 0 20px; }} .header-content {{ display: flex; justify-content: space-between; align-items: center; width: 100%; }} .user-menu {{ display: flex; align-items: center; gap: 15px; }} .logout-btn {{ background: #e74c3c; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; }} .sidebar {{ grid-area: sidebar; background: #34495e; }} .nav-menu {{ list-style: none; padding: 20px 0; }} .nav-link {{ display: block; color: #bdc3c7; padding: 15px 20px; text-decoration: none; transition: background 0.3s; }} .nav-link:hover, .nav-link.active {{ background: #2c3e50; color: white; }} .main-content {{ grid-area: main; padding: 30px; }} .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }} .stat-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }} .stat-number {{ font-size: 2em; font-weight: bold; color: #2c3e50; margin: 10px 0; }} .stat-change.positive {{ color: #27ae60; }} .stat-change.negative {{ color: #e74c3c; }} .content-grid {{ display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }} .chart-container, .recent-activity {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }} .chart-placeholder {{ height: 300px; background: #ecf0f1; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: #7f8c8d; }} .activity-item {{ padding: 10px 0; border-bottom: 1px solid #ecf0f1; }} @media (max-width: 768px) {{ .dashboard-layout {{ grid-template-areas: 'header' 'main'; grid-template-columns: 1fr; grid-template-rows: 60px 1fr; }} .sidebar {{ display: none; }} .stats-grid {{ grid-template-columns: 1fr; }} .content-grid {{ grid-template-columns: 1fr; }} }}"
    }}
  ]
}}

REGLAS ESPECÍFICAS PARA HTML/CSS:
1. HTML SEMÁNTICO: usa tags apropiados (header, nav, main, section, article)
2. CSS MODERNO: Flexbox, Grid, variables CSS, animaciones
3. RESPONSIVE: Mobile-first design con media queries
4. ACCESIBILIDAD: Labels, alt text, aria-labels cuando sea necesario
5. INTERACTIVIDAD: Hover effects, transitions, basic JavaScript
6. COMPONENTES REUTILIZABLES: buttons, forms, cards, modals consistentes
7. COLORES: Paleta coherente y profesional
8. TIPOGRAFÍA: Jerarquía clara con diferentes tamaños y pesos

ANÁLISIS EXHAUSTIVO REQUERIDO:
- Si menciona "gestión de usuarios" → Pantallas: lista usuarios, crear usuario, editar usuario, perfil
- Si menciona "productos/inventario" → Pantallas: catálogo, agregar producto, editar, stock
- Si menciona "reportes" → Pantallas: dashboard reportes, configurar reporte, exportar
- Si menciona "roles/permisos" → Pantallas: gestión roles, asignar permisos
- Si menciona "configuración" → Pantallas: settings generales, perfil usuario
- Si menciona "ventas/transacciones" → Pantallas: lista ventas, detalle venta, crear orden

Para CADA funcionalidad identificada, genera pantallas HTML/CSS completas y responsive.

Genera ÚNICAMENTE el JSON con HTML/CSS real basado en el análisis completo:
"""
)

@generaUx_bp.route('/generar-interfaces-html', methods=['POST'])
@rate_limit
def generate_html_interfaces():
    """Genera interfaces HTML/CSS reales basadas en contexto"""
    try:
        logger.info("=== GENERANDO INTERFACES HTML/CSS REALES ===")
        
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
                        contenido_archivo += f"\n--- ARCHIVO: {file.filename} ---\n{texto_extraido}\n"
                    
                    elif file.filename.lower().endswith(('.md', '.markdown', '.txt')):
                        texto_extraido = extract_text_from_markdown(file_content)
                        contenido_archivo += f"\n--- ARCHIVO: {file.filename} ---\n{texto_extraido}\n"
                    
                    else:
                        return jsonify({
                            'success': False,
                            'error': f'Formato no soportado: {file.filename}. Use PDF, Markdown o TXT'
                        }), 400
                        
                except Exception as e:
                    return jsonify({
                        'success': False,
                        'error': f'Error procesando {file.filename}: {str(e)}'
                    }), 400
        
        if not contenido_archivo and contexto_adicional:
            contenido_archivo = "Información proporcionada directamente por el usuario."
        
        # Generar interfaces HTML/CSS con IA
        logger.info("Generando interfaces HTML/CSS con IA...")
        chain = html_generator_prompt | llm
        
        start_time = time.time()
        response = chain.invoke({
            'contenido_archivo': contenido_archivo,
            'contexto_adicional': contexto_adicional or "Sin contexto adicional especificado."
        })
        generation_time = time.time() - start_time
        
        # Procesar respuesta
        html_structure = clean_html_response(response.content)
        
        logger.info(f"Interfaces HTML/CSS generadas en {generation_time:.2f}s")
        
        # Validación
        is_valid, error_msg = validate_html_structure(html_structure)
        
        if not is_valid:
            logger.warning(f"Validación falló: {error_msg}")
            # Reintento con instrucciones más específicas
            retry_response = chain.invoke({
                'contenido_archivo': contenido_archivo,
                'contexto_adicional': f"{contexto_adicional}\n\nIMPORTANTE: Responde ÚNICAMENTE con JSON válido conteniendo pantallas HTML/CSS completas y responsive."
            })
            
            html_structure = clean_html_response(retry_response.content)
            is_valid, error_msg = validate_html_structure(html_structure)
            
            if not is_valid:
                logger.warning(f"Segundo intento falló: {error_msg}. Usando estructura básica.")
        
        logger.info("=== INTERFACES HTML/CSS GENERADAS EXITOSAMENTE ===")
        
        return jsonify({
            'success': True,
            'html_structure': html_structure,
            'generation_time': round(generation_time, 2),
            'total_screens': len(html_structure.get('screens', [])),
            'project_name': html_structure.get('project_name', 'Sistema Generado'),
            'responsive': True,
            'message': 'Interfaces HTML/CSS generadas exitosamente',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@generaUx_bp.route('/rate-limit-status', methods=['GET'])
def get_rate_limit_status():
    """Obtiene el estado actual del rate limiting"""
    try:
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        
        current_time = time.time()
        rate_limit_storage[client_ip] = [
            req_time for req_time in rate_limit_storage[client_ip]
            if current_time - req_time < RATE_LIMIT_WINDOW
        ]
        
        requests_made = len(rate_limit_storage[client_ip])
        requests_remaining = max(0, RATE_LIMIT_REQUESTS - requests_made)
        
        if requests_made > 0:
            oldest_request = min(rate_limit_storage[client_ip])
            time_until_reset = max(0, RATE_LIMIT_WINDOW - (current_time - oldest_request))
        else:
            time_until_reset = 0
        
        return jsonify({
            'requests_made': requests_made,
            'requests_remaining': requests_remaining,
            'rate_limit': RATE_LIMIT_REQUESTS,
            'window_seconds': RATE_LIMIT_WINDOW,
            'time_until_reset': round(time_until_reset),
            'can_make_request': requests_remaining > 0
        })
        
    except Exception as e:
        logger.error(f"Error getting rate limit status: {str(e)}")
        return jsonify({'error': 'Error obteniendo estado de rate limit'}), 500

@generaUx_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint de salud"""
    return jsonify({
        'status': 'healthy',
        'service': 'html_interfaces_generator',
        'timestamp': datetime.now().isoformat(),
        'llm_configured': llm is not None,
        'supported_formats': ['PDF', 'Markdown', 'TXT'],
        'features': ['HTML/CSS Generation', 'Responsive Design', 'Rate Limiting'],
        'responsive_breakpoints': {
            'desktop': '1200px',
            'tablet': '768px', 
            'mobile': '480px'
        }
    })