import time

import pygame
import random
import torch as pt
import torch.nn as nn
import copy
import os
import threading #for the like input thing
import curses # so terminal doesn't SUCK
import pandas as pd
import plotly.graph_objects as go

GRID_SIZE = 64
CELL_SIZE = 10
WIDTH = GRID_SIZE * CELL_SIZE
HEIGHT = GRID_SIZE * CELL_SIZE

foodReward = 50
INITIAL_MARBLES = 5
MAX_MARBLES = 100
FOOD_COUNT = 100
speed = 200
log_iter = 0

rChance = 0
MUTATION_STRENGTH = 0.01
weightsDir = "marble_weights"
FOOD_DIRECTION_BONUS = 0.10


screen = None
clock = None
marble_lifespans = [] #array to store the like marble ages stuff so we can later graph it ye
#metrics_by_iteration = defaultdict(list)  # Track metrics per iteration


# default global logger — prints to stdout; curses_main will override this
def log(*args, **kwargs):
    print(*args, **kwargs)


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
        

        #this bit here is vibecoded. We'll see if it works
        # Small heuristic nudge toward the nearest food direction.
        ndx = inputs[4].item()
        ndy = inputs[5].item()
        if ndy < 0:
            output[0] += FOOD_DIRECTION_BONUS  # up
        elif ndy > 0:
            output[1] += FOOD_DIRECTION_BONUS  # down
        if ndx < 0:
            output[2] += FOOD_DIRECTION_BONUS  # left
        elif ndx > 0:
            output[3] += FOOD_DIRECTION_BONUS  # right
        #end: vibe coded
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
        self.color = (0, 255, 0)

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
        self.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)) #random color for fun. Fun? That was the ai autocomplete thing. I just think it makes it look better but uh I'm rambling im gonna stop and push this code

        self.brain = brain if brain is not None else MarbleBrain()
        self.hunger = 250
        self.age = 0  
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


def save_marbles_weights(marbles, directory=weightsDir):
    os.makedirs(directory, exist_ok=True)

    #clear previous marble weight files so the directory mirrors current marbles
    for filename in os.listdir(directory):
        if filename.startswith("marble_") and filename.endswith(".pt"):
            os.remove(os.path.join(directory, filename))

    for i, marble in enumerate(marbles):
        path = os.path.join(directory, f"marble_{i}.pt")
        pt.save(marble.brain.state_dict(), path)

    log(f"Saved {len(marbles)} marble brains to '{directory}'")


def load_marbles_from_weights(directory=weightsDir):
    if not os.path.isdir(directory):
        log(f"No weights directory found at '{directory}'")
        return []

    weight_files = sorted(
        [f for f in os.listdir(directory) if f.startswith("marble_") and f.endswith(".pt")],
        key=lambda name: int(name.split("_")[1].split(".")[0])
    )

    if not weight_files:
        log(f"No marble weight files found in '{directory}'")
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

    log(f"Loaded {len(loaded_marbles)} marble brains from '{directory}'")
    return loaded_marbles


def plot():
    #Yes, this function here is vibecoded. The simulation is alreay done, all the hard parts are done, and frankly I have better things to do then this
    """Generate an interactive plotly graph of marble lifespans over time."""
    if not marble_lifespans:
        log("No lifespan data collected yet.")
        return
    
    try:
        # Create dataframe
        df = pd.DataFrame({
            'Marble_ID': range(len(marble_lifespans)),
            'Lifespan': marble_lifespans
        })
        
        # Calculate running average
        df['Running_Avg'] = df['Lifespan'].expanding().mean()
        
        # Create figure
        fig = go.Figure()
        
        # Add scatter plot of individual lifespans
        fig.add_trace(go.Scatter(
            x=df['Marble_ID'],
            y=df['Lifespan'],
            mode='markers',
            name='Individual Lifespan',
            marker=dict(size=5, color='rgba(100, 150, 255, 0.6)'),
            hovertemplate='<b>Marble %{x}</b><br>Age: %{y} iterations<extra></extra>'
        ))
        
        # Add running average line
        fig.add_trace(go.Scatter(
            x=df['Marble_ID'],
            y=df['Running_Avg'],
            mode='lines',
            name='Running Average',
            line=dict(color='red', width=2),
            hovertemplate='<b>Running Avg</b><br>Average: %{y:.1f} iterations<extra></extra>'
        ))
        
        fig.update_layout(
            title='Marble Lifespan Evolution',
            xaxis_title='Marble Generation',
            yaxis_title='Lifespan (iterations)',
            hovermode='x unified',
            template='plotly_dark',
            width=1000,
            height=600
        )
        
        # Save and show
        output_file = 'marble_lifespan_graph.html'
        fig.write_html(output_file)
        log(f"Graph saved to {output_file}. Open it in a web browser to view.")
        log(f"Average lifespan: {df['Lifespan'].mean():.1f} iterations")
        log(f"Max lifespan: {df['Lifespan'].max()} iterations")
        log(f"Min lifespan: {df['Lifespan'].min()} iterations")
        
    except Exception as e:
        log(f"Error plotting lifespan data: {e}")


