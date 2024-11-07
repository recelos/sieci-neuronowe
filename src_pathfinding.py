import os
import pygame
from car import Car
import neat
import sys

WIDTH, HEIGHT = 683, 384

def run_simulation(genomes, config):
    pygame.init()
    win = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("NEAT Car Simulation")
    map = pygame.image.load("./maps/map1.png")

    nets = []
    cars = []

    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        g.fitness = 0

        cars.append(Car(map, WIDTH, HEIGHT))

    clock = pygame.time.Clock()
    speed_interval = 0.1
    rotation_speed = 5
    max_speed = 0.5
    max_rotation = 90

    while True:
        win.blit(map, (0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)

        for index, car in enumerate(cars):
            output = nets[index].activate(car.get_input_data())

            speed_control = output[0]
            rotation_control = output[1]
            print(speed_control)
            # TODO: check if moving works 
            if speed_control > 0.5:
                print("accelerate")
                car.speed = min(car.speed + speed_interval, max_speed)
            elif speed_control < -0.5:
                car.speed = max(car.speed - speed_interval, -max_speed)
            # else:
            #     car.speed = 0
            
            if rotation_control > 0.5:
                car.rotation = min(car.rotation + rotation_speed, max_rotation)
            elif rotation_control < -0.5:
                car.rotation = max(car.rotation - rotation_speed, -max_rotation)
            print("car", index, "speed:", car.speed, "rot:", car.rotation, "pos", car.rect.center)
        remain_cars = 0
        for i, car in enumerate(cars):
            if car.get_is_alive():
                remain_cars += 1
                car.update(win)
                genomes[i][1].fitness += car.reward()
        if remain_cars == 0:
            break

        for car in cars:
            if car.get_is_alive():
                car.draw(win)

        pygame.display.flip()
        clock.tick(0)

def run(config_file):
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)
    
    p = neat.Population(config)

    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    p.add_reporter(neat.Checkpointer(5))
    p.run(run_simulation, 50)

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)
