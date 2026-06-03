# -*- coding: utf-8 -*-
"""
Snake Game - Mouse Steering at Any Angle - No Click Needed
"""

import pygame
import random
import math
import sys

pygame.init()
pygame.display.set_caption("Snake Game - Mouse Steering")

CELL_SIZE = 30
COLS, ROWS = 20, 15
WIDTH = COLS * CELL_SIZE
HEIGHT = ROWS * CELL_SIZE + 60
GAME_H = ROWS * CELL_SIZE

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

try:
    font_score = pygame.font.SysFont("microsoftyahei", 28, bold=True)
    font_small = pygame.font.SysFont("microsoftyahei", 18)
    font_big = pygame.font.SysFont("microsoftyahei", 48, bold=True)
except Exception:
    font_score = pygame.font.Font(None, 36)
    font_small = pygame.font.Font(None, 22)
    font_big = pygame.font.Font(None, 60)

C_BG        = (25,  30,  45)
C_GRID1     = (35,  42,  58)
C_GRID2     = (30,  36,  50)
C_SNAKE_H   = (100, 220, 120)
C_SNAKE_B   = (70,  180, 90)
C_SNAKE_T   = (40,  120, 55)
C_FOOD      = (255, 90,  90)
C_FOOD_GLOW = (255, 160, 140)
C_SCORE     = (240, 240, 240)
C_OVERLAY   = (0,   0,   0)
C_BUTTON    = (90,  180, 255)
C_BUTTON_H  = (130, 210, 255)

KEY_DIRS = {
    pygame.K_UP:    (0, -1),
    pygame.K_DOWN:  (0,  1),
    pygame.K_LEFT:  (-1, 0),
    pygame.K_RIGHT: (1,  0),
    pygame.K_w:     (0, -1),
    pygame.K_s:     (0,  1),
    pygame.K_a:     (-1, 0),
    pygame.K_d:     (1,  0),
}

particles = []

def spawn_particles(x, y, count=15):
    colors = [
        (255, 200, 80), (255, 150, 60), (255, 230, 100),
        (255, 120, 120), (255, 180, 140),
    ]
    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 7)
        particles.append({
            "x": x, "y": y,
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed,
            "life": random.uniform(20, 45),
            "max_life": 45,
            "size": random.randint(3, 8),
            "color": random.choice(colors),
        })

def update_particles():
    global particles
    alive = []
    for p in particles:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["life"] -= 1
        if p["life"] > 0:
            alive.append(p)
    particles = alive

def draw_particles(surf):
    for p in particles:
        alpha = p["life"] / p["max_life"]
        r, g, b = p["color"]
        color = (int(r * alpha), int(g * alpha), int(b * alpha))
        radius = int(p["size"] * alpha)
        if radius > 0:
            pygame.draw.circle(surf, color, (int(p["x"]), int(p["y"])), radius)

def draw_glow_text(surf, font, text, x, y, color, glow_color, center=True):
    glow = font.render(text, True, glow_color)
    main = font.render(text, True, color)
    if center:
        r = main.get_rect(center=(x, y))
        g = glow.get_rect(center=(x, y))
    else:
        r = main.get_rect(topleft=(x, y))
        g = glow.get_rect(topleft=(x, y))
    for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
        surf.blit(glow, (g.x + dx, g.y + dy))
    surf.blit(main, r)


