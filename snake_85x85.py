import random
import sys
import heapq
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
BACKGROUND_IMAGE = [
    Path("Snake Eksamen/pixil-frame-0 (6).png"),
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
        
    #Load baggrund til samme størrelse som window.
    def load_background(self):
       
        for path in BACKGROUND_IMAGE:
            if path.exists():
                try:
                    image = pygame.image.load(str(path)).convert()
                    return pygame.transform.scale(image, (WINDOW_WIDTH, WINDOW_HEIGHT))
                except pygame.error:
                    pass

        # Fallback hvis baggrunden ik kunne loade
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
        self.ai_enabled = True
        self.current_path = []
        self.steps_taken = 0
        self.paths_found = 0

        # start time for enkelt run
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

    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def get_neighbors(self, node, obstacles):
        x, y = node
        candidates = [
            (x + CELL_SIZE, y),
            (x - CELL_SIZE, y),
            (x, y + CELL_SIZE),
            (x, y - CELL_SIZE),
        ]

        neighbors = []
        for nx, ny in candidates:
            if 0 <= nx < GAME_SIZE and 0 <= ny < GAME_SIZE:
                if (nx, ny) not in obstacles:
                    neighbors.append((nx, ny))

        return neighbors

    def reconstruct_path(self, came_from, current):
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

    def astar(self, start, goal, obstacles):
        open_set = []
        heapq.heappush(open_set, (0, start))

        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.heuristic(start, goal)}
        open_set_hash = {start}

        while open_set:
            current = heapq.heappop(open_set)[1]
            open_set_hash.remove(current)

            if current == goal:
                return self.reconstruct_path(came_from, current)

            for neighbor in self.get_neighbors(current, obstacles):
                tentative_g = g_score[current] + 1

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self.heuristic(neighbor, goal)

                    if neighbor not in open_set_hash:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
                        open_set_hash.add(neighbor)

        return None

    def path_to_direction(self, path):
        if not path or len(path) < 2:
            return self.direction

        current = path[0]
        next_cell = path[1]
        return (next_cell[0] - current[0], next_cell[1] - current[1])

    def is_opposite_direction(self, new_dir, current_dir):
        return new_dir[0] == -current_dir[0] and new_dir[1] == -current_dir[1]

    def get_ai_move(self):
        head = self.snake[0]

        if len(self.snake) > 1:
            obstacles = set(self.snake[:-1])
            obstacles.discard(head)
        else:
            obstacles = set()

        path = self.astar(head, self.food, obstacles)

        if path and len(path) >= 2:
            self.current_path = path
            self.paths_found += 1
            return self.path_to_direction(path)

        self.current_path = []
        possible_moves = [
            (CELL_SIZE, 0),
            (-CELL_SIZE, 0),
            (0, CELL_SIZE),
            (0, -CELL_SIZE),
        ]

        for move in possible_moves:
            if self.is_opposite_direction(move, self.direction):
                continue

            new_head = (head[0] + move[0], head[1] + move[1])

            if 0 <= new_head[0] < GAME_SIZE and 0 <= new_head[1] < GAME_SIZE:
                if new_head not in self.snake[:-1]:
                    return move

        return self.direction

    def end_game(self):
        self.game_over = True
        run_time = (pygame.time.get_ticks() - self.start_ticks) / 1000

        with open("game.log", "a") as f:
            f.write(
                f"AI: {self.ai_enabled}, Run time: {run_time:.2f} seconds, "
                f"Score: {self.score}, Steps: {self.steps_taken}, Paths found: {self.paths_found}\n"
            )

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not self.game_over:
                    self.ai_enabled = not self.ai_enabled
                elif self.game_over:
                    if event.key == pygame.K_r:
                        self.reset()
                    elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                        pygame.quit()
                        sys.exit()
                elif not self.ai_enabled:
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

        if self.ai_enabled:
            ai_move = self.get_ai_move()
            if not self.is_opposite_direction(ai_move, self.direction):
                self.next_direction = ai_move

        self.direction = self.next_direction
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        # Hit wall
        if not (0 <= new_head[0] < GAME_SIZE and 0 <= new_head[1] < GAME_SIZE):
            self.end_game()
            return

        # Hit self
        if new_head in self.snake[:-1] or (new_head == self.snake[-1] and new_head == self.food):
            self.end_game()
            return

        self.snake.insert(0, new_head)
        self.steps_taken += 1

        if new_head == self.food:
            self.score += 1
            self.spawn_food()
        else:
            self.snake.pop()

    def draw(self):
        self.screen.blit(self.background, (0, 0))

        # Reinforce the requested layout so it is visible over the background. (very unnessary but i like it)
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
        ai_text = self.font.render(f"AI: {'ON' if self.ai_enabled else 'OFF'}", True, SCORE_TEXT)
        controls_text = self.font.render("Space = toggle AI", True, SCORE_TEXT)
        self.screen.blit(score_text, (4, 2))
        self.screen.blit(ai_text, (140, 2))
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
    