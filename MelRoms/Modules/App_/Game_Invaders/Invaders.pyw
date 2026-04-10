import pygame
import random
import math
import sys

# --- MIKU THEME ---
MIKU_TEAL = (57, 197, 187)
MIKU_PINK = (255, 106, 170)
DARK_BLUE = (5, 5, 20)
WHITE = (200, 255, 250)
ENEMY_COLORS = [MIKU_PINK, (255, 150, 100), (150, 100, 255)]

# --- 3D PROJECTION ---
FOV = 400
OFFSET_X = 450          # 900px width
OFFSET_Y = 350          # 700px height
CUBE_SIZE = 22

def project_3d(x, y, z):
    factor = FOV / (z + 500)
    return x * factor + OFFSET_X, y * factor + OFFSET_Y

def draw_wireframe_cube(screen, x, y, z, size, color, thickness=1):
    s = size / 2
    pts = [(x-s, y-s, z-s), (x+s, y-s, z-s), (x+s, y+s, z-s), (x-s, y+s, z-s),
           (x-s, y-s, z+s), (x+s, y-s, z+s), (x+s, y+s, z+s), (x-s, y+s, z+s)]
    proj = [project_3d(p[0], p[1], p[2]) for p in pts]
    edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
    for e in edges:
        pygame.draw.line(screen, color, proj[e[0]], proj[e[1]], thickness)

class SoundEngine:
    def __init__(self):
        pygame.mixer.init(frequency=22050, size=-8, channels=1)

    def play_tone(self, freq, dur=0.12, vol=25):
        sample_rate = 22050
        n_samples = int(sample_rate * dur)
        buf = bytearray()
        for i in range(n_samples):
            t = i / sample_rate
            raw_val = 1 if math.sin(2 * math.pi * freq * t) > 0 else -1
            envelope = math.exp(-10 * t)
            val = int(vol * raw_val * envelope)
            buf.append(max(0, min(255, val + 128)))
        try:
            pygame.mixer.Sound(buffer=buf).play()
        except:
            pass

# --- GAME OBJECTS ---
class Player:
    def __init__(self):
        self.x = 0
        self.y = 12
        self.width = 2
        self.lives = 3
        self.invincible_timer = 0
        self.cooldown = 0

    def update(self):
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        if self.cooldown > 0:
            self.cooldown -= 1

    def shoot(self):
        if self.cooldown == 0:
            self.cooldown = 12
            return Bullet(self.x + 0.5, self.y - 0.8, -1)
        return None

    def hit(self):
        if self.invincible_timer == 0:
            self.lives -= 1
            self.invincible_timer = 60
            return True
        return False

class Enemy:
    def __init__(self, x, y, type_id):
        self.x = x
        self.y = y
        self.type = type_id   # 0,1,2
        self.alive = True
        self.size = 18 + type_id * 2   # slightly different sizes

    def draw(self, screen, sway):
        if not self.alive:
            return
        color = ENEMY_COLORS[self.type % len(ENEMY_COLORS)]
        wx = self.x * CUBE_SIZE + sway
        wy = self.y * CUBE_SIZE
        draw_wireframe_cube(screen, wx, wy, 0, self.size, color, 2)

    def shoot(self):
        return Bullet(self.x + 0.5, self.y + 0.8, 1)

class Bullet:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.direction = direction
        self.active = True

    def update(self):
        self.y += self.direction * 0.6
        if self.y < -2 or self.y > 15:
            self.active = False

