# KidsCanCode - Game Development with Pygame video series
# Shmup game - part 4
# Video link: https://www.youtube.com/watch?v=mOckdKp3V38
# Adding graphics
import pygame
import random
from os import path
import pickle
from xgboost import XGBClassifier
from sklearn.linear_model import LogisticRegression
import numpy as np

img_dir = path.join(path.dirname(__file__), 'img')

WIDTH = 480
HEIGHT = 600
FPS = 60
MOBS_SIZE = 8

# define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# initialize pygame and create window
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Shmup!")
clock = pygame.time.Clock()
frame_counter = 0

ai_model = pickle.load(open("ai_model.pkl", "rb"))


class Player(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.transform.scale(player_img, (50, 38))
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH / 2
        self.rect.bottom = HEIGHT - 10
        self.speedx = 0

    def dump_state(self):
        print("spaceship: {},{},{},{}".format(self.speedx, self.rect.left, self.rect.right, self.rect.centerx))

    def dump_state_vector(self):
        return [self.speedx, self.rect.left, self.rect.right, self.rect.centerx]

    def update_with_action(self, action):
        self.speedx = 0
        if action == 0:
            self.speedx = -8
        if action == 1:
            self.speedx = 8
        self.rect.x += self.speedx
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        if self.rect.left < 0:
            self.rect.left = 0

    def shoot(self):
        bullet = Bullet(self.rect.centerx, self.rect.top)
        all_sprites.add(bullet)
        bullets.add(bullet)


class Mob(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = meteor_img
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()
        self.rect.x = random.randrange(WIDTH - self.rect.width)
        self.rect.y = random.randrange(-100, -40)
        self.speedy = random.randrange(1, 8)
        self.speedx = random.randrange(-3, 3)

    def dump_state(self):
        print("mob: {},{},{},{}".format(self.rect.x, self.rect.y, self.speedx, self.speedy))

    def dump_state_vector(self):
        return [self.rect.x, self.rect.y, self.speedx, self.speedy]

    def update(self):
        self.rect.x += self.speedx
        self.rect.y += self.speedy
        if self.rect.top > HEIGHT + 10 or self.rect.left < -25 or self.rect.right > WIDTH + 20:
            self.rect.x = random.randrange(WIDTH - self.rect.width)
            self.rect.y = random.randrange(-100, -40)
            self.speedy = random.randrange(1, 8)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = bullet_img
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()
        self.rect.bottom = y
        self.rect.centerx = x
        self.speedy = -10

    def dump_state(self):
        print("bullet: {},{}".format(self.rect.centerx, self.speedy))

    def dump_state_vector(self):
        return [self.rect.centerx, self.speedy]

    def update(self):
        self.rect.y += self.speedy
        # kill if it moves off the top of the screen
        if self.rect.bottom < 0:
            self.kill()


def dump_human_readeable_state(all_sprites, pygame):
    print("NEW FRAME")

    for sprite in all_sprites.sprites():
        sprite.dump_state()

    keystate = pygame.key.get_pressed()
    if keystate[pygame.K_LEFT]:
        print("key_pressed: K_LEFT")
    elif keystate[pygame.K_RIGHT]:
        print("key_pressed: K_RIGHT")
    elif keystate[pygame.K_SPACE]:
        print("key_pressed: K_SPACE")
    else:
        print("key_pressed: NONE")


def get_game_state(mobs, player, bullets, frame_counter):
    state = []

    state.append(frame_counter)
    state.extend(player.dump_state_vector())

    for mob in mobs.sprites():
        state.extend(mob.dump_state_vector())

    # pad with empty mobs to have vector of the same size
    mob_lenght = len(mobs.sprites())
    for j in range(MOBS_SIZE - mob_lenght):
        state.extend([0, 0, 0, 0])
    return state


def dump_as_vector(mobs, player, bullets, pygame):
    state = []
    keystate = pygame.key.get_pressed()
    if keystate[pygame.K_LEFT]: # print("key_pressed: K_LEFT")
        state.append(0)
    elif keystate[pygame.K_RIGHT]: # print("key_pressed: K_RIGHT")
        state.append(1)
    elif keystate[pygame.K_SPACE]: # print("key_pressed: K_SPACE")
        state.append(2)
    else: # print("key_pressed: NONE")
        state.append(3)

    state.extend(get_game_state(mobs, player, bullets))

    print(','.join(map(str, state)))


def ai(game_state):
    input_state = np.array(game_state)
    return ai_model.predict(input_state.reshape(1, -1))
    # return random.randint(0, 3)


# Load all game graphics
background = pygame.image.load(path.join(img_dir, "starfield.png")).convert()
background_rect = background.get_rect()
player_img = pygame.image.load(path.join(img_dir, "playerShip1_orange.png")).convert()
meteor_img = pygame.image.load(path.join(img_dir, "meteorBrown_med1.png")).convert()
bullet_img = pygame.image.load(path.join(img_dir, "laserRed16.png")).convert()

all_sprites = pygame.sprite.Group()
mobs = pygame.sprite.Group()
bullets = pygame.sprite.Group()
player = Player()
all_sprites.add(player)
for i in range(MOBS_SIZE):
    m = Mob()
    all_sprites.add(m)
    mobs.add(m)

# Game loop
running = True
while running:
    # keep loop running at the right speed
    clock.tick(FPS)

    action = ai(get_game_state(mobs, player, bullets, frame_counter))

    # Process input (events)
    for event in pygame.event.get():
        # check for closing window
        if event.type == pygame.QUIT:
            running = False

    if action == 2:
        player.shoot()
    else:
        player.update_with_action(action)

    # Update
    all_sprites.update()

    # check to see if a bullet hit a mob
    hits = pygame.sprite.groupcollide(mobs, bullets, True, True)
    for hit in hits:
        m = Mob()
        all_sprites.add(m)
        mobs.add(m)

    # check to see if a mob hit the player
    hits = pygame.sprite.spritecollide(player, mobs, False)
    if hits:
        running = False

    # Draw / render
    screen.fill(BLACK)
    screen.blit(background, background_rect)
    all_sprites.draw(screen)
    # *after* drawing everything, flip the display
    pygame.display.flip()
    frame_counter += 1

pygame.quit()
