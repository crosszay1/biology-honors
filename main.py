import pygame
import random
import torch as pt #pt = pytorch. feels cool to do acronyms I guess. I just realized I talk to myself in code comments alot. Why? 
import torch.nn as nn ## nn = neural network. 
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

class MarbleBrain(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(4, 8),  # inputs 
            nn.ReLU(), #remove negatives
            nn.Linear(8, 4)   # outputs 
        )
    def forward(self, x):
        return self.net(x)
# --- Marble Class ---
class Marble:
    def __init__(self, x, y, color=(255, 255, 255), weights=None):
        self.x = x
        self.y = y
        self.color = color
        self.weights = [] #We shall store them weights here
        self.brain = MarbleBrain() # Initialize the neural network
    def move_up(self):
        if self.y > 0:
            self.y -= 1 # -1, because y=0 is top row, and y increases as we go down
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
    def decide(self, weights):
        #Where the magic actually happens. This is where the marble will decide which direction to move based on the weights.
        #For now let's do a random move as a placeholder
        move = random.choice(['up', 'down', 'left', 'right'])
        if move == 'up':
            self.move_up()
        elif move == 'down':
            self.move_down()
        elif move == 'left':
            self.move_left()
        elif move == 'right':
            self.move_right()

    def snapshot(self): #Do we need a function for this? No.... but it looks cleaner, ya know?
        return {
            'x': self.x,
            'y': self.y,
        }
class food:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.color = color=(255, 255, 255)
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
marbles = [ #spawn marbles at random places
    Marble(random.randint(0, 63), random.randint(0, 63), (255, 0, 0)),
    Marble(random.randint(0, 63), random.randint(0, 63), (255, 0, 0)),
    Marble(random.randint(0, 63), random.randint(0, 63), (255, 0, 0)),
    Marble(random.randint(0, 63), random.randint(0, 63), (255, 0, 0)),
    Marble(random.randint(0, 63), random.randint(0, 63), (255, 0, 0)),
    Marble(random.randint(0, 63), random.randint(0, 63), (255, 0, 0)),
    Marble(random.randint(0, 63), random.randint(0, 63), (255, 0, 0)),
    Marble(random.randint(0, 63), random.randint(0, 63), (255, 0, 0)),
    Marble(random.randint(0, 63), random.randint(0, 63), (255, 0, 0)),
    Marble(random.randint(0, 63), random.randint(0, 63), (255, 0, 0)),
]
foods = [ #spawn food at random places
    food(random.randint(0, 63), random.randint(0, 63)),
    food(random.randint(0, 63), random.randint(0, 63)),
    food(random.randint(0, 63), random.randint(0, 63)),
]
def get_all_marbles():
    return [marble.snapshot() for marble in marbles]

def main():
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                print(get_all_marbles())

        screen.fill((0, 0, 0))

        for x in range(0, WIDTH, CELL_SIZE):
            pygame.draw.line(screen, (40, 40, 40), (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, CELL_SIZE):
            pygame.draw.line(screen, (40, 40, 40), (0, y), (WIDTH, y))

        for marble in marbles:
            marble.decide(marble.weights)
            marble.draw(screen)
        print(get_all_marbles())
        pygame.display.flip()
        clock.tick(20)

    pygame.quit()


main()