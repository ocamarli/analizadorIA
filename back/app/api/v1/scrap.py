# app/modulos/generarUI.py
from flask import Blueprint, request, jsonify, send_file
import os
import datetime
import json
import re
import base64
import io
import zipfile
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuración desde variables de entorno o constantes
AZURE_OPENAI_ENDPOINT = "https://openaidemobside.openai.azure.com"
AZURE_OPENAI_API_KEY = "6076ii7OpLiuTEKYsEVvWyt57RYjzb8d4hDwZRqKuokBi1WTuKz9JQQJ99AJACYeBjFXJ3w3AAABACOGfwuS"
AZURE_OPENAI_DEPLOYMENT = "2024-08-01-preview"
AZURE_SEARCH_ENDPOINT = "https://azuresearhdemobside.search.windows.net"
AZURE_SEARCH_INDEX = "azureblob-index"
AZURE_SEARCH_KEY = "YdBHzUf4al4bPNDgDOLLc9XDnPaxucfrBU47RQbXtRAzSeCujuVS"
GPT_MODEL = "gpt-4o"  # Modelo a utilizar

# Cliente de OpenAI
openai_client = AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_DEPLOYMENT
)

# Blueprint para las rutas de generación de UI
scrap_bp = Blueprint('scrap', __name__)

# Configurar Selenium WebDriver
def setup_driver():
    """Configura y devuelve un navegador Chrome en modo headless."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Instalar el driver automáticamente si es necesario
    service = Service(ChromeDriverManager().install())
    
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# Función para hacer web scraping
def scrape_website(url):
    """Realiza web scraping de la URL proporcionada y devuelve los datos extraídos."""
    driver = None
    try:
        driver = setup_driver()
        driver.get(url)
        
        # Esperar a que la página cargue
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Extraer título
        title = driver.title
        
        # Extraer descripción meta
        description = ""
        try:
            meta_desc = driver.find_element(By.CSS_SELECTOR, 'meta[name="description"]')
            description = meta_desc.get_attribute('content')
        except:
            pass
        
        # Extraer texto principal
        driver.execute_script("""
            var elements = document.querySelectorAll('script, style, noscript, iframe');
            for (var i = 0; i < elements.length; i++) {
                elements[i].remove();
            }
        """)
        
        body_element = driver.find_element(By.TAG_NAME, 'body')
        text_content = body_element.text
        
        # Extraer enlaces
        links = []
        link_elements = driver.find_elements(By.TAG_NAME, 'a')
        for link in link_elements[:20]:
            href = link.get_attribute('href')
            if href and href.startswith('http'):
                text = link.text.strip()
                links.append({
                    "url": href,
                    "text": text if text else "[Sin texto]"
                })
        
        # Extraer imágenes
        images = []
        img_elements = driver.find_elements(By.TAG_NAME, 'img')
        for img in img_elements[:10]:
            src = img.get_attribute('src')
            if src and (src.startswith('http') or src.startswith('/')):
                # Convertir URLs relativas a absolutas
                if src.startswith('/'):
                    base_url = re.match(r'(https?://[^/]+)', url).group(1)
                    src = base_url + src
                images.append(src)
        
        result = {
            "url": url,
            "title": title,
            "description": description,
            "text": text_content[:5000],  # Limitar longitud
            "links": links,
            "images": images
        }
        
        return result
    
    except Exception as e:
        logger.error(f"Error en scraping: {str(e)}")
        return {"error": str(e), "url": url}
    
    finally:
        if driver:
            driver.quit()

@scrap_bp.route('/generate-ui', methods=['POST'])
def scrap():
    """
    Endpoint para generar interfaces de usuario basadas en un requerimiento
    """
    try:
        data = request.json
        prompt = data.get('prompt')
        
        if not prompt:
            return jsonify({"error": "Debes proporcionar un prompt para generar la interfaz de usuario"}), 400
        
        logger.info(f"Generando UI para: {prompt}")
        
        # Buscar documentos relevantes en Azure Search primero
        context = ""
        try:
            # Configuración para Azure Cognitive Search
            search_client = SearchClient(
                endpoint=AZURE_SEARCH_ENDPOINT,
                index_name=AZURE_SEARCH_INDEX,
                credential=AzureKeyCredential(AZURE_SEARCH_KEY)
            )
            
            # Realizar la búsqueda
            results = search_client.search(
                search_text=prompt,
                select=["id", "content", "metadata"],
                search_mode="all",
                include_total_count=True,
                top=3
            )
            
            # Procesar resultados para crear contexto
            context_docs = []
            for result in results:
                if hasattr(result, 'content') and result.content:
                    context_docs.append(f"Documento: {result.id}\nContenido: {result.content[:1000]}...")
            
            if context_docs:
                context = "Contexto de documentos relevantes:\n" + "\n\n".join(context_docs)
        
        except Exception as e:
            logger.warning(f"Error al buscar en Azure Search: {str(e)}")
            # Continuar sin contexto si hay error en la búsqueda
        
        # Determinar si el prompt incluye una URL para scraping
        urls = re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', prompt)
        scrape_data = []
        
        if urls:
            for url in urls[:3]:  # Limitar a 3 URLs para evitar sobrecarga
                logger.info(f"Realizando scraping de: {url}")
                scrape_result = scrape_website(url)
                if "error" not in scrape_result:
                    scrape_data.append(scrape_result)
        
        # Crear mensaje para OpenAI
        messages = [
            {"role": "system", "content": """Eres un experto en desarrollo de interfaces de usuario. Tu tarea es generar código React con Material UI para crear la interfaz solicitada.
            Genera componentes reutilizables y sigue las mejores prácticas de diseño. El código debe ser completo, funcional y listo para usar.
            Utiliza Material UI para todos los componentes visuales. Asegúrate de que el diseño sea responsivo y accesible.
            Incluye comentarios explicativos en el código."""}
        ]
        
        # Añadir contexto si existe
        if context:
            messages.append({"role": "system", "content": f"Utiliza esta información como referencia: {context}"})
        
        # Añadir datos de scraping si existen
        if scrape_data:
            scrape_context = "Datos obtenidos por scraping de URLs mencionadas:\n" + json.dumps(scrape_data, indent=2)
            messages.append({"role": "system", "content": f"Usa estos datos para inspirarte o incluirlos en la UI si es relevante: {scrape_context}"})
        
        # Añadir el prompt del usuario
        messages.append({"role": "user", "content": prompt})
        
        # Generar respuesta con OpenAI
        response = openai_client.chat.completions.create(
            model=GPT_MODEL,
            messages=messages,
            max_tokens=4000,
            temperature=0.7,
        )
        
        # Extraer código React del resultado
        result_content = response.choices[0].message.content
        
        # Buscar bloques de código en la respuesta
        code_blocks = re.findall(r'```(?:jsx|javascript|react)?\s*([\s\S]*?)```', result_content)
        
        if not code_blocks:
            # Si no hay bloques de código formateados, intentar extraer todo como código
            code_content = result_content
        else:
            # Unir todos los bloques de código encontrados
            code_content = "\n\n".join(code_blocks)
        
        # Crear archivo temporal con el código
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ui_component_{timestamp}.jsx"
        filepath = os.path.join(os.getcwd(), "temp", filename)
        
        # Asegurar que el directorio existe
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code_content)
        
        # Crear un zip con el componente y metadata
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Añadir el archivo JSX
            zf.write(filepath, filename)
            
            # Crear y añadir un archivo README con instrucciones
            readme_content = f"""# UI Component: {filename}

