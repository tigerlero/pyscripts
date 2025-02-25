import pygame
import numpy as np
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

# Game settings
WINDOW_WIDTH = 1920  # 1080p resolution width
WINDOW_HEIGHT = 1080  # 1080p resolution height
RENDER_DISTANCE = 8  # Increased render distance
MOVEMENT_SPEED = 0.1
ROTATION_SPEED = 1
GRAVITY = 0.01
JUMP_FORCE = 0.2

class Block:
    def __init__(self, position, block_type=1):
        self.position = position
        self.block_type = block_type
        self.vertices = [
            [position[0], position[1], position[2]],
            [position[0]+1, position[1], position[2]],
            [position[0]+1, position[1]+1, position[2]],
            [position[0], position[1]+1, position[2]],
            [position[0], position[1], position[2]+1],
            [position[0]+1, position[1], position[2]+1],
            [position[0]+1, position[1]+1, position[2]+1],
            [position[0], position[1]+1, position[2]+1]
        ]
        self.texture_map = {
            1: (0.5, 0.5, 0.1),  # Dirt/grass
            2: (0.7, 0.7, 0.7),  # Stone
            3: (0.6, 0.3, 0.0),  # Wood
            4: (0.0, 0.6, 0.0),  # Leaves
        }
    
    def render(self):
        # Cache color lookup
        color = self.texture_map.get(self.block_type, (1, 1, 1))

        surfaces = [
            [0, 1, 2, 3],  # Bottom face
            [4, 5, 6, 7],  # Top face
            [0, 1, 5, 4],  # Front face
            [3, 2, 6, 7],  # Back face
            [0, 3, 7, 4],  # Left face
            [1, 2, 6, 5]   # Right face
        ]

        # Single glBegin/End call for faces
        glBegin(GL_QUADS)
        glColor3fv(color)
        for surface in surfaces:
            for vertex in surface:
                glVertex3fv(self.vertices[vertex])
        glEnd()

        # Single glBegin/End call for edges
        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7)
        ]

        glBegin(GL_LINES)
        glColor3fv((0, 0, 0))
        for edge in edges:
            for vertex in edge:
                glVertex3fv(self.vertices[vertex])
        glEnd()

class Player:
    def __init__(self, position=(0, 2, 0)):
        self.position = list(position)
        self.rotation = [0, 0]
        self.velocity = [0, 0, 0]
        self.on_ground = False
        self.height = 1.8
        self.camera_offset = 1.7
        self.selected_block = 1
    
    def update(self, world):
        # Apply velocity
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]
        self.position[2] += self.velocity[2]
        
        # Apply gravity
        if not self.on_ground:
            self.velocity[1] -= GRAVITY
        
        # Check collision with world
        player_bounds = [
            (self.position[0] - 0.3, self.position[1], self.position[2] - 0.3),
            (self.position[0] + 0.3, self.position[1], self.position[2] + 0.3),
            (self.position[0] - 0.3, self.position[1] + self.height, self.position[2] - 0.3),
            (self.position[0] + 0.3, self.position[1] + self.height, self.position[2] + 0.3)
        ]
        
        self.on_ground = False
        for block in world.blocks:
            block_pos = block.position
            if (block_pos[0] <= self.position[0] + 0.3 and block_pos[0] + 1 >= self.position[0] - 0.3 and
                block_pos[2] <= self.position[2] + 0.3 and block_pos[2] + 1 >= self.position[2] - 0.3):
                
                # Ground collision
                if (self.position[1] >= block_pos[1] + 1 and 
                    self.position[1] <= block_pos[1] + 1.1):
                    self.position[1] = block_pos[1] + 1
                    self.velocity[1] = 0
                    self.on_ground = True
                
                # Ceiling collision
                if (self.position[1] + self.height >= block_pos[1] and 
                    self.position[1] + self.height <= block_pos[1] + 0.1):
                    self.position[1] = block_pos[1] - self.height
                    self.velocity[1] = 0
                
                # Side collisions
                if (self.position[1] + 0.1 < block_pos[1] + 1 and 
                    self.position[1] + self.height - 0.1 > block_pos[1]):
                    # X-axis collision
                    if (self.position[0] + 0.3 >= block_pos[0] and 
                        self.position[0] + 0.3 <= block_pos[0] + 0.1):
                        self.position[0] = block_pos[0] - 0.3
                        self.velocity[0] = 0
                    if (self.position[0] - 0.3 <= block_pos[0] + 1 and 
                        self.position[0] - 0.3 >= block_pos[0] + 0.9):
                        self.position[0] = block_pos[0] + 1.3
                        self.velocity[0] = 0
                    
                    # Z-axis collision
                    if (self.position[2] + 0.3 >= block_pos[2] and 
                        self.position[2] + 0.3 <= block_pos[2] + 0.1):
                        self.position[2] = block_pos[2] - 0.3
                        self.velocity[2] = 0
                    if (self.position[2] - 0.3 <= block_pos[2] + 1 and 
                        self.position[2] - 0.3 >= block_pos[2] + 0.9):
                        self.position[2] = block_pos[2] + 1.3
                        self.velocity[2] = 0
        
        # Limit player height to prevent falling infinitely
        if self.position[1] < -10:
            self.position = [0, 2, 0]
            self.velocity = [0, 0, 0]
        
        # Dampen velocity
        self.velocity[0] *= 0.8
        self.velocity[2] *= 0.8
        
        if abs(self.velocity[0]) < 0.01:
            self.velocity[0] = 0
        if abs(self.velocity[2]) < 0.01:
            self.velocity[2] = 0


