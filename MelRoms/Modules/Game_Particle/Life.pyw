import pygame
import sys
import math
import random
import colorsys

# ==================== OPTIMIZATION: SPATIAL GRID ====================
class SpatialGrid:
    """Optimization: Only check nearby particles instead of all-to-all"""
    def __init__(self, width, height, cell_size):
        self.cell_size = cell_size
        self.cols = int(width / cell_size) + 1
        self.rows = int(height / cell_size) + 1
        self.grid = [[[] for _ in range(self.rows)] for _ in range(self.cols)]
    
    def clear(self):
        self.grid = [[[] for _ in range(self.rows)] for _ in range(self.cols)]
    
    def add_particle(self, particle):
        col = int(particle.x / self.cell_size)
        row = int(particle.y / self.cell_size)
        if 0 <= col < self.cols and 0 <= row < self.rows:
            self.grid[col][row].append(particle)
    
    def get_nearby(self, particle, radius):
        """Get particles within radius using grid cells"""
        nearby = []
        col = int(particle.x / self.cell_size)
        row = int(particle.y / self.cell_size)
        
        cells_to_check = int(radius / self.cell_size) + 1
        for dc in range(-cells_to_check, cells_to_check + 1):
            for dr in range(-cells_to_check, cells_to_check + 1):
                check_col = col + dc
                check_row = row + dr
                if 0 <= check_col < self.cols and 0 <= check_row < self.rows:
                    nearby.extend(self.grid[check_col][check_row])
        
        return nearby

# ==================== PARTICLE PHYSICS ====================
class Particle:
    def __init__(self, pos, type_id, num_types, base_size=3.0):
        self.x, self.y = pos
        self.type = type_id
        self.base_size = base_size  # Store base size
        self.size = base_size * random.uniform(0.8, 1.2)  # Random variation
        self.vx = random.uniform(-1, 1)
        self.vy = random.uniform(-1, 1)
        
        # Color based on type
        if type_id == 3:  # Purple (formerly yellow)
            r, g, b = (180, 50, 220)  # Purple color
        else:
            hue = type_id / num_types
            r, g, b = [int(255 * c) for c in colorsys.hsv_to_rgb(hue, 0.8, 0.9)]
        self.color = (r, g, b)
        self.trail = []
        self.max_trail = 10
        self.health = 100.0

