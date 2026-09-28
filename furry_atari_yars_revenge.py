#!/usr/bin/env python3
"""
===============================================================================
       YAR'S REVENGE: ANTHRO EDITION (Atari 1982 Tribute - v2.0)
       A Furry Retro Arcade Homage to Howard Scott Warshaw's Classic
       Controls: Mouse (Follow & Left Click) OR Keyboard (WASD/Arrows & Space)
       by Thomas B. Sweet (Anthro Entertainment LLC) using Gemini 3.8 Flash
===============================================================================
"""

import sys
import math
import random
import pygame
import numpy as np

# Initialize Pygame & Mixer
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

WIDTH, HEIGHT = 880, 580
FPS = 60
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Yar's Revenge: Anthro Edition (Mouse & Keyboard)")
CLOCK = pygame.time.Clock()

# Colors (Authentic Atari TIA Palette)
C_BLACK    = (10, 8, 16)
C_WHITE    = (255, 255, 255)
C_GOLD     = (255, 226, 138)
C_PURPLE   = (160, 60, 220)
C_CYAN     = (40, 220, 240)
C_RED      = (240, 50, 60)
C_ORANGE   = (255, 140, 40)
C_GREEN    = (80, 230, 110)
C_FUR_BODY = (235, 150, 90)
C_FUR_BELLY= (255, 220, 180)
C_EAR_IN   = (255, 140, 170)
C_WING     = (90, 40, 130)


# =============================================================================
# PROCEDURAL 8-BIT ATARI SOUND SYNTHESIZER
# =============================================================================

