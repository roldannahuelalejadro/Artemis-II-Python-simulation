# main.py
from app import RocketApp

if __name__ == "__main__":
    print("🚀 Iniciando Rocket Trajectory Studio v2")
    print("Controles:")
    print("   SPACE → Iniciar/Pausar simulación")
    print("   N     → Crear nuevo cohete")
    print("   R     → Reset completo")
    print("   WASD  → Mover cámara")
    print("   ESC   → Salir")
    
    app = RocketApp()
    app.run()