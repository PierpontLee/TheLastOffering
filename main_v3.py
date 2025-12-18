"""
===LOGIC===
Player Has 3 actions:
0 - Attack  = Deal damage 1.0x to Enemy
1 - Parry = Fully block next Enemy attack and counter with 1.5x damage
2 - Heal = Restore health based on stat
Enemy Uses AI to predict Player's next move based on the previous actions

There are 3 areas:

index - Area name - Minigame - Enemy

0 - Cemetery - Coin Flip - Gravekeeper
1 - Village: Enemy - Rock Paper Scissors - Guard
2 - Castle: Enemy - Dice Roll - Cult Leader

On each area player fight enemy, to do the action player must play a minigame to succeed the action.
Coin flip - Guess heads or tails
Rock Paper Scissors - Play RPS against enemy
Dice Roll - The higher the rolls, the better action goes (1 = 0.2x, 2 = 0.5x, 3 = 0.8x, 4 = 1.2, 5 = 1.5x, 6 = 2x)

To progress, player must defeat enemy in each area.
===ENDLOGIC===

===UI===
Section	Coordinates (Approximate)	Grid Position	Dimensions (in pixels)
1st Part	(0, 0) to (900, 600)	Row 0, Column 0	900 wide, 600 high
2nd Part	(0, 600) to (900, 900)	Row 1, Column 0	900 wide, 300 high
3rd Part	(900, 0) to (1200, 900)	Rows 0 & 1, Column 1	300 wide, 900 high

1st Part: Main Game Display
- Background Image: Covers entire section
===ENDUI===


"""
import tkinter as tk
from PIL import Image, ImageTk
import random
import math
import numpy as np
import tensorflow as tf

WINDOW_TITLE = "The Last Offering"
WINDOW_SIZE = "1600x1200"

# --- Enemy AI Class ---
class EnemyAI:
    def __init__(self):
        self.model = tf.keras.Sequential([
            tf.keras.layers.Dense(16, activation='relu', input_shape=(3,)),
            tf.keras.layers.Dense(3, activation='softmax')
        ])
        self.model.compile(optimizer='adam', loss='sparse_categorical_crossentropy')
        self.history = [0, 1, 2] # Initial dummy history to prevent empty arrays

    def remember(self, action):
        self.history.append(action)
        if len(self.history) > 3:
            self.history.pop(0)

    def train(self):
        if len(self.history) >= 3:
            X = np.array([self.history[:3]])
            y = np.array([self.history[-1]])
            self.model.fit(X, y, epochs=2, verbose=0)

    def predict(self):
        X = np.array([self.history[-3:]]) # Use last 3 moves
        prediction = self.model.predict(X, verbose=0)
        return int(np.argmax(prediction))

# --- Character Class ---
class Character:
    def __init__(self, name, health, damage, type):
        self.name = name
        self.max_health = health
        self.health = health
        self.damage = damage
        self.type = type
        self.action = None
        self.multiplier = 1.0

