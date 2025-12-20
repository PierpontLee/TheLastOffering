import tkinter as tk
from PIL import Image, ImageTk
import random
from pathlib import Path
import numpy as np
import tensorflow as tf

# --- CONFIG ---
ASSET_PATH = Path(__file__).parent.absolute() / "Assets"
FONT_TITLE = ("Eczar", 32, "bold")
FONT_MAIN = ("Eczar", 18, "bold")
FONT_BTN = ("Eczar", 12)
FONT_LOG = ("Eczar", 13)

class EnemyAI:
    def __init__(self):
        self.model = tf.keras.Sequential([
            tf.keras.layers.Dense(16, activation="relu", input_shape=(3,)),
            tf.keras.layers.Dense(3, activation="softmax")
        ])
        self.model.compile(optimizer="adam", loss="sparse_categorical_crossentropy")
        self.history = [0, 1, 2]

    def predict(self) -> int:
        X = np.array([self.history[-3:]])
        return int(np.argmax(self.model.predict(X, verbose=0)[0]))

    def train(self, last_act: int):
        X, y = np.array([self.history[-3:]]), np.array([last_act])
        self.model.fit(X, y, epochs=1, verbose=0)
        self.history.append(last_act)

class GameSystem:
    def __init__(self, player_name="Player"):
        self.player_name = player_name
        self.current_area, self.victory, self.dead = 0, False, False
        self.player = {"hp": 100, "dmg": 15}
        self.ai = EnemyAI()
        self.areas = [
            {"name": "Cemetery", "bg": "Background/Catacomb", "e_hp": 50, "e_dmg": 10, "mg": "Coin",
             "s": {"idle": "Enemy/GravekeeperIdle", "atk": "Enemy/GravekeeperAttack", "pry": "Enemy/GravekeeperShield", "hel": "Enemy/GravekeeperHeal", "dmg": "Enemy/GravekeeperDamaged"}},
            {"name": "Village", "bg": "Background/Village", "e_hp": 100, "e_dmg": 15, "mg": "RPS",
             "s": {"idle": "Enemy/GuardIdle", "atk": "Enemy/GuardAttack", "pry": "Enemy/GuardParry", "hel": "Enemy/GuardHeal", "dmg": "Enemy/GuardDamaged"}},
            {"name": "Castle", "bg": "Background/Castle", "e_hp": 200, "e_dmg": 20, "mg": "Dice",
             "s": {"idle": "Enemy/CultLeaderIdle", "atk": "Enemy/CultLeaderAttack", "pry": "Enemy/CultLeaderParry", "hel": "Enemy/CultLeaderHeal", "dmg": "Enemy/CultLeaderDamaged"}}
        ]
        self.next_stage()

    def next_stage(self):
        if self.current_area < len(self.areas):
            a = self.areas[self.current_area]
            self.enemy = {"hp": a["e_hp"], "max": a["e_hp"], "dmg": a["e_dmg"]}
        else: self.victory = True

class StartScreen:
    def __init__(self, root):
        self.root = root
        self.frame = tk.Frame(root, bg="white", width=1200, height=900)
        self.frame.pack_propagate(False)
        self.frame.pack()

        tk.Label(self.frame, text="Who am I?", font=FONT_TITLE, bg="white", fg="black").pack(pady=(300, 10))
        
        self.name_var = tk.StringVar()
        self.entry = tk.Entry(self.frame, textvariable=self.name_var, font=FONT_MAIN, justify="center", bd=1, relief="solid")
        self.entry.insert(0, "Input name...")
        self.entry.pack(pady=10)
        self.entry.bind("<FocusIn>", lambda e: self.entry.delete(0, tk.END))
        self.entry.bind("<Return>", self.start_sequence)

    def start_sequence(self, event):
        self.name = self.name_var.get()
        self.entry.destroy()
        tk.Label(self.frame, text=self.name, font=FONT_MAIN, bg="white", fg="gray").pack()
        
        self.fade_label = tk.Label(self.frame, text="I have a bad feeling", font=FONT_MAIN, bg="white", fg="white")
        self.fade_label.pack(pady=40)
        self.fade_in(0)

    def fade_in(self, alpha):
        if alpha <= 255:
            # Gradually shift from white background to a dark red/black text
            color = f'#{255-alpha:02x}{max(0, 150-alpha):02x}{max(0, 150-alpha):02x}'
            self.fade_label.config(fg=color)
            self.root.after(15, lambda: self.fade_in(alpha + 5))
        else:
            self.root.after(3000, self.launch_game)

    def launch_game(self):
        self.frame.destroy()
        game_sys = GameSystem(self.name)
        GameUI(self.root, game_sys)

