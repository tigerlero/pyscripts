import pygame
import random
import time
from enum import Enum

# Game Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
GRID_SIZE = 20
GRID_WIDTH = WINDOW_WIDTH // GRID_SIZE
GRID_HEIGHT = WINDOW_HEIGHT // GRID_SIZE
FRAME_RATE = 10

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)

class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

class CodingChallenge:
    def __init__(self):
        self.challenge_text = ""
        self.solution = ""
        self.active = False
        self.completed = False
        self.start_time = 0
        self.time_limit = 30  # seconds

    def generate(self):
        challenges = [
            {"text": "Write a one-liner to reverse a string:", "solution": "s[::-1]"},
            {"text": "List comprehension to get even numbers:", "solution": "[x for x in range(10) if x % 2 == 0]"},
            {"text": "Lambda function to double a number:", "solution": "lambda x: x * 2"},
            {"text": "Dictionary comprehension for squares:", "solution": "{x: x**2 for x in range(5)}"},
            {"text": "One-liner to flatten a 2D list:", "solution": "[item for sublist in nested_list for item in sublist]"}
        ]
        challenge = random.choice(challenges)
        self.challenge_text = challenge["text"]
        self.solution = challenge["solution"]
        self.active = True
        self.completed = False
        self.start_time = time.time()

    def check_time(self):
        if self.active and not self.completed:
            return time.time() - self.start_time < self.time_limit
        return False

