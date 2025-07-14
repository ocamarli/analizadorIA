# app/modules/search.py
from flask import Blueprint, request, jsonify
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from openai import AzureOpenAI
import os
import glob
import datetime
# Importar search_client, etc.
# Configuración de Cognitive Search
COGNITIVE_SEARCH_ENDPOINT = "https://azuresearhdemobside.search.windows.net"
COGNITIVE_SEARCH_INDEX = "azureblob-index"
COGNITIVE_SEARCH_API_KEY = "YdBHzUf4al4bPNDgDOLLc9XDnPaxucfrBU47RQbXtRAzSeCujuVS"

AZURE_OPENAI_ENDPOINT = "https://openaidemobside.openai.azure.com"
AZURE_OPENAI_API_KEY = "6076ii7OpLiuTEKYsEVvWyt57RYjzb8d4hDwZRqKuokBi1WTuKz9JQQJ99AJACYeBjFXJ3w3AAABACOGfwuS"
AZURE_OPENAI_DEPLOYMENT = "2024-08-01-preview"  # Nombre del deployment en Azure
openai_client = AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_DEPLOYMENT
)

search_client = SearchClient(COGNITIVE_SEARCH_ENDPOINT, COGNITIVE_SEARCH_INDEX, AzureKeyCredential(COGNITIVE_SEARCH_API_KEY))
histories_bp = Blueprint('histories', __name__)

