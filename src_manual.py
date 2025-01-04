import pygame
from car import Car

pygame.init()
WIDTH, HEIGHT = 683, 384
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NEAT Car Simulation")
map = pygame.image.load("./maps/map2.png")

def run():
    car = Car(map, WIDTH, HEIGHT, (90, 90), 10, 6)
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

        car.update(win, [])

        car.draw(win)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    run()
