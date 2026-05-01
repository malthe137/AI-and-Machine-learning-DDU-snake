## Folder setup

```text
snake_game/
  snake_85x85_dqn.py          # run this file for the AI
  dqn_agent.py                # separate linked AI file
  pixil-frame-0.png           # background image
  dqn_snake_model.pth         # auto-created DQN save file
  game.log                    # auto-created run log
  requirements.txt
```

## Install

```bash
pip install -r requirements.txt
```

or:

```bash
pip install pygame torch numpy
```

## Run

```bash
python snake_85x85_dqn.py
```

## Controls

- `V` = toggle watch mode / slower visible mode
- `M` = toggle manual mode
- `SPACE` = pause
- `S` = save model now
- `Q` or `ESC` = quit and save

## Save data

The model is saved as `dqn_snake_model.pth`.
Do not delete that file unless you want the AI to restart from zero.
