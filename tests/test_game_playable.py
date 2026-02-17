from collections import deque

from core import JUMP_VELOCITY
from level_data import SCREEN_H, SCREEN_W, WORLD_H, WORLD_Y_OFFSET, build_level


def _platform_nodes():
    solids = build_level()
    return [(s.x + s.w / 2, s.y) for s in solids if s.w >= 100]


def _reachable(a, b):
    ax, ay = a
    bx, by = b
    dx = abs(bx - ax)
    dy_up = ay - by

    max_jump_up = (abs(JUMP_VELOCITY) ** 2) / (2 * 1800.0)
    if dy_up > max_jump_up + 8:
        return False

    if dy_up >= 0:
        return dx <= 560
    return dx <= 640 and (by - ay) <= 520


def test_level_route_to_extraction_is_connected():
    nodes = sorted(_platform_nodes(), key=lambda p: p[0])
    assert nodes, "No walkable nodes discovered"

    seen = {0}
    q = deque([0])
    while q:
        i = q.popleft()
        for j in range(len(nodes)):
            if j not in seen and _reachable(nodes[i], nodes[j]):
                seen.add(j)
                q.append(j)

    farthest = max(nodes[i][0] for i in seen)
    assert farthest > 15000, "Level does not provide a traversable route across the skyscraper"


def test_game_module_constants_for_vertical_space():
    assert SCREEN_H >= 700
    assert WORLD_H >= SCREEN_H * 4


def test_spawn_side_has_floor_under_water():
    solids = build_level()
    # Ensure there is a solid seabed under the initial water zone to prevent falling out.
    assert any(s.x <= 64 <= s.x + s.w and s.y >= SCREEN_H - 40 + WORLD_Y_OFFSET for s in solids)


def test_has_upper_tower_routes_for_vertical_exploration():
    solids = build_level()
    assert any(s.y < WORLD_Y_OFFSET for s in solids)


def test_level_width_supports_many_screen_skyscraper():
    from level_data import WORLD_W

    assert WORLD_W >= SCREEN_W * 10


def test_has_lower_cavern_maze_layers():
    solids = build_level()
    deep_layers = [s for s in solids if s.y >= 1800]
    assert len(deep_layers) >= 20


def test_main_floor_has_access_shafts_to_caverns():
    solids = build_level()
    floor_y = SCREEN_H - 44 + WORLD_Y_OFFSET
    floor_segments = sorted((s.x, s.x + s.w) for s in solids if s.y == floor_y and s.h == 44)
    assert len(floor_segments) >= 4


def test_has_helipad_top_and_silo_chamber():
    solids = build_level()
    assert any(s.y <= -220 and s.w >= 900 for s in solids)
    assert any(5200 <= s.x <= 5600 and s.y >= 2400 and s.w >= 3000 for s in solids)


def test_xp_curve_increases_per_level():
    from game import xp_to_next_level

    assert xp_to_next_level(1) < xp_to_next_level(2) < xp_to_next_level(5)
    assert xp_to_next_level(1) >= 50
