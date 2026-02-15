"""Saboteur Tribute: a feature-rich side-scrolling ninja action game in pygame.

This game is a respectful recreation inspired by ZX Spectrum Saboteur mechanics:
- multi-zone compound layout
- stealth/action enemies (ninjas + guards + dogs)
- collectible mission items
- melee fighting moves + thrown shuriken
- timer-driven extraction objective
"""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass

import pygame

from core import JUMP_VELOCITY, RUN_SPEED, Actor, Bomb, GameRules, PlayerState, Rect, WorldPhysics

SCREEN_W, SCREEN_H = 1200, 720
WORLD_W = 4200
FLOOR_H = 44

BG = (8, 10, 20)
PLATFORM = (56, 66, 90)
WHITE = (236, 236, 236)
RED = (210, 70, 90)
GREEN = (60, 205, 150)
YELLOW = (245, 220, 80)
BLUE = (80, 140, 230)
ORANGE = (245, 155, 85)
CYAN = (100, 220, 220)


@dataclass
class Enemy:
    actor: Actor
    kind: str
    left: float
    right: float
    speed: float
    hp: int = 2
    alive: bool = True
    attack_cd: float = 0.0

    def update(self, dt: float, physics: WorldPhysics) -> None:
        if not self.alive:
            return
        self.attack_cd = max(0.0, self.attack_cd - dt)
        self.actor.vx = self.speed
        physics.move_actor(self.actor, dt)
        if self.actor.rect.x <= self.left:
            self.actor.rect.x = self.left
            self.speed = abs(self.speed)
        elif self.actor.rect.x >= self.right:
            self.actor.rect.x = self.right
            self.speed = -abs(self.speed)


@dataclass
class Projectile:
    rect: Rect
    vx: float
    ttl: float
    source: str


@dataclass
class AttackWindow:
    rect: Rect
    ttl: float
    damage: int


@dataclass
class Pickup:
    name: str
    rect: Rect
    color: tuple[int, int, int]
    taken: bool = False


