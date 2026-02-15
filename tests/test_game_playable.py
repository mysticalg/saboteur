from collections import deque

from core import JUMP_VELOCITY
from level_data import SCREEN_H, build_level


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
    assert farthest > 3800, "Level does not provide a traversable route to extraction area"


def test_game_module_constants_for_vertical_space():
    assert SCREEN_H >= 700
