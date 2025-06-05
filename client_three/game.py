import pygame
import sys

WIDTH, HEIGHT = 1000, 800

class Player:
    def __init__(self, x, y, speed=4, color=(0, 200, 0)):
        self.speed = speed
        self.color = color

        self.health = 100
        self.bullet = 30
        self.size = 60
        
        self.x = x - self.size 
        self.y = y - self.size 

    def check_pos(self, x, y):
        if x < self.size // 2 or x > WIDTH - self.size // 2:
            return False
        if y < self.size // 2 or y > HEIGHT - self.size // 2:
            return False
        return True

    def handle_mouse(self):
        mouse = pygame.mouse.get_pos()

    def handle_keys(self):
        keys = pygame.key.get_pressed()

        if self.check_pos(self.x, self.y):
            if keys[pygame.K_a]:
                if self.check_pos(self.x - self.speed, self.y):
                    self.x -= self.speed
            if keys[pygame.K_d]:
                if self.check_pos(self.x + self.speed, self.y):
                    self.x += self.speed
            if keys[pygame.K_w]:
                if self.check_pos(self.x, self.y - self.speed):
                    self.y -= self.speed
            if keys[pygame.K_s]:
                 if self.check_pos(self.x, self.y + self.speed):
                    self.y += self.speed
        print (self.x, self.y)

    def draw_sight(self, screen):
        pass

    def draw_player(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size // 2)


class Game:
    WIDTH, HEIGHT = WIDTH, HEIGHT
    def __init__(self, client=None, interface=None, singleplayer=True):
        self.client = client
        self.interface = interface
        self.singleplayer = singleplayer

        pygame.init()
        pygame.display.set_caption("Game")
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.player = Player(self.WIDTH / 2, 100)

    def run(self):
        try:
            while self.running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False

                self.screen.fill((30, 30, 30))
                
                self.player.handle_keys()
                self.player.draw_player(self.screen)
                
                pygame.display.flip()
                self.clock.tick(60)
        except Exception as e:
            print(f"Error in game: {e}")
        finally:
            pygame.quit()
            sys.exit()

if __name__ == "__main__":
    Game().run()