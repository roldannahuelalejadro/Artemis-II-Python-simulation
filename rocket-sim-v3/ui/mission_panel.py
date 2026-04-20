"""Single mission control panel for phase inputs and launch configuration."""

from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk
from tkinter import messagebox, ttk

from camera.camera import Camera
from config.defaults import DEFAULTS
from coordinates.frame import FrameType, magnitude
from core.phase import MissionPhase
from core.simulation import SimulationState
from rendering.thrust_visual import thrust_indicator_text
from utils.formatting import format_energy, format_seconds


ORBIT_200KM_PRESET = [
    {
        "label": "Ascenso inicial",
        "duration_s": 100.0,
        "frame": FrameType.POLAR,
        "primary_expr": "18.0",
        "secondary_expr": "4.0 + 0.06*t",
    },
    {
        "label": "Giro gravitacional",
        "duration_s": 220.0,
        "frame": FrameType.POLAR,
        "primary_expr": "max(4.0, 14.0 - 0.045*t)",
        "secondary_expr": "18.0 + 0.025*t",
    },
    {
        "label": "Construccion orbital",
        "duration_s": 220.0,
        "frame": FrameType.POLAR,
        "primary_expr": "-6.0 - 0.02*t",
        "secondary_expr": "14.0 - 0.015*t",
    },
    {
        "label": "Circularizacion",
        "duration_s": 520.0,
        "frame": FrameType.POLAR,
        "primary_expr": "max(-10,min(10,-0.06*vr - 0.00004*(r-6680000.0)))",
        "secondary_expr": "max(-8,min(8,0.06*(sqrt(3.986004418e14/r)-speed)))",
    },
    {
        "label": "Afinado orbital",
        "duration_s": 180.0,
        "frame": FrameType.POLAR,
        "primary_expr": "max(-4,min(4,-0.04*vr - 0.00002*(r-6571000.0)))",
        "secondary_expr": "max(-3,min(3,0.04*(sqrt(3.986004418e14/r)-speed)))",
    },
    {
        "label": "Costa de chequeo",
        "duration_s": 5300.0,
        "frame": FrameType.NONE,
        "primary_expr": "0.0",
        "secondary_expr": "0.0",
    },
]

TRANSLUNAR_TRANSFER_PRESET = [
    {
        "label": "HEO 24h checkout",
        "duration_s": 86_400.0,
        "frame": FrameType.NONE,
        "primary_expr": "0.0",
        "secondary_expr": "0.0",
    },
    {
        "label": "TLI desde HEO",
        "duration_s": 700.0,
        "frame": FrameType.PROGRADE,
        "primary_expr": "max(0,min(8,0.025*(sqrt(3.986004418e14*(2/r - 1/233285500.0))-speed)))",
        "secondary_expr": "0.0",
    },
    {
        "label": "Costa translunar",
        "duration_s": 430000.0,
        "frame": FrameType.NONE,
        "primary_expr": "0.0",
        "secondary_expr": "0.0",
    },
]

HEO_24H_CHECKOUT = {
    "launch_altitude_m": 185_000.0,
    "launch_tangential_speed_m_s": 10_590.67,
    "launch_radial_speed_m_s": 0.0,
    "phase": {
        "label": "HEO 24h checkout",
        "duration_s": 86_400.0,
        "frame": FrameType.NONE,
        "primary_expr": "0.0",
        "secondary_expr": "0.0",
    },
}

HEO_24H_NASA_GEOMETRY = {
    "launch_altitude_m": 185_000.0,
    "launch_tangential_speed_m_s": 10_591.20,
    "launch_radial_speed_m_s": 0.0,
    "phase": {
        "label": "HEO 24h NASA geometry",
        "duration_s": 86_554.69,
        "frame": FrameType.NONE,
        "primary_expr": "0.0",
        "secondary_expr": "0.0",
    },
}

TOY_FREE_RETURN_PRESET = [
    {
        "label": "HEO 24h checkout",
        "duration_s": 86_400.0,
        "frame": FrameType.NONE,
        "primary_expr": "0.0",
        "secondary_expr": "0.0",
    },
    {
        "label": "TLI desde HEO",
        "duration_s": 700.0,
        "frame": FrameType.PROGRADE,
        "primary_expr": "max(0,min(8,0.025*(sqrt(mu_earth*(2/r - 1/233285500.0))-speed)))",
        "secondary_expr": "0.0",
    },
    {
        "label": "Guiado translunar lejano",
        "duration_s": 210_000.0,
        "frame": FrameType.XY,
        # Pull gently toward the Moon and damp transverse lunar-relative velocity.
        "primary_expr": "(0.00055*moon_radial_x - 0.00000035*moon_vrel_t*moon_tangent_x) if moon_dist > 8e7 else 0.0",
        "secondary_expr": "(0.00055*moon_radial_y - 0.00000035*moon_vrel_t*moon_tangent_y) if moon_dist > 8e7 else 0.0",
    },
    {
        "label": "Sesgo detras de la Luna",
        "duration_s": 120_000.0,
        "frame": FrameType.XY,
        # Near the encounter, push opposite the Moon orbital tangent if the
        # spacecraft is not yet behind the Moon. Add radial repulsion under
        # 9e6 m to avoid lunar impact.
        "primary_expr": "((-0.0014*moon_orbit_tangent_x if behind_score > -0.25 else 0.0) + (0.0025*(-moon_radial_x) if moon_dist < 9e6 else 0.0)) if moon_dist < 1.2e8 else 0.0",
        "secondary_expr": "((-0.0014*moon_orbit_tangent_y if behind_score > -0.25 else 0.0) + (0.0025*(-moon_radial_y) if moon_dist < 9e6 else 0.0)) if moon_dist < 1.2e8 else 0.0",
    },
    {
        "label": "Salida post-flyby",
        "duration_s": 430_000.0,
        "frame": FrameType.XY,
        # After the flyby, bias the spacecraft back toward Earth and damp
        # excess outward radial velocity so the coast bends back inward.
        "primary_expr": "(-0.006*x/r - 0.00000045*vr*x/r) if (moon_dist < 2.4e8 or r > 1.5e8) else 0.0",
        "secondary_expr": "(-0.006*y/r - 0.00000045*vr*y/r) if (moon_dist < 2.4e8 or r > 1.5e8) else 0.0",
    },
    {
        "label": "Costa de retorno",
        "duration_s": 180_000.0,
        "frame": FrameType.NONE,
        "primary_expr": "0.0",
        "secondary_expr": "0.0",
    },
]


