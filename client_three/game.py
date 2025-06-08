import pygame
import queue
import random
import math
import time
from threading import Thread as t
from client import data_queue, game_command_queue

WIDTH, HEIGHT = 1000, 800

headshot_music_path = "assets/sounds/headshot.mp3"
invited_music_path = "assets/sounds/invited.mp3"

def play_music(music_path):
    pygame.mixer.music.load(music_path) 
    pygame.mixer.music.play()  

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

        self.just_shot = False
        self.last_shot_angle = None

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
            self.just_shot = True
            self.last_shot_angle = angle

    def handle_keys(self, bullets: list):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_SPACE]:
            if not self.space_pressed:
                self.space_pressed = True
                self.shoot(bullets)
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
    def __init__(self, login, enemy_login, client=None, interface=None, singleplayer=True):
        self.client = client
        self.interface = interface
        self.singleplayer = singleplayer

        pygame.mixer.init()
        pygame.init()
        pygame.display.set_caption("Game")
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        self.clock = pygame.time.Clock()

        self.running = True
        self.end_game = False

        self.login = login
        self.enemy_login = enemy_login

        self.threads = []
        self.last_data = None

        self.bullets = []
        self.enemy_bullets = []

        self.damage_bullet = 10

        self.player = Player(random.randint(100, self.WIDTH - 100), random.randint(100, self.HEIGHT - 100))
        self.enemy = Player(self.WIDTH / 2, self.HEIGHT / 2, color=(200, 0, 0))

        self.enemy_target_x = self.enemy.x
        self.enemy_target_y = self.enemy.y

    def __kill_threads(self):
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1)  
        self.threads.clear()

    def __new_thread(self, func, *args, **kwargs):
        thread = t(target=func, args=args, kwargs=kwargs, daemon=True)
        self.threads.append(thread)
        thread.start()
    
    def handle_stop(self):
        while self.running:
            try:
                stop = game_command_queue.get(timeout=1)
                if "room closed" in stop:
                    if self.running:
                        self.stop_game()
                        break
            except queue.Empty:
                pass

    def send_game_data(self):
        while self.running:
            if self.last_data is not None:
                try:
                    self.client.send_msg(self.last_data, True)
                except Exception as e:
                    print(f"Send data error: {e}")
            time.sleep(1/60) 

    def update_data(self):
        while self.running:
            try:
                data = data_queue.get_nowait()
                if data:
                    self.enemy_target_x = data["x"]
                    self.enemy_target_y = data["y"]
                    self.player.health = data["health"]

                    shoot_event = data.get("shoot_event", False)
                    if shoot_event:
                        angle = data.get("shoot_angle", 0)
                        self.enemy_bullets.append(Bullet(self.enemy.x, self.enemy.y, angle, color=(255,0,0)))
            except queue.Empty:
                pass

    def draw_text(self, text, x, y, color=(255,255,255), size=30):
        font = pygame.font.SysFont(None, size)
        text_surface = font.render(text, True, color)
        self. screen.blit(text_surface, (x, y))

    def hit_yourself(self):
        self.player.health -= self.damage_bullet

    def hit(self):
        play_music(headshot_music_path)
        self.enemy.health -= self.damage_bullet

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

        for bullet in self.enemy_bullets[:]:
            bullet.update()
            bullet.draw(self.screen)
            dist = math.hypot(bullet.x - self.player.x, bullet.y - self.player.y)
            if dist < self.player.size // 2:
                self.enemy_bullets.remove(bullet)
                self.hit_yourself()
                continue
            if not (0 <= bullet.x <= self.WIDTH and 0 <= bullet.y <= self.HEIGHT):
                self.enemy_bullets.remove(bullet)
    
    def draw_enemy(self):
        lerp = 0.2
        self.enemy.x += (self.enemy_target_x - self.enemy.x) * lerp
        self.enemy.y += (self.enemy_target_y - self.enemy.y) * lerp
        self.enemy.draw_player(self.screen)
        self.draw_text(f"|{self.enemy_login}|", self.enemy.x  - self.enemy.size, self.enemy.y - self.enemy.size - 20, color=(255, 0, 255))
        self.draw_text(f"health: {self.enemy.health}", self.enemy.x  - self.enemy.size, self.enemy.y - self.enemy.size)

    def stop_game(self):
        print("stop")
        pygame.quit()
        self.running = False
        self.interface.deiconify()
        self.interface.menu_lable.configure(text="Menu")

    def draw_self(self):
        self.player.handle_mouse()
        self.player.handle_keys(self.bullets)

        self.draw_text(f"|{self.login}|", self.player.x  - self.player.size, self.player.y - self.player.size - 40, color=(255, 0, 255))
        self.draw_text(f"ammo: {self.player.bullet}", self.player.x  - self.player.size, self.player.y - self.player.size - 20)
        self.draw_text(f"health: {self.player.health}", self.player.x  - self.player.size, self.player.y - self.player.size)

        self.player.draw_sight(self.screen)
        self.player.draw_player(self.screen)

    def generate_last_data(self):
        self.last_data = {
                "x": self.player.x,
                "y": self.player.y,
                "health": self.enemy.health,
                "bullet": self.player.bullet,
                "shoot_event": self.player.just_shot, 
                "shoot_angle": self.player.last_shot_angle 
            }

    def run(self):
        try:
            self.__new_thread(self.update_data)
            self.__new_thread(self.send_game_data)
            self.__new_thread(self.handle_stop)
            play_music(invited_music_path)
            while self.running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False

                self.screen.fill((30, 30, 30))
                
                if self.player.health > 0:
                    self.draw_self()
                else:
                    self.draw_text("You lost :(", WIDTH / 2, HEIGHT / 2, size=100)
                    self.end_game = True

                self.draw_bullets()

                if self.enemy.health > 0:
                    self.draw_enemy()
                else:
                    self.draw_text("You win !", WIDTH / 2, HEIGHT / 2, size=100)
                    self.end_game = True

                self.generate_last_data()
                self.player.just_shot = False
                
                pygame.display.flip()
                self.clock.tick(60)

                if self.end_game:
                    time.sleep(2)
                    self.stop_game()
                    break
        except Exception as e:
            print(f"Error in game: {e}")
        finally:
            self.__new_thread(self.client.send_msg, "remove room")
            self.stop_game()