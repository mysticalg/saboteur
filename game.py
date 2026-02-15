"""Saboteur Tribute with pixel-art sprites and validated playable layout."""

from __future__ import annotations

import math
import random
import sys
from dataclasses import dataclass

import pygame

from core import JUMP_VELOCITY, RUN_SPEED, Actor, Bomb, GameRules, PlayerState, Rect, WorldPhysics
from level_data import FLOOR_H, SCREEN_H, SCREEN_W, WORLD_W, build_level

SKY = (12, 16, 30)
NEAR_BG = (24, 34, 58)
MID_BG = (36, 52, 82)
PLATFORM_TOP = (115, 123, 150)
PLATFORM_SIDE = (72, 79, 104)
WHITE = (240, 240, 240)
YELLOW = (245, 220, 92)
RED = (214, 84, 102)
GREEN = (76, 206, 150)
BLUE = (90, 140, 235)
CYAN = (98, 225, 225)
ORANGE = (245, 160, 90)


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




class SpriteBank:
    def __init__(self) -> None:
        self.player = self._make_humanoid((226, 226, 236), (40, 42, 55), band=(200, 44, 44))
        self.guard = self._make_humanoid((228, 86, 100), (48, 26, 32), band=(70, 70, 70))
        self.ninja = self._make_humanoid((50, 50, 56), (20, 20, 24), band=(220, 210, 120))
        self.dog = self._make_dog((162, 122, 82), (78, 52, 34))
        self.terminal = self._make_terminal()
        self.shuriken = self._make_shuriken()

    def _make_humanoid(
        self, body: tuple[int, int, int], trim: tuple[int, int, int], band: tuple[int, int, int]
    ) -> pygame.Surface:
        surf = pygame.Surface((32, 64), pygame.SRCALPHA)
        pygame.draw.rect(surf, body, pygame.Rect(9, 2, 14, 14), border_radius=4)
        pygame.draw.rect(surf, body, pygame.Rect(6, 16, 20, 28), border_radius=5)
        pygame.draw.rect(surf, trim, pygame.Rect(8, 46, 7, 16), border_radius=3)
        pygame.draw.rect(surf, trim, pygame.Rect(17, 46, 7, 16), border_radius=3)
        pygame.draw.rect(surf, band, pygame.Rect(6, 27, 20, 4))
        pygame.draw.rect(surf, (14, 14, 14), pygame.Rect(12, 8, 2, 2))
        pygame.draw.rect(surf, (14, 14, 14), pygame.Rect(18, 8, 2, 2))
        return surf

    def _make_dog(self, coat: tuple[int, int, int], dark: tuple[int, int, int]) -> pygame.Surface:
        surf = pygame.Surface((42, 44), pygame.SRCALPHA)
        pygame.draw.rect(surf, coat, pygame.Rect(3, 14, 34, 18), border_radius=8)
        pygame.draw.rect(surf, coat, pygame.Rect(28, 8, 12, 10), border_radius=4)
        pygame.draw.polygon(surf, dark, [(30, 8), (33, 3), (35, 9)])
        pygame.draw.rect(surf, dark, pygame.Rect(8, 30, 6, 12), border_radius=2)
        pygame.draw.rect(surf, dark, pygame.Rect(23, 30, 6, 12), border_radius=2)
        return surf

    def _make_terminal(self) -> pygame.Surface:
        surf = pygame.Surface((34, 48), pygame.SRCALPHA)
        pygame.draw.rect(surf, (56, 72, 96), pygame.Rect(3, 2, 28, 40), border_radius=4)
        pygame.draw.rect(surf, (86, 222, 158), pygame.Rect(7, 8, 20, 11), border_radius=2)
        pygame.draw.rect(surf, (26, 28, 36), pygame.Rect(8, 24, 18, 14), border_radius=2)
        return surf

    def _make_shuriken(self) -> pygame.Surface:
        surf = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.polygon(surf, (230, 230, 232), [(6, 0), (8, 6), (6, 12), (4, 6)])
        pygame.draw.polygon(surf, (190, 190, 194), [(0, 6), (6, 4), (12, 6), (6, 8)])
        pygame.draw.circle(surf, (60, 60, 70), (6, 6), 2)
        return surf