class World:
    def __init__(self):
        self.blocks = []
        self.generate_terrain()
    
    def generate_terrain(self):
        # Generate flat terrain
        for x in range(-RENDER_DISTANCE, RENDER_DISTANCE):
            for z in range(-RENDER_DISTANCE, RENDER_DISTANCE):
                # Base layer (stone)
                for y in range(-2, 0):
                    self.add_block((x, y, z), 2)
                
                # Top layer (grass)
                self.add_block((x, 0, z), 1)
        
        # Add some trees
        self.add_tree((2, 1, 2))
        self.add_tree((-3, 1, -1))
    
    def add_tree(self, position):
        x, y, z = position
        # Trunk
        for i in range(4):
            self.add_block((x, y + i, z), 3)
        
        # Leaves
        for dx in range(-2, 3):
            for dy in range(3, 6):
                for dz in range(-2, 3):
                    if abs(dx) == 2 and abs(dz) == 2:
                        continue  # Skip corners
                    if dy == 5 and (abs(dx) > 1 or abs(dz) > 1):
                        continue  # Make the top smaller
                    self.add_block((x + dx, y + dy, z + dz), 4)
    
    def add_block(self, position, block_type=1):
        self.blocks.append(Block(position, block_type))
    
    def remove_block(self, position):
        for i, block in enumerate(self.blocks):
            if block.position == position:
                self.blocks.pop(i)
                return True
        return False
    
    def render(self):
        for block in self.blocks:
            block.render()
    
    def ray_cast(self, start_pos, direction, max_distance=5):
        """Cast a ray and return the first block hit"""
        for i in range(int(max_distance * 10)):
            distance = i / 10
            point = [
                start_pos[0] + direction[0] * distance,
                start_pos[1] + direction[1] * distance,
                start_pos[2] + direction[2] * distance
            ]
            
            # Check if point is inside any block
            for block in self.blocks:
                x, y, z = block.position
                if (x <= point[0] <= x + 1 and
                    y <= point[1] <= y + 1 and
                    z <= point[2] <= z + 1):
                    return block, distance, point
        
        return None, max_distance, None

