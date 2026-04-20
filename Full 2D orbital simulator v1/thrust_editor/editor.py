# thrust_editor/editor.py
from core.physics.thrust import ThrustProfile

class ThrustEditor:
    """
    Backend para editar thrust con expresiones matemáticas.
    """
    def __init__(self):
        self.current_profile: ThrustProfile = None
        self.thrust_x_expr: str = "0.0"
        self.thrust_y_expr: str = "0.0"

    def load_profile(self, profile: ThrustProfile):
        self.current_profile = profile
        if profile:
            self.thrust_x_expr = profile.thrust_x_expr
            self.thrust_y_expr = profile.thrust_y_expr

    def apply_expressions(self, x_expr: str, y_expr: str):
        """Aplica las nuevas expresiones al perfil"""
        if self.current_profile:
            self.current_profile.set_expressions(x_expr, y_expr)
            self.thrust_x_expr = x_expr
            self.thrust_y_expr = y_expr
            print(f"Thrust actualizado → X: {x_expr} | Y: {y_expr}")