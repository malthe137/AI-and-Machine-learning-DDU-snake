from hamiltonian_ai import HamiltonianAI
from snake_game import SnakeGame


if __name__ == "__main__":
    ai = HamiltonianAI(grid_width=16, grid_height=16)
    SnakeGame(
        grid_width=16,
        grid_height=16,
        controller=ai,
        title="85x85 Snake - Hamiltonian AI",
    ).run()
