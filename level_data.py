"""Level constants and geometry shared between runtime and tests."""

from core import Rect

SCREEN_W, SCREEN_H = 1200, 720
WORLD_W = 16800
WORLD_H = 3320
FLOOR_H = 44
WORLD_Y_OFFSET = 760


def build_level() -> list[Rect]:
    """Massive multi-floor complex with shore approach, interior blocks, and a huge skyscraper."""
    oy = WORLD_Y_OFFSET
    solids: list[Rect] = [
        # Underwater seabed so the player cannot fall through at spawn.
        Rect(0, SCREEN_H - 24 + oy, 960, 24),
        Rect(220, SCREEN_H - 110 + oy, 360, 22),
        Rect(560, SCREEN_H - 170 + oy, 380, 24),
        Rect(960, SCREEN_H - FLOOR_H + oy, 2240, FLOOR_H),
        Rect(3360, SCREEN_H - FLOOR_H + oy, 2960, FLOOR_H),
        Rect(6500, SCREEN_H - FLOOR_H + oy, 3560, FLOOR_H),
        Rect(10240, SCREEN_H - FLOOR_H + oy, 3200, FLOOR_H),
        Rect(13620, SCREEN_H - FLOOR_H + oy, 3180, FLOOR_H),
        Rect(1120, 680 + oy, 2400, 20),
        Rect(3560, 680 + oy, 2400, 20),
        Rect(6020, 680 + oy, 2600, 20),
        Rect(8660, 680 + oy, 2400, 20),
        Rect(11100, 680 + oy, 2200, 20),
        Rect(13340, 680 + oy, 2200, 20),
    ]

    # Guaranteed traversable chain for playability tests and long-form progression.
    x = 980
    y = 620 + oy
    while x < 15800:
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
            # Main skyscraper shell + many-screen interior decks.
            Rect(7060, 76 + oy, 24, 604),
            Rect(15920, 72 + oy, 30, 608),
            Rect(7040, 678 + oy, 8920, 22),
            Rect(7140, 614 + oy, 8720, 18),
            Rect(7240, 550 + oy, 8520, 18),
            Rect(7340, 486 + oy, 8320, 18),
            Rect(7440, 422 + oy, 8120, 18),
            Rect(7540, 358 + oy, 7920, 18),
            Rect(7640, 294 + oy, 7720, 18),
            Rect(7740, 230 + oy, 7520, 18),
            Rect(7840, 166 + oy, 7320, 18),
            Rect(7940, 102 + oy, 7120, 18),
            Rect(8060, 38 + oy, 6880, 18),
            Rect(8200, -26 + oy, 6560, 16),
            Rect(8360, -90 + oy, 6200, 16),
            Rect(8540, -154 + oy, 5820, 16),
            Rect(8740, -218 + oy, 5400, 16),
            Rect(8960, -282 + oy, 4940, 16),
            Rect(9200, -346 + oy, 4440, 16),
            Rect(9460, -410 + oy, 3900, 16),
            Rect(9740, -474 + oy, 3300, 16),
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
            # Tower traversal blocks continue deep into upper levels.
            Rect(10200, 642 + oy, 180, 36),
            Rect(10400, 606 + oy, 180, 36),
            Rect(10600, 570 + oy, 180, 36),
            Rect(10800, 534 + oy, 180, 36),
            Rect(11000, 498 + oy, 180, 36),
            Rect(11200, 462 + oy, 180, 36),
            Rect(11400, 426 + oy, 180, 36),
            Rect(11600, 390 + oy, 180, 36),
            Rect(11800, 354 + oy, 180, 36),
            Rect(12000, 318 + oy, 180, 36),
            Rect(12200, 282 + oy, 180, 36),
            Rect(12400, 246 + oy, 180, 36),
            Rect(12600, 210 + oy, 180, 36),
            Rect(12800, 174 + oy, 180, 36),
            Rect(13000, 138 + oy, 180, 36),
            Rect(13200, 102 + oy, 180, 36),
            Rect(13400, 66 + oy, 180, 36),
            Rect(13600, 30 + oy, 180, 36),
            # Extra vertical-space roofs to make each area span many screens in height.
            Rect(7350, 340, 1540, 18),
            Rect(7480, 268, 1310, 16),
            Rect(7600, 196, 1060, 14),
            Rect(7740, 124, 840, 14),
            Rect(9000, 420, 2200, 18),
            Rect(9480, 332, 2060, 16),
            Rect(10020, 244, 1880, 16),
            Rect(10640, 156, 1660, 14),
            Rect(11280, 68, 1420, 14),
            Rect(11940, -20, 1160, 14),
            Rect(12620, -108, 880, 14),
            # Lower cavern maze (multiple underground screens).
            Rect(1740, 1640, 2800, 26),
            Rect(4700, 1640, 1900, 26),
            Rect(6900, 1640, 2300, 26),
            Rect(9600, 1640, 2200, 26),
            Rect(12040, 1640, 3000, 26),
            Rect(1820, 1860, 840, 22),
            Rect(2860, 1860, 760, 22),
            Rect(3820, 1860, 900, 22),
            Rect(5000, 1860, 980, 22),
            Rect(6180, 1860, 860, 22),
            Rect(7240, 1860, 960, 22),
            Rect(8380, 1860, 940, 22),
            Rect(9500, 1860, 980, 22),
            Rect(10680, 1860, 900, 22),
            Rect(11780, 1860, 1000, 22),
            Rect(12980, 1860, 980, 22),
            Rect(14180, 1860, 980, 22),
            Rect(1640, 2120, 760, 22),
            Rect(2580, 2120, 700, 22),
            Rect(3440, 2120, 760, 22),
            Rect(4380, 2120, 760, 22),
            Rect(5320, 2120, 760, 22),
            Rect(6260, 2120, 760, 22),
            Rect(7200, 2120, 760, 22),
            Rect(8140, 2120, 760, 22),
            Rect(9080, 2120, 760, 22),
            Rect(10020, 2120, 760, 22),
            Rect(10960, 2120, 760, 22),
            Rect(11900, 2120, 760, 22),
            Rect(12840, 2120, 760, 22),
            Rect(13780, 2120, 760, 22),
            Rect(14720, 2120, 760, 22),
            Rect(1740, 2380, 1200, 22),
            Rect(3220, 2380, 1220, 22),
            Rect(4720, 2380, 1160, 22),
            Rect(6120, 2380, 1240, 22),
            Rect(7620, 2380, 1160, 22),
            Rect(9000, 2380, 1260, 22),
            Rect(10520, 2380, 1200, 22),
            Rect(11980, 2380, 1240, 22),
            Rect(13480, 2380, 1160, 22),
            Rect(15000, 2380, 1040, 22),
            Rect(1520, 2660, 15280, 28),
            Rect(1400, 2920, 15600, 56),
        ]
    )
    return solids



