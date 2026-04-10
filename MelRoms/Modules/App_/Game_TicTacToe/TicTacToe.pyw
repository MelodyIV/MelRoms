import pygame
import sys
import math
import random
import numpy as np
from pygame.locals import *

# =============================================================================
# CONSTANTS
# =============================================================================
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

TEAL = (0, 251, 255)
MAGENTA = (255, 0, 127)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
BLUE = (50, 100, 255)

BOARD_MIN = -3.0
BOARD_MAX = 3.0
CELL_SIZE = 2.0
LINE_WIDTH = 0.25
LINE_HEIGHT = 0.2

FOV = 60
NEAR = 0.1
FAR = 100.0

# =============================================================================
# AUDIO SYNTHESIS
# =============================================================================
def ensure_mixer():
    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=44100, size=-16, channels=2)

def generate_sine(freq, duration, volume=0.5, sample_rate=44100):
    samples = int(sample_rate * duration)
    t = np.linspace(0, duration, samples, False)
    wave = np.sin(freq * 2 * np.pi * t)
    return (wave * volume * 32767).astype(np.int16)

def generate_square(freq, duration, volume=0.3, sample_rate=44100):
    samples = int(sample_rate * duration)
    t = np.linspace(0, duration, samples, False)
    wave = np.sign(np.sin(freq * 2 * np.pi * t))
    return (wave * volume * 32767).astype(np.int16)

def generate_noise(duration, volume=0.2, sample_rate=44100):
    samples = int(sample_rate * duration)
    noise = np.random.normal(0, volume * 32767, samples).astype(np.int16)
    return noise

def apply_envelope(wave, attack=0.02, decay=0.1, sustain=0.5, release=0.1, sample_rate=44100):
    length = len(wave)
    env = np.ones(length)
    a = int(attack * sample_rate)
    d = int(decay * sample_rate)
    r = int(release * sample_rate)
    if a > 0:
        env[:a] = np.linspace(0, 1, a)
    if d > 0:
        env[a:a+d] = np.linspace(1, sustain, d)
    if r > 0:
        env[-r:] = np.linspace(sustain, 0, r)
    return (wave * env).astype(np.int16)

def create_thud():
    ensure_mixer()
    sample_rate = 44100
    duration = 0.2
    bass = generate_sine(70, duration, 0.6, sample_rate)
    crunch = generate_square(140, duration, 0.25, sample_rate)
    noise = generate_noise(duration, 0.15, sample_rate)
    mixed = bass + crunch + noise
    mixed = apply_envelope(mixed, attack=0.01, decay=0.1, sustain=0.3, release=0.08, sample_rate=sample_rate)
    stereo = np.array([mixed, mixed]).T
    return pygame.sndarray.make_sound(stereo)

def create_win_drone():
    ensure_mixer()
    sample_rate = 44100
    duration = 1.0
    f1 = generate_sine(110, duration, 0.2, sample_rate)
    f2 = generate_sine(165, duration, 0.15, sample_rate)
    f3 = generate_sine(82, duration, 0.1, sample_rate)
    drone = (f1 + f2 + f3).astype(np.int16)
    drone = apply_envelope(drone, attack=0.2, decay=0.3, sustain=0.5, release=0.4, sample_rate=sample_rate)
    delay_samples = int(0.3 * sample_rate)
    delayed = np.zeros_like(drone)
    if delay_samples < len(drone):
        delayed[delay_samples:] = drone[:-delay_samples]
    echo = (drone * 0.6 + delayed * 0.2).astype(np.int16)
    stereo = np.array([echo, echo]).T
    return pygame.sndarray.make_sound(stereo)

place_sound = create_thud()
win_sound = create_win_drone()

