from flask import Blueprint, request, jsonify
from datetime import timedelta
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_pymongo import PyMongo
from flask_jsonpify import jsonify
from config import config
from langchain_community.chat_models import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import PromptTemplate
import os
import datetime
import json
import re
import tempfile
import shutil
import zipfile
from werkzeug.utils import secure_filename
 
# Blueprint
analizarCodigoo_bp = Blueprint('analizarCodigoo', __name__)


llm = AzureChatOpenAI(
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1"),
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
    openai_api_key=os.getenv("AZURE_OPENAI_API_KEY", "6076ii7OpLiuTEKYsEVvWyt57RYjzb8d4hDwZRqKuokBi1WTuKz9JQQJ99AJACYeBjFXJ3w3AAABACOGfwuS"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://openaidemobside.openai.azure.com"),
    temperature=0.7
)

# Configuración para subida de archivos
ALLOWED_EXTENSIONS = {'.c', '.cpp', '.cc', '.cxx', '.c++', '.h', '.hpp', '.hxx', '.h++', 
                     '.rc', '.def', '.mk', '.mak', '.cmake', '.txt', '.md', '.json', '.xml'}
MAX_FILES = 50
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB por archivo

def allowed_file(filename):
    return os.path.splitext(filename.lower())[1] in ALLOWED_EXTENSIONS

# Endpoint corregido para manejar archivos ZIP con análisis completo
# Endpoint corregido para manejar archivos ZIP con análisis completo
@analizarCodigoo_bp.route('/analizarCodigoo/zip', methods=['POST'])
def analyze_zip_file():
    if 'zip_file' not in request.files:
        return jsonify({"error": "No se envió archivo ZIP"}), 400
    
    zip_file = request.files['zip_file']
    project_name = request.form.get('project_name', 'Proyecto desde ZIP')
    
    if zip_file.filename == '' or not zip_file.filename.lower().endswith('.zip'):
        return jsonify({"error": "Debe ser un archivo ZIP válido"}), 400
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Guardar archivo ZIP
        zip_path = os.path.join(temp_dir, 'project.zip')
        zip_file.save(zip_path)
        
        # Extraer ZIP
        extract_dir = os.path.join(temp_dir, 'extracted')
        os.makedirs(extract_dir)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # Buscar archivos C/C++ en el directorio extraído
        uploaded_files = []
        total_size = 0
        
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                file_path = os.path.join(root, file)
                _, ext = os.path.splitext(file)
                
                if ext.lower() in ALLOWED_EXTENSIONS:
                    try:
                        file_size = os.path.getsize(file_path)
                        if file_size <= MAX_FILE_SIZE:
                            # Calcular ruta relativa para mantener estructura
                            rel_path = os.path.relpath(file_path, extract_dir)
                            uploaded_files.append({
                                'original_name': rel_path,
                                'temp_path': file_path,
                                'size': file_size
                            })
                            total_size += file_size
                            
                            if len(uploaded_files) >= MAX_FILES:
                                break
                    except Exception as e:
                        print(f"Error procesando archivo {file}: {e}")
                        continue
            
            if len(uploaded_files) >= MAX_FILES:
                break
        
        if not uploaded_files:
            return jsonify({"error": "No se encontraron archivos C/C++ válidos en el ZIP"}), 400
        
        print(f"Procesando {len(uploaded_files)} archivos extraídos del ZIP")
        
        # Debug: Imprimir información de los archivos encontrados
        for i, file_info in enumerate(uploaded_files[:3]):  # Solo los primeros 3 para debug
            print(f"Archivo {i}: {file_info}")
        print("...")
        
        # ===============================
        # AQUÍ EMPIEZA LA LÓGICA COMPLETA DE ANÁLISIS
        # (La misma que tienes en el endpoint principal)
        # ===============================
        
        # Función para analizar funciones y estructuras en código C/C++
        def analyze_cpp_code(content):
            functions = []
            classes = []
            structs = []
            includes = []
            defines = []
            
            # Buscar includes
            include_pattern = r'#include\s*[<"](.*?)[>"]'
            includes = re.findall(include_pattern, content)
            
            # Buscar defines
            define_pattern = r'#define\s+(\w+)'
            defines = re.findall(define_pattern, content)
            
            # Buscar funciones (patrón simplificado)
            function_pattern = r'(?:^|\n)\s*(?:static\s+|inline\s+|extern\s+)?(?:const\s+)?(?:\w+\s+)*(\w+)\s*\([^)]*\)\s*(?:\{|;)'
            functions = re.findall(function_pattern, content, re.MULTILINE)
            
            # Buscar estructuras
            struct_pattern = r'(?:struct|typedef\s+struct)\s+(\w+)'
            structs = re.findall(struct_pattern, content)
            
            # Buscar clases (C++)
            class_pattern = r'class\s+(\w+)'
            classes = re.findall(class_pattern, content)
            
            return {
                "functions": functions[:10],
                "classes": classes,
                "structs": structs,
                "includes": includes[:15],
                "defines": defines[:10]
            }
        
        # Analizar archivos extraídos
        project_stats = {
            "total_files": len(uploaded_files),
            "analyzed_files": len(uploaded_files),
            "extensions": {},
            "total_lines": 0,
            "header_files": 0,
            "source_files": 0,
            "total_functions": 0,
            "total_classes": 0,
            "total_structs": 0,
            "common_includes": [],
            "common_defines": []
        }
        
        all_code = ""
        analyzed_files = []
        all_includes = []
        all_defines = []
        
        for file_info in uploaded_files:
            try:
                with open(file_info['temp_path'], 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = content.count('\n') + 1
                    
                    # Analizar código C/C++
                    analysis = analyze_cpp_code(content)
                    
                    # Obtener extensión
                    _, ext = os.path.splitext(file_info['original_name'])
                    ext = ext.lower()
                    
                    # Estadísticas por extensión
                    if ext in project_stats["extensions"]:
                        project_stats["extensions"][ext] += 1
                    else:
                        project_stats["extensions"][ext] = 1
                    
                    # Clasificar archivos
                    if ext in ['.h', '.hpp', '.hxx', '.h++']:
                        project_stats["header_files"] += 1
                    elif ext in ['.c', '.cpp', '.cc', '.cxx', '.c++']:
                        project_stats["source_files"] += 1
                    
                    # Agregar a archivos analizados
                    analyzed_files.append({
                        "name": os.path.basename(file_info['original_name']),
                        "path": file_info['original_name'],
                        "extension": ext,
                        "size": file_info['size'],
                        "lines": lines,
                        "functions_count": len(analysis["functions"]),
                        "classes_count": len(analysis["classes"]),
                        "structs_count": len(analysis["structs"]),
                        "includes_count": len(analysis["includes"])
                    })
                    
                    # Acumular estadísticas
                    project_stats["total_lines"] += lines
                    project_stats["total_functions"] += len(analysis["functions"])
                    project_stats["total_classes"] += len(analysis["classes"])
                    project_stats["total_structs"] += len(analysis["structs"])
                    all_includes.extend(analysis["includes"])
                    all_defines.extend(analysis["defines"])
                    
                    # Agregar al código completo
                    all_code += f"\n\n--- Archivo: {file_info['original_name']} ({lines} líneas) ---\n"
                    all_code += f"Funciones encontradas: {len(analysis['functions'])}\n"
                    all_code += f"Clases encontradas: {len(analysis['classes'])}\n"
                    all_code += f"Estructuras encontradas: {len(analysis['structs'])}\n"
                    all_code += f"Includes: {len(analysis['includes'])}\n\n"
                    all_code += content
                    
            except Exception as e:
                print(f"Error al leer archivo {file_info['original_name']}: {e}")
        
        # Analizar includes y defines más comunes
        if all_includes:
            from collections import Counter
            include_counter = Counter(all_includes)
            project_stats["common_includes"] = include_counter.most_common(10)
        
        if all_defines:
            from collections import Counter
            define_counter = Counter(all_defines)
            project_stats["common_defines"] = define_counter.most_common(10)
        
        # Crear prompts especializados para C/C++ (los mismos que ya tienes)
        user_stories_prompt = PromptTemplate(
            input_variables=["project_name", "project_stats", "all_code"],
            template="""Eres un asistente especializado en análisis de código legacy C/C++ y generación de documentación ágil.
            Tu tarea es analizar código fuente C/C++ legacy y generar historias de usuario detalladas que capturen la funcionalidad del código.
            
            PROYECTO: {project_name}
            
            CONTEXTO ESPECIAL PARA CÓDIGO C/C++ LEGACY:
            - Enfócate en las funciones principales y módulos del sistema
            - Identifica patrones de programación estructurada y orientada a objetos
            - Considera las dependencias entre archivos .h y .cpp
            - Analiza el uso de bibliotecas estándar y externas
            - Identifica estructuras de datos y algoritmos principales
            
            Analiza el siguiente código C/C++ legacy y genera historias de usuario que describan su funcionalidad.
            Para cada módulo, biblioteca o funcionalidad principal, genera una historia de usuario en formato:
            
            Como [tipo de usuario/sistema],
            Quiero [acción/funcionalidad],
            Para [beneficio/valor de negocio].
            
            Incluye criterios de aceptación técnicos específicos para C/C++.
            Genera al menos 8 historias de usuario, cubriendo:
            - Funcionalidades principales del sistema
            - Gestión de memoria y recursos
            - Interfaces y APIs
            - Procesamiento de datos
            - Integración con sistemas externos
            
            ESTADÍSTICAS DEL PROYECTO C/C++:
            {project_stats}
            
            CÓDIGO C/C++ A ANALIZAR:
            {all_code}"""
        )
        
        def_analysis_prompt = PromptTemplate(
            input_variables=["project_name", "project_stats", "all_code"],
            template="""Eres un analista de sistemas experto en definición de requerimientos funcionales para sistemas legacy C/C++.
            Tu tarea es analizar código fuente C/C++ para extraer información relevante para un Documento de 
            Definición de Requerimientos Funcionales (DEF).
            
            PROYECTO: {project_name}
            
            ANÁLISIS ESPECÍFICO PARA PROYECTOS C/C++ LEGACY:
            - Arquitectura del sistema (módulos, bibliotecas, dependencias)
            - Gestión de memoria y recursos
            - Interfaces y APIs públicas
            - Estructuras de datos principales
            - Algoritmos y lógica de negocio
            - Configuración y parámetros del sistema
            - Dependencias externas y bibliotecas
            - Compatibilidad con diferentes plataformas
            - Rendimiento y optimizaciones
            
            Analiza el siguiente código C/C++ para extraer información relevante para un DEF.
            
            INFORMACIÓN A EXTRAER:
            1. Stakeholders técnicos (desarrolladores, administradores, usuarios finales)
            2. Procesos de negocio implementados en el código
            3. Requerimientos funcionales principales
            4. Requerimientos no funcionales (rendimiento, memoria, etc.)
            5. Reglas de negocio y validaciones
            6. Restricciones técnicas y limitaciones
            7. Dependencias del sistema (bibliotecas, SO, hardware)
            8. Arquitectura y diseño del sistema
            9. Datos de entrada y salida
            10. Integración con otros sistemas
            11. Configuración y parametrización
            12. Manejo de errores y excepciones
            
            ESTADÍSTICAS DEL PROYECTO C/C++:
            {project_stats}
            
            CÓDIGO FUENTE C/C++:
            {all_code}
            
            Proporciona la información en formato estructurado y detallado específico para sistemas C/C++ legacy."""
        )
        
        # Preparar datos para los prompts
        stats_text = f"""- Total de archivos: {project_stats["total_files"]}
- Archivos analizados: {project_stats["analyzed_files"]}
- Total de líneas de código: {project_stats["total_lines"]}
- Archivos de cabecera (.h/.hpp): {project_stats["header_files"]}
- Archivos fuente (.c/.cpp): {project_stats["source_files"]}
- Total de funciones encontradas: {project_stats["total_functions"]}
- Total de clases encontradas: {project_stats["total_classes"]}
- Total de estructuras encontradas: {project_stats["total_structs"]}
- Includes más comunes: {project_stats["common_includes"][:5]}"""
        
        print(f"Generando historias de usuario para proyecto: {project_name}")
        
        # Generar Historias de Usuario usando LangChain
        user_stories_formatted_prompt = user_stories_prompt.format(
            project_name=project_name,
            project_stats=stats_text,
            all_code=all_code
        )
        
        user_stories_response = llm.invoke([
            SystemMessage(content="Eres un especialista en análisis de código C/C++ legacy y generación de documentación ágil."),
            HumanMessage(content=user_stories_formatted_prompt)
        ])
        
        user_stories = user_stories_response.content
        
        print(f"Generando análisis DEF para proyecto: {project_name}")
        
        # Generar análisis DEF usando LangChain
        def_formatted_prompt = def_analysis_prompt.format(
            project_name=project_name,
            project_stats=stats_text,
            all_code=all_code
        )
        
        def_response = llm.invoke([
            SystemMessage(content="Eres un analista de sistemas experto en definición de requerimientos funcionales para sistemas C/C++ legacy."),
            HumanMessage(content=def_formatted_prompt)
        ])
        
        def_analysis = def_response.content
        
        # Generar timestamp para referencia
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Construir árbol de archivos desde los archivos extraídos
        def build_tree_from_files(files):
            tree = {
                "name": project_name,
                "type": "folder",
                "children": []
            }
            
            # Crear estructura de carpetas basada en rutas de archivos
            for file_info in files:
                # Usar 'path' en lugar de 'original_name' ya que esa es la clave que definimos en analyzed_files
                file_path = file_info.get('path', file_info.get('name', ''))
                if not file_path:
                    continue
                    
                path_parts = file_path.replace('\\', '/').split('/')
                current_node = tree
                
                # Crear carpetas intermedias
                for i, part in enumerate(path_parts[:-1]):
                    if not part:  # Saltar partes vacías
                        continue
                        
                    # Buscar si la carpeta ya existe
                    folder = next((child for child in current_node["children"] 
                                 if child["name"] == part and child["type"] == "folder"), None)
                    
                    if not folder:
                        folder = {
                            "name": part,
                            "type": "folder",
                            "children": []
                        }
                        current_node["children"].append(folder)
                    
                    current_node = folder
                
                # Agregar archivo
                filename = path_parts[-1] if path_parts else file_info.get('name', 'unknown')
                _, ext = os.path.splitext(filename)
                current_node["children"].append({
                    "name": filename,
                    "type": "file",
                    "extension": ext.lower(),
                    "path": file_path
                })
            
            return tree
        
        directory_tree = build_tree_from_files(analyzed_files)
        
        print(f"Análisis completado. Generadas {len(user_stories.split('Como')) - 1} historias de usuario")
        
        return jsonify({
            "success": True,
            "timestamp": timestamp,
            "user_stories": user_stories,
            "def_analysis": def_analysis,
            "analyzed_files": analyzed_files,
            "directory_tree": directory_tree,
            "project_stats": project_stats,
            "documentation_found": False,
            "analyzed_documents": [],
            "code_analysis": {
                "language": "C/C++",
                "total_functions": project_stats["total_functions"],
                "total_classes": project_stats["total_classes"],
                "total_structs": project_stats["total_structs"],
                "header_files": project_stats["header_files"],
                "source_files": project_stats["source_files"],
                "common_includes": project_stats["common_includes"][:5]
            },
            "summary": {
                "files_analyzed": len(analyzed_files),
                "total_lines_analyzed": project_stats["total_lines"],
                "documentation_files_found": 0,
                "analysis_completed": True,
                "upload_method": "zip_upload"
            }
        })
    
    except Exception as e:
        print(f"Error al analizar ZIP: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": f"Error procesando ZIP: {str(e)}",
            "success": False
        }), 500
    
    finally:
        try:
            shutil.rmtree(temp_dir)
        except Exception as cleanup_error:
            print(f"Error al limpiar archivos temporales: {cleanup_error}")
# Endpoint adicional para subir archivos ZIP
@analizarCodigoo_bp.route('/analizarCodigoo/zip', methods=['POST'])
def analyaze_zip_file():
    if 'zip_file' not in request.files:
        return jsonify({"error": "No se envió archivo ZIP"}), 400
    
    zip_file = request.files['zip_file']
    project_name = request.form.get('project_name', 'Proyecto desde ZIP')
    
    if zip_file.filename == '' or not zip_file.filename.lower().endswith('.zip'):
        return jsonify({"error": "Debe ser un archivo ZIP válido"}), 400
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Guardar archivo ZIP
        zip_path = os.path.join(temp_dir, 'project.zip')
        zip_file.save(zip_path)
        
        # Extraer ZIP
        extract_dir = os.path.join(temp_dir, 'extracted')
        os.makedirs(extract_dir)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # Buscar archivos C/C++ en el directorio extraído
        files_data = []
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                file_path = os.path.join(root, file)
                _, ext = os.path.splitext(file)
                
                if ext.lower() in ALLOWED_EXTENSIONS:
                    try:
                        file_size = os.path.getsize(file_path)
                        if file_size <= MAX_FILE_SIZE:
                            files_data.append({
                                'original_name': file,
                                'temp_path': file_path,
                                'size': file_size
                            })
                            
                            if len(files_data) >= MAX_FILES:
                                break
                    except Exception as e:
                        print(f"Error procesando archivo {file}: {e}")
                        continue
        
        if not files_data:
            return jsonify({"error": "No se encontraron archivos C/C++ válidos en el ZIP"}), 400
        
        # Procesar igual que el endpoint normal
        # (Aquí iría la misma lógica de análisis que en el endpoint principal)
        # Por brevedad, retorno solo un mensaje de éxito
        
        return jsonify({
            "success": True,
            "message": f"ZIP procesado exitosamente. Se encontraron {len(files_data)} archivos C/C++",
            "files_found": len(files_data)
        })
    
    except Exception as e:
        return jsonify({"error": f"Error procesando ZIP: {str(e)}"}), 500
    
    finally:
        try:
            shutil.rmtree(temp_dir)
        except Exception as cleanup_error:
            print(f"Error al limpiar archivos temporales: {cleanup_error}")