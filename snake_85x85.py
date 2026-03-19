import random
import sys
from pathlib import Path

import pygame

# Størrelser og layout
GAME_SIZE = 85 * 7
BORDER = 5 * 7
SCOREBOARD_HEIGHT = 15 * 7
CELL_SIZE = 5 * 7  # (17x17)*7 grid inden i (85x85)*7 game

WINDOW_WIDTH = GAME_SIZE + BORDER * 2
WINDOW_HEIGHT = SCOREBOARD_HEIGHT + BORDER + GAME_SIZE + BORDER
PLAYFIELD_X = BORDER
PLAYFIELD_Y = SCOREBOARD_HEIGHT + BORDER

# fps og farver
FPS = 7
WHITE = (245, 245, 245)
BLACK = (20, 20, 20)
SCORE_TEXT = (255, 255, 255)
SNAKE_COLOR = (255, 95, 25)
HEAD_COLOR = (255, 50, 25)
FOOD_COLOR = (0, 255, 0)
BORDER_COLOR = (190, 140, 255)
GAME_OVER_BG = (50, 0, 70)

# baggrund
BACKGROUND_CANDIDATES = [
    Path("pixil-frame-0.png"),
]


class SnakeGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("85x85 Snake")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 20, bold=True)
        self.big_font = pygame.font.SysFont("arial", 24, bold=True)

        self.background = self.load_background()
        self.reset()

    def load_background(self):
        """Load the provided image and scale it to the full window size."""
        for path in BACKGROUND_CANDIDATES:
            if path.exists():
                try:
                    image = pygame.image.load(str(path)).convert()
                    return pygame.transform.scale(image, (WINDOW_WIDTH, WINDOW_HEIGHT))
                except pygame.error:
                    pass

        # Fallback in case the image can't be loaded
        fallback = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        fallback.fill((90, 35, 130))
        return fallback

    def reset(self):
        center = (GAME_SIZE // CELL_SIZE // 2) * CELL_SIZE
        self.snake = [
            (center, center),
            (center - CELL_SIZE, center),
            (center - 2 * CELL_SIZE, center),
        ]
        self.direction = (CELL_SIZE, 0)
        self.next_direction = self.direction
        self.score = 0
        self.game_over = False

        # start time for this run
        self.start_ticks = pygame.time.get_ticks()

        self.spawn_food()

    def spawn_food(self):
        positions = [
            (x, y)
            for x in range(0, GAME_SIZE, CELL_SIZE)
            for y in range(0, GAME_SIZE, CELL_SIZE)
            if (x, y) not in self.snake
        ]
        self.food = random.choice(positions)

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if self.game_over:
                    if event.key == pygame.K_r:
                        self.reset()
                    elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                        pygame.quit()
                        sys.exit()
                else:
                    if event.key in (pygame.K_UP, pygame.K_w) and self.direction != (0, CELL_SIZE):
                        self.next_direction = (0, -CELL_SIZE)
                    elif event.key in (pygame.K_DOWN, pygame.K_s) and self.direction != (0, -CELL_SIZE):
                        self.next_direction = (0, CELL_SIZE)
                    elif event.key in (pygame.K_LEFT, pygame.K_a) and self.direction != (CELL_SIZE, 0):
                        self.next_direction = (-CELL_SIZE, 0)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d) and self.direction != (-CELL_SIZE, 0):
                        self.next_direction = (CELL_SIZE, 0)

    def update(self):
        if self.game_over:
            return

        self.direction = self.next_direction
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        # Hit wall
        if not (0 <= new_head[0] < GAME_SIZE and 0 <= new_head[1] < GAME_SIZE):
            self.game_over = True

            run_time = (pygame.time.get_ticks() - self.start_ticks) / 1000
            score = self.score

            with open("game.log", "a") as f:
                f.write(f"Run time: {run_time:.2f} seconds, Score: {score}\n")

            return

        # Hit self
        if new_head in self.snake:
            self.game_over = True

            run_time = (pygame.time.get_ticks() - self.start_ticks) / 1000
            score = self.score

            with open("game.log", "a") as f:
                f.write(f"Run time: {run_time:.2f} seconds, Score: {score}\n")

            return

        self.snake.insert(0, new_head)

        if new_head == self.food:
            self.score += 1
            self.spawn_food()
        else:
            self.snake.pop()

    def draw(self):
        self.screen.blit(self.background, (0, 0))

        # Reinforce the requested layout so it is visible over the background.
        pygame.draw.rect(
            self.screen,
            BORDER_COLOR,
            (0, SCOREBOARD_HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT - SCOREBOARD_HEIGHT),
            BORDER
        )

        # Transparent-ish board overlay effect using a surface.
        board_overlay = pygame.Surface((GAME_SIZE, GAME_SIZE), pygame.SRCALPHA)
        board_overlay.fill((255, 255, 255, 18))
        self.screen.blit(board_overlay, (PLAYFIELD_X, PLAYFIELD_Y))

        # Scoreboard text
        score_text = self.font.render(f"Score: {self.score}", True, SCORE_TEXT)
        controls_text = self.font.render("Arrows/WASD", True, SCORE_TEXT)
        self.screen.blit(score_text, (4, 2))
        self.screen.blit(controls_text, (WINDOW_WIDTH - controls_text.get_width() - 4, 2))

        # Food
        food_rect = pygame.Rect(
            PLAYFIELD_X + self.food[0],
            PLAYFIELD_Y + self.food[1],
            CELL_SIZE,
            CELL_SIZE
        )
        pygame.draw.rect(self.screen, FOOD_COLOR, food_rect)

        # Snake
        for i, (x, y) in enumerate(self.snake):
            color = HEAD_COLOR if i == 0 else SNAKE_COLOR
            rect = pygame.Rect(
                PLAYFIELD_X + x,
                PLAYFIELD_Y + y,
                CELL_SIZE,
                CELL_SIZE
            )
            pygame.draw.rect(self.screen, color, rect)

        if self.game_over:
            overlay = pygame.Surface((GAME_SIZE, GAME_SIZE), pygame.SRCALPHA)
            overlay.fill((*GAME_OVER_BG, 180))
            self.screen.blit(overlay, (PLAYFIELD_X, PLAYFIELD_Y))

            line1 = self.big_font.render("Game Over", True, WHITE)
            line2 = self.font.render("R = restart", True, WHITE)
            line3 = self.font.render("Q/Esc = quit", True, WHITE)
            cx = PLAYFIELD_X + GAME_SIZE // 2
            cy = PLAYFIELD_Y + GAME_SIZE // 2
            self.screen.blit(line1, (cx - line1.get_width() // 2, cy - 30))
            self.screen.blit(line2, (cx - line2.get_width() // 2, cy))
            self.screen.blit(line3, (cx - line3.get_width() // 2, cy + 30))

        pygame.display.flip()

    def run(self):
        while True:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)


if __name__ == "__main__":
    SnakeGame().run()
    