## Generado por IA el {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

### Descripción
Este componente fue generado automáticamente basado en el prompt:
"{prompt}"

### Instalación
Para usar este componente:

1. Asegúrate de tener Material UI instalado:
   ```
   npm install @mui/material @emotion/react @emotion/styled @mui/icons-material
   ```

2. Coloca el archivo JSX en tu directorio de componentes.

3. Importa el componente donde lo necesites:
   ```jsx
   import MiComponente from './ruta/al/componente';
   ```

### Personalización
Puedes modificar el componente según tus necesidades específicas.
"""
            zf.writestr("README.md", readme_content)
            
            # Añadir metadata
            metadata = {
                "prompt": prompt,
                "timestamp": datetime.datetime.now().isoformat(),
                "model": GPT_MODEL,
                "scraping_urls": urls if urls else []
            }
            zf.writestr("metadata.json", json.dumps(metadata, indent=2))
        
        memory_file.seek(0)
        
        # Limpiar archivo temporal
        try:
            os.remove(filepath)
        except:
            pass
        
        # Devolver el zip como descarga
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"ui_component_{timestamp}.zip"
        )
        
    except Exception as e:
        logger.error(f"Error en scrap: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@scrap_bp.route('/scrape', methods=['POST'])
def scrape():
    """
    Endpoint para realizar web scraping de una URL
    """
    try:
        data = request.json
        url = data.get('url')
        
        if not url:
            return jsonify({"error": "Debes proporcionar una URL para realizar el scraping"}), 400
        
        # Validar URL
        if not re.match(r'https?://', url):
            return jsonify({"error": "URL inválida. Debe comenzar con http:// o https://"}), 400
        
        logger.info(f"Realizando scraping de: {url}")
        
        result = scrape_website(url)
        
        if "error" in result:
            return jsonify({"error": result["error"]}), 500
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error en scrape: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# Rutas adicionales
@scrap_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint para verificar que el servicio está funcionando."""
    return jsonify({
        "status": "OK",
        "timestamp": datetime.datetime.now().isoformat()
    })