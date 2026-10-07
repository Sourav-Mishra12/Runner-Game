"""Cached, replaceable layered scenery and atmosphere for PIXEL ERA."""

from __future__ import annotations

import math
import random
from pathlib import Path

import pygame

WIDTH, FLOOR = 960, 420
WORLD_FOLDERS = ("day", "sunset", "night", "ruins")
SPEEDS = {"clouds": .025, "mountains": .075, "trees": .17, "foreground": .34}


class ParallaxSystem:
    """Draws cached sky, cloud, mountain, tree and foreground layers."""

    def __init__(self, assets_root: Path) -> None:
        self.assets_root = assets_root
        self.layers: dict[int, dict[str, pygame.Surface]] = {}
        self.sky_layers: dict[int, pygame.Surface | None] = {}
        self.day_sky = self._load_graphic("Sky.png")
        self.late_sky = self._load_graphic("background_2.png")
        self.stars = [(random.Random(i * 59).randrange(WIDTH), random.Random(i * 73).randrange(38, 250), i % 3 + 1) for i in range(90)]
        self.weather_particles = [[random.randrange(-WIDTH, WIDTH), random.randrange(FLOOR), random.uniform(220, 520), random.uniform(-50, 40)] for _ in range(90)]
        self.fog = pygame.Surface((WIDTH, FLOOR), pygame.SRCALPHA)
        self.flash = pygame.Surface((WIDTH, FLOOR), pygame.SRCALPHA)
        self.flash.fill((230, 239, 255, 58))
        self.last_event = ""
        self._build_layers()

    def _load_graphic(self, name: str) -> pygame.Surface | None:
        try:
            image = pygame.image.load(str(self.assets_root / "graphics" / name)).convert_alpha()
            return pygame.transform.smoothscale(image, (WIDTH, FLOOR))
        except (OSError, pygame.error):
            return None

    def _load_layer(self, world: int, name: str) -> pygame.Surface | None:
        path = self.assets_root / "assets" / "environments" / WORLD_FOLDERS[world] / f"{name}.png"
        try:
            source = pygame.image.load(str(path)).convert_alpha()
            return pygame.transform.smoothscale(source, (WIDTH * 2, FLOOR))
        except (OSError, pygame.error):
            return None

    def _build_layers(self) -> None:
        palettes = (
            ((147, 190, 184), (105, 151, 137), (49, 103, 70)),
            ((181, 124, 113), (115, 82, 100), (76, 70, 75)),
            ((56, 75, 112), (45, 72, 88), (35, 72, 65)),
            ((66, 83, 126), (50, 82, 101), (45, 77, 82)),
        )
        for world, (mountain_color, tree_color, foreground_color) in enumerate(palettes):
            cloud = pygame.Surface((WIDTH * 2, FLOOR), pygame.SRCALPHA)
            rng = random.Random(142 + world)
            for _ in range(18):
                x, y = rng.randrange(WIDTH * 2), rng.randrange(35, 190)
                width, height = rng.randrange(90, 190), rng.randrange(24, 48)
                color = (241, 247, 235, 120 if world < 2 else 48)
                pygame.draw.ellipse(cloud, color, (x, y, width, height))
                pygame.draw.ellipse(cloud, color, (x+width//4, y-12, width//2, height+16))
            mountains = pygame.Surface((WIDTH * 2, FLOOR), pygame.SRCALPHA)
            rng = random.Random(274 + world)
            points = [(0, FLOOR)]
            for x in range(0, WIDTH * 2 + 121, 120):
                peak = rng.randrange(215, 310)
                points.extend(((x+60, peak), (x+120, FLOOR)))
            pygame.draw.polygon(mountains, (*mountain_color, 255), points)
            trees = pygame.Surface((WIDTH * 2, FLOOR), pygame.SRCALPHA)
            rng = random.Random(319 + world)
            for x in range(-30, WIDTH * 2, 92):
                h = rng.randrange(50, 115)
                if world == 3:
                    pygame.draw.rect(trees, (*tree_color, 255), (x+34, FLOOR-h, 24, h))
                    pygame.draw.rect(trees, (*tree_color, 220), (x, FLOOR-h-20, 92, 24))
                    for yy in range(FLOOR-h+10, FLOOR-18, 28):
                        pygame.draw.rect(trees, (205, 163, 93, 140), (x+42, yy, 8, 8))
                else:
                    pygame.draw.rect(trees, (*tree_color, 255), (x+39, FLOOR-h+28, 14, h-28))
                    pygame.draw.circle(trees, (*tree_color, 255), (x+46, FLOOR-h+16), rng.randrange(24, 38))
            foreground = pygame.Surface((WIDTH * 2, FLOOR), pygame.SRCALPHA)
            for x in range(0, WIDTH * 2, 17):
                h = 8 + (x * 11 % 14)
                pygame.draw.line(foreground, (*foreground_color, 235), (x, FLOOR), (x+((x%3)-1)*4, FLOOR-h), 3)
            self.layers[world] = {}
            self.sky_layers[world] = self._load_layer(world, "sky")
            for name, fallback in (("clouds", cloud), ("mountains", mountains), ("trees", trees), ("foreground", foreground)):
                self.layers[world][name] = self._load_layer(world, name) or fallback

    @staticmethod
    def sky_phase(phase: float) -> tuple[str, float]:
        names = ("DAY", "SUNSET", "TWILIGHT", "NIGHT", "DAWN")
        return names[min(4, int((phase % 1.0) * 5))], phase % 1.0

    def draw(self, screen: pygame.Surface, distance: float, now: float, world: int, phase: float, weather: str = "clear", event: str = "") -> None:
        sky_stops = ((89, 174, 226), (238, 145, 111), (77, 80, 133), (20, 31, 67), (188, 136, 139), (89, 174, 226))
        scaled = (phase % 1.0) * 5
        segment, local_t = min(4, int(scaled)), scaled % 1
        start, end = sky_stops[segment], sky_stops[segment+1]
        top = tuple(int(a+(b-a)*local_t) for a, b in zip(start, end))
        ground_tint = (143, 205, 228)
        for band in range(24):
            t = band / 23
            color = tuple(int(top[i]*(1-t) + ground_tint[i]*t) for i in range(3))
            pygame.draw.rect(screen, color, (0, band * FLOOR // 24, WIDTH, FLOOR // 24 + 2))
        sky_art = self.sky_layers[world] or self.day_sky
        if sky_art:
            sky_art.set_alpha(78)
            screen.blit(sky_art, (0, 0))
        night_strength = max(0.0, min(1.0, (math.cos((phase-.72)*math.tau)+.18)/1.18))
        if self.late_sky:
            self.late_sky.set_alpha(int(night_strength * 76))
            screen.blit(self.late_sky, (0, 0))

        layers = self.layers[world]
        cloud_alpha = int(170 * (1 - max(0.0, (math.cos((phase-.72)*math.tau)+.18)/1.18)))
        wind_boost = 1.8 if event == "wind" else 1.0
        self._tile(screen, layers["clouds"], distance, SPEEDS["clouds"] * wind_boost, cloud_alpha, FLOOR)
        self._tile(screen, layers["mountains"], distance, SPEEDS["mountains"], 255, FLOOR)
        sway = math.sin(now * 1.8) * 3
        self._tile(screen, layers["trees"], distance, SPEEDS["trees"], 255, FLOOR, sway)
        self._tile(screen, layers["foreground"], distance, SPEEDS["foreground"], 255, FLOOR, math.sin(now * 3.2) * 2)
        # Fade into the next region across the final part of each section.
        region_progress = (distance % 1800) / 1800
        if region_progress > .88:
            blend = int(255 * (region_progress - .88) / .12)
            next_layers = self.layers[(world + 1) % len(self.layers)]
            for name in ("mountains", "trees", "foreground"):
                self._tile(screen, next_layers[name], distance, SPEEDS[name], blend, FLOOR)

        if night_strength > .05:
            for i, (x, y, size) in enumerate(self.stars):
                sx = (x + int(now * (1+i%3))) % WIDTH
                if math.sin(now*2+i) > -.3:
                    pygame.draw.circle(screen, (255, 243, 199), (sx, y), size)
            pygame.draw.circle(screen, (255, 241, 194), (790, 90), 30)
            pygame.draw.circle(screen, (49, 61, 99), (803, 79), 27)
        elif phase < .30 or phase > .84:
            sun_y = 105 + int(48 * math.sin(phase*math.tau))
            pygame.draw.circle(screen, (255, 224, 153), (790, sun_y), 33)

        if weather == "fog":
            self.fog.fill((190, 211, 216, 33))
            for i in range(4):
                x = int((now*12 + i*300) % (WIDTH+260))-130
                pygame.draw.ellipse(self.fog, (224, 235, 226, 34), (x, 255+i*23, 310, 90))
            screen.blit(self.fog, (0, 0))
        if weather in ("rain", "snow"):
            for p in self.weather_particles:
                p[0] += p[3] * .016
                p[1] += p[2] * .016
                if p[1] > FLOOR or p[0] < -10 or p[0] > WIDTH+10:
                    p[0], p[1] = random.randrange(WIDTH), random.randrange(-100, 0)
                x, y = int(p[0]), int(p[1])
                if weather == "rain":
                    pygame.draw.line(screen, (161, 204, 222), (x, y), (x-3, y+13), 1)
                else:
                    pygame.draw.circle(screen, (241, 247, 255), (x, y), 2)
        if event == "flock":
            for i in range(7):
                x = (WIDTH - int(now*90) + i*27) % WIDTH
                y = 118 + int(math.sin(now*8+i)*8)
                pygame.draw.arc(screen, (37, 54, 68), (x, y, 17, 9), 0, math.pi, 2)
        if event == "lightning" and self.last_event != "lightning":
            screen.blit(self.flash, (0, 0))
        self.last_event = event

    @staticmethod
    def _tile(screen: pygame.Surface, layer: pygame.Surface, distance: float, factor: float, alpha: int, bottom: int, sway: float = 0) -> None:
        layer.set_alpha(alpha)
        width = layer.get_width()
        offset = (int(distance * factor) + int(sway)) % width
        screen.blit(layer, (-offset, 0))
        screen.blit(layer, (width-offset, 0))