class Game:
    def __init__(self):
        self.level = 1
        self.score = 0
        self.player = Player()
        self.enemies = []
        self.bullets = []
        self.enemy_bullets = []
        self.enemy_direction = 1
        self.enemy_move_timer = 0
        self.enemy_shoot_timer = 0
        self.game_over = False
        self.fly_in_remaining = 0   # enemies still to fly in
        self.fly_in_delay = 2       # frames between new fly‑ins
        self.fly_in_counter = 0

        self.create_level()

    def create_level(self):
        self.enemies = []
        rows = 5
        cols = 8
        start_x = -3.5
        start_y = -4.0       # start above screen, will fly down
        self.target_y = -2.0  # final row Y position
        for row in range(rows):
            for col in range(cols):
                x = start_x + col * 1.0
                y = start_y - row * 1.2   # each row starts higher, so they fly in staggered
                enemy = Enemy(x, y, row % 3)
                self.enemies.append(enemy)
        self.fly_in_remaining = len(self.enemies)
        self.fly_in_counter = 0
        self.enemy_move_delay = max(20, 40 - self.level * 2)
        self.enemy_move_counter = 0
        self.enemy_shoot_delay = max(30, 80 - self.level * 3)
        self.enemy_shoot_counter = 0
        self.enemy_direction = 1
        self.enemy_step_down = False

    def update(self):
        if self.game_over:
            return

        self.player.update()

        # --- fly‑in animation: bring enemies down one by one ---
        if self.fly_in_remaining > 0:
            self.fly_in_counter += 1
            if self.fly_in_counter >= self.fly_in_delay:
                self.fly_in_counter = 0
                # find the enemy with highest Y (closest to target) that hasn't reached target
                for e in self.enemies:
                    if e.alive and e.y < self.target_y:
                        e.y += 0.2
                        if e.y >= self.target_y:
                            self.fly_in_remaining -= 1
                        break
            # during fly‑in, no other movement/shooting
            return

        # --- enemy movement (only after fly‑in) ---
        self.enemy_move_counter += 1
        if self.enemy_move_counter >= self.enemy_move_delay:
            self.enemy_move_counter = 0
            self.move_enemies()

        # --- enemy shooting ---
        self.enemy_shoot_counter += 1
        if self.enemy_shoot_counter >= self.enemy_shoot_delay:
            self.enemy_shoot_counter = 0
            self.enemy_shoot()

        # --- player shooting ---
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] or keys[pygame.K_UP]:
            bullet = self.player.shoot()
            if bullet:
                self.bullets.append(bullet)
                SoundEngine().play_tone(600, 0.05)

        # --- update bullets ---
        for b in self.bullets[:]:
            b.update()
            if not b.active:
                self.bullets.remove(b)

        for b in self.enemy_bullets[:]:
            b.update()
            if not b.active:
                self.enemy_bullets.remove(b)

        # --- collisions: player bullets vs enemies (accurate bounding boxes) ---
        for b in self.bullets[:]:
            hit = False
            for e in self.enemies:
                if e.alive and abs(b.x - e.x) < 0.7 and abs(b.y - e.y) < 0.7:
                    e.alive = False
                    hit = True
                    self.bullets.remove(b)
                    self.score += 10
                    SoundEngine().play_tone(400, 0.08)
                    break
            if hit:
                continue

        # --- collisions: enemy bullets vs player ---
        for b in self.enemy_bullets[:]:
            if abs(b.x - self.player.x) < 0.9 and abs(b.y - self.player.y) < 0.9:
                self.enemy_bullets.remove(b)
                if self.player.hit():
                    SoundEngine().play_tone(100, 0.2)
                if self.player.lives <= 0:
                    self.game_over = True

        # --- check level completion ---
        if all(not e.alive for e in self.enemies):
            self.level += 1
            self.create_level()

        # --- check if enemies reached bottom ---
        for e in self.enemies:
            if e.alive and e.y > 11:
                self.game_over = True

    def move_enemies(self):
        # check edge collision
        edge = False
        for e in self.enemies:
            if e.alive and (e.x >= 5.5 or e.x <= -5.5):
                edge = True
                break
        if edge:
            self.enemy_direction *= -1
            for e in self.enemies:
                if e.alive:
                    e.y += 0.4   # move down
            # speed up slightly after moving down
            self.enemy_move_delay = max(15, self.enemy_move_delay - 1)
        else:
            for e in self.enemies:
                if e.alive:
                    e.x += 0.15 * self.enemy_direction

    def enemy_shoot(self):
        # find bottommost alive enemies per column
        bottom = {}
        for e in self.enemies:
            if e.alive:
                col = int(e.x * 2)
                if col not in bottom or e.y > bottom[col][1]:
                    bottom[col] = (e, e.y)
        if bottom:
            shooter = random.choice(list(bottom.values()))[0]
            bullet = shooter.shoot()
            self.enemy_bullets.append(bullet)
            SoundEngine().play_tone(300, 0.05)

    def draw(self, screen):
        screen.fill(DARK_BLUE)
        sway = math.sin(pygame.time.get_ticks() * 0.002) * 5

        # draw background grid dots
        for x in range(-8, 9):
            for y in range(-5, 14):
                wx = x * CUBE_SIZE + sway
                wy = y * CUBE_SIZE
                p = project_3d(wx, wy, 0)
                pygame.draw.circle(screen, (30, 35, 60), p, 1)

        # draw enemies
        for e in self.enemies:
            e.draw(screen, sway)

        # draw player (three cubes)
        px = self.player.x * CUBE_SIZE + sway
        py = self.player.y * CUBE_SIZE
        draw_wireframe_cube(screen, px, py, 0, CUBE_SIZE, MIKU_TEAL, 2)
        draw_wireframe_cube(screen, px - CUBE_SIZE, py, 0, CUBE_SIZE, MIKU_TEAL, 2)
        draw_wireframe_cube(screen, px + CUBE_SIZE, py, 0, CUBE_SIZE, MIKU_TEAL, 2)

        # draw bullets
        for b in self.bullets:
            wx = b.x * CUBE_SIZE + sway
            wy = b.y * CUBE_SIZE
            draw_wireframe_cube(screen, wx, wy, 0, CUBE_SIZE//2, WHITE, 1)
        for b in self.enemy_bullets:
            wx = b.x * CUBE_SIZE + sway
            wy = b.y * CUBE_SIZE
            draw_wireframe_cube(screen, wx, wy, 0, CUBE_SIZE//2, MIKU_PINK, 1)

        # UI text
        font = pygame.font.SysFont('Courier', 22, True)
        score_txt = font.render(f"SCORE: {self.score}", True, MIKU_TEAL)
        lives_txt = font.render(f"LIVES: {self.player.lives}", True, MIKU_TEAL)
        level_txt = font.render(f"LEVEL: {self.level}", True, MIKU_TEAL)
        screen.blit(score_txt, (10, 10))
        screen.blit(lives_txt, (10, 40))
        screen.blit(level_txt, (10, 70))

        if self.game_over:
            font_big = pygame.font.SysFont('Courier', 40, True)
            over_txt = font_big.render("GAME OVER", True, MIKU_PINK)
            restart_txt = font.render("Press R to restart", True, WHITE)
            screen.blit(over_txt, (320, 300))
            screen.blit(restart_txt, (330, 350))

def main():
    pygame.init()
    pygame.display.set_caption("3D Wireframe Invaders")
    screen = pygame.display.set_mode((900, 700))
    clock = pygame.time.Clock()
    game = Game()
    sfx = SoundEngine()

    running = True
    while running:
        dt = clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    game.player.x = max(-6.5, game.player.x - 0.8)
                if event.key == pygame.K_RIGHT:
                    game.player.x = min(6.5, game.player.x + 0.8)
                if event.key == pygame.K_r and game.game_over:
                    game = Game()
                    sfx.play_tone(600, 0.2)

        game.update()
        game.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()