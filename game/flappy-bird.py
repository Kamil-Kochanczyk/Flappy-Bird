import pygame
import sys
import random
import tkinter as tk
from tkinter import simpledialog
from datetime import datetime
import json
import os

pygame.init()

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

FPS = 60
WIDTH, HEIGHT = 480, 640

BASE_W, BASE_H = WIDTH, 70
PIPE_W, PIPE_H = 80, HEIGHT
BIRD_W, BIRD_H = 55, 39

BIRD_X0, BIRD_Y0 = (WIDTH // 2) - (BIRD_W // 2), (HEIGHT // 2) - (BIRD_H // 2)

FLOAT_AMPLITUDE = 30
FLOAT_SPEED = 1
FLOAT_TOP_LIM = (HEIGHT // 2) - FLOAT_AMPLITUDE
FLOAT_BOTTOM_LIM = (HEIGHT // 2) + FLOAT_AMPLITUDE

GAP_W, GAP_H = PIPE_W, 152
GAP_SPEED = 3
GAP_INTERVAL = 288
GAP_Y_LIM_TOP, GAP_Y_LIM_BOTTOM = 0, HEIGHT - BASE_H - GAP_H

SCORE_X, SCORE_Y = 224, 50

GAME_WAITING = "game waiting"
GAME_RUNNING = "game running"
GAME_END = "game end"

SCALING_FACTOR = 220
V0 = -2.8 * SCALING_FACTOR
G = 10 * SCALING_FACTOR

def y(t, y0, v0):
    return y0 + v0 * t + (1 / 2) * G * t * t

def infinite_sequence():
    while True:
        yield 1
        yield 2
        yield 0

iterator = infinite_sequence()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy Bird")
pygame.display.set_icon(pygame.image.load("./game/assets/favicon.png"))

curtain = pygame.Surface((WIDTH, HEIGHT))
curtain.set_alpha(128)
curtain.fill(BLACK)

background = pygame.image.load("./game/assets/background.png")
background_x, background_y = 0, 0

base = pygame.image.load("./game/assets/base.png")
base_x, base_y = 0, HEIGHT - BASE_H

bottom_pipe_img = pygame.image.load("./game/assets/pipe.png")
top_pipe_img = pygame.transform.flip(bottom_pipe_img, False, True)
pipe_mask = pygame.mask.from_surface(pygame.Surface((PIPE_W, PIPE_H)))

bird_upflap = pygame.image.load("./game/assets/bird-upflap.png").convert_alpha()
bird_midflap = pygame.image.load("./game/assets/bird-midflap.png").convert_alpha()
bird_downflap = pygame.image.load("./game/assets/bird-downflap.png").convert_alpha()
bird_imgs = [bird_upflap, bird_midflap, bird_downflap]
current_img = 1

class Bird:
    def __init__(self):
        self.img = bird_imgs[current_img]
        self.rect = pygame.Rect(BIRD_X0, BIRD_Y0, BIRD_W, BIRD_H)
        self.float_velocity = -FLOAT_SPEED

    def reset(self):
        self.rect.x = BIRD_X0
        self.rect.y = BIRD_Y0
        self.float_velocity = -FLOAT_SPEED

    @property
    def centery(self):
        return self.rect.centery
    
    @centery.setter
    def centery(self, value):
        self.rect.centery = value

    @property
    def left(self):
        return self.rect.left

    @property
    def top(self):
        return self.rect.top

    @property
    def bottom(self):
        return self.rect.bottom

    def float(self):
        if self.top <= FLOAT_TOP_LIM or self.bottom >= FLOAT_BOTTOM_LIM:
            self.float_velocity *= -1
        self.centery += self.float_velocity

    def hits(self, pipe):
        rect_collision = self.rect.colliderect(pipe)
        rel_pos = pipe.x - self.rect.x, pipe.y - self.rect.y
        img_mask = pygame.mask.from_surface(self.img)
        pixel_overlap = img_mask.overlap(pipe_mask, rel_pos)
        return rect_collision and pixel_overlap

    def draw(self):
        screen.blit(self.img, (self.rect.x, self.rect.y))

class Gap:
    def __init__(self, x, y):
        if y >= GAP_Y_LIM_TOP and y <= GAP_Y_LIM_BOTTOM:
            self._x = x
            self._y = y
            self.floating_velocity = 0
        else:
            raise ValueError("Error - gap can't go beyond screen")

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = value

    @property
    def right(self):
        return self.x + GAP_W

    @property
    def bottom_pipe(self):
        return pygame.Rect(self.x, self.y + GAP_H, PIPE_W, PIPE_H)

    @property
    def top_pipe(self):
        return pygame.Rect(self.x, self.y - PIPE_H, PIPE_W, PIPE_H)

    def move_left(self):
        self.x -= GAP_SPEED

    def float(self):
        if self.y <= GAP_Y_LIM_TOP or self.y >= GAP_Y_LIM_BOTTOM:
            self.floating_velocity *= -1
        self.y += self.floating_velocity

    def draw(self):
        screen.blit(bottom_pipe_img, (self.x, self.y + GAP_H))
        screen.blit(top_pipe_img, (self.x, self.y - PIPE_H))

    def respawn_after_last_gap(self, last_gap_x):
        self.x = last_gap_x + GAP_INTERVAL
        self.y = random.randint(GAP_Y_LIM_TOP, GAP_Y_LIM_BOTTOM)

class RunningGaps:
    def __init__(self, gaps_num, initial_start_x):
        if gaps_num > 0:
            self.gaps = []
            for i in range(gaps_num):
                gap_x = initial_start_x + i * GAP_INTERVAL
                gap_y = random.randint(GAP_Y_LIM_TOP, GAP_Y_LIM_BOTTOM)
                self.gaps.append(Gap(gap_x, gap_y))
            self.last_gap = self.gaps[-1]
            self.gap_ahead_of_bird = 0  # index of a gap
        else:
            raise ValueError("Error - at least one gap is needed")

    def reset(self, initial_start_x):
        i = 0
        for gap in self.gaps:
            gap.x = initial_start_x + i * GAP_INTERVAL
            gap.y = random.randint(GAP_Y_LIM_TOP, GAP_Y_LIM_BOTTOM)
            i += 1
        self.last_gap = self.gaps[-1]
        self.gap_ahead_of_bird = 0

    def next_ahead_of(self):
        self.gap_ahead_of_bird = (self.gap_ahead_of_bird + 1) % len(self.gaps)

    def run(self, floating):
        for gap in self.gaps:
            if gap.right < 0:
                gap.respawn_after_last_gap(self.last_gap.x)
                self.last_gap = gap
                velocity = random.choice([-1, 0, 1])
                gap.floating_velocity = velocity
            gap.move_left()
            if floating:
                gap.float()

    def draw(self):
        for gap in self.gaps:
            gap.draw()

class Score:
    def __init__(self, x, y, font, value):
        self.x = x
        self.y = y
        self.font = font
        self.value = value

    def reset(self):
        self.value = 0

    def increment(self):
        self.value += 1

    def draw(self):
        score_render = self.font.render(str(self.value), True, WHITE)
        screen.blit(score_render, (self.x, self.y))

class Info:
    def __init__(self, x, y, font, text):
        self.x = x
        self.y = y
        self.font = font
        self.text = text

    def draw(self):
        info_render = self.font.render(self.text, True, WHITE)
        screen.blit(info_render, (self.x, self.y))

class LeaderboardEntry:
    def __init__(self, id, date, score):
        self.id = id
        self.date = date
        self.score = score

    def encode(self):
        return {"id": self.id, "date": self.date, "score": self.score}

    @staticmethod
    def decode(entry):
        return LeaderboardEntry(entry["id"], entry["date"], entry["score"])

class Leaderboard:
    def __init__(self, entries=None):
        if entries == None:
            self.entries = []
        else:
            self.entries = entries

    def add_entry(self, entry):
        self.entries.append(entry)

    def encode(self):
        return list(map(lambda x: x.encode(), self.entries))

    @staticmethod
    def decode(leaderboard):
        return Leaderboard(list(map(lambda x: LeaderboardEntry.decode(x), leaderboard)))

def get_current_time():
    return datetime.now().strftime("%d-%m-%Y %H:%M:%S")

def prompt_player():
    root = tk.Tk()
    root.withdraw()
    player_id = simpledialog.askstring("", "Enter you id:")
    return player_id

def save_to_leaderboard(leaderboard, player_id, score):
    with open("leaderboard.json", "w") as leaderboard_file:
        leaderboard_entry = LeaderboardEntry(player_id, get_current_time(), score)
        leaderboard.add_entry(leaderboard_entry)
        json.dump(leaderboard.encode(), leaderboard_file, indent=4)

leaderboard = None
best_try = None
path = "./leaderboard.json"

if os.path.exists(path):
    with open(path, "r") as leaderboard_file:
        data = json.load(leaderboard_file)
        leaderboard = Leaderboard.decode(data)
        best_try = max(leaderboard.entries, key=lambda entry: entry.score)
else:
    leaderboard = Leaderboard()

bird = Bird()

running_gaps = RunningGaps(2, 2 * WIDTH)

score_font = pygame.font.Font(None, 90)
score = Score(SCORE_X, SCORE_Y, score_font, 0)

info_font = pygame.font.Font(None, 30)

best_info = Info(200, 120, info_font, "Best: ")
if best_try != None:
    best_info.text += str(best_try.score)

info1 = Info(142, 500, info_font, "Press space to jump")
info2 = Info(60, 530, info_font, "Avoid hitting pipes, floor and ceiling")
info3 = Info(185, 250, info_font, "Game Over!")
info4 = Info(65, 300, info_font, "Space - play again, s - save, q - quit")

clock = pygame.time.Clock()

t0 = pygame.time.get_ticks()
y0 = BIRD_Y0
v0 = 0

game_state = GAME_WAITING
bird_falling = False

counter = 0
first_time = True
floating = False

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit(0)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                pygame.quit()
                sys.exit(0)
            elif event.key == pygame.K_s:
                if game_state == GAME_END and not bird_falling:
                    player_id = prompt_player()
                    if player_id:
                        save_to_leaderboard(leaderboard, player_id, score.value)
                        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
            elif event.key == pygame.K_SPACE:
                if game_state == GAME_WAITING:
                    t0 = pygame.time.get_ticks()
                    y0 = bird.centery
                    v0 = V0
                    first_time = False
                    game_state = GAME_RUNNING
                elif game_state == GAME_RUNNING:
                    t0 = pygame.time.get_ticks()
                    y0 = bird.centery
                    v0 = V0
                elif game_state == GAME_END:
                    if not bird_falling:
                        bird.reset()
                        running_gaps.reset(2 * WIDTH)
                        score.reset()
                        counter = 0
                        floating = False
                        game_state = GAME_WAITING

    if game_state == GAME_WAITING:
        bird.float()

        if base_x + BASE_W <= 0:
            base_x = 0
        base_x -= GAP_SPEED

        screen.fill(BLACK)
        screen.blit(background, (background_x, background_y))
        screen.blit(base, (base_x, base_y))
        screen.blit(base, (base_x + BASE_W, base_y))
        bird.draw()
        score.draw()

        if best_try != None:
            best_info.draw()

        if first_time:
            info1.draw()
            info2.draw()

        counter = (counter + 1) % 7

        if counter == 6:
            bird.img = bird_imgs[next(iterator)]
    elif game_state == GAME_RUNNING:
        running_gaps.run(floating)

        t = (pygame.time.get_ticks() - t0) / 1000.0
        bird.centery = y(t, y0, v0)

        gap_ahead = running_gaps.gaps[running_gaps.gap_ahead_of_bird]
        top_pipe_ahead = gap_ahead.top_pipe
        bottom_pipe_ahead = gap_ahead.bottom_pipe

        if bird.hits(top_pipe_ahead) or bird.hits(bottom_pipe_ahead):
            t0 = pygame.time.get_ticks()
            y0 = bird.centery
            v0 = 0
            bird_falling = True
            bird.img = bird_imgs[1]
            game_state = GAME_END

        if bird.top <= 0 or bird.bottom >= base_y:
            t0 = pygame.time.get_ticks()
            y0 = bird.centery
            v0 = 0
            bird_falling = True
            bird.img = bird_imgs[1]
            game_state = GAME_END

        if bird.left > gap_ahead.right:
            score.increment()
            running_gaps.next_ahead_of()
            if score.value >= 5:
                floating = True

        if base_x + BASE_W <= 0:
            base_x = 0
        base_x -= GAP_SPEED

        screen.fill(BLACK)
        screen.blit(background, (background_x, background_y))
        running_gaps.draw()
        screen.blit(base, (base_x, base_y))
        screen.blit(base, (base_x + BASE_W, base_y))
        bird.draw()
        score.draw()

        counter = (counter + 1) % 7

        if counter == 6:
            bird.img = bird_imgs[next(iterator)]
    elif game_state == GAME_END:
        if bird.bottom <= base_y:
            gap_ahead = running_gaps.gaps[running_gaps.gap_ahead_of_bird]
            bottom_pipe_ahead = gap_ahead.bottom_pipe
            t = (pygame.time.get_ticks() - t0) / 1000.0
            bird.centery = y(t, y0, v0)
            if base_x + BASE_W <= 0:
                base_x = 0
                base_x -= GAP_SPEED
        else:
            bird_falling = False

        screen.fill(BLACK)
        screen.blit(background, (background_x, background_y))
        running_gaps.draw()
        screen.blit(base, (base_x, base_y))
        screen.blit(base, (base_x + BASE_W, base_y))
        bird.draw()
        screen.blit(curtain, (0, 0))
        score.draw()
        info3.draw()
        info4.draw()

    pygame.display.flip()

    clock.tick(FPS)
