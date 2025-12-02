""" Scientific method: Questions: How long will it take to find the ideal marble (to 2 decimal places). How many generations does it take? how many marbles does it take? what IS the ideal marble? 
procedure plan: 5 marbles race to a goal, find the winner, everyone else dies, winner then splits into 4 new marbles, except those have mutated slightly, + or minus 0.1-0.5, the marbles then race. repeat.
coding checklist:
5 marbles race ...done 
winner found ... done
everyone else dies ...done 
winner splits ...done
new marbles mutate ...done
repeat ...done
original marble mass still present? ..done
results: 
On the following settings: change: 0.01   round: 6   inital mass: 0,1,1   ground friction: none
we found our result in 252 generatuins.

"""








import time
import pymunk  # Physics engine for 2D simulations
import pymunk.pygame_util  # Utility functions to draw Pymunk objects in Pygame
import pygame  # Library for making games and multimedia applications
import math, random
# --- Settings ---
from src.settings import SCREEN_HEIGHT, SCREEN_WIDTH

# Pygame initialization
pygame.init()  # Initialize all imported Pygame modules
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))  # Create game window
clock = pygame.time.Clock()  # Clock to control game FPS
draw_options = pymunk.pygame_util.DrawOptions(screen)  # Setup drawing helper for Pymunk
Generation = 0
#variables
balls = []
predators = []
ballgroup = pymunk.ShapeFilter(group=1)
old_placed = False
winner_mass_ball = None
winner_mass_predator = None
space = pymunk.Space()  
space.gravity = (0, 900) 
# Ground
Ground = pymunk.Segment(space.static_body, (0, SCREEN_HEIGHT-50), (SCREEN_WIDTH, SCREEN_HEIGHT-50), 3)
Finish_line = pymunk.Segment(space.static_body, (750, SCREEN_HEIGHT), (SCREEN_WIDTH-50, SCREEN_HEIGHT-550), 5)

race_finished = False

# Create a static Ground (line) representing the ground
Finish_line.color = (0, 128, 0, 0)
Finish_line.collision_type = 1
Ground.elasticity = 0.8
space.add(Ground, Finish_line)

def create5balls(rand_low, rand_high, old_mass):
    global balls
    balls = []  # reset fresh

    for i in range(5):
        if i == 0:
            # exact copy of the winner
            mass = old_mass
        else:
            # mutation
            random_between = round(random.uniform(rand_low, rand_high), 6)
            mass = old_mass + random_between 
            if mass < 0: #if the mass is less then -1, the program throws some weird bounds error at me.
                mass = old_mass + 0.01  

        radius = 20 + abs(mass - old_mass)
        ball = pymunk.Body(mass, pymunk.moment_for_circle(mass, 0, radius))
        ball.position = (49.8, SCREEN_HEIGHT - 100 - i*5)

        shape = pymunk.Circle(ball, radius)
        shape.name = f"ball {i}"
        shape.elasticity = 0.8
        shape.collision_type = 2
        shape.filter = pymunk.ShapeFilter(group=1)

        print(f"ball {i} has a mass of: {ball.mass}")
        space.add(ball, shape)
        balls.append(ball)
def createpredator(rand_low, rand_high, old_mass):
    global predators
    predators = []  # reset fresh

    for i in range(4):
        if i == 0:
            mass = old_mass
        else:
            random_between = round(random.uniform(rand_low, rand_high), 6)
            mass = old_mass + random_between
            if mass < 0:
                mass = old_mass + 0.01

        radius = 20 + abs(mass - old_mass)

        body = pymunk.Body(mass, pymunk.moment_for_circle(mass, 0, radius))
        body.position = (0, SCREEN_HEIGHT - 200 - i*40)  # spawn behind
        shape = pymunk.Circle(body, radius)
        shape.name = f"predator {i}"
        shape.elasticity = 0.0
        shape.collision_type = 3
        shape.filter = pymunk.ShapeFilter(group=3)

        shape.color = (255, 0, 0, 255)  # visible red

        print(f"predator {i} mass:", mass)

        space.add(body, shape)
        predators.append(body)

# --- Collision handler ---
def on_win(arbiter, space, data):
    global race_finished, winner_mass_ball
    if race_finished:
        return

    finish, ball = arbiter.shapes
    winner_mass_ball = ball.body.mass
    print(f"{ball.name} wins with mass {winner_mass_ball}")

    race_finished = True
    return False

# --- Robust collision handler for predator eats ball ---
def on_eaten(arbiter, space, data):
    shape_a, shape_b = arbiter.shapes
    
    # identify which is ball/predator
    if shape_a.collision_type == 2 and shape_b.collision_type == 3:
        ball = shape_a
        pred = shape_b
    elif shape_b.collision_type == 2 and shape_a.collision_type == 3:
        ball = shape_b
        pred = shape_a
    else:
        return True

    print(f"{ball.name} collided with {pred.name}. Both destroyed.")

    # Schedule deletion instead of deleting now
    to_delete.append(ball)
    to_delete.append(pred)

    # Remove from Python lists immediately
    global balls, predators
    balls = [b for b in balls if b is not ball.body]
    predators = [p for p in predators if p is not pred.body]

    return False

space.on_collision(1, 2, begin=on_win)      # finish line with balls
space.on_collision(2, 3, begin=on_eaten)    # ball with predator

def delete_balls():
    global balls
    for body in balls:
        for shape in body.shapes:  # remove each shape attached to the body
            space.remove(shape)
        space.remove(body)          # remove the body itself
    balls = []  # clear your list reference
def delete_predators():
    global predators
    # iterate a copy so we can mutate
    for body in predators[:]:
        # remove attached shapes
        for shape in getattr(body, "shapes", []):
            try:
                if shape.space is space:
                    space.remove(shape)
            except Exception:
                pass
        # remove body
        try:
            if body.space is space:
                space.remove(body)
        except Exception:
            pass
    predators = []

running = True
print("---START---")
create5balls(0, 1, 1)  # only once at start
def loop():
    global race_finished, running, winner_mass_ball, Generation
    

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((255, 255, 255))

        # apply force until a winner
        if not race_finished:
            for ball in balls:  
                ball.apply_force_at_local_point((100, 0))
            for predator in predators:
                predator.apply_force_at_local_point((100, 0))
        else: #rest of code goes in here
            print("---START---")
            old_placed = False
            Generation += 1
            delete_balls()
            delete_predators()


            print(f"This is Generation {Generation}")
            with open("mass_list.txt", "a") as f:
                f.write(f"\nWinner mass: {winner_mass_ball} Generation: {Generation}")
            create5balls(-0.01, 0.01, winner_mass_ball) #regenerate balls
            createpredator(-1, 0.01, winner_mass_ball)
            race_finished = False
            time.sleep(0.3)
            
        space.step(1/60.0)
        space.debug_draw(draw_options)

        pygame.display.flip()
        clock.tick(250)

    pygame.quit()
    
loop()
