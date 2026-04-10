import math
import random
import colorsys
from enum import Enum
from typing import Tuple, List

class InteractionMode(Enum):
    ATTRACT = 1
    REPEL = 2
    NEUTRAL = 3

class Particle:
    def __init__(self, pos, size, mass, charge, type_id, num_types):
        self.x, self.y = pos
        self.size = size
        self.mass = mass
        self.charge = charge
        self.type_id = type_id
        self.num_types = num_types
        
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        self.rotation = random.uniform(0, 2 * math.pi)
        self.rotation_speed = random.uniform(-0.05, 0.05)
        self.colour = self._get_color(type_id, num_types)
        self.trail = []
        self.max_trail_length = 15

    def _get_color(self, type_id, num_types):
        hue = type_id / num_types
        r, g, b = [int(255 * c) for c in colorsys.hsv_to_rgb(hue, 0.8, 0.9)]
        return (r, g, b)

    def move(self, dt, speed_multiplier=1.0):
        dt_scaled = dt * speed_multiplier
        self.x += self.vx * dt_scaled
        self.y += self.vy * dt_scaled
        self.rotation += self.rotation_speed * dt_scaled
        self.trail.append((self.x, self.y, self.colour))
        if len(self.trail) > self.max_trail_length:
            self.trail.pop(0)

    def apply_force(self, fx, fy, dt, speed_multiplier=1.0):
        dt_scaled = dt * speed_multiplier
        self.vx += fx / self.mass * dt_scaled
        self.vy += fy / self.mass * dt_scaled

    def mouse_move(self, pos, speed_multiplier=1.0):
        dx = pos[0] - self.x
        dy = pos[1] - self.y
        self.vx = dx * 0.1 * speed_multiplier
        self.vy = dy * 0.1 * speed_multiplier

