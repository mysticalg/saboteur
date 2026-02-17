"""Saboteur Tribute with massive compound infiltration gameplay."""

from __future__ import annotations

import base64
import json
import math
import os
import random
import sys
import urllib.request
import webbrowser
from urllib.error import HTTPError
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
    WORLD_H,
    WORLD_Y_OFFSET,
    build_bushes,
    build_ladders,
    build_level,
    build_one_way_platforms,
    build_train_track,
    build_water_zones,
)

SKY = (8, 10, 22)
WATER = (16, 62, 112)
WATER_FOAM = (170, 214, 238)
NEAR_BG = (20, 26, 42)
MID_BG = (28, 40, 64)
PLATFORM_TOP = (132, 138, 156)
PLATFORM_SIDE = (66, 72, 92)
WHITE = (240, 240, 240)
YELLOW = (245, 220, 92)
RED = (214, 84, 102)
GREEN = (76, 206, 150)
BLUE = (90, 140, 235)
CYAN = (98, 225, 225)
ORANGE = (245, 160, 90)
PURPLE = (126, 96, 225)
GOLD = (236, 198, 72)
OPENAI_IMAGE_MODEL = "gpt-image-1"
OPENAI_TOKEN_FILE = Path.home() / ".saboteur_openai_api_key"


ENEMY_XP = {
    "bat": 6,
    "rat": 7,
    "snake": 8,
    "dog": 8,
    "guard": 10,
    "henchman": 11,
    "thug": 12,
    "ninja": 13,
    "assassin": 16,
    "heavy": 18,
    "drone": 18,
    "robot": 20,
    "boss": 40,
}


def xp_to_next_level(level: int) -> int:
    return 70 + (level - 1) * 35


def weapon_profile(name: str) -> dict[str, float]:
    profiles: dict[str, dict[str, float]] = {
        "fists": {"melee": 1.0, "ranged": 0.0, "energy": 4.0, "ammo": 0.0, "fire_cd": 0.0},
        "bat": {"melee": 1.4, "ranged": 0.0, "energy": 5.0, "ammo": 0.0, "fire_cd": 0.0},
        "stick": {"melee": 1.2, "ranged": 0.0, "energy": 4.5, "ammo": 0.0, "fire_cd": 0.0},
        "brick": {"melee": 1.3, "ranged": 0.0, "energy": 5.0, "ammo": 0.0, "fire_cd": 0.0},
        "pole": {"melee": 1.35, "ranged": 0.0, "energy": 5.5, "ammo": 0.0, "fire_cd": 0.0},
        "nunchukas": {"melee": 1.6, "ranged": 0.0, "energy": 6.5, "ammo": 0.0, "fire_cd": 0.0},
        "sais": {"melee": 1.55, "ranged": 0.0, "energy": 6.0, "ammo": 0.0, "fire_cd": 0.0},
        "sword": {"melee": 1.85, "ranged": 0.0, "energy": 7.0, "ammo": 0.0, "fire_cd": 0.0},
        "gun": {"melee": 1.0, "ranged": 1.0, "energy": 2.0, "ammo": 30.0, "fire_cd": 0.34},
        "machine_gun": {"melee": 0.9, "ranged": 0.8, "energy": 2.8, "ammo": 70.0, "fire_cd": 0.13},
        "silencer": {"melee": 1.0, "ranged": 1.2, "energy": 1.8, "ammo": 28.0, "fire_cd": 0.28},
    }
    return profiles.get(name, profiles["fists"])


def meditate_recovery_per_sec(level: int) -> float:
    return 16.0 + min(14.0, (level - 1) * 1.4)


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
    max_hp: int = 2
    boss: bool = False

    def __post_init__(self) -> None:
        if self.max_hp <= 0:
            self.max_hp = self.hp

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
class Drop:
    kind: str
    rect: Rect
    ttl: float = 16.0


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    color: tuple[int, int, int]
    size: int


@dataclass
class ElevatorCar:
    rect: Rect
    y_min: float
    y_max: float
    speed: float


@dataclass
class GrappleLine:
    start: tuple[float, float]
    end: tuple[float, float]
    ttl: float


