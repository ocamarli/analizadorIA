from flask import Blueprint, request, jsonify
from .dua_base import crear_cadena

adm_bp = Blueprint('adm', __name__)

@adm_bp.route('/codigo/generar-backend', methods=['POST'])
def generar_codigo_backend():
    datos = request.json
    
    cadena = crear_cadena(
        "Eres un desarrollador backend senior. Genera código Python/Flask para:",
        "Funcionalidad: {funcionalidad}\nRequisitos técnicos: {requisitos}"
    )
    
    resultado = cadena.run({
        "funcionalidad": datos.get('funcionalidad', ''),
        "requisitos": datos.get('requisitos', '')
    })
    
    return jsonify({
        "codigo": resultado,
        "lenguaje": "Python",
        "framework": "Flask"
    })

@adm_bp.route('/seguridad/escaneo-vulnerabilidades', methods=['POST'])
def escanear_vulnerabilidades():
    datos = request.json
    
    cadena = crear_cadena(
        "Eres un especialista en seguridad. Analiza código para vulnerabilidades.",
        "Código:\n{codigo}\nTipo: {tipo}"
    )
    
    resultado = cadena.run({
        "codigo": datos.get('codigo', ''),
        "tipo": datos.get('tipo', 'backend')
    })
    
    return jsonify({
        "vulnerabilidades": resultado.split('\n'),
        "nivel_riesgo": "medio"  # Esto podría ser dinámico
    })