class ParticleSim:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.particles = []
        self.num_types = 4
        
        # Advanced default force matrix
        self.force_matrix = [
            [-0.32, -0.17, 0.34, 0.15],   # Red behavior
            [-0.34, -0.10, 0.00, -0.25],  # Green behavior
            [-0.20, 0.00, 0.15, 0.30],    # Blue behavior
            [0.25, -0.30, 0.10, -0.15]    # Purple behavior
        ]
        
        # Physics settings
        self.interaction_radius = 80
        self.collision_radius = 15  # Short-range collision radius
        self.friction = 0.5
        self.gravity = 0.0
        self.speed_multiplier = 1.0
        self.particle_scale = 1.0  # Global size multiplier
        
        # Force falloff settings
        self.attraction_radius = 60  # Radius for attraction forces
        self.repulsion_radius = 40   # Radius for repulsion forces
        self.force_falloff = 1.0     # How quickly forces diminish with distance
        
        # Collision settings
        self.collision_strength = 5.0  # How strong particle collisions are
        self.enable_collisions = True  # Toggle for collision physics
        
        # Optimization: Spatial grid
        self.grid = SpatialGrid(width, height, cell_size=100)
        
        # Performance tracking
        self.update_time = 0
        self.interaction_checks = 0
        self.current_preset = "Default"  # Track current preset

    def add_particles(self, count):
        particles_per_type = max(1, count // self.num_types)
        new_particles = []
        
        for type_id in range(self.num_types):
            for _ in range(particles_per_type):
                x = random.uniform(50, self.width-50)
                y = random.uniform(50, self.height-50)
                # Base size of 3, will be scaled by particle_scale
                particle = Particle((x, y), type_id, self.num_types, base_size=3.0)
                new_particles.append(particle)
        
        self.particles.extend(new_particles)
        self.update_grid()
    
    def update_grid(self):
        self.grid.clear()
        for particle in self.particles:
            self.grid.add_particle(particle)
    
    def clear(self):
        self.particles.clear()
        self.grid.clear()
    
    def calculate_force_falloff(self, distance, force_type="normal"):
        """Calculate force falloff based on distance and force type"""
        if force_type == "attraction":
            radius = self.attraction_radius
        elif force_type == "repulsion":
            radius = self.repulsion_radius
        else:
            radius = self.interaction_radius
        
        if distance > radius:
            return 0.0
        
        # Smooth falloff function (1 at center, 0 at radius)
        falloff = 1.0 - (distance / radius) ** self.force_falloff
        return max(0.0, falloff)
    
    def update(self, dt):
        start_time = pygame.time.get_ticks()
        dt_scaled = dt * self.speed_multiplier
        self.interaction_checks = 0
        
        if len(self.particles) > 0:
            self.update_grid()
        
        for i, p1 in enumerate(self.particles):
            fx, fy = 0, 0
            
            # Get nearby particles using spatial grid
            nearby = self.grid.get_nearby(p1, self.interaction_radius)
            
            for p2 in nearby:
                if p1 is p2:
                    continue
                
                dx = p2.x - p1.x
                dy = p2.y - p1.y
                dist_sq = dx*dx + dy*dy
                
                if 0 < dist_sq < self.interaction_radius**2:
                    self.interaction_checks += 1
                    distance = math.sqrt(dist_sq)
                    
                    # SHORT-RANGE COLLISION FORCE (prevents perfect overlap)
                    if self.enable_collisions and distance < self.collision_radius:
                        collision_force = self.collision_strength * (1.0 - distance / self.collision_radius)
                        F_collision = collision_force / (distance + 0.1)
                        fx -= F_collision * dx  # Repel away
                        fy -= F_collision * dy
                    
                    # Normal force calculation with falloff
                    force = self.force_matrix[p1.type][p2.type]
                    force_type = "attraction" if force > 0 else "repulsion"
                    factor = self.calculate_force_falloff(distance, force_type)
                    force *= factor
                    
                    if abs(force) > 0.001:
                        F = force / (distance + 0.1)
                        fx += F * dx
                        fy += F * dy
            
            # Apply forces
            p1.vx = (p1.vx + fx) * (1 - self.friction * 0.1)
            p1.vy = (p1.vy + fy + self.gravity) * (1 - self.friction * 0.1)
            
            # Limit velocity
            speed = math.sqrt(p1.vx*p1.vx + p1.vy*p1.vy)
            max_speed = 15.0
            if speed > max_speed:
                p1.vx = (p1.vx / speed) * max_speed
                p1.vy = (p1.vy / speed) * max_speed
            
            # Update position
            p1.x += p1.vx * dt_scaled
            p1.y += p1.vy * dt_scaled
            
            # Boundary bounce with GUI awareness
            padding = 20
            left_boundary = 320 if hasattr(self, 'gui_visible') and self.gui_visible else padding
            
            if p1.x < left_boundary:
                p1.x = left_boundary
                p1.vx = abs(p1.vx) * 0.8
            elif p1.x > self.width - padding:
                p1.x = self.width - padding
                p1.vx = -abs(p1.vx) * 0.8
            
            if p1.y < padding:
                p1.y = padding
                p1.vy = abs(p1.vy) * 0.8
            elif p1.y > self.height - padding:
                p1.y = self.height - padding
                p1.vy = -abs(p1.vy) * 0.8
            
            # Update trail
            if random.random() < 0.3:
                p1.trail.append((p1.x, p1.y))
                if len(p1.trail) > p1.max_trail:
                    p1.trail.pop(0)
        
        self.update_time = pygame.time.get_ticks() - start_time

# ==================== ENHANCED UNIQUE PRESETS ====================
PRESETS = {
    # Completely unique presets - NO SIMILARITIES
    "Default": [
        [-0.32, -0.17, 0.34, 0.15],   # Red: attracts blue
        [-0.34, -0.10, 0.00, -0.25],  # Green: neutral
        [-0.20, 0.00, 0.15, 0.30],    # Blue: self-attracts, attracts purple
        [0.25, -0.30, 0.10, -0.15]    # Purple: attracts red, repels green, attracts blue
    ],
    "Chaos": [
        [0.8, -0.5, 0.2, -0.7],      # Total randomness
        [-0.4, 0.6, -0.9, 0.3],
        [0.1, -0.8, 0.5, -0.2],
        [-0.6, 0.3, -0.4, 0.9]
    ],
    "Swarm": [
        [0.9, 0.7, 0.6, 0.5],        # All attract each other
        [0.7, 0.9, 0.8, 0.6],
        [0.6, 0.8, 0.9, 0.7],
        [0.5, 0.6, 0.7, 0.9]
    ],
    "Repel All": [
        [-0.8, -0.7, -0.6, -0.5],    # All repel each other
        [-0.7, -0.8, -0.9, -0.6],
        [-0.6, -0.9, -0.8, -0.7],
        [-0.5, -0.6, -0.7, -0.8]
    ],
    "Orbits": [
        [-0.1, 1.0, -0.5, 0.3],      # Circular orbital patterns
        [-1.0, -0.1, 0.5, -0.3],
        [0.5, -0.5, -0.1, 1.0],
        [-0.3, 0.3, -1.0, -0.1]
    ],
    "Flowing": [
        [0.3, -0.2, 0.4, -0.1],      # Smooth flowing streams
        [0.2, 0.3, -0.3, 0.4],
        [-0.4, 0.1, 0.3, -0.2],
        [0.1, -0.4, 0.2, 0.3]
    ],
    "Hunt & Flee": [
        [0.0, -0.8, 0.9, -0.5],      # Type 0 hunts 2, 2 flees 0
        [-0.8, 0.0, -0.9, 0.3],
        [-0.9, 0.9, 0.0, -0.7],
        [-0.5, 0.3, -0.7, 0.0]
    ],
    "Symbiosis": [
        [-0.2, 0.8, 0.7, -0.1],      # Mutual benefit ecosystem
        [0.8, -0.2, 0.6, 0.4],
        [0.7, 0.6, -0.2, 0.3],
        [-0.1, 0.4, 0.3, -0.2]
    ],
    "Parasite": [
        [0.5, -0.9, -0.8, -0.7],     # One type leeches off all
        [-0.9, 0.0, 0.4, 0.3],
        [-0.8, 0.4, 0.0, 0.2],
        [-0.7, 0.3, 0.2, 0.0]
    ],
    "Immune System": [
        [0.9, -1.0, -0.8, -0.6],     # Immune cells attack pathogens
        [-1.0, 0.8, 0.7, 0.6],       # Pathogens cluster
        [-0.8, 0.7, 0.9, 0.5],
        [-0.6, 0.6, 0.5, 0.8]
    ],
    "Social Groups": [
        [1.0, -0.9, -0.8, -0.7],     # Strong in-group, out-group repulsion
        [-0.9, 1.0, -0.7, -0.6],
        [-0.8, -0.7, 1.0, -0.5],
        [-0.7, -0.6, -0.5, 1.0]
    ],
    "Magnetic": [
        [1.0, -1.0, 0.8, -0.8],      # Like poles repel, opposites attract
        [-1.0, 1.0, -0.8, 0.8],
        [0.8, -0.8, 1.0, -1.0],
        [-0.8, 0.8, -1.0, 1.0]
    ],
    "Vortex": [
        [0.0, -0.7, 0.5, -0.3],      # Creates swirling vortex patterns
        [0.7, 0.0, -0.6, 0.4],
        [-0.5, 0.6, 0.0, -0.7],
        [0.3, -0.4, 0.7, 0.0]
    ],
    "Pulsing": [
        [0.6, -0.2, 0.4, -0.3],      # Expansion and contraction cycles
        [-0.2, 0.6, -0.3, 0.4],
        [0.4, -0.3, 0.6, -0.2],
        [-0.3, 0.4, -0.2, 0.6]
    ],
    "Neurons": [
        [0.0, 0.8, -0.9, 0.2],       # Neural network-like connections
        [0.8, 0.0, 0.3, -0.7],
        [-0.9, 0.3, 0.0, 0.5],
        [0.2, -0.7, 0.5, 0.0]
    ],
    "Crystal": [
        [1.0, -0.3, -0.3, -0.3],     # Forms crystal lattice patterns
        [-0.3, 1.0, -0.3, -0.3],
        [-0.3, -0.3, 1.0, -0.3],
        [-0.3, -0.3, -0.3, 1.0]
    ],
    "Eater": [
        [0.0, -0.8, 0.7, 0.0],       # Red: repels Green, attracts Blue, neutral Purple
        [-0.8, 0.0, 0.0, 0.0],       # Green: repels Red, neutral others
        [0.8, 0.0, 0.0, -0.9],       # Blue: attracts Red, repels Purple
        [0.0, 0.0, 0.9, 0.8]         # Purple: attracts Blue, attracts itself
    ]
}

# ==================== GUI COMPONENTS ====================
class Slider:
    def __init__(self, x, y, label, min_val, max_val, default_val, width=180):
        self.rect = pygame.Rect(x, y, width, 20)
        self.label = label
        self.min = min_val
        self.max = max_val
        self.value = default_val
        self.default_value = default_val  # Store default for reset
        self.dragging = False
    
    def draw(self, surface, font, y_offset=0):
        draw_rect = self.rect.copy()
        draw_rect.y += y_offset
        
        # Skip drawing if off-screen
        if draw_rect.bottom < 0 or draw_rect.top > surface.get_height():
            return
        
        pygame.draw.rect(surface, (50, 50, 60), draw_rect, border_radius=3)
        
        ratio = (self.value - self.min) / (self.max - self.min)
        fill_width = int(self.rect.width * ratio)
        fill_rect = pygame.Rect(draw_rect.x, draw_rect.y, fill_width, draw_rect.height)
        pygame.draw.rect(surface, (100, 150, 200), fill_rect, border_radius=3)
        
        pygame.draw.rect(surface, (80, 80, 90), draw_rect, 2, border_radius=3)
        
        text = font.render(f"{self.label}: {self.value:.2f}", True, (220, 220, 240))
        surface.blit(text, (draw_rect.x, draw_rect.y - 25))
    
    def handle_event(self, event, mouse_pos, y_offset=0):
        adjusted_mouse = (mouse_pos[0], mouse_pos[1] - y_offset)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                if self.rect.collidepoint(adjusted_mouse):
                    self.dragging = True
                    self.update_value(adjusted_mouse[0])
            elif event.button == 3:  # Right click - reset to default
                if self.rect.collidepoint(adjusted_mouse):
                    self.value = self.default_value
                    return True
        
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.update_value(adjusted_mouse[0])
        
        return False
    
    def update_value(self, mouse_x):
        rel_x = mouse_x - self.rect.x
        ratio = max(0, min(1, rel_x / self.rect.width))
        self.value = self.min + ratio * (self.max - self.min)

class Button:
    def __init__(self, x, y, width, height, text, color=(80, 120, 200), tooltip=""):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.tooltip = tooltip
        self.hovered = False
        self.show_tooltip = False
        self.hover_timer = 0
    
    def draw(self, surface, font, y_offset=0):
        draw_rect = self.rect.copy()
        draw_rect.y += y_offset
        
        # Skip drawing if completely off-screen
        if draw_rect.bottom < 0 or draw_rect.top > surface.get_height():
            return
        
        color = self.color
        if self.hovered:
            color = tuple(min(255, c + 30) for c in color)
        
        pygame.draw.rect(surface, color, draw_rect, border_radius=5)
        pygame.draw.rect(surface, (150, 150, 200), draw_rect, 2, border_radius=5)
        
        # Draw text with word wrapping if needed
        words = self.text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if font.size(test_line)[0] <= self.rect.width - 10:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        
        # Draw each line
        line_height = font.get_height()
        total_height = len(lines) * line_height
        start_y = draw_rect.centery - total_height // 2
        
        for i, line in enumerate(lines):
            line_surf = font.render(line, True, (240, 240, 255))
            line_rect = line_surf.get_rect(center=(draw_rect.centerx, start_y + i * line_height))
            surface.blit(line_surf, line_rect)
        
        # Draw tooltip if hovering long enough
        if self.show_tooltip and self.tooltip:
            self.draw_tooltip(surface, draw_rect)
    
    def draw_tooltip(self, surface, button_rect):
        tooltip_font = pygame.font.Font(None, 20)
        tooltip_lines = self.tooltip.split('\n')
        
        # Calculate tooltip size
        max_width = 0
        for line in tooltip_lines:
            width = tooltip_font.size(line)[0]
            max_width = max(max_width, width)
        
        tooltip_height = len(tooltip_lines) * 22
        tooltip_width = max_width + 20
        
        # Create tooltip surface
        tooltip_surf = pygame.Surface((tooltip_width, tooltip_height + 10), pygame.SRCALPHA)
        tooltip_surf.fill((20, 20, 30, 230))
        pygame.draw.rect(tooltip_surf, (80, 80, 100), (0, 0, tooltip_width, tooltip_height + 10), 2, border_radius=4)
        
        # Draw tooltip text
        for i, line in enumerate(tooltip_lines):
            line_surf = tooltip_font.render(line, True, (200, 200, 240))
            tooltip_surf.blit(line_surf, (10, 5 + i * 22))
        
        # Position tooltip above button
        tooltip_x = button_rect.centerx - tooltip_width // 2
        tooltip_y = button_rect.top - tooltip_height - 10
        
        # Adjust if off-screen
        if tooltip_y < 0:
            tooltip_y = button_rect.bottom + 10
        if tooltip_x < 5:
            tooltip_x = 5
        if tooltip_x + tooltip_width > surface.get_width() - 5:
            tooltip_x = surface.get_width() - tooltip_width - 5
        
        surface.blit(tooltip_surf, (tooltip_x, tooltip_y))
    
    def update(self, dt):
        if self.hovered:
            self.hover_timer += dt
            if self.hover_timer > 0.5:  # Show tooltip after 0.5 seconds
                self.show_tooltip = True
        else:
            self.hover_timer = 0
            self.show_tooltip = False
    
    def check_hover(self, mouse_pos, y_offset=0):
        adjusted_mouse = (mouse_pos[0], mouse_pos[1] - y_offset)
        self.hovered = self.rect.collidepoint(adjusted_mouse)
        return self.hovered
    
    def is_clicked(self, event, mouse_pos, y_offset=0):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False
        
        adjusted_mouse = (mouse_pos[0], mouse_pos[1] - y_offset)
        return self.rect.collidepoint(adjusted_mouse)

# ==================== MAIN ====================
def main():
    # INIT PYGAME
    pygame.init()
    WIDTH, HEIGHT = 1000, 700
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Particle Life - Enhanced Physics")
    clock = pygame.time.Clock()
    
    # CREATE SIMULATION
    sim = ParticleSim(WIDTH, HEIGHT)
    sim.add_particles(300)
    
    # CREATE GUI
    font = pygame.font.Font(None, 24)
    small_font = pygame.font.Font(None, 20)
    gui_visible = True
    sim.gui_visible = gui_visible  # Let simulation know about GUI visibility
    
    # GUI Layout Parameters
    GUI_WIDTH = 320
    gui_scroll_y = 0
    gui_content_height = 2300  # Increased for new controls
    gui_viewport_height = HEIGHT
    
    # Calculate positions with PROPER SPACING
    current_y = 20
    
    # Physics sliders
    sliders = []
    slider_labels = ["Interaction Radius", "Friction", "Gravity", "Speed", "Particle Count"]
    slider_ranges = [(10, 200), (0.1, 0.9), (-0.5, 0.5), (0.1, 5.0), (10, 2000)]
    slider_defaults = [80, 0.5, 0.0, 1.0, 300]
    
    for i in range(5):
        sliders.append(Slider(20, current_y, slider_labels[i], slider_ranges[i][0], 
                             slider_ranges[i][1], slider_defaults[i], width=250))
        current_y += 50
    
    # Force radius sliders
    current_y += 10
    force_radius_sliders = []
    force_radius_labels = ["Attraction Radius", "Repulsion Radius", "Force Falloff"]
    force_radius_ranges = [(10, 150), (5, 100), (0.5, 3.0)]
    force_radius_defaults = [60, 40, 1.0]
    
    for i in range(3):
        force_radius_sliders.append(Slider(20, current_y, force_radius_labels[i], 
                                          force_radius_ranges[i][0], force_radius_ranges[i][1], 
                                          force_radius_defaults[i], width=250))
        current_y += 50
    
    # Particle size and trail sliders
    current_y += 10
    size_sliders = []
    size_labels = ["Particle Size", "Trail Length", "Trail Opacity", "Trail Width", "Size Variation"]
    size_ranges = [(0.5, 5.0), (0, 50), (0, 255), (1, 10), (0.1, 2.0)]
    size_defaults = [1.0, 10, 100, 2, 0.5]
    
    for i in range(5):
        size_sliders.append(Slider(20, current_y, size_labels[i], size_ranges[i][0], 
                                  size_ranges[i][1], size_defaults[i], width=250))
        current_y += 50
    
    # Collision physics sliders
    current_y += 10
    collision_sliders = []
    collision_labels = ["Collision Strength", "Collision Radius"]
    collision_ranges = [(0.0, 10.0), (5, 50)]
    collision_defaults = [5.0, 15]
    
    for i in range(2):
        collision_sliders.append(Slider(20, current_y, collision_labels[i], 
                                       collision_ranges[i][0], collision_ranges[i][1], 
                                       collision_defaults[i], width=250))
        current_y += 50
    
    # Toggle buttons section
    toggle_buttons_y = current_y
    current_y += 60
    
    # Preset section header
    preset_header_y = current_y
    current_y += 40
    
    # Preset Buttons (2 columns, 9 rows for 17 presets including new Eater)
    preset_buttons = []
    preset_names = list(PRESETS.keys())
    button_width = 140
    button_height = 28
    button_spacing_x = 10
    button_spacing_y = 5
    
    # Tooltips for presets
    preset_tooltips = {
        "Default": "Red attracts Blue, Blue self-attracts\nPurple attracts Red and Blue",
        "Chaos": "Totally random forces\nComplete unpredictability",
        "Swarm": "All particles attract each other\nForms tight moving swarms",
        "Repel All": "Everything repels everything\nMaximum spacing",
        "Orbits": "Creates stable orbital patterns\nParticles circle each other",
        "Flowing": "Creates flowing rivers of particles\nSmooth, wave-like motion",
        "Hunt & Flee": "Type 0 hunts Type 2, Type 2 flees\nCreates predator-prey chases",
        "Symbiosis": "Different types help each other\nMutually beneficial relationships",
        "Parasite": "One type leeches off all others\nHost-parasite dynamics",
        "Immune System": "Immune cells attack pathogens\nSimulates immune response",
        "Social Groups": "Strong in-group attraction\nOut-group repulsion - segregation",
        "Magnetic": "Like poles repel, opposites attract\nMagnetic field simulation",
        "Vortex": "Creates swirling vortex patterns\nTornado-like motion",
        "Pulsing": "Expansion and contraction cycles\nBreathing patterns",
        "Neurons": "Neural network-like connections\nInformation flow simulation",
        "Crystal": "Forms crystal lattice patterns\nGeometric organization",
        "Eater": "Purple cells bunch up, chase blue\nBlue flees purple, chases red\nRed flees blue, repels green"
    }
    
    for i, name in enumerate(preset_names):
        col = i % 2
        row = i // 2
        x = 20 + col * (button_width + button_spacing_x)
        y = current_y + row * (button_height + button_spacing_y)
        tooltip = preset_tooltips.get(name, "")
        preset_buttons.append(Button(x, y, button_width, button_height, name, tooltip=tooltip))
    
    current_y += 9 * (button_height + button_spacing_y) + 30  # 9 rows for 17 presets
    
    # Action Buttons
    action_buttons = []
    action_labels = ["Clear All", "Randomize", "Reset"]
    action_tooltips = [
        "Remove all particles from simulation",
        "Randomize all force values\nCreates new random behaviors",
        "Reset to default force matrix\nand clear particles"
    ]
    action_width = 95
    
    for i, label in enumerate(action_labels):
        x = 20 + i * (action_width + 10)
        y = current_y
        action_buttons.append(Button(x, y, action_width, 32, label, tooltip=action_tooltips[i]))
    
    current_y += 60
    
    # Toggle buttons
    toggle_buttons = []
    toggle_labels = ["Collisions", "Trails", "Grid", "Performance"]
    toggle_colors = [(180, 80, 100), (100, 100, 200), (180, 180, 80), (200, 100, 200)]
    toggle_width = 150
    
    for i, label in enumerate(toggle_labels):
        x = 20 + (i % 2) * (toggle_width + 10)
        y = toggle_buttons_y + (i // 2) * 40
        toggle_buttons.append(Button(x, y, toggle_width, 32, label, color=toggle_colors[i]))
    
    # Type descriptions
    type_descriptions = [
        "Type 0 (Red) - Hunters/Predators",
        "Type 1 (Green) - Neutral/Swarmers", 
        "Type 2 (Blue) - Chasers/Flee-ers",
        "Type 3 (Purple) - Orbital/Support"
    ]
    type_colors = [(220, 50, 50), (50, 220, 50), (50, 100, 220), (180, 50, 220)]
    
    type_desc_y = current_y
    current_y += 110
    
    # Force matrix section
    force_header_y = current_y
    current_y += 40
    
    # Force matrix with labels
    force_buttons = []
    matrix_start_x = 20
    matrix_start_y = current_y
    cell_size = 55
    label_width = 85
    
    for i in range(4):
        for j in range(4):
            x = matrix_start_x + label_width + j * cell_size
            y = matrix_start_y + i * cell_size
            btn = pygame.Rect(x, y, cell_size, cell_size)
            force_buttons.append((btn, i, j))
    
    current_y += 4 * cell_size + 40
    
    # Stats section
    stats_header_y = current_y
    current_y += 40
    
    # Update content height based on ACTUAL content
    gui_content_height = current_y + 800
    
    # GUI state
    show_trails = True
    show_grid = True
    show_perf = True
    running = True
    
    while running:
        dt = clock.tick(60) / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        
        # Update GUI visibility in simulation
        sim.gui_visible = gui_visible
        
        # HANDLE EVENTS
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_y:
                    gui_visible = not gui_visible
                elif event.key == pygame.K_SPACE:
                    sim.clear()
                    sim.add_particles(int(sliders[4].value))
                elif event.key == pygame.K_t:
                    show_trails = not show_trails
                elif event.key == pygame.K_g:
                    show_grid = not show_grid
                elif event.key == pygame.K_p:
                    show_perf = not show_perf
                elif event.key == pygame.K_1:
                    sim.add_particles(100)
                elif event.key == pygame.K_2:
                    sim.clear()
                elif event.key == pygame.K_c:
                    sim.enable_collisions = not sim.enable_collisions
            
            elif event.type == pygame.MOUSEWHEEL:
                # Scroll wheel for GUI - EVEN LARGER STEPS
                if gui_visible:
                    gui_scroll_y -= event.y * 80  # Much larger steps
                    max_scroll = max(0, gui_content_height - gui_viewport_height)
                    gui_scroll_y = max(-max_scroll, min(0, gui_scroll_y))
            
            elif event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                sim.width, sim.height = WIDTH, HEIGHT
                sim.grid = SpatialGrid(WIDTH, HEIGHT, cell_size=100)
                gui_viewport_height = HEIGHT
            
            # Handle GUI events with scroll offset
            if gui_visible:
                # Physics sliders - handle right click reset
                for slider in sliders:
                    if slider.handle_event(event, mouse_pos, gui_scroll_y):
                        # If right-click reset a slider, update simulation
                        sim.interaction_radius = sliders[0].value
                        sim.friction = sliders[1].value
                        sim.gravity = sliders[2].value
                        sim.speed_multiplier = sliders[3].value
                
                # Force radius sliders
                for slider in force_radius_sliders:
                    if slider.handle_event(event, mouse_pos, gui_scroll_y):
                        sim.attraction_radius = force_radius_sliders[0].value
                        sim.repulsion_radius = force_radius_sliders[1].value
                        sim.force_falloff = force_radius_sliders[2].value
                
                # Size sliders - handle right click reset
                for slider in size_sliders:
                    slider.handle_event(event, mouse_pos, gui_scroll_y)
                
                # Collision sliders
                for slider in collision_sliders:
                    if slider.handle_event(event, mouse_pos, gui_scroll_y):
                        sim.collision_strength = collision_sliders[0].value
                        sim.collision_radius = collision_sliders[1].value
                
                # Toggle buttons
                for i, button in enumerate(toggle_buttons):
                    if button.is_clicked(event, mouse_pos, gui_scroll_y):
                        if i == 0:  # Collisions
                            sim.enable_collisions = not sim.enable_collisions
                        elif i == 1:  # Trails
                            show_trails = not show_trails
                        elif i == 2:  # Grid
                            show_grid = not show_grid
                        elif i == 3:  # Performance
                            show_perf = not show_perf
                
                # Preset buttons
                for button in preset_buttons:
                    if button.is_clicked(event, mouse_pos, gui_scroll_y):
                        preset_name = button.text
                        if preset_name in PRESETS:
                            sim.force_matrix = [row[:] for row in PRESETS[preset_name]]
                            sim.current_preset = preset_name
                
                # Action buttons
                for i, button in enumerate(action_buttons):
                    if button.is_clicked(event, mouse_pos, gui_scroll_y):
                        if i == 0:  # Clear All
                            sim.clear()
                        elif i == 1:  # Randomize
                            for i in range(4):
                                for j in range(4):
                                    sim.force_matrix[i][j] = random.uniform(-1, 1)
                            sim.current_preset = "Random"
                        elif i == 2:  # Reset
                            sim.force_matrix = [row[:] for row in PRESETS["Default"]]
                            sim.current_preset = "Default"
                            sim.clear()
                            sim.add_particles(300)
                
                # Force matrix button clicks - handle left and right click
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for btn, i, j in force_buttons:
                        adjusted_btn = btn.copy()
                        adjusted_btn.y += gui_scroll_y
                        if adjusted_btn.collidepoint(mouse_pos):
                            if event.button == 1:  # Left click - cycle values
                                # Cycle through force values
                                current = sim.force_matrix[i][j]
                                if current < -0.8:
                                    sim.force_matrix[i][j] = -0.4
                                elif current < -0.4:
                                    sim.force_matrix[i][j] = 0.0
                                elif current < 0.4:
                                    sim.force_matrix[i][j] = 0.8
                                else:
                                    sim.force_matrix[i][j] = -1.0
                            elif event.button == 3:  # Right click - reset to neutral (0.0)
                                sim.force_matrix[i][j] = 0.0
        
        # Update button hover states
        if gui_visible:
            for button in preset_buttons + action_buttons + toggle_buttons:
                button.check_hover(mouse_pos, gui_scroll_y)
                button.update(dt)
        
        # SPEED CONTROL WITH SHIFT/CTRL
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            sim.speed_multiplier = min(5.0, sim.speed_multiplier + 0.1)
            sliders[3].value = sim.speed_multiplier
        if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
            sim.speed_multiplier = max(0.1, sim.speed_multiplier - 0.1)
            sliders[3].value = sim.speed_multiplier
        
        # UPDATE SIMULATION FROM SLIDERS
        if gui_visible:
            sim.interaction_radius = sliders[0].value
            sim.friction = sliders[1].value
            sim.gravity = sliders[2].value
            sim.speed_multiplier = sliders[3].value
            sim.particle_scale = size_sliders[0].value
            
            # Update particle count if changed
            target_count = int(sliders[4].value)
            current_count = len(sim.particles)
            if target_count > current_count:
                sim.add_particles(target_count - current_count)
            elif target_count < current_count:
                sim.particles = sim.particles[:target_count]
            
            # Update particle trail lengths
            for particle in sim.particles:
                particle.max_trail = int(size_sliders[1].value)
        
        # UPDATE PHYSICS
        sim.update(dt)
        
        # DRAW EVERYTHING
        screen.fill((15, 15, 25))
        
        # Draw grid
        if show_grid:
            for x in range(0, WIDTH, 50):
                pygame.draw.line(screen, (30, 30, 40, 50), (x, 0), (x, HEIGHT), 1)
            for y in range(0, HEIGHT, 50):
                pygame.draw.line(screen, (30, 30, 40, 50), (0, y), (WIDTH, y), 1)
        
        # Draw particles with size scaling
        particle_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        
        for particle in sim.particles:
            # Draw trail with opacity and width controls
            if show_trails and len(particle.trail) > 1:
                trail_opacity = size_sliders[2].value
                trail_width = int(size_sliders[3].value)
                for i in range(1, len(particle.trail)):
                    alpha = int(trail_opacity * (i / len(particle.trail)))
                    start = (int(particle.trail[i-1][0]), int(particle.trail[i-1][1]))
                    end = (int(particle.trail[i][0]), int(particle.trail[i][1]))
                    pygame.draw.line(particle_surface, (*particle.color, alpha), start, end, trail_width)
            
            # Draw particle with size scaling
            base_size = particle.size * sim.particle_scale
            # Apply size variation
            size_variation = size_sliders[4].value
            size = max(1, int(base_size * random.uniform(1.0 - size_variation*0.5, 1.0 + size_variation*0.5)))
            
            # Draw particle
            pygame.draw.circle(particle_surface, particle.color, 
                             (int(particle.x), int(particle.y)), 
                             size)
            pygame.draw.circle(particle_surface, (255, 255, 255, 100), 
                             (int(particle.x), int(particle.y)), 
                             size, 1)
        
        screen.blit(particle_surface, (0, 0))
        
        # DRAW GUI
        if gui_visible:
            # Draw semi-transparent background
            gui_bg = pygame.Surface((GUI_WIDTH, HEIGHT), pygame.SRCALPHA)
            gui_bg.fill((25, 25, 35, 240))
            screen.blit(gui_bg, (0, 0))
            
            # Draw scroll bar - LARGE AND VISIBLE
            max_scroll = max(0, gui_content_height - gui_viewport_height)
            if max_scroll > 0:
                # Calculate scroll bar size and position
                scroll_ratio = gui_viewport_height / gui_content_height
                scroll_bar_height = max(100, int(gui_viewport_height * scroll_ratio))
                scroll_pos_ratio = -gui_scroll_y / max_scroll
                scroll_pos = scroll_pos_ratio * (gui_viewport_height - scroll_bar_height)
                
                # Draw scroll bar track
                pygame.draw.rect(screen, (40, 40, 60, 200), 
                               (GUI_WIDTH - 25, 10, 20, HEIGHT - 20), border_radius=10)
                
                # Draw scroll bar handle - VERY LARGE
                pygame.draw.rect(screen, (120, 170, 220, 240), 
                               (GUI_WIDTH - 25, 10 + scroll_pos, 20, scroll_bar_height), 
                               border_radius=10)
                pygame.draw.rect(screen, (180, 220, 255, 255), 
                               (GUI_WIDTH - 25, 10 + scroll_pos, 20, scroll_bar_height), 
                               2, border_radius=10)
            
            # Draw physics sliders
            for slider in sliders:
                slider.draw(screen, font, gui_scroll_y)
            
            # Draw force radius sliders
            for slider in force_radius_sliders:
                slider.draw(screen, font, gui_scroll_y)
            
            # Draw size sliders
            for slider in size_sliders:
                slider.draw(screen, font, gui_scroll_y)
            
            # Draw collision sliders
            for slider in collision_sliders:
                slider.draw(screen, font, gui_scroll_y)
            
            # Draw toggle buttons with state indicators
            for i, button in enumerate(toggle_buttons):
                # Update button color based on state
                state_on = False
                if i == 0:
                    state_on = sim.enable_collisions
                elif i == 1:
                    state_on = show_trails
                elif i == 2:
                    state_on = show_grid
                elif i == 3:
                    state_on = show_perf
                
                if state_on:
                    button.color = toggle_colors[i]
                else:
                    button.color = (80, 80, 100)
                
                button.draw(screen, small_font, gui_scroll_y)
            
            # Draw preset section header
            preset_title = font.render("Force Presets (17 Unique):", True, (220, 220, 240))
            screen.blit(preset_title, (20, preset_header_y + gui_scroll_y))
            
            # Draw preset buttons
            for button in preset_buttons:
                button.draw(screen, small_font, gui_scroll_y)
            
            # Draw action buttons
            for button in action_buttons:
                button.draw(screen, font, gui_scroll_y)
            
            # Draw type descriptions
            for i in range(4):
                desc_text = small_font.render(type_descriptions[i], True, type_colors[i])
                screen.blit(desc_text, (20, type_desc_y + i * 25 + gui_scroll_y))
            
            # Draw force matrix header
            force_title = font.render("Force Matrix (Attractor → Target):", True, (220, 220, 240))
            screen.blit(force_title, (20, force_header_y + gui_scroll_y))
            
            # Draw column headers
            column_labels = ["Red", "Green", "Blue", "Purple"]
            for j in range(4):
                x = matrix_start_x + label_width + j * cell_size
                y = matrix_start_y - 25 + gui_scroll_y
                if y > -25 and y < HEIGHT:
                    header_text = small_font.render(column_labels[j], True, type_colors[j])
                    text_rect = header_text.get_rect(center=(x + cell_size//2, y))
                    screen.blit(header_text, text_rect)
            
            # Draw row headers
            for i in range(4):
                x = matrix_start_x
                y = matrix_start_y + i * cell_size + gui_scroll_y
                if y > 0 and y < HEIGHT:
                    header_text = small_font.render(column_labels[i], True, type_colors[i])
                    screen.blit(header_text, (x, y + cell_size//2 - 10))
            
            # Draw force matrix cells
            for btn, i, j in force_buttons:
                draw_btn = btn.copy()
                draw_btn.y += gui_scroll_y
                
                # Skip drawing if off-screen
                if draw_btn.bottom < 0 or draw_btn.top > HEIGHT:
                    continue
                
                force = sim.force_matrix[i][j]
                
                # Color based on force value
                if force > 0.6:
                    color = (50, 220, 50)  # Strong attraction
                elif force > 0.2:
                    color = (100, 180, 100)  # Medium attraction
                elif force > -0.2:
                    color = (120, 120, 120)  # Neutral
                elif force > -0.6:
                    color = (180, 100, 100)  # Medium repulsion
                else:
                    color = (220, 50, 50)  # Strong repulsion
                
                pygame.draw.rect(screen, color, draw_btn, border_radius=4)
                pygame.draw.rect(screen, (150, 150, 150), draw_btn, 2, border_radius=4)
                
                # Draw force value
                force_text = small_font.render(f"{force:+.1f}", True, (255, 255, 255))
                text_rect = force_text.get_rect(center=draw_btn.center)
                screen.blit(force_text, text_rect)
            
            # Draw stats section (far down - requires scrolling)
            if stats_header_y + gui_scroll_y < HEIGHT:
                stats_title = font.render("Stats & Controls:", True, (220, 220, 240))
                screen.blit(stats_title, (20, stats_header_y + gui_scroll_y))
                
                # Draw stats and help
                stats_y = stats_header_y + 30 + gui_scroll_y
                stats_lines = [
                    f"FPS: {clock.get_fps():.0f}",
                    f"Particles: {len(sim.particles)}",
                    f"Speed: {sim.speed_multiplier:.1f}x",
                    f"Update: {sim.update_time}ms",
                    f"Interactions: {sim.interaction_checks:,}",
                    f"Preset: {sim.current_preset}",
                    f"Collisions: {'ON' if sim.enable_collisions else 'OFF'}",
                    "",
                    "=== ENHANCED PHYSICS ===",
                    "• Collision Physics: Particles can't overlap completely",
                    "• Force Radii: Attraction/Repulsion have different ranges",
                    "• Smooth Falloff: Forces diminish with distance",
                    "",
                    "=== EATER PRESET ===",
                    "• Purple: Strong self-attraction (bunch up)",
                    "• Purple chases Blue (attraction)",
                    "• Blue flees from Purple (repulsion)",
                    "• Blue chases Red (attraction)",
                    "• Red flees from Blue (repulsion)",
                    "• Red and Green repel each other",
                    "",
                    "=== CONTROLS ===",
                    "Y: Toggle GUI",
                    "SPACE: Reset simulation",
                    "C: Toggle collisions",
                    "T: Toggle trails",
                    "G: Toggle grid",
                    "P: Toggle performance stats",
                    "1: Add 100 particles",
                    "2: Clear all particles",
                    "SHIFT: Speed up",
                    "CTRL: Slow down",
                    "RIGHT-CLICK: Reset slider/cell to default/neutral",
                    "ESC: Quit program",
                    "",
                    "=== NAVIGATION ===",
                    "Mouse wheel: Scroll settings",
                    "Scroll bar: Drag to navigate"
                ]
                
                for line in stats_lines:
                    if line:  # Skip empty lines
                        # Only draw if visible on screen
                        if stats_y > 0 and stats_y < HEIGHT:
                            color = (180, 180, 220)
                            if line.startswith("==="):
                                color = (200, 200, 255)
                            elif line.startswith("•"):
                                color = (150, 200, 255)
                                
                            line_text = small_font.render(line, True, color)
                            screen.blit(line_text, (20, stats_y))
                    stats_y += 20
        else:
            # Minimal stats when GUI hidden
            minimal_stats = [
                f"Particles: {len(sim.particles)}",
                f"Speed: {sim.speed_multiplier:.1f}x",
                f"FPS: {clock.get_fps():.0f}",
                f"Collisions: {'ON' if sim.enable_collisions else 'OFF'}",
                "Y: Show GUI | ESC: Quit"
            ]
            
            y = 10
            for stat in minimal_stats:
                stat_text = font.render(stat, True, (220, 220, 240))
                screen.blit(stat_text, (WIDTH - stat_text.get_width() - 10, y))
                y += 25
        
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()