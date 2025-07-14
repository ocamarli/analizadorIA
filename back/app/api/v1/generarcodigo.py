# app/__init__.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import JWTManager

from flask_jsonpify import jsonify
from config import config
# Importar tus blueprints

import glob
import os
import requests
import datetime
import tempfile
from openai import AzureOpenAI
from werkzeug.utils import secure_filename
import PyPDF2
import json
import re
from flask import Flask, request, jsonify
jwt = JWTManager()
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
COGNITIVE_SEARCH_ENDPOINT = "https://azuresearhdemobside.search.windows.net"
COGNITIVE_SEARCH_INDEX = "azureblob-index"
COGNITIVE_SEARCH_API_KEY = "YdBHzUf4al4bPNDgDOLLc9XDnPaxucfrBU47RQbXtRAzSeCujuVS"
search_client = SearchClient(COGNITIVE_SEARCH_ENDPOINT, COGNITIVE_SEARCH_INDEX, AzureKeyCredential(COGNITIVE_SEARCH_API_KEY))
# Importa lo que necesites: openai_client, etc.
# O podrías importarlos desde un archivo de configuración/servicios.
AZURE_OPENAI_ENDPOINT = "https://openaidemobside.openai.azure.com"
AZURE_OPENAI_API_KEY = "6076ii7OpLiuTEKYsEVvWyt57RYjzb8d4hDwZRqKuokBi1WTuKz9JQQJ99AJACYeBjFXJ3w3AAABACOGfwuS"
AZURE_OPENAI_DEPLOYMENT = "2024-08-01-preview"  # Nombre del deployment en Azure
openai_client = AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_DEPLOYMENT
)
generarcodigo_bp = Blueprint('generarcodigo', __name__)

@generarcodigo_bp.route('/generate-code', methods=['POST'])
def generate_code():
        data = request.json
        prompt = data.get('prompt')
        
        if not prompt:
            return jsonify({"error": "Debes proporcionar un prompt para generar código"}), 400
        
        print(f"Generando código para: {prompt}")
        
        try:
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
                    top=5
                )
                
                # Procesar los resultados para crear el contexto
                for result in results:
                    context += f"Documento: {result.get('metadata', '')}\nContenido: {result['content']}\n\n"
                    
                print(f"Se encontraron documentos relevantes para el contexto")
                
            except Exception as e:
                print(f"Error al buscar documentos en Azure Search: {e}")
                # Continuar con un contexto vacío si falla la búsqueda
            
            # Crear el mensaje del sistema para el modelo
            system_message = """Eres un asistente especializado en generación de código que sigue estrictamente
            los estándares y mejores prácticas . Tu tarea es generar código de alta calidad basado
            en la solicitud del usuario, asegurándote de que cumpla con los estándares proporcionados en el contexto.
            
            Debes devolver un JSON con la siguiente estructura:
            {
                "explanation": "Explicación detallada del código generado y su funcionamiento",
                "files": [
                    {
                        "name": "nombre_del_archivo.extension",
                        "language": "lenguaje_de_programacion",
                        "content": "contenido_del_archivo"
                    },
                    ...
                ]
            }
            
            Asegúrate de incluir todos los archivos necesarios para que la solución sea funcional."""
            
            user_message = f"""
            Genera código para la siguiente solicitud siguiendo los estándares y mejores prácticas :
            
            {prompt}
            
            CONTEXTO CON ESTÁNDARES D:
            {context}
            
            Asegúrate de que el código sea:
            1. Completo y funcional
            2. Bien documentado
            3. Siguiendo los estándares mostrados en el contexto
            4. Organizado en archivos adecuados
            5. Con manejo de errores apropiado
            
            Devuelve un JSON con una explicación detallada y la lista de archivos.
            """
            
            # Llamada a Azure OpenAI
            response = openai_client.chat.completions.create(
                model="gpt-4o", # Asegúrate de usar el modelo disponible en tu despliegue
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.2,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            # Acceder correctamente a la respuesta
            result_json = response.choices[0].message.content
            token_usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            print(f"Uso de tokens en esta llamada:")
            print(f"  - Tokens del prompt: {token_usage['prompt_tokens']}")
            print(f"  - Tokens de la respuesta: {token_usage['completion_tokens']}")
            print(f"  - Total de tokens: {token_usage['total_tokens']}")
                     
            # Convertir la respuesta JSON en un objeto Python
            import json
            result_data = json.loads(result_json)
            result_data["token_usage"] = token_usage 
            # Guardar los archivos generados localmente (opcional)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join("generated_code", timestamp)
            os.makedirs(output_dir, exist_ok=True)
            
            for file in result_data.get("files", []):
                file_path = os.path.join(output_dir, file["name"])
                
                # Crear directorios intermedios si es necesario
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(file["content"])
                    
            # Devolver la respuesta al frontend
            return jsonify(result_data)
        
        except Exception as e:
            print(f"Error al generar código: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500
        

        """Extrae bloques de código de un texto markdown"""
        pattern = r'```(\w*)\n([\s\S]*?)\n```'
        matches = re.findall(pattern, text)
        
        code_blocks = []
        for language, code in matches:
            code_blocks.append({
                "language": language if language else "plaintext",
                "code": code
            })
        
        return code_blocks