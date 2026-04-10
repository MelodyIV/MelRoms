import pygame
import sys
import math
import colorsys
from py_particles_module import Environment, InteractionMode

# Constants
WIDTH, HEIGHT = 1200, 800
FPS = 60
DEFAULT_PARTICLE_COUNT = 60
MAX_PARTICLES = 300
GUI_BG_COLOR = (30, 30, 40, 220)
GUI_BORDER_COLOR = (70, 130, 180)
GUI_TEXT_COLOR = (220, 220, 240)
SLIDER_HEIGHT = 25
SLIDER_WIDTH = 180
BUTTON_HEIGHT = 35
BUTTON_WIDTH = 120

class Slider:
    def __init__(self, x, y, width, min_val, max_val, default_val, label, value_format="{:.2f}"):
        self.rect = pygame.Rect(x, y, width, SLIDER_HEIGHT)
        self.min_val = min_val
        self.max_val = max_val
        self.value = default_val
        self.label = label
        self.value_format = value_format
        self.dragging = False
        self.handle_radius = 8
        self.show_tooltip = False
        
    def get_handle_x(self):
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        return self.rect.x + ratio * self.rect.width
        
    def draw(self, surface, font):
        # Draw slider track
        pygame.draw.rect(surface, (60, 60, 70), self.rect, border_radius=4)
        pygame.draw.rect(surface, (80, 80, 90), self.rect, 2, border_radius=4)
        
        # Draw filled portion
        fill_width = (self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
        pygame.draw.rect(surface, (100, 150, 220, 120), fill_rect, border_radius=4)
        
        # Draw handle
        handle_x = self.get_handle_x()
        handle_y = self.rect.centery
        pygame.draw.circle(surface, (100, 150, 220), (int(handle_x), handle_y), self.handle_radius)
        pygame.draw.circle(surface, (240, 240, 255), (int(handle_x), handle_y), self.handle_radius - 2, 2)
        
        # Draw label and value
        label_text = f"{self.label}: {self.value_format.format(self.value)}"
        label_surf = font.render(label_text, True, GUI_TEXT_COLOR)
        surface.blit(label_surf, (self.rect.x, self.rect.y - 22))
        
        # Draw tooltip if hovering
        if self.show_tooltip:
            tooltip = f"Range: [{self.min_val}, {self.max_val}]"
            tooltip_surf = font.render(tooltip, True, (220, 220, 180))
            surface.blit(tooltip_surf, (self.rect.x, self.rect.y + self.rect.height + 5))
        
    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                handle_x = self.get_handle_x()
                handle_rect = pygame.Rect(handle_x - self.handle_radius, 
                                         self.rect.centery - self.handle_radius,
                                         self.handle_radius * 2, self.handle_radius * 2)
                if handle_rect.collidepoint(mouse_pos) or self.rect.collidepoint(mouse_pos):
                    self.dragging = True
                    self.update_value_from_mouse(mouse_pos[0])
                    
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
                
        elif event.type == pygame.MOUSEMOTION:
            # Update hover state
            self.show_tooltip = self.rect.collidepoint(mouse_pos)
            
            if self.dragging:
                self.update_value_from_mouse(mouse_pos[0])
                
    def update_value_from_mouse(self, mouse_x):
        rel_x = max(0, min(mouse_x - self.rect.x, self.rect.width))
        ratio = rel_x / self.rect.width
        self.value = self.min_val + ratio * (self.max_val - self.min_val)

class Button:
    def __init__(self, x, y, width, height, text, color=(80, 130, 200), hover_color=(100, 160, 230)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.hovered = False
        
    def draw(self, surface, font):
        color = self.hover_color if self.hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        pygame.draw.rect(surface, (200, 200, 220), self.rect, 2, border_radius=6)
        
        text_surf = font.render(self.text, True, GUI_TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        self.hovered = self.rect.collidepoint(mouse_pos)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.hovered:
                return True
        return False

class ParticleLifeGUI:
    def __init__(self, simulation):
        self.simulation = simulation
        self.visible = True
        
        # Fonts
        self.title_font = pygame.font.Font(None, 32)
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
        
        # GUI elements
        self.sliders = []
        self.buttons = []
        self.init_gui_elements()
        
    def init_gui_elements(self):
        x, y = 20, 60
        
        # Physics sliders
        self.sliders.append(Slider(x, y, SLIDER_WIDTH, -10, 10, 0, "Gravity"))
        y += 40
        self.sliders.append(Slider(x, y, SLIDER_WIDTH, 50, 500, 200, "Attraction", "{:.0f}"))
        y += 40
        self.sliders.append(Slider(x, y, SLIDER_WIDTH, 50, 500, 100, "Repulsion", "{:.0f}"))
        y += 40
        self.sliders.append(Slider(x, y, SLIDER_WIDTH, 50, 300, 150, "Int Radius", "{:.0f}"))
        y += 40
        self.sliders.append(Slider(x, y, SLIDER_WIDTH, 10, 100, 40, "Coll Radius", "{:.0f}"))
        y += 40
        self.sliders.append(Slider(x, y, SLIDER_WIDTH, 100, 1000, 500, "Coll Strength", "{:.0f}"))
        y += 40
        self.sliders.append(Slider(x, y, SLIDER_WIDTH, 0.95, 1.0, 0.99, "Friction"))
        y += 60
        
        # Particle controls
        self.sliders.append(Slider(x, y, SLIDER_WIDTH, 1, MAX_PARTICLES, 60, "Count", "{:.0f}"))
        y += 40
        self.sliders.append(Slider(x, y, SLIDER_WIDTH, 1, 10, 5, "Types", "{:.0f}"))
        y += 40
        self.sliders.append(Slider(x, y, SLIDER_WIDTH, 0.1, 5.0, 1.0, "Speed", "{:.2f}"))
        y += 60
        
        # Buttons
        button_x = x
        self.buttons.append(Button(button_x, y, BUTTON_WIDTH, BUTTON_HEIGHT, "Add Particles"))
        y += 45
        self.buttons.append(Button(button_x, y, BUTTON_WIDTH, BUTTON_HEIGHT, "Clear All"))
        y += 45
        self.buttons.append(Button(button_x, y, BUTTON_WIDTH, BUTTON_HEIGHT, "Randomize Forces"))
        y += 45
        
        # Interaction mode buttons
        mode_button_width = 110
        button_x = 20
        self.buttons.append(Button(button_x, y, mode_button_width, BUTTON_HEIGHT, 
                                  "Attract", (60, 180, 80)))
        button_x += mode_button_width + 10
        self.buttons.append(Button(button_x, y, mode_button_width, BUTTON_HEIGHT,
                                  "Repel", (180, 60, 80)))
        button_x += mode_button_width + 10
        self.buttons.append(Button(button_x, y, mode_button_width, BUTTON_HEIGHT,
                                  "Neutral", (100, 100, 150)))
        
    def draw(self, surface):
        if not self.visible:
            return
            
        # Draw GUI background
        gui_width = 240
        gui_surface = pygame.Surface((gui_width, HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(gui_surface, GUI_BG_COLOR, (0, 0, gui_width, HEIGHT))
        pygame.draw.rect(gui_surface, GUI_BORDER_COLOR, (0, 0, gui_width, HEIGHT), 3)
        
        # Draw title
        title = self.title_font.render("PARTICLE LIFE", True, (100, 200, 255))
        gui_surface.blit(title, (20, 15))
        
        subtitle = self.small_font.render("Press Y to hide/show GUI", True, GUI_TEXT_COLOR)
        gui_surface.blit(subtitle, (20, 45))
        
        # Draw sliders and buttons
        for slider in self.sliders:
            slider.draw(gui_surface, self.font)
            
        for button in self.buttons:
            button.draw(gui_surface, self.font)
        
        # Draw force matrix
        self.draw_force_matrix(gui_surface, 20, HEIGHT - 180, 200, 150)
        
        # Blit GUI to main surface
        surface.blit(gui_surface, (0, 0))
        
    def draw_force_matrix(self, surface, x, y, width, height):
        """Draw visualization of force matrix"""
        matrix_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, (40, 40, 50), matrix_rect, border_radius=4)
        pygame.draw.rect(surface, (70, 70, 90), matrix_rect, 2, border_radius=4)
        
        title = self.small_font.render("Force Matrix", True, GUI_TEXT_COLOR)
        surface.blit(title, (x + 10, y + 5))
        
        # Draw matrix cells
        cell_size = min(25, (width - 40) // self.simulation.num_types)
        start_x = x + 20
        start_y = y + 30
        
        for i in range(self.simulation.num_types):
            for j in range(self.simulation.num_types):
                cell_x = start_x + i * cell_size
                cell_y = start_y + j * cell_size
                
                force = self.simulation.force_matrix[i][j]
                
                # Color based on force value
                if force > 0:
                    intensity = min(255, int(force * 150))
                    color = (50, 150 + intensity//2, 50)
                else:
                    intensity = min(255, int(-force * 150))
                    color = (150 + intensity//2, 50, 50)
                    
                pygame.draw.rect(surface, color, (cell_x, cell_y, cell_size, cell_size))
                pygame.draw.rect(surface, (80, 80, 100), (cell_x, cell_y, cell_size, cell_size), 1)
                
                # Draw force value
                if cell_size > 20:
                    value_text = self.small_font.render(f"{force:.1f}", True, 
                                                       GUI_TEXT_COLOR if abs(force) < 0.5 else (255, 255, 255))
                    text_rect = value_text.get_rect(center=(cell_x + cell_size//2, 
                                                          cell_y + cell_size//2))
                    surface.blit(value_text, text_rect)
        
        # Draw labels
        for i in range(self.simulation.num_types):
            # Column labels (top)
            hue = i / self.simulation.num_types
            r, g, b = [int(255 * c) for c in colorsys.hsv_to_rgb(hue, 0.8, 0.9)]
            label_color = (r, g, b)
            
            label_x = start_x + i * cell_size + cell_size//2
            label = self.small_font.render(str(i), True, label_color)
            label_rect = label.get_rect(center=(label_x, start_y - 10))
            surface.blit(label, label_rect)
            
            # Row labels (left)
            label_y = start_y + i * cell_size + cell_size//2
            label = self.small_font.render(str(i), True, label_color)
            label_rect = label.get_rect(center=(start_x - 10, label_y))
            surface.blit(label, label_rect)
            
    def handle_event(self, event):
        if not self.visible:
            return
            
        # Handle sliders
        for slider in self.sliders:
            slider.handle_event(event)
            
        # Handle buttons
        for i, button in enumerate(self.buttons):
            if button.handle_event(event):
                if i == 0:  # Add Particles
                    target_count = int(self.sliders[7].value)
                    current_count = len(self.simulation.particles)
                    if current_count < target_count:
                        self.simulation.add_particles(target_count - current_count)
                elif i == 1:  # Clear All
                    self.simulation.clear_particles()
                elif i == 2:  # Randomize Forces
                    self.simulation.force_matrix = self.simulation._generate_force_matrix()
                elif i == 3:  # Attract mode
                    self.simulation.interaction_mode = InteractionMode.ATTRACT
                elif i == 4:  # Repel mode
                    self.simulation.interaction_mode = InteractionMode.REPEL
                elif i == 5:  # Neutral mode
                    self.simulation.interaction_mode = InteractionMode.NEUTRAL
                    
    def update_simulation_params(self):
        """Update simulation from GUI controls"""
        if not self.visible:
            return
            
        self.simulation.gravity = self.sliders[0].value
        self.simulation.interaction_strength = self.sliders[1].value
        self.simulation.collision_strength = self.sliders[5].value
        self.simulation.interaction_radius = self.sliders[3].value
        self.simulation.collision_radius = self.sliders[4].value
        self.simulation.friction = self.sliders[6].value
        self.simulation.speed_multiplier = self.sliders[9].value
        
        # Update particle count
        target_count = int(self.sliders[7].value)
        current_count = len(self.simulation.particles)
        if target_count > current_count:
            self.simulation.add_particles(target_count - current_count)
        elif target_count < current_count:
            self.simulation.remove_particles(current_count - target_count)
            
        # Update number of particle types
        new_num_types = int(self.sliders[8].value)
        if new_num_types != self.simulation.num_types:
            self.simulation.num_types = new_num_types
            self.simulation.force_matrix = self.simulation._generate_force_matrix()

def draw_particle(surface, particle, show_trails=True):
    """Draw a particle with its trail"""
    # Draw trail
    if show_trails and len(particle.trail) > 1:
        for i in range(1, len(particle.trail)):
            alpha = int(255 * (i / len(particle.trail)))
            color = (*particle.trail[i][2], alpha)
            start_pos = (int(particle.trail[i-1][0]), int(particle.trail[i-1][1]))
            end_pos = (int(particle.trail[i][0]), int(particle.trail[i][1]))
            
            if abs(end_pos[0] - start_pos[0]) > 0 or abs(end_pos[1] - start_pos[1]) > 0:
                pygame.draw.line(surface, color, start_pos, end_pos, 2)
    
    # Draw particle
    size = int(particle.size)
    
    # Create particle surface with alpha
    particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
    
    # Draw gradient effect
    center_color = (min(255, particle.colour[0] + 50), 
                   min(255, particle.colour[1] + 50), 
                   min(255, particle.colour[2] + 50))
    
    pygame.draw.circle(particle_surf, center_color, (size, size), size)
    pygame.draw.circle(particle_surf, particle.colour, (size, size), size, 2)
    
    # Add rotation
    angle = math.degrees(particle.rotation)
    rotated = pygame.transform.rotate(particle_surf, angle)
    surface.blit(rotated, (int(particle.x - rotated.get_width()/2), 
                          int(particle.y - rotated.get_height()/2)))

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Particle Life Simulation - Press Y for GUI, Shift/Ctrl for speed")
    clock = pygame.time.Clock()
    
    # Initialize simulation and GUI
    simulation = Environment((WIDTH, HEIGHT))
    simulation.add_particles(DEFAULT_PARTICLE_COUNT)
    gui = ParticleLifeGUI(simulation)
    
    # Font for stats
    stats_font = pygame.font.Font(None, 24)
    
    # Mouse interaction
    selected_particle = None
    show_trails = True
    
    # Speed control
    speed_step = 0.1
    min_speed = 0.1
    max_speed = 5.0
    
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # Delta time in seconds
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_y:
                    gui.visible = not gui.visible  # FIXED: Toggle GUI visibility
                elif event.key == pygame.K_SPACE:
                    simulation.clear_particles()
                    simulation.add_particles(DEFAULT_PARTICLE_COUNT)
                elif event.key == pygame.K_t:
                    show_trails = not show_trails
                elif event.key == pygame.K_g:
                    simulation.gravity = -simulation.gravity if simulation.gravity != 0 else 9.8
                elif event.key == pygame.K_a:
                    simulation.interaction_mode = InteractionMode.ATTRACT
                elif event.key == pygame.K_s:
                    simulation.interaction_mode = InteractionMode.REPEL
                elif event.key == pygame.K_d:
                    simulation.interaction_mode = InteractionMode.NEUTRAL
                elif event.key == pygame.K_1:
                    simulation.add_particles(10)
                elif event.key == pygame.K_2:
                    simulation.add_particles(50)
                    
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                simulation.width = event.w
                simulation.height = event.h
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    selected_particle = simulation.find_particle(pygame.mouse.get_pos())
                    
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    selected_particle = None
                    
            # Handle GUI events
            gui.handle_event(event)
        
        # Handle continuous key states for speed control
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            simulation.speed_multiplier = min(max_speed, simulation.speed_multiplier + speed_step * dt * 10)
        if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
            simulation.speed_multiplier = max(min_speed, simulation.speed_multiplier - speed_step * dt * 10)
        
        # Update particle with mouse if selected
        if selected_particle:
            selected_particle.mouse_move(pygame.mouse.get_pos(), simulation.speed_multiplier)
        
        # Update simulation parameters from GUI
        gui.update_simulation_params()
        
        # Update simulation
        simulation.update(dt)
        
        # Draw everything
        screen.fill(simulation.colour)
        
        # Draw background grid
        grid_size = 50
        for x in range(0, WIDTH, grid_size):
            pygame.draw.line(screen, (30, 30, 40), (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT, grid_size):
            pygame.draw.line(screen, (30, 30, 40), (0, y), (WIDTH, y), 1)
        
        # Draw particles
        for particle in simulation.particles:
            draw_particle(screen, particle, show_trails)
        
        # Draw GUI
        gui.draw(screen)  # This now respects gui.visible
        
        # Draw stats
        fps = clock.get_fps()
        stats = [
            f"Particles: {len(simulation.particles)}",
            f"FPS: {fps:.1f}",
            f"Mode: {simulation.interaction_mode.name}",
            f"Gravity: {simulation.gravity:.2f}",
            f"Speed: {simulation.speed_multiplier:.2f}x",
            f"Hold SHIFT/CTRL to change speed"
        ]
        
        y = 10
        for stat in stats:
            text = stats_font.render(stat, True, GUI_TEXT_COLOR)
            screen.blit(text, (WIDTH - text.get_width() - 10, y))
            y += 25
        
        # Draw help text
        help_text = [
            "CONTROLS:",
            "Y: Toggle GUI (visible)",
            "ESC: Quit",
            "SPACE: Reset",
            "T: Toggle trails",
            "G: Toggle gravity",
            "A/S/D: Attract/Repel/Neutral",
            "1/2: Add 10/50 particles",
            "SHIFT: Speed up",
            "CTRL: Slow down"
        ]
        
        y = HEIGHT - len(help_text) * 20 - 10
        for text in help_text:
            text_surf = stats_font.render(text, True, GUI_TEXT_COLOR)
            screen.blit(text_surf, (WIDTH - text_surf.get_width() - 10, y))
            y += 20
        
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()