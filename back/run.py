# run.py
import os
from app import create_app

#if __name__ == '__main__':
#    port = int(os.getenv('RUN_PORT', 5000))
#    app = create_app(env_name='docker')
#    app.run(host='0.0.0.0', port=port)


if __name__ == '__main__':
    port = int(os.getenv('RUN_PORT', 5000))
    app, socketio = create_app(env_name='docker')
    
    # Usar socketio.run() en lugar de app.run() para habilitar WebSockets
    socketio.run(
        app, 
        debug=True, 
        host='0.0.0.0', 
        port=port,
        allow_unsafe_werkzeug=True
    )