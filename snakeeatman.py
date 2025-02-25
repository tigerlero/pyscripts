import pygame
import random

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
GRID_SIZE = 8
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
SKIN_COLOR = (255, 224, 192)
HAIR_COLOR = (80, 80, 80)
MUSTACHE_COLOR = (50, 50, 50)
EYE_COLOR = (0, 0, 255)
NOSE_COLOR = (200, 180, 160)

# Create the screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pixel Face Snake")
direction = [1, 0]  # Initial direction: moving right

def handle_input():
    global direction
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP and direction != [0, 1]:
                direction = [0, -1]
            elif event.key == pygame.K_DOWN and direction != [0, -1]:
                direction = [0, 1]
            elif event.key == pygame.K_LEFT and direction != [1, 0]:
                direction = [-1, 0]
            elif event.key == pygame.K_RIGHT and direction != [-1, 0]:
                direction = [1, 0]
    return True

# More Detailed Face Data
face_pixels = [
    "..............",
    "..##..##......",
    ".########.....",
    ".##..##......",
    ".########.....",
    "...####......",
    "..######.....",
    ".########.....",
    "....##.......",
    "..##..##.....",
    "....##.......",
    "....##.......",
    "..####.......",
    "..............",
]

pr_messages = [
    "Let's synergize our core competencies.",
    "We need to enhance our brand narrative.",
    "This aligns with our strategic vision.",
    "We're pivoting to a customer-centric approach.",
    "We need to optimize our key performance indicators.",
    "Let's leverage our thought leadership.",
    "We need to create a holistic ecosystem.",
    "We're driving innovation through disruption.",
    "We need to amplify our social media presence.",
    "Let's create a viral campaign.",
    "We need to foster a culture of excellence.",
    "We're empowering our stakeholders."
]

# Create Face Grid with Colors
face_grid = [[WHITE for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
for y, row in enumerate(face_pixels):
    for x, char in enumerate(row):
        if char == '#':
            if 2 <= y <= 4:
                face_grid[y][x] = HAIR_COLOR
            elif 6 <= y <= 7:
                face_grid[y][x] = MUSTACHE_COLOR
            elif 9 <= y <= 10:
                face_grid[y][x] = EYE_COLOR
            elif y == 12:
                face_grid[y][x] = NOSE_COLOR
            else:
                face_grid[y][x] = SKIN_COLOR

# Snake
snake = [(GRID_WIDTH // 2, GRID_HEIGHT - 1)]


# Face Movement (Left-Right, Limited Out of Bounds)
face_move_direction = 1
face_move_speed = 1
face_offset_x = 0
left_bound_limit = -GRID_WIDTH // 4

# Game Loop
clock = pygame.time.Clock()
font = pygame.font.Font(None, 24)
text_display_timer = 0
text_display_duration = 2000

current_message = None

def draw_grid():
    for y, row in enumerate(face_grid):
        for x, cell in enumerate(row):
            screen_x = (x + face_offset_x) * GRID_SIZE
            if 0 <= screen_x < WIDTH:
                pygame.draw.rect(screen, cell, (screen_x, y * GRID_SIZE, GRID_SIZE, GRID_SIZE))

def draw_snake():
    for segment in snake:
        pygame.draw.rect(screen, GREEN, (segment[0] * GRID_SIZE, segment[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE))

    if current_message and pygame.time.get_ticks() - text_display_timer < text_display_duration:
        text = font.render(current_message, True, BLACK)
        screen.blit(text, (10, 10))

def move_snake():
    global snake, snake_direction
    head_x, head_y = snake[0]
    new_head = [head_x + snake_direction[0], head_y + snake_direction[1]]
    
    # Wrap around screen edges
    new_head[0] = new_head[0] % GRID_WIDTH
    new_head[1] = new_head[1] % GRID_HEIGHT
    
    snake.insert(0, new_head)
    if not check_eat():
        snake.pop()

def check_collision():
    head_x, head_y = snake[0]
    if head_x < 0 or head_x >= GRID_WIDTH or head_y < 0 or head_y >= GRID_HEIGHT:
        return True
    if (head_x, head_y) in snake[1:]:
        return True
    return False


def check_eat():
    global snake, face_grid, current_message, text_display_timer
    head_x, head_y = snake[0]
    adjusted_x = head_x - face_offset_x  # Adjust for face position
    
    # Check if snake head is within face grid bounds
    if 0 <= adjusted_x < len(face_grid[0]) and 0 <= head_y < len(face_grid):
        if face_grid[head_y][adjusted_x] != WHITE and face_grid[head_y][adjusted_x] != GREEN:
            # Instant pixel removal
            face_grid[head_y][adjusted_x] = WHITE
            screen_x = head_x * GRID_SIZE
            pygame.draw.rect(screen, WHITE, (screen_x, head_y*GRID_SIZE, GRID_SIZE, GRID_SIZE))
            pygame.display.update()
            
            current_message = random.choice(pr_messages)
            text_display_timer = pygame.time.get_ticks()
            snake.append(snake[-1])
            return True
    return False

def move_face():
    global face_offset_x, face_move_direction
    next_pos = face_offset_x + face_move_direction * face_move_speed
    
    # Set strict minimum and maximum bounds
    min_bound = 0
    max_bound = GRID_WIDTH // 4 - 2
    
    if next_pos < min_bound:
        face_offset_x = min_bound
        face_move_direction *= -1
    elif next_pos > max_bound:
        face_offset_x = max_bound
        face_move_direction *= -1
    else:
        face_offset_x = next_pos

def random_saying():
    global current_message, text_display_timer
    if random.random() < 0.01:
        current_message = random.choice(pr_messages)
        text_display_timer = pygame.time.get_ticks()

running = True
snake_direction = (1, 0)  # Initial direction: right

def check_win():
    # Check if any non-white pixels remain in face_grid
    for row in face_grid:
        for pixel in row:
            if pixel != WHITE and pixel != GREEN:
                return False
    return True


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP and snake_direction != (0, 1):
                snake_direction = (0, -1)
            elif event.key == pygame.K_DOWN and snake_direction != (0, -1):
                snake_direction = (0, 1)
            elif event.key == pygame.K_LEFT and snake_direction != (1, 0):
                snake_direction = (-1, 0)
            elif event.key == pygame.K_RIGHT and snake_direction != (-1, 0):
                snake_direction = (1, 0)

    move_snake()
    move_face()
    random_saying()

    if check_collision():
        print("Game Over!")
        running = False

    check_eat()
    if check_win():
        print("You Win! All pixels eaten!")
        running = False

    screen.fill(WHITE)
    draw_grid()
    draw_snake()  # draw snake and text
    pygame.display.flip()
    clock.tick(10)

pygame.quit()