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

import tensorflow as tf # type: ignore
import numpy as np # type: ignore

# Window Constants
WINDOW_TITLE = "grrr"
WINDOW_SIZE = "1200x900"

#Assets
Background = ['cemetery.png', 'village.png', 'castle.png']
EnemySprites = ['gravekeeper.png', 'guard.png', 'cultLeader.png']
area = {
0: 'cemetery',
1: 'village',
2: 'castle'
}
Enemylist = {
        # ID: {Name, Health, Damage, Heal}
        0: ['GraveKeeper', 50, 5 ,5],
        1: ['Guard', 100, 10, 10],
        2: ['CultLeader', 200, 15, 15]
    }


class EnemyAI:
    def __init__(self):
        self.model = tf.keras.Sequential([ # type: ignore
            tf.keras.layers.Dense(16, activation='relu', input_shape=(3,)), # type: ignore
            tf.keras.layers.Dense(3, activation='softmax') # type: ignore
        ])

        self.model.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy'
        )

        self.history = []  # stores player actions

    def remember(self, action):
        self.history.append(action)
        if len(self.history) > 3:
            self.history.pop(0)

    def train(self):
        if len(self.history) < 3:
            return

        X = np.array([self.history[:3]])
        y = np.array([self.history[-1]])

        self.model.fit(X, y, epochs=5, verbose=0)

    def predict(self):
        if len(self.history) < 3:
            return np.random.randint(0, 3)

        X = np.array([self.history[:3]])
        prediction = self.model.predict(X, verbose=0)
        return int(np.argmax(prediction))


def enemy_decision(predicted_player_move):
    if predicted_player_move == 0:   # Player attacks
        return "parry"
    elif predicted_player_move == 1: # Player parries
        return "heal"
    else:                            # Player heals
        return "attack"

#Entities
class Character:
    def __init__(self, name, health, damage, type):
        self.name = name
        self.health = health
        self.damage = damage
        self.type = type
        self.score = 0
        self.action = None
        self.multiplier = 1.0

    def IncreaseScore(self, amount):
        self.score += amount

#Game System
class GameSystem:
    #Initialize Game
    def __init__(self, name):
        self.current_area = 0
        self.areaName = area[self.current_area]
        self.enemy = Character(Enemylist[self.current_area][0], Enemylist[self.current_area][1], 
                          Enemylist[self.current_area][2], "Enemy")
        self.player = Character(name, 100, 10, "Player")        

    #Set Area
    def setArea(self, name = None):
        self.areaImage = Background[self.current_area]
        self.enemySprite = EnemySprites[self.current_area]
        self.enemy = Character(Enemylist[self.current_area][0], Enemylist[self.current_area][1], 
                          Enemylist[self.current_area][2], "Enemy")
        if self.current_area == 0: #Change to self.current_area FOR DEBUG !!!
            self.player = Character(name, 100, 10, "Player")
        elif self.current_area == 2:
            return "WIN"

    #Check Entity Status
    def CheckStatus(self, entity):
        if entity.health > 0:
            return
        if entity.type == "Enemy":
            self.current_area += 1
            self.setArea()
        else:
            self.current_area = 0
            self.setArea()
    
    #Calculate Outcome
    def CalculateOutcome(self):
        # Player's turn
        if self.player.action == "attack":
            if self.enemy.action == "parry":
                self.player.health -= math.ceil(1.5 * self.enemy.multiplier)
                self.CheckStatus(self.player)
            else:
                self.enemy.health -= math.ceil(self.player.damage * self.player.multiplier)
                self.CheckStatus(self.enemy)
        elif self.player.action == "heal":
            self.player.health += math.ceil(self.player.damage * self.player.multiplier)
            if self.player.health > 100:
                self.player.health = 100

        # Enemy's turn
        if self.enemy.action == "attack":
            if self.player.action == "parry":
                self.enemy.health -= math.ceil(1.5 * self.player.multiplier)
                self.CheckStatus(self.enemy)
            else:
                self.player.health -= math.ceil(self.enemy.damage * self.enemy.multiplier)
                self.CheckStatus(self.player)
        elif self.enemy.action == "heal":
            self.enemy.health += math.ceil(self.enemy.damage * self.enemy.multiplier)
            if self.enemy.health > Enemylist[self.current_area][1]:
                self.enemy.health = Enemylist[self.current_area][1]

    # Minigame: Coin Flip
    def coin_flip(self, player_guess):
        flip_result = random.choice(['heads', 'tails'])
        # Player in
        if player_guess == flip_result:
            self.player.multiplier = 1.5
            self.enemy.multiplier = 0.5
            self.player.score += 1
        
        # Enemy infavored
        else:
            self.player.multiplier = 0.5
            self.enemy.multiplier = 1.5

    # Minigame: Rock Paper Scissors
    def rock_paper_scissors(self, player_choice):
        choices = ['rock', 'paper', 'scissors']
        enemy_choice = random.choice(choices)

        # Draw
        if player_choice == enemy_choice:
            self.player.multiplier = 1.0
            self.enemy.multiplier = 1.0

        # Player wins
        elif (player_choice == 'rock' and enemy_choice == 'scissors') or \
             (player_choice == 'paper' and enemy_choice == 'rock') or \
             (player_choice == 'scissors' and enemy_choice == 'paper'):
            self.player.multiplier = 1.5
            self.enemy.multiplier = 0.5
            self.player.score += 1

        # Enemy wins
        else: 
            self.player.multiplier = 0.5
            self.enemy.multiplier = 1.5
    
    # Minigame: Dice Roll
    def dice_roll(self):
        player_roll = random.randint(1, 6) #later implement animation of rolling dice player and enemy
        enemy_roll = random.randint(1, 6)

        # Determine multipliers based on rolls
        roll_multipliers = {
            1: 0.2,
            2: 0.5,
            3: 0.8,
            4: 1.2,
            5: 1.5,
            6: 2.0
        }

        self.player.multiplier = roll_multipliers[player_roll]
        self.enemy.multiplier = roll_multipliers[enemy_roll]
        if player_roll >= 4:
            self.player.score += player_roll - 3


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