class Environment:
    def __init__(self, dimensions):
        self.width, self.height = dimensions
        self.particles = []
        self.colour = (15, 15, 25)
        
        # Core Particle Life parameters
        self.num_types = 5
        self.force_matrix = self._generate_force_matrix()
        self.interaction_radius = 150.0
        self.interaction_strength = 200.0
        self.collision_radius = 40.0
        self.collision_strength = 500.0
        
        # Global physics
        self.gravity = 0.0
        self.friction = 0.99
        self.elasticity = 0.75
        self.collision_elasticity = 0.9
        self.mass_of_air = 0.2
        
        # Interaction mode
        self.interaction_mode = InteractionMode.ATTRACT
        
        # Performance
        self.use_spatial_hashing = True
        self.cell_size = 150
        self.spatial_grid = {}
        
        # Speed control
        self.speed_multiplier = 1.0

    def _generate_force_matrix(self):
        """Create asymmetric attraction/repulsion matrix"""
        matrix = [[0.0 for _ in range(self.num_types)] for _ in range(self.num_types)]
        for i in range(self.num_types):
            for j in range(self.num_types):
                if i == j:
                    matrix[i][j] = random.uniform(0.8, 1.5)  # strong self-attraction
                else:
                    matrix[i][j] = random.uniform(-1.0, 1.0)  # random attraction/repulsion
        return matrix

    def add_particles(self, n=1, **kwargs):
        for _ in range(n):
            size = kwargs.get('size', random.uniform(4, 8))
            mass = kwargs.get('mass', random.uniform(50, 150))
            charge = kwargs.get('charge', random.uniform(-1, 1))
            x = kwargs.get('x', random.uniform(50, self.width - 50))
            y = kwargs.get('y', random.uniform(50, self.height - 50))
            type_id = random.randint(0, self.num_types - 1)
            
            particle = Particle((x, y), size, mass, charge, type_id, self.num_types)
            self.particles.append(particle)

    def remove_particles(self, count):
        count = min(count, len(self.particles))
        self.particles = self.particles[:-count] if count > 0 else []

    def clear_particles(self):
        self.particles.clear()

    def _update_spatial_grid(self):
        self.spatial_grid.clear()
        for idx, p in enumerate(self.particles):
            cell_x = int(p.x / self.cell_size)
            cell_y = int(p.y / self.cell_size)
            self.spatial_grid.setdefault((cell_x, cell_y), []).append(idx)

    def _get_nearby_particles(self, particle_idx):
        if not self.use_spatial_hashing:
            return range(len(self.particles))
            
        p = self.particles[particle_idx]
        cell_x = int(p.x / self.cell_size)
        cell_y = int(p.y / self.cell_size)
        
        nearby = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                cell_key = (cell_x + dx, cell_y + dy)
                nearby.extend(self.spatial_grid.get(cell_key, []))
        return nearby

    def update(self, dt):
        dt_scaled = dt * self.speed_multiplier
        
        if self.use_spatial_hashing:
            self._update_spatial_grid()
        
        for i, p in enumerate(self.particles):
            fx, fy = 0.0, 0.0
            
            for j in self._get_nearby_particles(i):
                if i == j:
                    continue
                    
                q = self.particles[j]
                dx = q.x - p.x
                dy = q.y - p.y
                dist_sq = dx*dx + dy*dy
                
                if dist_sq < 1e-6:
                    continue
                    
                dist = math.sqrt(dist_sq)
                
                # Calculate interaction force (linear drop-off)
                if dist < self.interaction_radius:
                    strength = self.force_matrix[p.type_id][q.type_id]
                    if self.interaction_mode == InteractionMode.ATTRACT:
                        strength *= self.interaction_strength
                    elif self.interaction_mode == InteractionMode.REPEL:
                        strength = -abs(strength) * self.interaction_strength
                    else:  # NEUTRAL
                        strength = 0.0
                    
                    if abs(strength) > 1e-6:
                        factor = max(0.0, 1.0 - dist / self.interaction_radius)
                        fx += strength * factor * dx / dist
                        fy += strength * factor * dy / dist
                
                # Calculate collision force (always repulsive)
                if dist < self.collision_radius:
                    factor = max(0.0, 1.0 - dist / self.collision_radius)
                    fx -= self.collision_strength * factor * dx / dist
                    fy -= self.collision_strength * factor * dy / dist
            
            # Apply gravity
            fy += self.gravity * p.mass
            
            # Apply forces
            p.apply_force(fx, fy, dt, self.speed_multiplier)
            p.vx *= self.friction
            p.vy *= self.friction
            
            # Boundary collisions
            self._handle_boundary_collision(p)
            p.move(dt, self.speed_multiplier)
        
        self._handle_particle_collisions()

    def _handle_boundary_collision(self, p):
        if p.x < p.size:
            p.x = p.size
            p.vx = abs(p.vx) * self.elasticity
        elif p.x > self.width - p.size:
            p.x = self.width - p.size
            p.vx = -abs(p.vx) * self.elasticity
            
        if p.y < p.size:
            p.y = p.size
            p.vy = abs(p.vy) * self.elasticity
        elif p.y > self.height - p.size:
            p.y = self.height - p.size
            p.vy = -abs(p.vy) * self.elasticity

    def _handle_particle_collisions(self):
        for i in range(len(self.particles)):
            for j in range(i+1, len(self.particles)):
                p1, p2 = self.particles[i], self.particles[j]
                dx = p2.x - p1.x
                dy = p2.y - p1.y
                dist = math.hypot(dx, dy)
                
                if dist < p1.size + p2.size:
                    # Simple elastic collision
                    nx, ny = dx/dist, dy/dist
                    v1n = p1.vx*nx + p1.vy*ny
                    v2n = p2.vx*nx + p2.vy*ny
                    
                    m1, m2 = p1.mass, p2.mass
                    new_v1n = (v1n*(m1-m2) + 2*m2*v2n) / (m1+m2) * self.collision_elasticity
                    new_v2n = (v2n*(m2-m1) + 2*m1*v1n) / (m1+m2) * self.collision_elasticity
                    
                    p1.vx += (new_v1n - v1n) * nx
                    p1.vy += (new_v1n - v1n) * ny
                    p2.vx += (new_v2n - v2n) * nx
                    p2.vy += (new_v2n - v2n) * ny

    def find_particle(self, pos):
        for p in self.particles:
            if math.hypot(p.x - pos[0], p.y - pos[1]) < p.size:
                return p
        return None