"""Level constants and geometry shared between runtime and tests."""

from core import Rect

SCREEN_W, SCREEN_H = 1200, 720
WORLD_W = 9800
WORLD_H = 1920
FLOOR_H = 44
WORLD_Y_OFFSET = 760


def build_level() -> list[Rect]:
    """Massive multi-floor complex with shore approach, interior blocks, and basement."""
    oy = WORLD_Y_OFFSET
    solids: list[Rect] = [
        # Underwater seabed so the player cannot fall through at spawn.
        Rect(0, SCREEN_H - 24 + oy, 960, 24),
        Rect(220, SCREEN_H - 110 + oy, 360, 22),
        Rect(560, SCREEN_H - 170 + oy, 380, 24),
        Rect(960, SCREEN_H - FLOOR_H + oy, WORLD_W - 960, FLOOR_H),
        Rect(1120, 680 + oy, 1700, 20),
        Rect(3020, 680 + oy, 1500, 20),
        Rect(4700, 680 + oy, 1500, 20),
        Rect(6420, 680 + oy, 1700, 20),
    ]

    # Guaranteed traversable chain for playability tests and long-form progression.
    x = 980
    y = 620 + oy
    while x < 9300:
        solids.append(Rect(x, y, 420, 22))
        x += 500
        y -= 38
        y = max(90 + oy, min(640 + oy, y))

    solids.extend(
        [
            Rect(1420, 430 + oy, 260, 18),
            Rect(1920, 390 + oy, 260, 18),
            Rect(2440, 350 + oy, 260, 18),
            Rect(2960, 310 + oy, 260, 18),
            Rect(3480, 270 + oy, 260, 18),
            Rect(4000, 230 + oy, 260, 18),
            Rect(4520, 190 + oy, 260, 18),
            Rect(5040, 150 + oy, 260, 18),
            Rect(5560, 110 + oy, 260, 18),
            Rect(6080, 80 + oy, 260, 18),
            Rect(3000, 620 + oy, 420, 18),
            Rect(5950, 620 + oy, 460, 18),
            # Main skyscraper shell + interior decks.
            Rect(7060, 78 + oy, 24, 602),
            Rect(9550, 70 + oy, 30, 610),
            Rect(7040, 678 + oy, 2560, 22),
            Rect(7120, 616 + oy, 2320, 18),
            Rect(7180, 552 + oy, 2210, 18),
            Rect(7260, 488 + oy, 2080, 18),
            Rect(7360, 424 + oy, 1940, 18),
            Rect(7440, 360 + oy, 1780, 18),
            Rect(7520, 296 + oy, 1620, 18),
            Rect(7600, 232 + oy, 1450, 18),
            Rect(7680, 168 + oy, 1290, 18),
            Rect(7740, 104 + oy, 1160, 18),
            # Stair blocks for ascend + descend options.
            Rect(7340, 642 + oy, 160, 36),
            Rect(7500, 606 + oy, 160, 36),
            Rect(7660, 570 + oy, 160, 36),
            Rect(7820, 534 + oy, 160, 36),
            Rect(7980, 498 + oy, 160, 36),
            Rect(8140, 462 + oy, 160, 36),
            Rect(8300, 426 + oy, 160, 36),
            Rect(8460, 390 + oy, 160, 36),
            Rect(8620, 354 + oy, 160, 36),
            Rect(8780, 318 + oy, 160, 36),
            Rect(8940, 282 + oy, 160, 36),
            Rect(9100, 246 + oy, 160, 36),
            Rect(9260, 210 + oy, 160, 36),
            Rect(9420, 174 + oy, 160, 36),
            # Extra vertical-space roofs to make each area span roughly two screens in height.
            Rect(7350, 340, 1540, 18),
            Rect(7480, 268, 1310, 16),
            Rect(7600, 196, 1060, 14),
            Rect(7740, 124, 840, 14),
        ]
    )
    return solids



