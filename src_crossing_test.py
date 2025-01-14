import os
import pygame
from car import Car
import neat
import sys
import random
import math
from enum import Enum
import pickle

WIDTH, HEIGHT = 683, 384
car_size = 30

obstacles_speed = 1.0
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
            if (right_priority in [ObstacleDirection.TOP, ObstacleDirection.BOTTOM] and
                abs(obs.rect.y - stop_lines[right_priority]) <= 2) or \
               (right_priority in [ObstacleDirection.LEFT, ObstacleDirection.RIGHT] and
                abs(obs.rect.x - stop_lines[right_priority]) <= 2):
                return True
        return False

    def has_priority(self):
        if not self.is_at_stop_position():
            return True
        if self.is_intersection_busy():
            return False
        if self.check_right_priority():
            return False
        return True

    def auto_move(self):
        speed = self.speed
        if not self.has_priority():
            speed = 0
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

def run_game(config_file):
    pygame.init()
    win = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("NEAT Car - Pretrained Model")
    map_img = pygame.image.load("./maps/crossing.png")

    # Wczytaj konfigurację
    config = neat.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_file
    )

    # Wczytaj wytrenowany genom i stwórz sieć
    with open("220.pkl", "rb") as f:
        winner = pickle.load(f)
    winner_net = neat.nn.FeedForwardNetwork.create(winner, config)

    # Tworzymy kilka samochodów, wszystkie korzystające z tej samej sieci
    cars = []
    starting_positions = [(100, 220), (100, 220), (100, 220)]
    for i in range(len(starting_positions)):
        car = Car(map_img, WIDTH, HEIGHT, starting_positions[i], car_size, config.genome_config.num_inputs)
        cars.append(car)

    obstacles = []
    clock = pygame.time.Clock()

    # Podstawowe parametry ruchu
    speed_interval = 0.1
    max_speed = 1.5
    rotation_speed = 3

    # Pętla główna
    running = True
    generation_time = 0
    max_generation_time = 2200
    obstacle_timer = 0

    target = pygame.Rect(360, 0, 10, 10)
    pre_target = pygame.Rect(target.x, target.y + 130, target.width, target.height)
    penalty_area = pygame.Rect(0, 0, 2, 2)

    while running:
        win.blit(map_img, (0, 0))
        pygame.draw.rect(win, (0, 255, 0), target)
        pygame.draw.rect(win, (255, 255, 0), pre_target)
        pygame.draw.rect(win, (255, 0, 0), penalty_area, 2)
        generation_time += 1
        obstacle_timer += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Losowe generowanie samochodów przeszkód
        if obstacle_timer >= random.randint(5, 15):
            obstacle_timer = 0
            direction = random.choice(list(ObstacleDirection))
            if len(active_obstacles[direction]) < 1:
                start_pos, obs_speed, obs_rotation = direction.value[:3]
                new_obstacle = ObstacleCar(map_img, WIDTH, HEIGHT, start_pos, car_size, 0, obs_speed, obs_rotation, direction)
                obstacles.append(new_obstacle)
                active_obstacles[direction].append(new_obstacle)

        # Obsługa ruchu i rysowania przeszkód
        for obs in obstacles:
            obs.auto_move()
            obs.draw(win)
            if not obs.get_is_alive():
                active_obstacles[obs.direction].remove(obs)
                obstacles.remove(obs)

        # Decyzje sieci dla każdego samochodu
        for car in cars:
            if car.get_is_alive():
                output = winner_net.activate(car.get_input_data())
                speed_control = output[0]
                rotation_control = output[1]

                if speed_control > 0:
                    car.speed = min(car.speed + speed_interval, max_speed)
                else:
                    car.speed = max(car.speed - speed_interval, -max_speed)

                if rotation_control > 0:
                    car.rotation += rotation_speed
                    car.update_rotation(rotation_speed)
                elif rotation_control < 0:
                    car.rotation -= rotation_speed
                    car.update_rotation(-rotation_speed)
                else:
                    car.rotation -= rotation_speed
                    car.update_rotation(-rotation_speed)

        # Aktualizacja i sprawdzanie stanu samochodów
        remain_cars = 0
        for car in cars:
            if car.get_is_alive():
                remain_cars += 1
                car.update(win, obstacles)

                # Sprawdzenie kolizji z celem
                if car.rect.colliderect(target):
                    car.is_alive = False
                    print("Car reached target")

                # Kolizje z obszarem kary
                if car.rect.colliderect(penalty_area):
                    pass  # można tutaj dodać logikę

                # Kolizje z przeszkodami
                for obs in obstacles:
                    if car.rect.colliderect(obs.rect):
                        car.is_alive = False

        if remain_cars == 0 or generation_time > max_generation_time:
            print("Koniec symulacji – wszystkie auta wyłączone lub przekroczono czas.")
            clear_obstacles()
            running = False

        # Rysowanie żywych samochodów
        for car in cars:
            if car.get_is_alive():
                car.draw(win)

        pygame.display.flip()
        clock.tick(60)

def run(config_file):
    run_game(config_file)

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    for i in range(5):
        run(config_path)