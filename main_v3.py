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
from pathlib import Path
import logging
import numpy as np
import tensorflow as tf

# --- CONFIG ---
WINDOW_TITLE = "The Last Offering"
DEBUG = True

logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

script_parent = Path(__file__).parent.absolute()
ASSET_PATH = script_parent / "Assets"

# --- 1. ENEMY AI ---
class EnemyAI:
    def __init__(self):
        self.model = tf.keras.Sequential([ # type: ignore
            tf.keras.layers.Dense(16, activation="relu", input_shape=(3,)), # type: ignore
            tf.kera s.layers.Dense(3, activation="softmax") # type: ignore
        ])
        self.model.compile(
            optimizer="adam",
            loss="sparse_categorical_crossentropy"
        )
        self.history = [0, 1, 2]  # seed history

    def train(self, last_player_action: int):
        X = np.array([self.history[-3:]])
        y = np.array([last_player_action])
        logger.debug(f"AI train X={X} y={y}")
        self.model.fit(X, y, epochs=2, verbose=0)

    def predict(self) -> int:
        X = np.array([self.history[-3:]])
        pred = self.model.predict(X, verbose=0)
        action = int(np.argmax(pred))
        logger.debug(f"AI predict {action} from {pred}")
        return action

# --- 2. GAME LOGIC ---
class Character:
    def __init__(self, name, health, damage):
        self.name = name
        self.max_health = health
        self.health = health
        self.damage = damage

class GameSystem:
    def __init__(self, player_name):
        self.current_area = 0
        self.player = Character(player_name, 100, 15)
        self.ai = EnemyAI()

        self.area_data = [
            {
                "name": "Cemetery",
                "bg": "Catacomb.png",
                "e_name": "GraveKeeper",
                "hp": 50,
                "dmg": 10,
                "minigame": "Coin Flip",
                "sprites": {
                    "idle": "GravekeeperIdle.png",
                    "atk": "GravekeeperAttack.png",
                    "pry": "GravekeeperShield.png",
                    "hel": "GravekeeperHeal.png",
                    "dmg": "GravekeeperDamaged.png"
                }
            },
            {
                "name": "Village",
                "bg": "Village.png",
                "e_name": "Guard",
                "hp": 100,
                "dmg": 15,
                "minigame": "RPS",
                "sprites": {
                    "idle": "GuardIdle.png",
                    "atk": "GuardAttack.png",
                    "pry": "GuardParry.png",
                    "hel": "GuardHeal.png",
                    "dmg": "GuardDamaged.png"
                }
            },
            {
                "name": "Castle",
                "bg": "Castle.png",
                "e_name": "Cult Leader",
                "hp": 200,
                "dmg": 20,
                "minigame": "Dice",
                "sprites": {
                    "idle": "CultLeaderIdle.png",
                    "atk": "CultLeaderAttack.png",
                    "pry": "CultLeaderParry.png",
                    "hel": "CultLeaderHeal.png",
                    "dmg": "CultLeaderDamaged.png"
                }
            }
        ]
        self.set_area()

    def set_area(self):
        d = self.area_data[self.current_area]
        self.enemy = Character(d["e_name"], d["hp"], d["dmg"])
        logger.debug(f"Loaded area {d['name']}")

    def calculate_multiplier(self, choice):
        area = self.area_data[self.current_area]

        if area["minigame"] == "Coin Flip":
            result = random.choice(["Heads", "Tails"])
            mult = 1.0 if choice == result else 0.0
            return mult, result

        if area["minigame"] == "RPS":
            enemy = random.choice(["Rock", "Paper", "Scissors"])
            beats = {"Rock": "Scissors", "Paper": "Rock", "Scissors": "Paper"}
            if choice == enemy:
                return 0.5, enemy
            if beats.get(choice) == enemy:
                return 1.0, enemy
            return 0.0, enemy

        if area["minigame"] == "Dice":
            roll = random.randint(1, 6)
            mults = {1:0.2, 2:0.5, 3:0.8, 4:1.2, 5:1.5, 6:2.0}
            return mults[roll], roll

        return 0.0, None