class SpriteBank:
    GENERATED_FILES = [
        "player.png",
        "guard.png",
        "ninja.png",
        "dog.png",
        "terminal.png",
        "shuriken.png",
        "ladder.png",
        "train.png",
        "dinghy.png",
    ]

    def __init__(self, use_generated_assets: bool = True) -> None:
        self.asset_dir = Path("assets/generated")
        self.use_generated_assets = use_generated_assets
        self.player = self._load_or_make("player.png", (32, 64), lambda: self._make_humanoid((226, 226, 236), (40, 42, 55), band=(200, 44, 44)))
        self.guard = self._load_or_make("guard.png", (32, 64), lambda: self._make_humanoid((228, 86, 100), (48, 26, 32), band=(70, 70, 70)))
        self.ninja = self._load_or_make("ninja.png", (32, 64), lambda: self._make_humanoid((50, 50, 56), (20, 20, 24), band=(220, 210, 120)))
        self.dog = self._load_or_make("dog.png", (42, 44), lambda: self._make_dog((162, 122, 82), (78, 52, 34)))
        self.terminal = self._load_or_make("terminal.png", (34, 48), self._make_terminal)
        self.shuriken = self._load_or_make("shuriken.png", (12, 12), self._make_shuriken)
        self.ladder = self._load_or_make("ladder.png", (34, 68), self._make_ladder)
        self.train = self._load_or_make("train.png", (180, 64), self._make_train)
        self.dinghy = self._load_or_make("dinghy.png", (120, 48), self._make_dinghy)

    @classmethod
    def generated_assets_ready(cls, asset_dir: Path | None = None) -> bool:
        directory = asset_dir or Path("assets/generated")
        return all((directory / name).exists() for name in cls.GENERATED_FILES)

    def _load_or_make(self, filename: str, size: tuple[int, int], fallback: Callable[[], pygame.Surface]) -> pygame.Surface:
        path = self.asset_dir / filename
        if self.use_generated_assets and path.exists():
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
        try:
            pygame.scrap.init()
        except pygame.error:
            pass
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Saboteur Replica - Massive Compound")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 20)
        self.big = pygame.font.SysFont("consolas", 42, bold=True)
        self.medium = pygame.font.SysFont("consolas", 30, bold=True)

        self.state = "splash"
        self.use_openai_sprites = True
        self.generated_assets_present = SpriteBank.generated_assets_ready()
        self.sprites = SpriteBank(use_generated_assets=self.use_openai_sprites)
        self.openai_api_key = self._load_api_key()
        self.options_status = ""
        self.options_input_mode = False
        self.options_reveal_key = False
        self.solids = build_level()
        self.one_way = build_one_way_platforms()
        self.ladders = build_ladders()
        self.water = build_water_zones()
        self.bushes = build_bushes()
        self.physics = WorldPhysics(self.solids, one_way_platforms=self.one_way, ladders=self.ladders, water_zones=self.water)

        self.player = PlayerState(Actor(Rect(64, SCREEN_H - 140, 32, 64)))
        self.player.actor.rect.y += WORLD_Y_OFFSET
        self.player.health = 8
        self.player.shots = 26
        self.facing = 1
        self.attack_cd = 0.0
        self.attack: AttackWindow | None = None
        self.hidden = False
        self.gold = 0
        self.invisibility_timer = 0.0
        self.invincibility_timer = 0.0
        self.speed_timer = 0.0
        self.level = 1
        self.xp = 0
        self.next_level_xp = xp_to_next_level(self.level)
        self.grapple_bonus = 0.0
        self.grapple_line: GrappleLine | None = None
        self.energy = 100.0
        self.max_energy = 100.0
        self.meditating = False
        self.weapons_owned: set[str] = {"fists", "bat"}
        self.current_weapon = "bat"
        self.weapon_ammo: dict[str, int] = {"gun": 0, "machine_gun": 0, "silencer": 0}
        self.ranged_cd = 0.0

        self.bomb = Bomb(seconds_left=3600)
        self.rules = GameRules(self.bomb)

        self.pickups = [
            Pickup("time_bomb", Rect(1520, 578 + WORLD_Y_OFFSET, 22, 22), RED),
            Pickup("keycard", Rect(3220, 638 + WORLD_Y_OFFSET, 22, 22), BLUE),
            Pickup("train_token", Rect(6190, 638 + WORLD_Y_OFFSET, 22, 22), CYAN),
            Pickup("engineering_codes", Rect(10320, 210 + WORLD_Y_OFFSET, 22, 22), YELLOW),
            Pickup("vault_relay", Rect(14120, -84 + WORLD_Y_OFFSET, 22, 22), ORANGE),
            Pickup("silo_overrides", Rect(6200, 2460, 22, 22), RED),
        ]
        self.weapon_pickups = [
            Pickup("stick", Rect(1860, 638 + WORLD_Y_OFFSET, 22, 22), (170, 150, 112)),
            Pickup("brick", Rect(2920, 638 + WORLD_Y_OFFSET, 22, 22), (188, 92, 86)),
            Pickup("pole", Rect(4180, 638 + WORLD_Y_OFFSET, 22, 22), (186, 166, 104)),
            Pickup("nunchukas", Rect(7440, 530 + WORLD_Y_OFFSET, 22, 22), (192, 166, 120)),
            Pickup("sais", Rect(9580, 466 + WORLD_Y_OFFSET, 22, 22), (170, 180, 210)),
            Pickup("sword", Rect(13140, 102 + WORLD_Y_OFFSET, 22, 22), (208, 214, 226)),
            Pickup("gun", Rect(5620, 2440, 22, 22), (146, 156, 172)),
            Pickup("machine_gun", Rect(10940, 2060, 22, 22), (132, 144, 168)),
            Pickup("silencer", Rect(15240, -250, 22, 22), (112, 136, 166)),
        ]
        self.terminal = Rect(14820, -128 + WORLD_Y_OFFSET, 34, 48)
        self.exit_pad = Rect(15480, -96 + WORLD_Y_OFFSET, 170, 26)
        self.silo_console = Rect(6240, 2422, 46, 56)
        self.silo_sabotaged = False
        self.helicopter_pad = Rect(15120, -236, 980, 16)
        self.helicopter = Rect(15740, -296, 220, 76)
        self.areas = [
            AreaLabel("SHORE ENTRY", Rect(120, 594 + WORLD_Y_OFFSET, 320, 58), (76, 130, 180)),
            AreaLabel("MAINTENANCE STAIRS", Rect(2860, 586 + WORLD_Y_OFFSET, 420, 58), (110, 130, 155)),
            AreaLabel("MONORAIL ACCESS", Rect(5200, 586 + WORLD_Y_OFFSET, 420, 58), (136, 116, 170)),
            AreaLabel("SKYSCRAPER SECURITY", Rect(7220, 618 + WORLD_Y_OFFSET, 580, 52), (136, 82, 92)),
            AreaLabel("STORAGE AREA", Rect(8960, 554 + WORLD_Y_OFFSET, 620, 52), (124, 112, 90)),
            AreaLabel("SERVER ROOMS", Rect(10420, 426 + WORLD_Y_OFFSET, 640, 52), (80, 132, 146)),
            AreaLabel("GUARD POSTS", Rect(11600, 330 + WORLD_Y_OFFSET, 640, 52), (144, 96, 96)),
            AreaLabel("HEADQUARTERS", Rect(13180, 94 + WORLD_Y_OFFSET, 820, 62), (150, 116, 78)),
            AreaLabel("TOWER CORE", Rect(9400, 220, 980, 52), (108, 102, 120)),
            AreaLabel("SKY TERRACES", Rect(12280, 42, 920, 48), (96, 136, 142)),
            AreaLabel("NUCLEAR SILO", Rect(5560, 2440, 760, 52), (152, 96, 72)),
            AreaLabel("HELIPAD", Rect(15180, -248, 520, 50), (124, 140, 166)),
        ]


        self.enemies: list[Enemy] = [
            Enemy(Actor(Rect(1320, 554 + WORLD_Y_OFFSET, 30, 56)), "guard", 1200, 1760, 94, hp=2, max_hp=2),
            Enemy(Actor(Rect(2040, 514 + WORLD_Y_OFFSET, 30, 56)), "ninja", 1900, 2480, 116, hp=3, max_hp=3),
            Enemy(Actor(Rect(3120, 624 + WORLD_Y_OFFSET, 30, 56)), "guard", 3040, 4440, 120, hp=3, max_hp=3),
            Enemy(Actor(Rect(4860, 414 + WORLD_Y_OFFSET, 30, 56)), "heavy", 4680, 5440, 92, hp=5, max_hp=5),
            Enemy(Actor(Rect(6520, 624 + WORLD_Y_OFFSET, 42, 44)), "dog", 6460, 8040, 152, hp=2, max_hp=2),
            Enemy(Actor(Rect(9460, 294 + WORLD_Y_OFFSET, 30, 56)), "ninja", 9220, 10400, 146, hp=4, max_hp=4),
            Enemy(Actor(Rect(10820, 562 + WORLD_Y_OFFSET, 30, 56)), "guard", 10440, 11380, 118, hp=3, max_hp=3),
            Enemy(Actor(Rect(12020, 498 + WORLD_Y_OFFSET, 30, 56)), "drone", 11600, 12640, 160, hp=2, max_hp=2),
            Enemy(Actor(Rect(13640, 96, 30, 56)), "boss", 13280, 14440, 126, hp=10, max_hp=10, boss=True),
            Enemy(Actor(Rect(14980, 32, 30, 56)), "boss", 14620, 15620, 134, hp=12, max_hp=12, boss=True),
            # Lower-cavern ecosystem + hostile underground garrison.
            Enemy(Actor(Rect(2120, 1808, 28, 40)), "bat", 1900, 3000, 170, hp=1, max_hp=1),
            Enemy(Actor(Rect(3660, 1808, 28, 40)), "bat", 3320, 4520, 176, hp=1, max_hp=1),
            Enemy(Actor(Rect(6160, 2068, 30, 44)), "rat", 5820, 6900, 148, hp=2, max_hp=2),
            Enemy(Actor(Rect(7920, 2068, 30, 44)), "rat", 7560, 8660, 152, hp=2, max_hp=2),
            Enemy(Actor(Rect(9800, 2328, 34, 40)), "snake", 9420, 10440, 132, hp=2, max_hp=2),
            Enemy(Actor(Rect(11820, 2328, 34, 40)), "snake", 11420, 12460, 138, hp=2, max_hp=2),
            Enemy(Actor(Rect(2960, 2322, 30, 56)), "henchman", 2520, 3480, 112, hp=3, max_hp=3),
            Enemy(Actor(Rect(5480, 2322, 30, 56)), "thug", 5040, 6060, 124, hp=4, max_hp=4),
            Enemy(Actor(Rect(7240, 2322, 30, 56)), "guard", 6840, 7820, 126, hp=3, max_hp=3),
            Enemy(Actor(Rect(8880, 2322, 30, 56)), "ninja", 8480, 9480, 144, hp=4, max_hp=4),
            Enemy(Actor(Rect(10620, 2062, 30, 56)), "assassin", 10120, 11180, 156, hp=5, max_hp=5),
            Enemy(Actor(Rect(12820, 2588, 32, 58)), "robot", 12320, 13500, 108, hp=6, max_hp=6),
            Enemy(Actor(Rect(14620, 2588, 32, 58)), "robot", 14120, 15380, 112, hp=6, max_hp=6),
        ]

        self.projectiles: list[Projectile] = []
        self.drops: list[Drop] = []
        self.particles: list[Particle] = []
        self.camera_x = 0.0
        self.camera_y = float(WORLD_Y_OFFSET)
        self.failed = False
        self.won = False
        self.time_alive = 0.0
        self.anim_time = 0.0
        self.drop_through_timer = 0.0

        track_y, self.train_min_x, self.train_max_x = build_train_track()
        self.train_rect = Rect(self.train_min_x, track_y - 58, 180, 64)
        self.train_speed = 150.0
        self.elevators = [
            ElevatorCar(Rect(7480, 610 + WORLD_Y_OFFSET, 52, 22), 150 + WORLD_Y_OFFSET, 650 + WORLD_Y_OFFSET, -96.0),
            ElevatorCar(Rect(9800, 610 + WORLD_Y_OFFSET, 52, 22), 130 + WORLD_Y_OFFSET, 650 + WORLD_Y_OFFSET, -102.0),
            ElevatorCar(Rect(12060, 610 + WORLD_Y_OFFSET, 52, 22), 30 + WORLD_Y_OFFSET, 650 + WORLD_Y_OFFSET, -108.0),
            ElevatorCar(Rect(15340, -218, 52, 22), -320, 620 + WORLD_Y_OFFSET, -116.0),
        ]

    def run(self) -> None:
        while True:
            dt = self.clock.tick(60) / 1000
            self._events()
            if self.state == "playing" and not self.failed and not self.won:
                self._update(dt)
            self._draw()

    def _events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if event.type != pygame.KEYDOWN:
                continue

            if self.state == "splash":
                if event.key in {pygame.K_RETURN, pygame.K_SPACE}:
                    self.state = "playing"
                elif event.key == pygame.K_o:
                    self.state = "options"
                elif event.key in {pygame.K_ESCAPE, pygame.K_q}:
                    pygame.quit()
                    sys.exit(0)
                continue

            if self.state == "options":
                if self.options_input_mode:
                    ctrl_down = bool(event.mod & (pygame.KMOD_CTRL | pygame.KMOD_META))
                    if event.key == pygame.K_RETURN:
                        self._save_api_key(self.openai_api_key)
                        self.options_input_mode = False
                        self.options_status = "API key saved locally."
                    elif event.key == pygame.K_ESCAPE:
                        self.options_input_mode = False
                        self.options_reveal_key = False
                    elif event.key == pygame.K_BACKSPACE:
                        self.openai_api_key = self.openai_api_key[:-1]
                    elif event.key == pygame.K_v and ctrl_down:
                        pasted = self._read_clipboard_text()
                        if pasted:
                            self.openai_api_key += pasted.strip()
                            self.options_status = "Pasted API key text from clipboard."
                        else:
                            self.options_status = "Clipboard paste unavailable (try terminal/env var)."
                    elif event.key == pygame.K_TAB:
                        self.options_reveal_key = not self.options_reveal_key
                    else:
                        if event.unicode and event.unicode.isprintable():
                            self.openai_api_key += event.unicode
                    continue

                if event.key in {pygame.K_LEFT, pygame.K_RIGHT}:
                    self._toggle_sprite_mode()
                elif event.key in {pygame.K_g}:
                    self._generate_sprites_from_openai()
                elif event.key in {pygame.K_b}:
                    self._open_openai_browser_oauth()
                elif event.key in {pygame.K_k}:
                    self.options_input_mode = True
                    self.options_reveal_key = False
                    self.options_status = "Type key, Ctrl+V to paste, Tab to show/hide, Enter to save."
                elif event.key in {pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_o}:
                    self.state = "splash"
                continue

            if (self.failed or self.won) and event.key == pygame.K_r:
                self.__init__()
                self.state = "playing"
                continue

            if self.failed or self.won:
                continue

            down_pressed = pygame.key.get_pressed()[pygame.K_DOWN] or pygame.key.get_pressed()[pygame.K_s]
            if event.key == pygame.K_SPACE and down_pressed and self.player.actor.on_ground:
                self.drop_through_timer = 0.18
                self.player.actor.rect.y += 4
            elif event.key == pygame.K_SPACE and (self.player.actor.on_ground or self.player.actor.in_water or self.player.actor.on_ladder):
                self.player.actor.vy = JUMP_VELOCITY * (0.58 if self.player.actor.in_water else 1.0)
            if event.key == pygame.K_z:
                self._use_weapon_fire()
            if event.key == pygame.K_TAB:
                self._cycle_weapon()
            if event.key == pygame.K_g:
                self._use_grappling_hook()
            if event.key == pygame.K_x:
                self._start_melee("punch")
            if event.key == pygame.K_c:
                self._start_melee("kick")
            if event.key == pygame.K_v:
                self._start_melee("flying_kick")
            if event.key == pygame.K_e:
                if self.player.actor.rect.intersects(self.terminal):
                    self.rules.defuse_bomb()
                if self.player.actor.rect.intersects(self.silo_console) and self.player.has_bomb and self.player.has_codes:
                    self.silo_sabotaged = True
            if event.key == pygame.K_ESCAPE:
                self.state = "splash"

    def _cycle_weapon(self) -> None:
        owned = sorted(self.weapons_owned)
        if not owned:
            return
        i = owned.index(self.current_weapon) if self.current_weapon in owned else 0
        self.current_weapon = owned[(i + 1) % len(owned)]

    def _use_weapon_fire(self) -> None:
        weapon = weapon_profile(self.current_weapon)
        if weapon["ranged"] <= 0:
            # fallback to classic shuriken throw
            if self.player.shots <= 0 or self.energy < 3:
                return
            p = self.player.actor.rect
            self.projectiles.append(Projectile(Rect(p.x + p.w / 2, p.y + 24, 12, 12), 700 * self.facing, 1.1, "player"))
            self.player.shots -= 1
            self.energy = max(0.0, self.energy - 3)
            return

        if self.ranged_cd > 0:
            return
        ammo = self.weapon_ammo.get(self.current_weapon, 0)
        if ammo <= 0:
            return
        energy_cost = weapon["energy"]
        if self.energy < energy_cost:
            return

        p = self.player.actor.rect
        speed = 760 if self.current_weapon == "machine_gun" else 700
        ttl = 1.0 if self.current_weapon == "machine_gun" else 1.2
        self.projectiles.append(Projectile(Rect(p.x + p.w / 2, p.y + 20, 10, 10), speed * self.facing, ttl, "player"))
        self.weapon_ammo[self.current_weapon] = ammo - 1
        self.energy = max(0.0, self.energy - energy_cost)
        self.ranged_cd = weapon["fire_cd"]

    def _start_melee(self, style: str) -> None:
        if self.attack_cd > 0:
            return
        p = self.player.actor.rect
        width, height, ttl, dmg = 40, 24, 0.18, 1
        weapon = weapon_profile(self.current_weapon)
        if style == "kick":
            width, height, ttl, dmg = 54, 24, 0.2, 2
        if style == "flying_kick":
            width, height, ttl, dmg = 68, 28, 0.24, 3
            if self.player.actor.on_ground:
                self.player.actor.vy = -350
        dmg = int((dmg + (self.level - 1) // 2) * weapon["melee"])
        if self.energy < weapon["energy"]:
            return
        self.energy = max(0.0, self.energy - weapon["energy"])
        hit_x = p.right if self.facing > 0 else p.left - width
        self.attack = AttackWindow(Rect(hit_x, p.y + 20, width, height), ttl, dmg)
        self.attack_cd = 0.3

    def _update(self, dt: float) -> None:
        self.time_alive += dt
        self.anim_time += dt
        self.drop_through_timer = max(0.0, self.drop_through_timer - dt)
        self.attack_cd = max(0.0, self.attack_cd - dt)
        self.invisibility_timer = max(0.0, self.invisibility_timer - dt)
        self.invincibility_timer = max(0.0, self.invincibility_timer - dt)
        self.speed_timer = max(0.0, self.speed_timer - dt)
        self.ranged_cd = max(0.0, self.ranged_cd - dt)
        if self.grapple_line:
            self.grapple_line.ttl -= dt
            if self.grapple_line.ttl <= 0:
                self.grapple_line = None
        keys = pygame.key.get_pressed()

        speed_boost = 1.45 if self.speed_timer > 0 else 1.0
        level_speed = 1.0 + (self.level - 1) * 0.03
        move_speed = RUN_SPEED * level_speed * speed_boost * (0.58 if self.player.actor.in_water else 1.0)
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

        drop_down = self.drop_through_timer > 0 or ((keys[pygame.K_DOWN] or keys[pygame.K_s]) and keys[pygame.K_SPACE])
        self.hidden = keys[pygame.K_DOWN] and any(self.player.actor.rect.intersects(b) for b in self.bushes)
        self.meditating = bool(keys[pygame.K_m] and self.player.actor.on_ground and abs(self.player.actor.vx) < 8 and abs(self.player.actor.vy) < 18)
        if self.meditating:
            self.energy = min(self.max_energy, self.energy + meditate_recovery_per_sec(self.level) * dt)
        else:
            self.energy = min(self.max_energy, self.energy + 2.2 * dt)

        self.physics.move_actor(self.player.actor, dt, drop_down=drop_down, climb_dir=climb_dir)
        self.player.actor.rect.x = max(0, min(WORLD_W - self.player.actor.rect.w, self.player.actor.rect.x))
        self.player.actor.rect.y = max(0, min(WORLD_H - self.player.actor.rect.h, self.player.actor.rect.y))
        self._update_train(dt)
        self._update_elevators(dt)
        for e in self.enemies:
            e.update(dt, self.physics)

        self._update_attack(dt)
        self._update_projectiles(dt)
        self._enemy_logic()
        self._update_drops(dt)
        self._collect_items()
        self._collect_drops()
        self._update_particles(dt)
        self.bomb.tick(dt)
        self._check_end_state()

        target = self.player.actor.rect.x - SCREEN_W * 0.45
        self.camera_x = max(0, min(WORLD_W - SCREEN_W, target))
        target_y = self.player.actor.rect.y - SCREEN_H * 0.52
        self.camera_y = max(0, min(WORLD_H - SCREEN_H, target_y))

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

    def _update_elevators(self, dt: float) -> None:
        p = self.player.actor.rect
        for elevator in self.elevators:
            old_y = elevator.rect.y
            elevator.rect.y += elevator.speed * dt
            if elevator.rect.y <= elevator.y_min:
                elevator.rect.y = elevator.y_min
                elevator.speed = abs(elevator.speed)
            elif elevator.rect.y >= elevator.y_max:
                elevator.rect.y = elevator.y_max
                elevator.speed = -abs(elevator.speed)

            standing = (
                p.bottom <= old_y + 10
                and p.bottom >= old_y - 8
                and p.right > elevator.rect.left + 2
                and p.left < elevator.rect.right - 2
            )
            if standing:
                p.y += elevator.rect.y - old_y
                p.y = elevator.rect.top - p.h
                self.player.actor.on_ground = True

    def _grapple_range(self) -> float:
        return 260.0 + self.grapple_bonus + (self.level - 1) * 35.0

    def _award_xp(self, amount: int) -> None:
        self.xp += amount
        while self.xp >= self.next_level_xp:
            self.xp -= self.next_level_xp
            self.level += 1
            self.grapple_bonus += 18.0
            self.next_level_xp = xp_to_next_level(self.level)
            self._emit_particles(self.player.actor.rect.x + 16, self.player.actor.rect.y + 16, GOLD, 20)

    def _on_enemy_defeated(self, enemy: Enemy) -> None:
        self._spawn_enemy_drop(enemy)
        self._award_xp(ENEMY_XP.get(enemy.kind, 10))

    def _use_grappling_hook(self) -> None:
        if self.energy < 14:
            return
        self.energy = max(0.0, self.energy - 14)
        p = self.player.actor.rect
        start = (p.x + p.w / 2, p.y + 16)
        max_range = self._grapple_range()
        direction = 1 if self.facing > 0 else -1
        target_x = start[0] + direction * max_range
        target_y = start[1] - min(210, max_range * 0.55)

        anchor: tuple[float, float] | None = None
        # Find an anchor point on nearby solid tops.
        for solid in self.solids:
            top_y = solid.top
            if top_y >= start[1]:
                continue
            if direction > 0 and solid.left < start[0]:
                continue
            if direction < 0 and solid.right > start[0]:
                continue
            ax = solid.left if direction > 0 else solid.right
            dx = ax - start[0]
            dy = top_y - start[1]
            if dx * dx + dy * dy <= max_range * max_range:
                if anchor is None or abs(dx) < abs(anchor[0] - start[0]):
                    anchor = (ax, top_y)

        if anchor is None:
            anchor = (target_x, target_y)

        self.grapple_line = GrappleLine(start=start, end=anchor, ttl=0.2)
        pull_x = (anchor[0] - start[0]) * 2.4
        pull_y = (anchor[1] - start[1]) * 2.0
        self.player.actor.vx = max(-520, min(520, pull_x))
        self.player.actor.vy = max(-760, min(-220, pull_y))

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
                    self._on_enemy_defeated(e)

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
                if self.invincibility_timer <= 0:
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
                self._on_enemy_defeated(e)
            return True
        return False

    def _enemy_logic(self) -> None:
        p = self.player.actor.rect
        for e in self.enemies:
            if not e.alive:
                continue
            if p.intersects(e.actor.rect):
                if self.invincibility_timer <= 0:
                    self.player.health = max(0, self.player.health - 1)
                    self._emit_particles(p.x + p.w / 2, p.y + 32, RED, 7)
                    self.player.actor.rect.x = max(40, self.player.actor.rect.x - 70)
            dist = abs((e.actor.rect.x + e.actor.rect.w / 2) - (p.x + p.w / 2))
            same_level = abs(e.actor.rect.y - p.y) < 56
            sight = 380 if e.kind in {"boss", "drone", "robot"} else (340 if e.kind in {"ninja", "assassin"} else 260)
            sees_player = self.invisibility_timer <= 0 and not self.hidden and dist < sight
            if sees_player and same_level and e.attack_cd <= 0 and e.kind in {"ninja", "guard", "drone", "boss", "assassin", "henchman", "robot"}:
                sign = -1 if p.x < e.actor.rect.x else 1
                proj_speed = 640 if e.kind == "boss" else (600 if e.kind in {"drone", "robot"} else (560 if e.kind == "assassin" else 540))
                self.projectiles.append(Projectile(Rect(e.actor.rect.x + e.actor.rect.w / 2, e.actor.rect.y + 18, 12, 12), proj_speed * sign, 1.1, "enemy"))
                e.attack_cd = 0.85 if e.kind == "boss" else (1.1 if e.kind == "assassin" else 1.5)

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

        for wp in self.weapon_pickups:
            if not wp.taken and p.intersects(wp.rect):
                wp.taken = True
                self.weapons_owned.add(wp.name)
                if wp.name in self.weapon_ammo:
                    self.weapon_ammo[wp.name] = max(self.weapon_ammo[wp.name], int(weapon_profile(wp.name)["ammo"]))
                self.current_weapon = wp.name
                self._emit_particles(wp.rect.x + 11, wp.rect.y + 11, wp.color, 16)

    def _update_drops(self, dt: float) -> None:
        alive: list[Drop] = []
        for drop in self.drops:
            drop.ttl -= dt
            if drop.ttl > 0:
                alive.append(drop)
        self.drops = alive

    def _spawn_enemy_drop(self, enemy: Enemy) -> None:
        cx = enemy.actor.rect.x + enemy.actor.rect.w / 2 - 12
        cy = enemy.actor.rect.y + enemy.actor.rect.h / 2 - 12

        if enemy.boss:
            self.drops.append(Drop("gold", Rect(cx - 12, cy, 24, 24), ttl=24.0))
            self.drops.append(Drop("invisibility", Rect(cx + 16, cy, 24, 24), ttl=24.0))
            self.drops.append(Drop("invincibility", Rect(cx + 44, cy, 24, 24), ttl=24.0))
            return

        if random.random() < 0.16:
            self.drops.append(Drop("gold", Rect(cx, cy, 24, 24)))

        if random.random() < 0.12:
            kind = random.choice(["invisibility", "invincibility", "speed", "energy_orb"])
            self.drops.append(Drop(kind, Rect(cx + 18, cy, 24, 24)))

        if enemy.kind in {"thug", "henchman", "guard", "ninja", "assassin", "robot"} and random.random() < 0.14:
            kind = random.choice(["stick", "brick", "pole", "nunchukas", "sais", "sword", "gun", "machine_gun", "silencer"])
            self.drops.append(Drop(kind, Rect(cx - 20, cy + 12, 24, 24)))

    def _collect_drops(self) -> None:
        p = self.player.actor.rect
        remaining: list[Drop] = []
        for drop in self.drops:
            if not p.intersects(drop.rect):
                remaining.append(drop)
                continue
            if drop.kind == "gold":
                self.gold += 15
                self._emit_particles(drop.rect.x + 12, drop.rect.y + 12, GOLD, 10)
            elif drop.kind == "invisibility":
                self.invisibility_timer = max(self.invisibility_timer, 10.0)
                self._emit_particles(drop.rect.x + 12, drop.rect.y + 12, CYAN, 12)
            elif drop.kind == "invincibility":
                self.invincibility_timer = max(self.invincibility_timer, 8.0)
                self._emit_particles(drop.rect.x + 12, drop.rect.y + 12, YELLOW, 12)
            elif drop.kind == "speed":
                self.speed_timer = max(self.speed_timer, 9.0)
                self._emit_particles(drop.rect.x + 12, drop.rect.y + 12, GREEN, 12)
            elif drop.kind == "energy_orb":
                self.energy = min(self.max_energy, self.energy + 38)
                self._emit_particles(drop.rect.x + 12, drop.rect.y + 12, CYAN, 14)
            elif drop.kind in {"stick", "brick", "pole", "nunchukas", "sais", "sword", "gun", "machine_gun", "silencer"}:
                self.weapons_owned.add(drop.kind)
                if drop.kind in self.weapon_ammo:
                    self.weapon_ammo[drop.kind] = self.weapon_ammo.get(drop.kind, 0) + 18
                self.current_weapon = drop.kind
                self._emit_particles(drop.rect.x + 12, drop.rect.y + 12, ORANGE, 12)
        self.drops = remaining

    def _all_mission_items_collected(self) -> bool:
        return all(i.taken for i in self.pickups)

    def _check_end_state(self) -> None:
        if self.player.health <= 0 or self.rules.bomb_exploded():
            self.failed = True
            return
        if self._all_mission_items_collected() and self.player.actor.rect.intersects(self.terminal):
            self.rules.defuse_bomb()
        helicopter_ready = self.player.actor.rect.intersects(self.helicopter) or self.player.actor.rect.intersects(self.helicopter_pad)
        if self.rules.can_escape(self.player) and self._all_mission_items_collected() and self.silo_sabotaged and helicopter_ready:
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
        self.screen.blit(image, (rect.x - self.camera_x, rect.y - self.camera_y))

    def _draw_sprite_at(self, x: float, y: float, sprite: pygame.Surface, flip: bool = False) -> None:
        image = pygame.transform.flip(sprite, flip, False) if flip else sprite
        self.screen.blit(image, (x - self.camera_x, y - self.camera_y))

    def _draw_character_animated(self, rect: Rect, sprite: pygame.Surface, flip: bool = False, moving: bool = False, fast: bool = False, airborne: bool = False) -> None:
        sway = 0.0
        bob = 0.0
        if airborne:
            bob = 1.0 * math.sin(self.anim_time * 20)
        elif moving:
            speed = 24 if fast else 16
            sway = 1.4 * math.sin(self.anim_time * speed)
            bob = 1.5 * abs(math.sin(self.anim_time * speed * 0.7))
        self._draw_sprite_at(rect.x + sway, rect.y - bob, sprite, flip)

    def _draw_spinning_shuriken(self, rect: Rect) -> None:
        angle = (self.anim_time * 1600) % 360
        rotated = pygame.transform.rotozoom(self.sprites.shuriken, angle, 1.0)
        cx = rect.x + rect.w / 2 - self.camera_x
        cy = rect.y + rect.h / 2 - self.camera_y
        self.screen.blit(rotated, rotated.get_rect(center=(cx, cy)))

    def _draw_world(self) -> None:
        for y in range(SCREEN_H):
            t = y / SCREEN_H
            col = (int(SKY[0] * (1 - t) + 6 * t), int(SKY[1] * (1 - t) + 10 * t), int(SKY[2] * (1 - t) + 18 * t))
            pygame.draw.line(self.screen, col, (0, y), (SCREEN_W, y))

        moon_x = int(SCREEN_W * 0.8 - (self.camera_x * 0.05) % (SCREEN_W + 140))
        pygame.draw.circle(self.screen, (230, 236, 255), (moon_x, 90), 36)

        for zone in self.water:
            sx = zone.x - self.camera_x
            sy = zone.y - self.camera_y
            pygame.draw.rect(self.screen, WATER, pygame.Rect(sx, sy, zone.w, zone.h))
            for i in range(0, int(zone.w), 38):
                wave = int(4 * math.sin(self.time_alive * 4 + i * 0.1))
                pygame.draw.line(self.screen, WATER_FOAM, (sx + i, sy + 10 + wave), (sx + i + 20, sy + 10 + wave), 2)
            pygame.draw.rect(self.screen, (54, 46, 34), pygame.Rect(sx, SCREEN_H - 24 - self.camera_y + WORLD_Y_OFFSET, zone.w, 24))

        for x in range(0, SCREEN_W, 120):
            h = 120 + int(30 * math.sin((x + self.camera_x * 0.2) * 0.02))
            pygame.draw.rect(self.screen, MID_BG, pygame.Rect(x, SCREEN_H - FLOOR_H - h, 90, h))
            pygame.draw.rect(self.screen, NEAR_BG, pygame.Rect(x + 14, SCREEN_H - FLOOR_H - h + 18, 10, 10), border_radius=1)
            pygame.draw.rect(self.screen, NEAR_BG, pygame.Rect(x + 38, SCREEN_H - FLOOR_H - h + 34, 10, 10), border_radius=1)

        # Retro skyline silhouettes to mimic the original's strong city profile.
        for x in range(-120, SCREEN_W + 120, 80):
            offset = (self.camera_x * 0.12) % 80
            sx = x - offset
            b_h = 160 + int(46 * math.sin((x + self.camera_x) * 0.016))
            pygame.draw.rect(self.screen, (14, 18, 30), pygame.Rect(sx, SCREEN_H - FLOOR_H - b_h, 64, b_h))
            if b_h > 170:
                pygame.draw.rect(self.screen, (196, 178, 96), pygame.Rect(sx + 14, SCREEN_H - FLOOR_H - b_h + 24, 6, 6))
                pygame.draw.rect(self.screen, (196, 178, 96), pygame.Rect(sx + 34, SCREEN_H - FLOOR_H - b_h + 50, 6, 6))

        for bush in self.bushes:
            sx = bush.x - self.camera_x
            pygame.draw.ellipse(self.screen, (42, 122, 72), pygame.Rect(sx, bush.y - self.camera_y, bush.w, bush.h))

        for area in self.areas:
            sx = area.rect.x - self.camera_x
            sy = area.rect.y - self.camera_y
            if sx > SCREEN_W or sx + area.rect.w < -8:
                continue
            pygame.draw.rect(self.screen, area.color, pygame.Rect(sx, sy, area.rect.w, area.rect.h), border_radius=6)
            pygame.draw.rect(self.screen, (18, 22, 30), pygame.Rect(sx, sy, area.rect.w, area.rect.h), width=2, border_radius=6)
            label = self.font.render(area.name, True, (240, 242, 248))
            self.screen.blit(label, (sx + 12, sy + 16))

        # Elevator shafts and monorail supports inside the tower.
        for shaft_x in (7420, 8080, 8740, 9320):
            sx = shaft_x - self.camera_x
            pygame.draw.rect(self.screen, (48, 54, 70), pygame.Rect(sx, 92 - self.camera_y + WORLD_Y_OFFSET, 52, 586), border_radius=3)
            for y in range(116, 650, 64):
                pygame.draw.rect(self.screen, (104, 118, 146), pygame.Rect(sx + 6, y - self.camera_y + WORLD_Y_OFFSET, 40, 20), border_radius=2)

        for elevator in self.elevators:
            pygame.draw.rect(self.screen, (168, 184, 212), pygame.Rect(elevator.rect.x - self.camera_x, elevator.rect.y - self.camera_y, elevator.rect.w, elevator.rect.h), border_radius=3)
            pygame.draw.rect(self.screen, (52, 58, 74), pygame.Rect(elevator.rect.x - self.camera_x + 3, elevator.rect.y - self.camera_y + 4, elevator.rect.w - 6, elevator.rect.h - 8), border_radius=2)

        pygame.draw.rect(self.screen, (84, 96, 128), pygame.Rect(7240 - self.camera_x, 122 - self.camera_y + WORLD_Y_OFFSET, 2220, 8))
        for i in range(7240, 9460, 58):
            pygame.draw.rect(self.screen, (152, 166, 198), pygame.Rect(i - self.camera_x, 126 - self.camera_y + WORLD_Y_OFFSET, 34, 5), border_radius=1)

        for s in self.solids:
            sx = s.x - self.camera_x
            if sx > SCREEN_W or sx + s.w < -4:
                continue
            sy = s.y - self.camera_y
            pygame.draw.rect(self.screen, PLATFORM_SIDE, pygame.Rect(sx, sy, s.w, s.h), border_radius=2)
            pygame.draw.rect(self.screen, PLATFORM_TOP, pygame.Rect(sx, sy, s.w, 4), border_radius=2)

        for p in self.one_way:
            sx = p.x - self.camera_x
            if sx > SCREEN_W or sx + p.w < -4:
                continue
            sy = p.y - self.camera_y
            pygame.draw.rect(self.screen, (90, 100, 124), pygame.Rect(sx, sy, p.w, p.h), border_radius=2)
            pygame.draw.line(self.screen, (180, 190, 210), (sx, sy), (sx + p.w, sy), 2)

        for ladder in self.ladders:
            for seg in range(int(ladder.h // 68) + 1):
                y = ladder.y + seg * 68
                self.screen.blit(self.sprites.ladder, (ladder.x - self.camera_x, y - self.camera_y))

        # Missile silo and helipad landmarks.
        pygame.draw.rect(self.screen, (96, 86, 82), pygame.Rect(5520 - self.camera_x, 1900 - self.camera_y, 180, 600), border_radius=10)
        pygame.draw.rect(self.screen, (198, 82, 70), pygame.Rect(5580 - self.camera_x, 1980 - self.camera_y, 60, 430), border_radius=14)
        pygame.draw.rect(self.screen, (82, 112, 136), pygame.Rect(self.silo_console.x - self.camera_x, self.silo_console.y - self.camera_y, self.silo_console.w, self.silo_console.h), border_radius=4)
        silo_txt = "SILO SABOTAGED" if self.silo_sabotaged else "SILO CONSOLE"
        self.screen.blit(self.font.render(silo_txt, True, (230, 230, 230)), (self.silo_console.x - self.camera_x - 30, self.silo_console.y - self.camera_y - 20))

        pygame.draw.rect(self.screen, (112, 126, 144), pygame.Rect(self.helicopter_pad.x - self.camera_x, self.helicopter_pad.y - self.camera_y, self.helicopter_pad.w, self.helicopter_pad.h), border_radius=3)
        pygame.draw.circle(self.screen, (232, 232, 236), (int(self.helicopter_pad.x - self.camera_x + self.helicopter_pad.w / 2), int(self.helicopter_pad.y - self.camera_y + 8)), 70, width=3)
        pygame.draw.rect(self.screen, (68, 90, 114), pygame.Rect(self.helicopter.x - self.camera_x, self.helicopter.y - self.camera_y, self.helicopter.w, self.helicopter.h), border_radius=8)
        pygame.draw.rect(self.screen, (170, 192, 220), pygame.Rect(self.helicopter.x - self.camera_x + 34, self.helicopter.y - self.camera_y + 18, 120, 20), border_radius=6)
        pygame.draw.rect(self.screen, (28, 34, 48), pygame.Rect(self.helicopter.x - self.camera_x - 50, self.helicopter.y - self.camera_y + 4, self.helicopter.w + 100, 6), border_radius=2)

        self.screen.blit(self.sprites.train, (self.train_rect.x - self.camera_x, self.train_rect.y - self.camera_y))
        pygame.draw.rect(self.screen, (60, 62, 70), pygame.Rect(self.train_min_x - self.camera_x, self.train_rect.y + 58 - self.camera_y, self.train_max_x - self.train_min_x, 6))

        self.screen.blit(self.sprites.dinghy, (24 - self.camera_x * 0.03, SCREEN_H - 120))

    def _read_clipboard_text(self) -> str:
        try:
            if not pygame.scrap.get_init():
                pygame.scrap.init()
            raw = pygame.scrap.get(pygame.SCRAP_TEXT)
            if not raw:
                return ""
            return raw.decode("utf-8", errors="ignore").replace("\x00", "").strip()
        except Exception:
            return ""

    def _load_api_key(self) -> str:
        if OPENAI_TOKEN_FILE.exists():
            return OPENAI_TOKEN_FILE.read_text(encoding="utf-8").strip()
        return os.environ.get("OPENAI_API_KEY", "").strip()

    def _save_api_key(self, key: str) -> None:
        OPENAI_TOKEN_FILE.write_text(key.strip(), encoding="utf-8")

    def _open_openai_browser_oauth(self) -> None:
        webbrowser.open("https://platform.openai.com/settings/organization/api-keys")
        self.options_status = "Browser opened: sign in and create key, then paste with K."

    def _generate_sprites_from_openai(self) -> None:
        api_key = self.openai_api_key.strip()
        if not api_key:
            self.options_status = "No API key set. Press K to paste a key."
            return

        sprites = {
            "player.png": {"size": "1024x1024", "prompt": "single full-body stealth operative sprite, side-on platformer style, edgy tactical outfit, photorealistic PBR textures, dramatic cinematic lighting, transparent background, no text"},
            "guard.png": {"size": "1024x1024", "prompt": "single full-body security guard sprite, side-on platformer style, hardened urban gear, photorealistic textures, transparent background, pre-rendered game art, no text"},
            "ninja.png": {"size": "1024x1024", "prompt": "single full-body elite ninja enemy sprite, side-on platformer style, edgy dark armor, photorealistic material detail, transparent background, pre-rendered game art, no text"},
            "dog.png": {"size": "1024x1024", "prompt": "single guard dog sprite, side-on platformer style, photorealistic fur texture and harness, transparent background, pre-rendered game art, no text"},
            "terminal.png": {"size": "1024x1024", "prompt": "single sci-fi hacking terminal object sprite, side-on platformer style, realistic metal wear and emissive screens, transparent background, pre-rendered game art"},
            "shuriken.png": {"size": "1024x1024", "prompt": "single shuriken weapon sprite, centered, brushed steel photoreal detail, transparent background, pre-rendered game art"},
            "ladder.png": {"size": "1024x1024", "prompt": "single metal ladder module sprite for platform game, industrial grime and paint wear, transparent background, pre-rendered game art"},
            "train.png": {"size": "1536x1024", "prompt": "single side-view futuristic train car sprite for stealth platform game, gritty photorealistic materials and reflections, transparent background, pre-rendered game art"},
            "dinghy.png": {"size": "1024x1024", "prompt": "single inflatable dinghy boat sprite, side view, photorealistic rubber and wet surface detail, transparent background, pre-rendered game art"},
        }

        out_dir = Path("assets/generated")
        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            for filename, spec in sprites.items():
                payload = {
                    "model": OPENAI_IMAGE_MODEL,
                    "prompt": spec["prompt"],
                    "size": spec["size"],
                    "background": "transparent",
                    "quality": "high",
                }
                request = urllib.request.Request(
                    url="https://api.openai.com/v1/images/generations",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(request, timeout=120) as response:
                    data = json.loads(response.read().decode("utf-8"))
                png = base64.b64decode(data["data"][0]["b64_json"])
                (out_dir / filename).write_bytes(png)
        except HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8", errors="replace")
            except Exception:
                detail = ""
            detail = detail.replace("\n", " ")
            self.options_status = f"Generation failed ({exc.code}): {detail or exc.reason}"[:120]
            return
        except Exception as exc:
            self.options_status = f"Generation failed: {exc}"[:120]
            return

        self.generated_assets_present = SpriteBank.generated_assets_ready()
        self.sprites = SpriteBank(use_generated_assets=self.use_openai_sprites)
        self.options_status = "Sprites generated and loaded from assets/generated/."

    def _toggle_sprite_mode(self) -> None:
        self.use_openai_sprites = not self.use_openai_sprites
        self.generated_assets_present = SpriteBank.generated_assets_ready()
        self.sprites = SpriteBank(use_generated_assets=self.use_openai_sprites)
        self.openai_api_key = self._load_api_key()
        self.options_status = ""
        self.options_input_mode = False

    def _draw_splash(self) -> None:
        self.screen.fill((8, 10, 18))
        title = self.big.render("SABOTEUR REPLICA", True, (236, 238, 248))
        subtitle = self.medium.render("Vertical + Horizontal Infiltration", True, (136, 196, 214))
        hint1 = self.font.render("ENTER = Start Mission", True, (220, 220, 230))
        hint2 = self.font.render("O = Options (OpenAI connect + generate)", True, (220, 220, 230))
        hint3 = self.font.render("Q / ESC = Quit", True, (190, 190, 205))
        mode = "ON (generated if files exist)" if self.use_openai_sprites else "OFF (procedural art only)"
        status = self.font.render(f"OpenAI sprites: {mode}", True, (120, 226, 170))
        files = "ready" if self.generated_assets_present else "not found"
        files_line = self.font.render(f"Generated sprite files: {files}", True, (180, 190, 210))
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 170))
        self.screen.blit(subtitle, (SCREEN_W // 2 - subtitle.get_width() // 2, 230))
        self.screen.blit(hint1, (SCREEN_W // 2 - hint1.get_width() // 2, 340))
        self.screen.blit(hint2, (SCREEN_W // 2 - hint2.get_width() // 2, 376))
        self.screen.blit(hint3, (SCREEN_W // 2 - hint3.get_width() // 2, 412))
        self.screen.blit(status, (SCREEN_W // 2 - status.get_width() // 2, 500))
        self.screen.blit(files_line, (SCREEN_W // 2 - files_line.get_width() // 2, 532))
        pygame.display.flip()

    def _draw_options(self) -> None:
        self.screen.fill((12, 16, 26))
        title = self.big.render("OPTIONS", True, (240, 240, 246))
        mode = "ON" if self.use_openai_sprites else "OFF"
        mode_desc = "Use generated sprites when PNG files exist." if self.use_openai_sprites else "Always use built-in procedural sprites."
        row = self.medium.render(f"OpenAI sprites: {mode}", True, (120, 226, 170) if self.use_openai_sprites else (226, 166, 120))
        row2 = self.font.render(mode_desc, True, (212, 214, 224))
        files = "All required files found." if self.generated_assets_present else "Generated files missing (game will fallback safely)."
        row3 = self.font.render(files, True, (182, 192, 212))
        if self.options_input_mode:
            token_value = self.openai_api_key if self.options_reveal_key else ("*" * len(self.openai_api_key))
            token_preview = token_value if token_value else "(empty)"
            token_title = "API key (editing):"
        else:
            token_preview = (self.openai_api_key[:6] + "..." + self.openai_api_key[-4:]) if len(self.openai_api_key) > 12 else ("(set)" if self.openai_api_key else "(not set)")
            token_title = "API key:"
        token_line = self.font.render(f"{token_title} {token_preview}", True, (210, 214, 230))
        oauth_line = self.font.render("B: Browser key page  K: Edit key  G: Generate sprites", True, (220, 220, 230))
        mode_line = self.font.render("(During key edit: Ctrl+V paste, Tab show/hide key, Enter save, Esc cancel.)", True, (170, 180, 205))
        status_line = self.font.render(self.options_status or "", True, (120, 226, 170))
        help2 = self.font.render("LEFT/RIGHT: toggle sprite mode   ESC/BACKSPACE/O: back", True, (220, 220, 230))
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 120))
        self.screen.blit(row, (SCREEN_W // 2 - row.get_width() // 2, 240))
        self.screen.blit(row2, (SCREEN_W // 2 - row2.get_width() // 2, 282))
        self.screen.blit(row3, (SCREEN_W // 2 - row3.get_width() // 2, 312))
        self.screen.blit(token_line, (SCREEN_W // 2 - token_line.get_width() // 2, 360))
        self.screen.blit(oauth_line, (SCREEN_W // 2 - oauth_line.get_width() // 2, 398))
        self.screen.blit(mode_line, (SCREEN_W // 2 - mode_line.get_width() // 2, 428))
        self.screen.blit(status_line, (SCREEN_W // 2 - status_line.get_width() // 2, 462))
        self.screen.blit(help2, (SCREEN_W // 2 - help2.get_width() // 2, 514))
        pygame.display.flip()

    def _draw_pickup(self, item: Pickup) -> None:
        cx = int(item.rect.x - self.camera_x + 11)
        cy = int(item.rect.y - self.camera_y + 11)
        pulse = 1.0 + 0.15 * math.sin(self.time_alive * 6 + item.rect.x * 0.02)
        radius = int(10 * pulse)
        pygame.draw.circle(self.screen, (255, 255, 255), (cx, cy), radius + 2, width=1)
        pygame.draw.circle(self.screen, item.color, (cx, cy), radius)

    def _draw(self) -> None:
        if self.state == "splash":
            self._draw_splash()
            return
        if self.state == "options":
            self._draw_options()
            return

        self._draw_world()

        for item in self.pickups:
            if not item.taken:
                self._draw_pickup(item)
        for wp in self.weapon_pickups:
            if not wp.taken:
                self._draw_pickup(wp)

        terminal_glow = 0.84 + 0.16 * (0.5 + 0.5 * math.sin(self.anim_time * 10.0))
        terminal_frame = self.sprites.terminal.copy()
        terminal_frame.set_alpha(int(255 * terminal_glow))
        self._draw_sprite(self.terminal, terminal_frame)
        pygame.draw.rect(self.screen, ORANGE, pygame.Rect(self.exit_pad.x - self.camera_x, self.exit_pad.y - self.camera_y, self.exit_pad.w, self.exit_pad.h), border_radius=4)
        self.screen.blit(self.font.render("OLD EXIT", True, (22, 22, 24)), (self.exit_pad.x - self.camera_x + 20, self.exit_pad.y - self.camera_y + 2))

        for e in self.enemies:
            if not e.alive:
                continue
            if e.kind in {"guard", "heavy", "henchman", "thug"}:
                moving = abs(e.actor.vx) > 1
                self._draw_character_animated(e.actor.rect, self.sprites.guard, e.speed < 0, moving=moving, fast=abs(e.speed) > 110, airborne=not e.actor.on_ground)
                if e.kind == "heavy":
                    pygame.draw.rect(self.screen, (90, 90, 105), pygame.Rect(e.actor.rect.x - self.camera_x - 2, e.actor.rect.y - self.camera_y - 2, e.actor.rect.w + 4, e.actor.rect.h + 4), width=2, border_radius=3)
                if e.kind == "henchman":
                    pygame.draw.rect(self.screen, (82, 120, 168), pygame.Rect(e.actor.rect.x - self.camera_x - 2, e.actor.rect.y - self.camera_y + 14, e.actor.rect.w + 4, 6), border_radius=2)
                if e.kind == "thug":
                    pygame.draw.rect(self.screen, (128, 92, 70), pygame.Rect(e.actor.rect.x - self.camera_x - 2, e.actor.rect.y - self.camera_y - 2, e.actor.rect.w + 4, e.actor.rect.h + 4), width=2, border_radius=3)
            elif e.kind in {"ninja", "boss", "drone", "assassin", "robot"}:
                moving = abs(e.actor.vx) > 1
                self._draw_character_animated(e.actor.rect, self.sprites.ninja, e.speed < 0, moving=moving, fast=abs(e.speed) > 130, airborne=not e.actor.on_ground)
                if e.kind == "boss":
                    pygame.draw.rect(self.screen, ORANGE, pygame.Rect(e.actor.rect.x - self.camera_x - 4, e.actor.rect.y - self.camera_y - 4, e.actor.rect.w + 8, e.actor.rect.h + 8), width=2, border_radius=4)
                if e.kind == "drone":
                    pygame.draw.circle(self.screen, CYAN, (int(e.actor.rect.x - self.camera_x + e.actor.rect.w / 2), int(e.actor.rect.y - self.camera_y - 8)), 7, width=2)
                if e.kind == "assassin":
                    pygame.draw.rect(self.screen, PURPLE, pygame.Rect(e.actor.rect.x - self.camera_x - 3, e.actor.rect.y - self.camera_y + 18, e.actor.rect.w + 6, 5), border_radius=2)
                if e.kind == "robot":
                    pygame.draw.rect(self.screen, (120, 180, 210), pygame.Rect(e.actor.rect.x - self.camera_x - 2, e.actor.rect.y - self.camera_y - 2, e.actor.rect.w + 4, e.actor.rect.h + 4), width=2, border_radius=3)
            else:
                moving = abs(e.actor.vx) > 1
                self._draw_character_animated(e.actor.rect, self.sprites.dog, e.speed < 0, moving=moving, fast=True, airborne=not e.actor.on_ground)
                cx = int(e.actor.rect.x - self.camera_x + e.actor.rect.w / 2)
                cy = int(e.actor.rect.y - self.camera_y + e.actor.rect.h / 2)
                if e.kind == "bat":
                    pygame.draw.polygon(self.screen, PURPLE, [(cx - 12, cy - 6), (cx, cy - 14), (cx + 12, cy - 6), (cx, cy - 2)])
                elif e.kind == "rat":
                    pygame.draw.line(self.screen, (188, 150, 120), (cx + 10, cy + 6), (cx + 20, cy + 10), 2)
                elif e.kind == "snake":
                    pygame.draw.arc(self.screen, GREEN, pygame.Rect(cx - 14, cy - 8, 28, 16), 0.2, 2.8, 3)

        for p in self.projectiles:
            self._draw_spinning_shuriken(p.rect)

        if self.grapple_line:
            sx = self.grapple_line.start[0] - self.camera_x
            sy = self.grapple_line.start[1] - self.camera_y
            ex = self.grapple_line.end[0] - self.camera_x
            ey = self.grapple_line.end[1] - self.camera_y
            pygame.draw.line(self.screen, (202, 212, 236), (sx, sy), (ex, ey), 2)
            pygame.draw.circle(self.screen, (228, 236, 248), (int(ex), int(ey)), 4)

        for drop in self.drops:
            sx = int(drop.rect.x - self.camera_x + drop.rect.w / 2)
            sy = int(drop.rect.y - self.camera_y + drop.rect.h / 2)
            if drop.kind == "gold":
                pygame.draw.circle(self.screen, GOLD, (sx, sy), 10)
            elif drop.kind == "invisibility":
                pygame.draw.circle(self.screen, CYAN, (sx, sy), 10, width=3)
            elif drop.kind == "invincibility":
                pygame.draw.circle(self.screen, YELLOW, (sx, sy), 10, width=3)
            elif drop.kind == "energy_orb":
                pygame.draw.circle(self.screen, (120, 240, 240), (sx, sy), 10)
            elif drop.kind in {"stick", "brick", "pole", "nunchukas", "sais", "sword", "gun", "machine_gun", "silencer"}:
                pygame.draw.rect(self.screen, (198, 176, 124), pygame.Rect(sx - 10, sy - 6, 20, 12), border_radius=2)
            else:
                pygame.draw.polygon(self.screen, GREEN, [(sx, sy - 10), (sx + 10, sy), (sx, sy + 10), (sx - 10, sy)])

        for p in self.particles:
            pygame.draw.circle(self.screen, p.color, (int(p.x - self.camera_x), int(p.y - self.camera_y)), p.size)

        if self.attack:
            pygame.draw.rect(self.screen, (180, 255, 180), pygame.Rect(self.attack.rect.x - self.camera_x, self.attack.rect.y - self.camera_y, self.attack.rect.w, self.attack.rect.h), width=2, border_radius=4)

        if self.invisibility_timer > 0:
            ghost = self.sprites.player.copy()
            ghost.set_alpha(120)
            moving = abs(self.player.actor.vx) > 1
            self._draw_character_animated(self.player.actor.rect, ghost, self.facing < 0, moving=moving, fast=abs(self.player.actor.vx) > RUN_SPEED, airborne=not self.player.actor.on_ground)
        else:
            moving = abs(self.player.actor.vx) > 1
            self._draw_character_animated(self.player.actor.rect, self.sprites.player, self.facing < 0, moving=moving, fast=abs(self.player.actor.vx) > RUN_SPEED, airborne=not self.player.actor.on_ground)
        if self.hidden:
            self.screen.blit(self.font.render("HIDDEN", True, GREEN), (self.player.actor.rect.x - self.camera_x - 4, self.player.actor.rect.y - self.camera_y - 22))
        if self.meditating:
            self.screen.blit(self.font.render("MEDITATING", True, CYAN), (self.player.actor.rect.x - self.camera_x - 10, self.player.actor.rect.y - self.camera_y - 40))

        hud = (
            f"ZONE:{min(12, int((self.player.actor.rect.x / WORLD_W) * 12) + 1)}/12 HP:{self.player.health} SHURIKEN:{self.player.shots} "
            f"BOMB:{'YES' if self.player.has_bomb else 'NO'} CODES:{'YES' if self.player.has_codes else 'NO'} "
            f"ITEMS:{sum(1 for p in self.pickups if p.taken)}/{len(self.pickups)} GOLD:{self.gold} "
            f"TIMER:{'DEFUSED' if self.bomb.defused else f'{self.bomb.seconds_left:06.1f}s'}"
        )
        self.screen.blit(self.font.render(hud, True, WHITE), (14, 12))
        buffs = f"BUFFS INVIS:{self.invisibility_timer:04.1f}s INVINC:{self.invincibility_timer:04.1f}s SPEED:{self.speed_timer:04.1f}s"
        self.screen.blit(self.font.render(buffs, True, (176, 224, 214)), (14, 62))
        sprite_mode = "ON" if self.use_openai_sprites else "OFF"
        self.screen.blit(self.font.render(f"OPENAI SPRITES:{sprite_mode}", True, (168, 192, 232)), (14, 112))
        self.screen.blit(self.font.render("ANIMATION:60FPS LOOP", True, (168, 212, 168)), (14, 136))
        obj = f"OBJECTIVES SILO:{'DONE' if self.silo_sabotaged else 'PENDING'} HELI:TOP PAD"
        self.screen.blit(self.font.render(obj, True, (220, 204, 156)), (14, 160))
        ammo = self.weapon_ammo.get(self.current_weapon, 0) if self.current_weapon in self.weapon_ammo else self.player.shots
        xp_line = f"LEVEL:{self.level} XP:{self.xp}/{self.next_level_xp} GRAPPLE:{int(self._grapple_range())}px ENERGY:{int(self.energy)} WEAPON:{self.current_weapon.upper()} AMMO:{ammo}"
        self.screen.blit(self.font.render(xp_line, True, (180, 210, 250)), (14, 184))
        controls = "Move:A/D Jump:Space Fire:Z Grapple:G Meditate:M Cycle:Tab Interact:E ESC:Menu"
        self.screen.blit(self.font.render(controls, True, (200, 210, 230)), (14, 86))

        if self.failed:
            t = self.big.render("MISSION FAILED - R TO RETRY", True, RED)
            self.screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2, SCREEN_H // 2 - 24))
        if self.won:
            t = self.big.render("MISSION COMPLETE - R TO REPLAY", True, GREEN)
            self.screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2, SCREEN_H // 2 - 24))

        # CRT-like scanlines for a classic retro look.
        scan = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for y in range(0, SCREEN_H, 4):
            pygame.draw.line(scan, (8, 8, 12, 28), (0, y), (SCREEN_W, y), 1)
        self.screen.blit(scan, (0, 0))

        pygame.display.flip()


if __name__ == "__main__":
    SaboteurReplica().run()
