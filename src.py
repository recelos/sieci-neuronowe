import pygame
import math

pygame.init()

WIDTH, HEIGHT = 683, 384

CAR_WIDTH = 10
car_sprite = pygame.image.load("car.png")
CAR_IMG = pygame.transform.scale(car_sprite, (CAR_WIDTH, int(CAR_WIDTH * car_sprite.get_height() / car_sprite.get_width())))
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NEAT Car Simulation")
map = pygame.image.load("map2.png")
class Car:
    def __init__(self):
        self.image = CAR_IMG
        self.start_pos = (50, 50)
        self.rect = self.image.get_rect(center=(self.start_pos[0], self.start_pos[1]))
        self.speed = 0
        self.rotation = 0
        self.radars_count = 6
        self.radars = [0] * self.radars_count
        self.map = map
        self.is_alive = True

    def move(self):
        radians = math.radians(self.rotation)
        self.rect.x += self.speed * math.sin(radians)
        self.rect.y -= self.speed * math.cos(radians)

    def draw(self, window):
        rotated_image = pygame.transform.rotate(self.image, -self.rotation)
        new_rect = rotated_image.get_rect(center=self.rect.center)
        
        pygame.draw.rect(win, (0, 0, 255), new_rect, 2)
        window.blit(rotated_image, new_rect.topleft)

    def check_collision(self):
        if self.map.get_at((int(self.rect.centerx), int(self.rect.centery))) == (255, 255, 255, 255):
            self.is_alive = False
            return True
        return False
    
    def radar(self, angle):
        x_center, y_center = self.rect.center
        length = 0
        x1, y1 = x_center + length * math.sin(angle), y_center - length * math.cos(angle)
        while length < 500 and self.map.get_at((int(x1), int(y1))) != (255, 255, 255, 255):
            x1, y1 = x_center + length * math.sin(angle), y_center - length * math.cos(angle)
            length += 1
        pygame.draw.line(win, (0, 255, 0), (x_center, y_center), (x1, y1))
        pygame.draw.circle(win, (0, 255, 0), (int(x1), int(y1)), 5)
        return math.hypot(x1 - x_center, y1 - y_center)
        
    def check_radars(self):
        for i in range(self.radars_count):
            angle = math.radians(self.rotation - 90 + i * (180 // (self.radars_count - 1)))
            self.radars[i] = self.radar(angle)
        print(self.radars)
    
    def is_alive(self):
        return self.is_alive

def run():
    car = Car()
    running = True
    clock = pygame.time.Clock()
    speed_interval = 0.1
    max_speed = 2
    rotation_speed = 5
    while running:
        win.blit(map, (0, 0))
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            car.speed = min(car.speed + speed_interval, max_speed)
        elif keys[pygame.K_DOWN]:
            car.speed = max(car.speed - speed_interval, -max_speed)
        else:
            car.speed = 0

        if keys[pygame.K_LEFT] and car.speed != 0:
            car.rotation -= rotation_speed
        if keys[pygame.K_RIGHT] and car.speed != 0:
            car.rotation += rotation_speed

        car.move()
        car.check_radars()
        if car.check_collision():
            print("Collision with road boundary!")

        car.draw(win)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    run()
