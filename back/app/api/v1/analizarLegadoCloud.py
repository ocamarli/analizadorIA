# app/__init__.py - Versión actualizada con análisis C++ legacy
from flask import Blueprint, request, jsonify
from datetime import timedelta
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_pymongo import PyMongo
from flask_jsonpify import jsonify
from config import config
from langchain_community.chat_models import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import glob
import os
import datetime
import json
import re
import tempfile
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename
import PyPDF2

# Importar tus blueprints existentes
from app.modulos.chatOpenAi import chat_bp
from app.modulos.shearchDocument import search_bp

# Azure imports para Blob Storage
try:
    from azure.storage.blob import BlobServiceClient, BlobClient
    from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
    AZURE_AVAILABLE = True
except ImportError:
    print("Azure SDK no disponible. Funcionará sin Blob Storage.")
    AZURE_AVAILABLE = False

from openai import AzureOpenAI
jwt = JWTManager()

# Tu configuración existente
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

COGNITIVE_SEARCH_ENDPOINT = "https://azuresearhdemobside.search.windows.net"
COGNITIVE_SEARCH_INDEX = "azureblob-index"
COGNITIVE_SEARCH_API_KEY = "YdBHzUf4al4bPNDgDOLLc9XDnPaxucfrBU47RQbXtRAzSeCujuVS"
search_client = SearchClient(COGNITIVE_SEARCH_ENDPOINT, COGNITIVE_SEARCH_INDEX, AzureKeyCredential(COGNITIVE_SEARCH_API_KEY))

# Configuración Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
BLOB_CONTAINER_NAME = os.getenv("BLOB_CONTAINER_NAME", "cpp-legacy-analysis")

# Configurar cliente de Azure Blob Storage
blob_service_client = None
if AZURE_AVAILABLE and AZURE_STORAGE_CONNECTION_STRING:
    try:
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        # Crear contenedor si no existe
        try:
            blob_service_client.create_container(BLOB_CONTAINER_NAME)
            print(f"Contenedor {BLOB_CONTAINER_NAME} creado o ya existe")
        except ResourceExistsError:
            print(f"Contenedor {BLOB_CONTAINER_NAME} ya existe")
    except Exception as e:
        print(f"Error configurando Azure Blob Storage: {e}")
        blob_service_client = None

# Cliente OpenAI (usando tu configuración existente)
openai_client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://openaidemobside.openai.azure.com"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY", "6076ii7OpLiuTEKYsEVvWyt57RYjzb8d4hDwZRqKuokBi1WTuKZ9JQQJ99AJACYeBjFXJ3w3AAABACOGfwuS"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
)

