import pygame
import sys
import random
import json
import os
import tkinter as tk
from tkinter import simpledialog
from datetime import datetime

pygame.init()

root = tk.Tk()
root.withdraw()

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

FPS = 60
WIDTH, HEIGHT = 480, 640

LEADERBOARD_PATH = "./leaderboard.json"

# Dimensions of base.png
BASE_W, BASE_H = WIDTH, 70

# Dimensions of bird-*.png
BIRD_W, BIRD_H = 55, 39

# Dimensions of pipe.png
PIPE_W, PIPE_H = 80, HEIGHT

# Dimensions of a gap between two pipes
GAP_W, GAP_H = PIPE_W, 160

# Bird constants
X0, Y0 = (WIDTH // 2) - (BIRD_W // 2), (HEIGHT // 2) - (BIRD_H // 2)
FLOAT_SPEED = 1
FLOAT_AMPLITUDE = 30
FLOAT_TOP_LIM = (HEIGHT // 2) - FLOAT_AMPLITUDE
FLOAT_BOTTOM_LIM = (HEIGHT // 2) + FLOAT_AMPLITUDE

# Gap constants
GAP_SPEED = 3
GAP_INTERVAL = 288
GAP_Y_TOP_LIM = 0
GAP_Y_BOTTOM_LIM = HEIGHT - BASE_H - GAP_H

# Game state constants
GAME_WAITING = "game waiting"
GAME_RUNNING = "game running"
GAME_END = "game end"

# Constants controlling the mechanics of the game
SCALING_FACTOR = 220          # makes the length of vectors bigger
V0 = -2.8 * SCALING_FACTOR    # velocity/force making the bird jump upwards
G = 10 * SCALING_FACTOR       # gravity

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy Bird")
pygame.display.set_icon(pygame.image.load("./assets/favicon.png"))

# Auxiliary surface - makes the screen darker when the game is over
curtain = pygame.Surface((WIDTH, HEIGHT))
curtain.set_alpha(128)
curtain.fill(BLACK)

background = pygame.image.load("./assets/background.png")
background_x, background_y = 0, 0

base = pygame.image.load("./assets/base.png")
base_x, base_y = 0, HEIGHT - BASE_H

bottom_pipe_img = pygame.image.load("./assets/pipe.png")
top_pipe_img = pygame.transform.flip(bottom_pipe_img, False, True)

# The image pipe.png isn't a perfect rectangle
# But - to make things simpler - its mask will be
pipe_mask = pygame.mask.from_surface(pygame.Surface((PIPE_W, PIPE_H)))

bird_upflap = pygame.image.load("./assets/bird-upflap.png").convert_alpha()
bird_midflap = pygame.image.load("./assets/bird-midflap.png").convert_alpha()
bird_downflap = pygame.image.load("./assets/bird-downflap.png").convert_alpha()
bird_imgs = [bird_upflap, bird_midflap, bird_downflap]

def y(t, y0, v0):
    """Returns the current y position of the center of the bird."""
    return y0 + v0 * t + (1 / 2) * G * t * t

def get_current_time():
    """Returns formatted current time, e.g. 24-12-2023 12:43:17."""
    return datetime.now().strftime("%d-%m-%Y %H:%M:%S")

def infinite_sequence():
    """1, 2, 0, 1, 2, 0, 1, 2, 0, ..."""
    while True:
        yield 1    # bird-midflap.png
        yield 2    # bird-downflap.png
        yield 0    # bird-upflap.png

# Auxiliary iterator
# Used to switch between bird images to make the bird animation effect
iterator = infinite_sequence()

class Bird:
    """Represents the main protagonist of the game."""

    def __init__(self):
        self.rect = pygame.Rect(X0, Y0, BIRD_W, BIRD_H)
        self.img = bird_imgs[1]
        self.float_velocity = -FLOAT_SPEED

    @property
    def centery(self):
        return self.rect.centery

    @centery.setter
    def centery(self, value):
        self.rect.centery = value

    @property
    def x(self):
        return self.rect.x

    @x.setter
    def x(self, value):
        self.rect.x = value

    @property
    def y(self):
        return self.rect.y

    @y.setter
    def y(self, value):
        self.rect.y = value

    @property
    def left(self):
        return self.rect.left

    @property
    def top(self):
        return self.rect.top

    @property
    def bottom(self):
        return self.rect.bottom

    def reset(self):
        self.x = X0
        self.y = Y0
        self.float_velocity = -FLOAT_SPEED

    def float(self):
        if self.top <= FLOAT_TOP_LIM or self.bottom >= FLOAT_BOTTOM_LIM:
            self.float_velocity *= -1
        self.centery += self.float_velocity

    def hits(self, pipe):
        rect_collision = self.rect.colliderect(pipe)
        rel_pos = pipe.x - self.x, pipe.y - self.y
        img_mask = pygame.mask.from_surface(self.img)
        pixel_overlap = img_mask.overlap(pipe_mask, rel_pos)
        return rect_collision and pixel_overlap

    def draw(self):
        screen.blit(self.img, (self.x, self.y))

class Gap:
    """Represents an empty rectangle between two pipes."""

    def __init__(self, x, y):
        if y >= GAP_Y_TOP_LIM and y <= GAP_Y_BOTTOM_LIM:
            self._x = x
            self._y = y
            self.vertical_velocity = random.choice([-1, 0, 1])
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

    def move_vertically(self):
        if self.y <= GAP_Y_TOP_LIM or self.y >= GAP_Y_BOTTOM_LIM:
            self.vertical_velocity *= -1
        self.y += self.vertical_velocity

    def respawn_after_last_gap(self, last_gap_x):
        self.x = last_gap_x + GAP_INTERVAL
        self.y = random.randint(GAP_Y_TOP_LIM, GAP_Y_BOTTOM_LIM)
        self.vertical_velocity = random.choice([-1, 0, 1])

    def draw(self):
        screen.blit(bottom_pipe_img, (self.x, self.y + GAP_H))
        screen.blit(top_pipe_img, (self.x, self.y - PIPE_H))

class MovingGaps:
    """Represents the list of gaps moving in cycle in the left direction."""

    def __init__(self, gaps_num, init_x):
        if gaps_num > 0:
            self.init_x = init_x
            self.gaps = []
            for i in range(gaps_num):
                gap_x = init_x + i * GAP_INTERVAL
                gap_y = random.randint(GAP_Y_TOP_LIM, GAP_Y_BOTTOM_LIM)
                self.gaps.append(Gap(gap_x, gap_y))
            self.last_gap = self.gaps[-1]
            self.gap_ahead_of_bird = 0
        else:
            raise ValueError("Error - at least one gap is needed")

    def reset(self):
        i = 0
        for gap in self.gaps:
            gap.x = self.init_x + i * GAP_INTERVAL
            gap.y = random.randint(GAP_Y_TOP_LIM, GAP_Y_BOTTOM_LIM)
            i += 1
        self.last_gap = self.gaps[-1]
        self.gap_ahead_of_bird = 0

    def next_ahead_of(self):
        self.gap_ahead_of_bird = (self.gap_ahead_of_bird + 1) % len(self.gaps)

    def move(self):
        for gap in self.gaps:
            if gap.right < 0:
                gap.respawn_after_last_gap(self.last_gap.x)
                self.last_gap = gap
            gap.move_left()
            gap.move_vertically()

    def draw(self):
        for gap in self.gaps:
            gap.draw()

class Info:
    """Represents some text displayed on screen."""

    def __init__(self, x, y, font, text):
        self.x = x
        self.y = y
        self.font = font
        self.text = text

    def draw(self):
        render = self.font.render(self.text, True, WHITE)
        screen.blit(render, (self.x, self.y))

class Score(Info):
    """Represents the current score displayed on screen."""

    def __init__(self, x, y, font, value):
        super().__init__(x, y, font, str(value))

    def get_value(self):
        return int(self.text)

    def reset(self):
        self.text = str(0)

    def increment(self):
        self.text = str(int(self.text) + 1)

class LeaderboardEntry:
    """Represents info about one game try that is/will be in leaderboard.json"""

    def __init__(self, id, date, score):
        self.id = id
        self.date = date
        self.score = score

    @staticmethod
    def to_dict(entry):
        """Returns the dictionary representation of a LeaderboardEntry object."""
        return {"id": entry.id, "date": entry.date, "score": entry.score}

    @staticmethod
    def from_dict(entry):
        """Returns a LeaderboardEntry object from its dictionary representation."""
        return LeaderboardEntry(entry["id"], entry["date"], entry["score"])

    @staticmethod
    def get_id():
        """Opens a popup window with a text field to get an id from a player."""
        id = simpledialog.askstring("", "Enter your id:")
        return id

class Leaderboard:
    """Represents the list of all game tries in leaderboard.json"""

    # self.entries is a list of LeaderboardEntry objects
    def __init__(self, entries=None):
        if entries == None:
            self.entries = []
        else:
            self.entries = entries

    def add_entry(self, entry):
        self.entries.append(entry)

    def get_best(self):
        if self.entries == []:
            return None
        else:
            return max(self.entries, key=lambda entry: entry.score)

    def print(self):
        print(json.dumps(Leaderboard.to_list(self), indent=4))

    @staticmethod
    def to_list(leaderboard):
        """Converts a Leaderboard object to its json representation."""
        return list(map(lambda x: LeaderboardEntry.to_dict(x), leaderboard.entries))

    @staticmethod
    def from_list(leaderboard):
        """Gets a Leaderboard object from its json representation."""
        return Leaderboard(list(map(lambda x: LeaderboardEntry.from_dict(x), leaderboard)))

    @staticmethod
    def save_to_json(leaderboard, path):
        """Saves the json representation of a Leaderboard object to a json file."""
        with open(path, "w") as leaderboard_json:
            json.dump(Leaderboard.to_list(leaderboard), leaderboard_json, indent=4)

    @staticmethod
    def get_from_json(path):
        """Returns a Leaderboard object based on its representation in a json file."""
        if os.path.exists(path):
            with open(path, "r") as leaderboard_json:
                json_data = json.load(leaderboard_json)
                return Leaderboard.from_list(json_data)
        else:
            return Leaderboard()

bird = Bird()

moving_gaps = MovingGaps(3, 2 * WIDTH)

info_font = pygame.font.Font(None, 30)
info1 = Info(142, 500, info_font, "Press space to jump")
info2 = Info(60, 530, info_font, "Avoid hitting pipes, floor and ceiling")
info3 = Info(185, 250, info_font, "Game Over!")
info4 = Info(65, 300, info_font, "Space - play again, s - save, q - quit")
info5 = Info(85, 350, info_font, "p - print leaderboard in console")

score_font = pygame.font.Font(None, 90)
score = Score(224, 50, score_font, 0)

leaderboard = Leaderboard.get_from_json(LEADERBOARD_PATH)

best_try = leaderboard.get_best()

best_try_txt = "Best: "

if best_try != None:
    best_try_txt += str(best_try.score)

best_try_info = Info(200, 120, info_font, best_try_txt)

# After losing the game, the bird will fall on the ground
bird_falling = False

# info1 and info2 will disappear after first game try
first_game_try = True

# We will change the bird image every 7 frames to make the animation effect
counter = 0

# Variables that will be responsible for the movement of the bird
t0 = pygame.time.get_ticks()
y0 = Y0
v0 = 0

game_state = GAME_WAITING

clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit(0)
        if event.type == pygame.KEYDOWN:

            # Player pressed q - quitting the game
            if event.key == pygame.K_q:
                pygame.quit()
                sys.exit(0)

            # Player pressed s - saving the score to the leaderboard
            if event.key == pygame.K_s:
                if game_state == GAME_END and not bird_falling:
                    id = LeaderboardEntry.get_id()
                    if id != None:
                        date = get_current_time()
                        leaderboard.add_entry(LeaderboardEntry(id, date, score.get_value()))
                        Leaderboard.save_to_json(leaderboard, LEADERBOARD_PATH)
                        best_try_info.text = "Best: " + str(leaderboard.get_best().score)
                        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))

            # Player pressed space - controlling the game
            if event.key == pygame.K_SPACE:
                if game_state == GAME_WAITING:
                    first_game_try = False
                    game_state = GAME_RUNNING
                if game_state == GAME_RUNNING:
                    t0 = pygame.time.get_ticks()
                    y0 = bird.centery
                    v0 = V0
                if game_state == GAME_END:
                    if not bird_falling:
                        bird.reset()
                        moving_gaps.reset()
                        score.reset()
                        counter = 0
                        game_state = GAME_WAITING

            # Player pressed p - displaying leaderboard in console
            if event.key == pygame.K_p:
                    print("================================================")
                    leaderboard.print()
                    print("================================================")
                    print()

    # What happens when the game is waiting for the player to start
    if game_state == GAME_WAITING:

        # Make the bird move gently up and down
        bird.float()

        # Make the animation effect by changing the bird image every 7 frames
        counter = (counter + 1) % 7
        if counter == 6:
            bird.img = bird_imgs[next(iterator)]

        # Move the base in the left direction in the same speed as gaps and pipes
        if base_x + BASE_W <= 0:
            base_x = 0
        base_x -= GAP_SPEED

        # Draw everything necessary on the screen
        screen.fill(BLACK)
        screen.blit(background, (background_x, background_y))
        screen.blit(base, (base_x, base_y))
        screen.blit(base, (base_x + BASE_W, base_y))    # draw additional base to make the smooth scrolling effect
        bird.draw()
        score.draw()
        best_try_info.draw()
        if first_game_try:
            info1.draw()
            info2.draw()

    # What happens when the player has started playing
    if game_state == GAME_RUNNING:

        # Move gaps and pipes in cycle in the left direction
        moving_gaps.move()

        # Calculate the current y position of the bird
        t = (pygame.time.get_ticks() - t0) / 1000.0
        bird.centery = y(t, y0, v0)

        # Get the obstacle that is currently in front of the bird
        gap_ahead = moving_gaps.gaps[moving_gaps.gap_ahead_of_bird]
        top_pipe_ahead = gap_ahead.top_pipe
        bottom_pipe_ahead = gap_ahead.bottom_pipe

        # Check if the player hit something...
        hit_pipe = bird.hits(top_pipe_ahead) or bird.hits(bottom_pipe_ahead)
        hit_floor = bird.bottom >= base_y
        hit_ceiling = bird.top <= 0

        # ... and if so, make the bird fall and end the current game
        if hit_pipe or hit_ceiling or hit_floor:
            t0 = pygame.time.get_ticks()
            y0 = bird.centery
            v0 = 0
            bird_falling = True
            bird.img = bird_imgs[1]
            base_x = 0
            game_state = GAME_END

        # Check if the player has passed through the gap between pipes
        if bird.left > gap_ahead.right:
            score.increment()
            moving_gaps.next_ahead_of()

        # Make the animation effect by changing the bird image every 7 frames
        counter = (counter + 1) % 7
        if counter == 6:
            bird.img = bird_imgs[next(iterator)]

        # Move the base in the left direction in the same speed as gaps and pipes
        if base_x + BASE_W <= 0:
            base_x = 0
        base_x -= GAP_SPEED

        # Draw everything necessary on the screen
        screen.fill(BLACK)
        screen.blit(background, (background_x, background_y))
        moving_gaps.draw()
        screen.blit(base, (base_x, base_y))
        screen.blit(base, (base_x + BASE_W, base_y))    # draw additional base to make the smooth scrolling effect
        bird.draw()
        score.draw()

    # What happens when the player has lost and the game is over
    if game_state == GAME_END:

        # Make the bird fall freely until it hits the ground
        if bird.bottom <= base_y:
            t = (pygame.time.get_ticks() - t0) / 1000.0
            bird.centery = y(t, y0, v0)
        else:
            bird_falling = False

        # Draw everything necessary on the screen
        screen.fill(BLACK)
        screen.blit(background, (background_x, background_y))
        moving_gaps.draw()
        screen.blit(base, (base_x, base_y))
        bird.draw()
        screen.blit(curtain, (0, 0))
        score.draw()
        info3.draw()
        info4.draw()
        info5.draw()

    pygame.display.flip()

    clock.tick(FPS)
