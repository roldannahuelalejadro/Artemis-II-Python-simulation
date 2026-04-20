# Rocket Sim v3

Simulador 2D de misiones orbitales con un solo cohete, fases modulares de empuje y una interfaz simple en Tkinter. El objetivo del proyecto no es reproducir una mision real con alta fidelidad, sino tener un laboratorio visual para probar transferencias, orbitas, guiado relativo a la Luna y perfiles de empuje por fases.

## Estado Actual

El simulador trabaja con:

- Un unico cohete.
- Tierra y Luna en 2D.
- Gravedad combinada Tierra-Luna.
- Luna en orbita circular uniforme.
- Fases secuenciales de mision.
- Empuje configurable por expresiones matematicas.
- Frames de empuje `xy`, `polar`, `prograde` y `none`.
- Trail de trayectoria largo.
- Zoom, paneo y seguimiento de camara.
- Colisiones con Tierra y Luna.
- Registro de delta-v y energia de impulso.
- Metricas lunares para free-return de juguete.

## Como Ejecutar

Desde la carpeta `rocket-sim-v3`:

```powershell
py main.py
```

Tambien se puede abrir el proyecto en VS Code y ejecutar `main.py`.

## Dependencias

No hay dependencias externas de `pip`.

El proyecto usa solamente librerias estandar de Python:

- `tkinter`
- `math`
- `dataclasses`
- `enum`
- `typing`
- `pathlib`
- `sys`

Un `requirements.txt` puede quedar asi:

```txt
# No external dependencies.
# Uses only Python standard library modules.
```

Nota: en Windows, `tkinter` normalmente viene incluido con Python. En Linux puede requerir instalacion del paquete del sistema, por ejemplo `python3-tk`.

## Estructura Del Proyecto

```text
rocket-sim-v3/
├── main.py
├── app.py
├── README.md
├── imgui.ini
│
├── camera/
│   └── camera.py
│
├── config/
│   ├── colors.py
│   ├── constants.py
│   └── defaults.py
│
├── coordinates/
│   └── frame.py
│
├── core/
│   ├── phase.py
│   ├── phase_manager.py
│   ├── rocket.py
│   ├── simulation.py
│   │
│   ├── entities/
│   │   └── celestial.py
│   │
│   ├── physics/
│   │   ├── gravity.py
│   │   ├── integrator.py
│   │   └── kepler.py
│   │
│   └── thrust/
│       ├── controller.py
│       ├── frame_converter.py
│       └── profile.py
│
├── input/
│   └── handler.py
│
├── rendering/
│   ├── renderer.py
│   └── thrust_visual.py
│
├── tests/
│   ├── heo_24h_checkout_test.py
│   ├── launch_to_200km_test.py
│   ├── orbit_stability_test.py
│   └── toy_free_return_sweep.py
│
├── trajectory/
│   ├── energy_logger.py
│   └── predictor.py
│
├── ui/
│   └── mission_panel.py
│
└── utils/
    ├── formatting.py
    └── safe_eval.py
```

## Modulos Principales

### `main.py`

Punto de entrada. Crea y ejecuta la aplicacion.

### `app.py`

Inicializa la ventana Tkinter y conecta la UI con `SimulationState`.

### `core/simulation.py`

Contiene el estado global de la simulacion:

- Tiempo de mision.
- Tierra.
- Luna.
- Cohete.
- Fases activas y pendientes.
- Integracion fisica.
- Colisiones.
- Metricas orbitales.
- Metricas lunares.
- Acciones especiales, como el pegado a HEO conocida.

### `core/rocket.py`

Representa el cohete unico:

- Posicion.
- Velocidad.
- Masa.
- Trail.
- Empuje activo.
- Velocidad maxima registrada.

### `core/phase.py`

Define una fase de mision:

```python
MissionPhase(
    label="Nombre",
    duration_s=100.0,
    frame=FrameType.PROGRADE,
    primary_expr="...",
    secondary_expr="...",
)
```

### `core/phase_manager.py`

Administra la cola de fases:

- Fase activa.
- Fases pendientes.
- Fases completadas.
- Pausa automatica al terminar cada fase.

### `core/thrust/profile.py`

Evalua las expresiones matematicas de empuje.

Expone variables como:

- `t`
- `mission_t`
- `x`, `y`
- `vx`, `vy`
- `r`, `theta`
- `speed`
- `vr`, `vtheta`
- `mu_earth`
- `moon_dist`
- `moon_vrel_r`
- `moon_vrel_t`
- `behind_score`
- `hz_earth`
- `earth_dist`
- `earth_vr`
- `earth_vtheta`

### `core/thrust/frame_converter.py`

Convierte los componentes de empuje desde el frame elegido hacia coordenadas globales `xy`.

Frames soportados:

- `none`
- `xy`
- `polar`
- `prograde`

### `coordinates/frame.py`

Define operaciones vectoriales y transformaciones:

- Magnitud.
- Normalizacion.
- Producto escalar.
- Base radial/tangencial.
- Base prograde/normal.
- Estado polar.

### `core/physics/gravity.py`

Calcula la aceleracion gravitatoria combinada de Tierra y Luna.

### `core/physics/integrator.py`

Integra la dinamica con Euler simplectico.

### `core/physics/kepler.py`

Funciones auxiliares para orbitas:

- Velocidad circular.
- Periodo orbital.
- Clasificacion orbital.
- Calidad de orbita.

### `ui/mission_panel.py`

Contiene la interfaz completa:

- Condiciones iniciales.
- Editor de fases.
- Presets.
- Controles de camara.
- Canvas de simulacion.
- Bitacora.
- Estado numerico.

