import pygame
import queue
import sys
import math
import time
from threading import Thread as t
from client import data_queue, command_queue

WIDTH, HEIGHT = 1000, 800
game_data_queue = queue.Queue()

class Map:
    pass

class Bullet:
    def __init__(self, x, y, angle, speed=12, color=(255, 220, 0)):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.color = color
        self.radius = 7

    def update(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

class Player:
    def __init__(self, x, y, speed=4, color=(0, 200, 0)):
        self.speed = speed
        self.color = color

        self.health = 100
        self.bullet = 20
        self.size = 50
        
        self.x = x - self.size 
        self.y = y - self.size

        self.x_mouse = WIDTH / 2
        self.y_mouse = HEIGHT / 2 

        self.space_pressed = False

    def check_pos(self, x, y):
        if x < self.size // 2 or x > WIDTH - self.size // 2:
            return False
        if y < self.size // 2 or y > HEIGHT - self.size // 2:
            return False
        return True

    def handle_mouse(self):
        pygame.mouse.set_visible(False)
        mouse = pygame.mouse.get_pos()
        self.x_mouse = mouse[0]
        self.y_mouse = mouse[1]

    def shoot(self, bullets_list: list):
        if self.bullet > 0:
            angle = math.atan2(self.y_mouse - self.y, self.x_mouse - self.x)
            bullets_list.append(Bullet(self.x, self.y, angle))
            self.bullet -= 1

    def handle_keys(self, bullets: list):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_SPACE]:
            if not self.space_pressed:
                self.shoot(bullets)
                self.space_pressed = True
        else:
            self.space_pressed = False

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

    def draw_sight(self, screen):
        dx = self.x_mouse - self.x
        dy = self.y_mouse - self.y
        angle = math.atan2(dy, dx)

        max_len = max(WIDTH, HEIGHT) * 2

        end_x = int(self.x + math.cos(angle) * max_len)
        end_y = int(self.y + math.sin(angle) * max_len)

        sight_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.line(
            sight_surface,
            (180, 180, 180, 120),
            (int(self.x), int(self.y)),
            (end_x, end_y),
            width=5
        )
        screen.blit(sight_surface, (0, 0))

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
        
        self.threads = []

        self.bullets = []
        self.player = Player(self.WIDTH / 2, 100)
        self.enemy = Player(self.WIDTH / 2, 700 - 100, color=(200, 0, 0))

        #self.__new_thread(self.update_data)

    def __new_thread(self, func, *args, **kwargs):
        thread = t(target=func, args=args, kwargs=kwargs, daemon=True)
        self.threads.append(thread)
        thread.start()

    def update_data(self):
        while True:
            try:
                data = data_queue.get_nowait()
                if data:
                    self.enemy.x = data["x"]
                    self.enemy.y = data["y"]

                    self.enemy.health = data["health"]
                    self.enemy.bullet = data["bullet"]
                    print(data)
            except queue.Empty:
                pass

    def draw_text(self, text, x, y, color=(255,255,255), size=30):
        font = pygame.font.SysFont(None, size)
        text_surface = font.render(text, True, color)
        self. screen.blit(text_surface, (x, y))

    def hit(self):
        self.enemy.health -= 10 

    def draw_bullets(self):
        for bullet in self.bullets[:]:
            bullet.update()
            bullet.draw(self.screen)

            dist = math.hypot(bullet.x - self.enemy.x, bullet.y - self.enemy.y)
            if dist < self.enemy.size // 2:
                self.bullets.remove(bullet)
                self.hit()
                continue
            if not (0 <= bullet.x <= self.WIDTH and 0 <= bullet.y <= self.HEIGHT):
                self.bullets.remove(bullet)
    
    def draw_enemy(self):
        self.enemy.draw_player(self.screen)
        self.draw_text(f"health: {self.enemy.health}", self.enemy.x  - self.enemy.size, self.enemy.y - self.enemy.size)

    def draw_self(self):
        self.player.handle_mouse()
        self.player.handle_keys(self.bullets)

        self.draw_text(f"ammo: {self.player.bullet}", self.player.x  - self.player.size, self.player.y - self.player.size - 20)
        self.draw_text(f"health: {self.player.health}", self.player.x  - self.player.size, self.player.y - self.player.size)

        self.player.draw_sight(self.screen)
        self.player.draw_player(self.screen)

    def run(self):
        try:
            while self.running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False

                self.screen.fill((30, 30, 30))

                self.update_data()
                
                if self.player.health > 0:
                    self.draw_self()
                self.draw_bullets()
                if self.enemy.health > 0:
                    self.draw_enemy()
                
                data = {
                    "x": self.player.x,
                    "y": self.player.y,
                    "health": self.player.health,
                    "bullet": self.player.bullet, 
                    "shoot": self.enemy.space_pressed
                }
                self.client.send_msg(data, True)

                pygame.display.flip()
                self.clock.tick(60)
        except Exception as e:
            print(f"Error in game: {e}")
        finally:
            self.interface.deiconify()
            pygame.quit()
            sys.exit()