@histories_bp.route('/generate-user-stories', methods=['POST'])
def generate_user_stories():
    data = request.json
    code_path = data.get('code_path')
    normalized = code_path.replace('\\', '/')
    code_path = normalized
    print(f"Analizando código en: {code_path}")
    
    # Límite de archivos a analizar (puedes ajustar según necesites)
    file_limit = 100 # Incrementado de 5 a 15
    
    if not code_path:
        return jsonify({"error": "Debes proporcionar la ruta del código"}), 400
    
    # Función para construir el árbol de directorios
    def build_directory_tree(start_path):
        tree = {"name": os.path.basename(start_path), "type": "folder", "children": []}
        
        try:
            for item in os.listdir(start_path):
                item_path = os.path.join(start_path, item)
                
                # Ignorar archivos y carpetas ocultos
                if item.startswith('.'):
                    continue
                    
                if os.path.isdir(item_path):
                    tree["children"].append(build_directory_tree(item_path))
                else:
                    # Incluir solo archivos con extensiones soportadas
                    _, ext = os.path.splitext(item)
                    if ext.lower() in [
                # Lenguajes de programación
                '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.kt', '.scala', 
                '.go', '.rs', '.rb', '.pl', '.pm', '.lua', '.swift', '.m', '.mm',
                '.dart', '.elm', '.clj', '.r', '.sh', '.bash', '.zsh', '.fish',
                '.ps1', '.bat', '.cmd','.def','.txt',
                
                # .NET y C familia
                '.cs', '.vb', '.fs', '.c', '.cpp', '.h', '.hpp', '.cc', '.hh',
                
                # Web y markup
                '.html', '.htm', '.xhtml', '.css', '.scss', '.sass', '.less',
                '.xml', '.json', '.yaml', '.yml', '.toml', '.md', '.rst',
                
                # Bases de datos
                '.sql', '.psql', '.pgsql', '.mysql', '.mssql',
                
                # Binarios y librerías
                '.dll', '.so', '.dylib', '.a', '.lib', '.exe',
                
                # Configuraciones y otros
                '.ini', '.cfg', '.conf', '.properties', '.env', '.dockerfile',
                '.makefile', '.cmake'
            ]:
                        tree["children"].append({
                            "name": item,
                            "type": "file",
                            "extension": ext.lower()
                        })
        except Exception as e:
            print(f"Error al construir árbol en {start_path}: {e}")
        
        return tree
    
    # Construir el árbol de directorios
    directory_tree = build_directory_tree(code_path)
    
    # Recolectar archivos de código recursivamente (todos los archivos, no solo del directorio principal)
    code_files = []
    supported_extensions = [
                # Lenguajes de programación
                '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.kt', '.scala', 
                '.go', '.rs', '.rb', '.pl', '.pm', '.lua', '.swift', '.m', '.mm',
                '.dart', '.elm', '.clj', '.r', '.sh', '.bash', '.zsh', '.fish',
                '.ps1', '.bat', '.cmd','.def','.txt',
                
                # .NET y C familia
                '.cs', '.vb', '.fs', '.c', '.cpp', '.h', '.hpp', '.cc', '.hh',
                
                # Web y markup
                '.html', '.htm', '.xhtml', '.css', '.scss', '.sass', '.less',
                '.xml', '.json', '.yaml', '.yml', '.toml', '.md', '.rst',
                
                # Bases de datos
                '.sql', '.psql', '.pgsql', '.mysql', '.mssql',
                
                # Binarios y librerías
                '.dll', '.so', '.dylib', '.a', '.lib', '.exe',
                
                # Configuraciones y otros
                '.ini', '.cfg', '.conf', '.properties', '.env', '.dockerfile',
                '.makefile', '.cmake'
            ]
    
    for ext in supported_extensions:
        code_files.extend(glob.glob(f"{code_path}/**/*{ext}", recursive=True))
    
    # Ordenar archivos por tamaño para priorizar archivos más pequeños y probablemente más importantes
    code_files.sort(key=lambda f: os.path.getsize(f) if os.path.exists(f) else 0)
    
    if not code_files:
        return jsonify({
            "error": "No se encontraron archivos de código en la ruta especificada",
            "directory_tree": directory_tree
        }), 404
    
    # Extraer estadísticas del proyecto
    project_stats = {
        "total_files": len(code_files),
        "analyzed_files": min(len(code_files), file_limit),
        "extensions": {},
        "largest_file": {"name": "", "size": 0},
        "total_lines": 0
    }
    
    # Contar archivos por extensión
    for file in code_files:
        _, ext = os.path.splitext(file)
        ext = ext.lower()
        if ext in project_stats["extensions"]:
            project_stats["extensions"][ext] += 1
        else:
            project_stats["extensions"][ext] = 1
        
        # Verificar si es el archivo más grande
        file_size = os.path.getsize(file) if os.path.exists(file) else 0
        if file_size > project_stats["largest_file"]["size"]:
            project_stats["largest_file"] = {
                "name": os.path.basename(file),
                "size": file_size,
                "path": file
            }
    
    # Extraer y unir código de los archivos (limitado por file_limit)
    all_code = ""
    analyzed_files = []
    total_lines = 0
    
    for file in code_files[:file_limit]:
        try:
            with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.count('\n') + 1
                total_lines += lines
                
                # Añadir metadatos del archivo
                file_path = os.path.relpath(file, code_path)
                file_size = os.path.getsize(file)
                
                analyzed_files.append({
                    "name": os.path.basename(file),
                    "path": file_path,
                    "extension": os.path.splitext(file)[1].lower(),
                    "size": file_size,
                    "lines": lines
                })
                
                all_code += f"\n\n--- Archivo: {file_path} ({lines} líneas) ---\n\n{content}"
        except Exception as e:
            print(f"Error al leer archivo {file}: {e}")
    
    project_stats["total_lines"] = total_lines
    
    # Generar Historias de Usuario con Azure OpenAI
    system_message = """Eres un asistente especializado en análisis de código y generación de documentación ágil. Tu tarea es analizar código fuente, identificar automáticamente su tipo (procedimiento almacenado SQL, código de aplicación, etc.) y generar historias de usuario detalladas que capturen la funcionalidad del código. Adaptas tu análisis según el tipo de código detectado, siguiendo diferentes plantillas según corresponda. Incluye criterios de aceptación claros y precisos para cada historia. Utiliza el contexto del proyecto para crear historias con un alto valor de negocio y bien estructuradas."""

    user_message = f"""
    Analiza el siguiente código legado, identifica automáticamente su tipo y genera historias de usuario que describan su funcionalidad.

    Para cada módulo, función o procedimiento identificado, genera una historia de usuario en formato:

    Como [tipo de usuario],
    Quiero [acción/funcionalidad],
    Para [beneficio/valor de negocio].

    Incluye criterios de aceptación para cada historia que integren la explicación de las fórmulas y reglas de negocio en lenguaje natural. En los criterios de aceptación, muestra las variables entre paréntesis para facilitar la relación con el código original.

    Si el código es un PROCEDIMIENTO ALMACENADO SQL:
    1. Comienza con un análisis técnico que incluya: propósito general, estructura del procedimiento, parámetros de entrada, tablas utilizadas, lógica de negocio clave y patrones de diseño SQL notables.
    2. Luego, genera historias de usuario para cada funcionalidad principal, capturando el flujo de trabajo de distribución, cálculos, validaciones, etc.

    Si el código es CÓDIGO DE APLICACIÓN (C#, Java, etc.):
    1. Analiza cada módulo o función por separado.
    2. Describe las fórmulas de reglas de negocios en lenguaje natural, mostrando las variables del código entre paréntesis como en este ejemplo:
    "La profundidad E se calcula tomando el prototipo E modificado (`txbProtoEModificado.Text`), dividiéndolo entre la suma de tallas promedio (`lblTallasPromedioModificadoValor.Text`) y tallas más vendedoras (`lblTallaMasVendedoraValor.Text`), y finalmente dividiendo este resultado entre el número de tiendas con disponibilidad E (`lblTdaENumTiendas.Text`), redondeando a 2 decimales."


    ESTADÍSTICAS DEL PROYECTO:
    - Total de archivos: {project_stats["total_files"]}
    - Archivos analizados: {project_stats["analyzed_files"]}
    - Total de líneas de código: {project_stats["total_lines"]}

    CÓDIGO A ANALIZAR:
    {all_code}
    """  
    try:
        # Llamada a la API de Azure OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # Asegúrate de que este modelo esté disponible en tu despliegue
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.2,
            max_tokens=10000
        )

        # Obtener información de uso de tokens
        tokens_prompt = response.usage.prompt_tokens
        tokens_completion = response.usage.completion_tokens
        tokens_total = response.usage.total_tokens

        print(f"Tokens utilizados en esta llamada:")
        print(f"  - Tokens del prompt: {tokens_prompt}")
        print(f"  - Tokens de la respuesta: {tokens_completion}")
        print(f"  - Total de tokens: {tokens_total}")


        # Acceder correctamente a la respuesta (como objeto, no como diccionario)
        user_stories = response.choices[0].message.content
        
        # Generar nombre de archivo con timestamp para evitar sobreescrituras
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"historias_usuario_{timestamp}.md"
        output_path = os.path.join(code_path, output_filename)
        
        # Guardar historias de usuario en un archivo Markdown
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Historias de Usuario Generadas\n\n")
            f.write(f"Fecha de generación: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## Estadísticas del Proyecto\n\n")
            f.write(f"- **Total de archivos:** {project_stats['total_files']}\n")
            f.write(f"- **Archivos analizados:** {project_stats['analyzed_files']}\n")
            f.write(f"- **Total de líneas de código:** {project_stats['total_lines']}\n\n")
            f.write(f"## Archivos Analizados\n\n")
            
            for file in analyzed_files:
                f.write(f"- {file['path']} ({file['lines']} líneas)\n")
            
            f.write(f"\n## Historias de Usuario\n\n")
            f.write(user_stories)
        
        # Formatear respuesta
        return jsonify({
            "user_stories": user_stories,
            "analyzed_files": analyzed_files,
            "directory_tree": directory_tree,
            "project_stats": project_stats,
            "output_file": output_path,
            "token_usage": {
                "prompt_tokens": tokens_prompt,
                "completion_tokens": tokens_completion,
                "total_tokens": tokens_total
            }
        })
    
    except Exception as e:
        print(f"Error al generar historias de usuario: {e}")
        return jsonify({
            "error": str(e), 
            "directory_tree": directory_tree,
            "analyzed_files": analyzed_files if 'analyzed_files' in locals() else []
        }), 500
    