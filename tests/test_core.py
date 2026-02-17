from core import Actor, Bomb, GameRules, PlayerState, Rect, WorldPhysics


def test_actor_lands_on_platform():
    floor = Rect(0, 100, 300, 30)
    physics = WorldPhysics([floor])
    actor = Actor(Rect(10, 0, 20, 20), vy=0)
    for _ in range(20):
        physics.move_actor(actor, 0.05)
    assert actor.on_ground is True
    assert actor.rect.bottom == floor.top


def test_bomb_and_escape_rules():
    bomb = Bomb(seconds_left=10)
    rules = GameRules(bomb)
    player = PlayerState(Actor(Rect(0, 0, 10, 10)))

    rules.player_collects_bomb(player)
    rules.player_collects_codes(player)
    assert rules.can_escape(player) is False

    rules.defuse_bomb()
    assert rules.can_escape(player) is True


def test_bomb_explodes_when_timer_runs_out():
    bomb = Bomb(seconds_left=0.1, armed=True)
    rules = GameRules(bomb)
    bomb.tick(0.2)
    assert rules.bomb_exploded() is True


def test_drop_down_through_one_way_platform_when_requested():
    one_way = Rect(0, 100, 300, 10)
    physics = WorldPhysics([], one_way_platforms=[one_way])
    actor = Actor(Rect(40, 80, 20, 20), vy=0)

    # First, actor stands on one-way platform normally.
    for _ in range(5):
        physics.move_actor(actor, 0.05, drop_down=False)
    assert actor.on_ground is True

    # Then, with drop_down enabled, actor should pass through it.
    for _ in range(8):
        physics.move_actor(actor, 0.05, drop_down=True)
    assert actor.rect.top > one_way.top
    assert actor.on_ground is False


def test_ladder_climb_down_can_pass_through_one_way_platform():
    one_way = Rect(0, 100, 220, 10)
    ladder = Rect(80, 40, 34, 180)
    physics = WorldPhysics([], one_way_platforms=[one_way], ladders=[ladder])
    actor = Actor(Rect(86, 76, 20, 20), vy=0)

    # Actor is on ladder and pressing down; should descend through the one-way floor.
    for _ in range(8):
        physics.move_actor(actor, 0.05, drop_down=False, climb_dir=1)

    assert actor.rect.top > one_way.top
    assert actor.on_ground is False
