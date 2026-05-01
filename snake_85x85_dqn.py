import random
import sys
from collections import deque
from pathlib import Path

import numpy as np
import pygame

from dqn_agent import DQNSnakeAgent, turn_direction

GAME_SIZE = 85 * 7
BORDER = 5 * 7
SCOREBOARD_HEIGHT = 15 * 7
CELL_SIZE = 5 * 7
GRID_SIZE = GAME_SIZE // CELL_SIZE
WINDOW_WIDTH = GAME_SIZE + BORDER * 2
WINDOW_HEIGHT = SCOREBOARD_HEIGHT + BORDER + GAME_SIZE + BORDER
PLAYFIELD_X = BORDER
PLAYFIELD_Y = SCOREBOARD_HEIGHT + BORDER

TRAINING_FPS = 0
WATCH_FPS = 15
RENDER_EVERY_N_GAMES = 25
MAX_STEPS_WITHOUT_FOOD = 200

WHITE = (245, 245, 245)
SCORE_TEXT = (255, 255, 255)
SNAKE_COLOR = (255, 95, 25)
HEAD_COLOR = (255, 50, 25)
FOOD_COLOR = (0, 255, 0)
BORDER_COLOR = (190, 140, 255)
BACKGROUND_IMAGE = [Path("pixil-frame-0.png")]