class SaboteurReplica:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Saboteur Replica - Pixel Edition")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 21)
        self.big = pygame.font.SysFont("consolas", 44, bold=True)

        self.sprites = SpriteBank()
        self.solids = build_level()
        self.physics = WorldPhysics(self.solids)

        self.player = PlayerState(Actor(Rect(88, SCREEN_H - FLOOR_H - 64, 32, 64)))
        self.player.health = 6
        self.player.shots = 16
        self.facing = 1
        self.attack_cd = 0.0
        self.attack: AttackWindow | None = None

        self.bomb = Bomb(seconds_left=260)
        self.rules = GameRules(self.bomb)

        self.pickups = [
            Pickup("time_bomb", Rect(360, 568, 22, 22), RED),
            Pickup("keycard", Rect(1080, 508, 22, 22), BLUE),
            Pickup("floppy_disk", Rect(1590, 448, 22, 22), CYAN),
            Pickup("secret_scroll", Rect(2620, 328, 22, 22), YELLOW),
            Pickup("gold_idol", Rect(3410, 208, 22, 22), ORANGE),
        ]
        self.terminal = Rect(2900, 252, 34, 48)
        self.exit_pad = Rect(3920, 130, 140, 26)

        self.enemies: list[Enemy] = [
            Enemy(Actor(Rect(760, 540 - 56, 30, 56)), "guard", 720, 1080, 104, hp=2),
            Enemy(Actor(Rect(1260, 480 - 56, 30, 56)), "ninja", 1220, 1600, 132, hp=3),
            Enemy(Actor(Rect(1770, 420 - 56, 30, 56)), "ninja", 1740, 2140, 144, hp=3),
            Enemy(Actor(Rect(2280, 360 - 56, 30, 56)), "guard", 2260, 2640, 112, hp=2),
            Enemy(Actor(Rect(3270, 240 - 56, 30, 56)), "ninja", 3260, 3640, 152, hp=3),
            Enemy(Actor(Rect(3500, 240 - 44, 42, 44)), "dog", 3380, 3780, 162, hp=2),
        ]

        self.projectiles: list[Projectile] = []
        self.camera_x = 0.0
        self.failed = False
        self.won = False

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
        self.projectiles.append(Projectile(Rect(p.x + p.w / 2, p.y + 24, 12, 12), 700 * self.facing, 1.1, "player"))
        self.player.shots -= 1

    def _start_melee(self, style: str) -> None:
        if self.attack_cd > 0:
            return
        p = self.player.actor.rect
        width, height, ttl, dmg = 40, 24, 0.18, 1
        if style == "kick":
            width, height, ttl, dmg = 54, 24, 0.20, 2
        if style == "flying_kick":
            width, height, ttl, dmg = 68, 28, 0.24, 2
            if self.player.actor.on_ground:
                self.player.actor.vy = -350
        hit_x = p.right if self.facing > 0 else p.left - width
        self.attack = AttackWindow(Rect(hit_x, p.y + 20, width, height), ttl, dmg)
        self.attack_cd = 0.3

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
        self._enemy_logic()
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
        self.attack.rect.y = p.y + 20
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
            if p.ttl <= 0 or any(p.rect.intersects(s) for s in self.solids):
                continue
            if p.source == "player":
                if any(self._hit_enemy(e, p) for e in self.enemies):
                    continue
            elif p.rect.intersects(self.player.actor.rect):
                self.player.health = max(0, self.player.health - 1)
                continue
            alive.append(p)
        self.projectiles = alive

    def _hit_enemy(self, e: Enemy, p: Projectile) -> bool:
        if e.alive and p.rect.intersects(e.actor.rect):
            e.hp -= 1
            if e.hp <= 0:
                e.alive = False
            return True
        return False

    def _enemy_logic(self) -> None:
        p = self.player.actor.rect
        for e in self.enemies:
            if not e.alive:
                continue
            if p.intersects(e.actor.rect):
                self.player.health = max(0, self.player.health - 1)
                self.player.actor.rect.x = max(40, self.player.actor.rect.x - 70)
            dist = abs((e.actor.rect.x + e.actor.rect.w / 2) - (p.x + p.w / 2))
            same_level = abs(e.actor.rect.y - p.y) < 48
            if e.kind == "ninja" and dist < 280 and same_level and e.attack_cd <= 0:
                sign = -1 if p.x < e.actor.rect.x else 1
                self.projectiles.append(
                    Projectile(Rect(e.actor.rect.x + e.actor.rect.w / 2, e.actor.rect.y + 18, 12, 12), 560 * sign, 1.1, "enemy")
                )
                e.attack_cd = 1.4

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

    def _draw_sprite(self, rect: Rect, sprite: pygame.Surface, flip: bool = False) -> None:
        image = pygame.transform.flip(sprite, flip, False) if flip else sprite
        self.screen.blit(image, (rect.x - self.camera_x, rect.y))

    def _draw_world(self) -> None:
        self.screen.fill(SKY)
        for x in range(0, SCREEN_W, 120):
            h = 120 + int(30 * math.sin((x + self.camera_x * 0.2) * 0.02))
            pygame.draw.rect(self.screen, MID_BG, pygame.Rect(x, SCREEN_H - FLOOR_H - h, 90, h))
        for x in range(0, SCREEN_W, 90):
            h = 70 + int(20 * math.sin((x + self.camera_x * 0.4) * 0.04))
            pygame.draw.rect(self.screen, NEAR_BG, pygame.Rect(x, SCREEN_H - FLOOR_H - h, 60, h))

        for s in self.solids:
            sx = s.x - self.camera_x
            if sx > SCREEN_W or sx + s.w < -4:
                continue
            pygame.draw.rect(self.screen, PLATFORM_SIDE, pygame.Rect(sx, s.y, s.w, s.h), border_radius=2)
            pygame.draw.rect(self.screen, PLATFORM_TOP, pygame.Rect(sx, s.y, s.w, 4), border_radius=2)

    def _draw(self) -> None:
        self._draw_world()

        for item in self.pickups:
            if not item.taken:
                pygame.draw.circle(self.screen, item.color, (int(item.rect.x - self.camera_x + 11), int(item.rect.y + 11)), 11)
                pygame.draw.circle(self.screen, WHITE, (int(item.rect.x - self.camera_x + 11), int(item.rect.y + 11)), 4)

        self._draw_sprite(self.terminal, self.sprites.terminal)
        pygame.draw.rect(
            self.screen,
            ORANGE,
            pygame.Rect(self.exit_pad.x - self.camera_x, self.exit_pad.y, self.exit_pad.w, self.exit_pad.h),
            border_radius=4,
        )
        self.screen.blit(self.font.render("EXTRACT", True, (22, 22, 24)), (self.exit_pad.x - self.camera_x + 26, self.exit_pad.y + 2))

        for e in self.enemies:
            if not e.alive:
                continue
            if e.kind == "guard":
                self._draw_sprite(e.actor.rect, self.sprites.guard, e.speed < 0)
            elif e.kind == "ninja":
                self._draw_sprite(e.actor.rect, self.sprites.ninja, e.speed < 0)
            else:
                self._draw_sprite(e.actor.rect, self.sprites.dog, e.speed < 0)

        for p in self.projectiles:
            self._draw_sprite(p.rect, self.sprites.shuriken)

        if self.attack:
            pygame.draw.rect(
                self.screen,
                (180, 255, 180),
                pygame.Rect(self.attack.rect.x - self.camera_x, self.attack.rect.y, self.attack.rect.w, self.attack.rect.h),
                width=2,
                border_radius=4,
            )

        self._draw_sprite(self.player.actor.rect, self.sprites.player, self.facing < 0)

        zone = min(7, int((self.player.actor.rect.x / WORLD_W) * 7) + 1)
        hud = (
            f"ZONE:{zone}/7 HP:{self.player.health} SHURIKEN:{self.player.shots} "
            f"BOMB:{'YES' if self.player.has_bomb else 'NO'} CODES:{'YES' if self.player.has_codes else 'NO'} "
            f"ITEMS:{sum(1 for p in self.pickups if p.taken)}/{len(self.pickups)} "
            f"TIMER:{'DEFUSED' if self.bomb.defused else f'{self.bomb.seconds_left:05.1f}s'}"
        )
        self.screen.blit(self.font.render(hud, True, WHITE), (14, 12))
        self.screen.blit(
            self.font.render("Move:A/D Jump:Space Shuriken:Z Punch:X Kick:C FlyingKick:V Interact:E", True, (200, 210, 230)),
            (14, 38),
        )

        if self.failed:
            t = self.big.render("MISSION FAILED - R TO RETRY", True, RED)
            self.screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2, SCREEN_H // 2 - 24))
        if self.won:
            t = self.big.render("MISSION COMPLETE - R TO REPLAY", True, GREEN)
            self.screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2, SCREEN_H // 2 - 24))

        pygame.display.flip()


if __name__ == "__main__":
    SaboteurReplica().run()