class Game:
    def __init__(self):
        self.segment_spacing = CELL_SIZE * 0.75
        self.speed = 4.0
        self.turn_speed = 0.15
        self.chain_smooth = 0.55   # exponential smoothing factor
        self.reset()

    def reset(self):
        start_x = WIDTH // 2
        start_y = GAME_H // 2
        sp = self.segment_spacing
        self.snake = [
            (start_x, start_y),
            (start_x - sp, start_y),
            (start_x - 2 * sp, start_y),
        ]
        self.heading = 0.0
        self.target_heading = 0.0
        self.food = self._place_food()
        self.score = 0
        self.level = 1
        self.alive = True
        self.frame = 0
        self.food_pulse = 0
        self.shake_timer = 0
        self.speed = 4.0
        global particles
        particles.clear()

    def _place_food(self):
        for _ in range(200):
            fx = random.randint(1, COLS - 1) * CELL_SIZE + CELL_SIZE // 2
            fy = random.randint(1, ROWS - 1) * CELL_SIZE + CELL_SIZE // 2
            too_close = False
            for seg in self.snake:
                if math.hypot(seg[0] - fx, seg[1] - fy) < CELL_SIZE * 1.0:
                    too_close = True
                    break
            if not too_close:
                return (float(fx), float(fy))
        return (float(random.randint(2, COLS - 2) * CELL_SIZE + CELL_SIZE // 2),
                float(random.randint(2, ROWS - 2) * CELL_SIZE + CELL_SIZE // 2))

    def step(self):
        mx, my = pygame.mouse.get_pos()

        if my < GAME_H:
            hx, hy = self.snake[0]
            self.target_heading = math.atan2(my - hy, mx - hx)

        diff = ((self.target_heading - self.heading + math.pi) % (2 * math.pi)) - math.pi
        self.heading += diff * self.turn_speed
        self.heading %= (2 * math.pi)

        hx, hy = self.snake[0]
        nx = hx + math.cos(self.heading) * self.speed
        ny = hy + math.sin(self.heading) * self.speed

        margin = CELL_SIZE * 0.4
        if nx < margin or nx > WIDTH - margin or ny < margin or ny > GAME_H - margin:
            self.alive = False
            self.shake_timer = 30
            return

        self.snake.insert(0, (nx, ny))

        # Food
        fx, fy = self.food
        if math.hypot(nx - fx, ny - fy) < CELL_SIZE * 0.85:
            self.score += 10
            spawn_particles(fx, fy, 20)
            self.food = self._place_food()
            if self.food is None:
                self.alive = False
            if self.score % 50 == 0:
                self.level += 1
                self.speed = min(9.0, 4.0 + self.level * 0.5)
            # Growth: don't pop tail
        else:
            self.snake.pop()

        # Chain-following with exponential smoothing (no jitter)
        for i in range(1, len(self.snake)):
            px, py = self.snake[i - 1]
            cx, cy = self.snake[i]
            dx = px - cx
            dy = py - cy
            dist = math.hypot(dx, dy)
            if dist < 0.5:
                continue  # skip duplicates, handled by post-pass below
            # Ideal position: exactly segment_spacing behind predecessor
            target_x = px - dx / dist * self.segment_spacing
            target_y = py - dy / dist * self.segment_spacing
            # Exponential smooth: move fraction toward target
            s = self.chain_smooth
            self.snake[i] = (
                cx + (target_x - cx) * s,
                cy + (target_y - cy) * s,
            )

        # Post-pass: force apart any segments that are too close (handles growth duplicates)
        for i in range(1, len(self.snake)):
            px, py = self.snake[i - 1]
            cx, cy = self.snake[i]
            dx = cx - px
            dy = cy - py
            dist = math.hypot(dx, dy)
            if dist < self.segment_spacing * 0.4:
                if dist < 0.01:
                    # Determine push direction
                    if i >= 2:
                        dx = self.snake[i - 1][0] - self.snake[i - 2][0]
                        dy = self.snake[i - 1][1] - self.snake[i - 2][1]
                        dist = math.hypot(dx, dy)
                    if dist < 0.01:
                        dx, dy = -math.cos(self.heading), -math.sin(self.heading)
                        dist = 1.0
                self.snake[i] = (
                    px + dx / dist * self.segment_spacing,
                    py + dy / dist * self.segment_spacing,
                )

        # Self-collision
        if len(self.snake) > 6:
            for i in range(5, len(self.snake)):
                if math.hypot(nx - self.snake[i][0], ny - self.snake[i][1]) < self.segment_spacing * 0.55:
                    self.alive = False
                    self.shake_timer = 30
                    return

    def set_keyboard_direction(self, dx, dy):
        self.target_heading = math.atan2(dy, dx)

    def draw(self):
        self.frame += 1
        self.food_pulse = math.sin(self.frame * 0.1) * 0.3 + 0.7

        shake_dx = shake_dy = 0
        if self.shake_timer > 0:
            self.shake_timer -= 1
            intensity = self.shake_timer / 30 * 8
            shake_dx = random.randint(-int(intensity), int(intensity))
            shake_dy = random.randint(-int(intensity), int(intensity))

        screen.fill(C_BG)

        for r in range(ROWS):
            for c in range(COLS):
                color = C_GRID1 if (r + c) % 2 == 0 else C_GRID2
                rect = pygame.Rect(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, color, rect, 1)

        fx, fy = self.food
        glow_radius = int(CELL_SIZE * 0.55 * (1.0 + self.food_pulse * 0.3))
        glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        alpha = int(60 * self.food_pulse)
        pygame.draw.circle(glow_surf, (*C_FOOD_GLOW, alpha),
                           (glow_radius, glow_radius), glow_radius)
        screen.blit(glow_surf, (fx - glow_radius, fy - glow_radius))
        pygame.draw.circle(screen, C_FOOD, (int(fx), int(fy)), int(CELL_SIZE * 0.4))
        pygame.draw.circle(screen, (255, 180, 180),
                           (int(fx - CELL_SIZE * 0.1), int(fy - CELL_SIZE * 0.12)),
                           int(CELL_SIZE * 0.12))

        n = len(self.snake)
        for i in range(n - 1, -1, -1):
            x, y = self.snake[i]
            ratio = i / max(n - 1, 1)
            r = int(C_SNAKE_H[0] * (1 - ratio) + C_SNAKE_T[0] * ratio)
            g = int(C_SNAKE_H[1] * (1 - ratio) + C_SNAKE_T[1] * ratio)
            b = int(C_SNAKE_H[2] * (1 - ratio) + C_SNAKE_T[2] * ratio)

            scale = 0.85 if i == 0 else (0.85 - 0.04 * min(i, 10))
            rr = max(4, int(CELL_SIZE * 0.45 * scale))

            pygame.draw.circle(screen, (r, g, b), (int(x), int(y)), rr)

            if i == 0:
                hl_x = int(x + math.cos(self.heading) * rr * 0.15)
                hl_y = int(y + math.sin(self.heading) * rr * 0.15)
                pygame.draw.circle(screen, (180, 255, 200), (hl_x, hl_y), int(rr * 0.55))

                eye_forward = rr * 0.35
                eye_side = rr * 0.5
                cos_h = math.cos(self.heading)
                sin_h = math.sin(self.heading)
                eye1 = (int(x + cos_h * eye_forward - sin_h * eye_side),
                        int(y + sin_h * eye_forward + cos_h * eye_side))
                eye2 = (int(x + cos_h * eye_forward + sin_h * eye_side),
                        int(y + sin_h * eye_forward - cos_h * eye_side))
                er = max(2, rr // 3)
                pygame.draw.circle(screen, (255, 255, 255), eye1, er)
                pygame.draw.circle(screen, (255, 255, 255), eye2, er)
                pupil_r = max(1, rr // 5)
                pupil1 = (int(eye1[0] + cos_h * pupil_r),
                          int(eye1[1] + sin_h * pupil_r))
                pupil2 = (int(eye2[0] + cos_h * pupil_r),
                          int(eye2[1] + sin_h * pupil_r))
                pygame.draw.circle(screen, (20, 20, 20), pupil1, pupil_r)
                pygame.draw.circle(screen, (20, 20, 20), pupil2, pupil_r)

        update_particles()
        draw_particles(screen)

        bar_y = GAME_H
        pygame.draw.rect(screen, (15, 20, 35), (0, bar_y, WIDTH, 60))
        pygame.draw.line(screen, (60, 120, 200), (0, bar_y), (WIDTH, bar_y), 3)

        draw_glow_text(screen, font_score,
            "Score: " + str(self.score),
            WIDTH // 2, bar_y + 18,
            C_SCORE, (100, 200, 255))

        draw_glow_text(screen, font_small,
            "Level: " + str(self.level),
            WIDTH // 2, bar_y + 43,
            (180, 200, 220), (60, 120, 200))

        draw_glow_text(screen, font_small,
            "Move mouse to steer | Arrow Keys / WASD",
            8, bar_y + 30,
            (160, 180, 210), (50, 100, 180), center=False)

        if not self.alive:
            self._draw_game_over(shake_dx, shake_dy)

        pygame.display.flip()

    def _draw_game_over(self, shake_dx, shake_dy):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        cx = WIDTH // 2 + shake_dx
        cy = GAME_H // 2 - 20 + shake_dy

        draw_glow_text(screen, font_big, "Game Over", cx, cy - 20,
                       (255, 100, 100), (255, 50, 50))
        draw_glow_text(screen, font_score,
                       "Final Score: " + str(self.score),
                       cx, cy + 35, C_SCORE, (100, 200, 255))

        btn_w, btn_h = 200, 45
        btn_x = cx - btn_w // 2
        btn_y = cy + 75
        btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

        mx, my = pygame.mouse.get_pos()
        hovering = btn_rect.collidepoint(mx, my)
        btn_color = C_BUTTON_H if hovering else C_BUTTON

        pygame.draw.rect(screen, btn_color, btn_rect, border_radius=12)
        pygame.draw.rect(screen, (255, 255, 255), btn_rect, 2, border_radius=12)
        draw_glow_text(screen, font_score, "Play Again", cx,
                       btn_y + btn_h // 2, (255, 255, 255), (200, 230, 255))

    def check_restart_click(self, mx, my):
        if self.alive:
            return False
        cx = WIDTH // 2
        cy = GAME_H // 2 - 20
        btn_w, btn_h = 200, 45
        btn_x = cx - btn_w // 2
        btn_y = cy + 75
        return btn_x <= mx <= btn_x + btn_w and btn_y <= my <= btn_y + btn_h


def main():
    game = Game()
    running = True

    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif game.alive and event.key in KEY_DIRS:
                    dx, dy = KEY_DIRS[event.key]
                    game.set_keyboard_direction(dx, dy)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if not game.alive and game.check_restart_click(mx, my):
                    game.reset()

        if game.alive:
            game.step()

        game.draw()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()