def build_one_way_platforms() -> list[Rect]:
    """Jump-through interior floors and maintenance decks."""
    oy = WORLD_Y_OFFSET
    plats = [
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

    # Wide skyscraper rooms spanning many screens with jump-through floors.
    for x in range(9300, 15600, 620):
        plats.append(Rect(x, 594 + oy, 520, 12))
        plats.append(Rect(x + 120, 530 + oy, 460, 12))
        plats.append(Rect(x + 240, 466 + oy, 420, 12))
        plats.append(Rect(x + 180, 402 + oy, 460, 12))
    for x in range(9800, 15000, 740):
        plats.append(Rect(x, 338 + oy, 420, 12))
        plats.append(Rect(x + 100, 274 + oy, 360, 12))
        plats.append(Rect(x + 180, 210 + oy, 320, 12))
    for x, y in [(10600, 248), (11400, 176), (12200, 104), (13000, 32), (13800, -40), (14600, -112)]:
        plats.append(Rect(x, y, 560, 12))

    # Underground catwalks through the cavern maze.
    for x in range(1900, 15500, 880):
        plats.append(Rect(x, 1730, 420, 12))
        plats.append(Rect(x + 200, 1990, 360, 12))
        plats.append(Rect(x + 80, 2250, 380, 12))
        plats.append(Rect(x + 260, 2510, 340, 12))

    return plats


def build_ladders() -> list[Rect]:
    oy = WORLD_Y_OFFSET
    ladders = [
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

    # Deep ladder grid so every major tower floor can be climbed up and down.
    for x in [9560, 10320, 11080, 11840, 12600, 13360, 14120, 14880]:
        ladders.append(Rect(x, -180 + oy, 34, 860))
    for x in [9900, 10660, 11420, 12180, 12940, 13700, 14460, 15220]:
        ladders.append(Rect(x, -430 + oy, 34, 630))

    # Cavern shafts and maze connectors.
    for x in [3240, 6380, 10080, 13600]:
        ladders.append(Rect(x, 1390, 34, 1290))
    for x in [1860, 2340, 2840, 3360, 3920, 4520, 5140, 5760, 6440, 7120, 7780, 8460, 9140, 9820, 10500, 11180, 11860, 12540, 13220, 13900, 14580, 15260]:
        ladders.append(Rect(x, 1600, 34, 1060))

    return ladders


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
