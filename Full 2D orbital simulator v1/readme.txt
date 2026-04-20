# Rocket Trajectory Studio v2

Simulador 2D de trayectorias de cohetes con control total mediante funciones matemáticas (estilo Desmos).

**Características principales:**
- Tierra y Luna quietas al inicio.
- Configuración libre de posición inicial de la Luna (ángulo).
- Cohetes definidos 100% matemáticamente (posición, velocidad y thrust como función de `t`).
- Sin interacción directa del mouse con la simulación (solo UI).
- Simulación solo comienza al pulsar **START SIMULATION**.
- Múltiples cohetes simultáneos.
- Editor de thrust tipo Desmos con previsualización.
- Trayectorias predictivas (fantasma) en tiempo real.
- Guardado/carga de escenarios.

---

## Estructura del Proyecto

rocket-sim-v2/
├── main.py                          # Punto de entrada mínimo
├── app.py                           # Orquestador principal de la aplicación
│
├── config/
│   ├── constants.py                 # Constantes físicas y de simulación
│   ├── defaults.py                  # Valores por defecto (spawn, ángulo luna, etc.)
│   └── colors.py                    # Paleta de colores
│
├── core/
│   ├── simulation.py                # Motor de simulación (tiempo, estado running/paused)
│   ├── physics/
│   │   ├── gravity.py               # Cálculo de aceleración gravitatoria (Tierra + Luna)
│   │   ├── kepler.py                # Solución de Kepler con ángulo inicial para la Luna
│   │   ├── integrators.py           # Métodos de integración (Symplectic Euler, RK4)
│   │   └── thrust.py                # Gestión de perfiles de thrust (funciones del usuario)
│   │
│   └── entities/
│       ├── celestial.py             # Earth y Moon (con soporte para estado congelado)
│       └── rocket.py                # Clase Rocket (posición, velocidad, thrust, trail)
│
├── thrust_editor/
│   ├── editor.py                    # Panel completo de edición tipo Desmos
│   ├── parser.py                    # SafeEval seguro para expresiones matemáticas
│   ├── presets.py                   # Presets útiles de thrust
│   └── preview.py                   # Gráfico pequeño de thrust vs tiempo
│
├── trajectory/
│   ├── manager.py                   # Gestión de lista de cohetes (agregar, eliminar, seleccionar)
│   ├── predictor.py                 # Integración predictiva para órbitas fantasma
│   └── serializer.py                # Guardado y carga en JSON (incluye expresiones)
│
├── rendering/
│   ├── renderer.py                  # Motor de renderizado con ModernGL
│   ├── labels.py                    # Etiquetas dinámicas (velocidad, thrust, nombre)
│   ├── predictive.py                # Renderizado de trayectorias predictivas
│   └── effects.py                   # Efectos visuales (glow, trails optimizados)
│
├── ui/
│   ├── hud.py                       # Información en pantalla (tiempo, estado, etc.)
│   ├── panel_rockets.py             # Lista de cohetes (nombre, color, visibilidad, botón Edit)
│   ├── panel_spawn.py               # Panel "Nuevo Cohete" + configuración inicial Luna + botón START
│   ├── thrust_editor_panel.py       # Integración del editor de thrust
│   └── widgets/                     # Componentes reutilizables (inputs numéricos, sliders)
│
├── camera/
│   └── camera.py                    # Cámara (WASD + zoom) - solo movimiento
│
├── input/
│   └── handler.py                   # Manejo de inputs (solo UI y shortcuts globales)
│
├── utils/
│   ├── safe_eval.py                 # Evaluador seguro de expresiones
│   ├── formatting.py                # Formateo de vectores, tiempo, etc.
│   └── io.py                        # Utilidades de lectura/escritura
│
├── assets/                          # Texturas, fuentes
└── scenarios/                       # Archivos .json guardados

---

### Descripción Detallada de Módulos y Funciones Principales

#### `core/simulation.py`
- `SimulationState`: Clase central que controla el estado global.
  - `is_running: bool`
  - `sim_time: float`
  - `start()` → Inicia Luna + todos los cohetes
  - `pause()` / `reset()`

#### `core/physics/kepler.py`
- `get_moon_pos(t: float, n: float, initial_angle: float = 0.0) → np.ndarray`
  - Calcula posición de la Luna usando ecuación de Kepler con ángulo inicial configurable.

#### `core/physics/thrust.py`
- `ThrustProfile`
  - `thrust_x_expr: str`
  - `thrust_y_expr: str`
  - `evaluate(t, pos, vel) → np.ndarray` → Devuelve aceleración en m/s²

#### `core/entities/rocket.py`
- `class Rocket`
  - `pos`, `vel`, `trail`
  - `thrust_profile: ThrustProfile`
  - `update(dt, moon_pos)` → integra física
  - `is_colliding_earth()` → con margen para permitir despegue desde superficie

#### `core/entities/celestial.py`
- `class Earth` y `class Moon`
  - `Moon` soporta `initial_angle`
  - `frozen: bool` (no se mueve hasta START)

#### `thrust_editor/editor.py`
- `ThrustEditorPanel`
  - Interfaz estilo Desmos con dos campos (thrust_x y thrust_y)
  - Actualización en tiempo real de la trayectoria predictiva

#### `trajectory/predictor.py`
- `TrajectoryPredictor`
  - `compute_ghost_trajectory(rocket, duration)` → calcula trayectoria futura sin afectar la simulación real

#### `ui/panel_spawn.py`
- Contiene:
  - Campos para x₀, y₀, vx₀, vy₀
  - Control de ángulo inicial de la Luna
  - Botón grande **START SIMULATION**

#### `rendering/renderer.py`
- Maneja todo el dibujo con ModernGL (Tierra, Luna, cohetes, trails, predictivos)

---

### Flujo de Uso

1. Se abre el simulador → Tierra y Luna **quietas**.
2. Configura posición inicial de la Luna (opcional).
3. Crea uno o más cohetes definiendo posición, velocidad y funciones de thrust.
4. Pulsa **START SIMULATION**.
5. Todo evoluciona: Luna orbita + cohetes siguen sus funciones de thrust.
6. Puedes pausar, editar thrust en cualquier momento y ver predicciones.

---