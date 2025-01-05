import os
import pygame
from car import Car
import neat
import sys
import random
import math
from enum import Enum

WIDTH, HEIGHT = 683, 384

car_size = 30

obstacles_speed = 1.5
obstacles_rot = 90

class ObstacleDirection(Enum):
    TOP = ((310, 50), obstacles_speed, 2 * obstacles_rot) 
    BOTTOM = ((351, 334), obstacles_speed, 0)
    LEFT = ((40, 220), obstacles_speed, obstacles_rot)
    RIGHT = ((640, 160), obstacles_speed, 3 * obstacles_rot)

priority_order = [
    ObstacleDirection.TOP,
    ObstacleDirection.RIGHT,
    ObstacleDirection.BOTTOM,
    ObstacleDirection.LEFT
]

stop_lines = {
    ObstacleDirection.TOP: 140 - car_size,
    ObstacleDirection.BOTTOM: 234 + car_size,
    ObstacleDirection.LEFT: 255 - car_size,
    ObstacleDirection.RIGHT: 397 + car_size
}

active_obstacles = {
    ObstacleDirection.TOP: [],
    ObstacleDirection.BOTTOM: [],
    ObstacleDirection.LEFT: [],
    ObstacleDirection.RIGHT: []
}

def clear_obstacles():
    active_obstacles[ObstacleDirection.TOP].clear()
    active_obstacles[ObstacleDirection.BOTTOM].clear()
    active_obstacles[ObstacleDirection.LEFT].clear()
    active_obstacles[ObstacleDirection.RIGHT].clear()

class ObstacleCar(Car):
    def __init__(self, map, win_width, win_height, start_pos, car_size, radars_count, speed, rotation, direction):
        super().__init__(map, win_width, win_height, start_pos, car_size, radars_count)
        self.rect = self.image.get_rect(center=start_pos)
        self.speed = speed
        self.rotation = rotation
        self.direction = direction
        self.stop_position = stop_lines[direction]

    def get_right_priority(self):
        index = priority_order.index(self.direction)
        return priority_order[(index - 1) % len(priority_order)]
    
    def get_oposite_direction(self):
        index = priority_order.index(self.direction)
        return priority_order[(index + 2) % len(priority_order)]

    def is_at_stop_position(self):
        if self.direction in [ObstacleDirection.TOP, ObstacleDirection.BOTTOM]:
            return abs(self.rect.y - self.stop_position) <= 2
        else:
            return abs(self.rect.x - self.stop_position) <= 2

    # Check if any other car is in the intersection
    def is_intersection_busy(self):
        for direction in active_obstacles:
            for obs in active_obstacles[direction]:
                if obs == self:
                    continue
                if (direction in [ObstacleDirection.TOP, ObstacleDirection.BOTTOM] and
                    stop_lines[ObstacleDirection.TOP] < obs.rect.y < stop_lines[ObstacleDirection.BOTTOM]) or \
                (direction in [ObstacleDirection.LEFT, ObstacleDirection.RIGHT] and
                    stop_lines[ObstacleDirection.LEFT] < obs.rect.x < stop_lines[ObstacleDirection.RIGHT]):
                    return True
        return False

    def check_right_priority(self):
        right_priority = self.get_right_priority()
        for obs in active_obstacles[right_priority]:
            if (right_priority in [ObstacleDirection.TOP, ObstacleDirection.BOTTOM] and abs(obs.rect.y - stop_lines[right_priority]) <= 2) or \
            (right_priority in [ObstacleDirection.LEFT, ObstacleDirection.RIGHT] and abs(obs.rect.x - stop_lines[right_priority]) <= 2):
                return True
        return False

    def has_priority(self):    
        if not self.is_at_stop_position():
            return True
        if self.is_intersection_busy():
            #print(f"car {self.direction} stopped, because the intersection is busy")
            return False
        if self.check_right_priority():
            #print(f"car {self.direction} stopped, because of right priority")
            return False
        
        return True

    def auto_move(self):
        speed = self.speed
        if not self.has_priority():
            speed = 0  # Stop if no priority

        radians = math.radians(self.rotation)
        self.rect.x += speed * math.sin(radians)
        self.rect.y -= speed * math.cos(radians)

        if self.direction == ObstacleDirection.TOP:
            self.is_alive = False if self.rect.y >= stop_lines[ObstacleDirection.BOTTOM] else True
        elif self.direction == ObstacleDirection.BOTTOM:
            self.is_alive = False if self.rect.y <= stop_lines[ObstacleDirection.TOP] else True
        elif self.direction == ObstacleDirection.LEFT:
            self.is_alive = False if self.rect.x >= stop_lines[ObstacleDirection.RIGHT] else True
        else:
            self.is_alive = False if self.rect.x <= stop_lines[ObstacleDirection.LEFT] else True

