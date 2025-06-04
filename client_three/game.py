import pygame
import sys

class Game:
    def __init__(self, singlplayer=True):
        self.singlplayer = singlplayer

pygame.init()
WIDTH, HEIGHT = 400, 300
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Мини-игра на Pygame")

clock = pygame.time.Clock()
x, y = WIDTH // 2, HEIGHT // 2
speed = 5

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        x -= speed
    if keys[pygame.K_RIGHT]:
        x += speed
    if keys[pygame.K_UP]:
        y -= speed
    if keys[pygame.K_DOWN]:
        y += speed

    screen.fill((30, 30, 30))
    pygame.draw.rect(screen, (0, 200, 0), (x, y, 40, 40))
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()