class Game:
    def __init__(self):
        pygame.init()
        self.display = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), DOUBLEBUF | OPENGL | FULLSCREEN)
        pygame.display.set_caption("Minecraft in Python")
        
        # Setup OpenGL
        glMatrixMode(GL_PROJECTION)
        gluPerspective(45, (WINDOW_WIDTH / WINDOW_HEIGHT), 0.1, 50.0)
        glMatrixMode(GL_MODELVIEW)
        glEnable(GL_DEPTH_TEST)
        
        # Game objects
        self.world = World()
        self.player = Player()
        
        # Mouse settings
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
        
        # Game state
        self.running = True
        self.last_mouse_pos = pygame.mouse.get_pos()
        self.last_block_pos = None
        self.last_place_time = 0
        self.block_cooldown = 200  # ms
        self.font = pygame.font.SysFont(None, 24)
    
    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                
                # Block selection
                if event.key == pygame.K_1:
                    self.player.selected_block = 1
                elif event.key == pygame.K_2:
                    self.player.selected_block = 2
                elif event.key == pygame.K_3:
                    self.player.selected_block = 3
                elif event.key == pygame.K_4:
                    self.player.selected_block = 4
                
                # Jump
                if event.key == pygame.K_SPACE and self.player.on_ground:
                    self.player.velocity[1] = JUMP_FORCE
            
            # Block placement/removal
            if event.type == pygame.MOUSEBUTTONDOWN:
                current_time = pygame.time.get_ticks()
                if current_time - self.last_place_time > self.block_cooldown:
                    self.last_place_time = current_time
                    
                    # Get direction player is looking
                    direction = [
                        np.cos(np.radians(self.player.rotation[0])) * np.cos(np.radians(self.player.rotation[1])),
                        np.sin(np.radians(self.player.rotation[1])),
                        np.sin(np.radians(self.player.rotation[0])) * np.cos(np.radians(self.player.rotation[1]))
                    ]
                    
                    # Ray cast to find block
                    start_pos = [
                        self.player.position[0],
                        self.player.position[1] + self.player.camera_offset,
                        self.player.position[2]
                    ]
                    block, distance, hit_point = self.world.ray_cast(start_pos, direction)
                    
                    if block:
                        x, y, z = block.position
                        if event.button == 1:  # Left click (remove block)
                            self.world.remove_block((x, y, z))
                        elif event.button == 3:  # Right click (place block)
                            # Calculate adjacent position
                            # Determine which face was hit
                            rel_x = hit_point[0] - x
                            rel_y = hit_point[1] - y
                            rel_z = hit_point[2] - z
                            
                            if rel_x < 0.01:
                                new_pos = (x - 1, y, z)
                            elif rel_x > 0.99:
                                new_pos = (x + 1, y, z)
                            elif rel_y < 0.01:
                                new_pos = (x, y - 1, z)
                            elif rel_y > 0.99:
                                new_pos = (x, y + 1, z)
                            elif rel_z < 0.01:
                                new_pos = (x, y, z - 1)
                            elif rel_z > 0.99:
                                new_pos = (x, y, z + 1)
                            
                            # Check if player is not inside the new block position
                            player_bounds = [
                                (self.player.position[0] - 0.3, self.player.position[1], self.player.position[2] - 0.3),
                                (self.player.position[0] + 0.3, self.player.position[1], self.player.position[2] + 0.3),
                                (self.player.position[0] - 0.3, self.player.position[1] + self.player.height, self.player.position[2] - 0.3),
                                (self.player.position[0] + 0.3, self.player.position[1] + self.player.height, self.player.position[2] + 0.3)
                            ]
                            
                            can_place = True
                            if (new_pos[0] <= self.player.position[0] + 0.3 and new_pos[0] + 1 >= self.player.position[0] - 0.3 and
                                new_pos[1] <= self.player.position[1] + self.player.height and new_pos[1] + 1 >= self.player.position[1] and
                                new_pos[2] <= self.player.position[2] + 0.3 and new_pos[2] + 1 >= self.player.position[2] - 0.3):
                                can_place = False
                            
                            if can_place:
                                self.world.add_block(new_pos, self.player.selected_block)
        
        # Mouse movement for camera
        mouse_pos = pygame.mouse.get_pos()
        mouse_change = [mouse_pos[0] - self.last_mouse_pos[0], mouse_pos[1] - self.last_mouse_pos[1]]
        pygame.mouse.set_pos([WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2])
        self.last_mouse_pos = [WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2]
        
        # Update camera rotation
        self.player.rotation[0] += mouse_change[0] * ROTATION_SPEED * 0.1
        self.player.rotation[1] -= mouse_change[1] * ROTATION_SPEED * 0.1
        
        # Clamp vertical rotation
        if self.player.rotation[1] > 90:
            self.player.rotation[1] = 90
        elif self.player.rotation[1] < -90:
            self.player.rotation[1] = -90
        
        # Keyboard input for movement
        keys = pygame.key.get_pressed()
        forward_vec = [
            np.cos(np.radians(self.player.rotation[0])),
            0,
            np.sin(np.radians(self.player.rotation[0]))
        ]
        right_vec = [
            np.cos(np.radians(self.player.rotation[0] + 90)),
            0,
            np.sin(np.radians(self.player.rotation[0] + 90))
        ]
        
        movement = [0, 0, 0]
        
        # Fixed W/S controls - reversed from original
        if keys[pygame.K_w]:
            movement[0] -= forward_vec[0] * MOVEMENT_SPEED  # Reversed direction
            movement[2] -= forward_vec[2] * MOVEMENT_SPEED  # Reversed direction
        if keys[pygame.K_s]:
            movement[0] += forward_vec[0] * MOVEMENT_SPEED  # Reversed direction
            movement[2] += forward_vec[2] * MOVEMENT_SPEED  # Reversed direction
        if keys[pygame.K_a]:
            movement[0] -= right_vec[0] * MOVEMENT_SPEED
            movement[2] -= right_vec[2] * MOVEMENT_SPEED
        if keys[pygame.K_d]:
            movement[0] += right_vec[0] * MOVEMENT_SPEED
            movement[2] += right_vec[2] * MOVEMENT_SPEED
        
        self.player.velocity[0] += movement[0]
        self.player.velocity[2] += movement[2]
    
    def render_hud(self):
        # Create a surface for text
        info_text = f"Position: ({self.player.position[0]:.1f}, {self.player.position[1]:.1f}, {self.player.position[2]:.1f})"
        block_text = f"Selected Block: {self.player.selected_block}"
        controls_text = "WASD: Move | Mouse: Look | Left-click: Mine | Right-click: Place | 1-4: Block Type | Space: Jump | ESC: Quit"
        
        # Switch back to orthographic projection for HUD
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, WINDOW_WIDTH, WINDOW_HEIGHT, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Draw crosshair
        glColor3f(1, 1, 1)
        glBegin(GL_LINES)
        glVertex2f(WINDOW_WIDTH // 2 - 10, WINDOW_HEIGHT // 2)
        glVertex2f(WINDOW_WIDTH // 2 + 10, WINDOW_HEIGHT // 2)
        glVertex2f(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 10)
        glVertex2f(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 10)
        glEnd()
        
        # Return to 3D projection
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
    
    def update(self):
        self.player.update(self.world)
    
    def render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # Apply camera rotation
        glRotatef(self.player.rotation[1], 1, 0, 0)
        glRotatef(360 - self.player.rotation[0], 0, 1, 0)
        
        # Apply camera position (negative since we're moving the world, not the camera)
        glTranslatef(
            -self.player.position[0],
            -(self.player.position[1] + self.player.camera_offset),
            -self.player.position[2]
        )
        
        # Render world
        self.world.render()
        
        # Render HUD
        self.render_hud()
        
        pygame.display.flip()
    
    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            self.handle_input()
            self.update()
            self.render()
            clock.tick(60)
        
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()