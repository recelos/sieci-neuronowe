import pygame
import math

pygame.init()

WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
ROAD_COLOR = (50, 50, 50)
ROAD_LEFT = 250
ROAD_RIGHT = 550
CAR_WIDTH = 50
CAR_IMG = pygame.transform.scale(pygame.image.load("car.png"), (CAR_WIDTH, int(CAR_WIDTH * pygame.image.load("car.png").get_height() / pygame.image.load("car.png").get_width())))
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NEAT Car Simulation")

class Car:
    def __init__(self):
        self.image = CAR_IMG
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT - 50))
        self.speed = 0
        self.rotation = 0
        self.radars_count = 6
        self.radars = [0] * self.radars_count

    def move(self):
        radians = math.radians(self.rotation)
        self.rect.x += self.speed * math.sin(radians)
        self.rect.y -= self.speed * math.cos(radians)

    def draw(self, window):
        rotated_image = pygame.transform.rotate(self.image, -self.rotation)
        new_rect = rotated_image.get_rect(center=self.rect.center)
        window.blit(rotated_image, new_rect.topleft)

    def check_collision(self):
        if self.rect.left < ROAD_LEFT or self.rect.right > ROAD_RIGHT:
            return True
        return False
    
    def radar(self, angle):
        x_center, y_center = self.rect.center
        length = 0
        x1, y1 = x_center + length * math.sin(angle), y_center - length * math.cos(angle)
        while length < 500 and ROAD_LEFT < x1 < ROAD_RIGHT and 0 < y1 < HEIGHT:
            length += 1
            x1, y1 = x_center + length * math.sin(angle), y_center - length * math.cos(angle)
        pygame.draw.line(win, (0, 255, 0), (x_center, y_center), (x1, y1))
        return math.hypot(x1 - x_center, y1 - y_center)
        
    def check_radars(self):
        for i in range(self.radars_count):
            angle = math.radians(self.rotation - 90 + i * (180 // (self.radars_count - 1)))
            self.radars[i] = self.radar(angle)
        print(self.radars)

def run():
    car = Car()
    running = True
    clock = pygame.time.Clock()

    while running:
        clock.tick(60)
        win.fill(WHITE)

        pygame.draw.rect(win, ROAD_COLOR, (ROAD_LEFT, 0, ROAD_RIGHT - ROAD_LEFT, HEIGHT))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            car.speed = min(car.speed + 0.1, 5)
        elif keys[pygame.K_DOWN]:
            car.speed = max(car.speed - 0.1, -5)
        else:
            car.speed *= 0.95

        if keys[pygame.K_LEFT]:
            car.rotation -= 2
        if keys[pygame.K_RIGHT]:
            car.rotation += 2

        car.move()
        car.check_radars()
        if car.check_collision():
            print("Collision with road boundary!")

        car.draw(win)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    run()
