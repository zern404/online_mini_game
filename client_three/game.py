import pygame
import sys

class Game:
    WIDTH, HEIGHT = 800, 800
    x, y = WIDTH // 2, HEIGHT // 2
    speed = 4
    def __init__(self, client, singlplayer=True):
        self.client = client

        pygame.init()
        pygame.display.set_caption("Game")

        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        self.clock = pygame.time.Clock()
        self.singlplayer = singlplayer
        self.running = True
    
    def start_singlplayer(self):
        try:
            while self.running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False

                keys = pygame.key.get_pressed()
                if keys[pygame.K_a]:
                    self.x -= self.speed
                if keys[pygame.K_d]:
                    self.x += self.speed
                if keys[pygame.K_w]:
                    self.y -= self.speed
                if keys[pygame.K_s]:
                    self.y += self.speed

                self.screen.fill((30, 30, 30))
                pygame.draw.rect(self.screen, (0, 200, 0), (self.x, self.y, 40, 40))
                pygame.display.flip()
                self.clock.tick(60)
        except Exception as e:
            print(f"Error in start game: {e}")
        finally:
            pygame.quit()
            sys.exit()

    def start_multiplayer(self):
        print("Multiplayer")