def main():



    global screen, clock, running
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Marble Evolution")
    clock = pygame.time.Clock()
    marbles = load_marbles_from_weights()
    if not marbles:
        log("No saved marbles found, starting with random marbles.")
        marbles = [
            Marble(random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1))
            for _ in range(INITIAL_MARBLES)
        ]
    else:
        log(f"Starting with {len(marbles)} loaded marbles.")
    foods = []
    for _ in range(FOOD_COUNT):
        spawn_food(marbles, foods)
    log("Waiting 2 seconds...")
    time.sleep(2)
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
            global log_iter
            marble.age += 1
            marble.decide(foods)
            if log_iter % 1000 == 0:
                log(f"Marble at ({marble.x}, {marble.y}) with hunger {marble.hunger}: ")
                for name, param in marble.brain.named_parameters():
                    log(f"{name}: {param.data}")
            
            #marble dies when hunger is depleted
            if marble.hunger <= 0:
                marble_lifespans.append(marble.age)  #record lifespan.
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
                marble.hunger += foodReward

                # duplicate on eat (with mutation)
                if len(marbles) < MAX_MARBLES:
                    marbles.append(marble.clone_with_mutation())
        log_iter += 1
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





def curses_main(stdscr):
    global log, running
    curses.curs_set(1)
    stdscr.clear()

    height, width = stdscr.getmaxyx()

    # Split screen: top = output, bottom = input
    output_h = height - 3
    input_h = 3

    output_win = curses.newwin(output_h, width, 0, 0)
    input_win = curses.newwin(input_h, width, output_h, 0)

    output_win.scrollok(True)
    input_win.border()

    log_lines = []

    def log(msg):
        try:
            log_lines.append(msg)

            output_win.clear()

            # Show only visible lines
            max_lines = output_h - 1
            visible = log_lines[-max_lines:]

            for i, line in enumerate(visible):
                output_win.addstr(i, 0, line[:width - 1])

            output_win.refresh()
        except Exception as e:
            # If logging fails, print to standard output as a fallback
            try:
                log("Logging error:", e)
            except Exception as e:
                print(f"Logging error: {e}")
                print(f"The message was: {msg}")
    def get_input(prompt="> "):
        input_win.clear()
        input_win.border()
        input_win.addstr(1, 1, prompt)
        input_win.refresh()

        curses.echo()
        user_input = input_win.getstr(1, len(prompt) + 1).decode("utf-8")
        curses.noecho()

        return user_input
    def init_menu(): 
        log("Console started")
        log("   Current settings:")
        log(f"  Random chance {rChance}")
        log(f"  Mutation strength {MUTATION_STRENGTH}")
        log(f"  Food reward: {foodReward}")
        log(f"  Init marbles: {INITIAL_MARBLES}")
        log(f"  Max Marbles: {MAX_MARBLES}")
    # Demo loop
    init_menu()
    while True:
        global running
        cmd = get_input()
        log(f"> {cmd}")
        if cmd.lower() in ("quit", "exit"):
            running = False
            exit(1)
        elif cmd.lower() in ("help", "?"):
            log("Commands:")
            log("  help/? - Show this message")
            log("  quit/exit - Exit the program")
            log("  rchance <value> - Set random move chance (0.0 to 1.0)")
            log("  exec <code> - Execute arbitrary Python code (use with caution!)")
            log("  start - Start the marble evolution simulation")
            log("  plot/graph - Generate lifespan graph and save as HTML")
            log(" omg I clicked tab and ai generated list of all my commands so cool")
        elif cmd.lower().startswith("rchance"):
            try:
                global rChance
                value_str = cmd[7:].strip()  # "rchance" is 7 characters
                if not value_str:
                    log("Error: COuldn't find number after rChance command")
                    continue
                rChance = float(value_str)
                log(f"Successfully updated rChance to {rChance}")
            except ValueError as e:
                log(f"Error getting new rChance value: {e}")
                continue
            
        elif cmd.lower().startswith("exec"):
            code = cmd[4:].strip()  # "exec" is 4 characters
            if not code:
                log("Error: No code provided to exec command")
                continue
            try:
                exec(code, globals())
                log("Executed sucessfully")
            except Exception as e:
                log(f"Error executing code: {e}")
        elif cmd.lower().startswith("start"):   
            try:
                running = True
                thread = threading.Thread(target=main)
                log("Starting main loop...")
                thread.start()
            except Exception as e:
                log(f"Error starting main loop: {e}")
        elif cmd.lower() in ("plot", "graph"):
            plot()
                

curses.wrapper(curses_main)





