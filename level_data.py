"""Level constants and geometry shared between runtime and tests."""

from core import Rect

SCREEN_W, SCREEN_H = 1200, 720
WORLD_W = 4200
FLOOR_H = 44


def build_level() -> list[Rect]:
    """Traversable staircase-like level spanning 7 zones."""
    return [
        Rect(0, SCREEN_H - FLOOR_H, WORLD_W, FLOOR_H),
        Rect(180, 600, 430, 20),
        Rect(690, 540, 430, 20),
        Rect(1210, 480, 420, 20),
        Rect(1730, 420, 430, 20),
        Rect(2240, 360, 430, 20),
        Rect(2750, 300, 430, 20),
        Rect(3260, 240, 430, 20),
        Rect(3770, 160, 360, 20),
        Rect(320, 470, 210, 18),
        Rect(1030, 410, 190, 18),
        Rect(2060, 300, 200, 18),
        Rect(3050, 240, 180, 18),
    ]
