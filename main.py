import pygame
import random
import torch as pt
import torch.nn as nn
import copy
import os

GRID_SIZE = 64
CELL_SIZE = 10
WIDTH = GRID_SIZE * CELL_SIZE
HEIGHT = GRID_SIZE * CELL_SIZE

INITIAL_MARBLES = 20
MAX_MARBLES = 100
FOOD_COUNT = 100
speed = 2000

rChance = 0.5
MUTATION_STRENGTH = 0.01
WEIGHTS_DIR = "marble_weights"


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Marble Evolution")
clock = pygame.time.Clock()


class MarbleBrain(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(10, 32), #INPUT SIZE = 10. brain input: marble(x,y) + nearest_food(x,y,dx,dy) + wall_dist(up,down,left,right) 
            nn.ReLU(),
            nn.Linear(32, 4)  # up/down/left/right
        )

    def forward(self, x):
        return self.net(x)

    def decide_move(self, inputs, x, y):
        output = self.forward(inputs).clone()

        # mask illegal moves
        if y <= 0:
            output[0] = -1e9  # up
        if y >= GRID_SIZE - 1:
            output[1] = -1e9  # down
        if x <= 0:
            output[2] = -1e9  # left
        if x >= GRID_SIZE - 1:
            output[3] = -1e9  # right

        move = pt.argmax(output).item()
        return ["up", "down", "left", "right"][move]

    def mutate(self, strength=MUTATION_STRENGTH):
        with pt.no_grad():
            for param in self.parameters():
                param += pt.randn_like(param) * strength


