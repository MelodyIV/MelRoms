import pygame
import math
import random
WIDTH, HEIGHT = 800, 600
FPS = 60
MIKU_TEAL = (57, 197, 187)
MIKU_PINK = (255, 106, 170)
DARK_BLUE = (10, 10, 26)
WHITE = (255, 255, 255)
FOV = 350
CAMERA_Z = -500

class MikuPong:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=1)
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("MelRoms // Cyber-Pong 3D")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Courier New", 24, bold=True)  # smaller font
        
        self.running = True
        self.paused = False
        self.shake_intensity = 0
        self.last_sound_time = 0
        
        self.score_l = 0
        self.score_r = 0
        self.win_score = 10

        self.reset_ball()
        self.paddle_l_y = 0
        self.paddle_r_y = 0
        self.paddle_speed = 11          
        self.ai_difficulty = 0.25
        
        self.particles = []
        self.ball_trail = []
        self.decorations = []
        for _ in range(20):  
            x = random.uniform(-470, 470)  
            y = random.choice([-250, 250])
            z = random.uniform(80, 940)     
            size = random.uniform(8, 32)  
            color = random.choice([MIKU_TEAL, MIKU_PINK, (100, 100, 255)])
            self.decorations.append({
                'pos': [x, y, z], 
                'size': [size, size, size], 
                'color': color,
                'active': True
            })

    def reset_ball(self):
        self.ball_pos = [0.0, 0.0, 0.0]
        side = 1 if random.random() > 0.5 else -1
        self.ball_vel = [7.0 * side, random.uniform(-3.5, 3.5), 0.0]  
        self.ball_trail = []

    def play_sfx(self, type='hit'):
        now = pygame.time.get_ticks()
        if now - self.last_sound_time < 80: return
        self.last_sound_time = now

        sample_rate = 44100
        buf = bytearray()
        
        if type == 'hit':
            freq, duration, decay_rate = 880, 0.1, -25
        elif type == 'score':
            freq, duration, decay_rate = 1320, 0.2, -10
        else:
            freq, duration, decay_rate = 110, 0.3, -5

        n_samples = int(sample_rate * duration)
        for i in range(n_samples):
            t = i / sample_rate
            if type == 'fail':
                val = 40 if math.sin(2 * math.pi * freq * t) > 0 else -40
            else:
                val = int(127 * (2 / math.pi) * math.asin(math.sin(2 * math.pi * freq * t)))
            decay = math.exp(decay_rate * t) 
            buf.append(int(val * decay) + 128)
        
        try:
            sound = pygame.mixer.Sound(buffer=buf)
            sound.set_volume(0.1)
            sound.play()
        except: pass

    def project(self, x, y, z):
        factor = FOV / (max(0.1, z - CAMERA_Z))
        return int(x * factor + WIDTH // 2), int(y * factor + HEIGHT // 2)

    def draw_wireframe_cube(self, pos, size, color, thickness=1, rot=0):
        w, h, d = size
        x_p, y_p, z_p = pos
        c, s = math.cos(rot), math.sin(rot)
        
        verts = [(-w,-h,-d),(w,-h,-d),(w,h,-d),(-w,h,-d),(-w,-h,d),(w,-h,d),(w,h,d),(-w,h,d)]
        pts = []
        for v in verts:
            rx = v[0] * c - v[2] * s
            rz = v[0] * s + v[2] * c
            pts.append(self.project(rx + x_p, v[1] + y_p, rz + z_p))

        for i in range(4):
            pygame.draw.line(self.screen, color, pts[i], pts[(i+1)%4], thickness)
            pygame.draw.line(self.screen, color, pts[i+4], pts[(i+4+1)%4 if i<3 else 4], thickness)
            pygame.draw.line(self.screen, color, pts[i], pts[i+4], thickness)

    def update(self):
        if self.paused: return

        prev_x = self.ball_pos[0]
        self.ball_pos[0] += self.ball_vel[0]
        self.ball_pos[1] += self.ball_vel[1]
        
        self.ball_trail.append(list(self.ball_pos))
        if len(self.ball_trail) > 8: self.ball_trail.pop(0)
        self.paddle_r_y += (self.ball_pos[1] - self.paddle_r_y) * self.ai_difficulty
        if abs(self.ball_pos[1]) > 220:  
            self.ball_vel[1] *= -1
            self.ball_pos[1] = 220 if self.ball_pos[1] > 0 else -220
            self.play_sfx('hit')
        px = 285         
        paddle_depth = 10
        
        if prev_x > -px and self.ball_pos[0] <= -px:
            if abs(self.ball_pos[1] - self.paddle_l_y) < 70 and abs(self.ball_pos[2]) < paddle_depth:  # hit height scaled
                self.ball_vel[0] = abs(self.ball_vel[0]) + 0.4
                self.ball_vel[1] += (self.ball_pos[1] - self.paddle_l_y) * 0.15
                self.play_sfx('hit')
                self.ball_pos[0] = -px

        if prev_x < px and self.ball_pos[0] >= px:
            if abs(self.ball_pos[1] - self.paddle_r_y) < 70 and abs(self.ball_pos[2]) < paddle_depth:
                self.ball_vel[0] = -abs(self.ball_vel[0]) - 0.4
                self.ball_vel[1] += (self.ball_pos[1] - self.paddle_r_y) * 0.15
                self.play_sfx('hit')
                self.ball_pos[0] = px
        for d in self.decorations:
            cx, cy, cz = d['pos']
            sx, sy, sz = d['size']
            if (abs(self.ball_pos[0] - cx) < sx and
                abs(self.ball_pos[1] - cy) < sy and
                abs(self.ball_pos[2] - cz) < sz):
                dx = self.ball_pos[0] - cx
                dy = self.ball_pos[1] - cy
                dz = self.ball_pos[2] - cz
                abs_dx, abs_dy, abs_dz = abs(dx), abs(dy), abs(dz)
                if abs_dx < abs_dy and abs_dx < abs_dz:
                    self.ball_vel[0] *= -1
                elif abs_dy < abs_dx and abs_dy < abs_dz:
                    self.ball_vel[1] *= -1
                else:
                    self.ball_vel[2] *= -1
                self.play_sfx('hit')
                self.ball_pos[0] += self.ball_vel[0] * 0.1
                self.ball_pos[1] += self.ball_vel[1] * 0.1
        if abs(self.ball_pos[0]) > 470:  
            if self.ball_pos[0] > 0:
                self.score_l += 1
                self.play_sfx('score')
            else:
                self.score_r += 1
                self.play_sfx('fail')
            self.shake_intensity = 20
            self.reset_ball()
    def draw(self):
        self.screen.fill(DARK_BLUE)
        for d in self.decorations:
            self.draw_wireframe_cube(d['pos'], d['size'], d['color'], 1)
        txt = self.font.render(f"{self.score_l} - {self.score_r}", True, MIKU_TEAL)
        self.screen.blit(txt, (WIDTH//2 - txt.get_width()//2, 30))
        for p in self.ball_trail:
            pygame.draw.circle(self.screen, (30, 70, 70), self.project(p[0], p[1], p[2]), 2)
        r = pygame.time.get_ticks() * 0.003
        self.draw_wireframe_cube(self.ball_pos, [10,10,10], MIKU_TEAL, 2, rot=r)  
        self.draw_wireframe_cube([-300, self.paddle_l_y, 0], [8, 55, 16], MIKU_TEAL, 3)  
        self.draw_wireframe_cube([300, self.paddle_r_y, 0], [8, 55, 16], MIKU_PINK, 3)
        pygame.display.flip()
    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: self.running = False
            k = pygame.key.get_pressed()
            if k[pygame.K_w] or k[pygame.K_UP]: self.paddle_l_y -= self.paddle_speed
            if k[pygame.K_s] or k[pygame.K_DOWN]: self.paddle_l_y += self.paddle_speed
            self.paddle_l_y = max(-190, min(190, self.paddle_l_y))  # scaled limits
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
if __name__ == "__main__":
    MikuPong().run()