# --- 3. GUI ---
class GameUI:
    def __init__(self, root, game):
        self.root = root
        self.game = game
        self.images = {}
        self.action_buttons = []

        root.geometry("1200x900")
        root.title(WINDOW_TITLE)

        self.canvas = tk.Canvas(root, width=900, height=600, bg="black")
        self.canvas.grid(row=0, column=0)

        self.side_panel = tk.Frame(root, width=300, bg="#2c2c2c")
        self.side_panel.grid(row=0, column=1, rowspan=2, sticky="nsew")

        self.action_panel = tk.Frame(root, height=300, bg="#1a1a1a")
        self.action_panel.grid(row=1, column=0)

        self.bg_id = self.canvas.create_image(0, 0, anchor="nw")
        self.enemy_id = self.canvas.create_image(650, 350)
        self.player_id = self.canvas.create_image(200, 400)

        self.p_bar = self.canvas.create_rectangle(50, 50, 250, 70, fill="green")
        self.e_bar = self.canvas.create_rectangle(650, 50, 850, 70, fill="red")

        self.log = tk.Label(
            self.side_panel,
            text="BATTLE START",
            fg="white",
            bg="#2c2c2c",
            font=("Arial", 14, "bold"),
            wraplength=260
        )
        self.log.pack(pady=40)

        self.mini_frame = tk.Frame(self.side_panel, bg="#2c2c2c")
        self.mini_frame.pack()

        self.load_assets()
        self.setup_buttons()
        self.refresh_ui()

    def load_image(self, path, size):
        if path.exists():
            img = Image.open(path).resize(size)
            return ImageTk.PhotoImage(img)
        return None

    def load_assets(self):
        for k, f in [
            ("idle","MCIdle.png"),
            ("atk","MCAttack.png"),
            ("pry","MCParry.png"),
            ("hel","MCHeal.png"),
            ("dmg","MCDamaged.png")
        ]:
            self.images[f"p_{k}"] = self.load_image(ASSET_PATH / f, (300, 400))

    def setup_buttons(self):
        for i, name in enumerate(["Attack", "Parry", "Heal"]):
            btn = tk.Button(
                self.action_panel,
                text=name,
                font=("Arial", 16, "bold"),
                width=12,
                command=lambda v=i: self.start_minigame(v)
            )
            btn.pack(side="left", padx=20, pady=50)
            self.action_buttons.append(btn)

    def start_minigame(self, idx):
        self.pending_action = idx
        for b in self.action_buttons:
            b.config(state="disabled")

        for w in self.mini_frame.winfo_children():
            w.destroy()

        area = self.game.area_data[self.game.current_area]
        self.log.config(text=f"MINIGAME: {area['minigame']}")

        opts = (
            ["Heads","Tails"] if area["minigame"]=="Coin Flip"
            else ["Rock","Paper","Scissors"] if area["minigame"]=="RPS"
            else [None]
        )

        for o in opts:
            tk.Button(
                self.mini_frame,
                text="ROLL" if o is None else o,
                font=("Arial", 12, "bold"),
                command=lambda v=o: self.resolve_turn(v)
            ).pack(pady=6)

    def resolve_turn(self, choice):
        e_action = ["atk","pry","hel"][self.game.ai.predict()]
        mult, _ = self.game.calculate_multiplier(choice)
        p_action = ["attack","parry","heal"][self.pending_action]

        dmg_e = dmg_p = 0

        if p_action == "attack":
            dmg_e = self.game.player.damage * mult if e_action!="pry" else 0
            dmg_p = self.game.enemy.damage if e_action=="pry" else 0
        elif p_action == "parry":
            dmg_e = self.game.player.damage*1.5 if e_action=="atk" and mult>0 else 0
            dmg_p = self.game.enemy.damage if e_action=="atk" and mult==0 else 0
        elif p_action == "heal":
            self.game.player.health = min(100, self.game.player.health + 15*mult)
            dmg_p = self.game.enemy.damage if e_action=="atk" else 0

        self.game.enemy.health -= dmg_e
        self.game.player.health -= dmg_p

        self.game.ai.history.append(self.pending_action)
        self.game.ai.train(self.pending_action)

        self.refresh_ui("dmg" if dmg_p>0 else "idle", "dmg" if dmg_e>0 else e_action)
        self.root.after(1000, lambda: self.refresh_ui("idle","idle"))
        self.root.after(1200, self.reset_turn)

    def reset_turn(self):
        for b in self.action_buttons:
            b.config(state="normal")
        self.log.config(text="SELECT MOVE")

    def refresh_ui(self, p_state="idle", e_state="idle"):
        area = self.game.area_data[self.game.current_area]

        bg = self.load_image(ASSET_PATH / area["bg"], (900,600))
        if bg:
            self.images["bg"] = bg
            self.canvas.itemconfig(self.bg_id, image=bg)

        enemy_img = self.load_image(
            ASSET_PATH / area["sprites"][e_state], (400,500)
        )
        if enemy_img:
            self.images["enemy"] = enemy_img
            self.canvas.itemconfig(self.enemy_id, image=enemy_img)

        self.canvas.itemconfig(self.player_id, image=self.images[f"p_{p_state}"])

        self.canvas.coords(self.p_bar, 50, 50, 50+200*(self.game.player.health/100), 70)
        self.canvas.coords(self.e_bar, 650, 50, 650+200*(self.game.enemy.health/self.game.enemy.max_health), 70)

if __name__ == "__main__":
    root = tk.Tk()
    GameUI(root, GameSystem("Hero"))
    root.mainloop()