# =============================================================================
# PARTICLE SYSTEM
# =============================================================================
class Particle:
    def __init__(self, x, y, vx, vy, size, color, lifetime):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = size
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt
        self.size *= 0.96
        return self.lifetime > 0

    def draw(self, surf):
        brightness = int(255 * (self.lifetime / self.max_lifetime))
        col = (min(255, self.color[0] * brightness // 255),
               min(255, self.color[1] * brightness // 255),
               min(255, self.color[2] * brightness // 255))
        rect = pygame.Rect(self.x - self.size//2, self.y - self.size//2, self.size, self.size)
        pygame.draw.rect(surf, col, rect)

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def burst(self, x, y, count=25):
        for _ in range(count):
            angle = random.uniform(0, math.pi*2)
            speed = random.uniform(80, 250)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.randint(4, 10)
            color = random.choice([(255,255,200), (0,255,255), (255,200,100)])
            lifetime = random.uniform(0.3, 0.8)
            self.particles.append(Particle(x, y, vx, vy, size, color, lifetime))

    def update(self, dt):
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, surf):
        for p in self.particles:
            p.draw(surf)

# =============================================================================
# BUTTON
# =============================================================================
class Button:
    def __init__(self, x, y, w, h, text, callback, color=(60,60,80), hover=(100,100,130)):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.color = color
        self.hover_color = hover
        self.hovered = False

    def handle_event(self, event):
        if event.type == MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered:
                self.callback()

    def draw(self, surf):
        col = self.hover_color if self.hovered else self.color
        pygame.draw.rect(surf, col, self.rect, border_radius=8)
        pygame.draw.rect(surf, TEAL, self.rect, 2, border_radius=8)
        font = pygame.font.Font(None, 28)
        text_surf = font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surf.blit(text_surf, text_rect)

# =============================================================================
# CAMERA
# =============================================================================
class Camera:
    def __init__(self, position, target, up=(0,1,0)):
        self.position = np.array(position, dtype=np.float32)
        self.target = np.array(target, dtype=np.float32)
        self.up = np.array(up, dtype=np.float32)
        self.aspect = SCREEN_WIDTH / SCREEN_HEIGHT
        self.fov = FOV
        self.near = NEAR
        self.far = FAR
        self.view_matrix = np.eye(4)
        self.proj_matrix = np.eye(4)
        self.update_matrices()

    def update_matrices(self):
        forward = self.target - self.position
        forward = forward / np.linalg.norm(forward)
        right = np.cross(forward, self.up)
        right = right / np.linalg.norm(right)
        up = np.cross(right, forward)
        self.view_matrix = np.array([
            [right[0], right[1], right[2], -np.dot(right, self.position)],
            [up[0], up[1], up[2], -np.dot(up, self.position)],
            [-forward[0], -forward[1], -forward[2], np.dot(forward, self.position)],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        fov_rad = math.radians(self.fov)
        f = 1.0 / math.tan(fov_rad / 2.0)
        self.proj_matrix = np.array([
            [f / self.aspect, 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, (self.far + self.near) / (self.near - self.far), (2 * self.far * self.near) / (self.near - self.far)],
            [0, 0, -1, 0]
        ], dtype=np.float32)

    def project_points(self, points):
        result = []
        for p in points:
            p4 = np.array([p[0], p[1], p[2], 1.0])
            cam = self.view_matrix @ p4
            if cam[2] >= 0:
                result.append(None)
                continue
            proj = self.proj_matrix @ cam
            if proj[3] != 0:
                x = proj[0] / proj[3]
                y = proj[1] / proj[3]
                screen_x = (x + 1) * 0.5 * SCREEN_WIDTH
                screen_y = (1 - (y + 1) * 0.5) * SCREEN_HEIGHT
                result.append((int(screen_x), int(screen_y)))
            else:
                result.append(None)
        return result

    def interpolate(self, other, t):
        pos = self.position * (1-t) + other.position * t
        target = self.target * (1-t) + other.target * t
        return Camera(pos, target)

# =============================================================================
# CUBOID
# =============================================================================
class Cuboid:
    def __init__(self, center, width, depth, height, color=TEAL):
        cx, cy, cz = center
        w2, d2, h2 = width/2, depth/2, height/2
        self.vertices = np.array([
            [cx-w2, cy-h2, cz-d2], [cx+w2, cy-h2, cz-d2],
            [cx+w2, cy+h2, cz-d2], [cx-w2, cy+h2, cz-d2],
            [cx-w2, cy-h2, cz+d2], [cx+w2, cy-h2, cz+d2],
            [cx+w2, cy+h2, cz+d2], [cx-w2, cy+h2, cz+d2]
        ], dtype=np.float32)
        self.edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
        self.color = color

    def transform(self, matrix):
        ones = np.ones((len(self.vertices), 1))
        verts_h = np.hstack([self.vertices, ones])
        transformed = (matrix @ verts_h.T).T
        self.vertices = transformed[:, :3]

# =============================================================================
# PIECES (Red X, Blue O)
# =============================================================================
class XPiece:
    def __init__(self, x, z, color=RED):
        self.parts = []
        length = 1.4
        thick = 0.3
        height = 0.3
        box = Cuboid((0,0,0), length, thick, height)
        angle = math.radians(45)
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        rot_mat = np.array([[cos_a,0,sin_a,0],[0,1,0,0],[-sin_a,0,cos_a,0],[0,0,0,1]])
        box.transform(rot_mat)
        box.transform(np.array([[1,0,0,x],[0,1,0,0],[0,0,1,z],[0,0,0,1]]))
        self.parts.append(box)
        box2 = Cuboid((0,0,0), length, thick, height)
        angle2 = math.radians(-45)
        cos_a2, sin_a2 = math.cos(angle2), math.sin(angle2)
        rot_mat2 = np.array([[cos_a2,0,sin_a2,0],[0,1,0,0],[-sin_a2,0,cos_a2,0],[0,0,0,1]])
        box2.transform(rot_mat2)
        box2.transform(np.array([[1,0,0,x],[0,1,0,0],[0,0,1,z],[0,0,0,1]]))
        self.parts.append(box2)
        for part in self.parts:
            part.color = color

    def draw(self, camera, surf):
        for part in self.parts:
            screen_pts = camera.project_points(part.vertices)
            for edge in part.edges:
                if screen_pts[edge[0]] and screen_pts[edge[1]]:
                    pygame.draw.line(surf, part.color, screen_pts[edge[0]], screen_pts[edge[1]], 2)

class OPiece:
    def __init__(self, x, z, color=BLUE, segments=24):
        self.color = color
        radius = 0.8
        self.vertices = []
        self.edges = []
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            px = x + radius * math.cos(angle)
            pz = z + radius * math.sin(angle)
            self.vertices.append([px, -0.15, pz])
            self.vertices.append([px, 0.15, pz])
        for i in range(segments):
            self.edges.append((i*2, (i*2+2) % (segments*2)))
            self.edges.append((i*2+1, (i*2+3) % (segments*2)))
            self.edges.append((i*2, i*2+1))

    def draw(self, camera, surf):
        screen_pts = camera.project_points(self.vertices)
        for edge in self.edges:
            if screen_pts[edge[0]] and screen_pts[edge[1]]:
                pygame.draw.line(surf, self.color, screen_pts[edge[0]], screen_pts[edge[1]], 2)

# =============================================================================
# FLOOR GRID (Animated, turn-based)
# =============================================================================
def draw_floor_grid(camera, surf, y_level=-1.2, spacing=1.0, range_min=-20, range_max=20, turn_color_hint=None):
    lines = []
    for z in np.arange(range_min, range_max+spacing, spacing):
        lines.append(((range_min, y_level, z), (range_max, y_level, z)))
    for x in np.arange(range_min, range_max+spacing, spacing):
        lines.append(((x, y_level, range_min), (x, y_level, range_max)))
    time = pygame.time.get_ticks() * 0.002
    for start, end in lines:
        p1 = camera.project_points([start])[0]
        p2 = camera.project_points([end])[0]
        if p1 and p2:
            if turn_color_hint == 'X':
                base_color = RED
            elif turn_color_hint == 'O':
                base_color = BLUE
            else:
                base_color = TEAL
            intensity = 0.3 + 0.2 * math.sin(time + start[0] * 0.5 + start[2] * 0.3)
            color = (int(base_color[0]*intensity), int(base_color[1]*intensity), int(base_color[2]*intensity))
            pygame.draw.line(surf, color, p1, p2, 1)

# =============================================================================
# BOARD CUBOIDS (3x3 grid)
# =============================================================================
def create_board_cuboids():
    cuboids = []
    # Outer border
    cuboids.append(Cuboid((0, 0, -3), 6.0, 0.2, LINE_HEIGHT, TEAL))
    cuboids.append(Cuboid((0, 0, 3), 6.0, 0.2, LINE_HEIGHT, TEAL))
    cuboids.append(Cuboid((-3, 0, 0), 0.2, 6.0, LINE_HEIGHT, TEAL))
    cuboids.append(Cuboid((3, 0, 0), 0.2, 6.0, LINE_HEIGHT, TEAL))
    for x in [-1.0, 1.0]:
        cuboids.append(Cuboid((x, 0, 0), LINE_WIDTH, 6.0, LINE_HEIGHT, TEAL))
    for z in [-1.0, 1.0]:
        cuboids.append(Cuboid((0, 0, z), 6.0, LINE_WIDTH, LINE_HEIGHT, TEAL))
    return cuboids

# =============================================================================
# GAME LOGIC & AI
# =============================================================================
class TicTacToe:
    def __init__(self):
        self.grid = [['' for _ in range(3)] for _ in range(3)]
        self.winner = None
        self.winning_cells = []

    def reset(self):
        self.grid = [['' for _ in range(3)] for _ in range(3)]
        self.winner = None
        self.winning_cells = []

    def make_move(self, row, col, player):
        if self.grid[row][col] == '' and not self.winner:
            self.grid[row][col] = player
            if self.check_winner(row, col, player):
                self.winner = player
                return True
            return True
        return False

    def check_winner(self, row, col, player):
        if all(self.grid[row][c] == player for c in range(3)):
            self.winning_cells = [(row, c) for c in range(3)]
            return True
        if all(self.grid[r][col] == player for r in range(3)):
            self.winning_cells = [(r, col) for r in range(3)]
            return True
        if row == col and all(self.grid[i][i] == player for i in range(3)):
            self.winning_cells = [(i,i) for i in range(3)]
            return True
        if row+col == 2 and all(self.grid[i][2-i] == player for i in range(3)):
            self.winning_cells = [(i,2-i) for i in range(3)]
            return True
        return False

    def is_full(self):
        return all(self.grid[r][c] != '' for r in range(3) for c in range(3))

    def empty_cells(self):
        return [(r,c) for r in range(3) for c in range(3) if self.grid[r][c] == '']

class MinimaxAI:
    def __init__(self, player, opponent):
        self.player = player
        self.opponent = opponent

    def best_move(self, board):
        best_score = -float('inf')
        best = None
        for r,c in board.empty_cells():
            board.grid[r][c] = self.player
            score = self.minimax(board, 0, False)
            board.grid[r][c] = ''
            if score > best_score:
                best_score = score
                best = (r,c)
        return best

    def minimax(self, board, depth, is_max):
        winner = board.winner
        if winner == self.player:
            return 10 - depth
        elif winner == self.opponent:
            return depth - 10
        elif board.is_full():
            return 0
        if is_max:
            best = -float('inf')
            for r,c in board.empty_cells():
                board.grid[r][c] = self.player
                best = max(best, self.minimax(board, depth+1, False))
                board.grid[r][c] = ''
            return best
        else:
            best = float('inf')
            for r,c in board.empty_cells():
                board.grid[r][c] = self.opponent
                best = min(best, self.minimax(board, depth+1, True))
                board.grid[r][c] = ''
            return best

# =============================================================================
# GAME CONTROLLER
# =============================================================================
class GameState:
    MENU, TRANSITION, PLAYING, GAME_OVER = range(4)

class GameController:
    def __init__(self):
        self.state = GameState.MENU
        self.mode = None
        self.match_type = 'single'
        self.board = TicTacToe()
        self.current_player = 'X'
        self.scores = {'X':0, 'O':0}
        self.match_winner = None
        self.ai = None
        self.particles = ParticleSystem()
        self.win_glow = 0
        self.next_round_timer = 0

    def start_match(self, mode, match_type):
        self.mode = mode
        self.match_type = match_type
        self.scores = {'X':0, 'O':0}
        self.match_winner = None
        self.start_round()

    def start_round(self):
        self.board.reset()
        self.current_player = 'X'
        self.win_glow = 0
        if self.mode == 'cpu' and self.current_player == 'O':
            self.ai = MinimaxAI('O', 'X')
            self.ai_move()

    def ai_move(self):
        if self.state != GameState.PLAYING:
            return
        move = self.ai.best_move(self.board)
        if move:
            self.make_move(move[0], move[1])

    def make_move(self, row, col):
        if self.state != GameState.PLAYING:
            return False
        if self.board.grid[row][col] != '' or self.board.winner:
            return False
        self.board.make_move(row, col, self.current_player)
        place_sound.play()
        if self.board.winner:
            self.end_round(self.board.winner)
            return True
        elif self.board.is_full():
            self.end_round(None)
            return True
        self.current_player = 'O' if self.current_player == 'X' else 'X'
        if self.mode == 'cpu' and self.current_player == 'O' and not self.board.winner and not self.board.is_full():
            self.ai_move()
        return True

    def end_round(self, winner):
        self.state = GameState.GAME_OVER
        if winner:
            self.scores[winner] += 1
            win_sound.play()
            target = 2 if self.match_type == 'best3' else 3 if self.match_type == 'best5' else None
            if target and self.scores[winner] >= target:
                self.match_winner = winner
            else:
                self.next_round_timer = pygame.time.get_ticks() + 2000
        else:
            self.next_round_timer = pygame.time.get_ticks() + 1500

    def update(self):
        if self.state == GameState.GAME_OVER and self.next_round_timer and pygame.time.get_ticks() > self.next_round_timer:
            if self.match_winner:
                self.state = GameState.MENU
            else:
                self.start_round()
                self.state = GameState.PLAYING
            self.next_round_timer = 0
        if self.board.winner:
            self.win_glow = (math.sin(pygame.time.get_ticks() * 0.01) + 1) / 2

# =============================================================================
# MAIN APPLICATION
# =============================================================================
class NeonTicTacToe3D:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Neon Wireframe Tic-Tac-Toe")
        self.clock = pygame.time.Clock()
        self.font_small = pygame.font.Font(None, 28)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_large = pygame.font.Font(None, 48)

        self.board_cuboids = create_board_cuboids()
        self.pieces = [[None for _ in range(3)] for _ in range(3)]
        self.game = GameController()
        self.camera_menu = Camera((8, 6, 8), (0,0,0))
        self.camera_play = Camera((0, 8, 10), (0,0,0))
        self.current_camera = self.camera_menu
        self.transition_t = 1.0
        self.setup_menu_buttons()

    def setup_menu_buttons(self):
        btn_w, btn_h = 220, 50
        cx = SCREEN_WIDTH // 2 - btn_w//2
        y = SCREEN_HEIGHT//2 + 40
        self.menu_buttons = [
            Button(cx, y, btn_w, btn_h, "Solo (2 Players)", lambda: self.start_game('solo')),
            Button(cx, y+70, btn_w, btn_h, "CPU (Unbeatable)", lambda: self.start_game('cpu')),
            Button(cx-120, y+140, 100, 40, "Single", lambda: self.set_match('single')),
            Button(cx-10, y+140, 100, 40, "Best of 3", lambda: self.set_match('best3')),
            Button(cx+100, y+140, 100, 40, "Best of 5", lambda: self.set_match('best5'))
        ]
        self.selected_match = 'single'

    def set_match(self, match):
        self.selected_match = match

    def start_game(self, mode):
        self.game.start_match(mode, self.selected_match)
        self.game.state = GameState.TRANSITION
        self.transition_t = 0.0
        self.transition_start = pygame.time.get_ticks()
        self.transition_duration = 1.5

    def update_transition(self):
        elapsed = (pygame.time.get_ticks() - self.transition_start) / 1000.0
        t = min(1.0, elapsed / self.transition_duration)
        ease = t * t * (3 - 2*t)
        self.transition_t = ease
        self.current_camera = self.camera_menu.interpolate(self.camera_play, ease)
        if t >= 1.0:
            self.game.state = GameState.PLAYING
            self.current_camera = self.camera_play

    def update_menu_rotation(self):
        if self.game.state == GameState.MENU:
            angle = pygame.time.get_ticks() * 0.002
            orbit_rad = math.radians(angle * 30)
            x = 8 * math.cos(orbit_rad)
            z = 8 * math.sin(orbit_rad)
            self.camera_menu.position = np.array([x, 5, z])
            self.camera_menu.target = np.array([0,0,0])
            self.camera_menu.update_matrices()
            self.current_camera = self.camera_menu

    def draw_board_and_pieces(self, surf):
        turn_hint = self.game.current_player if self.game.state == GameState.PLAYING else None
        draw_floor_grid(self.current_camera, surf, y_level=-1.0, spacing=1.0, turn_color_hint=turn_hint)

        for cuboid in self.board_cuboids:
            verts_screen = self.current_camera.project_points(cuboid.vertices)
            for edge in cuboid.edges:
                if verts_screen[edge[0]] and verts_screen[edge[1]]:
                    pygame.draw.line(surf, cuboid.color, verts_screen[edge[0]], verts_screen[edge[1]], 2)

        for r in range(3):
            for c in range(3):
                cell_val = self.game.board.grid[r][c]
                if cell_val and self.pieces[r][c] is None:
                    x = BOARD_MIN + c * CELL_SIZE + CELL_SIZE/2
                    z = BOARD_MIN + r * CELL_SIZE + CELL_SIZE/2
                    if cell_val == 'X':
                        self.pieces[r][c] = XPiece(x, z, RED)
                    else:
                        self.pieces[r][c] = OPiece(x, z, BLUE)
                if self.pieces[r][c]:
                    if self.game.board.winner and (r,c) in self.game.board.winning_cells:
                        glow_color = (255, int(200 + 55*self.game.win_glow), 100)
                        if isinstance(self.pieces[r][c], XPiece):
                            for part in self.pieces[r][c].parts:
                                old = part.color
                                part.color = glow_color
                                part.draw(self.current_camera, surf)
                                part.color = old
                        else:
                            old = self.pieces[r][c].color
                            self.pieces[r][c].color = glow_color
                            self.pieces[r][c].draw(self.current_camera, surf)
                            self.pieces[r][c].color = old
                    else:
                        self.pieces[r][c].draw(self.current_camera, surf)

        if self.game.board.winner:
            dim_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            dim_surf.fill((0,0,0, 150))
            surf.blit(dim_surf, (0,0))

    def draw_ui(self, surf):
        if self.game.state in (GameState.PLAYING, GameState.GAME_OVER):
            if self.game.match_type != 'single':
                target = 2 if self.game.match_type == 'best3' else 3
                text = f"Score: X {self.game.scores['X']} - {self.game.scores['O']} O  (First to {target})"
                txt = self.font_medium.render(text, True, WHITE)
                surf.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2, 20))
            if self.game.state == GameState.PLAYING and not self.game.board.winner:
                turn = self.font_small.render(f"Turn: {self.game.current_player}", True, TEAL)
                surf.blit(turn, (20, SCREEN_HEIGHT-50))
            if self.game.state == GameState.GAME_OVER:
                if self.game.match_winner:
                    msg = f"Player {self.game.match_winner} wins the match!"
                elif self.game.board.winner:
                    msg = f"Player {self.game.board.winner} wins this round!"
                else:
                    msg = "It's a tie!"
                msg_surf = self.font_large.render(msg, True, MAGENTA)
                surf.blit(msg_surf, (SCREEN_WIDTH//2 - msg_surf.get_width()//2, SCREEN_HEIGHT//2 - 60))
            btn = Button(SCREEN_WIDTH-150, SCREEN_HEIGHT-60, 130, 40, "Menu", self.return_to_menu)
            btn.draw(surf)
        elif self.game.state == GameState.MENU:
            title = self.font_large.render("NEON WIREFRAME TIC-TAC-TOE", True, TEAL)
            surf.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
            for btn in self.menu_buttons:
                btn.draw(surf)
            match_str = "Single" if self.selected_match=='single' else "Best of 3" if self.selected_match=='best3' else "Best of 5"
            match_txt = self.font_small.render(f"Match: {match_str}", True, WHITE)
            surf.blit(match_txt, (SCREEN_WIDTH//2 - match_txt.get_width()//2, SCREEN_HEIGHT//2 + 190))

    def return_to_menu(self):
        self.game.state = GameState.MENU
        self.game.match_winner = None
        self.pieces = [[None for _ in range(3)] for _ in range(3)]
        self.transition_t = 1.0
        self.current_camera = self.camera_menu

    def handle_click(self, pos):
        if self.game.state != GameState.PLAYING:
            return
        cell_centers = []
        for r in range(3):
            for c in range(3):
                x = BOARD_MIN + c * CELL_SIZE + CELL_SIZE/2
                z = BOARD_MIN + r * CELL_SIZE + CELL_SIZE/2
                screen = self.current_camera.project_points([(x, 0.2, z)])[0]
                if screen:
                    cell_centers.append((r, c, screen))
        min_dist = 50
        chosen = None
        for r,c,scr in cell_centers:
            dist = ((scr[0]-pos[0])**2 + (scr[1]-pos[1])**2)**0.5
            if dist < min_dist:
                min_dist = dist
                chosen = (r,c)
        if chosen:
            self.game.make_move(chosen[0], chosen[1])
            screen_center = self.current_camera.project_points([(BOARD_MIN + chosen[1]*CELL_SIZE+CELL_SIZE/2, 0.2, BOARD_MIN + chosen[0]*CELL_SIZE+CELL_SIZE/2)])[0]
            if screen_center:
                self.game.particles.burst(screen_center[0], screen_center[1])

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                elif event.type == KEYDOWN and event.key == K_ESCAPE:
                    if self.game.state != GameState.MENU:
                        self.return_to_menu()
                elif event.type == MOUSEBUTTONDOWN:
                    if self.game.state == GameState.MENU:
                        for btn in self.menu_buttons:
                            btn.handle_event(event)
                    elif self.game.state in (GameState.PLAYING, GameState.GAME_OVER):
                        ret_rect = pygame.Rect(SCREEN_WIDTH-150, SCREEN_HEIGHT-60, 130, 40)
                        if ret_rect.collidepoint(event.pos):
                            self.return_to_menu()
                        else:
                            self.handle_click(event.pos)
                elif event.type == MOUSEMOTION:
                    if self.game.state == GameState.MENU:
                        for btn in self.menu_buttons:
                            btn.handle_event(event)

            if self.game.state == GameState.TRANSITION:
                self.update_transition()
            elif self.game.state in (GameState.PLAYING, GameState.GAME_OVER):
                self.game.update()
                self.game.particles.update(dt)
            else:
                self.update_menu_rotation()

            self.screen.fill(BLACK)
            self.draw_board_and_pieces(self.screen)
            self.game.particles.draw(self.screen)
            self.draw_ui(self.screen)
            pygame.display.flip()

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = NeonTicTacToe3D()
    game.run()