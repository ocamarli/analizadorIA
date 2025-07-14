# app/modules/search.py
from flask import Blueprint, request, jsonify
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
# Importar search_client, etc.
# Configuración de Cognitive Search
COGNITIVE_SEARCH_ENDPOINT = "https://azuresearhdemobside.search.windows.net"
COGNITIVE_SEARCH_INDEX = "azureblob-index"
COGNITIVE_SEARCH_API_KEY = "YdBHzUf4al4bPNDgDOLLc9XDnPaxucfrBU47RQbXtRAzSeCujuVS"
search_client = SearchClient(COGNITIVE_SEARCH_ENDPOINT, COGNITIVE_SEARCH_INDEX, AzureKeyCredential(COGNITIVE_SEARCH_API_KEY))
search_bp = Blueprint('search', __name__)

@search_bp.route('/search', methods=['POST'])
def search():
    """
    Realiza una consulta en Azure Cognitive Search y devuelve los resultados.
    """
    user_query = request.json.get("query", "").strip()
    user_query = "curricu"
    if not user_query:
        return jsonify({"error": "La consulta no puede estar vacía"}), 400

    print("\n🔹 [LOG] Enviando consulta a Azure Search...")
    print(f"🔹 Endpoint: {COGNITIVE_SEARCH_ENDPOINT}")
    print(f"🔹 Query: {user_query}")

    try:
        # No usar "metadata_storage_name" ni "metadata_storage_path" si no están disponibles
        results = search_client.search(search_text=user_query, select=["content"], top=5)
        results = search_client.search(
            search_text=f"{user_query}*",
            search_mode="all",  # Busca en todos los documentos
            select=["content"],
            top=5
        )
        simplified_results = [
            {
                "score": result.get("@search.score", 0),
                "content": result.get("content", "No hay contenido disponible.")
            }
            for result in results
        ]
        
        print("🔹 [LOG] Resultados simplificados:", simplified_results)
        return jsonify(simplified_results)
    
    except Exception as e:
        print("[ERROR] Error en la solicitud a Azure Search:", str(e))
        return jsonify({"error": str(e)}), 500