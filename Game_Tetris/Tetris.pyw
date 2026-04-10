import pygame
import random
import math
import sys
MIKU_TEAL = (57, 197, 187)
MIKU_PINK = (255, 106, 170)
DARK_BLUE = (5, 5, 20)
WHITE = (200, 255, 250)
colors = [(0,0,0), MIKU_PINK, MIKU_TEAL, (100,100,255), (150,50,255), MIKU_TEAL, MIKU_PINK]
FOV, OFFSET_X, OFFSET_Y = 400, 225, 300
def project_3d(x, y, z):
    factor = FOV / (z + 500)
    return x * factor + OFFSET_X, y * factor + OFFSET_Y
def draw_wireframe_cube(screen, x, y, z, size, color, thickness=1):
    s = size / 2
    pts = [(x-s,y-s,z-s), (x+s,y-s,z-s), (x+s,y+s,z-s), (x-s,y+s,z-s),
           (x-s,y-s,z+s), (x+s,y-s,z+s), (x+s,y+s,z+s), (x-s,y+s,z+s)]
    proj = [project_3d(p[0], p[1], p[2]) for p in pts]
    edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
    for e in edges: pygame.draw.line(screen, color, proj[e[0]], proj[e[1]], thickness)
class SoundEngine:
    def __init__(self):
        try:
            pygame.mixer.init(frequency=22050, size=-8, channels=1)
        except:
            pass
    def _generate_sine(self, freq, dur, volume=0.7, fade=True):
        sample_rate = 22050
        n_samples = int(sample_rate * dur)
        buf = bytearray()
        for i in range(n_samples):
            t = i / sample_rate
            val = math.sin(2 * math.pi * freq * t)
            if fade:
                envelope = math.exp(-12 * t)
            else:
                envelope = 1.0
            int_val = int(128 + val * volume * envelope)
            buf.append(max(0, min(255, int_val)))
        return buf
    def _play_buffer(self, buffer):
        try:
            pygame.mixer.Sound(buffer=buffer).play()
        except:
            pass

    def play_landing(self):
        sample_rate = 22050
        dur = 0.15
        n_samples = int(sample_rate * dur)
        buf = bytearray()
        for i in range(n_samples):
            t = i / sample_rate
            freq = 100 - 50 * (t / dur) 
            val = math.sin(2 * math.pi * freq * t)
            envelope = math.exp(-15 * t)
            int_val = int(128 + val * 0.7 * envelope)  
            buf.append(max(0, min(255, int_val)))
        self._play_buffer(buf)
    def play_turn(self):
        sample_rate = 22050
        dur = 0.12
        n_samples = int(sample_rate * dur)
        buf = bytearray()
        for i in range(n_samples):
            t = i / sample_rate
            freq = 350 - 200 * (t / dur) 
            val = math.sin(2 * math.pi * freq * t)
            envelope = math.exp(-10 * t)
            int_val = int(128 + val * 0.7 * envelope) 
            buf.append(max(0, min(255, int_val)))
        self._play_buffer(buf)
    def play_move(self):
        sample_rate = 22050
        dur = 0.1
        n_samples = int(sample_rate * dur)
        buf = bytearray()
        for i in range(n_samples):
            t = i / sample_rate
            if t < 0.005:
                click = math.sin(2 * math.pi * 600 * t) * math.exp(-2000 * t)
                val = click * 0.3
            else:
                freq = 120 + 20 * math.sin(2 * math.pi * 4 * t)
                val = math.sin(2 * math.pi * freq * t)
            envelope = math.exp(-12 * t)
            int_val = int(128 + val * 0.7 * envelope)
            buf.append(max(0, min(255, int_val)))
        self._play_buffer(buf)

    def play_hold(self):
        sample_rate = 22050
        dur = 0.18
        n_samples = int(sample_rate * dur)
        buf = bytearray()
        for i in range(n_samples):
            t = i / sample_rate
            val = math.sin(2 * math.pi * 180 * t)
            envelope = math.exp(-10 * t)
            int_val = int(128 + val * 0.7 * envelope)
            buf.append(max(0, min(255, int_val)))
        self._play_buffer(buf)

    def play_tone(self, freq, dur=0.1, vol=2):
        buf = self._generate_sine(freq, dur, min(vol, 2), fade=True)
        self._play_buffer(buf)

class Figure:
    figures = [
        [[1, 5, 9, 13], [4, 5, 6, 7]], [[4, 5, 9, 10], [2, 6, 5, 9]],
        [[6, 7, 9, 10], [1, 5, 6, 10]], [[1, 2, 5, 9], [0, 4, 5, 6], [1, 5, 9, 8], [4, 5, 6, 10]],
        [[1, 2, 6, 10], [5, 6, 7, 9], [2, 6, 10, 11], [3, 5, 6, 7]],
        [[1, 4, 5, 6], [1, 4, 5, 9], [4, 5, 6, 9], [1, 5, 6, 9]], [[1, 2, 5, 6]],
    ]
    def __init__(self, x, y, type=None):
        self.x, self.y = x, y
        self.type = random.randint(0, len(self.figures)-1) if type is None else type
        self.color = random.randint(1, len(colors)-1)
        self.rotation = 0
    def image(self): return self.figures[self.type][self.rotation]
    def rotate(self): self.rotation = (self.rotation + 1) % len(self.figures[self.type])

