import pygame
import random
import math
import sys
MIKU_TEAL = (57, 197, 187)
MIKU_PINK = (255, 106, 170)
DARK_BLUE = (5, 5, 20)
WHITE = (200, 255, 250)
FOV = 400
OFFSET_X = 450       
OFFSET_Y = 350       
GRID_SIZE = 18        
GRID_WIDTH = 30      
GRID_HEIGHT = 20        

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

class SnakeGame:
    def __init__(self):
        start_x = GRID_WIDTH // 2
        start_y = GRID_HEIGHT // 2
        self.snake = [(start_x, start_y)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.food = self._random_food()
        self.score = 0
        self.state = "playing"

    def _random_food(self):
        while True:
            pos = (random.randint(0, GRID_WIDTH-1), random.randint(0, GRID_HEIGHT-1))
            if pos not in self.snake:
                return pos

    def update(self):
        if self.state != "playing":
            return

        if (self.next_direction[0] != -self.direction[0] or
            self.next_direction[1] != -self.direction[1]):
            self.direction = self.next_direction

        head = self.snake[0]
        new_head = (head[0] + self.direction[0], head[1] + self.direction[1])
        if (new_head[0] < 0 or new_head[0] >= GRID_WIDTH or
            new_head[1] < 0 or new_head[1] >= GRID_HEIGHT):
            self.state = "gameover"
            return

        if new_head in self.snake:
            self.state = "gameover"
            return

        self.snake.insert(0, new_head)
        if new_head == self.food:
            self.score += 10
            self.food = self._random_food()
            SoundEngine().play_tone(800, 0.1)
        else:
            self.snake.pop()

    def change_direction(self, dx, dy):
        self.next_direction = (dx, dy)

def main():
    pygame.init()
    pygame.display.set_caption("3D Wireframe Snake - Horizontal")
    screen = pygame.display.set_mode((900, 700))
    clock = pygame.time.Clock()
    game = SnakeGame()
    sfx = SoundEngine()
    move_timer = 0
    MOVE_DELAY = 120 
    running = True
    while running:
        dt = clock.tick(30)
        move_timer += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    game.change_direction(0, -1)
                    sfx.play_tone(400, 0.05)
                elif event.key == pygame.K_DOWN:
                    game.change_direction(0, 1)
                    sfx.play_tone(400, 0.05)
                elif event.key == pygame.K_LEFT:
                    game.change_direction(-1, 0)
                    sfx.play_tone(400, 0.05)
                elif event.key == pygame.K_RIGHT:
                    game.change_direction(1, 0)
                    sfx.play_tone(400, 0.05)
                elif event.key == pygame.K_r and game.state == "gameover":
                    game = SnakeGame()
                    sfx.play_tone(600, 0.2)
        if move_timer >= MOVE_DELAY and game.state == "playing":
            game.update()
            move_timer = 0
        screen.fill(DARK_BLUE)
        sway = math.sin(pygame.time.get_ticks() * 0.002) * 10
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                wx = (x - GRID_WIDTH//2) * GRID_SIZE + sway
                wy = (y - GRID_HEIGHT//2) * GRID_SIZE
                p = project_3d(wx, wy, 0)
                pygame.draw.circle(screen, (30, 35, 60), p, 1)
        fx = (game.food[0] - GRID_WIDTH//2) * GRID_SIZE + sway
        fy = (game.food[1] - GRID_HEIGHT//2) * GRID_SIZE
        draw_wireframe_cube(screen, fx, fy, 0, GRID_SIZE, MIKU_PINK, 2)
        for i, (sx, sy) in enumerate(game.snake):
            color = MIKU_TEAL if i == 0 else MIKU_TEAL
            wx = (sx - GRID_WIDTH//2) * GRID_SIZE + sway
            wy = (sy - GRID_HEIGHT//2) * GRID_SIZE
            draw_wireframe_cube(screen, wx, wy, 0, GRID_SIZE, color, 2 if i == 0 else 1)
        font = pygame.font.SysFont('Courier', 22, True)
        score_txt = font.render(f"SCORE: {game.score}", True, MIKU_TEAL)
        screen.blit(score_txt, (10, 10))
        if game.state == "gameover":
            font_big = pygame.font.SysFont('Courier', 40, True)
            over_txt = font_big.render("GAME OVER", True, MIKU_PINK)
            restart_txt = font.render("Press R to restart", True, WHITE)
            screen.blit(over_txt, (320, 300))
            screen.blit(restart_txt, (330, 350))
        pygame.display.flip()
    pygame.quit()
    sys.exit()
if __name__ == "__main__":
    main()