from dataclasses import dataclass


@dataclass(slots=True)
class Telemetry:
    steering: float = 0.0
    throttle: float = 0.0
    brake: float = 0.0
    clutch: float = 0.0
    hat_x: int = 0
    hat_y: int = 0
    pressed_buttons: tuple[int, ...] = ()