class Tetris:
    def __init__(self, height, width):
        self.height, self.width = height, width
        self.field = [[0 for _ in range(width)] for _ in range(height)]
        self.score, self.state, self.zoom = 0, "start", 22
        self.figure, self.next_figure = None, Figure(3, 0)
        self.held_type, self.can_hold = None, True
        self.lock_delay_timer = 0 

    def new_figure(self):
        self.figure = self.next_figure
        self.next_figure = Figure(3, 0)
        self.can_hold = True
        self.lock_delay_timer = 0
        if self.intersects(): self.state = "gameover"

    def intersects(self):
        for i in range(4):
            for j in range(4):
                if i * 4 + j in self.figure.image():
                    if i + self.figure.y > self.height - 1 or \
                       j + self.figure.x > self.width - 1 or \
                       j + self.figure.x < 0 or \
                       self.field[i + self.figure.y][j + self.figure.x] > 0:
                        return True
        return False

    def freeze(self):
        for i in range(4):
            for j in range(4):
                if i * 4 + j in self.figure.image():
                    self.field[i + self.figure.y][j + self.figure.x] = self.figure.color
        lines = 0
        for i in range(1, self.height):
            if 0 not in self.field[i]:
                lines += 1
                for i1 in range(i, 1, -1): self.field[i1] = self.field[i1-1][:]
        self.score += lines ** 2
        self.new_figure()

    def go_space(self):
        while not self.intersects(): self.figure.y += 1
        self.figure.y -= 1
        self.freeze()

    def go_down(self):
        self.figure.y += 1
        if self.intersects(): self.figure.y -= 1
        else: self.lock_delay_timer = 0

    def go_side(self, dx):
        old_x = self.figure.x
        self.figure.x += dx
        if self.intersects(): self.figure.x = old_x

    def rotate(self):
        old_rot = self.figure.rotation
        self.figure.rotate()
        if self.intersects(): self.figure.rotation = old_rot

pygame.init()

pygame.display.set_caption("MelRoms Tetris")
try:
    icon = pygame.image.load('icon.ico')
    pygame.display.set_icon(icon)
except:
    pass

screen = pygame.display.set_mode((450, 600))
sfx = SoundEngine()
clock = pygame.time.Clock()
game = Tetris(20, 10)
pressing_down = False
counter = 0

while True:
    dt = clock.tick(30)
    if game.figure is None: game.new_figure()
    
    game.figure.y += 1
    if game.intersects():
        game.figure.y -= 1
        game.lock_delay_timer += dt
        if game.lock_delay_timer >= 300: game.freeze()
    else:
        game.figure.y -= 1
        counter += 1
        if counter % 15 == 0 or pressing_down:
            game.go_down()

    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                game.rotate()
                sfx.play_turn()
            if event.key == pygame.K_DOWN:
                pressing_down = True
            if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                if event.key == pygame.K_LEFT:
                    game.go_side(-1)
                else:
                    game.go_side(1)
                sfx.play_move()
            if event.key == pygame.K_SPACE:
                game.go_space()
                sfx.play_landing()
            if event.key == pygame.K_c and game.can_hold:
                old_type = game.figure.type
                if game.held_type is None:
                    game.held_type = old_type
                    game.new_figure()
                else:
                    game.figure = Figure(3, 0, game.held_type)
                    game.held_type = old_type
                game.can_hold = False
                sfx.play_hold()
            if event.key == pygame.K_ESCAPE:
                game.__init__(20, 10)
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_DOWN:
                pressing_down = False

    screen.fill(DARK_BLUE)
    sway = math.sin(pygame.time.get_ticks() * 0.002) * 10
    
    def draw_mini_preview(f_type, x_off, label):
        lbl = pygame.font.SysFont('Courier', 18, True).render(label, True, WHITE)
        screen.blit(lbl, [x_off - 20, 50])
        if f_type is not None:
            temp = Figure(0, 0, f_type)
            for i in range(4):
                for j in range(4):
                    if i*4+j in temp.image():
                        px = (j * 12) + x_off - 15
                        py = (i * 12) + 80
                        pygame.draw.rect(screen, MIKU_TEAL, [px, py, 10, 10], 1)

    draw_mini_preview(game.next_figure.type, 380, "NEXT")
    draw_mini_preview(game.held_type, 60, "HOLD")

    active_color = MIKU_TEAL
    if game.lock_delay_timer > 0:
        active_color = MIKU_PINK if (pygame.time.get_ticks() // 50) % 2 == 0 else MIKU_TEAL

    for i in range(game.height):
        for j in range(game.width):
            gx, gy = (j-5)*game.zoom + sway, (i-10)*game.zoom
            if game.field[i][j] > 0:
                draw_wireframe_cube(screen, gx, gy, 0, game.zoom, colors[game.field[i][j]], 1)
            else:
                p = project_3d(gx, gy, 0)
                pygame.draw.circle(screen, (30, 35, 60), p, 1)
    
    if game.figure:
        for i in range(4):
            for j in range(4):
                if i*4+j in game.figure.image():
                    fx, fy = (j+game.figure.x-5)*game.zoom + sway, (i+game.figure.y-10)*game.zoom
                    draw_wireframe_cube(screen, fx, fy, 0, game.zoom, active_color, 2)

    score_txt = pygame.font.SysFont('Courier', 22, True).render(f"SCORE: {game.score}", True, MIKU_TEAL)
    screen.blit(score_txt, [10, 10])

    if game.state == "gameover":
        over = pygame.font.SysFont('Courier', 40, True).render("SYSTEM FAIL", True, MIKU_PINK)
        screen.blit(over, [90, 250])

    pygame.display.flip()