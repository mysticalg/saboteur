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