def build_one_way_platforms() -> list[Rect]:
    """Jump-through interior floors and maintenance decks."""
    oy = WORLD_Y_OFFSET
    return [
        Rect(1260, 540 + oy, 420, 14),
        Rect(1760, 500 + oy, 500, 14),
        Rect(2360, 460 + oy, 420, 14),
        Rect(2880, 420 + oy, 500, 14),
        Rect(3460, 380 + oy, 520, 14),
        Rect(4060, 340 + oy, 500, 14),
        Rect(4640, 300 + oy, 530, 14),
        Rect(5250, 260 + oy, 520, 14),
        Rect(5840, 220 + oy, 560, 14),
        Rect(6460, 180 + oy, 560, 14),
        Rect(7080, 220 + oy, 520, 14),
        Rect(7700, 260 + oy, 500, 14),
        Rect(8300, 300 + oy, 480, 14),
        Rect(8880, 260 + oy, 560, 14),
        # Basement maintenance crossovers
        Rect(1320, 640 + oy, 240, 12),
        Rect(2040, 640 + oy, 260, 12),
        Rect(3300, 640 + oy, 280, 12),
        Rect(5120, 640 + oy, 320, 12),
        Rect(6900, 640 + oy, 300, 12),
        # Tower rooms + server/electrical catwalks.
        Rect(7220, 594 + oy, 620, 12),
        Rect(8020, 594 + oy, 620, 12),
        Rect(8820, 594 + oy, 540, 12),
        Rect(7340, 530 + oy, 680, 12),
        Rect(8200, 530 + oy, 700, 12),
        Rect(7500, 466 + oy, 700, 12),
        Rect(8380, 466 + oy, 700, 12),
        Rect(7660, 402 + oy, 760, 12),
        Rect(8580, 402 + oy, 620, 12),
        Rect(7780, 338 + oy, 660, 12),
        Rect(8540, 338 + oy, 620, 12),
        Rect(7900, 274 + oy, 520, 12),
        Rect(8520, 274 + oy, 470, 12),
        Rect(8020, 210 + oy, 450, 12),
        Rect(8560, 210 + oy, 360, 12),
        Rect(8120, 146 + oy, 360, 12),
        Rect(8560, 146 + oy, 280, 12),
        # Upper skyscraper vertical exploration.
        Rect(7480, 320, 560, 12),
        Rect(8200, 248, 520, 12),
        Rect(7860, 176, 540, 12),
    ]


def build_ladders() -> list[Rect]:
    oy = WORLD_Y_OFFSET
    return [
        Rect(1510, 544 + oy, 34, 136),
        Rect(2110, 504 + oy, 34, 176),
        Rect(2700, 464 + oy, 34, 216),
        Rect(3280, 424 + oy, 34, 256),
        Rect(3880, 384 + oy, 34, 296),
        Rect(4480, 344 + oy, 34, 336),
        Rect(5100, 304 + oy, 34, 376),
        Rect(5720, 264 + oy, 34, 416),
        Rect(6360, 224 + oy, 34, 456),
        Rect(7000, 184 + oy, 34, 496),
        Rect(7600, 224 + oy, 34, 456),
        Rect(8220, 264 + oy, 34, 416),
        Rect(8840, 304 + oy, 34, 376),
        # Tower ladder shafts and maintenance ladders.
        Rect(7460, 146 + oy, 34, 532),
        Rect(8120, 106 + oy, 34, 572),
        Rect(8780, 86 + oy, 34, 592),
        Rect(9340, 106 + oy, 34, 572),
        # Upper tower ladders.
        Rect(7860, 182, 34, 176),
        Rect(8440, 110, 34, 176),
    ]


def build_water_zones() -> list[Rect]:
    return [Rect(0, SCREEN_H - 150 + WORLD_Y_OFFSET, 760, 180)]


def build_bushes() -> list[Rect]:
    oy = WORLD_Y_OFFSET
    return [
        Rect(1220, SCREEN_H - 88 + oy, 120, 40),
        Rect(2100, SCREEN_H - 88 + oy, 130, 40),
        Rect(3200, SCREEN_H - 88 + oy, 160, 40),
        Rect(4720, SCREEN_H - 88 + oy, 150, 40),
        Rect(6400, SCREEN_H - 88 + oy, 170, 40),
        Rect(8180, SCREEN_H - 88 + oy, 140, 40),
    ]


def build_train_track() -> tuple[float, float, float]:
    """y, x_min, x_max"""
    return (652.0 + WORLD_Y_OFFSET, 3100.0, 6300.0)