# --- Integrated Game System ---
class GameSystem:
    def __init__(self, player_name):
        self.current_area = 0
        self.player = Character(player_name, 100, 10, "Player")
        self.ai = EnemyAI()
        self.minigame_result = None # 'win', 'lose', 'draw', or dice value
        self.setArea()

    def setArea(self):
        if self.current_area > 2: return "GAME_WIN"
        
        enemy_data = [
            ['GraveKeeper', 50, 5],
            ['Guard', 100, 10],
            ['CultLeader', 200, 15]
        ]
        data = enemy_data[self.current_area]
        self.enemy = Character(data[0], data[1], data[2], "Enemy")

    def get_enemy_move(self):
        # 1. AI predicts player
        predicted_move = self.ai.predict()
        # 2. Decide counter
        if predicted_move == 0: self.enemy.action = "parry"
        elif predicted_move == 1: self.enemy.action = "heal"
        else: self.enemy.action = "attack"
        return self.enemy.action

    def play_turn(self, player_action_idx, minigame_input=None):
        # Map: 0: attack, 1: parry, 2: heal
        actions = ["attack", "parry", "heal"]
        self.player.action = actions[player_action_idx]
        
        # Enemy decides and Player move is remembered
        self.get_enemy_move()
        self.ai.remember(player_action_idx)
        self.ai.train()

        # Resolve Minigame based on area
        if self.current_area == 0: self.resolve_coin(minigame_input)
        elif self.current_area == 1: self.resolve_rps(minigame_input)
        elif self.current_area == 2: self.resolve_dice()

        self.CalculateOutcome()

    # --- Minigame Logic ---
    def resolve_coin(self, guess):
        result = random.choice(['heads', 'tails'])
        self.minigame_result = 'win' if guess == result else 'lose'

    def resolve_rps(self, guess):
        enemy_choice = random.choice(['rock', 'paper', 'scissors'])
        if guess == enemy_choice: self.minigame_result = 'draw'
        elif (guess == 'rock' and enemy_choice == 'scissors') or \
             (guess == 'paper' and enemy_choice == 'rock') or \
             (guess == 'scissors' and enemy_choice == 'paper'):
            self.minigame_result = 'win'
        else: self.minigame_result = 'lose'

    def resolve_dice(self):
        self.minigame_result = random.randint(1, 6)

    # --- REFINED OUTCOME CALCULATION ---
    def CalculateOutcome(self):
        p = self.player
        e = self.enemy
        res = self.minigame_result

        # --- 1. HANDLE PARRY REFINEMENT ---
        if p.action == "parry":
            if e.action == "attack":
                # Area 0: Coin Flip
                if self.current_area == 0:
                    if res == 'lose': p.health -= e.damage # Parry Failed
                    else: e.health -= math.ceil(p.damage * 1.5) # Successful Parry
                
                # Area 1: RPS
                elif self.current_area == 1:
                    if res == 'lose': p.health -= math.ceil(e.damage * 1.5)
                    elif res == 'draw': pass # Blocked, no damage
                    else: e.health -= math.ceil(p.damage * 1.5) # Counter
                
                # Area 2: Dice
                elif self.current_area == 2:
                    if res == 1: p.health -= (e.damage * 2)
                    elif res == 2: p.health -= math.ceil(e.damage * 1.5)
                    elif res in [3, 4]: e.health -= p.damage # Normal counter
                    elif res == 5: e.health -= math.ceil(p.damage * 1.5)
                    elif res == 6: e.health -= (p.damage * 2)
            else:
                pass # Enemy didn't attack, parry does nothing

        # --- 2. HANDLE ATTACK / HEAL ---
        else:
            # Simple multiplier logic for standard actions
            mult = 1.5 if res == 'win' or (isinstance(res, int) and res >= 4) else 1.0
            
            if p.action == "attack":
                if e.action == "parry": p.health -= math.ceil(e.damage * 1.5)
                else: e.health -= math.ceil(p.damage * mult)
            
            if p.action == "heal":
                p.health += math.ceil(10 * mult)
                if p.health > p.max_health: p.health = p.max_health

        # --- 3. ENEMY NON-PARRY ACTIONS ---
        if e.action == "attack" and p.action != "parry":
            p.health -= e.damage
        elif e.action == "heal":
            e.health += 10

        # Check for deaths
        self.check_progression()

    def check_progression(self):
        if self.enemy.health <= 0:
            self.current_area += 1
            self.setArea()
        elif self.player.health <= 0:
            print("Game Over")


class GameUI:
    def __init__(self, root, game_system):
        self.root = root
        self.game_system = game_system
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)

        # Layout frames
        self.main_frame = tk.Frame(root,width=900, height=600)
        self.main_frame.grid(row=0, column=0)

        self.action_frame = tk.Frame(root, width=900, height=300)
        self.action_frame.grid(row=1, column=0)

        self.miniGame_frame = tk.Frame(root, width=300, height=00)
        self.miniGame_frame.grid(row=0, column=1, rowspan=2)

        # Placeholder for further UI elements


def main():
    #idk what to put here yet
    pass