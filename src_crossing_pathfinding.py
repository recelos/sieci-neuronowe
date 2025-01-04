import os
import pygame
from car import Car, ObstacleCar
import neat
import sys
import random
import math
from enum import Enum

WIDTH, HEIGHT = 683, 384

def run_simulation(genomes, config):
    pygame.init()
    win = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("NEAT Car Simulation")
    map = pygame.image.load("./maps/crossing.png")

    nets = []
    cars = []
    obstacles = []
    target = pygame.Rect(660, 192, 20, 20)  # Adjusted target position

    # Initialize cars controlled by NEAT
    starting_positions = [(100, 190), (100, 190), (100, 190)]  # Adjusted starting positions
    for i, (genome_id, g) in enumerate(genomes):
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        g.fitness = 0

        cars.append(Car(map, WIDTH, HEIGHT, starting_positions[i % len(starting_positions)], 30, config.genome_config.num_inputs))

    class ObstacleInitialData():
        # pos_x, pos_y, speed, rotation
        LEFT = [(10, 190), 1, 90]
        RIGHT = [(660, 190), 1, 270]
        TOP = [(341, 50), 1, 180]

    obstacle_positions = [ObstacleInitialData.LEFT[0], ObstacleInitialData.TOP[0]]
    obstacle_speeds = [ObstacleInitialData.LEFT[1], ObstacleInitialData.TOP[1]]
    obstacle_rotations = [ObstacleInitialData.LEFT[2], ObstacleInitialData.TOP[2]]

    for i in range(len(obstacle_positions)):
        obstacles.append(ObstacleCar(map, WIDTH, HEIGHT, obstacle_positions[i], 30, 0, obstacle_speeds[i], obstacle_rotations[i]))

    clock = pygame.time.Clock()
    speed_interval = 0.1
    max_speed = 2
    rotation_speed = 5
    max_generation_time = 1200
    generation_time = 0

    while True:
        win.blit(map, (0, 0))
        pygame.draw.rect(win, (0, 255, 0), target)  # Draw target point
        generation_time += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)

        # Move obstacle cars automatically
        for obs in obstacles:
            obs.auto_move()
            obs.draw(win)

        for index, car in enumerate(cars):
            if car.get_is_alive():
                output = nets[index].activate(car.get_input_data())

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
                genomes[i][1].fitness = car.reward()

                # Reward minimizing the distance to the target
                distance_to_target = math.hypot(target.centerx - car.rect.centerx, target.centery - car.rect.centery)
                genomes[i][1].fitness += (1 / (distance_to_target + 1)) * 10

                # Reward reaching the target
                if car.rect.colliderect(target):
                    genomes[i][1].fitness += 50
                    car.is_alive = False
                    print(f"Car {i} reached the target!")

                # Penalize for excessive rotation
                if car.total_rotation > 7000:
                    genomes[i][1].fitness -= 5
                    car.is_alive = False
                    print(f"Car {i} is rotating too much.")

                # Penalize for reversing
                if car.speed < 0:
                    genomes[i][1].fitness -= 5
                    car.is_alive = False
                    print(f"Car {i} is reversing.")

                # Check collision with obstacles
                for obs in obstacles:
                    if car.rect.colliderect(obs.rect):
                        genomes[i][1].fitness -= 10
                        car.is_alive = False
                        print(f"Car {i} collided with obstacle.")
            else:
                genomes[i][1].fitness -= 1  # Penalize for crashing

        if remain_cars == 0 or generation_time > max_generation_time:
            break

        for car in cars:
            if car.get_is_alive():
                car.draw(win)

        pygame.display.flip()
        clock.tick(60) # limit 60 fps


def run(config_file):
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)

    p = neat.Population(config)

    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    p.add_reporter(neat.Checkpointer(10)) # save checkpoint after ... generations
    p.run(run_simulation, 100)  # number of generations


if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)
