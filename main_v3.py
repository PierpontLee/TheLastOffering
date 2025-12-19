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
import os
import numpy as np
import tensorflow as tf

# --- CONFIGURATION ---
WINDOW_TITLE = "The Last Offering"
ASSET_PATH = r"c:\Users\user\Downloads\assignment\assignment\assets"

# --- 1. ENEMY AI ---
class EnemyAI:
    def __init__(self):
        self.model = tf.keras.Sequential([ # type: ignore
            tf.keras.layers.Dense(16, activation='relu', input_shape=(3,)), # type: ignore
            tf.keras.layers.Dense(3, activation='softmax') # type: ignore
        ])
        self.model.compile(optimizer='adam', loss='sparse_categorical_crossentropy')
        self.history = [0, 1, 2]

    def train(self, last_player_action):
        X = np.array([self.history[-3:]])
        y = np.array([last_player_action])
        self.model.fit(X, y, epochs=2, verbose=0)

    def predict(self):
        X = np.array([self.history[-3:]]) 
        pred = self.model.predict(X, verbose=0)
        return int(np.argmax(pred))

# --- 2. GAME LOGIC ---
class Character:
    def __init__(self, name, health, damage):
        self.name, self.max_health, self.health, self.damage = name, health, health, damage

class GameSystem:
    def __init__(self, player_name):
        self.current_area = 0
        self.player = Character(player_name, 100, 15)
        self.ai = EnemyAI()
        self.area_data = [
            {'name': 'Cemetery', 'bg': 'Catacomb.png', 'e_name': 'GraveKeeper', 'hp': 50, 'dmg': 10, 'minigame': 'Coin Flip', 
             'sprites': {'idle': 'GravekeeperIdle.png', 'atk': 'GravekeeperAttack.png', 'pry': 'GravekeeperShield.png', 'hel': 'GravekeeperHeal.png', 'dmg': 'GravekeeperDamaged.png'}},
            {'name': 'Village', 'bg': 'Village.png', 'e_name': 'Guard', 'hp': 100, 'dmg': 15, 'minigame': 'RPS', 
             'sprites': {'idle': 'GuardIdle.png', 'atk': 'GuardAttack.png', 'pry': 'GuardParry.png', 'hel': 'GuardHeal.png', 'dmg': 'GuardDamaged.png'}},
            {'name': 'Castle', 'bg': 'Castle.png', 'e_name': 'Cult Leader', 'hp': 200, 'dmg': 20, 'minigame': 'Dice', 
             'sprites': {'idle': 'CultLeaderIdle.png', 'atk': 'CultLeaderAttack.png', 'pry': 'CultLeaderParry.png', 'hel': 'CultLeaderHeal.png', 'dmg': 'CultLeaderDamaged.png'}}
        ]
        self.set_area()

    def set_area(self):
        if self.current_area < len(self.area_data):
            d = self.area_data[self.current_area]
            self.enemy = Character(d['e_name'], d['hp'], d['dmg'])

    def calculate_multiplier(self, choice):
        area = self.area_data[self.current_area]
        if area['minigame'] == 'Coin Flip':
            res = random.choice(['Heads', 'Tails'])
            return (1.0, res) if choice == res else (0.0, res)
        elif area['minigame'] == 'RPS':
            enemy_rps = random.choice(['Rock', 'Paper', 'Scissors'])
            if choice == enemy_rps: return 0.5, enemy_rps
            beats = {'Rock': 'Scissors', 'Paper': 'Rock', 'Scissors': 'Paper'}
            return (1.0, enemy_rps) if beats[choice] == enemy_rps else (0.0, enemy_rps)
        elif area['minigame'] == 'Dice':
            roll = random.randint(1, 6)
            mults = {1: 0.2, 2: 0.5, 3: 0.8, 4: 1.2, 5: 1.5, 6: 2.0}
            return mults[roll], roll
        return 0.0, ""

