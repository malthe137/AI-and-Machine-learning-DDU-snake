import random
import sys
from pathlib import Path

import pygame

CELL_SIZE = 5 * 7
GAME_SIZE = 85 * 7
BORDER = 5 * 7
SCOREBOARD_HEIGHT = 15 * 7
WINDOW_WIDTH = GAME_SIZE + BORDER * 2
WINDOW_HEIGHT = SCOREBOARD_HEIGHT + BORDER + GAME_SIZE + BORDER
FPS = 17

WHITE = (245, 245, 245)
SCORE_TEXT = (255, 255, 255)
SNAKE_COLOR = (255, 95, 25)
HEAD_COLOR = (255, 50, 25)
FOOD_COLOR = (0, 255, 0)
BORDER_COLOR = (190, 140, 255)
GAME_OVER_BG = (50, 0, 70)

BACKGROUND_IMAGE = [
    Path("pixil-frame-0.png"),
]


class SnakeGame:
    def __init__(self, grid_width=17, grid_height=17, controller=None, title="85x85 Snake"):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.controller = controller
        self.playfield_width = self.grid_width * CELL_SIZE
        self.playfield_height = self.grid_height * CELL_SIZE
        self.playfield_x = BORDER + (GAME_SIZE - self.playfield_width) // 2
        self.playfield_y = SCOREBOARD_HEIGHT + BORDER + (GAME_SIZE - self.playfield_height) // 2

        pygame.init()
        pygame.display.set_caption(title)
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 20, bold=True)
        self.big_font = pygame.font.SysFont("arial", 24, bold=True)
        self.background = self.load_background()
        self.reset()

    def load_background(self):
        for path in BACKGROUND_IMAGE:
            if path.exists():
                try:
                    image = pygame.image.load(str(path)).convert()
                    return pygame.transform.scale(image, (WINDOW_WIDTH, WINDOW_HEIGHT))
                except pygame.error:
                    pass

        fallback = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        fallback.fill((90, 35, 130))
        return fallback

    def cell_to_pixel(self, cell):
        x, y = cell
        return x * CELL_SIZE, y * CELL_SIZE

    def pixel_to_cell(self, pos):
        x, y = pos
        return x // CELL_SIZE, y // CELL_SIZE

    def reset(self):
        if self.controller:
            initial_cells = self.controller.initial_snake_cells()
        else:
            center_x = self.grid_width // 2
            center_y = self.grid_height // 2
            initial_cells = [
                (center_x, center_y),
                (center_x - 1, center_y),
                (center_x - 2, center_y),
            ]

        self.snake = [self.cell_to_pixel(cell) for cell in initial_cells]
        self.direction = (CELL_SIZE, 0)
        self.next_direction = self.direction
        self.score = 0
        self.game_over = False
        self.start_ticks = pygame.time.get_ticks()
        self.spawn_food()

    def spawn_food(self):
        snake_cells = {self.pixel_to_cell(part) for part in self.snake}
        positions = [
            (x, y)
            for x in range(self.grid_width)
            for y in range(self.grid_height)
            if (x, y) not in snake_cells
        ]

        if not positions:
            self.food = None
            self.end_run()
            return

        self.food = self.cell_to_pixel(random.choice(positions))

    def end_run(self):
        if self.game_over:
            return

        self.game_over = True
        run_time = (pygame.time.get_ticks() - self.start_ticks) / 1000
        with open("game.log", "a", encoding="utf-8") as f:
            f.write(f"Run time: {run_time:.2f} seconds, Score: {self.score}\n")

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type != pygame.KEYDOWN:
            return

        if self.game_over:
            if event.key == pygame.K_r:
                self.reset()
            elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                pygame.quit()
                sys.exit()
            return

        if self.controller:
            return

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

        if self.controller:
            dx, dy = self.controller.next_direction(self.pixel_to_cell(self.snake[0]))
            self.next_direction = (dx * CELL_SIZE, dy * CELL_SIZE)

        self.direction = self.next_direction
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)
        growing = new_head == self.food

        if not (0 <= new_head[0] < self.playfield_width and 0 <= new_head[1] < self.playfield_height):
            self.end_run()
            return

        body_to_check = self.snake if growing else self.snake[:-1]
        if new_head in body_to_check:
            self.end_run()
            return

        self.snake.insert(0, new_head)

        if growing:
            self.score += 1
            self.spawn_food()
        else:
            self.snake.pop()

    def draw(self):
        self.screen.blit(self.background, (0, 0))

        pygame.draw.rect(
            self.screen,
            BORDER_COLOR,
            (0, SCOREBOARD_HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT - SCOREBOARD_HEIGHT),
            BORDER,
        )

        board_overlay = pygame.Surface((self.playfield_width, self.playfield_height), pygame.SRCALPHA)
        board_overlay.fill((255, 255, 255, 18))
        self.screen.blit(board_overlay, (self.playfield_x, self.playfield_y))

        score_text = self.font.render(f"Score: {self.score}", True, SCORE_TEXT)
        mode_text = self.font.render("AI" if self.controller else "Manual", True, SCORE_TEXT)
        controls_label = "R = restart" if self.game_over else ("Hamilton cycle" if self.controller else "Arrows/WASD")
        controls_text = self.font.render(controls_label, True, SCORE_TEXT)

        self.screen.blit(score_text, (4, 2))
        self.screen.blit(mode_text, (4, 28))
        self.screen.blit(controls_text, (WINDOW_WIDTH - controls_text.get_width() - 4, 2))

        if self.food is not None and not self.game_over:
            food_rect = pygame.Rect(
                self.playfield_x + self.food[0],
                self.playfield_y + self.food[1],
                CELL_SIZE,
                CELL_SIZE,
            )
            pygame.draw.rect(self.screen, FOOD_COLOR, food_rect)

        for index, (x, y) in enumerate(self.snake):
            color = HEAD_COLOR if index == 0 else SNAKE_COLOR
            rect = pygame.Rect(
                self.playfield_x + x,
                self.playfield_y + y,
                CELL_SIZE,
                CELL_SIZE,
            )
            pygame.draw.rect(self.screen, color, rect)

        if self.game_over:
            overlay = pygame.Surface((self.playfield_width, self.playfield_height), pygame.SRCALPHA)
            overlay.fill((*GAME_OVER_BG, 180))
            self.screen.blit(overlay, (self.playfield_x, self.playfield_y))

            line1 = self.big_font.render("Game Over", True, WHITE)
            line2 = self.font.render("R = restart", True, WHITE)
            line3 = self.font.render("Q/Esc = quit", True, WHITE)
            cx = self.playfield_x + self.playfield_width // 2
            cy = self.playfield_y + self.playfield_height // 2
            self.screen.blit(line1, (cx - line1.get_width() // 2, cy - 35))
            self.screen.blit(line2, (cx - line2.get_width() // 2, cy))
            self.screen.blit(line3, (cx - line3.get_width() // 2, cy + 30))

        pygame.display.flip()

    def run(self):
        while True:
            for event in pygame.event.get():
                self.handle_event(event)
            self.update()
            self.draw()
            self.clock.tick(FPS)