def synth_sound(freq_func, duration, volume=0.35, noise=False):
    sr = 22050
    n_samples = int(sr * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    if noise:
        samples = np.random.uniform(-1.0, 1.0, n_samples)
    else:
        freqs = freq_func(t)
        phase = 2.0 * np.pi * np.cumsum(freqs) / sr
        samples = np.sign(np.sin(phase)) * 0.7 + np.sin(phase * 0.5) * 0.3

    env = np.linspace(1.0, 0.0, n_samples) ** 1.5
    audio = (samples * env * volume * 32767).astype(np.int16)

    # Stereo / Mono Hardware Guard
    mixer_init = pygame.mixer.get_init()
    channels = mixer_init[2] if mixer_init else 1
    if channels == 2:
        audio = np.column_stack((audio, audio))

    return pygame.sndarray.make_sound(np.ascontiguousarray(audio))

SND_CHOMP = synth_sound(lambda t: 200 + t * 400, 0.06, volume=0.25)
SND_LASER = synth_sound(lambda t: 900 - t * 2400, 0.12, volume=0.3)
SND_ZORLON_ARMED = synth_sound(lambda t: 300 + np.sin(t * 40) * 150, 0.4, volume=0.35)
SND_ZORLON_FIRE = synth_sound(lambda t: 1400 - t * 1800, 0.45, volume=0.55)
SND_SWIRL = synth_sound(lambda t: 400 + np.sin(t * 70) * 260, 0.3, volume=0.4)
SND_BOOM = synth_sound(lambda t: 80, 0.6, volume=0.5, noise=True)


# =============================================================================
# GAME ENTITIES
# =============================================================================

class AnthroYar:
    """The player: Animated winged bat-fox hero."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 4.8
        self.w = 26
        self.h = 24
        self.wing_timer = 0.0
        self.nibble_count = 0
        self.alive = True
        self.respawn_timer = 0

    def update(self, keys, mouse_pos, mouse_active):
        if not self.alive:
            self.respawn_timer -= 1
            if self.respawn_timer <= 0:
                self.respawn()
            return

        dx, dy = 0, 0

        # Keyboard Movement
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:  dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:    dy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:  dy += 1

        if dx != 0 or dy != 0:
            if dx != 0 and dy != 0:
                dx *= 0.707
                dy *= 0.707
            self.x += dx * self.speed
            self.y += dy * self.speed
        elif mouse_active:
            # Smoothly follow mouse
            mx, my = mouse_pos
            target_x = max(10, min(WIDTH - 190, mx))
            target_y = max(50, min(HEIGHT - 65, my))
            dist = math.hypot(target_x - self.x, target_y - self.y)
            if dist > 4:
                move_step = min(dist, self.speed * 1.25)
                angle = math.atan2(target_y - self.y, target_x - self.x)
                self.x += math.cos(angle) * move_step
                self.y += math.sin(angle) * move_step

        self.x = max(10, min(WIDTH - 190, self.x))
        self.y = max(50, min(HEIGHT - 65, self.y))
        self.wing_timer += 0.25

    def respawn(self):
        self.x = 100
        self.y = HEIGHT // 2
        self.alive = True
        self.nibble_count = 0

    def draw(self, surf):
        if not self.alive:
            return

        cx, cy = int(self.x), int(self.y)
        flap = math.sin(self.wing_timer) * 8

        # 1. Bat-Wings
        wing_l = [(cx - 4, cy), (cx - 18, cy - 12 + flap), (cx - 12, cy + 8)]
        wing_r = [(cx + 4, cy), (cx + 18, cy - 12 - flap), (cx + 12, cy + 8)]
        pygame.draw.polygon(surf, C_WING, wing_l)
        pygame.draw.polygon(surf, C_WING, wing_r)

        # 2. Fluffy Fox Tail
        tail_tip = (cx - 14, cy + 10 + math.sin(self.wing_timer * 0.7) * 4)
        pygame.draw.circle(surf, C_FUR_BODY, (int(tail_tip[0]), int(tail_tip[1])), 6)
        pygame.draw.circle(surf, C_WHITE, (int(tail_tip[0] - 2), int(tail_tip[1] + 1)), 3)

        # 3. Anthro Body & Head
        pygame.draw.ellipse(surf, C_FUR_BODY, (cx - 8, cy - 8, 16, 18))
        pygame.draw.ellipse(surf, C_FUR_BELLY, (cx - 4, cy - 4, 8, 12))

        # 4. Pointy Ears
        pygame.draw.polygon(surf, C_FUR_BODY, [(cx - 6, cy - 8), (cx - 10, cy - 18), (cx - 2, cy - 10)])
        pygame.draw.polygon(surf, C_EAR_IN,   [(cx - 5, cy - 8), (cx - 8, cy - 15), (cx - 3, cy - 10)])
        pygame.draw.polygon(surf, C_FUR_BODY, [(cx + 2, cy - 10), (cx + 10, cy - 18), (cx + 6, cy - 8)])
        pygame.draw.polygon(surf, C_EAR_IN,   [(cx + 3, cy - 10), (cx + 8, cy - 15), (cx + 5, cy - 8)])

        # 5. Glowing Eyes & Cute Snout
        eye_color = C_CYAN if (cx % 8 < 4) else C_WHITE
        pygame.draw.circle(surf, eye_color, (cx + 3, cy - 4), 2)
        pygame.draw.circle(surf, C_BLACK, (cx + 7, cy - 2), 2)


class PlayerMissile:
    """The regular energy bolt fired forward by Yar."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 13.0
        self.active = True

    def update(self):
        self.x += self.speed
        if self.x > WIDTH - 50:
            self.active = False

    def draw(self, surf):
        cx, cy = int(self.x), int(self.y)
        pygame.draw.line(surf, C_CYAN, (cx - 10, cy), (cx + 8, cy), 3)
        pygame.draw.circle(surf, C_WHITE, (cx + 8, cy), 3)


class EnergyBarrier:
    """The pulsating cellular shield protecting the Qotile."""
    def __init__(self, start_x, start_y, cols=6, rows=28):
        self.start_x = start_x
        self.start_y = start_y
        self.cols = cols
        self.rows = rows
        self.cell_w = 12
        self.cell_h = 14
        self.grid = np.ones((rows, cols), dtype=bool)
        self.anim_offset = 0

    def update(self):
        self.anim_offset = (self.anim_offset + 1) % 60

    def draw(self, surf):
        palettes = [C_GOLD, C_ORANGE, C_PURPLE, C_CYAN, C_GREEN]
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r, c]:
                    bx = self.start_x + c * (self.cell_w + 2)
                    by = self.start_y + r * (self.cell_h + 2)
                    col = palettes[(r + c + self.anim_offset // 6) % len(palettes)]
                    pygame.draw.rect(surf, col, (bx, by, self.cell_w, self.cell_h), border_radius=2)

    def check_nibble(self, px, py, radius=12):
        nibbled = 0
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r, c]:
                    bx = self.start_x + c * (self.cell_w + 2) + self.cell_w // 2
                    by = self.start_y + r * (self.cell_h + 2) + self.cell_h // 2
                    if math.hypot(px - bx, py - by) < radius + 6:
                        self.grid[r, c] = False
                        nibbled += 1
        return nibbled


class Qotile:
    """The Boss: Swirling crystalline enemy that morphs into the deadly Swirl!"""
    def __init__(self, x, y):
        self.home_x = x
        self.home_y = y
        self.x = x
        self.y = y
        self.radius = 26
        self.state = "IDLE"
        self.state_timer = 0
        self.angle = 0.0
        self.swirl_vx = 0.0
        self.swirl_vy = 0.0

    def update(self, target_y):
        self.angle += 0.08
        self.state_timer += 1

        if self.state == "IDLE":
            self.y = self.home_y + math.sin(self.state_timer * 0.05) * 45
            self.x = self.home_x
            if self.state_timer > 380:
                self.state = "CHARGING"
                self.state_timer = 0

        elif self.state == "CHARGING":
            self.angle += 0.25
            if self.state_timer > 90:
                self.state = "SWIRL_ATTACK"
                self.state_timer = 0
                SND_SWIRL.play()
                self.swirl_vx = -9.5
                self.swirl_vy = (target_y - self.y) * 0.035

        elif self.state == "SWIRL_ATTACK":
            self.angle += 0.45
            self.x += self.swirl_vx
            self.y += self.swirl_vy
            if self.x < 30 or self.x > WIDTH:
                self.swirl_vx *= -1
            if self.state_timer > 120:
                self.state = "IDLE"
                self.state_timer = 0
                self.x = self.home_x

    def draw(self, surf):
        cx, cy = int(self.x), int(self.y)

        if self.state == "SWIRL_ATTACK":
            n_arms = 6
            for i in range(n_arms):
                ang = self.angle + (i * 2.0 * math.pi / n_arms)
                ex = cx + int(math.cos(ang) * 28)
                ey = cy + int(math.sin(ang) * 28)
                color = C_WHITE if i % 2 == 0 else C_RED
                pygame.draw.line(surf, color, (cx, cy), (ex, ey), 4)
                pygame.draw.circle(surf, C_GOLD, (ex, ey), 4)
        else:
            r = self.radius + (math.sin(self.angle * 2) * 3 if self.state == "CHARGING" else 0)
            pts = []
            for i in range(8):
                ang = self.angle + (i * math.pi / 4)
                pts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
            c = C_RED if self.state == "CHARGING" else (C_PURPLE if int(self.angle * 4) % 2 == 0 else C_CYAN)
            pygame.draw.polygon(surf, c, pts)
            pygame.draw.polygon(surf, C_WHITE, pts, 2)


class DestroyerMissile:
    """The slow, relentless guided missile that stalks Yar."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 2.4

    def update(self, target_y):
        self.x -= self.speed
        if self.y < target_y: self.y += 1.2
        elif self.y > target_y: self.y -= 1.2

        if self.x < 10:
            self.x = WIDTH - 50
            self.y = random.randint(80, HEIGHT - 80)

    def draw(self, surf):
        cx, cy = int(self.x), int(self.y)
        pygame.draw.rect(surf, C_RED, (cx - 10, cy - 3, 20, 6), border_radius=3)
        pygame.draw.circle(surf, C_WHITE, (cx - 8, cy), 3)


class ZorlonCannon:
    """The ultimate weapon: fires across the screen to destroy the Qotile!"""
    def __init__(self):
        self.active = False
        self.x = 0
        self.y = 0
        self.speed = 18.0

    def fire(self, start_x, start_y):
        self.active = True
        self.x = start_x
        self.y = start_y
        SND_ZORLON_FIRE.play()

    def update(self):
        if self.active:
            self.x += self.speed
            if self.x > WIDTH + 50:
                self.active = False

    def draw(self, surf):
        if self.active:
            cx, cy = int(self.x), int(self.y)
            pygame.draw.line(surf, C_GOLD, (cx - 30, cy), (cx + 15, cy), 6)
            pygame.draw.line(surf, C_WHITE, (cx - 18, cy), (cx + 20, cy), 3)
            pygame.draw.circle(surf, C_CYAN, (cx + 20, cy), 7)


# =============================================================================
# MAIN GAME
# =============================================================================

def draw_neutral_zone(surf, nz_x, nz_w):
    static_surf = pygame.Surface((nz_w, HEIGHT))
    stripes = [C_CYAN, C_PURPLE, C_GOLD, C_GREEN, C_RED, C_ORANGE, (120, 80, 255), (50, 180, 140)]
    for y in range(0, HEIGHT, 8):
        c = random.choice(stripes)
        pygame.draw.rect(static_surf, c, (0, y, nz_w, 8))
    static_surf.set_alpha(150)
    surf.blit(static_surf, (nz_x, 0))


def render_1m_point_freeze(surf, score):
    surf.fill(C_BLACK)
    for y in range(0, HEIGHT, 12):
        col = (random.randint(40, 255), random.randint(40, 255), random.randint(40, 255))
        pygame.draw.line(surf, col, (0, y), (WIDTH, y), 3)

    font_huge = pygame.font.SysFont("Courier", 34, bold=True)
    font_sub = pygame.font.SysFont("Courier", 18, bold=True)

    t1 = font_huge.render("! 1,000,000 POINT SYSTEM OVERFLOW !", True, C_GOLD)
    t2 = font_sub.render("ORIGINAL ATARI 2600 GLITCH PRESERVED: BUFFER LOCKED", True, C_WHITE)
    t3 = font_sub.render("HSW GHOST LINE ACTIVATED  •  ANTHRO VICTORY COMPLETE", True, C_CYAN)
    t4 = font_sub.render("Press [R] to Reset Reality  |  [ESC] to Quit", True, C_GREEN)

    surf.blit(t1, (WIDTH // 2 - t1.get_width() // 2, HEIGHT // 2 - 70))
    surf.blit(t2, (WIDTH // 2 - t2.get_width() // 2, HEIGHT // 2 - 20))
    surf.blit(t3, (WIDTH // 2 - t3.get_width() // 2, HEIGHT // 2 + 20))
    surf.blit(t4, (WIDTH // 2 - t4.get_width() // 2, HEIGHT // 2 + 80))


def main():
    player = AnthroYar(120, HEIGHT // 2)
    barrier = EnergyBarrier(WIDTH - 280, 70, cols=6, rows=26)
    qotile = Qotile(WIDTH - 120, HEIGHT // 2)
    missile = DestroyerMissile(WIDTH - 50, HEIGHT // 2)
    cannon = ZorlonCannon()
    lasers = []

    nz_x = WIDTH // 2 - 60
    nz_w = 120

    score = 0
    lives = 3
    zorlon_armed = False
    game_state = "PLAYING"

    font_hud = pygame.font.SysFont("Courier", 17, bold=True)
    font_guide = pygame.font.SysFont("Segoe UI", 13, bold=True)

    mouse_active = True
    last_mouse_pos = pygame.mouse.get_pos()

    running = True
    while running:
        CLOCK.tick(FPS)

        cur_mouse_pos = pygame.mouse.get_pos()
        if cur_mouse_pos != last_mouse_pos:
            mouse_active = True
            last_mouse_pos = cur_mouse_pos

        # -------------------------------------------------------------
        # USER INPUT: FIRE TRIGGER (Click or Space)
        # -------------------------------------------------------------
        fire_triggered = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    fire_triggered = True
                elif game_state in ["1M_GLITCH", "GAME_OVER"] and event.key == pygame.K_r:
                    score = 0
                    lives = 3
                    player.respawn()
                    barrier = EnergyBarrier(WIDTH - 280, 70, cols=6, rows=26)
                    qotile = Qotile(WIDTH - 120, HEIGHT // 2)
                    cannon.active = False
                    lasers.clear()
                    game_state = "PLAYING"

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                fire_triggered = True

        # Handle Firing
        if fire_triggered and game_state == "PLAYING" and player.alive:
            in_nz = (nz_x <= player.x <= nz_x + nz_w)

            # Case A: Firing the big Zorlon Cannon
            if zorlon_armed and not cannon.active:
                cannon.fire(40, player.y)
                zorlon_armed = False
            # Case B: Firing regular laser (Only allowed outside Neutral Zone)
            elif not in_nz:
                lasers.append(PlayerMissile(player.x + 14, player.y))
                SND_LASER.play()

        if score >= 1_000_000 and game_state == "PLAYING":
            game_state = "1M_GLITCH"
            SND_BOOM.play()

        if game_state == "1M_GLITCH":
            render_1m_point_freeze(SCREEN, score)
            pygame.display.flip()
            continue

        # -------------------------------------------------------------
        # GAMEPLAY UPDATES
        # -------------------------------------------------------------
        keys = pygame.key.get_pressed()
        if any(keys[k] for k in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN,
                                 pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s]):
            mouse_active = False

        player.update(keys, cur_mouse_pos, mouse_active)
        barrier.update()
        qotile.update(player.y)
        missile.update(player.y)
        cannon.update()

        # Update flying lasers
        for l in lasers[:]:
            l.update()
            if not l.active:
                lasers.remove(l)
            else:
                hit = barrier.check_nibble(l.x, l.y, radius=8)
                if hit > 0:
                    l.active = False
                    score += hit * 50
                    player.nibble_count += hit
                    SND_CHOMP.play()
                    if player.nibble_count >= 5 and not zorlon_armed:
                        zorlon_armed = True
                        SND_ZORLON_ARMED.play()

        in_neutral_zone = (nz_x <= player.x <= nz_x + nz_w)

        # Nibbling directly with body
        nibbled = barrier.check_nibble(player.x, player.y, radius=14)
        if nibbled > 0:
            score += nibbled * 69
            player.nibble_count += nibbled
            SND_CHOMP.play()
            if player.nibble_count >= 5 and not zorlon_armed:
                zorlon_armed = True
                SND_ZORLON_ARMED.play()

        # Touch Qotile directly to arm
        if math.hypot(player.x - qotile.x, player.y - qotile.y) < qotile.radius + 10:
            if not zorlon_armed:
                zorlon_armed = True
                SND_ZORLON_ARMED.play()

        # Destroyer Missile
        if not in_neutral_zone and player.alive:
            if math.hypot(player.x - missile.x, player.y - missile.y) < 16:
                player.alive = False
                player.respawn_timer = 90
                lives -= 1
                SND_BOOM.play()
                if lives <= 0:
                    game_state = "GAME_OVER"

        # Swirl attack (deadly anywhere)
        if qotile.state == "SWIRL_ATTACK" and player.alive:
            if math.hypot(player.x - qotile.x, player.y - qotile.y) < 28:
                player.alive = False
                player.respawn_timer = 90
                lives -= 1
                SND_BOOM.play()
                if lives <= 0:
                    game_state = "GAME_OVER"

        # Zorlon Cannon collisions
        if cannon.active:
            if math.hypot(cannon.x - qotile.x, cannon.y - qotile.y) < qotile.radius + 15:
                cannon.active = False
                SND_BOOM.play()
                earned = 2000 if qotile.state == "SWIRL_ATTACK" else 1000
                score += earned
                barrier = EnergyBarrier(WIDTH - 280, 70, cols=6, rows=26)
                qotile = Qotile(WIDTH - 120, HEIGHT // 2)

            elif math.hypot(cannon.x - player.x, cannon.y - player.y) < 18 and player.alive:
                cannon.active = False
                player.alive = False
                player.respawn_timer = 90
                lives -= 1
                SND_BOOM.play()
                if lives <= 0:
                    game_state = "GAME_OVER"

        # -------------------------------------------------------------
        # DRAW FRAME
        # -------------------------------------------------------------
        SCREEN.fill(C_BLACK)

        # Neutral Zone
        draw_neutral_zone(SCREEN, nz_x, nz_w)

        # Entities
        barrier.draw(SCREEN)
        qotile.draw(SCREEN)
        missile.draw(SCREEN)
        cannon.draw(SCREEN)
        for l in lasers:
            l.draw(SCREEN)
        player.draw(SCREEN)

        # Top Scoreboard
        txt_score = font_hud.render(f"SCORE: {score:07d}", True, C_WHITE)
        txt_lives = font_hud.render(f"YARS: {'♥ ' * max(0, lives)}", True, C_RED)
        SCREEN.blit(txt_score, (20, 14))
        SCREEN.blit(txt_lives, (WIDTH - 160, 14))

        # Bottom Instructions & Weapon Status Guide
        pygame.draw.rect(SCREEN, (20, 16, 28), (0, HEIGHT - 38, WIDTH, 38))
        pygame.draw.line(SCREEN, (80, 60, 120), (0, HEIGHT - 38), (WIDTH, HEIGHT - 38), 1)

        if zorlon_armed:
            # Draw targeting crosshair line
            ret_y = int(player.y)
            pygame.draw.line(SCREEN, (255, 226, 138), (40, ret_y), (WIDTH - 100, ret_y), 1)
            pygame.draw.line(SCREEN, C_GOLD, (10, ret_y), (40, ret_y), 4)
            pygame.draw.circle(SCREEN, C_CYAN, (40, ret_y), 7, 2)
            lbl_status = font_guide.render("⚡ ZORLON CANNON READY! ALIGN VERTICALLY WITH QOTILE & CLICK/SPACE TO FIRE! ⚡", True, C_GOLD)
        elif in_neutral_zone:
            lbl_status = font_guide.render("🛡️ NEUTRAL ZONE: PROTECTED FROM GUIDED MISSILE (REGULAR LASER DISABLED)", True, C_CYAN)
        else:
            lbl_status = font_guide.render("🟢 LASER READY: LEFT-CLICK OR SPACE TO SHOOT | FLY INTO BLOCKS TO EAT SHIELD", True, C_GREEN)

        SCREEN.blit(lbl_status, (WIDTH // 2 - lbl_status.get_width() // 2, HEIGHT - 26))

        if game_state == "GAME_OVER":
            gov = font_hud.render("GAME OVER - Press [R] to Restart", True, C_RED)
            SCREEN.blit(gov, (WIDTH // 2 - gov.get_width() // 2, HEIGHT // 2))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