class SnakeGameDQN:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("85x85 Snake - DQN AI")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 18, bold=True)
        self.big_font = pygame.font.SysFont("arial", 24, bold=True)
        self.background = self.load_background()
        self.manual_mode = False
        self.watch_mode = False
        self.paused = False
        self.agent = DQNSnakeAgent(state_size=self.state_size())
        self.reset()

    def load_background(self):
        for path in BACKGROUND_IMAGE:
            if path.exists():
                try:
                    return pygame.transform.scale(pygame.image.load(str(path)).convert(), (WINDOW_WIDTH, WINDOW_HEIGHT))
                except pygame.error:
                    pass
        fallback = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        fallback.fill((90, 35, 130))
        return fallback

    @staticmethod
    def state_size():
        return 4 + 3 + 3 + 4 + 24 + 3

    def reset(self):
        center = (GRID_SIZE // 2) * CELL_SIZE
        self.snake = [(center, center), (center - CELL_SIZE, center), (center - 2 * CELL_SIZE, center)]
        self.direction = (CELL_SIZE, 0)
        self.next_direction = self.direction
        self.score = 0
        self.game_over = False
        self.steps_since_food = 0
        self.start_ticks = pygame.time.get_ticks()
        self.spawn_food()

    def spawn_food(self):
        positions = [(x, y) for x in range(0, GAME_SIZE, CELL_SIZE) for y in range(0, GAME_SIZE, CELL_SIZE) if (x, y) not in self.snake]
        self.food = random.choice(positions) if positions else None

    def food_distance(self):
        if self.food is None:
            return 0
        hx, hy = self.snake[0]
        return abs(hx - self.food[0]) // CELL_SIZE + abs(hy - self.food[1]) // CELL_SIZE

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.agent.save(); pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    self.agent.save(); pygame.quit(); sys.exit()
                if event.key == pygame.K_m:
                    self.manual_mode = not self.manual_mode
                if event.key == pygame.K_v:
                    self.watch_mode = not self.watch_mode
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                if event.key == pygame.K_s:
                    self.agent.save(); print("Saved DQN model.")
                if self.manual_mode:
                    if event.key in (pygame.K_UP, pygame.K_w) and self.direction != (0, CELL_SIZE):
                        self.next_direction = (0, -CELL_SIZE)
                    elif event.key in (pygame.K_DOWN, pygame.K_s) and self.direction != (0, -CELL_SIZE):
                        self.next_direction = (0, CELL_SIZE)
                    elif event.key in (pygame.K_LEFT, pygame.K_a) and self.direction != (CELL_SIZE, 0):
                        self.next_direction = (-CELL_SIZE, 0)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d) and self.direction != (-CELL_SIZE, 0):
                        self.next_direction = (CELL_SIZE, 0)

    def cell_blocked(self, pos, snake_body=None):
        if snake_body is None:
            snake_body = self.snake
        x, y = pos
        return x < 0 or x >= GAME_SIZE or y < 0 or y >= GAME_SIZE or pos in snake_body

    def flood_fill_area(self, start, snake_body=None):
        snake_body = set(self.snake if snake_body is None else snake_body)
        if self.cell_blocked(start, snake_body):
            return 0
        q = deque([start])
        seen = {start}
        area = 0
        while q:
            x, y = q.popleft(); area += 1
            for dx, dy in ((CELL_SIZE, 0), (-CELL_SIZE, 0), (0, CELL_SIZE), (0, -CELL_SIZE)):
                nxt = (x + dx, y + dy)
                if nxt not in seen and not self.cell_blocked(nxt, snake_body):
                    seen.add(nxt); q.append(nxt)
        return area

    def direction_vision(self, vx, vy):
        hx, hy = self.snake[0]
        x, y = hx, hy
        distance = 0
        body_distance = 0
        food_seen = 0
        body = set(self.snake[1:])
        while True:
            x += vx * CELL_SIZE; y += vy * CELL_SIZE; distance += 1
            if x < 0 or x >= GAME_SIZE or y < 0 or y >= GAME_SIZE:
                wall_distance = distance / GRID_SIZE
                break
            if (x, y) in body and body_distance == 0:
                body_distance = distance
            if self.food == (x, y):
                food_seen = 1
        body_signal = 0.0 if body_distance == 0 else 1.0 / body_distance
        return wall_distance, body_signal, float(food_seen)

    def make_state(self):
        hx, hy = self.snake[0]
        dx, dy = self.direction
        left, straight, right = (dy, -dx), (dx, dy), (-dy, dx)

        def danger(move, steps=1):
            return 1.0 if self.cell_blocked((hx + move[0] * steps, hy + move[1] * steps)) else 0.0

        state = [
            1.0 if self.direction == (0, -CELL_SIZE) else 0.0,
            1.0 if self.direction == (0, CELL_SIZE) else 0.0,
            1.0 if self.direction == (-CELL_SIZE, 0) else 0.0,
            1.0 if self.direction == (CELL_SIZE, 0) else 0.0,
        ]
        for move in (left, straight, right):
            state.append(danger(move, 1))
        for move in (left, straight, right):
            state.append(danger(move, 2))
        fx, fy = self.food
        state += [float(fx < hx), float(fx > hx), float(fy < hy), float(fy > hy)]
        for vx, vy in ((0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)):
            state.extend(self.direction_vision(vx, vy))
        for move in (left, straight, right):
            area = self.flood_fill_area((hx + move[0], hy + move[1]))
            state.append(min(area / (GRID_SIZE * GRID_SIZE), 1.0))
        return np.array(state, dtype=np.float32)

    def step(self, action):
        old_distance = self.food_distance()
        safe_before = self.flood_fill_area(self.snake[0])
        self.direction = self.next_direction if self.manual_mode else turn_direction(self.direction, action)
        self.next_direction = self.direction
        hx, hy = self.snake[0]
        dx, dy = self.direction
        new_head = (hx + dx, hy + dy)
        self.steps_since_food += 1
        reward = -0.02
        done = False

        if self.cell_blocked(new_head):
            self.game_over = True
            return -100.0, True

        self.snake.insert(0, new_head)
        if new_head == self.food:
            self.score += 1
            reward += 20.0
            self.steps_since_food = 0
            self.spawn_food()
        else:
            self.snake.pop()
            new_distance = self.food_distance()
            reward += 0.5 if new_distance < old_distance else -0.5

        safe_after = self.flood_fill_area(self.snake[0])
        if safe_after < len(self.snake) + 4:
            reward -= 5.0
        else:
            reward += 0.2 * min(safe_after / max(safe_before, 1), 1.5)

        if self.steps_since_food > MAX_STEPS_WITHOUT_FOOD:
            reward -= 30.0
            self.game_over = True
            done = True
        return reward, done

    def log_game(self):
        run_time = (pygame.time.get_ticks() - self.start_ticks) / 1000
        with open("game.log", "a") as f:
            f.write(f"DQN game {self.agent.games_played + 1}, Run time: {run_time:.2f} seconds, Score: {self.score}, Best: {self.agent.best_score}, Epsilon: {self.agent.epsilon:.4f}\n")

    def update(self):
        if self.paused:
            return
        state = self.make_state()
        action = self.agent.choose_action(state) if not self.manual_mode else 0
        reward, done = self.step(action)
        next_state = self.make_state() if not done else np.zeros(self.state_size(), dtype=np.float32)
        if not self.manual_mode:
            self.agent.remember(state, action, reward, next_state, done)
            self.agent.train_step()
        if done:
            self.log_game()
            if not self.manual_mode:
                self.agent.finish_game(self.score)
            self.reset()

    def should_draw(self):
        return self.watch_mode or self.manual_mode or self.agent.games_played % RENDER_EVERY_N_GAMES == 0

    def draw(self):
        self.screen.blit(self.background, (0, 0))
        pygame.draw.rect(self.screen, BORDER_COLOR, (0, SCOREBOARD_HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT - SCOREBOARD_HEIGHT), BORDER)
        overlay = pygame.Surface((GAME_SIZE, GAME_SIZE), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, 18))
        self.screen.blit(overlay, (PLAYFIELD_X, PLAYFIELD_Y))
        info = f"Score {self.score} | Best {self.agent.best_score} | Games {self.agent.games_played} | eps {self.agent.epsilon:.3f}"
        controls = "V watch | M manual | SPACE pause | S save | Q quit"
        self.screen.blit(self.font.render(info, True, SCORE_TEXT), (4, 2))
        self.screen.blit(self.font.render(controls, True, SCORE_TEXT), (4, 24))
        if self.food:
            pygame.draw.rect(self.screen, FOOD_COLOR, pygame.Rect(PLAYFIELD_X + self.food[0], PLAYFIELD_Y + self.food[1], CELL_SIZE, CELL_SIZE))
        for i, (x, y) in enumerate(self.snake):
            pygame.draw.rect(self.screen, HEAD_COLOR if i == 0 else SNAKE_COLOR, pygame.Rect(PLAYFIELD_X + x, PLAYFIELD_Y + y, CELL_SIZE, CELL_SIZE))
        if self.paused:
            line = self.big_font.render("Paused", True, WHITE)
            self.screen.blit(line, (WINDOW_WIDTH // 2 - line.get_width() // 2, WINDOW_HEIGHT // 2))
        pygame.display.flip()

    def run(self):
        while True:
            self.handle_input()
            self.update()
            if self.should_draw():
                self.draw()
            self.clock.tick(WATCH_FPS if self.watch_mode or self.manual_mode else TRAINING_FPS)


if __name__ == "__main__":
    SnakeGameDQN().run()
