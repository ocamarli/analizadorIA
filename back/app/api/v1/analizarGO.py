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
import glob
import os
import datetime
import json
import re
 
# Blueprint
analizarGo_bp = Blueprint('analizarGO', __name__)

# Configuración de LangChain (tu configuración existente)
llm = AzureChatOpenAI(
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1"),
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
    openai_api_key=os.getenv("AZURE_OPENAI_API_KEY", "6076ii7OpLiuTEKYsEVvWyt57RYjzb8d4hDwZRqKuokBi1WTuKz9JQQJ99AJACYeBjFXJ3w3AAABACOGfwuS"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://openaidemobside.openai.azure.com"),
    temperature=0.7
)

@analizarGo_bp.route('/analizarCodigoGO', methods=['POST'])
def generate_user_stories():
    data = request.json
    code_path = data.get('code_path')
    normalized = code_path.replace('\\', '/')
    code_path = normalized
    print(f"Analizando código Go en: {code_path}")
    
    # Límite de archivos a analizar (proyectos Go suelen ser más modulares)
    file_limit = 25
    
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
                    # Incluir archivos con extensiones soportadas para Go
                    _, ext = os.path.splitext(item)
                    if ext.lower() in ['.go', '.mod', '.sum', '.yaml', '.yml', '.json', '.toml', 
                                     '.txt', '.md', '.dockerfile', '.proto', '.sql']:
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
    
    # Recolectar archivos de código Go recursivamente
    code_files = []
    go_extensions = ['.go']
    
    for ext in go_extensions:
        code_files.extend(glob.glob(f"{code_path}/**/*{ext}", recursive=True))
    
    # Buscar archivos de configuración y documentación importantes para proyectos Go
    documentation_files = []
    important_files = [
        'README.md', 'README.txt', 'README', 'INSTALL', 'INSTALL.txt',
        'go.mod', 'go.sum', 'Makefile', 'makefile', 'docker-compose.yml', 'docker-compose.yaml',
        'Dockerfile', 'dockerfile', '.dockerignore',
        'main.go', 'config.go', 'config.yaml', 'config.yml', 'config.json', 'config.toml',
        '*.proto', '*.sql', 'migrate.sql', 'schema.sql',
        'CHANGELOG', 'CHANGELOG.md', 'CHANGES', 'HISTORY',
        'LICENSE', 'LICENSE.txt', 'COPYING', 'LICENSE.md',
        'AUTHORS', 'CONTRIBUTORS', 'MAINTAINERS',
        '.env', '.env.example', '.env.local',
        'swagger.json', 'swagger.yaml', 'swagger.yml',
        '*.docx', '*.doc', '*.pdf', '*.txt'
    ]
    
    for file_pattern in important_files:
        if '*' in file_pattern:
            matches = glob.glob(f"{code_path}/**/{file_pattern}", recursive=True)
        else:
            matches = glob.glob(f"{code_path}/**/{file_pattern}", recursive=True)
        documentation_files.extend(matches)
    
    # Ordenar archivos por tamaño (archivos más pequeños primero para mejor análisis)
    code_files.sort(key=lambda f: os.path.getsize(f) if os.path.exists(f) else 0)
    
    if not code_files:
        return jsonify({
            "error": "No se encontraron archivos de código Go en la ruta especificada",
            "directory_tree": directory_tree
        }), 404
    
    # Extraer estadísticas del proyecto Go
    project_stats = {
        "total_files": len(code_files),
        "analyzed_files": min(len(code_files), file_limit),
        "extensions": {},
        "largest_file": {"name": "", "size": 0},
        "total_lines": 0,
        "main_files": 0,
        "test_files": 0,
        "handler_files": 0,
        "usecase_files": 0,
        "entity_files": 0,
        "adapter_files": 0,
        "has_go_mod": False,
        "packages": set()
    }
    
    # Verificar si existe go.mod
    go_mod_files = glob.glob(f"{code_path}/**/go.mod", recursive=True)
    project_stats["has_go_mod"] = len(go_mod_files) > 0
    
    # Contar archivos por tipo y patrón
    for file in code_files:
        filename = os.path.basename(file).lower()
        _, ext = os.path.splitext(file)
        ext = ext.lower()
        
        if ext in project_stats["extensions"]:
            project_stats["extensions"][ext] += 1
        else:
            project_stats["extensions"][ext] = 1
        
        # Clasificar archivos por tipo/patrón común en Go
        if filename == 'main.go':
            project_stats["main_files"] += 1
        elif filename.endswith('_test.go'):
            project_stats["test_files"] += 1
        elif 'handler' in filename or 'controller' in filename:
            project_stats["handler_files"] += 1
        elif 'usecase' in filename or 'service' in filename:
            project_stats["usecase_files"] += 1
        elif 'entity' in filename or 'model' in filename or 'domain' in filename:
            project_stats["entity_files"] += 1
        elif 'adapter' in filename or 'repository' in filename:
            project_stats["adapter_files"] += 1
        
        # Verificar si es el archivo más grande
        file_size = os.path.getsize(file) if os.path.exists(file) else 0
        if file_size > project_stats["largest_file"]["size"]:
            project_stats["largest_file"] = {
                "name": os.path.basename(file),
                "size": file_size,
                "path": file
            }
    
    # Función para analizar código Go
    def analyze_go_code(content):
        functions = []
        structs = []
        interfaces = []
        imports = []
        package_name = ""
        methods = []
        
        # Buscar package
        package_pattern = r'^package\s+(\w+)'
        package_match = re.search(package_pattern, content, re.MULTILINE)
        if package_match:
            package_name = package_match.group(1)
        
        # Buscar imports
        import_pattern = r'import\s*(?:\(([^)]+)\)|"([^"]+)")'
        import_matches = re.findall(import_pattern, content, re.MULTILINE | re.DOTALL)
        for match in import_matches:
            if match[0]:  # Import block
                import_lines = match[0].strip().split('\n')
                for line in import_lines:
                    line = line.strip().strip('"')
                    if line and not line.startswith('//'):
                        imports.append(line)
            elif match[1]:  # Single import
                imports.append(match[1])
        
        # Buscar funciones
        function_pattern = r'func\s+(?:\([^)]*\)\s+)?(\w+)\s*\([^)]*\)(?:\s*\([^)]*\))?(?:\s*error)?\s*\{'
        functions = re.findall(function_pattern, content)
        
        # Buscar métodos (funciones con receiver)
        method_pattern = r'func\s+\(([^)]+)\)\s+(\w+)\s*\([^)]*\)(?:\s*\([^)]*\))?(?:\s*error)?\s*\{'
        method_matches = re.findall(method_pattern, content)
        methods = [(match[1], match[0].strip()) for match in method_matches]
        
        # Buscar estructuras
        struct_pattern = r'type\s+(\w+)\s+struct\s*\{'
        structs = re.findall(struct_pattern, content)
        
        # Buscar interfaces
        interface_pattern = r'type\s+(\w+)\s+interface\s*\{'
        interfaces = re.findall(interface_pattern, content)
        
        return {
            "package": package_name,
            "functions": functions[:15],
            "methods": methods[:15],
            "structs": structs,
            "interfaces": interfaces,
            "imports": imports[:20]
        }
    
    # Extraer y unir código de los archivos
    all_code = ""
    analyzed_files = []
    total_lines = 0
    code_analysis = {
        "total_functions": 0,
        "total_methods": 0,
        "total_structs": 0,
        "total_interfaces": 0,
        "common_imports": [],
        "packages": set()
    }
    
    all_imports = []
    
    for file in code_files[:file_limit]:
        try:
            with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.count('\n') + 1
                total_lines += lines
                
                # Analizar código Go
                analysis = analyze_go_code(content)
                
                # Añadir metadatos del archivo
                file_path = os.path.relpath(file, code_path)
                file_size = os.path.getsize(file)
                
                analyzed_files.append({
                    "name": os.path.basename(file),
                    "path": file_path,
                    "package": analysis["package"],
                    "size": file_size,
                    "lines": lines,
                    "functions_count": len(analysis["functions"]),
                    "methods_count": len(analysis["methods"]),
                    "structs_count": len(analysis["structs"]),
                    "interfaces_count": len(analysis["interfaces"]),
                    "imports_count": len(analysis["imports"])
                })
                
                # Acumular estadísticas
                code_analysis["total_functions"] += len(analysis["functions"])
                code_analysis["total_methods"] += len(analysis["methods"])
                code_analysis["total_structs"] += len(analysis["structs"])
                code_analysis["total_interfaces"] += len(analysis["interfaces"])
                all_imports.extend(analysis["imports"])
                if analysis["package"]:
                    code_analysis["packages"].add(analysis["package"])
                
                all_code += f"\n\n--- Archivo: {file_path} ({lines} líneas, package: {analysis['package']}) ---\n"
                all_code += f"Funciones: {len(analysis['functions'])}, Métodos: {len(analysis['methods'])}\n"
                all_code += f"Structs: {len(analysis['structs'])}, Interfaces: {len(analysis['interfaces'])}\n"
                all_code += f"Imports: {len(analysis['imports'])}\n\n"
                all_code += content
                
        except Exception as e:
            print(f"Error al leer archivo {file}: {e}")
    
    # Analizar imports más comunes
    if all_imports:
        from collections import Counter
        import_counter = Counter(all_imports)
        code_analysis["common_imports"] = import_counter.most_common(15)
    
    project_stats["total_lines"] = total_lines
    project_stats["packages"] = list(code_analysis["packages"])
    project_stats.update(code_analysis)
    
    # Extraer contenido de documentación para análisis DEF
    documentation_content = ""
    analyzed_docs = []
    
    for doc_file in documentation_files[:20]:
        try:
            if doc_file.endswith('.pdf'):
                # Leer PDF
                try:
                    import PyPDF2
                    with open(doc_file, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        pdf_text = ""
                        for page in pdf_reader.pages:
                            pdf_text += page.extract_text()
                        
                        analyzed_docs.append({
                            "name": os.path.basename(doc_file),
                            "path": os.path.relpath(doc_file, code_path),
                            "type": "pdf_document",
                            "pages": len(pdf_reader.pages)
                        })
                        
                        documentation_content += f"\n\n--- DOCUMENTO PDF: {os.path.relpath(doc_file, code_path)} ---\n\n{pdf_text[:2000]}..."
                except Exception as pdf_error:
                    print(f"Error al leer PDF {doc_file}: {pdf_error}")
                    
            elif doc_file.endswith(('.docx', '.doc')):
                # Para archivos Word, solo registrar su existencia
                analyzed_docs.append({
                    "name": os.path.basename(doc_file),
                    "path": os.path.relpath(doc_file, code_path),
                    "type": "word_document"
                })
                documentation_content += f"\n\n--- DOCUMENTO WORD ENCONTRADO: {os.path.relpath(doc_file, code_path)} ---\n"
            else:
                # Archivos de texto
                with open(doc_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    doc_path = os.path.relpath(doc_file, code_path)
                    
                    analyzed_docs.append({
                        "name": os.path.basename(doc_file),
                        "path": doc_path,
                        "type": "text_document",
                        "size": os.path.getsize(doc_file)
                    })
                    
                    documentation_content += f"\n\n--- DOCUMENTO: {doc_path} ---\n\n{content}"
        except Exception as e:
            print(f"Error al leer documento {doc_file}: {e}")
    
    # Crear prompts especializados para Go
    user_stories_prompt = PromptTemplate(
        input_variables=["project_stats", "all_code"],
        template="""Eres un asistente especializado en análisis de código Go y generación de documentación ágil.
        Tu tarea es analizar código fuente Go y generar historias de usuario detalladas que capturen la funcionalidad del código.
        
        CONTEXTO ESPECIAL PARA CÓDIGO GO:
        - Enfócate en la arquitectura hexagonal/clean architecture típica de Go
        - Identifica handlers HTTP, casos de uso, entidades de dominio y adaptadores
        - Analiza el uso de goroutines y concurrencia
        - Considera las interfaces y su implementación
        - Identifica middlewares, servicios y repositorios
        - Analiza APIs REST, GraphQL o gRPC
        - Considera la gestión de errores con error wrapping
        - Identifica patrones de inyección de dependencias
        
        Analiza el siguiente código Go y genera historias de usuario que describan su funcionalidad.
        Para cada módulo, servicio o funcionalidad principal, genera una historia de usuario en formato:
        
        Como [tipo de usuario/sistema],
        Quiero [acción/funcionalidad],
        Para [beneficio/valor de negocio].
        
        Incluye criterios de aceptación técnicos específicos para Go.
        Genera al menos 10 historias de usuario, cubriendo:
        - APIs y endpoints HTTP
        - Casos de uso y lógica de negocio
        - Entidades de dominio y modelos
        - Servicios externos y adaptadores
        - Middleware y autenticación
        - Manejo de datos y persistencia
        - Configuración y variables de entorno
        - Logging y monitoreo
        - Testing y validaciones
        - Concurrencia y performance
        
        ESTADÍSTICAS DEL PROYECTO GO:
        {project_stats}
        
        CÓDIGO GO A ANALIZAR:
        {all_code}"""
    )
    
    def_analysis_prompt = PromptTemplate(
        input_variables=["project_stats", "documentation_content", "all_code", "analyzed_docs_count"],
        template="""Eres un analista de sistemas experto en definición de requerimientos funcionales para aplicaciones Go.
        Tu tarea es analizar código fuente Go y documentación para extraer información relevante para un Documento de 
        Definición de Requerimientos Funcionales (DEF).
        
        ANÁLISIS ESPECÍFICO PARA PROYECTOS GO:
        - Arquitectura del sistema (clean architecture, hexagonal, microservicios)
        - APIs REST, GraphQL, gRPC y sus endpoints
        - Modelos de dominio y entidades de negocio
        - Casos de uso y servicios de aplicación
        - Repositorios y adaptadores de datos
        - Middleware y manejo de autenticación/autorización
        - Configuración de aplicación y variables de entorno
        - Integración con bases de datos (SQL, NoSQL)
        - Servicios externos y APIs de terceros
        - Manejo de concurrencia y goroutines
        - Sistema de logging y monitoreo
        - Validaciones y manejo de errores
        - Testing y calidad de código
        - Deployment y contenedores Docker
        - Performance y escalabilidad
        
        Analiza el siguiente código Go y documentación para extraer información relevante para un DEF.
        
        INFORMACIÓN A EXTRAER:
        1. Stakeholders técnicos y de negocio
        2. Procesos de negocio implementados
        3. Requerimientos funcionales por módulo
        4. APIs y contratos de servicios
        5. Modelos de datos y entidades
        6. Reglas de negocio y validaciones
        7. Integración con sistemas externos
        8. Requerimientos no funcionales (performance, seguridad, etc.)
        9. Configuración y parametrización
        10. Manejo de errores y excepciones
        11. Autenticación y autorización
        12. Logging y auditoria
        13. Testing y casos de prueba
        14. Deployment y infraestructura
        15. Monitoreo y métricas
        
        ESTADÍSTICAS DEL PROYECTO GO:
        {project_stats}
        
        DOCUMENTOS ENCONTRADOS: {analyzed_docs_count}
        
        DOCUMENTACIÓN ENCONTRADA:
        {documentation_content}
        
        CÓDIGO FUENTE GO:
        {all_code}
        
        Proporciona la información en formato estructurado y detallado específico para aplicaciones Go modernas."""
    )
    
    try:
        # Preparar datos para los prompts
        stats_text = f"""- Total de archivos: {project_stats["total_files"]}
- Archivos analizados: {project_stats["analyzed_files"]}
- Total de líneas de código: {project_stats["total_lines"]}
- Archivos main.go: {project_stats["main_files"]}
- Archivos de test: {project_stats["test_files"]}
- Archivos de handlers: {project_stats["handler_files"]}
- Archivos de casos de uso: {project_stats["usecase_files"]}
- Archivos de entidades: {project_stats["entity_files"]}
- Archivos de adaptadores: {project_stats["adapter_files"]}
- Total de funciones: {project_stats["total_functions"]}
- Total de métodos: {project_stats["total_methods"]}
- Total de structs: {project_stats["total_structs"]}
- Total de interfaces: {project_stats["total_interfaces"]}
- Packages identificados: {len(project_stats["packages"])}
- Tiene go.mod: {'Sí' if project_stats["has_go_mod"] else 'No'}
- Imports más comunes: {project_stats["common_imports"][:10]}"""
        
        # Generar Historias de Usuario usando LangChain
        user_stories_formatted_prompt = user_stories_prompt.format(
            project_stats=stats_text,
            all_code=all_code
        )
        
        user_stories_response = llm.invoke([
            SystemMessage(content="Eres un especialista en análisis de código Go y generación de documentación ágil."),
            HumanMessage(content=user_stories_formatted_prompt)
        ])
        
        user_stories = user_stories_response.content
        
        # Generar análisis DEF usando LangChain
        def_formatted_prompt = def_analysis_prompt.format(
            project_stats=stats_text,
            documentation_content=documentation_content,
            all_code=all_code,
            analyzed_docs_count=len(analyzed_docs)
        )
        
        def_response = llm.invoke([
            SystemMessage(content="Eres un analista de sistemas experto en definición de requerimientos funcionales para aplicaciones Go."),
            HumanMessage(content=def_formatted_prompt)
        ])
        
        def_analysis = def_response.content
        
        # Generar nombre de archivo con timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Guardar historias de usuario
        user_stories_filename = f"historias_usuario_go_{timestamp}.md"
        user_stories_path = os.path.join(code_path, user_stories_filename)
        
        with open(user_stories_path, 'w', encoding='utf-8') as f:
            f.write(f"# Historias de Usuario Generadas - Proyecto Go\n\n")
            f.write(f"Fecha de generación: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## Estadísticas del Proyecto Go\n\n")
            f.write(f"- **Total de archivos:** {project_stats['total_files']}\n")
            f.write(f"- **Archivos analizados:** {project_stats['analyzed_files']}\n")
            f.write(f"- **Total de líneas de código:** {project_stats['total_lines']}\n")
            f.write(f"- **Archivos main.go:** {project_stats['main_files']}\n")
            f.write(f"- **Archivos de test:** {project_stats['test_files']}\n")
            f.write(f"- **Handlers:** {project_stats['handler_files']}\n")
            f.write(f"- **Casos de uso:** {project_stats['usecase_files']}\n")
            f.write(f"- **Entidades:** {project_stats['entity_files']}\n")
            f.write(f"- **Adaptadores:** {project_stats['adapter_files']}\n")
            f.write(f"- **Total de funciones:** {project_stats['total_functions']}\n")
            f.write(f"- **Total de métodos:** {project_stats['total_methods']}\n")
            f.write(f"- **Total de structs:** {project_stats['total_structs']}\n")
            f.write(f"- **Total de interfaces:** {project_stats['total_interfaces']}\n")
            f.write(f"- **Packages:** {', '.join(project_stats['packages'])}\n")
            f.write(f"- **Tiene go.mod:** {'Sí' if project_stats['has_go_mod'] else 'No'}\n\n")
            
            if project_stats['common_imports']:
                f.write(f"## Imports Más Utilizados\n\n")
                for import_pkg, count in project_stats['common_imports'][:15]:
                    f.write(f"- `{import_pkg}` (usado {count} veces)\n")
                f.write("\n")
            
            f.write(f"## Archivos Analizados\n\n")
            for file in analyzed_files:
                f.write(f"- **{file['path']}** (package: {file['package']}, {file['lines']} líneas, {file['functions_count']} funciones, {file['methods_count']} métodos)\n")
            
            f.write(f"\n## Historias de Usuario\n\n")
            f.write(user_stories)
        
        # Guardar análisis DEF
        def_filename = f"analisis_def_go_{timestamp}.md"
        def_path = os.path.join(code_path, def_filename)
        
        with open(def_path, 'w', encoding='utf-8') as f:
            f.write(f"# Análisis DEF - Proyecto Go\n\n")
            f.write(f"Fecha de análisis: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## Información del Proyecto Go\n\n")
            f.write(f"- **Total de archivos de código:** {project_stats['total_files']}\n")
            f.write(f"- **Archivos de código analizados:** {project_stats['analyzed_files']}\n")
            f.write(f"- **Documentos encontrados:** {len(analyzed_docs)}\n")
            f.write(f"- **Total de líneas de código:** {project_stats['total_lines']}\n")
            f.write(f"- **Archivos main.go:** {project_stats['main_files']}\n")
            f.write(f"- **Archivos de test:** {project_stats['test_files']}\n")
            f.write(f"- **Handlers identificados:** {project_stats['handler_files']}\n")
            f.write(f"- **Casos de uso identificados:** {project_stats['usecase_files']}\n")
            f.write(f"- **Entidades identificadas:** {project_stats['entity_files']}\n")
            f.write(f"- **Adaptadores identificados:** {project_stats['adapter_files']}\n")
            f.write(f"- **Funciones identificadas:** {project_stats['total_functions']}\n")
            f.write(f"- **Métodos identificados:** {project_stats['total_methods']}\n")
            f.write(f"- **Structs identificados:** {project_stats['total_structs']}\n")
            f.write(f"- **Interfaces identificadas:** {project_stats['total_interfaces']}\n")
            f.write(f"- **Packages:** {', '.join(project_stats['packages'])}\n")
            f.write(f"- **Proyecto con go.mod:** {'Sí' if project_stats['has_go_mod'] else 'No'}\n\n")
            
            if analyzed_docs:
                f.write(f"## Documentos Analizados\n\n")
                for doc in analyzed_docs:
                    f.write(f"- {doc['path']} ({doc['type']})\n")
                f.write("\n")
            
            f.write(f"## Archivos de Código Analizados\n\n")
            for file in analyzed_files:
                f.write(f"- **{file['path']}** (package: {file['package']}, {file['lines']} líneas, {file['functions_count']} funciones, {file['methods_count']} métodos)\n")
            
            f.write(f"\n## Análisis para DEF\n\n")
            f.write(def_analysis)
            
            f.write(f"\n\n---\n\n")
            f.write(f"**Nota:** Este análisis está especializado para proyectos Go. ")
            f.write(f"Se recomienda validar y complementar la información con el equipo de desarrollo y stakeholders del proyecto.\n")
        
        # Formatear respuesta
        return jsonify({
            "user_stories": user_stories,
            "analyzed_files": analyzed_files,
            "directory_tree": directory_tree,
            "project_stats": project_stats,
            "output_file": user_stories_path,
            "def_analysis_file": def_path,
            "documentation_found": len(analyzed_docs) > 0,
            "analyzed_documents": analyzed_docs,
            "code_analysis": {
                "language": "Go",
                "total_functions": project_stats["total_functions"],
                "total_methods": project_stats["total_methods"],
                "total_structs": project_stats["total_structs"],
                "total_interfaces": project_stats["total_interfaces"],
                "packages": project_stats["packages"],
                "has_go_mod": project_stats["has_go_mod"],
                "common_imports": project_stats["common_imports"][:10]
            }
        })
    
    except Exception as e:
        print(f"Error al generar análisis de código Go: {e}")
        return jsonify({
            "error": str(e), 
            "directory_tree": directory_tree,
            "analyzed_files": analyzed_files if 'analyzed_files' in locals() else []
        }), 500