class SaboteurReplica:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Saboteur Replica - Python")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 22)
        self.big = pygame.font.SysFont("consolas", 44, bold=True)

        self.solids = self._build_level()
        self.physics = WorldPhysics(self.solids)

        self.player = PlayerState(Actor(Rect(90, SCREEN_H - FLOOR_H - 64, 32, 64)))
        self.player.health = 6
        self.player.shots = 12
        self.facing = 1
        self.attack_cd = 0.0
        self.attack: AttackWindow | None = None

        self.bomb = Bomb(seconds_left=240)
        self.rules = GameRules(self.bomb)

        self.pickups = [
            Pickup("time_bomb", Rect(340, 140, 22, 22), RED),
            Pickup("keycard", Rect(980, 562, 22, 22), BLUE),
            Pickup("floppy_disk", Rect(1740, 362, 22, 22), CYAN),
            Pickup("secret_scroll", Rect(2480, 252, 22, 22), YELLOW),
            Pickup("gold_idol", Rect(3340, 472, 22, 22), ORANGE),
        ]
        self.terminal = Rect(2860, 472, 34, 48)
        self.exit_pad = Rect(3960, 78, 120, 24)

        self.enemies: list[Enemy] = [
            Enemy(Actor(Rect(620, SCREEN_H - FLOOR_H - 56, 30, 56)), "guard", 540, 900, 110, hp=2),
            Enemy(Actor(Rect(1210, 586 - 56, 30, 56)), "ninja", 1160, 1540, 140, hp=3),
            Enemy(Actor(Rect(1640, 386 - 56, 30, 56)), "ninja", 1600, 2120, 170, hp=3),
            Enemy(Actor(Rect(2400, 276 - 56, 30, 56)), "guard", 2280, 2690, 120, hp=2),
            Enemy(Actor(Rect(3050, 496 - 56, 30, 56)), "ninja", 2920, 3420, 150, hp=3),
            Enemy(Actor(Rect(3500, SCREEN_H - FLOOR_H - 44, 42, 44)), "dog", 3420, 3890, 170, hp=2),
        ]

        self.projectiles: list[Projectile] = []
        self.camera_x = 0.0
        self.failed = False
        self.won = False

    def _build_level(self) -> list[Rect]:
        return [
            Rect(0, SCREEN_H - FLOOR_H, WORLD_W, FLOOR_H),
            Rect(180, 610, 460, 18),
            Rect(760, 610, 540, 18),
            Rect(1420, 610, 510, 18),
            Rect(2050, 610, 520, 18),
            Rect(2710, 610, 520, 18),
            Rect(3380, 610, 560, 18),
            Rect(220, 410, 460, 18),
            Rect(860, 410, 560, 18),
            Rect(1520, 410, 560, 18),
            Rect(2220, 410, 500, 18),
            Rect(2860, 520, 420, 18),
            Rect(300, 300, 360, 18),
            Rect(1540, 300, 300, 18),
            Rect(2360, 300, 300, 18),
            Rect(3820, 102, 300, 18),
            Rect(710, 300, 24, 310),
            Rect(1360, 300, 24, 310),
            Rect(2160, 300, 24, 310),
            Rect(2800, 300, 24, 310),
            Rect(3340, 300, 24, 310),
        ]

    def run(self) -> None:
        while True:
            dt = self.clock.tick(60) / 1000
            self._events()
            if not self.failed and not self.won:
                self._update(dt)
            self._draw()

    def _events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if event.type == pygame.KEYDOWN and (self.failed or self.won) and event.key == pygame.K_r:
                self.__init__()
            if event.type == pygame.KEYDOWN and not (self.failed or self.won):
                if event.key == pygame.K_SPACE and self.player.actor.on_ground:
                    self.player.actor.vy = JUMP_VELOCITY
                if event.key == pygame.K_z:
                    self._throw_shuriken()
                if event.key == pygame.K_x:
                    self._start_melee("punch")
                if event.key == pygame.K_c:
                    self._start_melee("kick")
                if event.key == pygame.K_v:
                    self._start_melee("flying_kick")
                if event.key == pygame.K_e and self.player.actor.rect.intersects(self.terminal):
                    self.rules.defuse_bomb()

    def _throw_shuriken(self) -> None:
        if self.player.shots <= 0:
            return
        p = self.player.actor.rect
        self.projectiles.append(Projectile(Rect(p.x + p.w / 2, p.y + 24, 10, 6), 680 * self.facing, 1.1, "player"))
        self.player.shots -= 1

    def _start_melee(self, style: str) -> None:
        if self.attack_cd > 0:
            return
        p = self.player.actor.rect
        width, height, ttl, dmg, offset_y = 42, 24, 0.18, 1, 18
        if style == "kick":
            width, height, ttl, dmg = 58, 24, 0.2, 2
        if style == "flying_kick":
            width, height, ttl, dmg, offset_y = 70, 28, 0.24, 2, 30
            if self.player.actor.on_ground:
                self.player.actor.vy = -340
        hit_x = p.right if self.facing > 0 else p.left - width
        self.attack = AttackWindow(Rect(hit_x, p.y + offset_y, width, height), ttl, dmg)
        self.attack_cd = 0.28

    def _update(self, dt: float) -> None:
        self.attack_cd = max(0.0, self.attack_cd - dt)
        keys = pygame.key.get_pressed()
        self.player.actor.vx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player.actor.vx = -RUN_SPEED
            self.facing = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player.actor.vx = RUN_SPEED
            self.facing = 1

        self.physics.move_actor(self.player.actor, dt)

        for e in self.enemies:
            e.update(dt, self.physics)

        self._update_attack(dt)
        self._update_projectiles(dt)
        self._enemy_logic(dt)
        self._collect_items()
        self.bomb.tick(dt)
        self._check_end_state()

        target = self.player.actor.rect.x - SCREEN_W * 0.45
        self.camera_x = max(0, min(WORLD_W - SCREEN_W, target))

    def _update_attack(self, dt: float) -> None:
        if not self.attack:
            return
        self.attack.ttl -= dt
        p = self.player.actor.rect
        self.attack.rect.x = p.right if self.facing > 0 else p.left - self.attack.rect.w
        self.attack.rect.y = p.y + 18
        if self.attack.ttl <= 0:
            self.attack = None
            return

        for e in self.enemies:
            if e.alive and self.attack.rect.intersects(e.actor.rect):
                e.hp -= self.attack.damage
                if e.hp <= 0:
                    e.alive = False

    def _update_projectiles(self, dt: float) -> None:
        alive: list[Projectile] = []
        for p in self.projectiles:
            p.rect.x += p.vx * dt
            p.ttl -= dt
            if p.ttl <= 0:
                continue
            if any(p.rect.intersects(s) for s in self.solids):
                continue
            if p.source == "player":
                hit = False
                for e in self.enemies:
                    if e.alive and p.rect.intersects(e.actor.rect):
                        e.hp -= 1
                        if e.hp <= 0:
                            e.alive = False
                        hit = True
                        break
                if hit:
                    continue
            else:
                if p.rect.intersects(self.player.actor.rect):
                    self.player.health = max(0, self.player.health - 1)
                    continue
            alive.append(p)
        self.projectiles = alive

    def _enemy_logic(self, dt: float) -> None:
        p = self.player.actor.rect
        for e in self.enemies:
            if not e.alive:
                continue
            if p.intersects(e.actor.rect):
                self.player.health = max(0, self.player.health - 1)
                self.player.actor.rect.x = max(40, self.player.actor.rect.x - 80)

            dist = abs((e.actor.rect.x + e.actor.rect.w / 2) - (p.x + p.w / 2))
            same_level = abs(e.actor.rect.y - p.y) < 44
            if e.kind == "ninja" and dist < 260 and same_level and e.attack_cd <= 0:
                dir_sign = -1 if p.x < e.actor.rect.x else 1
                self.projectiles.append(
                    Projectile(Rect(e.actor.rect.x + e.actor.rect.w / 2, e.actor.rect.y + 20, 10, 6), 520 * dir_sign, 1.0, "enemy")
                )
                e.attack_cd = 1.5

    def _collect_items(self) -> None:
        p = self.player.actor.rect
        for item in self.pickups:
            if not item.taken and p.intersects(item.rect):
                item.taken = True
                if item.name == "time_bomb":
                    self.rules.player_collects_bomb(self.player)
                elif item.name == "keycard":
                    self.rules.player_collects_codes(self.player)

    def _all_mission_items_collected(self) -> bool:
        return all(i.taken for i in self.pickups)

    def _check_end_state(self) -> None:
        if self.player.health <= 0 or self.rules.bomb_exploded():
            self.failed = True
            return
        if self._all_mission_items_collected() and self.player.actor.rect.intersects(self.terminal):
            self.rules.defuse_bomb()
        if self.rules.can_escape(self.player) and self._all_mission_items_collected() and self.player.actor.rect.intersects(self.exit_pad):
            self.won = True

    def _draw_rect(self, r: Rect, color: tuple[int, int, int]) -> None:
        pygame.draw.rect(self.screen, color, pygame.Rect(r.x - self.camera_x, r.y, r.w, r.h), border_radius=4)

    def _draw(self) -> None:
        self.screen.fill(BG)

        for s in self.solids:
            self._draw_rect(s, PLATFORM)

        for item in self.pickups:
            if not item.taken:
                self._draw_rect(item.rect, item.color)

        self._draw_rect(self.terminal, GREEN if self.bomb.defused else YELLOW)
        self._draw_rect(self.exit_pad, ORANGE)

        for e in self.enemies:
            if e.alive:
                color = RED if e.kind in {"guard", "ninja"} else (170, 130, 85)
                self._draw_rect(e.actor.rect, color)

        for p in self.projectiles:
            self._draw_rect(p.rect, CYAN if p.source == "player" else YELLOW)

        if self.attack:
            self._draw_rect(self.attack.rect, (180, 255, 180))

        self._draw_rect(self.player.actor.rect, WHITE)

        zone = int((self.player.actor.rect.x / WORLD_W) * 7) + 1
        hud = (
            f"ZONE:{zone}/7 HP:{self.player.health} SHURIKEN:{self.player.shots} "
            f"BOMB:{'YES' if self.player.has_bomb else 'NO'} CODES:{'YES' if self.player.has_codes else 'NO'} "
            f"ITEMS:{sum(1 for p in self.pickups if p.taken)}/{len(self.pickups)} TIMER:{'DEFUSED' if self.bomb.defused else f'{self.bomb.seconds_left:05.1f}s'}"
        )
        self.screen.blit(self.font.render(hud, True, WHITE), (16, 14))

        controls = "Move:A/D Jump:Space Shuriken:Z Punch:X Kick:C FlyingKick:V Interact:E"
        self.screen.blit(self.font.render(controls, True, (180, 188, 210)), (16, 42))

        if self.failed:
            t = self.big.render("MISSION FAILED - R TO RETRY", True, RED)
            self.screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2, SCREEN_H // 2 - 24))
        if self.won:
            t = self.big.render("MISSION COMPLETE - R TO REPLAY", True, GREEN)
            self.screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2, SCREEN_H // 2 - 24))

        pygame.display.flip()


def main() -> None:
    SaboteurReplica().run()


if __name__ == "__main__":
    main()