# Configuración de LangChain (tu configuración existente)
llm = AzureChatOpenAI(
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
    openai_api_key=os.getenv("AZURE_OPENAI_API_KEY", "6076ii7OpLiuTEKYsEVvWyt57RYjzb8d4hDwZRqKuokBi1WTuKZ9JQQJ99AJACYeBjFXJ3w3AAABACOGfwuS"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://openaidemobside.openai.azure.com"),
    temperature=0.7
)

# Tu blueprint existente
analizarLegadoCloud_bp = Blueprint('analizarLegadoCloud', __name__)

# Clase para análisis de C++
class CppLegacyAnalyzer:
    def __init__(self):
        self.supported_extensions = ['.cpp', '.cc', '.cxx', '.c', '.h', '.hpp', '.hxx', '.def', '.rc']
        self.config_files = ['CMakeLists.txt', 'Makefile', '*.vcxproj', '*.vcproj', '*.sln', '*.pro']
        
    def analyze_file_content(self, file_path, content):
        """Analiza el contenido de un archivo C++"""
        analysis = {
            'file_path': file_path,
            'size': len(content.encode('utf-8')),
            'lines': content.count('\n') + 1,
            'includes': [],
            'functions': [],
            'classes': [],
            'mfc_patterns': [],
            'complexity_score': 0
        }
        
        # Extraer includes
        includes = re.findall(r'#include\s*[<"](.*?)[>"]', content)
        analysis['includes'] = includes
        
        # Detectar clases
        classes = re.findall(r'class\s+(\w+)(?:\s*:\s*(?:public|private|protected)\s+(\w+))?', content)
        analysis['classes'] = [{'name': cls[0], 'base': cls[1] if cls[1] else None} for cls in classes]
        
        # Detectar funciones
        functions = re.findall(r'^\s*(?:static\s+|virtual\s+|inline\s+)*(\w+(?:\s*\*|\s*&)*)\s+(\w+)\s*\([^{]*\)(?:\s*const)?\s*(?:{|;)', content, re.MULTILINE)
        analysis['functions'] = [{'return_type': func[0].strip(), 'name': func[1].strip()} for func in functions]
        
        # Detectar patrones MFC
        mfc_includes = ['afxwin.h', 'afxext.h', 'afxdlgs.h', 'afxcmn.h', 'afxcview.h']
        mfc_patterns = []
        
        if any(inc in includes for inc in mfc_includes):
            mfc_patterns.append('MFC_Framework')
        
        if re.search(r'class\s+\w+\s*:\s*public\s+CDialog', content):
            mfc_patterns.append('MFC_Dialog')
        if re.search(r'class\s+\w+\s*:\s*public\s+CWnd', content):
            mfc_patterns.append('MFC_Window')
        if re.search(r'class\s+\w+\s*:\s*public\s+CView', content):
            mfc_patterns.append('MFC_View')
        if re.search(r'class\s+\w+\s*:\s*public\s+CDocument', content):
            mfc_patterns.append('MFC_Document')
            
        analysis['mfc_patterns'] = mfc_patterns
        
        # Calcular complejidad básica
        complexity = 0
        complexity += content.count('if ') * 1
        complexity += content.count('for ') * 2
        complexity += content.count('while ') * 2
        complexity += content.count('switch ') * 3
        complexity += len(analysis['functions']) * 1
        complexity += len(analysis['classes']) * 2
        
        analysis['complexity_score'] = complexity
        
        return analysis

    def upload_to_blob(self, file_path, content, analysis_id):
        """Sube archivo a Azure Blob Storage"""
        if not blob_service_client:
            return None
            
        try:
            blob_name = f"{analysis_id}/source_files/{os.path.basename(file_path)}"
            blob_client = blob_service_client.get_blob_client(
                container=BLOB_CONTAINER_NAME, 
                blob=blob_name
            )
            
            # Subir contenido
            blob_client.upload_blob(content, overwrite=True)
            return blob_client.url
        except Exception as e:
            print(f"Error subiendo a blob: {e}")
            return None

    def save_analysis_to_blob(self, analysis_result, analysis_id):
        """Guarda el resultado del análisis en Blob Storage"""
        if not blob_service_client:
            return None
            
        try:
            blob_name = f"{analysis_id}/analysis_result.json"
            blob_client = blob_service_client.get_blob_client(
                container=BLOB_CONTAINER_NAME, 
                blob=blob_name
            )
            
            json_content = json.dumps(analysis_result, indent=2, ensure_ascii=False)
            blob_client.upload_blob(json_content, overwrite=True)
            return blob_client.url
        except Exception as e:
            print(f"Error guardando análisis en blob: {e}")
            return None

# Instancia del analizador
cpp_analyzer = CppLegacyAnalyzer()

# NUEVO ENDPOINT: Análisis de código C++ legacy
@analizarLegadoCloud_bp.route('/analizarCppLegacy', methods=['POST'])
def analyze_cpp_legacy():
    """Nuevo endpoint para análisis específico de C++ legacy"""
    data = request.json
    code_path = data.get('code_path')
    
    if not code_path:
        return jsonify({"error": "Debes proporcionar la ruta del código"}), 400
    
    # Normalizar ruta
    normalized_path = code_path.replace('\\', '/')
    print(f"Analizando código C++ legacy en: {normalized_path}")
    
    # Generar ID único para este análisis
    analysis_id = f"cpp_analysis_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    
    try:
        # Función para construir árbol de directorios (compatible con tu frontend)
        def build_directory_tree(start_path):
            tree = {"name": os.path.basename(start_path), "type": "folder", "children": []}
            
            try:
                for item in os.listdir(start_path):
                    item_path = os.path.join(start_path, item)
                    
                    if item.startswith('.'):
                        continue
                        
                    if os.path.isdir(item_path):
                        tree["children"].append(build_directory_tree(item_path))
                    else:
                        _, ext = os.path.splitext(item)
                        if ext.lower() in cpp_analyzer.supported_extensions:
                            tree["children"].append({
                                "name": item,
                                "type": "file",
                                "extension": ext.lower()
                            })
            except Exception as e:
                print(f"Error al construir árbol en {start_path}: {e}")
            
            return tree

        directory_tree = build_directory_tree(normalized_path)
        
        # Encontrar archivos C++
        cpp_files = []
        for ext in cpp_analyzer.supported_extensions:
            cpp_files.extend(glob.glob(f"{normalized_path}/**/*{ext}", recursive=True))
        
        if not cpp_files:
            return jsonify({
                "error": "No se encontraron archivos C++ en la ruta especificada",
                "directory_tree": directory_tree
            }), 404
        
        # Limitar archivos para análisis
        file_limit = 100
        cpp_files = cpp_files[:file_limit]
        
        # Estadísticas del proyecto
        project_stats = {
            "total_files": len(cpp_files),
            "analyzed_files": len(cpp_files),
            "extensions": {},
            "total_lines": 0,
            "mfc_usage": 0,
            "complexity_total": 0
        }
        
        # Analizar archivos
        all_analyses = []
        analyzed_files = []
        
        for file_path in cpp_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                file_analysis = cpp_analyzer.analyze_file_content(file_path, content)
                all_analyses.append(file_analysis)
                
                # Estadísticas
                _, ext = os.path.splitext(file_path)
                ext = ext.lower()
                project_stats["extensions"][ext] = project_stats["extensions"].get(ext, 0) + 1
                project_stats["total_lines"] += file_analysis['lines']
                project_stats["mfc_usage"] += len(file_analysis['mfc_patterns'])
                project_stats["complexity_total"] += file_analysis['complexity_score']
                
                # Para el frontend (compatible con tu estructura existente)
                analyzed_files.append({
                    "name": os.path.basename(file_path),
                    "path": os.path.relpath(file_path, normalized_path),
                    "extension": ext,
                    "size": file_analysis['size'],
                    "lines": file_analysis['lines']
                })
                
                # Subir a Blob Storage si está disponible
                if blob_service_client:
                    blob_url = cpp_analyzer.upload_to_blob(file_path, content, analysis_id)
                    if blob_url:
                        file_analysis['blob_url'] = blob_url
                        
            except Exception as e:
                print(f"Error al analizar archivo {file_path}: {e}")
                continue
        
        # Preparar contexto para análisis con IA
        context_summary = {
            "total_files": len(all_analyses),
            "total_classes": sum(len(a.get('classes', [])) for a in all_analyses),
            "total_functions": sum(len(a.get('functions', [])) for a in all_analyses),
            "mfc_detected": project_stats["mfc_usage"] > 0,
            "main_includes": list(set(inc for a in all_analyses for inc in a.get('includes', []))),
            "complexity_score": project_stats["complexity_total"]
        }
        
        # Generar análisis con OpenAI
        try:
            analysis_prompt = f"""
            Analiza este proyecto C++ legacy y proporciona un análisis en formato JSON:
            
            ESTADÍSTICAS:
            - Archivos: {context_summary['total_files']}
            - Clases: {context_summary['total_classes']}  
            - Funciones: {context_summary['total_functions']}
            - MFC detectado: {'Sí' if context_summary['mfc_detected'] else 'No'}
            - Complejidad: {context_summary['complexity_score']}
            
            INCLUDES PRINCIPALES: {', '.join(context_summary['main_includes'][:15])}
            
            Responde en JSON con:
            {{
                "architecture_summary": "Descripción de la arquitectura",
                "technology_stack": ["tecnología1", "tecnología2"],
                "main_components": ["componente1", "componente2"],
                "modernization_suggestions": [
                    {{"category": "UI", "suggestion": "Migrar de MFC a...", "effort": "Alto"}}
                ],
                "technical_debt": "Alto/Medio/Bajo",
                "migration_complexity": "Alto/Medio/Bajo"
            }}
            """
            
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Eres un experto en análisis de código C++ legacy y modernización."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            ai_analysis = json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error en análisis con IA: {e}")
            ai_analysis = {
                "architecture_summary": "Aplicación C++ legacy detectada",
                "technology_stack": ["C++", "MFC" if context_summary['mfc_detected'] else "Win32"],
                "main_components": ["UI Layer", "Business Logic", "Data Access"],
                "modernization_suggestions": [
                    {"category": "Framework", "suggestion": "Considerar migración a framework moderno", "effort": "Alto"}
                ],
                "technical_debt": "Alto",
                "migration_complexity": "Alto"
            }
        
        # Resultado final
        final_result = {
            "analysis_id": analysis_id,
            "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "project_stats": project_stats,
            "analyzed_files": analyzed_files,
            "directory_tree": directory_tree,
            "ai_analysis": ai_analysis,
            "blob_storage_used": blob_service_client is not None
        }
        
        # Guardar en archivo local
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"cpp_legacy_analysis_{timestamp}.json"
        
        # Intentar guardar en la ruta del proyecto, si no, en directorio actual
        try:
            output_path = os.path.join(normalized_path, output_filename)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(final_result, f, indent=2, ensure_ascii=False)
        except:
            output_path = output_filename
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(final_result, f, indent=2, ensure_ascii=False)
        
        # Guardar en Azure Blob Storage
        blob_url = None
        if blob_service_client:
            blob_url = cpp_analyzer.save_analysis_to_blob(final_result, analysis_id)
        
        # Respuesta compatible con tu frontend
        return jsonify({
            "analysis_id": analysis_id,
            "directory_tree": directory_tree,
            "project_stats": project_stats,
            "analyzed_files": analyzed_files,
            "architecture_summary": ai_analysis.get("architecture_summary", ""),
            "technology_stack": ai_analysis.get("technology_stack", []),
            "modernization_suggestions": ai_analysis.get("modernization_suggestions", []),
            "technical_debt": ai_analysis.get("technical_debt", "Medium"),
            "migration_complexity": ai_analysis.get("migration_complexity", "Medium"),
            "output_file": output_path,
            "blob_url": blob_url,
            "success": True
        })
        
    except Exception as e:
        print(f"Error general en análisis C++: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "directory_tree": directory_tree if 'directory_tree' in locals() else None
        }), 500