def run_simulation(genomes, config):
    pygame.init()
    win = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("NEAT Car Simulation")
    map = pygame.image.load("./maps/crossing.png")

    nets = []
    cars = []
    obstacles = []
    target = pygame.Rect(660, 192, 20, 20)

    starting_positions = [(100, 190), (100, 190), (100, 190)]
    for i, (_, g) in enumerate(genomes):
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        g.fitness = 0
        cars.append(Car(map, WIDTH, HEIGHT, starting_positions[i % len(starting_positions)], car_size, config.genome_config.num_inputs))

    clock = pygame.time.Clock()
    speed_interval = 0.1
    max_speed = 2
    rotation_speed = 5
    max_generation_time = 1200
    generation_time = 0
    obstacle_timer = 0

    # Track previous distances to encourage forward progress
    previous_distances = [None] * len(cars)

    while True:
        win.blit(map, (0, 0))
        pygame.draw.rect(win, (0, 255, 0), target)
        generation_time += 1
        obstacle_timer += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)

        if obstacle_timer >= random.randint(30, 60):
            obstacle_timer = 0
            direction = random.choice(list(ObstacleDirection))
            if len(active_obstacles[direction]) < 1:
                start_pos, speed, rotation = direction.value[:3]
                new_obstacle = ObstacleCar(map, WIDTH, HEIGHT, start_pos, car_size, 0, speed, rotation, direction)
                obstacles.append(new_obstacle)
                active_obstacles[direction].append(new_obstacle)

        for obs in obstacles:
            obs.auto_move()
            obs.draw(win)
            if not obs.get_is_alive():
                active_obstacles[obs.direction].remove(obs)
                obstacles.remove(obs)

        # Network decisions
        for i, car in enumerate(cars):
            if car.get_is_alive():
                output = nets[i].activate(car.get_input_data())
                speed_control = output[0]
                rotation_control = output[1]
                if speed_control > 0:
                    car.speed = min(car.speed + speed_interval, max_speed)
                else:
                    car.speed = max(car.speed - speed_interval, -max_speed)
                if rotation_control > 0:
                    car.rotation += rotation_speed
                    car.update_rotation(rotation_speed)
                else:
                    car.rotation -= rotation_speed
                    car.update_rotation(-rotation_speed)

        remain_cars = 0
        for i, car in enumerate(cars):
            if car.get_is_alive():
                remain_cars += 1
                car.update(win, obstacles)

                # Distance-based incentive
                distance_to_target = math.hypot(target.centerx - car.rect.centerx, target.centery - car.rect.centery)
                distance_reward = (1 / (distance_to_target + 1)) * 2
                genomes[i][1].fitness += distance_reward

                # Additional reward for moving closer
                if previous_distances[i] is not None and distance_to_target < previous_distances[i]:
                    genomes[i][1].fitness += 0.5
                previous_distances[i] = distance_to_target

                # Small penalty for reversing
                if car.speed < 0:
                    genomes[i][1].fitness -= 0.1

                # Big reward for reaching target
                if car.rect.colliderect(target):
                    genomes[i][1].fitness += 50
                    car.is_alive = False

                # Penalty for heavy rotation
                if car.total_rotation > 2000:
                    genomes[i][1].fitness -= 5
                    car.is_alive = False

                # Collisions
                for obs in obstacles:
                    if car.rect.colliderect(obs.rect):
                        car.is_alive = False
            else:
                # Penalize crashing
                if not car.recieved_reward:
                    genomes[i][1].fitness -= 3
                    car.recieved_reward = True
                    print(f"Car {i} fitness: {genomes[i][1].fitness}")

        # If no cars remain or generation took too long, end
        if remain_cars == 0 or generation_time > max_generation_time:
            for i, car in enumerate(cars):
                if car.get_is_alive():
                    genomes[i][1].fitness -= 10  # penalize inactivity
            clear_obstacles()
            break

        # Draw living cars
        for car in cars:
            if car.get_is_alive():
                car.draw(win)

        pygame.display.flip()
        clock.tick(60)

def run(config_file):

    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)

    p = neat.Population(config)

    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    #p.add_reporter(neat.Checkpointer(10)) # save checkpoint after ... generations
    p.run(run_simulation, 100)  # number of generations


if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)