# --- 3. GUI ---
class GameUI:
    def __init__(self, root, game_system):
        self.root, self.game = root, game_system
        self.images = {}
        self.action_buttons = []
        
        # Grid weight configuration to fill all space
        root.grid_columnconfigure(0, weight=0)
        root.grid_columnconfigure(1, weight=1)
        root.grid_rowconfigure(0, weight=0)
        root.grid_rowconfigure(1, weight=1)

        # 1. Canvas (Top Left)
        self.canvas = tk.Canvas(root, width=900, height=600, bg="black", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nw")
        
        # 2. Side Panel (Right Column - Spans 2 rows)
        self.side_panel = tk.Frame(root, width=300, bg="#2c2c2c")
        self.side_panel.grid(row=0, column=1, rowspan=2, sticky="nsew")
        
        # 3. Action Panel (Bottom Row)
        self.action_panel = tk.Frame(root, height=300, bg="#1a1a1a")
        self.action_panel.grid(row=1, column=0, sticky="nsew")

        # Canvas Elements
        self.bg_id = self.canvas.create_image(0, 0, anchor="nw")
        self.e_sprite_id = self.canvas.create_image(650, 350, anchor="center")
        self.p_sprite_id = self.canvas.create_image(200, 400, anchor="center")
        self.p_bar = self.canvas.create_rectangle(50, 50, 250, 70, fill="green")
        self.e_bar = self.canvas.create_rectangle(650, 50, 850, 70, fill="red")
        
        # Log UI
        self.log = tk.Label(self.side_panel, text="BATTLE START", fg="white", bg="#2c2c2c", 
                            font=("Arial", 14, "bold"), wraplength=250)
        self.log.pack(pady=40)
        
        self.mini_frame = tk.Frame(self.side_panel, bg="#2c2c2c")
        self.mini_frame.pack(pady=10, fill="x")

        self.load_assets()
        self.setup_buttons()
        self.refresh_ui()

    def load_assets(self):
        def get_img(f, sz):
            p = os.path.join(ASSET_PATH, f)
            return ImageTk.PhotoImage(Image.open(p).resize(sz)) if os.path.exists(p) else None
        
        for k, f in [('idle','MCIdle.png'),('atk','MCAttack.png'),('pry','MCParry.png'),('hel','MCHeal.png'),('dmg','MCDamaged.png')]:
            self.images[f'p_{k}'] = get_img(f, (300, 400))
        for i in range(3):
            self.images[f'btn{i}'] = get_img(['AttackButton.png','ParryButton.png','HealButton.png'][i], (280, 280))

    def setup_buttons(self):
        self.btn_container = tk.Frame(self.action_panel, bg="#1a1a1a")
        self.btn_container.pack(expand=True)
        for i in range(3):
            img = self.images.get(f'btn{i}')
            btn = tk.Button(self.btn_container, image=img if img else "", borderwidth=0, 
                            bg="#1a1a1a", activebackground="#1a1a1a", command=lambda v=i: self.start_minigame(v))
            btn.pack(side="left", padx=10)
            self.action_buttons.append(btn)

    def start_minigame(self, idx):
        for btn in self.action_buttons: btn.config(state="disabled")
        self.pending_action = idx
        for w in self.mini_frame.winfo_children(): w.destroy()
        area = self.game.area_data[self.game.current_area]
        self.log.config(text=f"MINIGAME: {area['minigame']}")
        opts = ['Heads', 'Tails'] if area['minigame'] == 'Coin Flip' else (['Rock', 'Paper', 'Scissors'] if area['minigame'] == 'RPS' else [None])
        for o in opts:
            tk.Button(self.mini_frame, text=o if o else "ROLL", width=15, font=("Arial", 12, "bold"),
                      command=lambda val=o: self.resolve_turn(val)).pack(pady=10)

    # --- DAMAGE VISUALS (CANVAS BASED) ---
    def show_dmg(self, amt, x, y):
        txt_id = self.canvas.create_text(x, y, text=f"-{int(amt)}", fill="#ff4444", 
                                         font=("Arial", 35, "bold"))
        # Animated "pop" effect
        def animate_dmg(step=0):
            if step < 10:
                self.canvas.move(txt_id, 0, -2) # Drift up
                self.root.after(30, lambda: animate_dmg(step + 1))
            else:
                self.root.after(500, lambda: self.canvas.delete(txt_id))
        animate_dmg()

    def shake_screen(self):
        for _ in range(6):
            dx, dy = random.randint(-8, 8), random.randint(-8, 8)
            self.canvas.move("all", dx, dy)
            self.root.update()
            self.root.after(20)
            self.canvas.move("all", -dx, -dy)

    def resolve_turn(self, p_input):
        e_pred = self.game.ai.predict()
        e_action = ["atk", "pry", "hel"][1 if e_pred == 0 else (2 if e_pred == 1 else 0)]
        mult, _ = self.game.calculate_multiplier(p_input)
        p_act_name = ["attack", "parry", "heal"][self.pending_action]
        
        dmg_e = 0; dmg_p = 0
        if p_act_name == "attack":
            if e_action == "pry": dmg_p = self.game.enemy.damage
            else: dmg_e = self.game.player.damage * mult
        elif p_act_name == "parry":
            if e_action == "atk" and mult > 0: dmg_e = self.game.player.damage * 1.5
            else: dmg_p = self.game.enemy.damage if e_action == "atk" else 0
        elif p_act_name == "heal":
            self.game.player.health = min(100, self.game.player.health + (15 * mult))
            if e_action == "atk": dmg_p = self.game.enemy.damage

        self.game.enemy.health -= dmg_e; self.game.player.health -= dmg_p
        self.game.ai.history.append(self.pending_action); self.game.ai.train(self.pending_action)
        
        # Display Damage
        if dmg_e > 0: self.show_dmg(dmg_e, 650, 200); self.shake_screen()
        if dmg_p > 0: self.show_dmg(dmg_p, 200, 200)

        p_vis_map = {"attack":"atk", "parry":"pry", "heal":"hel"}
        p_vis = "dmg" if dmg_p > 0 else p_vis_map[p_act_name]
        self.refresh_ui(p_state=p_vis, e_state="dmg" if dmg_e > 0 else e_action)
        for w in self.mini_frame.winfo_children(): w.destroy()

        if self.game.player.health <= 0:
            self.log.config(text="OFFERING FAILED", fg="red")
        elif self.game.enemy.health <= 0:
            self.root.after(1000, self.next_area)
        else:
            self.root.after(1200, self.reset_turn)

    def reset_turn(self):
        for btn in self.action_buttons: btn.config(state="normal")
        self.log.config(text="SELECT MOVE")
        self.refresh_ui('idle', 'idle')

    def next_area(self):
        self.game.current_area += 1
        self.game.set_area()
        self.reset_turn()

    def refresh_ui(self, p_state='idle', e_state='idle'):
        if self.game.current_area >= len(self.game.area_data):
            self.canvas.delete("all")
            self.canvas.create_text(450, 300, text="OFFERING COMPLETE", font=("Arial", 50, "bold"), fill="gold")
            return
        area = self.game.area_data[self.game.current_area]
        bg_p = os.path.join(ASSET_PATH, area['bg'])
        if os.path.exists(bg_p):
            self.images['bg'] = ImageTk.PhotoImage(Image.open(bg_p).resize((900, 600)))
            self.canvas.itemconfig(self.bg_id, image=self.images['bg'])
        e_f = area['sprites'].get(e_state, area['sprites']['idle'])
        e_p = os.path.join(ASSET_PATH, e_f)
        if os.path.exists(e_p):
            self.images['enemy'] = ImageTk.PhotoImage(Image.open(e_p).resize((400, 500)))
            self.canvas.itemconfig(self.e_sprite_id, image=self.images['enemy'])
        if f'p_{p_state}' in self.images: self.canvas.itemconfig(self.p_sprite_id, image=self.images[f'p_{p_state}'])
        
        p_r = max(0, self.game.player.health/100); e_r = max(0, self.game.enemy.health/self.game.enemy.max_health)
        self.canvas.coords(self.p_bar, 50, 50, 50 + (200 * p_r), 70)
        self.canvas.coords(self.e_bar, 650, 50, 650 + (200 * e_r), 70)

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1200x90")
    root.title(WINDOW_TITLE)
    app = GameUI(root, GameSystem("Hero"))
    root.mainloop()