# Tu endpoint existente (mantenerlo sin cambios)
@analizarLegadoCloud_bp.route('/analizarLegadoCloud', methods=['POST'])
def analyze_user_stories():
    """Tu endpoint existente para análisis de PDFs - sin cambios"""
    # Verificar si hay archivos en la solicitud
    if 'files' not in request.files:
        return jsonify({"error": "No se encontraron archivos"}), 400
    
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return jsonify({"error": "No se seleccionaron archivos"}), 400
    
    # Crear directorio temporal para guardar archivos
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Procesar cada archivo PDF
        all_text = ""
        file_info = []
        
        for file in files:
            if file and file.filename.endswith('.pdf'):
                filename = secure_filename(file.filename)
                filepath = os.path.join(temp_dir, filename)
                file.save(filepath)
                
                # Extraer texto del PDF
                with open(filepath, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    num_pages = len(pdf_reader.pages)
                    
                    text = ""
                    for page_num in range(num_pages):
                        page = pdf_reader.pages[page_num]
                        text += page.extract_text()
                
                all_text += f"\n--- Documento: {filename} ---\n{text}\n"
                file_info.append({
                    "filename": filename,
                    "pages": num_pages,
                    "text_length": len(text)
                })
        
        # Si no hay texto extraído, devolver error
        if not all_text.strip():
            return jsonify({"error": "No se pudo extraer texto de los archivos PDF"}), 400
        
        # Analizar directamente con OpenAI
        analysis_result = analyze_with_openai_direct(all_text, len(file_info))
        
        # Guardar resultados en un directorio
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join("analysis_results", timestamp)
        os.makedirs(output_dir, exist_ok=True)
        
        # Guardar los archivos generados
        for file in analysis_result.get("generatedFiles", []):
            file_path = os.path.join(output_dir, file["name"])
            
            # Crear directorios intermedios si es necesario
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file["content"])
        
        # Devolver resultados al frontend
        return jsonify(analysis_result)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        # Limpiar archivos temporales
        for filename in os.listdir(temp_dir):
            os.unlink(os.path.join(temp_dir, filename))
        os.rmdir(temp_dir)

