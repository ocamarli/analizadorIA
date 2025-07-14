# app/modules/chat.py
from flask import Blueprint, request, jsonify
from openai import AzureOpenAI

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
chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat', methods=['POST'])
def chat_with_azure_openai():
    """
    Endpoint que se conecta a Azure OpenAI y devuelve una respuesta generada.
    """
    data = request.json
    user_input = data.get("input", "").strip()

    if not user_input:
        return jsonify({"error": "El campo 'input' no puede estar vacío"}), 400

    print("\n🔹 [LOG] Enviando solicitud a Azure OpenAI...")
    print(f"🔹 Input del usuario: {user_input}")

    try:
        # Llamar a Azure OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # Nombre del deployment en Azure
            messages=[{"role": "system", "content": "Eres un asistente de IA."},
                      {"role": "user", "content": user_input}],
            temperature=0.7,
           
        )

        # Extraer la respuesta generada
        generated_response = response.choices[0].message.content.strip()

        print(f"🔹 [LOG] Respuesta de OpenAI: {generated_response}")

        return jsonify({"response": generated_response})

    except Exception as e:
        print(" [ERROR] Error en la solicitud a OpenAI:", str(e))
        return jsonify({"error": str(e)}), 500
    