import pygame
import math

class Car:
    def __init__(self, map, win_width, win_height, start_pos, car_size, radars_counts):
        car_sprite = pygame.image.load("./sprites/car.png")
        self.win_width, self.win_height = win_width, win_height
        CAR_IMG = pygame.transform.scale(car_sprite, (car_size, int(car_size * car_sprite.get_height() / car_sprite.get_width())))
        self.image = CAR_IMG
        self.start_pos = start_pos
        self.rect = self.image.get_rect(center=(self.start_pos[0], self.start_pos[1]))
        self.speed = 0
        self.rotation = 90
        self.radars_count = radars_counts
        self.radars = [0] * self.radars_count
        self.map = map
        self.is_alive = True
        self.distance = 0
        self.time_alive = 0
        self.total_rotation = 0  # Track total rotation
        self.recieved_reward = False

    def move(self):
        if self.rect.centerx >= self.win_width:
            self.rect.centerx = self.win_width - 1
        if self.rect.centerx <= 0:
            self.rect.centerx = 1
        if self.rect.centery <= 0:
            self.rect.centery = 1
        if self.rect.centery >= self.win_height:
            self.rect.centery = self.win_height - 1
        
        self.rotation = min(self.rotation, 90)
        radians = math.radians(self.rotation)
        self.rect.x += self.speed * math.sin(radians)
        self.rect.y -= self.speed * math.cos(radians)
        self.distance += self.speed
        self.time_alive += 1

    def draw(self, win):
        rotated_image = pygame.transform.rotate(self.image, -self.rotation)
        new_rect = rotated_image.get_rect(center=self.rect.center)
        
        pygame.draw.rect(win, (0, 0, 255), new_rect, 2)
        win.blit(rotated_image, new_rect.topleft)

    def check_collision(self):
        x, y = self.rect.center
        if x <= 0 or x >= self.win_width or y <= 0 or y >= self.win_height or self.map.get_at((int(x), int(y))) == (255, 255, 255, 255):
            self.is_alive = False
            print(f"Car at position ({x}, {y}) collided and is no longer alive.")

    def radar(self, win, angle, obstacles):
        x_center, y_center = self.rect.center
        length = 0
        x1, y1 = x_center, y_center
        if x1 <= 0 or x1 >= self.win_width or y1 <= 0 or y1 >= self.win_height:
            return 1

        while length < 100:
            x1, y1 = x_center + length * math.sin(angle), y_center - length * math.cos(angle)
            
            if not (0 <= int(x1) < self.win_width and 0 <= int(y1) < self.win_height):
                break
            
            if self.map.get_at((int(x1), int(y1))) == (255, 255, 255, 255):
                break
            
            collision = False
            for obs in obstacles:
                if obs.rect.collidepoint(x1, y1):
                    collision = True
                    break
            if collision:
                break

            length += 1
        pygame.draw.line(win, (0, 255, 0), (x_center, y_center), (x1, y1))
        pygame.draw.circle(win, (0, 255, 0), (int(x1), int(y1)), 5)
        return math.hypot(x1 - x_center, y1 - y_center)
        
    def check_radars(self, win, obstacles):
        for i in range(self.radars_count):
            angle = math.radians(self.rotation - 90 + i * (180 // (self.radars_count - 1)))
            self.radars[i] = self.radar(win, angle, obstacles)

    def reward(self):
        # Emphasize distance traveled and slight reward for continuous movement.
        # Penalize total inactivity so the car doesn't just stay alive without moving.
        reward = self.distance * 0.8
        reward += self.time_alive * 0.005  # small time-based reward
        if self.speed < 0.1:  # idle penalty
            reward -= 0.1
        return reward
    
    def get_input_data(self):
        return [radar / 50 for radar in self.radars]

    def update(self, win, obstacles):
        self.move()
        self.check_radars(win, obstacles)
        self.check_collision()

    def get_is_alive(self):
        return self.is_alive

    def update_rotation(self, rotation_change):
        self.total_rotation += abs(rotation_change)