class Food:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.color = (255, 255, 255)

    def draw(self, surface):
        pygame.draw.circle(
            surface,
            self.color,
            (self.x * CELL_SIZE + CELL_SIZE // 2, self.y * CELL_SIZE + CELL_SIZE // 2),
            CELL_SIZE // 3
        )


class Marble:
    def __init__(self, x, y, color=(255, 0, 0), brain=None):
        self.x = x
        self.y = y
        self.color = color
        self.brain = brain if brain is not None else MarbleBrain()
        self.hunger = 500
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

    def apply_move(self, move):
        if move == "up":
            self.move_up()
        elif move == "down":
            self.move_down()
        elif move == "left":
            self.move_left()
        elif move == "right":
            self.move_right()
        self.hunger -= 1
    def build_local_state(self, foods):
        # nearest food
        nearest = min(foods, key=lambda f: abs(f.x - self.x) + abs(f.y - self.y))
        dx = nearest.x - self.x
        dy = nearest.y - self.y

        # normalize position to 0-1 bc internet ppl told me to do this
        nx = self.x / (GRID_SIZE - 1)
        ny = self.y / (GRID_SIZE - 1)

        # nearest food position
        nfx = nearest.x / (GRID_SIZE - 1)
        nfy = nearest.y / (GRID_SIZE - 1)

        # so like normalize the things ye
        ndx = dx / (GRID_SIZE - 1)
        ndy = dy / (GRID_SIZE - 1)

        # wall distances normalized [0,1]
        up_d = self.y / (GRID_SIZE - 1)
        down_d = (GRID_SIZE - 1 - self.y) / (GRID_SIZE - 1)
        left_d = self.x / (GRID_SIZE - 1)
        right_d = (GRID_SIZE - 1 - self.x) / (GRID_SIZE - 1)

        return pt.tensor(
            [nx, ny, nfx, nfy, ndx, ndy, up_d, down_d, left_d, right_d],
            dtype=pt.float32
        )

    def decide(self, foods):
        state = self.build_local_state(foods)
        #uh so if like the random chance is like true ro false then the brain turns on or off and this allows us to allow the marble to actually train yk
        if random.random() < rChance:
            move = random.choice(["up", "down", "left", "right"])
            # keep random move legal
            legal = []
            if self.y > 0: legal.append("up")
            if self.y < GRID_SIZE - 1: legal.append("down")
            if self.x > 0: legal.append("left")
            if self.x < GRID_SIZE - 1: legal.append("right")
            move = random.choice(legal) if legal else "up"
        else:
            move = self.brain.decide_move(state, self.x, self.y)

        self.apply_move(move)

    def draw(self, surface):
        pygame.draw.circle(
            surface,
            self.color,
            (self.x * CELL_SIZE + CELL_SIZE // 2, self.y * CELL_SIZE + CELL_SIZE // 2),
            CELL_SIZE // 3
        )

    def clone_with_mutation(self):
        child_brain = copy.deepcopy(self.brain)
        child_brain.mutate(MUTATION_STRENGTH)

        # spawn child near parent 
        cx = self.x + random.choice([-1, 0, 1])
        cy = self.y + random.choice([-1, 0, 1])
        cx = max(0, min(GRID_SIZE - 1, cx))
        cy = max(0, min(GRID_SIZE - 1, cy))

        return Marble(cx, cy, self.color, brain=child_brain)


def random_empty_cell(marbles, foods):
    occupied = {(m.x, m.y) for m in marbles}
    occupied |= {(f.x, f.y) for f in foods}

    for _ in range(2000):
        x = random.randint(0, GRID_SIZE - 1)
        y = random.randint(0, GRID_SIZE - 1)
        if (x, y) not in occupied:
            return x, y

    # fallback if very crowded. Shouldn't happen.. but like.. it could
    return random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)


def spawn_food(marbles, foods):
    x, y = random_empty_cell(marbles, foods)
    foods.append(Food(x, y))


def draw_grid():
    for x in range(0, WIDTH, CELL_SIZE):
        pygame.draw.line(screen, (40, 40, 40), (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, CELL_SIZE):
        pygame.draw.line(screen, (40, 40, 40), (0, y), (WIDTH, y))


def save_marbles_weights(marbles, directory=WEIGHTS_DIR):
    os.makedirs(directory, exist_ok=True)

    #clear previous marble weight files so the directory mirrors current marbles
    for filename in os.listdir(directory):
        if filename.startswith("marble_") and filename.endswith(".pt"):
            os.remove(os.path.join(directory, filename))

    for i, marble in enumerate(marbles):
        path = os.path.join(directory, f"marble_{i}.pt")
        pt.save(marble.brain.state_dict(), path)

    print(f"Saved {len(marbles)} marble brains to '{directory}'")


def load_marbles_from_weights(directory=WEIGHTS_DIR):
    if not os.path.isdir(directory):
        print(f"No weights directory found at '{directory}'")
        return []

    weight_files = sorted(
        [f for f in os.listdir(directory) if f.startswith("marble_") and f.endswith(".pt")],
        key=lambda name: int(name.split("_")[1].split(".")[0])
    )

    if not weight_files:
        print(f"No marble weight files found in '{directory}'")
        return []

    loaded_marbles = []
    for filename in weight_files:
        path = os.path.join(directory, filename)
        brain = MarbleBrain()
        state_dict = pt.load(path, map_location=pt.device("cpu"))
        brain.load_state_dict(state_dict)

        loaded_marbles.append(
            Marble(
                random.randint(0, GRID_SIZE - 1),
                random.randint(0, GRID_SIZE - 1),
                brain=brain
            )
        )

    print(f"Loaded {len(loaded_marbles)} marble brains from '{directory}'")
    return loaded_marbles


def main():
    marbles = load_marbles_from_weights()
    if not marbles:
        marbles = [
            Marble(random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1))
            for _ in range(INITIAL_MARBLES)
        ]

    foods = []
    for _ in range(FOOD_COUNT):
        spawn_food(marbles, foods)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_s:
                    save_marbles_weights(marbles)

        #Main loop for each marble
        for marble in list(marbles):
            marble.decide(foods)
            print(f"Marble at ({marble.x}, {marble.y}) with hunger {marble.hunger}")
            #marble dies when hunger is depleted
            if marble.hunger <= 0:
                marbles.remove(marble)
                continue

            #check collisions
            eaten = None
            for f in foods:
                if marble.x == f.x and marble.y == f.y:
                    eaten = f
                    break

            if eaten is not None:
                new_x, new_y = random_empty_cell(marbles, foods)
                eaten.x = new_x
                eaten.y = new_y
                marble.hunger += 500

                # duplicate on eat (with mutation)
                if len(marbles) < MAX_MARBLES:
                    marbles.append(marble.clone_with_mutation())

        # --- Draw ---
        screen.fill((0, 0, 0))
        draw_grid()

        for f in foods:
            f.draw(screen)
        for m in marbles:
            m.draw(screen)

        pygame.display.flip()
        clock.tick(speed)

    pygame.quit()


main()