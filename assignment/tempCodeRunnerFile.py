import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
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
        # FIX 1: Removed the space in 'tf.kera s'
        self.model = tf.keras.Sequential([
            tf.keras.layers.Dense(16, activation="relu", input_shape=(3,)),
            tf.keras.layers.Dense(3, activation="softmax")
        ])
        self.model.compile(
            optimizer="adam",
            loss="sparse_categorical_crossentropy"
        )
        self.history = [0, 1, 2]  # seed history

    def train(self, last_player_action: int):
        X = np.array([self.history[-3:]])
        y = np.array([last_player_action])
        # Silent training to reduce console spam
        self.model.fit(X, y, epochs=1, verbose=0)

    def predict(self) -> int:
        X = np.array([self.history[-3:]])
        pred = self.model.predict(X, verbose=0)
        action = int(np.argmax(pred))
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
        self.game_over = False
        self.victory = False

        self.area_data = [
            {
                "name": "Cemetery",
                "bg": "Background/Catacomb.png",
                "e_name": "GraveKeeper",
                "hp": 50,
                "dmg": 10,
                "minigame": "Coin Flip",
                "sprites": {
                    "idle": "Enemy/GravekeeperIdle.png",
                    "atk": "Enemy/GravekeeperAttack.png",
                    "pry": "Enemy/GravekeeperShield.png",
                    "hel": "Enemy/GravekeeperHeal.png",
                    "dmg": "Enemy/GravekeeperDamaged.png"
                }
            },
            {
                "name": "Village",
                "bg": "Background/Village.png",
                "e_name": "Guard",
                "hp": 100,
                "dmg": 15,
                "minigame": "RPS",
                "sprites": {
                    "idle": "Enemy/GuardIdle.png",
                    "atk": "Enemy/GuardAttack.png",
                    "pry": "Enemy/GuardParry.png",
                    "hel": "Enemy/GuardHeal.png",
                    "dmg": "Enemy/GuardDamaged.png"
                }
            },
            {
                "name": "Castle",
                "bg": "Background/Castle.png",
                "e_name": "Cult Leader",
                "hp": 200,
                "dmg": 20,
                "minigame": "Dice",
                "sprites": {
                    "idle": "Enemy/CultLeaderIdle.png",
                    "atk": "Enemy/CultLeaderAttack.png",
                    "pry": "Enemy/CultLeaderParry.png",
                    "hel": "Enemy/CultLeaderHeal.png",
                    "dmg": "Enemy/CultLeaderDamaged.png"
                }
            }
        ]
        self.set_area()

    def set_area(self):
        if self.current_area < len(self.area_data):
            d = self.area_data[self.current_area]
            self.enemy = Character(d["e_name"], d["hp"], d["dmg"])
            logger.debug(f"Loaded area {d['name']}")
        else:
            self.victory = True

    # FIX 2: Added Logic to advance the level
    def check_progression(self):
        if self.player.health <= 0:
            self.game_over = True
            return "LOSE"
        
        if self.enemy.health <= 0:
            self.current_area += 1
            if self.current_area >= len(self.area_data):
                self.victory = True
                return "WIN_GAME"
            else:
                self.set_area() # Load next boss
                return "NEXT_LEVEL"
        
        return "CONTINUE"

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

        # Main Game Canvas
        self.canvas = tk.Canvas(root, width=900, height=600, bg="black")
        self.canvas.grid(row=0, column=0)

        # Side Panel
        self.side_panel = tk.Frame(root, width=300, bg="#2c2c2c")
        self.side_panel.grid(row=0, column=1, rowspan=2, sticky="nsew")

        # Action Panel (Bottom)
        self.action_panel = tk.Frame(root, height=300, bg="#1a1a1a")
        self.action_panel.grid(row=1, column=0, sticky="nsew")

        # Canvas Elements
        self.bg_id = self.canvas.create_image(0, 0, anchor="nw")
        self.enemy_id = self.canvas.create_image(650, 350)
        self.player_id = self.canvas.create_image(200, 400)

        # HP Bars
        self.p_bar = self.canvas.create_rectangle(50, 50, 250, 70, fill="green", outline="white")
        self.e_bar = self.canvas.create_rectangle(650, 50, 850, 70, fill="red", outline="white")
        
        # Text Labels for Names
        self.p_name = self.canvas.create_text(50, 30, text=self.game.player.name, anchor="w", fill="white", font=("Arial", 12, "bold"))
        self.e_name = self.canvas.create_text(650, 30, text=self.game.enemy.name, anchor="w", fill="white", font=("Arial", 12, "bold"))

        # Log
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

    # FIX 4: Robust Image Loading (Creates placeholders if files missing)
    def load_image(self, path, size):
        try:
            if path.exists():
                img = Image.open(path).resize(size)
                return ImageTk.PhotoImage(img)
            else:
                raise FileNotFoundError
        except:
            # Create a placeholder colored rectangle if image missing
            color = (random.randint(50,200), random.randint(50,200), random.randint(50,200))
            img = Image.new('RGB', size, color=color)
            draw = ImageDraw.Draw(img)
            draw.text((10,10), str(path.name), fill="white")
            return ImageTk.PhotoImage(img)

    def load_assets(self):
        for k, f in [
            ("idle","MC/MCIdle.png"),
            ("atk","MC/MCAttack.png"),
            ("pry","MC/MCParry.png"),
            ("hel","MC/MCHeal.png"),
            ("dmg","MC/MCDamaged.png")
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
        if self.game.game_over or self.game.victory: return
        
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
        # 1. AI Predicts
        e_action_idx = self.game.ai.predict()
        e_action_str = ["atk","pry","hel"][e_action_idx]
        
        # 2. Player Minigame Result
        mult, result_val = self.game.calculate_multiplier(choice)
        p_action_str = ["attack","parry","heal"][self.pending_action]

        dmg_e = dmg_p = 0
        
        # 3. Combat Logic
        if p_action_str == "attack":
            dmg_e = self.game.player.damage * mult if e_action_str!="pry" else 0
            dmg_p = self.game.enemy.damage if e_action_str=="pry" else 0
        elif p_action_str == "parry":
            dmg_e = self.game.player.damage*1.5 if e_action_str=="atk" and mult>0 else 0
            dmg_p = self.game.enemy.damage if e_action_str=="atk" and mult==0 else 0
        elif p_action_str == "heal":
            self.game.player.health = min(100, self.game.player.health + 15*mult)
            dmg_p = self.game.enemy.damage if e_action_str=="atk" else 0
            
        # 4. Apply Damage
        self.game.enemy.health -= dmg_e
        self.game.player.health -= dmg_p
        
        # 5. Train AI
        self.game.ai.history.append(self.pending_action)
        self.game.ai.train(self.pending_action)

        # 6. Update UI with Damage Animation
        self.refresh_ui("dmg" if dmg_p>0 else "idle", "dmg" if dmg_e>0 else e_action_str)
        self.log.config(text=f"You rolled: {result_val}\nEnemy did: {e_action_str.upper()}\nDmg Given: {dmg_e}\nDmg Taken: {dmg_p}")

        # 7. Check Progression or Reset Turn
        status = self.game.check_progression()
        
        if status == "CONTINUE":
            self.root.after(1000, lambda: self.refresh_ui("idle","idle"))
            self.root.after(1200, self.reset_turn)
        elif status == "NEXT_LEVEL":
            self.root.after(1500, self.load_next_level)
        elif status == "WIN_GAME":
            self.log.config(text="YOU DEFEATED THE CULT!", fg="gold")
            self.canvas.create_text(450, 300, text="VICTORY", font=("Arial", 50, "bold"), fill="gold")
        elif status == "LOSE":
            self.log.config(text="YOU DIED", fg="red")
            self.canvas.create_text(450, 300, text="GAME OVER", font=("Arial", 50, "bold"), fill="red")

    def load_next_level(self):
        self.log.config(text=f"ENTERING {self.game.area_data[self.game.current_area]['name']}...")
        self.refresh_ui()
        self.reset_turn()

    def reset_turn(self):
        for b in self.action_buttons: 
            b.config(state="normal")
        for w in self.mini_frame.winfo_children():
            w.destroy()
        if not self.game.victory and not self.game.game_over:
            self.log.config(text="SELECT MOVE")

    def refresh_ui(self, p_state="idle", e_state="idle"):
        if self.game.victory: return

        area = self.game.area_data[self.game.current_area]

        # Update Background
        bg = self.load_image(ASSET_PATH / area["bg"], (900,600))
        if bg:
            self.images["bg"] = bg
            self.canvas.itemconfig(self.bg_id, image=bg)

        # Update Enemy
        enemy_img = self.load_image(
            ASSET_PATH / area["sprites"][e_state], (400,500)
        )
        if enemy_img:
            self.images["enemy"] = enemy_img
            self.canvas.itemconfig(self.enemy_id, image=enemy_img)

        # Update Player
        self.canvas.itemconfig(self.player_id, image=self.images[f"p_{p_state}"])
        
        # Update Text
        self.canvas.itemconfig(self.e_name, text=f"{self.game.enemy.name} ({int(self.game.enemy.health)}/{self.game.enemy.max_health})")

        # Update Bars
        p_pct = max(0, self.game.player.health/100)
        e_pct = max(0, self.game.enemy.health/self.game.enemy.max_health)
        
        self.canvas.coords(self.p_bar, 50, 50, 50+200*p_pct, 70)
        self.canvas.coords(self.e_bar, 650, 50, 650+200*e_pct, 70)

if __name__ == "__main__":
    root = tk.Tk()
    GameUI(root, GameSystem("Hero"))
    root.mainloop()