class GameUI:
    def __init__(self, root, game):
        self.root, self.game, self.assets = root, game, {}
        
        # Battle Layout
        self.canvas = tk.Canvas(root, width=900, height=600, bg="black", highlightthickness=0)
        self.canvas.grid(row=0, column=0)
        
        self.side = tk.Frame(root, width=300, bg="#2c2c2c")
        self.side.grid(row=0, column=1, rowspan=2, sticky="nsew")
        
        self.btns_frame = tk.Frame(root, height=300, bg="#1a1a1a")
        self.btns_frame.grid(row=1, column=0, sticky="nsew")

        self.ids = {k: self.canvas.create_image(x, y) for k, x, y in [("bg", 0, 0), ("p", 200, 400), ("e", 650, 350)]}
        self.canvas.itemconfig(self.ids["bg"], anchor="nw")
        
        self.p_bar = self.canvas.create_rectangle(50, 50, 250, 70, fill="#2ecc71")
        self.e_bar = self.canvas.create_rectangle(650, 50, 850, 70, fill="#e74c3c")
        
        self.log = tk.Label(self.side, text="BATTLE START", fg="white", bg="#2c2c2c", font=FONT_LOG, wraplength=250, justify="center")
        self.log.pack(pady=20)
        
        self.m_frame = tk.Frame(self.side, bg="#2c2c2c")
        self.m_frame.pack()
        
        self.res_label = tk.Label(self.side, bg="#2c2c2c")
        self.res_label.pack(pady=10)

        self.load_static()
        self.action_btns = []
        for i, n in enumerate(["Attack", "Parry", "Heal"]):
            b = tk.Button(self.btns_frame, image=self.assets[f"btn_{n}"], command=lambda v=i: self.start_mg(v), borderwidth=0, bg="#1a1a1a", activebackground="#1a1a1a")
            b.pack(side="left", padx=30)
            self.action_btns.append(b)
        self.refresh()

    def load_img(self, path, size):
        p = (ASSET_PATH / path).with_suffix(".png")
        return ImageTk.PhotoImage(Image.open(p).resize(size)) if p.exists() else None

    def load_static(self):
        for k, f in [("p_atk","MC/MCAttack"), ("p_pry","MC/MCParry"), ("p_hel","MC/MCHeal"), ("p_dmg","MC/MCDamaged"), ("p_idle","MC/MCIdle")]:
            self.assets[k] = self.load_img(f, (300, 400))
        for n in ["Attack", "Parry", "Heal"]: 
            self.assets[f"btn_{n}"] = self.load_img(f"ActionButton/{n}Button", (200, 80))
        
        self.assets["mg_Heads"] = self.load_img("MiniGames/CoinHead", (120, 120))
        self.assets["mg_Tails"] = self.load_img("MiniGames/CoinTail", (120, 120))
        for i in range(1, 7): self.assets[f"dice{i}"] = self.load_img(f"MiniGames/dice{i}", (100, 100))
        for r in ["Rock", "Paper", "Scissor"]:
            self.assets[f"pmg_{r}"] = self.load_img(f"MiniGames/MC{r}", (120, 120))
            self.assets[f"emg_{r}"] = self.load_img(f"MiniGames/Guard{r}", (120, 120))

    def start_mg(self, idx):
        if self.game.dead or self.game.victory: return
        for b in self.action_btns: b.config(state="disabled")
        self.pending = idx
        area = self.game.areas[self.game.current_area]
        
        opts = ["Heads", "Tails"] if "Coin" in area["mg"] else ["Rock", "Paper", "Scissor"] if "RPS" in area["mg"] else [None]
        for o in opts:
            tk.Button(self.m_frame, text=o or "ROLL", font=FONT_BTN, fg="white", bg="#333", 
                      command=lambda v=o: self.resolve_logic(v), width=12).pack(pady=5)

    def resolve_logic(self, choice):
        area = self.game.areas[self.game.current_area]
        self.log.config(text="REVEALING...")
        for w in self.m_frame.winfo_children(): w.destroy()

        e_move = ["atk", "pry", "hel"][self.game.ai.predict()]
        p_move = ["atk", "pry", "hel"][self.pending]
        
        mult, res_img_key, pool = 0.0, "", []

        if area["mg"] == "Coin":
            res = random.choice(["Heads", "Tails"])
            mult = 1.0 if choice == res else 0.0
            res_img_key = f"mg_{res}"
            pool = [self.assets["mg_Heads"], self.assets["mg_Tails"]]
        elif area["mg"] == "RPS":
            res = random.choice(["Rock", "Paper", "Scissor"])
            mult = 0.5 if choice == res else (1.0 if {"Rock":"Scissor","Paper":"Rock","Scissor":"Paper"}[choice] == res else 0.0)
            res_img_key = f"emg_{res}"
            pool = [self.assets[f"emg_{r}"] for r in ["Rock", "Paper", "Scissor"]]
        else:
            roll = random.randint(1, 6)
            mult = {1:0.2, 2:0.5, 3:0.8, 4:1.2, 5:1.5, 6:2.0}[roll]
            res_img_key = f"dice{roll}"
            pool = [self.assets[f"dice{i}"] for i in range(1, 7)]

        self.shuffle_effect(pool, self.assets[res_img_key], 12, p_move, e_move, mult)

    def shuffle_effect(self, pool, final_img, count, p_move, e_move, mult):
        if count > 0:
            self.res_label.config(image=random.choice(pool))
            self.root.after(80, lambda: self.shuffle_effect(pool, final_img, count-1, p_move, e_move, mult))
        else:
            self.res_label.config(image=final_img)
            self.apply_turn_results(p_move, e_move, mult)

    def apply_turn_results(self, p_move, e_move, mult):
        dmg_to_e = int(self.game.player["dmg"] * mult) if p_move == "atk" and e_move != "pry" else 0
        dmg_to_p = int(self.game.enemy["dmg"]) if e_move == "atk" and p_move != "pry" else 0
        
        # Detailed Combat Log
        if p_move == "pry" and e_move == "atk":
            msg = f"PERFECT PARRY!\nYou deflected the strike."
        elif e_move == "pry" and p_move == "atk":
            msg = "CLANG!\nThe enemy parried your blade."
        elif dmg_to_e > 0:
            msg = f"DIRECT HIT!\nYou dealt {dmg_to_e} damage."
        elif dmg_to_p > 0:
            msg = f"YOU WERE STRUCK!\nReceived {dmg_to_p} damage."
        else:
            msg = "A tense standoff...\nNo damage was dealt."

        self.log.config(text=msg)
        self.game.enemy["hp"] -= dmg_to_e
        self.game.player["hp"] -= dmg_to_p
        
        if self.game.player["hp"] <= 0: self.game.dead = True
        self.game.ai.train(self.pending)
        
        self.refresh("p_dmg" if dmg_to_p > 0 else f"p_{p_move}", "dmg" if dmg_to_e > 0 else e_move)
        self.root.after(2000, self.cleanup)

    def cleanup(self):
        self.res_label.config(image="")
        self.log.config(text="YOUR MOVE")
        for w in self.m_frame.winfo_children(): w.destroy()
        if not self.game.dead and not self.game.victory:
            if self.game.enemy["hp"] <= 0: 
                self.game.current_area += 1
                self.game.next_stage()
            for b in self.action_btns: b.config(state="normal")
        self.refresh()

    def refresh(self, p_s="p_idle", e_s="idle"):
        if self.game.victory: self.log.config(text="THE OFFERING IS COMPLETE", fg="gold"); return
        if self.game.dead: self.log.config(text="YOUR JOURNEY ENDS HERE", fg="red"); return
        
        a = self.game.areas[self.game.current_area]
        self.assets["cb"], self.assets["ce"] = self.load_img(a["bg"], (900, 600)), self.load_img(a["s"][e_s], (400, 500))
        self.canvas.itemconfig(self.ids["bg"], image=self.assets["cb"])
        self.canvas.itemconfig(self.ids["e"], image=self.assets["ce"])
        self.canvas.itemconfig(self.ids["p"], image=self.assets[p_s])
        
        # Update HP Bars
        self.canvas.coords(self.p_bar, 50, 50, 50 + (2 * max(0, self.game.player["hp"])), 70)
        self.canvas.coords(self.e_bar, 650, 50, 650 + (200 * max(0, self.game.enemy["hp"]/self.game.enemy["max"])), 70)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("The Last Offering")
    StartScreen(root)
    root.mainloop()