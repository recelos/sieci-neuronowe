import pygame
import math

pygame.init()

WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
ROAD_COLOR = (50, 50, 50)
ROAD_LEFT = 250
ROAD_RIGHT = 550
CAR_IMG = pygame.transform.scale(pygame.image.load("car.png"), (100, int(100 * pygame.image.load("car.png").get_height() / pygame.image.load("car.png").get_width())))
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NEAT Car Simulation")

class Car:
    def __init__(self):
        self.image = CAR_IMG
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT - 50))
        self.speed = 0
        self.rotation = 0

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

        if car.check_collision():
            print("Collision with road boundary!")

        car.draw(win)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    run()
