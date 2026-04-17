import pygame
import random

# --- Config ---
GRID_SIZE = 64
CELL_SIZE = 10  # pixels per cell
WIDTH = GRID_SIZE * CELL_SIZE
HEIGHT = GRID_SIZE * CELL_SIZE

# --- Init ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Marble Grid")
clock = pygame.time.Clock()

# --- Marble Class ---
class Marble:
    def __init__(self, x, y, color=(255, 255, 255)):
        self.x = x
        self.y = y
        self.color = color

    def move_up(self):
        if self.y > 0:
            self.y -= 1

    def move_down(self):
        if self.y < GRID_SIZE - 1:
            self.y += 1

    def move_left(self):
        if self.x > 0:
            self.x -= 1

    def move_right(self):
        if self.x < GRID_SIZE - 1:
            self.x += 1

    def draw(self, surface):
        pygame.draw.circle(
            surface,
            self.color,
            (
                self.x * CELL_SIZE + CELL_SIZE // 2,
                self.y * CELL_SIZE + CELL_SIZE // 2
            ),
            CELL_SIZE // 3
        )

# --- Create Marbles ---
marbles = [
    Marble(random.randint(0, 63), random.randint(0, 63), (255, 0, 0)),
    Marble(random.randint(0, 63), random.randint(0, 63), (0, 255, 0)),
    Marble(random.randint(0, 63), random.randint(0, 63), (0, 0, 255)),
]

# --- Main Loop ---
running = True
while running:
    screen.fill((0, 0, 0))

    # Draw grid (optional but helpful)
    for x in range(0, WIDTH, CELL_SIZE):
        pygame.draw.line(screen, (40, 40, 40), (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, CELL_SIZE):
        pygame.draw.line(screen, (40, 40, 40), (0, y), (WIDTH, y))

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- Example movement (random for now) ---
    for marble in marbles:
        move = random.choice(["up", "down", "left", "right"])
        if move == "up":
            marble.move_up()
        elif move == "down":
            marble.move_down()
        elif move == "left":
            marble.move_left()
        elif move == "right":
            marble.move_right()

    # Draw marbles
    for marble in marbles:
        marble.draw(screen)

    pygame.display.flip()
    clock.tick(10)  # slow so you can see movement

pygame.quit()