"""A compact, asset-independent arcade runner built around a clear state machine."""

from __future__ import annotations

import math
import random
from pathlib import Path

import pygame

from .save_manager import SaveManager
from .systems.parallax import ParallaxSystem

WIDTH, HEIGHT, FLOOR = 960, 540, 420
INK = (26, 29, 48)
CREAM = (255, 245, 218)
MINT = (109, 226, 177)
GOLD = (255, 206, 91)
PINK = (255, 111, 143)


class PixelEra:
    """Owns the game loop and delegates persistence/audio/assets to small systems."""

    def __init__(self) -> None:
        pygame.init()
        try:
            pygame.mixer.init()
        except pygame.error:
            pass
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("PIXEL ERA — RUN. EXPLORE. SURVIVE.")
        self.clock = pygame.time.Clock()
        self.root = Path(__file__).resolve().parent.parent
        self.save = SaveManager()
        self.data = self.save.data
        self.fonts = {size: self._font(size) for size in (16, 18, 20, 22, 24, 30, 38, 52, 70)}
        self.images = self._load_images()
        self.parallax = ParallaxSystem(self.root)
        self.sounds = self._load_sounds()
        self.state = "menu"
        self.page = "main"
        self.running = True
        self.ticks = 0.0
        self.menu_time = 0.0
        self.buttons: list[tuple[pygame.Rect, str, str]] = []
        self.message = ""
        self.message_until = 0.0
        self.reset_run()

    def _font(self, size: int) -> pygame.font.Font:
        # A common bold sans serif stays crisp and readable at every UI size.
        return pygame.font.SysFont("Arial", size, bold=True)

    def _image(self, name: str, size: tuple[int, int] | None = None) -> pygame.Surface | None:
        try:
            image = pygame.image.load(str(self.root / "graphics" / name)).convert_alpha()
            return pygame.transform.smoothscale(image, size) if size else image
        except (OSError, pygame.error):
            return None

    def _load_images(self) -> dict[str, pygame.Surface | None]:
        return {
            "stand": self._image("player_stand.png", (58, 72)),
            "walk1": self._image("player_walk_1.png"), "walk2": self._image("player_walk_2.png"),
            "jump": self._image("jump.png"), "snail1": self._image("snail1.png", (56, 30)),
            "snail2": self._image("snail2.png", (56, 30)), "fly1": self._image("Fly1.png", (46, 28)),
            "fly2": self._image("Fly2.png", (46, 28)), "pause": self._image("pause-button.png", (42, 42)),
        }

    def _load_sounds(self) -> dict[str, pygame.mixer.Sound]:
        result: dict[str, pygame.mixer.Sound] = {}
        if pygame.mixer.get_init():
            for key, file in (("jump", "jump.mp3"), ("hit", "collision.mp3")):
                try:
                    sound = pygame.mixer.Sound(str(self.root / "audio" / file))
                    result[key] = sound
                except (OSError, pygame.error):
                    pass
            try:
                pygame.mixer.music.load(str(self.root / "audio" / "music.wav"))
                pygame.mixer.music.set_volume(float(self.data["settings"].get("music_volume", .3)))
                if self.data["settings"].get("music", True):
                    pygame.mixer.music.play(-1)
            except (OSError, pygame.error):
                pass
        return result

    def sound(self, name: str) -> None:
        if self.data["settings"].get("sfx", True) and name in self.sounds:
            self.sounds[name].set_volume(float(self.data["settings"].get("sfx_volume", .8)))
            self.sounds[name].play()

    def reset_run(self) -> None:
        self.player = pygame.Rect(118, FLOOR - 62, 46, 62)
        self.vy = 0.0
        self.obstacles: list[dict[str, object]] = []
        self.coins: list[pygame.Rect] = []
        self.powerups: list[pygame.Rect] = []
        self.particles: list[list[float | tuple[int, int, int]]] = []
        self.distance = 0.0
        self.run_score = 0
        self.run_coins = 0
        self.best_combo_run = 0
        self.combo = 0
        self.combo_time = 0.0
        self.spawn_after = 1.0
        self.coin_timer = 0.8
        self.power_timer = 14.0
        self.shield = False
        self.magnet = 0.0
        self.slow = 0.0
        self.boost = 0.0
        self.multiplier = 0.0
        self.invulnerable = 0.0
        self.hit_reason = ""
        self.world_notice_until = 0.0
        self.last_world = -1
        self.weather = "clear"
        self.weather_timer = random.uniform(12, 18)
        self.world_event = ""
        self.event_timer = random.uniform(18, 28)
        self.event_left = 0.0
        self.shake_until = 0.0

    @property
    def speed(self) -> float:
        return min(12.5, 5.0 + self.distance / 1400.0) * (1.35 if self.boost > 0 else 1.0)

    @property
    def world_index(self) -> int:
        return int(self.distance // 1800) % 4

    @property
    def world_name(self) -> str:
        return ("GRASSLAND", "SUNSET", "MOONLIT GROVE", "NEON RUINS")[self.world_index]

    def begin_run(self) -> None:
        self.reset_run()
        self.data["stats"]["runs"] += 1
        self.save.write()
        self.state = "playing"

    def finish_run(self, reason: str) -> None:
        self.sound("hit")
        self.shake_until = self.ticks + .22
        self.hit_reason = reason
        self.state = "game_over"
        self.data["coins"] += self.run_coins
        self.data["stats"]["coins"] += self.run_coins
        self.data["stats"]["distance"] += int(self.distance)
        self.data["stats"]["best_combo"] = max(self.data["stats"]["best_combo"], self.best_combo_run)
        self.data["high_score"] = max(self.data["high_score"], self.run_score)
        self.unlock("First Steps", self.data["stats"]["runs"] >= 1)
        self.unlock("Pocket Change", self.data["stats"]["coins"] >= 100)
        self.unlock("Night Runner", self.distance >= 5400)
        self.unlock("Untouchable", self.distance >= 3000 and self.combo >= 15)
        self.save.write()

    def unlock(self, name: str, condition: bool) -> None:
        if condition and name not in self.data["achievements"]:
            self.data["achievements"].append(name)

    def jump(self) -> None:
        if self.player.bottom >= FLOOR - 1:
            self.vy = -710
            self.sound("jump")
            self.burst(self.player.centerx, FLOOR, MINT, 8)

    def add_coin_pattern(self) -> None:
        x = WIDTH + 45
        pattern = random.choice(("line", "arc", "steps"))
        for i in range(5 if pattern == "line" else 6):
            if pattern == "line":
                y = FLOOR - random.choice((76, 92, 108))
                offset = i * 43
            elif pattern == "arc":
                y = FLOOR - 76 - int(math.sin(i / 5 * math.pi) * 85)
                offset = i * 42
            else:
                y = FLOOR - 62 - (i % 3) * 38
                offset = i * 42
            self.coins.append(pygame.Rect(x + offset, y, 22, 22))

    def spawn_obstacle_pattern(self, level: float) -> None:
        """Choose a readable pattern with generous space after each sequence."""
        choices = ["single_ground", "single_ground", "single_flyer"]
        if self.distance > 800:
            choices.extend(("ground_pair", "coin_challenge"))
        if self.distance > 2200:
            choices.append("rapid_pair")
        pattern = random.choice(choices)

        def add(x: int, flying: bool = False) -> None:
            height = 29 if flying else 34
            # Flyers sit high enough to run below, encouraging jump timing choices.
            y = FLOOR - random.choice((138, 152, 166)) if flying else FLOOR - height
            self.obstacles.append({"rect": pygame.Rect(x, y, 48 if flying else 56, height), "flying": flying, "cleared": False})

        add(WIDTH + 30, flying=pattern == "single_flyer")
        if pattern in ("ground_pair", "rapid_pair"):
            gap = 280 if pattern == "ground_pair" else 205
            add(WIDTH + 30 + gap)
            self.spawn_after = random.uniform(2.2, 2.7) - .25 * level
        elif pattern == "coin_challenge":
            # Jumping the enemy opens a high coin arc; staying grounded is safer.
            for i in range(6):
                y = FLOOR - 88 - int(math.sin(i / 5 * math.pi) * 92)
                self.coins.append(pygame.Rect(WIDTH + 210 + i * 42, y, 22, 22))
            self.spawn_after = random.uniform(1.45, 1.8) - .15 * level
        else:
            self.spawn_after = random.uniform(1.15, 1.6) - .2 * level

    def update_atmosphere(self, dt: float) -> None:
        self.weather_timer -= dt
        if self.weather_timer <= 0:
            options = ["clear", "clear", "rain", "fog"]
            if self.world_index in (2, 3):
                options.append("snow")
            self.weather = random.choice(options)
            self.weather_timer = random.uniform(16, 25)
            if self.weather != "clear":
                self.toast(f"{self.weather.upper()} ROLLING IN", 1.7)

        self.event_timer -= dt
        if self.event_left > 0:
            self.event_left = max(0.0, self.event_left - dt)
            if self.event_left == 0:
                self.world_event = ""
        if self.event_timer <= 0:
            self.world_event = random.choice(("flock", "lightning", "wind", "bonus"))
            self.event_left = random.uniform(3.5, 5.0)
            self.event_timer = random.uniform(24, 38)
            if self.world_event == "bonus":
                self.add_coin_pattern()
                self.toast("BONUS COIN FLIGHT!", 2.0)
            elif self.world_event == "flock":
                self.toast("A FLOCK PASSES OVERHEAD", 1.8)

    def burst(self, x: float, y: float, color: tuple[int, int, int], count: int) -> None:
        for _ in range(count):
            self.particles.append([x, y, random.uniform(-100, 100), random.uniform(-160, 20), random.uniform(.25, .65), color])

    def update(self, dt: float) -> None:
        self.menu_time += dt
        if self.state != "playing":
            return
        self.distance += self.speed * dt * 14
        self.run_score = int(self.distance / 8) + self.run_coins * 10 * (2 if self.multiplier > 0 else 1)
        if self.world_index != self.last_world:
            self.last_world = self.world_index
            self.world_notice_until = self.ticks + 2.6
            if self.weather == "snow" and self.world_index not in (2, 3):
                self.weather = "clear"
        self.update_atmosphere(dt)
        self.vy += 1850 * dt
        self.player.y += int(self.vy * dt)
        if self.player.bottom >= FLOOR:
            if self.vy > 260:
                self.burst(self.player.centerx, FLOOR, (204, 224, 200), 5)
            self.player.bottom = FLOOR
            self.vy = 0
        self.spawn_after -= dt
        if self.spawn_after <= 0:
            level = min(1.0, self.distance / 10000)
            self.spawn_obstacle_pattern(level)
        self.coin_timer -= dt
        if self.coin_timer <= 0:
            self.add_coin_pattern()
            self.coin_timer = random.uniform(2.5, 4.2)
        self.power_timer -= dt
        if self.power_timer <= 0:
            self.powerups.append(pygame.Rect(WIDTH + 40, FLOOR - random.choice((100, 135, 165)), 30, 30))
            self.power_timer = random.uniform(18, 25)
        active_speed = self.speed * (0.62 if self.slow > 0 else 1)
        for obstacle in self.obstacles:
            rect = obstacle["rect"]
            rect.x -= int(active_speed * 60 * dt)
            if not obstacle["cleared"] and rect.right < self.player.left:
                obstacle["cleared"] = True
                self.combo += 1
                self.combo_time = 3.5
                self.best_combo_run = max(self.best_combo_run, self.combo)
                self.data["stats"]["avoided"] += 1
            if rect.colliderect(self.player) and self.invulnerable <= 0:
                if self.shield:
                    self.shield = False
                    self.invulnerable = 1.25
                    self.burst(rect.centerx, rect.centery, MINT, 18)
                    rect.x = -200
                    self.combo = 0
                else:
                    self.finish_run("A little too close to the action")
                    return
        self.obstacles = [o for o in self.obstacles if o["rect"].right > -20]
        for coin in self.coins:
            coin.x -= int(active_speed * 60 * dt)
            if self.magnet > 0 and coin.centerx < 440:
                coin.x += int((self.player.centerx - coin.centerx) * min(.12, dt * 3))
                coin.y += int((self.player.centery - coin.centery) * min(.12, dt * 3))
            if coin.colliderect(self.player):
                self.run_coins += 1
                self.combo += 1
                self.combo_time = 3.5
                self.best_combo_run = max(self.best_combo_run, self.combo)
                self.burst(coin.centerx, coin.centery, GOLD, 5)
                coin.x = -100
        self.coins = [c for c in self.coins if c.x > -40]
        for power in self.powerups:
            power.x -= int(active_speed * 60 * dt)
            if power.colliderect(self.player):
                effect = random.choice(("shield", "magnet", "slow", "multiplier"))
                if effect == "shield":
                    self.shield = True
                elif effect == "magnet":
                    self.magnet = 8
                elif effect == "slow":
                    self.slow = 6
                else:
                    self.multiplier = 8
                self.data["stats"]["powerups"] += 1
                self.burst(power.centerx, power.centery, MINT, 14)
                power.x = -100
                self.toast(f"{effect.upper()} ACTIVATED", 1.5)
        self.powerups = [p for p in self.powerups if p.x > -40]
        for name in ("magnet", "slow", "boost", "multiplier", "invulnerable"):
            setattr(self, name, max(0.0, getattr(self, name) - dt))
        self.combo_time -= dt
        if self.combo_time <= 0:
            self.combo = 0
        for particle in self.particles:
            particle[0] = float(particle[0]) + float(particle[2]) * dt
            particle[1] = float(particle[1]) + float(particle[3]) * dt
            particle[3] = float(particle[3]) + 260 * dt
            particle[4] = float(particle[4]) - dt
        self.particles = [p for p in self.particles if float(p[4]) > 0]

    def toast(self, text: str, duration: float) -> None:
        self.message = text
        self.message_until = self.ticks + duration

    def event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
            return
        if event.type == pygame.KEYDOWN:
            if self.state == "playing":
                if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                    self.jump()
                elif event.key == pygame.K_ESCAPE:
                    self.state = "paused"
            elif self.state == "paused":
                if event.key in (pygame.K_ESCAPE, pygame.K_SPACE):
                    self.state = "playing"
                elif event.key == pygame.K_r:
                    self.begin_run()
                elif event.key == pygame.K_m:
                    self.state = "menu"
            elif event.key == pygame.K_ESCAPE:
                if self.state in ("shop", "achievements", "settings", "stats"):
                    self.state, self.page = "menu", "main"
                elif self.state in ("game_over",):
                    self.state = "menu"
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.state == "menu":
                    if self.page == "main":
                        self.begin_run()
                    else:
                        self.state, self.page = "menu", "main"
                elif self.state == "game_over":
                    self.begin_run()
            if self.state == "settings" and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                self.adjust_setting(-1 if event.key == pygame.K_LEFT else 1)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, action, label in self.buttons:
                if rect.collidepoint(event.pos):
                    self.sound("click")
                    self.activate(action)
                    break

    def adjust_setting(self, direction: int) -> None:
        settings = self.data["settings"]
        settings["music_volume"] = min(1.0, max(0.0, settings.get("music_volume", .3) + direction * .05))
        settings["sfx_volume"] = min(1.0, max(0.0, settings.get("sfx_volume", .8) + direction * .05))
        self.save.write()

    def activate(self, action: str) -> None:
        if action == "play":
            self.begin_run()
        elif action == "pause":
            self.state = "paused"
        elif action == "resume":
            self.state = "playing"
        elif action == "restart":
            self.begin_run()
        elif action == "main":
            self.state, self.page = "menu", "main"
        elif action in ("shop", "achievements", "settings", "stats"):
            self.state, self.page = action, action
        elif action == "back":
            self.state, self.page = "menu", "main"
        elif action == "music":
            self.data["settings"]["music"] = not self.data["settings"].get("music", True)
            if pygame.mixer.get_init():
                if self.data["settings"]["music"]:
                    pygame.mixer.music.unpause()
                else:
                    pygame.mixer.music.pause()
            self.save.write()
        elif action == "sfx":
            self.data["settings"]["sfx"] = not self.data["settings"].get("sfx", True)
            self.save.write()
        elif action.startswith("buy:"):
            self.buy(action[4:])
        elif action == "quit":
            self.running = False

    def buy(self, item: str) -> None:
        prices = {"ninja": 150, "robot": 350, "astronaut": 600, "blue trail": 100, "gold trail": 250}
        cost = prices[item]
        if item in self.data["unlocked"]:
            self.data["selected"] = item
            self.toast(f"{item.upper()} SELECTED", 1.4)
        elif self.data["coins"] >= cost:
            self.data["coins"] -= cost
            self.data["unlocked"].append(item)
            self.data["selected"] = item
            self.toast(f"{item.upper()} UNLOCKED", 1.4)
        else:
            self.toast("NOT ENOUGH COINS YET", 1.4)
        self.save.write()

    def text(self, value: str, size: int, color: tuple[int, int, int], pos: tuple[int, int], center: bool = False) -> pygame.Rect:
        available = WIDTH - 40 if center else WIDTH - pos[0] - 20
        candidates = [font_size for font_size in sorted(self.fonts, reverse=True) if font_size <= size]
        fitted_size = next((font_size for font_size in candidates if self.fonts[font_size].size(value)[0] <= available), min(candidates))
        if self.fonts[fitted_size].size(value)[0] > available:
            clipped = value
            while clipped and self.fonts[fitted_size].size(clipped + "…")[0] > available:
                clipped = clipped[:-1]
            value = clipped + "…" if clipped else "…"
        surface = self.fonts[fitted_size].render(value, True, color)
        rect = surface.get_rect(center=pos) if center else surface.get_rect(topleft=pos)
        shadow = self.fonts[fitted_size].render(value, True, (16, 20, 34))
        self.screen.blit(shadow, rect.move(1, 2))
        self.screen.blit(surface, rect)
        return rect

    def panel(self, rect: pygame.Rect, color: tuple[int, int, int, int] = (25, 31, 55, 218), radius: int = 15) -> None:
        layer = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(layer, color, layer.get_rect(), border_radius=radius)
        pygame.draw.rect(layer, (255, 255, 255, 30), layer.get_rect(), 1, border_radius=radius)
        self.screen.blit(layer, rect)

    def button(self, label: str, action: str, rect: pygame.Rect, primary: bool = False) -> None:
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        fill = (82, 217, 166, 245) if primary else ((91, 105, 143, 240) if hovered else (51, 62, 96, 230))
        self.panel(rect, fill, 12)
        color = INK if primary else CREAM
        label_size = next((size for size in (24, 20, 16) if self.fonts[size].size(label)[0] <= rect.width - 20), 16)
        self.text(label, label_size, color, rect.center, True)
        self.buttons.append((rect, action, label))

    def draw_background(self, now: float) -> None:
        world = self.world_index if self.state in ("playing", "paused", "game_over") else 0
        phase = (self.distance % 7200) / 7200 if self.state in ("playing", "paused", "game_over") else (now % 90) / 90
        camera = self.distance if self.state in ("playing", "paused", "game_over") else now * 42
        self.parallax.draw(self.screen, camera, now, world, phase, self.weather, self.world_event if self.event_left > 0 else "")
        pygame.draw.rect(self.screen, (43, 55, 69) if world == 3 else (74, 112, 86), (0, FLOOR, WIDTH, HEIGHT-FLOOR))
        pygame.draw.line(self.screen, (MINT if world == 3 else (165, 201, 125)), (0, FLOOR), (WIDTH, FLOOR), 4)
        for x in range(-10, WIDTH, 48):
            xx = (x - int(self.distance * 3) % 48) if self.state in ("playing", "paused", "game_over") else x
            pygame.draw.line(self.screen, (105, 119, 102), (xx, FLOOR+22), (xx+18, FLOOR+22), 2)

    def draw_player(self, now: float) -> None:
        if self.invulnerable > 0 and int(now * 16) % 2:
            return
        selected = self.data.get("selected", "runner")
        sprite = self.images["jump"] if self.player.bottom < FLOOR else self.images["walk1" if int(now * 10) % 2 == 0 else "walk2"]
        if sprite and selected == "runner":
            self.screen.blit(sprite, sprite.get_rect(midbottom=self.player.midbottom))
        else:
            color = {"ninja": (31, 34, 52), "robot": (117, 173, 213), "astronaut": (236, 228, 211)}.get(selected, (88, 214, 164))
            pygame.draw.rect(self.screen, color, self.player, border_radius=8)
            pygame.draw.rect(self.screen, (32, 42, 64), (self.player.x+8, self.player.y+12, 28, 12), border_radius=5)
            pygame.draw.circle(self.screen, GOLD, (self.player.x+32, self.player.y+18), 3)
        if self.shield:
            pygame.draw.circle(self.screen, (122, 228, 238), self.player.center, 39, 2)

    def draw_game(self, now: float) -> None:
        self.draw_background(now)
        for coin in self.coins:
            pygame.draw.circle(self.screen, (125, 81, 27), coin.center, 13)
            pygame.draw.circle(self.screen, GOLD, coin.center, 10)
            pygame.draw.line(self.screen, (255, 243, 178), (coin.centerx, coin.top+5), (coin.centerx, coin.bottom-5), 2)
        for power in self.powerups:
            pygame.draw.rect(self.screen, (64, 220, 200), power, border_radius=8)
            self.text("+", 24, INK, power.center, True)
        for obstacle in self.obstacles:
            rect = obstacle["rect"]
            if obstacle["flying"]:
                sprite = self.images["fly1" if int(now*8)%2 == 0 else "fly2"]
            else:
                sprite = self.images["snail1" if int(now*3)%2 == 0 else "snail2"]
            if sprite:
                self.screen.blit(sprite, sprite.get_rect(midbottom=rect.midbottom))
            elif obstacle["flying"]:
                pygame.draw.ellipse(self.screen, PINK, rect)
            else:
                pygame.draw.rect(self.screen, (148, 96, 111), rect, border_radius=9)
        self.draw_player(now)
        for x, y, _, _, life, color in self.particles:
            pygame.draw.circle(self.screen, color, (int(x), int(y)), max(1, int(4 * min(1, float(life)*2))))
        self.panel(pygame.Rect(24, 20, 335, 74), (24, 32, 52, 205))
        self.text(f"SCORE  {self.run_score:06d}", 30, CREAM, (43, 30))
        self.text(f"● {self.run_coins}     COMBO x{max(1, self.combo//4+1)}", 20, GOLD, (44, 62))
        self.panel(pygame.Rect(718, 20, 220, 74), (24, 32, 52, 205))
        self.text(self.world_name, 20, MINT, (828, 42), True)
        phase = (self.distance % 7200) / 7200
        sky_stage = ("DAY", "SUNSET", "TWILIGHT", "NIGHT", "DAWN")[min(4, int(phase * 5))]
        self.text(f"BEST {self.data['high_score']}  ·  {sky_stage}", 16, CREAM, (828, 69), True)
        if self.images["pause"]:
            self.screen.blit(self.images["pause"], (902, 99))
        else:
            self.button("Ⅱ", "pause", pygame.Rect(902, 99, 42, 42))
        status = []
        if self.shield: status.append("SHIELD")
        if self.magnet: status.append(f"MAGNET {self.magnet:.0f}s")
        if self.slow: status.append(f"SLOW {self.slow:.0f}s")
        if self.multiplier: status.append(f"2X SCORE {self.multiplier:.0f}s")
        if status:
            self.panel(pygame.Rect(24, 104, 220, 32), (24, 32, 52, 195), 9)
            self.text("  •  ".join(status), 16, MINT, (33, 112))
        if self.ticks < self.world_notice_until:
            self.panel(pygame.Rect(308, 105, 344, 50), (24, 32, 52, 210))
            self.text(f"WORLD DISCOVERED  ·  {self.world_name}", 20, GOLD, (480, 130), True)
        if self.ticks < self.message_until:
            self.panel(pygame.Rect(340, 169, 280, 44), (25, 31, 55, 235))
            self.text(self.message, 20, MINT, (480, 191), True)

    def draw_menu(self, now: float) -> None:
        self.draw_background(now)
        # Decorative pixel motes and animated logo/character.
        for i in range(24):
            x = (i*83 + int(now*(12+i%4))) % WIDTH
            y = 110 + (i*47) % 300
            pygame.draw.circle(self.screen, (190, 239, 207), (x, y), 1+(i%3==0))
        self.panel(pygame.Rect(200, 28, 560, 468), (25, 31, 55, 218), 24)
        self.text("PIXEL ERA", 70, CREAM, (480, 84 + int(math.sin(now*2)*3)), True)
        pygame.draw.line(self.screen, MINT, (348, 126), (612, 126), 3)
        self.text("RUN  ·  EXPLORE  ·  SURVIVE", 20, MINT, (480, 146), True)
        idle_y = 206 + int(math.sin(now*3)*5)
        self.screen.blit(self.images["stand"], self.images["stand"].get_rect(center=(480, idle_y))) if self.images["stand"] else pygame.draw.rect(self.screen, MINT, (458, idle_y-28, 44, 58), border_radius=8)
        self.buttons = []
        if self.page == "main":
            self.button("▶   PLAY", "play", pygame.Rect(355, 244, 250, 46), True)
            self.button("PIXEL SHOP", "shop", pygame.Rect(250, 301, 220, 40))
            self.button("RECORDS", "stats", pygame.Rect(490, 301, 220, 40))
            self.button("ACHIEVEMENTS", "achievements", pygame.Rect(250, 348, 220, 40))
            self.button("SETTINGS", "settings", pygame.Rect(490, 348, 220, 40))
            self.text(f"BEST RUN   {self.data['high_score']}     •     COINS   {self.data['coins']}", 20, GOLD, (480, 466), True)
            self.text("SPACE TO PLAY   ·   SPACE / ↑ TO JUMP   ·   ESC TO PAUSE", 16, CREAM, (480, 518), True)
        else:
            self.draw_page()

    def draw_page(self) -> None:
        self.buttons = []
        title = {"shop": "PIXEL SHOP", "achievements": "ACHIEVEMENTS", "settings": "SETTINGS", "stats": "RUN RECORDS"}.get(self.page, "")
        self.text(title, 38, GOLD, (480, 241), True)
        self.button("← BACK", "back", pygame.Rect(372, 443, 216, 42))
        if self.page == "shop":
            self.text(f"AVAILABLE COINS: {self.data['coins']}", 24, CREAM, (480, 277), True)
            items = (("ninja",150),("robot",350),("astronaut",600),("blue trail",100),("gold trail",250))
            for i, (name, price) in enumerate(items):
                row = pygame.Rect(310, 300 + i*28, 340, 25)
                owned = name in self.data["unlocked"]
                label = f"{name.upper()}  ·  {'SELECTED' if self.data['selected']==name else ('OWNED' if owned else str(price)+' COINS')}"
                self.text(label, 16, MINT if owned else CREAM, row.center, True)
                self.buttons.append((row, f"buy:{name}", label))
        elif self.page == "achievements":
            names = ("FIRST STEPS", "POCKET CHANGE · 100 COINS", "NIGHT RUNNER", "UNTOUCHABLE")
            self.text("Persistent milestones from your runs", 20, CREAM, (480, 278), True)
            for i, name in enumerate(names):
                unlocked = any(a.upper() in name for a in self.data["achievements"])
                self.text(("✓  " if unlocked else "○  ")+name, 20, MINT if unlocked else CREAM, (344, 314+i*31))
        elif self.page == "settings":
            self.text(f"MUSIC   {'ON' if self.data['settings']['music'] else 'OFF'}", 22, CREAM, (480, 293), True)
            self.button("TOGGLE MUSIC", "music", pygame.Rect(374, 309, 212, 35))
            self.button("TOGGLE SFX", "sfx", pygame.Rect(374, 351, 212, 35))
            self.text(f"MUSIC {int(self.data['settings']['music_volume']*100)}%   ·   SFX {int(self.data['settings']['sfx_volume']*100)}%", 18, CREAM, (480, 405), True)
            self.text("← / → ADJUST BOTH VOLUMES", 16, MINT, (480, 429), True)
        elif self.page == "stats":
            stats = self.data["stats"]
            entries = (("TOTAL RUNS", stats["runs"]), ("TOTAL DISTANCE", stats["distance"]), ("COINS EARNED", stats["coins"]), ("BEST COMBO", stats["best_combo"]), ("ENEMIES AVOIDED", stats["avoided"]), ("POWER-UPS FOUND", stats["powerups"]))
            for i, (label, value) in enumerate(entries):
                self.text(f"{label:<19}  {value}", 18, CREAM, (360, 280+i*25))

    def draw_overlay(self, title: str, lines: list[str], actions: list[tuple[str, str]]) -> None:
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((9, 12, 25, 172))
        self.screen.blit(shade, (0, 0))
        self.panel(pygame.Rect(300, 60, 360, 420), (25, 31, 55, 245), 22)
        self.text(title, 52, CREAM, (480, 112), True)
        for i, line in enumerate(lines):
            self.text(line, 20, GOLD if i == 0 else CREAM, (480, 184+i*34), True)
        self.buttons = []
        button_start = 204 + len(lines) * 34
        for i, (label, action) in enumerate(actions):
            self.button(label, action, pygame.Rect(361, button_start+i*48, 238, 40), i == 0)

    def draw(self, now: float) -> None:
        self.buttons = []
        if self.state == "playing":
            self.draw_game(now)
            # Main pause control gets a reliable mouse hit box.
            self.buttons.append((pygame.Rect(902, 99, 42, 42), "pause", "pause"))
        elif self.state in ("menu", "shop", "achievements", "settings", "stats"):
            self.draw_menu(now)
        elif self.state == "paused":
            self.draw_game(now)
            self.draw_overlay("PAUSED", ["YOUR RUN IS WAITING"], [("▶  RESUME", "resume"), ("RESTART RUN", "restart"), ("MAIN MENU", "main")])
        elif self.state == "game_over":
            self.draw_game(now)
            self.draw_overlay("RUN OVER", [self.hit_reason, f"SCORE   {self.run_score}", f"HIGH SCORE   {self.data['high_score']}", f"COINS EARNED   +{self.run_coins}   ·   BEST COMBO x{self.best_combo_run}"], [("▶  RUN IT BACK", "restart"), ("MAIN MENU", "main")])
        if now < self.shake_until:
            frame = self.screen.copy()
            self.screen.fill((12, 15, 27))
            self.screen.blit(frame, (random.randint(-4, 4), random.randint(-3, 3)))
        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            dt = min(self.clock.tick(60) / 1000.0, .04)
            self.ticks += dt
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and self.state == "paused" and event.key == pygame.K_ESCAPE:
                    self.state = "playing"
                else:
                    self.event(event)
            if self.state == "playing":
                self.update(dt)
            self.draw(self.ticks)
        self.save.write()
        pygame.quit()