class Snake:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.length = 3
        self.positions = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = Direction.RIGHT
        self.score = 0
        self.coding_power = 0
        self.challenges_completed = 0
        
    def get_head_position(self):
        return self.positions[0]
    
    def update(self):
        head = self.get_head_position()
        dx, dy = self.direction.value
        new_x = (head[0] + dx) % GRID_WIDTH
        new_y = (head[1] + dy) % GRID_HEIGHT
        
        if new_x < 0:
            new_x = GRID_WIDTH - 1
        if new_y < 0:
            new_y = GRID_HEIGHT - 1
            
        if (new_x, new_y) in self.positions:
            return False  # Collision with self
            
        self.positions.insert(0, (new_x, new_y))
        
        if len(self.positions) > self.length:
            self.positions.pop()
            
        return True
    
    def render(self, surface):
        for p in self.positions:
            pygame.draw.rect(surface, GREEN, 
                             (p[0] * GRID_SIZE, p[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE))
            
    def change_direction(self, direction):
        if (direction == Direction.UP and self.direction != Direction.DOWN) or \
           (direction == Direction.DOWN and self.direction != Direction.UP) or \
           (direction == Direction.LEFT and self.direction != Direction.RIGHT) or \
           (direction == Direction.RIGHT and self.direction != Direction.LEFT):
            self.direction = direction

class Food:
    def __init__(self):
        self.position = (0, 0)
        self.randomize_position()
        
    def randomize_position(self):
        self.position = (random.randint(0, GRID_WIDTH - 1), 
                         random.randint(0, GRID_HEIGHT - 1))
        
    def render(self, surface):
        pygame.draw.rect(surface, RED, 
                         (self.position[0] * GRID_SIZE, self.position[1] * GRID_SIZE, 
                          GRID_SIZE, GRID_SIZE))

class BugItem:
    def __init__(self):
        self.position = (0, 0)
        self.active = False
        self.bug_type = random.choice(["syntax", "logic", "runtime"])
        
    def activate(self):
        self.position = (random.randint(0, GRID_WIDTH - 1), 
                         random.randint(0, GRID_HEIGHT - 1))
        self.active = True
        self.bug_type = random.choice(["syntax", "logic", "runtime"])
        
    def render(self, surface):
        if self.active:
            color = YELLOW if self.bug_type == "syntax" else BLUE if self.bug_type == "logic" else PURPLE
            pygame.draw.rect(surface, color, 
                             (self.position[0] * GRID_SIZE, self.position[1] * GRID_SIZE, 
                              GRID_SIZE, GRID_SIZE))

class Game:
    def __init__(self):
        pygame.init()
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Coder Snake")
        self.font = pygame.font.SysFont('monospace', 16)
        self.big_font = pygame.font.SysFont('monospace', 32)
        
        self.snake = Snake()
        self.food = Food()
        self.bug = BugItem()
        self.challenge = CodingChallenge()
        self.game_over = False
        self.paused = False
        self.user_input = ""
        self.challenge_active = False
        
    def handle_keys(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False
                
            elif event.type == pygame.KEYDOWN:
                if self.challenge_active:
                    if event.key == pygame.K_RETURN:
                        self.check_solution()
                    elif event.key == pygame.K_BACKSPACE:
                        self.user_input = self.user_input[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        self.challenge_active = False
                        self.challenge.active = False
                    else:
                        if event.unicode.isprintable():
                            self.user_input += event.unicode
                else:
                    if self.game_over:
                        if event.key == pygame.K_SPACE:
                            self.reset_game()
                    elif event.key == pygame.K_UP:
                        self.snake.change_direction(Direction.UP)
                    elif event.key == pygame.K_DOWN:
                        self.snake.change_direction(Direction.DOWN)
                    elif event.key == pygame.K_LEFT:
                        self.snake.change_direction(Direction.LEFT)
                    elif event.key == pygame.K_RIGHT:
                        self.snake.change_direction(Direction.RIGHT)
                    elif event.key == pygame.K_p:
                        self.paused = not self.paused
                    
        return True
    
    def check_solution(self):
        if self.user_input.strip() == self.challenge.solution:
            self.snake.coding_power += 10
            self.snake.challenges_completed += 1
            self.challenge.completed = True
        else:
            self.snake.length = max(3, self.snake.length - 1)
        
        self.challenge_active = False
        self.challenge.active = False
        self.user_input = ""
    
    def update(self):
        if self.paused or self.game_over or self.challenge_active:
            return
            
        if not self.snake.update():
            self.game_over = True
            return
            
        head_pos = self.snake.get_head_position()
        
        # Check for food collision
        if head_pos == self.food.position:
            self.snake.length += 1
            self.snake.score += 10
            self.food.randomize_position()
            
            # Occasionally spawn a bug
            if random.random() < 0.3:
                self.bug.activate()
                
            # Occasionally trigger a coding challenge
            if random.random() < 0.2:
                self.activate_challenge()
        
        # Check for bug collision
        if self.bug.active and head_pos == self.bug.position:
            self.bug.active = False
            
            if self.bug.bug_type == "syntax":
                self.activate_challenge()
            elif self.bug.bug_type == "logic":
                # Reverse direction
                if self.snake.direction == Direction.UP:
                    self.snake.change_direction(Direction.DOWN)
                elif self.snake.direction == Direction.DOWN:
                    self.snake.change_direction(Direction.UP)
                elif self.snake.direction == Direction.LEFT:
                    self.snake.change_direction(Direction.RIGHT)
                elif self.snake.direction == Direction.RIGHT:
                    self.snake.change_direction(Direction.LEFT)
            elif self.bug.bug_type == "runtime":
                # Slow down for a few seconds
                global FRAME_RATE
                FRAME_RATE = 5
                pygame.time.set_timer(pygame.USEREVENT, 3000)  # Reset speed after 3 seconds
        
        # Check if challenge time expired
        if self.challenge.active and not self.challenge.check_time():
            self.challenge.active = False
            self.snake.length = max(3, self.snake.length - 1)
    
    def activate_challenge(self):
        self.challenge.generate()
        self.challenge_active = True
        self.user_input = ""
    
    def render(self):
        self.screen.fill(BLACK)
        
        if not self.game_over and not self.challenge_active:
            self.snake.render(self.screen)
            self.food.render(self.screen)
            if self.bug.active:
                self.bug.render(self.screen)
            
            # Display score and coding power
            score_text = self.font.render(f"Score: {self.snake.score}", True, WHITE)
            power_text = self.font.render(f"Coding Power: {self.snake.coding_power}", True, WHITE)
            challenges_text = self.font.render(f"Challenges: {self.snake.challenges_completed}", True, WHITE)
            self.screen.blit(score_text, (10, 10))
            self.screen.blit(power_text, (10, 30))
            self.screen.blit(challenges_text, (10, 50))
            
            if self.paused:
                paused_text = self.big_font.render("PAUSED", True, WHITE)
                self.screen.blit(paused_text, (WINDOW_WIDTH // 2 - 60, WINDOW_HEIGHT // 2 - 20))
        
        elif self.challenge_active:
            # Draw challenge interface
            pygame.draw.rect(self.screen, (50, 50, 50), 
                             (WINDOW_WIDTH // 6, WINDOW_HEIGHT // 6, 
                              WINDOW_WIDTH * 2 // 3, WINDOW_HEIGHT * 2 // 3))
            
            challenge_text = self.font.render(self.challenge.challenge_text, True, WHITE)
            time_left = max(0, self.challenge.time_limit - (time.time() - self.challenge.start_time))
            time_text = self.font.render(f"Time left: {int(time_left)}s", True, WHITE)
            
            input_text = self.font.render(self.user_input, True, GREEN)
            prompt_text = self.font.render("Your solution:", True, WHITE)
            
            self.screen.blit(challenge_text, (WINDOW_WIDTH // 6 + 20, WINDOW_HEIGHT // 6 + 20))
            self.screen.blit(time_text, (WINDOW_WIDTH // 6 + 20, WINDOW_HEIGHT // 6 + 50))
            self.screen.blit(prompt_text, (WINDOW_WIDTH // 6 + 20, WINDOW_HEIGHT // 6 + 90))
            self.screen.blit(input_text, (WINDOW_WIDTH // 6 + 20, WINDOW_HEIGHT // 6 + 120))
        
        else:  # Game over
            game_over_text = self.big_font.render("GAME OVER", True, RED)
            score_text = self.big_font.render(f"Score: {self.snake.score}", True, WHITE)
            power_text = self.big_font.render(f"Coding Power: {self.snake.coding_power}", True, WHITE)
            restart_text = self.font.render("Press SPACE to restart", True, WHITE)
            
            self.screen.blit(game_over_text, (WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2 - 60))
            self.screen.blit(score_text, (WINDOW_WIDTH // 2 - 90, WINDOW_HEIGHT // 2 - 20))
            self.screen.blit(power_text, (WINDOW_WIDTH // 2 - 120, WINDOW_HEIGHT // 2 + 20))
            self.screen.blit(restart_text, (WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2 + 60))
        
        pygame.display.update()
    
    def reset_game(self):
        self.snake.reset()
        self.food.randomize_position()
        self.bug.active = False
        self.game_over = False
        self.paused = False
        self.challenge_active = False
        global FRAME_RATE
        FRAME_RATE = 10
    
    def run(self):
        while True:
            if not self.handle_keys():
                break
                
            self.update()
            self.render()
            self.clock.tick(FRAME_RATE)

if __name__ == "__main__":
    game = Game()
    game.run()