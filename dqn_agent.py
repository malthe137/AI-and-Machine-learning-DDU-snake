"""DQN Snake agent with bigger vision, trap awareness, and persistent training."""
from __future__ import annotations

import random
from collections import deque
from pathlib import Path
from typing import Deque, Tuple

import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
except ImportError as exc:
    raise SystemExit(
        "PyTorch is required for the DQN version. Install it with:\n"
        "    pip install torch numpy pygame\n"
    ) from exc


class SnakeNet(nn.Module):
    def __init__(self, input_size: int, hidden_size: int = 256, output_size: int = 3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_size, hidden_size), nn.ReLU(),
            nn.Linear(hidden_size, hidden_size), nn.ReLU(),
            nn.Linear(hidden_size, 128), nn.ReLU(),
            nn.Linear(128, output_size),
        )

    def forward(self, x):
        return self.net(x)


class DQNSnakeAgent:
    ACTIONS = [0, 1, 2]

    def __init__(self, state_size: int, save_file: str = "dqn_snake_model.pth",
                 gamma: float = 0.95, learning_rate: float = 0.001,
                 epsilon: float = 1.0, epsilon_min: float = 0.05,
                 epsilon_decay: float = 0.9995, replay_size: int = 80000,
                 batch_size: int = 256, target_update_games: int = 20):
        self.state_size = state_size
        self.save_file = Path(save_file)
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.target_update_games = target_update_games
        self.memory: Deque[Tuple[np.ndarray, int, float, np.ndarray, bool]] = deque(maxlen=replay_size)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = SnakeNet(state_size).to(self.device)
        self.target_model = SnakeNet(state_size).to(self.device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        self.loss_fn = nn.SmoothL1Loss()

        self.games_played = 0
        self.best_score = 0
        self.total_steps = 0
        self.load()
        self.sync_target_model()

    def sync_target_model(self):
        self.target_model.load_state_dict(self.model.state_dict())
        self.target_model.eval()

    def choose_action(self, state: np.ndarray) -> int:
        if random.random() < self.epsilon:
            return random.choice(self.ACTIONS)
        with torch.no_grad():
            state_t = torch.tensor(state, dtype=torch.float32, device=self.device).unsqueeze(0)
            return int(torch.argmax(self.model(state_t), dim=1).item())

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))
        self.total_steps += 1

    def train_step(self):
        if len(self.memory) < self.batch_size:
            return None
        batch = random.sample(self.memory, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        states_t = torch.tensor(np.array(states), dtype=torch.float32, device=self.device)
        actions_t = torch.tensor(actions, dtype=torch.long, device=self.device).unsqueeze(1)
        rewards_t = torch.tensor(rewards, dtype=torch.float32, device=self.device).unsqueeze(1)
        next_states_t = torch.tensor(np.array(next_states), dtype=torch.float32, device=self.device)
        dones_t = torch.tensor(dones, dtype=torch.float32, device=self.device).unsqueeze(1)

        current_q = self.model(states_t).gather(1, actions_t)
        with torch.no_grad():
            next_q = self.target_model(next_states_t).max(1, keepdim=True)[0]
            target_q = rewards_t + (1.0 - dones_t) * self.gamma * next_q
        loss = self.loss_fn(current_q, target_q)
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=5.0)
        self.optimizer.step()
        return float(loss.item())

    def finish_game(self, score: int):
        self.games_played += 1
        self.best_score = max(self.best_score, score)
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        if self.games_played % self.target_update_games == 0:
            self.sync_target_model()
        self.save()

    def save(self):
        torch.save({
            "state_size": self.state_size,
            "model": self.model.state_dict(),
            "target_model": self.target_model.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "epsilon": self.epsilon,
            "games_played": self.games_played,
            "best_score": self.best_score,
            "total_steps": self.total_steps,
        }, self.save_file)

    def load(self):
        if not self.save_file.exists():
            return
        data = torch.load(self.save_file, map_location=self.device)
        if data.get("state_size") != self.state_size:
            print("Existing DQN save has a different state size. Starting a new model.")
            return
        self.model.load_state_dict(data["model"])
        self.target_model.load_state_dict(data.get("target_model", data["model"]))
        if "optimizer" in data:
            self.optimizer.load_state_dict(data["optimizer"])
        self.epsilon = float(data.get("epsilon", self.epsilon))
        self.games_played = int(data.get("games_played", 0))
        self.best_score = int(data.get("best_score", 0))
        self.total_steps = int(data.get("total_steps", 0))


def turn_direction(direction, action):
    dx, dy = direction
    if action == 0:
        return direction
    if action == 1:
        return (dy, -dx)
    if action == 2:
        return (-dy, dx)
    return direction
