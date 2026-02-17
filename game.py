"""Saboteur Tribute with massive compound infiltration gameplay."""

from __future__ import annotations

import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pygame

from core import JUMP_VELOCITY, RUN_SPEED, Actor, Bomb, GameRules, PlayerState, Rect, WorldPhysics
from level_data import (
    FLOOR_H,
    SCREEN_H,
    SCREEN_W,
    WORLD_W,
    build_bushes,
    build_ladders,
    build_level,
    build_one_way_platforms,
    build_train_track,
    build_water_zones,
)

SKY = (10, 14, 28)
WATER = (20, 70, 126)
WATER_FOAM = (184, 224, 246)
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
PURPLE = (126, 96, 225)


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


@dataclass
class AreaLabel:
    name: str
    rect: Rect
    color: tuple[int, int, int]


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    color: tuple[int, int, int]
    size: int


class SpriteBank:
    def __init__(self) -> None:
        self.asset_dir = Path("assets/generated")
        self.player = self._load_or_make("player.png", (32, 64), lambda: self._make_humanoid((226, 226, 236), (40, 42, 55), band=(200, 44, 44)))
        self.guard = self._load_or_make("guard.png", (32, 64), lambda: self._make_humanoid((228, 86, 100), (48, 26, 32), band=(70, 70, 70)))
        self.ninja = self._load_or_make("ninja.png", (32, 64), lambda: self._make_humanoid((50, 50, 56), (20, 20, 24), band=(220, 210, 120)))
        self.dog = self._load_or_make("dog.png", (42, 44), lambda: self._make_dog((162, 122, 82), (78, 52, 34)))
        self.terminal = self._load_or_make("terminal.png", (34, 48), self._make_terminal)
        self.shuriken = self._load_or_make("shuriken.png", (12, 12), self._make_shuriken)
        self.ladder = self._load_or_make("ladder.png", (34, 68), self._make_ladder)
        self.train = self._load_or_make("train.png", (180, 64), self._make_train)
        self.dinghy = self._load_or_make("dinghy.png", (120, 48), self._make_dinghy)

    def _load_or_make(self, filename: str, size: tuple[int, int], fallback: Callable[[], pygame.Surface]) -> pygame.Surface:
        path = self.asset_dir / filename
        if path.exists():
            loaded = pygame.image.load(str(path)).convert_alpha()
            return pygame.transform.smoothscale(loaded, size)
        return fallback()

    def _make_humanoid(self, body: tuple[int, int, int], trim: tuple[int, int, int], band: tuple[int, int, int]) -> pygame.Surface:
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

    def _make_ladder(self) -> pygame.Surface:
        surf = pygame.Surface((34, 68), pygame.SRCALPHA)
        pygame.draw.rect(surf, (145, 122, 88), pygame.Rect(3, 0, 4, 68))
        pygame.draw.rect(surf, (145, 122, 88), pygame.Rect(27, 0, 4, 68))
        for y in range(6, 68, 10):
            pygame.draw.rect(surf, (178, 146, 98), pygame.Rect(4, y, 26, 3), border_radius=1)
        return surf

    def _make_train(self) -> pygame.Surface:
        surf = pygame.Surface((180, 64), pygame.SRCALPHA)
        pygame.draw.rect(surf, (68, 84, 112), pygame.Rect(0, 10, 180, 48), border_radius=8)
        pygame.draw.rect(surf, (100, 126, 170), pygame.Rect(8, 18, 40, 18), border_radius=3)
        pygame.draw.rect(surf, (100, 126, 170), pygame.Rect(56, 18, 40, 18), border_radius=3)
        pygame.draw.rect(surf, (100, 126, 170), pygame.Rect(104, 18, 40, 18), border_radius=3)
        pygame.draw.rect(surf, (225, 172, 74), pygame.Rect(150, 18, 20, 24), border_radius=2)
        pygame.draw.circle(surf, (26, 26, 30), (30, 58), 6)
        pygame.draw.circle(surf, (26, 26, 30), (148, 58), 6)
        return surf

    def _make_dinghy(self) -> pygame.Surface:
        surf = pygame.Surface((120, 48), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (58, 50, 46), pygame.Rect(6, 16, 108, 26))
        pygame.draw.ellipse(surf, (84, 74, 62), pygame.Rect(14, 22, 92, 16))
        pygame.draw.rect(surf, (126, 112, 96), pygame.Rect(58, 2, 4, 20))
        return surf


