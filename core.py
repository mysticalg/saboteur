"""Core game simulation for a Saboteur-inspired platform game."""

from __future__ import annotations

from dataclasses import dataclass


GRAVITY = 1800.0
RUN_SPEED = 230.0
JUMP_VELOCITY = -620.0
PLAYER_MAX_HEALTH = 5


@dataclass
class Rect:
    x: float
    y: float
    w: float
    h: float

    @property
    def left(self) -> float:
        return self.x

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def top(self) -> float:
        return self.y

    @property
    def bottom(self) -> float:
        return self.y + self.h

    def intersects(self, other: "Rect") -> bool:
        return not (
            self.right <= other.left
            or self.left >= other.right
            or self.bottom <= other.top
            or self.top >= other.bottom
        )


@dataclass
class Actor:
    rect: Rect
    vx: float = 0.0
    vy: float = 0.0
    on_ground: bool = False


@dataclass
class Bomb:
    seconds_left: float = 120.0
    armed: bool = False
    defused: bool = False

    def tick(self, dt: float) -> None:
        if self.armed and not self.defused:
            self.seconds_left = max(0.0, self.seconds_left - dt)


@dataclass
class PlayerState:
    actor: Actor
    health: int = PLAYER_MAX_HEALTH
    has_bomb: bool = False
    has_codes: bool = False
    shots: int = 8


class WorldPhysics:
    """Collision and movement helpers usable in tests and runtime."""

    def __init__(self, solids: list[Rect]):
        self.solids = solids

    def move_actor(self, actor: Actor, dt: float) -> None:
        actor.vy += GRAVITY * dt
        actor.rect.x += actor.vx * dt
        for wall in self.solids:
            if actor.rect.intersects(wall):
                if actor.vx > 0:
                    actor.rect.x = wall.left - actor.rect.w
                elif actor.vx < 0:
                    actor.rect.x = wall.right
                actor.vx = 0

        actor.rect.y += actor.vy * dt
        actor.on_ground = False
        for wall in self.solids:
            if actor.rect.intersects(wall):
                if actor.vy > 0:
                    actor.rect.y = wall.top - actor.rect.h
                    actor.on_ground = True
                elif actor.vy < 0:
                    actor.rect.y = wall.bottom
                actor.vy = 0


class GameRules:
    def __init__(self, bomb: Bomb):
        self.bomb = bomb

    def player_collects_bomb(self, state: PlayerState) -> None:
        state.has_bomb = True
        self.bomb.armed = True

    def player_collects_codes(self, state: PlayerState) -> None:
        state.has_codes = True

    def can_escape(self, state: PlayerState) -> bool:
        return state.has_bomb and state.has_codes and self.bomb.defused

    def defuse_bomb(self) -> None:
        if self.bomb.armed and self.bomb.seconds_left > 0:
            self.bomb.defused = True

    def bomb_exploded(self) -> bool:
        return self.bomb.armed and not self.bomb.defused and self.bomb.seconds_left <= 0
