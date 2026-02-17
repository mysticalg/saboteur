"""Level constants and geometry shared between runtime and tests."""

from core import Rect

SCREEN_W, SCREEN_H = 1200, 720
WORLD_W = 9800
FLOOR_H = 44


def build_level() -> list[Rect]:
    """Massive multi-floor complex with shore approach, interior blocks, and basement."""
    solids: list[Rect] = [
        Rect(220, SCREEN_H - 110, 360, 22),
        Rect(560, SCREEN_H - 170, 380, 24),
        Rect(960, SCREEN_H - FLOOR_H, WORLD_W - 960, FLOOR_H),
        Rect(1120, 680, 1700, 20),
        Rect(3020, 680, 1500, 20),
        Rect(4700, 680, 1500, 20),
        Rect(6420, 680, 1700, 20),
    ]

    # Guaranteed traversable chain for playability tests and long-form progression.
    x = 980
    y = 620
    while x < 9300:
        solids.append(Rect(x, y, 420, 22))
        x += 500
        y -= 38
        y = max(90, min(640, y))

    solids.extend(
        [
            Rect(1420, 430, 260, 18),
            Rect(1920, 390, 260, 18),
            Rect(2440, 350, 260, 18),
            Rect(2960, 310, 260, 18),
            Rect(3480, 270, 260, 18),
            Rect(4000, 230, 260, 18),
            Rect(4520, 190, 260, 18),
            Rect(5040, 150, 260, 18),
            Rect(5560, 110, 260, 18),
            Rect(6080, 80, 260, 18),
            Rect(3000, 620, 420, 18),
            Rect(5950, 620, 460, 18),
        ]
    )
    return solids



def build_one_way_platforms() -> list[Rect]:
    """Jump-through interior floors and maintenance decks."""
    return [
        Rect(1260, 540, 420, 14),
        Rect(1760, 500, 500, 14),
        Rect(2360, 460, 420, 14),
        Rect(2880, 420, 500, 14),
        Rect(3460, 380, 520, 14),
        Rect(4060, 340, 500, 14),
        Rect(4640, 300, 530, 14),
        Rect(5250, 260, 520, 14),
        Rect(5840, 220, 560, 14),
        Rect(6460, 180, 560, 14),
        Rect(7080, 220, 520, 14),
        Rect(7700, 260, 500, 14),
        Rect(8300, 300, 480, 14),
        Rect(8880, 260, 560, 14),
        # Basement maintenance crossovers
        Rect(1320, 640, 240, 12),
        Rect(2040, 640, 260, 12),
        Rect(3300, 640, 280, 12),
        Rect(5120, 640, 320, 12),
        Rect(6900, 640, 300, 12),
    ]


def build_ladders() -> list[Rect]:
    return [
        Rect(1510, 544, 34, 136),
        Rect(2110, 504, 34, 176),
        Rect(2700, 464, 34, 216),
        Rect(3280, 424, 34, 256),
        Rect(3880, 384, 34, 296),
        Rect(4480, 344, 34, 336),
        Rect(5100, 304, 34, 376),
        Rect(5720, 264, 34, 416),
        Rect(6360, 224, 34, 456),
        Rect(7000, 184, 34, 496),
        Rect(7600, 224, 34, 456),
        Rect(8220, 264, 34, 416),
        Rect(8840, 304, 34, 376),
    ]


def build_water_zones() -> list[Rect]:
    return [Rect(0, SCREEN_H - 150, 760, 180)]


def build_bushes() -> list[Rect]:
    return [
        Rect(1220, SCREEN_H - 88, 120, 40),
        Rect(2100, SCREEN_H - 88, 130, 40),
        Rect(3200, SCREEN_H - 88, 160, 40),
        Rect(4720, SCREEN_H - 88, 150, 40),
        Rect(6400, SCREEN_H - 88, 170, 40),
        Rect(8180, SCREEN_H - 88, 140, 40),
    ]


def build_train_track() -> tuple[float, float, float]:
    """y, x_min, x_max"""
    return (652.0, 3100.0, 6300.0)