class SaboteurReplica:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Saboteur Replica - Massive Compound")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 20)
        self.big = pygame.font.SysFont("consolas", 42, bold=True)

        self.sprites = SpriteBank()
        self.solids = build_level()
        self.one_way = build_one_way_platforms()
        self.ladders = build_ladders()
        self.water = build_water_zones()
        self.bushes = build_bushes()
        self.physics = WorldPhysics(self.solids, one_way_platforms=self.one_way, ladders=self.ladders, water_zones=self.water)

        self.player = PlayerState(Actor(Rect(64, SCREEN_H - 140, 32, 64)))
        self.player.health = 8
        self.player.shots = 26
        self.facing = 1
        self.attack_cd = 0.0
        self.attack: AttackWindow | None = None
        self.hidden = False

        self.bomb = Bomb(seconds_left=3600)
        self.rules = GameRules(self.bomb)

        self.pickups = [
            Pickup("time_bomb", Rect(1520, 578, 22, 22), RED),
            Pickup("keycard", Rect(3220, 638, 22, 22), BLUE),
            Pickup("train_token", Rect(6190, 638, 22, 22), CYAN),
            Pickup("engineering_codes", Rect(8060, 338, 22, 22), YELLOW),
            Pickup("vault_relay", Rect(9460, 248, 22, 22), ORANGE),
        ]
        self.terminal = Rect(9120, 290, 34, 48)
        self.exit_pad = Rect(9630, 306, 140, 26)
        self.areas = [
            AreaLabel("SHORE ENTRY", Rect(120, 594, 320, 58), (76, 130, 180)),
            AreaLabel("MAINTENANCE STAIRS", Rect(2860, 586, 420, 58), (110, 130, 155)),
            AreaLabel("MONORAIL ACCESS", Rect(5200, 586, 420, 58), (136, 116, 170)),
            AreaLabel("SKYSCRAPER SECURITY", Rect(7220, 618, 540, 52), (136, 82, 92)),
            AreaLabel("STORAGE AREA", Rect(7920, 554, 560, 52), (124, 112, 90)),
            AreaLabel("SERVER ROOMS", Rect(7580, 426, 580, 52), (80, 132, 146)),
            AreaLabel("GUARD POSTS", Rect(8440, 362, 540, 52), (144, 96, 96)),
            AreaLabel("HEADQUARTERS", Rect(8200, 170, 600, 62), (150, 116, 78)),
        ]


        self.enemies: list[Enemy] = [
            Enemy(Actor(Rect(1320, 554, 30, 56)), "guard", 1200, 1760, 94, hp=2),
            Enemy(Actor(Rect(2040, 514, 30, 56)), "ninja", 1900, 2480, 116, hp=3),
            Enemy(Actor(Rect(3120, 624, 30, 56)), "guard", 3040, 4440, 120, hp=3),
            Enemy(Actor(Rect(4860, 414, 30, 56)), "ninja", 4680, 5440, 128, hp=3),
            Enemy(Actor(Rect(6520, 624, 42, 44)), "dog", 6460, 8040, 152, hp=2),
            Enemy(Actor(Rect(8460, 294, 30, 56)), "ninja", 8340, 9400, 146, hp=4),
            Enemy(Actor(Rect(7580, 562, 30, 56)), "guard", 7420, 8200, 118, hp=3),
            Enemy(Actor(Rect(8780, 498, 30, 56)), "guard", 8600, 9380, 130, hp=3),
            Enemy(Actor(Rect(8420, 178, 30, 56)), "ninja", 8260, 9000, 152, hp=4),
        ]

        self.projectiles: list[Projectile] = []
        self.particles: list[Particle] = []
        self.camera_x = 0.0
        self.failed = False
        self.won = False
        self.time_alive = 0.0

        track_y, self.train_min_x, self.train_max_x = build_train_track()
        self.train_rect = Rect(self.train_min_x, track_y - 58, 180, 64)
        self.train_speed = 150.0

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
                if event.key == pygame.K_SPACE and (self.player.actor.on_ground or self.player.actor.in_water or self.player.actor.on_ladder):
                    self.player.actor.vy = JUMP_VELOCITY * (0.58 if self.player.actor.in_water else 1.0)
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
            width, height, ttl, dmg = 54, 24, 0.2, 2
        if style == "flying_kick":
            width, height, ttl, dmg = 68, 28, 0.24, 3
            if self.player.actor.on_ground:
                self.player.actor.vy = -350
        hit_x = p.right if self.facing > 0 else p.left - width
        self.attack = AttackWindow(Rect(hit_x, p.y + 20, width, height), ttl, dmg)
        self.attack_cd = 0.3

    def _update(self, dt: float) -> None:
        self.time_alive += dt
        self.attack_cd = max(0.0, self.attack_cd - dt)
        keys = pygame.key.get_pressed()

        move_speed = RUN_SPEED * (0.58 if self.player.actor.in_water else 1.0)
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            move_speed *= 0.55
        self.player.actor.vx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player.actor.vx = -move_speed
            self.facing = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player.actor.vx = move_speed
            self.facing = 1

        climb_dir = 0
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            climb_dir = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            climb_dir = 1

        drop_down = (keys[pygame.K_DOWN] or keys[pygame.K_s]) and keys[pygame.K_SPACE]
        self.hidden = keys[pygame.K_DOWN] and any(self.player.actor.rect.intersects(b) for b in self.bushes)

        self.physics.move_actor(self.player.actor, dt, drop_down=drop_down, climb_dir=climb_dir)
        self._update_train(dt)
        for e in self.enemies:
            e.update(dt, self.physics)

        self._update_attack(dt)
        self._update_projectiles(dt)
        self._enemy_logic()
        self._collect_items()
        self._update_particles(dt)
        self.bomb.tick(dt)
        self._check_end_state()

        target = self.player.actor.rect.x - SCREEN_W * 0.45
        self.camera_x = max(0, min(WORLD_W - SCREEN_W, target))

    def _update_train(self, dt: float) -> None:
        self.train_rect.x += self.train_speed * dt
        if self.train_rect.x <= self.train_min_x:
            self.train_rect.x = self.train_min_x
            self.train_speed = abs(self.train_speed)
        if self.train_rect.x + self.train_rect.w >= self.train_max_x:
            self.train_rect.x = self.train_max_x - self.train_rect.w
            self.train_speed = -abs(self.train_speed)
        p = self.player.actor.rect
        standing_on_train = p.bottom <= self.train_rect.top + 12 and p.bottom >= self.train_rect.top - 10 and p.right > self.train_rect.left and p.left < self.train_rect.right
        if standing_on_train:
            p.x += self.train_speed * dt
            p.y = self.train_rect.top - p.h
            self.player.actor.on_ground = True

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
                self._emit_particles(e.actor.rect.x + e.actor.rect.w / 2, e.actor.rect.y + 24, RED, 6)
                if e.hp <= 0:
                    e.alive = False
                    self._emit_particles(e.actor.rect.x + e.actor.rect.w / 2, e.actor.rect.y + 24, ORANGE, 14)

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
                self._emit_particles(p.rect.x, p.rect.y, RED, 8)
                continue
            alive.append(p)
        self.projectiles = alive

    def _hit_enemy(self, e: Enemy, p: Projectile) -> bool:
        if e.alive and p.rect.intersects(e.actor.rect):
            e.hp -= 1
            self._emit_particles(e.actor.rect.x + e.actor.rect.w / 2, e.actor.rect.y + 24, RED, 5)
            if e.hp <= 0:
                e.alive = False
                self._emit_particles(e.actor.rect.x + e.actor.rect.w / 2, e.actor.rect.y + 24, ORANGE, 12)
            return True
        return False

    def _enemy_logic(self) -> None:
        p = self.player.actor.rect
        for e in self.enemies:
            if not e.alive:
                continue
            if p.intersects(e.actor.rect):
                self.player.health = max(0, self.player.health - 1)
                self._emit_particles(p.x + p.w / 2, p.y + 32, RED, 7)
                self.player.actor.rect.x = max(40, self.player.actor.rect.x - 70)
            dist = abs((e.actor.rect.x + e.actor.rect.w / 2) - (p.x + p.w / 2))
            same_level = abs(e.actor.rect.y - p.y) < 56
            sees_player = not self.hidden and dist < (320 if e.kind == "ninja" else 250)
            if sees_player and same_level and e.attack_cd <= 0 and e.kind in {"ninja", "guard"}:
                sign = -1 if p.x < e.actor.rect.x else 1
                self.projectiles.append(Projectile(Rect(e.actor.rect.x + e.actor.rect.w / 2, e.actor.rect.y + 18, 12, 12), 540 * sign, 1.1, "enemy"))
                e.attack_cd = 1.5

    def _collect_items(self) -> None:
        p = self.player.actor.rect
        for item in self.pickups:
            if not item.taken and p.intersects(item.rect):
                item.taken = True
                self._emit_particles(item.rect.x + 11, item.rect.y + 11, item.color, 14)
                if item.name == "time_bomb":
                    self.rules.player_collects_bomb(self.player)
                elif item.name in {"keycard", "engineering_codes"}:
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

    def _update_particles(self, dt: float) -> None:
        alive: list[Particle] = []
        for particle in self.particles:
            particle.life -= dt
            if particle.life <= 0:
                continue
            particle.x += particle.vx * dt
            particle.y += particle.vy * dt
            particle.vy += 420 * dt
            alive.append(particle)
        self.particles = alive

    def _emit_particles(self, x: float, y: float, color: tuple[int, int, int], amount: int) -> None:
        for _ in range(amount):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(80, 240)
            self.particles.append(Particle(x=x, y=y, vx=math.cos(angle) * speed, vy=math.sin(angle) * speed - 50, life=random.uniform(0.18, 0.5), color=color, size=random.randint(2, 4)))

    def _draw_sprite(self, rect: Rect, sprite: pygame.Surface, flip: bool = False) -> None:
        image = pygame.transform.flip(sprite, flip, False) if flip else sprite
        self.screen.blit(image, (rect.x - self.camera_x, rect.y))

    def _draw_world(self) -> None:
        for y in range(SCREEN_H):
            t = y / SCREEN_H
            col = (int(SKY[0] * (1 - t) + 6 * t), int(SKY[1] * (1 - t) + 10 * t), int(SKY[2] * (1 - t) + 18 * t))
            pygame.draw.line(self.screen, col, (0, y), (SCREEN_W, y))

        moon_x = int(SCREEN_W * 0.8 - (self.camera_x * 0.05) % (SCREEN_W + 140))
        pygame.draw.circle(self.screen, (230, 236, 255), (moon_x, 90), 36)

        for zone in self.water:
            sx = zone.x - self.camera_x
            pygame.draw.rect(self.screen, WATER, pygame.Rect(sx, zone.y, zone.w, zone.h))
            for i in range(0, int(zone.w), 38):
                wave = int(4 * math.sin(self.time_alive * 4 + i * 0.1))
                pygame.draw.line(self.screen, WATER_FOAM, (sx + i, zone.y + 10 + wave), (sx + i + 20, zone.y + 10 + wave), 2)

        for x in range(0, SCREEN_W, 120):
            h = 120 + int(30 * math.sin((x + self.camera_x * 0.2) * 0.02))
            pygame.draw.rect(self.screen, MID_BG, pygame.Rect(x, SCREEN_H - FLOOR_H - h, 90, h))

        for bush in self.bushes:
            sx = bush.x - self.camera_x
            pygame.draw.ellipse(self.screen, (42, 122, 72), pygame.Rect(sx, bush.y, bush.w, bush.h))

        for area in self.areas:
            sx = area.rect.x - self.camera_x
            if sx > SCREEN_W or sx + area.rect.w < -8:
                continue
            pygame.draw.rect(self.screen, area.color, pygame.Rect(sx, area.rect.y, area.rect.w, area.rect.h), border_radius=6)
            pygame.draw.rect(self.screen, (18, 22, 30), pygame.Rect(sx, area.rect.y, area.rect.w, area.rect.h), width=2, border_radius=6)
            label = self.font.render(area.name, True, (240, 242, 248))
            self.screen.blit(label, (sx + 12, area.rect.y + 16))

        # Elevator shafts and monorail supports inside the tower.
        for shaft_x in (7420, 8080, 8740, 9320):
            sx = shaft_x - self.camera_x
            pygame.draw.rect(self.screen, (48, 54, 70), pygame.Rect(sx, 92, 52, 586), border_radius=3)
            for y in range(116, 650, 64):
                pygame.draw.rect(self.screen, (104, 118, 146), pygame.Rect(sx + 6, y, 40, 20), border_radius=2)

        pygame.draw.rect(self.screen, (84, 96, 128), pygame.Rect(7240 - self.camera_x, 122, 2220, 8))
        for i in range(7240, 9460, 58):
            pygame.draw.rect(self.screen, (152, 166, 198), pygame.Rect(i - self.camera_x, 126, 34, 5), border_radius=1)

        for s in self.solids:
            sx = s.x - self.camera_x
            if sx > SCREEN_W or sx + s.w < -4:
                continue
            pygame.draw.rect(self.screen, PLATFORM_SIDE, pygame.Rect(sx, s.y, s.w, s.h), border_radius=2)
            pygame.draw.rect(self.screen, PLATFORM_TOP, pygame.Rect(sx, s.y, s.w, 4), border_radius=2)

        for p in self.one_way:
            sx = p.x - self.camera_x
            if sx > SCREEN_W or sx + p.w < -4:
                continue
            pygame.draw.rect(self.screen, (90, 100, 124), pygame.Rect(sx, p.y, p.w, p.h), border_radius=2)
            pygame.draw.line(self.screen, (180, 190, 210), (sx, p.y), (sx + p.w, p.y), 2)

        for ladder in self.ladders:
            for seg in range(int(ladder.h // 68) + 1):
                y = ladder.y + seg * 68
                self.screen.blit(self.sprites.ladder, (ladder.x - self.camera_x, y))

        self.screen.blit(self.sprites.train, (self.train_rect.x - self.camera_x, self.train_rect.y))
        pygame.draw.rect(self.screen, (60, 62, 70), pygame.Rect(self.train_min_x - self.camera_x, self.train_rect.y + 58, self.train_max_x - self.train_min_x, 6))

        self.screen.blit(self.sprites.dinghy, (24 - self.camera_x * 0.03, SCREEN_H - 120))

    def _draw_pickup(self, item: Pickup) -> None:
        cx = int(item.rect.x - self.camera_x + 11)
        cy = int(item.rect.y + 11)
        pulse = 1.0 + 0.15 * math.sin(self.time_alive * 6 + item.rect.x * 0.02)
        radius = int(10 * pulse)
        pygame.draw.circle(self.screen, (255, 255, 255), (cx, cy), radius + 2, width=1)
        pygame.draw.circle(self.screen, item.color, (cx, cy), radius)

    def _draw(self) -> None:
        self._draw_world()

        for item in self.pickups:
            if not item.taken:
                self._draw_pickup(item)

        self._draw_sprite(self.terminal, self.sprites.terminal)
        pygame.draw.rect(self.screen, ORANGE, pygame.Rect(self.exit_pad.x - self.camera_x, self.exit_pad.y, self.exit_pad.w, self.exit_pad.h), border_radius=4)
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

        for p in self.particles:
            pygame.draw.circle(self.screen, p.color, (int(p.x - self.camera_x), int(p.y)), p.size)

        if self.attack:
            pygame.draw.rect(self.screen, (180, 255, 180), pygame.Rect(self.attack.rect.x - self.camera_x, self.attack.rect.y, self.attack.rect.w, self.attack.rect.h), width=2, border_radius=4)

        self._draw_sprite(self.player.actor.rect, self.sprites.player, self.facing < 0)
        if self.hidden:
            self.screen.blit(self.font.render("HIDDEN", True, GREEN), (self.player.actor.rect.x - self.camera_x - 4, self.player.actor.rect.y - 22))

        hud = (
            f"ZONE:{min(12, int((self.player.actor.rect.x / WORLD_W) * 12) + 1)}/12 HP:{self.player.health} SHURIKEN:{self.player.shots} "
            f"BOMB:{'YES' if self.player.has_bomb else 'NO'} CODES:{'YES' if self.player.has_codes else 'NO'} "
            f"ITEMS:{sum(1 for p in self.pickups if p.taken)}/{len(self.pickups)} "
            f"TIMER:{'DEFUSED' if self.bomb.defused else f'{self.bomb.seconds_left:06.1f}s'}"
        )
        self.screen.blit(self.font.render(hud, True, WHITE), (14, 12))
        controls = "Move:A/D Jump:Space Drop:Down+Space Climb:W/S Crouch/Hide:Down Sprint:Shift Throw:Z Interact:E"
        self.screen.blit(self.font.render(controls, True, (200, 210, 230)), (14, 38))

        if self.failed:
            t = self.big.render("MISSION FAILED - R TO RETRY", True, RED)
            self.screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2, SCREEN_H // 2 - 24))
        if self.won:
            t = self.big.render("MISSION COMPLETE - R TO REPLAY", True, GREEN)
            self.screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2, SCREEN_H // 2 - 24))

        pygame.display.flip()


if __name__ == "__main__":
    SaboteurReplica().run()