@dataclass(slots=True)
class MissionPanelState:
    launch_theta_deg: float = DEFAULTS["launch_theta_deg"]
    launch_altitude_m: float = DEFAULTS["launch_altitude_m"]
    launch_tangential_speed_m_s: float = DEFAULTS["launch_tangential_speed_m_s"]
    launch_radial_speed_m_s: float = DEFAULTS["launch_radial_speed_m_s"]
    moon_angle_deg: float = DEFAULTS["moon_angle_deg"]
    phase_duration_s: float = DEFAULTS["phase_duration_s"]
    phase_frame: str = DEFAULTS["phase_frame"]
    primary_expr: str = DEFAULTS["phase_fx"]
    secondary_expr: str = DEFAULTS["phase_fy"]
    phase_label: str = DEFAULTS["phase_label"]

    def build_phase(self) -> MissionPhase:
        return MissionPhase(
            label=self.phase_label,
            duration_s=self.phase_duration_s,
            frame=FrameType(self.phase_frame),
            primary_expr=self.primary_expr,
            secondary_expr=self.secondary_expr,
        )


class MissionControlPanel(ttk.Frame):
    def __init__(self, master: tk.Misc, simulation: SimulationState):
        super().__init__(master, padding=12)
        self.master = master
        self.simulation = simulation
        self.camera = Camera()
        self.state = MissionPanelState()
        self.refresh_ms = DEFAULTS["ui_refresh_ms"]
        self.steps_per_frame = DEFAULTS["steps_per_frame"]
        self.time_speed_options = DEFAULTS["time_speed_options"]
        self._scheduled_tick: str | None = None
        self._drag_last_xy: tuple[int, int] | None = None
        self._last_logged_termination: str | None = None
        self._tick_counter = 0
        self._render_every_ticks = 1
        self.max_trail_draw_points = 1200
        self._steps_remaining_this_frame = 0
        self._max_steps_per_ui_pulse = 25

        self._build_style()
        self._build_variables()
        self._build_layout()
        self.pack(fill="both", expand=True)

        self.apply_launch_config(log_message=False)
        self.camera.follow(self.simulation.rocket.position_xy)
        self.refresh_status()
        self.log("UI v3 lista. Configura una fase y presiona 'Agregar fase'.")

    def _build_style(self) -> None:
        style = ttk.Style(self.master)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        self.master.configure(bg="#0b1020")
        style.configure("Root.TFrame", background="#0b1020")
        style.configure("Card.TLabelframe", background="#111831", foreground="#f1f5f9")
        style.configure("Card.TLabelframe.Label", background="#111831", foreground="#f8fafc")
        style.configure("Body.TLabel", background="#111831", foreground="#dbe7ff")
        style.configure("Headline.TLabel", background="#0b1020", foreground="#f8fafc", font=("Segoe UI", 18, "bold"))
        style.configure("Hint.TLabel", background="#0b1020", foreground="#93a4c3")
        style.configure("Action.TButton", font=("Segoe UI", 10, "bold"))
        style.configure("TFrame", background="#0b1020")

    def _build_variables(self) -> None:
        self.launch_theta_var = tk.StringVar(value=str(self.state.launch_theta_deg))
        self.launch_altitude_var = tk.StringVar(value=str(self.state.launch_altitude_m))
        self.launch_tangential_var = tk.StringVar(value=str(self.state.launch_tangential_speed_m_s))
        self.launch_radial_var = tk.StringVar(value=str(self.state.launch_radial_speed_m_s))
        self.moon_angle_var = tk.StringVar(value=str(self.state.moon_angle_deg))
        self.phase_label_var = tk.StringVar(value=self.state.phase_label)
        self.phase_duration_var = tk.StringVar(value=str(self.state.phase_duration_s))
        self.phase_frame_var = tk.StringVar(value=self.state.phase_frame)
        self.primary_expr_var = tk.StringVar(value=self.state.primary_expr)
        self.secondary_expr_var = tk.StringVar(value=self.state.secondary_expr)
        self.status_var = tk.StringVar(value="Esperando configuracion.")
        self.phase_hint_var = tk.StringVar(value="Componentes: f_prograde(t), f_normal(t)")
        self.zoom_var = tk.StringVar(value="Zoom 1.00x")
        self.follow_var = tk.BooleanVar(value=True)
        self.show_trail_var = tk.BooleanVar(value=True)
        self.time_speed_var = tk.StringVar(value=f"x{self.steps_per_frame}")
        self.preset_var = tk.StringVar(value="manual")

    def _build_layout(self) -> None:
        self.configure(style="Root.TFrame")
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, style="Root.TFrame")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        ttk.Label(header, text="Rocket Sim v3 | Panel unico de mision", style="Headline.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Un solo cohete, fases modulares, coordenadas XY/prograde/polar, zoom y seguimiento.",
            style="Hint.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        left_container = ttk.Frame(self, style="Root.TFrame")
        left_container.grid(row=1, column=0, sticky="nsw")
        left_container.rowconfigure(0, weight=1)
        left_container.columnconfigure(0, weight=1)

        left_canvas = tk.Canvas(left_container, bg="#0b1020", highlightthickness=0, width=355)
        left_canvas.grid(row=0, column=0, sticky="nsw")
        left_scroll = ttk.Scrollbar(left_container, orient="vertical", command=left_canvas.yview)
        left_scroll.grid(row=0, column=1, sticky="ns")
        left_canvas.configure(yscrollcommand=left_scroll.set)

        left = ttk.Frame(left_canvas, style="Root.TFrame")
        left_window = left_canvas.create_window((0, 0), window=left, anchor="nw")

        def _sync_left_scroll(_event=None) -> None:
            left_canvas.configure(scrollregion=left_canvas.bbox("all"))

        def _resize_left_window(event) -> None:
            left_canvas.itemconfigure(left_window, width=event.width)

        left.bind("<Configure>", _sync_left_scroll)
        left_canvas.bind("<Configure>", _resize_left_window)

        def _on_left_mousewheel(event) -> None:
            if hasattr(event, "delta") and event.delta:
                left_canvas.yview_scroll(int(-event.delta / 120), "units")
            else:
                num = getattr(event, "num", 0)
                direction = -1 if num == 4 else 1
                left_canvas.yview_scroll(direction, "units")

        left_canvas.bind("<MouseWheel>", _on_left_mousewheel)
        left_canvas.bind("<Button-4>", _on_left_mousewheel)
        left_canvas.bind("<Button-5>", _on_left_mousewheel)
        left.bind("<MouseWheel>", _on_left_mousewheel)
        left.bind("<Button-4>", _on_left_mousewheel)
        left.bind("<Button-5>", _on_left_mousewheel)

        right = ttk.Frame(self, style="Root.TFrame")
        right.grid(row=1, column=1, sticky="nsew", padx=(12, 0))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        launch_card = ttk.LabelFrame(left, text="Condiciones iniciales", style="Card.TLabelframe", padding=10)
        launch_card.pack(fill="x", pady=(0, 10))
        self._add_labeled_entry(launch_card, "Theta terrestre (deg)", self.launch_theta_var, 0)
        self._add_labeled_entry(launch_card, "Altitud (m)", self.launch_altitude_var, 1)
        self._add_labeled_entry(launch_card, "Vel tangencial (m/s)", self.launch_tangential_var, 2)
        self._add_labeled_entry(launch_card, "Vel radial (m/s)", self.launch_radial_var, 3)
        self._add_labeled_entry(launch_card, "Angulo inicial Luna (deg)", self.moon_angle_var, 4)
        ttk.Button(launch_card, text="Aplicar configuracion inicial", style="Action.TButton", command=self.apply_launch_config).grid(
            row=5, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )

        phase_card = ttk.LabelFrame(left, text="Editor de fase", style="Card.TLabelframe", padding=10)
        phase_card.pack(fill="x")
        self._add_labeled_entry(phase_card, "Nombre de fase", self.phase_label_var, 0)
        self._add_labeled_entry(phase_card, "Duracion total (s)", self.phase_duration_var, 1)

        ttk.Label(phase_card, text="Frame de thrust", style="Body.TLabel").grid(row=2, column=0, sticky="w", pady=(6, 0))
        frame_combo = ttk.Combobox(
            phase_card,
            textvariable=self.phase_frame_var,
            state="readonly",
            values=[frame.value for frame in FrameType],
        )
        frame_combo.grid(row=2, column=1, sticky="ew", pady=(6, 0))
        frame_combo.bind("<<ComboboxSelected>>", lambda _event: self._sync_phase_hints())

        self.primary_label = ttk.Label(phase_card, text="Componente primaria", style="Body.TLabel")
        self.primary_label.grid(row=3, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(phase_card, textvariable=self.primary_expr_var).grid(row=3, column=1, sticky="ew", pady=(6, 0))

        self.secondary_label = ttk.Label(phase_card, text="Componente secundaria", style="Body.TLabel")
        self.secondary_label.grid(row=4, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(phase_card, textvariable=self.secondary_expr_var).grid(row=4, column=1, sticky="ew", pady=(6, 0))

        ttk.Label(phase_card, textvariable=self.phase_hint_var, style="Hint.TLabel", wraplength=300, justify="left").grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(8, 8)
        )

        phase_buttons = ttk.Frame(phase_card, style="Root.TFrame")
        phase_buttons.grid(row=6, column=0, columnspan=2, sticky="ew")
        phase_buttons.columnconfigure((0, 1), weight=1)
        ttk.Button(phase_buttons, text="Agregar fase", style="Action.TButton", command=self.add_phase).grid(
            row=0, column=0, sticky="ew", padx=(0, 4)
        )
        ttk.Button(phase_buttons, text="Agregar costa", command=self.add_coast_phase).grid(
            row=0, column=1, sticky="ew", padx=(4, 0)
        )

        mission_buttons = ttk.Frame(left, style="Root.TFrame")
        mission_buttons.pack(fill="x", pady=(10, 0))
        mission_buttons.columnconfigure((0, 1), weight=1)
        ttk.Button(mission_buttons, text="Ejecutar siguiente fase", style="Action.TButton", command=self.run_next_phase).grid(
            row=0, column=0, sticky="ew", padx=(0, 4)
        )
        ttk.Button(mission_buttons, text="Pausar", command=self.pause_simulation).grid(
            row=0, column=1, sticky="ew", padx=(4, 0)
        )
        ttk.Button(mission_buttons, text="Reset total", command=self.reset_mission).grid(
            row=1, column=0, sticky="ew", padx=(0, 4), pady=(8, 0)
        )
        ttk.Button(mission_buttons, text="Limpiar fases", command=self.clear_phases).grid(
            row=1, column=1, sticky="ew", padx=(4, 0), pady=(8, 0)
        )

        preset_card = ttk.LabelFrame(left, text="Presets y tiempo", style="Card.TLabelframe", padding=10)
        preset_card.pack(fill="x", pady=(10, 0))
        ttk.Label(preset_card, text="Preset de mision", style="Body.TLabel").grid(row=0, column=0, sticky="w")
        preset_combo = ttk.Combobox(
            preset_card,
            textvariable=self.preset_var,
            state="readonly",
            values=[
                "manual",
                "orbita 200 km",
                "HEO 24h checkout",
                "HEO 24h NASA geometry",
                "transferencia translunar",
                "toy free return",
            ],
        )
        preset_combo.grid(row=0, column=1, sticky="ew")
        ttk.Button(preset_card, text="Cargar preset", command=self.load_selected_preset).grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )
        ttk.Label(preset_card, text="Velocidad temporal", style="Body.TLabel").grid(row=2, column=0, sticky="w", pady=(10, 0))
        time_combo = ttk.Combobox(
            preset_card,
            textvariable=self.time_speed_var,
            state="readonly",
            values=[f"x{value}" for value in self.time_speed_options],
        )
        time_combo.grid(row=2, column=1, sticky="ew", pady=(10, 0))
        time_combo.bind("<<ComboboxSelected>>", lambda _event: self._apply_time_speed())
        ttk.Label(
            preset_card,
            text="Aumenta cuantas iteraciones fisicas se dibujan por frame de pantalla.",
            style="Hint.TLabel",
            wraplength=300,
            justify="left",
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))
        preset_card.columnconfigure(1, weight=1)

        camera_card = ttk.LabelFrame(left, text="Camara", style="Card.TLabelframe", padding=10)
        camera_card.pack(fill="x", pady=(10, 0))
        ttk.Checkbutton(camera_card, text="Seguir cohete", variable=self.follow_var, command=self._toggle_follow).grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Checkbutton(camera_card, text="Mostrar trail", variable=self.show_trail_var, command=self.refresh_status).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(6, 0)
        )
        ttk.Label(camera_card, textvariable=self.zoom_var, style="Body.TLabel").grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))
        ttk.Button(camera_card, text="Zoom +", command=lambda: self._adjust_zoom(1.25)).grid(
            row=3, column=0, sticky="ew", pady=(8, 0), padx=(0, 4)
        )
        ttk.Button(camera_card, text="Zoom -", command=lambda: self._adjust_zoom(0.8)).grid(
            row=3, column=1, sticky="ew", pady=(8, 0), padx=(4, 0)
        )
        ttk.Button(camera_card, text="Encuadrar sistema", command=self._fit_camera_to_scene).grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )
        ttk.Label(
            camera_card,
            text="Rueda: zoom | Arrastre: paneo cuando el seguimiento esta apagado.",
            style="Hint.TLabel",
            wraplength=300,
            justify="left",
        ).grid(row=5, column=0, columnspan=2, sticky="w", pady=(8, 0))
        camera_card.columnconfigure((0, 1), weight=1)

        status_card = ttk.LabelFrame(right, text="Estado y visualizacion", style="Card.TLabelframe", padding=10)
        status_card.grid(row=0, column=0, sticky="nsew")
        status_card.columnconfigure(0, weight=1)
        status_card.rowconfigure(1, weight=1)

        ttk.Label(status_card, textvariable=self.status_var, style="Body.TLabel", wraplength=720, justify="left").grid(
            row=0, column=0, sticky="ew"
        )
        self.canvas = tk.Canvas(status_card, bg="#08101d", highlightthickness=0, width=760, height=420)
        self.canvas.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)
        self.canvas.bind("<ButtonPress-1>", self._start_pan)
        self.canvas.bind("<B1-Motion>", self._drag_pan)
        self.canvas.bind("<ButtonRelease-1>", self._stop_pan)

        log_card = ttk.LabelFrame(right, text="Bitacora de mision", style="Card.TLabelframe", padding=10)
        log_card.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        log_card.columnconfigure(0, weight=1)
        log_card.rowconfigure(0, weight=1)
        self.log_widget = tk.Text(
            log_card,
            height=14,
            bg="#0b1326",
            fg="#dbe7ff",
            insertbackground="#dbe7ff",
            wrap="word",
            relief="flat",
        )
        self.log_widget.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(log_card, orient="vertical", command=self.log_widget.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_widget.configure(yscrollcommand=scrollbar.set)
        self.log_widget.configure(state="disabled")

        for card in (launch_card, phase_card):
            card.columnconfigure(1, weight=1)

        self._sync_phase_hints()
        self._update_zoom_label()
        self._apply_time_speed()

    def _add_labeled_entry(self, parent: ttk.Widget, label: str, variable: tk.StringVar, row: int) -> None:
        ttk.Label(parent, text=label, style="Body.TLabel").grid(row=row, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=(6, 0))

    def _sync_phase_hints(self) -> None:
        frame = FrameType(self.phase_frame_var.get())
        if frame == FrameType.XY:
            self.primary_label.configure(text="f_x(t)")
            self.secondary_label.configure(text="f_y(t)")
            self.phase_hint_var.set("Usa aceleraciones inerciales en XY. Ideal para pruebas directas.")
        elif frame == FrameType.PROGRADE:
            self.primary_label.configure(text="f_prograde(t)")
            self.secondary_label.configure(text="f_normal(t)")
            self.phase_hint_var.set("Empuje alineado con la velocidad y su normal. Util para ascenso y circularizacion.")
        elif frame == FrameType.POLAR:
            self.primary_label.configure(text="f_r(t)")
            self.secondary_label.configure(text="f_theta(t)")
            self.phase_hint_var.set("Empuje en base radial/tangencial respecto al centro de la Tierra.")
        else:
            self.primary_label.configure(text="0")
            self.secondary_label.configure(text="0")
            self.phase_hint_var.set("Fase sin empuje. La nave solo coast/gravita.")

    def _read_float(self, variable: tk.StringVar, label: str) -> float:
        try:
            return float(variable.get())
        except ValueError as exc:
            raise ValueError(f"Valor invalido en '{label}'") from exc

    def _read_state(self) -> MissionPanelState:
        return MissionPanelState(
            launch_theta_deg=self._read_float(self.launch_theta_var, "Theta terrestre"),
            launch_altitude_m=self._read_float(self.launch_altitude_var, "Altitud"),
            launch_tangential_speed_m_s=self._read_float(self.launch_tangential_var, "Vel tangencial"),
            launch_radial_speed_m_s=self._read_float(self.launch_radial_var, "Vel radial"),
            moon_angle_deg=self._read_float(self.moon_angle_var, "Angulo Luna"),
            phase_duration_s=self._read_float(self.phase_duration_var, "Duracion fase"),
            phase_frame=self.phase_frame_var.get(),
            primary_expr=self.primary_expr_var.get().strip(),
            secondary_expr=self.secondary_expr_var.get().strip(),
            phase_label=self.phase_label_var.get().strip() or "Fase sin nombre",
        )

    def apply_launch_config(self, log_message: bool = True) -> None:
        try:
            self.state = self._read_state()
            self.simulation.set_moon_angle_deg(self.state.moon_angle_deg)
            self.simulation.place_rocket_on_surface(
                theta_deg=self.state.launch_theta_deg,
                altitude_m=self.state.launch_altitude_m,
                tangential_speed_m_s=self.state.launch_tangential_speed_m_s,
                radial_speed_m_s=self.state.launch_radial_speed_m_s,
            )
        except Exception as exc:
            messagebox.showerror("Configuracion invalida", str(exc))
            return

        if self.follow_var.get():
            self.camera.follow(self.simulation.rocket.position_xy)
        else:
            self.camera.set_center(self.simulation.rocket.position_xy)
        self._last_logged_termination = None
        self.refresh_status()
        if log_message:
            self.log("Configuracion inicial aplicada al cohete unico.")

    def add_phase(self) -> None:
        try:
            self.state = self._read_state()
            phase = self.state.build_phase()
            self.simulation.queue_phase(phase)
        except Exception as exc:
            messagebox.showerror("No se pudo agregar la fase", str(exc))
            return

        labels = phase.component_labels()
        self.log(
            f"Fase agregada: {phase.label} | duracion={phase.duration_s:.1f}s | frame={phase.frame.value} | {labels[0]}={phase.primary_expr} | {labels[1]}={phase.secondary_expr}"
        )
        self.refresh_status()

    def add_coast_phase(self) -> None:
        try:
            duration = self._read_float(self.phase_duration_var, "Duracion fase")
            label = self.phase_label_var.get().strip() or "Costa"
            phase = MissionPhase(label=label, duration_s=duration, frame=FrameType.NONE)
            self.simulation.queue_phase(phase)
        except Exception as exc:
            messagebox.showerror("No se pudo agregar la costa", str(exc))
            return

        self.log(f"Fase de costa agregada: {phase.label} | duracion={phase.duration_s:.1f}s")
        self.refresh_status()

    def run_next_phase(self) -> None:
        if self.simulation.is_running:
            self.log("La simulacion ya esta corriendo.")
            return
        if not self.simulation.resume():
            self.log("No hay fases pendientes para ejecutar.")
            return
        active = self.simulation.phase_manager.active
        self.log(f"Ejecutando fase: {active.label}")
        self._schedule_tick()

    def pause_simulation(self) -> None:
        self.simulation.pause()
        self._cancel_tick()
        self.log("Simulacion pausada manualmente.")
        self.refresh_status()

    def reset_mission(self) -> None:
        self._cancel_tick()
        self.simulation.reset()
        self.apply_launch_config(log_message=False)
        self.camera.follow(self.simulation.rocket.position_xy)
        self.follow_var.set(True)
        self._last_logged_termination = None
        self.log("Simulacion reiniciada. Cohete reposicionado y energia reseteada.")
        self.refresh_status()

    def clear_phases(self) -> None:
        self._cancel_tick()
        self.simulation.clear_phases()
        self._last_logged_termination = None
        self.log("Cola de fases limpiada.")
        self.refresh_status()

    def load_selected_preset(self) -> None:
        selected = self.preset_var.get()
        if selected == "manual":
            self.log("Preset manual seleccionado. No se cargaron fases.")
            return
        if selected not in {"orbita 200 km", "HEO 24h checkout", "HEO 24h NASA geometry", "transferencia translunar", "toy free return"}:
            self.log(f"Preset no reconocido: {selected}")
            return

        self._cancel_tick()
        self.simulation.clear_phases()

        if selected in {"HEO 24h checkout", "HEO 24h NASA geometry"}:
            heo = HEO_24H_CHECKOUT if selected == "HEO 24h checkout" else HEO_24H_NASA_GEOMETRY
            self.launch_altitude_var.set(str(heo["launch_altitude_m"]))
            self.launch_tangential_var.set(str(heo["launch_tangential_speed_m_s"]))
            self.launch_radial_var.set(str(heo["launch_radial_speed_m_s"]))
            self.apply_launch_config(log_message=False)
            preset_items = [heo["phase"]]
        elif selected in {"transferencia translunar", "toy free return"}:
            self.launch_altitude_var.set(str(HEO_24H_CHECKOUT["launch_altitude_m"]))
            self.launch_tangential_var.set(str(HEO_24H_CHECKOUT["launch_tangential_speed_m_s"]))
            self.launch_radial_var.set(str(HEO_24H_CHECKOUT["launch_radial_speed_m_s"]))
            if selected == "toy free return":
                self.moon_angle_var.set("206")
                preset_items = TOY_FREE_RETURN_PRESET
            else:
                self.moon_angle_var.set("200")
                preset_items = TRANSLUNAR_TRANSFER_PRESET
            self.apply_launch_config(log_message=False)
        else:
            self.launch_theta_var.set("90")
            self.launch_altitude_var.set("0")
            self.launch_tangential_var.set("0")
            self.launch_radial_var.set("0")
            self.moon_angle_var.set("0")
            self.apply_launch_config(log_message=False)
            preset_items = ORBIT_200KM_PRESET

        for item in preset_items:
            phase = MissionPhase(
                label=item["label"],
                duration_s=item["duration_s"],
                frame=item["frame"],
                primary_expr=item["primary_expr"],
                secondary_expr=item["secondary_expr"],
            )
            self.simulation.queue_phase(phase)

        first = preset_items[0]
        self.phase_label_var.set(first["label"])
        self.phase_duration_var.set(str(first["duration_s"]))
        self.phase_frame_var.set(first["frame"].value)
        self.primary_expr_var.set(first["primary_expr"])
        self.secondary_expr_var.set(first["secondary_expr"])
        self._sync_phase_hints()
        if selected == "toy free return":
            self.log("Preset 'toy free return' cargado: HEO 24h + TLI + guiado lunar suave + retorno.")
            self.log("Usa variables lunares: moon_dist, moon_vrel_r/t y behind_score para forzar paso trasero.")
        elif selected == "transferencia translunar":
            self.log("Preset 'transferencia translunar' cargado: arranca directo en HEO 24h, coast y luego TLI.")
            self.log("Angulo lunar inicial sugerido: 200 deg para sobrevuelo seguro; 210 deg impacta la Luna en este modelo.")
        elif selected == "HEO 24h checkout":
            self.log("Preset 'HEO 24h checkout' cargado: perigeo 185 km, v_t=10590.67 m/s, coast 86400 s.")
            self.log("Theta terrestre y angulo lunar quedan configurables para fasear la orientacion respecto de la Luna.")
        elif selected == "HEO 24h NASA geometry":
            self.log("Preset 'HEO 24h NASA geometry' cargado: perigeo 185 km, v_t=10591.20 m/s, coast 86554.69 s.")
            self.log("Theta terrestre y angulo lunar quedan configurables para fasear la orientacion respecto de la Luna.")
        else:
            self.log("Preset 'orbita 200 km' cargado en la cola de fases.")
        self._last_logged_termination = None
        self.refresh_status()

    def _apply_time_speed(self) -> None:
        text = self.time_speed_var.get().strip().lower().replace("x", "")
        try:
            value = int(text)
        except ValueError:
            return
        self.steps_per_frame = max(1, value)
        if self.steps_per_frame >= 500:
            self._render_every_ticks = 10
            self.max_trail_draw_points = 500
        elif self.steps_per_frame >= 100:
            self._render_every_ticks = 5
            self.max_trail_draw_points = 800
        elif self.steps_per_frame >= 30:
            self._render_every_ticks = 3
            self.max_trail_draw_points = 1000
        else:
            self._render_every_ticks = 1
            self.max_trail_draw_points = 1200
        self.log(f"Velocidad temporal ajustada a x{self.steps_per_frame}.")
        self.refresh_status()

    def _schedule_tick(self) -> None:
        self._cancel_tick()
        self._steps_remaining_this_frame = self.steps_per_frame
        self._scheduled_tick = self.after(1, self._tick)

    def _cancel_tick(self) -> None:
        if self._scheduled_tick is not None:
            self.after_cancel(self._scheduled_tick)
            self._scheduled_tick = None

    def _tick(self) -> None:
        self._scheduled_tick = None
        finished = None
        budget = min(self._max_steps_per_ui_pulse, max(1, self._steps_remaining_this_frame))
        for _ in range(budget):
            finished = self.simulation.update_step()
            self._steps_remaining_this_frame -= 1
            if finished is not None:
                break

        termination = self.simulation.termination_reason
        if finished is None and termination is None and self._steps_remaining_this_frame > 0 and self.simulation.is_running:
            self._scheduled_tick = self.after(1, self._tick)
            return

        self._tick_counter += 1
        should_render = finished is not None or termination is not None or self._tick_counter % self._render_every_ticks == 0

        if should_render:
            self.refresh_status()

        if finished is not None:
            self.log(self.simulation.phase_completion_message(finished))
            self.log("Simulacion pausada automaticamente. Esperando siguiente fase.")
            return

        if termination and termination != self._last_logged_termination:
            self._last_logged_termination = termination
            self.log(f"{termination}. Mision abortada.")
            return

        if self.simulation.is_running:
            self._schedule_tick()

    def refresh_status(self) -> None:
        snap = self.simulation.status_snapshot()
        if self.follow_var.get():
            self.camera.update_follow(snap["rocket_pos"])
        pending = snap["phase_pending"]
        active_label = snap["phase_label"] or "sin fase activa"
        pending_text = ", ".join(pending) if pending else "sin fases pendientes"
        termination_reason = snap["termination_reason"] or "-"
        self.status_var.set(
            "\n".join(
                [
                    f"Tiempo mision: {format_seconds(float(snap['sim_time_s']))} | Estado: {'corriendo' if snap['is_running'] else 'pausado'}",
                    f"Fase activa: {active_label} | tiempo en fase: {float(snap['phase_elapsed_s']):.1f} s",
                    f"Pendientes: {pending_text}",
                    f"Evento terminal: {termination_reason}",
                    f"Posicion XY: ({snap['rocket_pos'][0]:.1f}, {snap['rocket_pos'][1]:.1f}) m",
                    f"r,theta: ({float(snap['rocket_radius_m']):.1f} m, {float(snap['rocket_theta_deg']):.2f} deg)",
                    f"Velocidad XY: ({snap['rocket_vel'][0]:.2f}, {snap['rocket_vel'][1]:.2f}) m/s | |v|={float(snap['rocket_speed_m_s']):.2f} m/s",
                    f"Estado orbital: {snap['orbit_state']}",
                    f"Min distancia Luna: {float(snap['min_moon_distance_m'])/1000:.1f} km en t={format_seconds(float(snap['min_moon_distance_time_s']))}",
                    f"Behind score en peri-lunio: {float(snap['min_moon_behind_score']):.3f} (<0 detras, >0 delante)",
                    f"Camara: centro=({self.camera.center_xy[0]:.1f}, {self.camera.center_xy[1]:.1f}) m | zoom={self.camera.zoom:.2f}x | seguimiento={'on' if self.follow_var.get() else 'off'}",
                    f"Tiempo en pantalla: x{self.steps_per_frame}",
                    thrust_indicator_text(snap["thrust_xy"]),
                    f"Delta-v acumulado: {float(snap['delta_v_m_s']):.2f} m/s | Energia de impulso: {format_energy(float(snap['work_j']))}",
                ]
            )
        )
        self._update_zoom_label()
        self._draw_scene(snap)

    def _draw_scene(self, snap: dict[str, object]) -> None:
        width = max(self.canvas.winfo_width(), 760)
        height = max(self.canvas.winfo_height(), 420)
        self.canvas.delete("all")

        cx = width * 0.5
        cy = height * 0.52
        rocket_pos = snap["rocket_pos"]
        moon_pos = snap["moon_pos"]
        offsets = (
            (0.0 - self.camera.center_xy[0], 0.0 - self.camera.center_xy[1]),
            (rocket_pos[0] - self.camera.center_xy[0], rocket_pos[1] - self.camera.center_xy[1]),
            (moon_pos[0] - self.camera.center_xy[0], moon_pos[1] - self.camera.center_xy[1]),
        )
        farthest = max(magnitude(offset) for offset in offsets)
        if farthest < 1.0:
            farthest = 6_371_000.0
        base_scale = (min(width, height) * 0.38) / farthest
        scale = base_scale * self.camera.zoom
        earth_radius_px = max(8.0, 6_371_000.0 * scale)
        moon_radius_px = max(4.0, 1_737_400.0 * scale)

        def world_to_canvas(vec: tuple[float, float]) -> tuple[float, float]:
            return (
                cx + (vec[0] - self.camera.center_xy[0]) * scale,
                cy - (vec[1] - self.camera.center_xy[1]) * scale,
            )

        earth_canvas = world_to_canvas((0.0, 0.0))
        self.canvas.create_oval(
            earth_canvas[0] - earth_radius_px,
            earth_canvas[1] - earth_radius_px,
            earth_canvas[0] + earth_radius_px,
            earth_canvas[1] + earth_radius_px,
            fill="#1d4ed8",
            outline="#93c5fd",
            width=2,
        )

        moon_canvas = world_to_canvas(moon_pos)
        self.canvas.create_oval(
            moon_canvas[0] - moon_radius_px,
            moon_canvas[1] - moon_radius_px,
            moon_canvas[0] + moon_radius_px,
            moon_canvas[1] + moon_radius_px,
            fill="#cbd5e1",
            outline="#f8fafc",
            width=1,
        )

        trail = self.simulation.rocket.trail
        if self.show_trail_var.get() and len(trail) > 1:
            points: list[float] = []
            max_draw_points = self.max_trail_draw_points
            stride = max(1, len(trail) // max_draw_points)
            for point in trail[::stride]:
                px, py = world_to_canvas(point)
                points.extend((px, py))
            self.canvas.create_line(*points, fill="#f59e0b", width=2, smooth=True)

        rocket_canvas = world_to_canvas(rocket_pos)
        self.canvas.create_oval(
            rocket_canvas[0] - 5,
            rocket_canvas[1] - 5,
            rocket_canvas[0] + 5,
            rocket_canvas[1] + 5,
            fill="#ef4444",
            outline="#fff7ed",
            width=1,
        )

        thrust_xy = snap["thrust_xy"]
        thrust_mag = float(snap["thrust_mag_m_s2"])
        if thrust_mag > 0.0:
            arrow_scale = 18.0 / thrust_mag if thrust_mag > 18.0 else 1.0
            tx = rocket_canvas[0] + thrust_xy[0] * arrow_scale * 8.0
            ty = rocket_canvas[1] - thrust_xy[1] * arrow_scale * 8.0
            self.canvas.create_line(rocket_canvas[0], rocket_canvas[1], tx, ty, fill="#fde047", width=3, arrow=tk.LAST)

        termination = snap["termination_reason"] or ""
        if "Impacto" in termination:
            cross_size = 10
            self.canvas.create_line(
                rocket_canvas[0] - cross_size,
                rocket_canvas[1] - cross_size,
                rocket_canvas[0] + cross_size,
                rocket_canvas[1] + cross_size,
                fill="#f8fafc",
                width=3,
            )
            self.canvas.create_line(
                rocket_canvas[0] - cross_size,
                rocket_canvas[1] + cross_size,
                rocket_canvas[0] + cross_size,
                rocket_canvas[1] - cross_size,
                fill="#f8fafc",
                width=3,
            )

        self.canvas.create_text(18, 18, anchor="nw", fill="#dbe7ff", font=("Segoe UI", 10, "bold"), text="Tierra")
        self.canvas.create_text(moon_canvas[0] + 10, moon_canvas[1] - 10, anchor="sw", fill="#e2e8f0", font=("Segoe UI", 10), text="Luna")
        self.canvas.create_text(rocket_canvas[0] + 10, rocket_canvas[1] + 10, anchor="nw", fill="#fca5a5", font=("Segoe UI", 10), text="Cohete")
        self.canvas.create_text(
            18,
            38,
            anchor="nw",
            fill="#93a4c3",
            font=("Segoe UI", 9),
            text=f"Zoom {self.camera.zoom:.2f}x | seguimiento {'on' if self.follow_var.get() else 'off'}",
        )

    def log(self, message: str) -> None:
        self.log_widget.configure(state="normal")
        self.log_widget.insert("end", f"{message}\n")
        self.log_widget.see("end")
        self.log_widget.configure(state="disabled")

    def _toggle_follow(self) -> None:
        if self.follow_var.get():
            self.camera.follow(self.simulation.rocket.position_xy)
            self.log("Seguimiento del cohete activado.")
        else:
            self.camera.stop_follow()
            self.log("Seguimiento del cohete desactivado.")
        self.refresh_status()

    def _adjust_zoom(self, factor: float) -> None:
        self.camera.zoom_by(factor)
        self.refresh_status()

    def _fit_camera_to_scene(self) -> None:
        moon_pos = self.simulation.moon.position_xy
        rocket_pos = self.simulation.rocket.position_xy
        center = (
            (moon_pos[0] + rocket_pos[0]) * 0.5,
            (moon_pos[1] + rocket_pos[1]) * 0.5,
        )
        self.camera.set_center(center)
        self.camera.stop_follow()
        self.follow_var.set(False)
        self.camera.set_zoom(1.0)
        self.log("Camara reencuadrada para mostrar Tierra, Luna y cohete.")
        self.refresh_status()

    def _update_zoom_label(self) -> None:
        self.zoom_var.set(f"Zoom {self.camera.zoom:.2f}x")

    def _on_mousewheel(self, event: tk.Event) -> None:
        if hasattr(event, "delta") and event.delta:
            factor = 1.12 if event.delta > 0 else 0.89
        else:
            num = getattr(event, "num", 0)
            factor = 1.12 if num == 4 else 0.89
        self._adjust_zoom(factor)

    def _start_pan(self, event: tk.Event) -> None:
        self._drag_last_xy = (event.x, event.y)

    def _drag_pan(self, event: tk.Event) -> None:
        if self.follow_var.get():
            return
        if self._drag_last_xy is None:
            self._drag_last_xy = (event.x, event.y)
            return

        width = max(self.canvas.winfo_width(), 760)
        height = max(self.canvas.winfo_height(), 420)
        moon_pos = self.simulation.moon.position_xy
        rocket_pos = self.simulation.rocket.position_xy
        offsets = (
            (0.0 - self.camera.center_xy[0], 0.0 - self.camera.center_xy[1]),
            (rocket_pos[0] - self.camera.center_xy[0], rocket_pos[1] - self.camera.center_xy[1]),
            (moon_pos[0] - self.camera.center_xy[0], moon_pos[1] - self.camera.center_xy[1]),
        )
        farthest = max(magnitude(offset) for offset in offsets)
        if farthest < 1.0:
            farthest = 6_371_000.0
        scale = ((min(width, height) * 0.38) / farthest) * self.camera.zoom
        if scale <= 0.0:
            return

        dx_px = event.x - self._drag_last_xy[0]
        dy_px = event.y - self._drag_last_xy[1]
        self.camera.pan((-dx_px / scale, dy_px / scale))
        self._drag_last_xy = (event.x, event.y)
        self.refresh_status()

    def _stop_pan(self, _event: tk.Event) -> None:
        self._drag_last_xy = None
