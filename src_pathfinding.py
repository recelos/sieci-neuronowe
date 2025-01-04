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

    for genome_id, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        g.fitness = 0

        cars.append(Car(map, WIDTH, HEIGHT))

    clock = pygame.time.Clock()
    speed_interval = 0.1
    max_speed = 2
    rotation_speed = 5
    max_generation_time = 1200
    generation_time = 0

    while True:
        win.blit(map, (0, 0))
        generation_time += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)

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
                car.update(win)
                genomes[i][1].fitness = car.reward()
                # Penalize for excessive rotation
                if car.total_rotation > 7000:  
                    genomes[i][1].fitness -= 5
                    car.is_alive = False
                    print(f"Car {i} is rotating too much.")
                # Penalize for very low speed
                if abs(car.speed) < 0.2: 
                    #genomes[i][1].fitness -= 1
                    #print(f"Car {i} is moving too slow.")
                    pass
                if car.speed < 0:
                    genomes[i][1].fitness -= 5
                    car.is_alive = False
                    print(f"Car {i} is reversing.")
            else:
                genomes[i][1].fitness -= 1  #penalize for crashing

        if remain_cars == 0 or generation_time > max_generation_time:
            break

        for car in cars:
            if car.get_is_alive():
                car.draw(win)

        pygame.display.flip()
        clock.tick(60) #limit 60 fps

def run(config_file):
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)
    
    p = neat.Population(config)

    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    p.add_reporter(neat.Checkpointer(10)) #save checkpoint after ... generations
    p.run(run_simulation, 100)  #number of generations

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)