def analyze_with_openai_direct(document_text, num_files):
    """Tu función existente - sin cambios"""
    # Crear el mensaje del sistema para el modelo
    system_message = """Eres un experto en análisis de historias de usuario y requisitos de software.
    Tu tarea es analizar documentos que contienen historias de usuario, identificar y extraer estas historias,
    analizar problemas, generar recomendaciones técnicas, funcionales y no funcionales, y detectar información faltante.
    
    Debes responder en formato JSON con la siguiente estructura:
    {
        "filesAnalyzed": número de archivos analizados,
        "totalUserStories": número total de historias de usuario encontradas,
        "totalRecommendations": número total de recomendaciones,
        "userStories": [
            {
                "title": "Título representativo de la historia",
                "content": "Contenido original de la historia",
                "analysis": "Análisis detallado de la historia",
                "issues": [
                    {
                        "title": "Título del problema",
                        "description": "Descripción del problema",
                        "severity": "high/medium/low"
                    }
                ]
            }
        ],
        "recommendations": [
            {
                "title": "Título de la recomendación",
                "description": "Descripción detallada",
                "category": "functional/technical/non-functional",
                "severity": "high/medium/low",
                "tags": ["tag1", "tag2"]
            }
        ],
        "missingInformation": [
            {
                "story": "Referencia a la historia",
                "type": "Tipo de información faltante",
                "description": "Descripción de lo que falta"
            }
        ],
        "generatedFiles": [
            {
                "name": "nombre_del_archivo.extension",
                "content": "contenido del archivo"
            }
        ]
    }
    
    En generatedFiles, incluye archivos que ayuden a implementar o mejorar las historias de usuario,
    como prototipos de código, ejemplos, estructuras de archivos recomendadas, o documentación adicional.
    """
    
    # Crear mensaje para el usuario
    user_message = f"""
    Analiza el siguiente texto extraído de {num_files} documentos PDF que contienen historias de usuario 
    para un proyecto de software:
    
    {document_text}
    
    En tu análisis:
    1. Identifica todas las historias de usuario presentes
    2. Detecta problemas en las historias (ambigüedad, falta de detalle, etc.)
    3. Genera recomendaciones técnicas, funcionales y no funcionales
    4. Identifica información faltante en cada historia
    5. Sugiere mejoras y refinamientos
    6. Genera archivos de ejemplo que podrían ayudar a implementar estas historias (incluye al menos 3 archivos)
    
    Asegúrate de que tu respuesta esté en el formato JSON solicitado.
    """
    
    try:
        # Llamada a Azure OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # Asegúrate de que este modelo esté disponible en tu despliegue
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.2,
            max_tokens=4000,
            response_format={"type": "json_object"}
        )
        
        # Acceder a la respuesta
        result_json = response.choices[0].message.content
        
        # Convertir la respuesta JSON en un objeto Python
        result_data = json.loads(result_json)
        
        return result_data
        
    except Exception as e:
        print(f"Error en la llamada a OpenAI: {e}")
        raise