Tambien contiene los presets principales.

## Presets Disponibles

### `orbita 200 km`

Lanza desde superficie y busca una orbita baja cercana a 200 km.

Fases:

```text
Ascenso inicial
Giro gravitacional
Construccion orbital
Circularizacion
Afinado orbital
Costa de chequeo
```

### `HEO 24h checkout`

Arranca directamente en una orbita eliptica alta tipo HEO de 24 h.

Parametros iniciales:

```text
altitud = 185000 m
velocidad tangencial = 10590.67 m/s
velocidad radial = 0 m/s
```

### `HEO 24h NASA geometry`

Variante de HEO con parametros cercanos a una geometria publica tipo NASA.

### `transferencia translunar`

Preset simple:

```text
HEO 24h checkout
TLI desde HEO
Costa translunar
```

### `toy free return`

Preset de free-return de juguete.

Fases:

```text
HEO 24h checkout
TLI desde HEO
Guiado translunar lejano
Sesgo detras de la Luna
Salida post-flyby
Costa de retorno
```

Este preset usa variables relativas a la Luna:

- `moon_dist`
- `moon_vrel_r`
- `moon_vrel_t`
- `behind_score`
- `moon_radial_x`, `moon_radial_y`
- `moon_tangent_x`, `moon_tangent_y`
- `moon_orbit_tangent_x`, `moon_orbit_tangent_y`

### `simulacion Artemis`

Preset compuesto de juguete.

La idea es:

```text
1. Lanzar desde superficie.
2. Construir una LEO de aproximadamente 200 km.
3. Completar una fase de chequeo en LEO.
4. Pegar la nave a la HEO 24h conocida.
5. Ejecutar el toy free return original.
```

Fases:

```text
Ascenso inicial
Giro gravitacional
Construccion orbital
Circularizacion
Afinado orbital
Costa de chequeo
Pegado a HEO 24h conocida
HEO 24h checkout
TLI desde HEO
Guiado translunar lejano
Sesgo detras de la Luna
Salida post-flyby
Costa de retorno
```

## Pegado A HEO Conocida

La fase especial:

```text
Pegado a HEO 24h conocida
```

existe para unir visualmente el lanzamiento a LEO con el preset translunar que ya estaba calibrado.

No intenta construir dinamicamente la HEO. En cambio:

- Lee el angulo geocentrico actual de la nave al final de LEO.
- Coloca la nave en la HEO conocida usando ese mismo angulo.
- Usa altitud `185000 m`.
- Usa velocidad tangencial `10590.67 m/s`.
- Usa velocidad radial `0 m/s`.
- Re-fasea la Luna para conservar la geometria relativa del preset `toy free return`.

Esto evita un salto angular visible alrededor de la Tierra, aunque sigue siendo un pegado artificial de energia y radio.

## Variables De Expresion

Las expresiones de empuje pueden usar variables como:

```text
t
mission_t
x, y
vx, vy
r
theta
speed
vr
vtheta
mu_earth
r_moon_mean
```

Variables lunares:

```text
moon_x, moon_y
moon_vx, moon_vy
moon_dx, moon_dy
moon_dist
moon_theta
moon_radial_x, moon_radial_y
moon_tangent_x, moon_tangent_y
moon_vrel_x, moon_vrel_y
moon_vrel_r, moon_vrel_t
moon_orbit_tangent_x, moon_orbit_tangent_y
moon_hz
behind_score
```

Variables geocentricas:

```text
hz_earth
earth_dist
earth_vr
earth_vtheta
```

Convenciones:

```text
behind_score < 0  => paso por detras de la Luna
behind_score > 0  => paso por delante de la Luna

hz_earth > 0      => giro geocentrico antihorario
hz_earth < 0      => giro geocentrico horario
```

## Tests Y Barridos

Los tests son scripts ejecutables directamente.

### Orbita estable

```powershell
py tests\orbit_stability_test.py
```

### Lanzamiento a 200 km

```powershell
py tests\launch_to_200km_test.py
```

### HEO 24h

```powershell
py tests\heo_24h_checkout_test.py
```

### Barrido toy free return

```powershell
py tests\toy_free_return_sweep.py
```

Este barrido explora parametros del free-return de juguete y reporta combinaciones candidatas.

## Notas De Modelo

Este simulador es deliberadamente simplificado:

- Es 2D.
- La Luna tiene orbita circular uniforme.
- No hay atmosfera.
- No hay masa variable.
- No hay consumo real de combustible.
- El empuje se modela como aceleracion directa.
- No se busca fidelidad real de Artemis II.

El objetivo principal es poder experimentar con geometria orbital, fases de mision y control por expresiones.

## Consejos De Uso

- Para probar fases largas, usar velocidad temporal alta, por ejemplo `x100` o `x500`.
- Para analizar encuentros lunares, activar seguimiento del cohete y ajustar zoom.
- Para depurar retornos, mirar:
  - `Min distancia Luna`
  - `Behind score en peri-lunio`
  - `hz_earth`
  - `sentido geocentrico`
  - `Evento terminal`
- Si una trayectoria falla por geometria lunar, el primer parametro a modificar suele ser `moon_angle_deg`.

## Estado Recomendado Para Continuar

El preset `toy free return` original es la base estable para seguir ajustando retornos lunares.

El preset `simulacion Artemis` debe entenderse como una demostracion visual compuesta:

```text
LEO real del simulador + pegado artificial a HEO conocida + toy free return calibrado
```

El siguiente paso natural seria reemplazar el pegado artificial por una construccion dinamica real de la HEO de 24 h desde LEO.
