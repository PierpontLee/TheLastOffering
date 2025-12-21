"""
===LOGIC===
Player Has 3 actions:
0 - Attack  = Deal damage 1.0x to Enemy
1 - Parry = Fully block next Enemy attack and counter with 1.5x damage
2 - Heal = Restore health based on stat
Enemy Uses AI to predict Player'states next move based on the previous actions
There are 3 areas:

index - Area name - Minigame - Enemy

0 - Cemetery - Coin Flip - Gravekeeper
1 - Village: Enemy - Rock Paper Scissors - Guard
2 - Castle: Enemy - Dice Roll - Cult Leader

On each area player fight enemy, to do the action player must play areas minigame to succeed the action.
Coin flip - Guess Head or Tail
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
import numpy as np
import tensorflow as tf
import pygame

# --- CONFIG ---
ASSET_PATH = Path(__file__).parent.absolute() / "Assets"
FONT_TITLE = ("Eczar", 32, "bold")
FONT_MAIN = ("Eczar", 18, "bold")
FONT_BTN = ("Eczar", 12)
FONT_LOG = ("Eczar", 13)

# Enemy AI
class EnemyAI:
    def __init__(self):
        self.history = []
        self.memory = {}
        self.exploration_rate = 0.15
        self.decay = 0.97   # forget old patterns

    def predict(self) -> int:
        if len(self.history) < 2 or random.random() < self.exploration_rate:
            return random.randint(0, 2)

        key = tuple(self.history[-2:])

        if key not in self.memory:
            return random.randint(0, 2)

        return max(range(3), key=lambda i: self.memory[key][i])

    def train(self, action: int):
        if len(self.history) >= 2:
            key = tuple(self.history[-2:])

            if key not in self.memory:
                self.memory[key] = [0.0, 0.0, 0.0]

            # decay old knowledge
            self.memory[key] = [v * self.decay for v in self.memory[key]]

            # reinforce new action
            self.memory[key][action] += 1.0

        self.history.append(action)

# GameSystem
class GameSystem:
    def __init__(self, playerName="Player"):
        self.playerName = playerName
        
        #Set to area 1, not win and not lose
        self.currentArea, self.victory, self.dead = 0, False, False
        
        #Set player Stat
        self.player = {"hp": 100, "damage": 15}
        self.ai = EnemyAI()
        
        # Area Data
        self.areas = [
            {"name": "Cemetery", 
             "bg": "Background/Catacomb", 
             "enemyHP": 50, 
             "enemyDamage": 10, 
             "minigame": "Coin",
             "states": {
                 "idle": "Enemy/GravekeeperIdle", 
                "attack": "Enemy/GravekeeperAttack", 
                "parry": "Enemy/GravekeeperParry", 
                 "heal": "Enemy/GravekeeperHeal", 
                 "damage": "Enemy/GravekeeperDamaged"
                 }
            },
            {"name": "Village", 
             "bg": "Background/Village", 
             "enemyHP": 100, 
             "enemyDamage": 15, 
             "minigame": "RPS",
             "states": {
                 "idle": "Enemy/GuardIdle", 
                 "attack": "Enemy/GuardAttack",
                 "parry": "Enemy/GuardParry", 
                 "heal": "Enemy/GuardHeal", 
                 "damage": "Enemy/GuardDamaged"
                 }
             },
            {"name": "Castle", 
             "bg": "Background/Castle", 
             "enemyHP": 200, "enemyDamage": 20, 
             "minigame": "Dice",
             "states": {
                 "idle": "Enemy/CultLeaderIdle", 
                 "attack": "Enemy/CultLeaderAttack", 
                 "parry": "Enemy/CultLeaderParry", 
                 "heal": "Enemy/CultLeaderHeal", 
                 "damage": "Enemy/CultLeaderDamaged"
                 }
             }
        ]
        self.nextStage()

    #Check stage then move and change the enemy
    def nextStage(self):
        if self.currentArea < len(self.areas):
            areas = self.areas[self.currentArea]
            self.enemy = {"hp": areas["enemyHP"], "max": areas["enemyHP"], "damage": areas["enemyDamage"]}
        else: self.victory = True
        
    def resetGame(self):
        self.currentArea = 0
        self.victory = False
        self.dead = False

        # Reset player
        self.player = {"hp": 100, "damage": 15}

        # Reset AI (VERY IMPORTANT)
        self.ai = EnemyAI()

        # Load first enemy again
        self.nextStage()

#Start Screen
class StartScreen:
    def __init__(self, root):
        self.root = root
        self.frame = tk.Frame(root, bg="white", width=1200, height=900)
        self.frame.pack_propagate(False)
        self.frame.pack()

        # Setting for first frame
        tk.Label(self.frame, text="Who am I?", font=FONT_TITLE, bg="white", fg="black").pack(pady=(300, 10))
        
        # ask plyer name
        self.nameVar = tk.StringVar()
        self.entry = tk.Entry(self.frame, textvariable=self.nameVar, font=FONT_MAIN, justify="center", bd=1, relief="solid")
        self.entry.insert(0, "Input name...")
        self.entry.pack(pady=10)
        self.entry.bind("<FocusIn>", lambda enemy: self.entry.delete(0, tk.END))
        self.entry.bind("<Return>", self.startSequence)
        
    #First frame
    def startSequence(self, event):
        self.name = self.nameVar.get()
        self.entry.destroy()
        tk.Label(self.frame, text=self.name, font=FONT_MAIN, bg="white", fg="gray").pack()
        
        self.fadeLabel = tk.Label(self.frame, text="I have a bad feeling", font=FONT_MAIN, bg="white", fg="white")
        self.fadeLabel.pack(pady=40)
        self.fadeIn(0)

    #Fade in func
    def fadeIn(self, alpha):
        if alpha <= 255:
            # Gradually shift from white background to areas dark red/black text
            color = f'#{255-alpha:02x}{max(0, 150-alpha):02x}{max(0, 150-alpha):02x}'
            self.fadeLabel.config(fg=color)
            self.root.after(15, lambda: self.fadeIn(alpha + 5))
        else:
            self.root.after(3000, self.launchGame)

    #Launch game
    def launchGame(self):
        self.frame.destroy()
        gameSys = GameSystem(self.name)
        GameUI(self.root, gameSys)

#Game UI 
class GameUI:
    def __init__(self, root, game):
        self.root, self.game, self.assets = root, game, {}
        #sound loading
        try:
            pygame.mixer.init()
            self.sounds = {}
            self.loadSounds() # Load all audio files
        except Exception as e:
            print(f"Audio init failed: {e}")
        
        # Battle Layout
        self.canvas = tk.Canvas(root, width=900, height=600, bg="black", highlightthickness=0)
        self.canvas.grid(row=0, column=0)
        
        #Minigame Section
        self.side = tk.Frame(root, width=400, bg="#2c2c2c")
        self.side.grid(row=0, column=1, rowspan=2, sticky="nsew")
        
        #Action Button Section
        self.buttonFrame = tk.Frame(root, height=300, bg="#1a1a1a")
        self.buttonFrame.grid(row=1, column=0, sticky="nsew")

        self.ids = {k: self.canvas.create_image(x, y) for k, x, y in [("bg", 0, 0), ("player", 240, 430),("enemy", 450, 300)]}
        self.canvas.itemconfig(self.ids["bg"], anchor="nw")
        
        #Health bar
        self.playerHpBar = self.canvas.create_rectangle(50, 50, 250, 70, fill="#2ecc71")
        self.enemyHpBar = self.canvas.create_rectangle(650, 50, 850, 70, fill="#e74c3c")
        
        #Log
        self.log = tk.Label(self.side, 
                            text="BATTLE START", 
                            fg="white", 
                            bg="#2c2c2c", 
                            font=FONT_LOG, 
                            wraplength=250, 
                            justify="center")
        self.log.pack(pady=20)
        
        self.minigameFrame = tk.Frame(self.side, bg="#2c2c2c")
        self.minigameFrame.pack()
        
        self.resultLabel = tk.Label(self.side, bg="#2c2c2c")
        self.resultLabel.pack(pady=10)

        self.loadStatic()
        self.actionButtons = []
        for i, action in enumerate(["Attack", "Parry", "Heal"]):
            button = tk.Button(self.buttonFrame, image=self.assets[f"button{action}"], 
                          command=lambda v=i: self.startMinigame(v), 
                          borderwidth=0, 
                          bg="#1a1a1a", 
                          activebackground="#1a1a1a"
                        )
            button.pack(side="left", padx=30)
            self.actionButtons.append(button)
        self.refresh()

    #Image loader
    def loadImage(self, path, size):
        player = (ASSET_PATH / path).with_suffix(".png")
        try:
            if player.exists():
                return ImageTk.PhotoImage(Image.open(player).resize(size))
        except Exception as e:
            print(f"Error loading image {player}: {e}")

        # Fallback: return a transparent placeholder so UI keeps running
        try:
            img = Image.new("RGBA", size, (0, 0, 0, 0))
            return ImageTk.PhotoImage(img)
        except Exception:
            return None

    #Load Animation
    def loadStatic(self):
        #Asset setter
        for k, f in [("playerAttack","MC/MCAttack"), 
                     ("playerParry","MC/MCParry"), 
                     ("playerHeal","MC/MCHeal"), 
                     ("playerDamaged","MC/MCDamaged"), 
                     ("playerIdle","MC/MCIdle")]:
            self.assets[k] = self.loadImage(f, (150, 200))
        
        #Set action img
        for action in ["Attack", "Parry", "Heal"]: 
            self.assets[f"button{action}"] = self.loadImage(f"ActionButton/{action}Button", (200, 80))
        
        # Minigame img (folder is 'Minigame')
        self.assets["minigameHead"] = self.loadImage("Minigame/CoinHead", (120, 120))
        self.assets["minigameTail"] = self.loadImage("Minigame/CoinTail", (120, 120))
        for i in range(1, 7): self.assets[f"dice{i}"] = self.loadImage(f"Minigame/Dice{i}", (100, 100))
        for r in ["Rock", "Paper", "Scissor"]:
            self.assets[f"playerMinigame{r}"] = self.loadImage(f"Minigame/MC{r}", (120, 120))
            self.assets[f"enemyMinigame{r}"] = self.loadImage(f"Minigame/Guard{r}", (120, 120))

    #Start minigame
    def startMinigame(self, idx):
        if self.game.dead or self.game.victory: return
        
        #After chosen action cannot change
        for button in self.actionButtons: button.config(state="disabled")
        self.pending = idx
        area = self.game.areas[self.game.currentArea]
        
        opts = ["Head", "Tail"] if "Coin" in area["minigame"] else ["Rock", "Paper", "Scissor"] if "RPS" in area["minigame"] else [None]
        for o in opts:
            tk.Button(self.minigameFrame, text=o or "ROLL", font=FONT_BTN, fg="white", bg="#333", 
                      command=lambda v=o: self.resolveLogic(v), width=12).pack(pady=5)

    #Logic calc
    def resolveLogic(self, choice):
        area = self.game.areas[self.game.currentArea]
        self.log.config(text="REVEALING...")
        for w in self.minigameFrame.winfo_children(): w.destroy()

        enemyMove = ["attack", "parry", "heal"][self.game.ai.predict()]
        playerMove = ["attack", "parry", "heal"][self.pending]
        
        #Multiplier, image key, and pool
        multiplier, resultImageKey, pool = 0.0, "", []

        #Check area
        if area["minigame"] == "Coin":
            self.playSound("coin")
            result = random.choice(["Head", "Tail"])
            multiplier = 1.0 if choice == result else 0.0
            resultImageKey = f"minigame{result}"
            pool = [self.assets["minigameHead"], self.assets["minigameTail"]]
        elif area["minigame"] == "RPS":
            self.playSound("rps")
            result = random.choice(["Rock", "Paper", "Scissor"])
            multiplier = (
                1.5 if {"Rock": "Scissor", "Paper": "Rock", "Scissor": "Paper"}[choice] == result
                else 1.0 if choice == result
                else 0.0
            )
            resultImageKey = f"enemyMinigame{result}"
            pool = [self.assets[f"enemyMinigame{r}"] for r in ["Rock", "Paper", "Scissor"]]
        else: #Dice
            self.playSound("dice")
            roll = random.randint(1, 6)
            multiplier = {1:0.2, 2:0.5, 3:0.8, 4:1.2, 5:1.5, 6:2.0}[roll]
            resultImageKey = f"dice{roll}"
            pool = [self.assets[f"dice{i}"] for i in range(1, 7)]
            
        #shuffle call
        self.shuffleEffect(pool, self.assets[resultImageKey], 12, playerMove, enemyMove, multiplier)

    #Shuffle effect on minigame
    def shuffleEffect(self, pool, finalImage, count, playerMove, enemyMove, multiplier):
        # sanitize pool to remove None placeholders
        pool = [p for p in pool if p is not None]
        if not pool and finalImage is not None:
            pool = [finalImage]

        #Final Image
        if finalImage is None and pool:
            finalImage = pool[-1]
        
        if count > 0:
            img = random.choice(pool) if pool else None
            self.resultLabel.config(image=img) # type: ignore
            self.root.after(80, lambda: self.shuffleEffect(pool, finalImage, count-1, playerMove, enemyMove, multiplier))
        else:
            # ensure we at least set some image before applying results
            self.resultLabel.config(image=finalImage)
            self.applyTurnResults(playerMove, enemyMove, multiplier)

    #Applying result from action button and minigame mult
    def applyTurnResults(self, playerMove, enemyMove, multiplier):
        damageToEnemy = 0
        damageToPlayer = 0
        message = ""

        #Player successful attack
        if playerMove == "attack" and enemyMove != "parry":
            damageToEnemy = int(self.game.player["damage"] * multiplier)
            self.playSound("slash")
            message = f"DIRECT HIT!\nYou dealt {damageToEnemy} damage."

        #Player sucessfull parry
        elif playerMove == "parry" and enemyMove == "attack":
            damageToEnemy = int(self.game.player["damage"] * 1.5 * multiplier)
            damageToPlayer = 0
            self.playSound("parry")
            message = f"PERFECT PARRY!\nYou deflected the strike."
        
        #Heal
        elif playerMove or enemyMove == "heal":
            #Player heal
            if playerMove == "heal":
                if multiplier > 0:
                    healed = int(15 * multiplier)
                    self.game.player["hp"] = min(100, self.game.player["hp"] + healed)
                    self.playSound("heal")
                    message = f"You healed {healed} health."
            #Enemy heal
            elif enemyMove == "heal":
                self.game.enemy["hp"] = min(
                self.game.enemy["max"],
                self.game.enemy["hp"] + int(self.game.enemy["max"] * 0.1)
                )
                self.playSound("heal")
            elif playerMove and enemyMove == "heal": #both heal
                if multiplier > 0:
                    healed = int(15 * multiplier)
                    self.game.player["hp"] = min(100, self.game.player["hp"] + healed)
                self.game.enemy["hp"] = min(
                self.game.enemy["max"],
                self.game.enemy["hp"] + int(self.game.enemy["max"] * 0.1))
                self.playSound("heal")
                message = "You both healed."

        #Enemy Sucessful Attack
        elif enemyMove == "attack" and playerMove != "parry":
            damageToPlayer = int(self.game.enemy["damage"])
            self.playSound("slash")
            message = f"YOU WERE HIT!\nReceived {damageToPlayer} damage."
            
        #Enemy Sucessful Parry
        elif enemyMove == "parry" and playerMove == "attack":
            damageToPlayer = int(self.game.player["damage"] * 1.5 * multiplier)
            damageToEnemy = 0
            self.playSound("parry")
            message = "CLANG!\nYou've got parried by the enemy."
        
        else:
            message = "A tense standoff...\nNo damage was dealt."
        
        #Impact sound
        def playImpactSound():
            if damageToEnemy > 0:
                self.playSound("enemy_hurt")
            elif damageToPlayer > 0:
                self.playSound("mc_hurt")
            elif enemyMove == "parry" and playerMove == "attack":
                self.playSound("parry")

        self.root.after(500, playImpactSound)
        self.log.config(text=message)
        self.game.enemy["hp"] -= damageToEnemy
        self.game.player["hp"] -= damageToPlayer
        
        if self.game.player["hp"] <= 0:
            self.game.dead = True
            self.log.config(text="YOU DIED...\nReturning to the Catacomb")

            # Disable buttons immediately
            for button in self.actionButtons:
                button.config(state="disabled")

            # Restart after 3 seconds
            self.root.after(3000, self.restartGame)
            return

        
        player_state_key = "playerDamaged" if damageToPlayer > 0 else f"player{playerMove.capitalize()}"
        self.refresh(player_state_key, "damage" if damageToEnemy > 0 else enemyMove)
        self.root.after(2000, self.cleanUp)

    #Restart game (lose)
    def restartGame(self):
        # Reset logic
        self.game.resetGame()

        # Clear UI
        self.resultLabel.config(image="")
        self.log.config(text="A new offering begins...")
        for w in self.minigameFrame.winfo_children():
            w.destroy()

        # Re-enable buttons
        for button in self.actionButtons:
            button.config(state="normal")

        # Refresh visuals to Area 0
        self.refresh()

    #cleaning up
    def cleanUp(self):
        self.resultLabel.config(image="")
        self.log.config(text="YOUR MOVE")
        for w in self.minigameFrame.winfo_children(): w.destroy()
        #check winning
        if not self.game.dead and not self.game.victory:
            if self.game.enemy["hp"] <= 0: 
                self.game.currentArea += 1
                self.game.nextStage()
            for button in self.actionButtons: button.config(state="normal")
        self.refresh()

    #Refresh and check stats
    def refresh(self, playerState="playerIdle", enemyState="idle"):
        if self.game.victory: self.log.config(text="You're The last Offering?", fg="gold"); return
        if self.game.dead: self.log.config(text="You're NOT The last Offerings", fg="red"); return
        
        areas = self.game.areas[self.game.currentArea]
        self.assets["cb"] = self.loadImage(areas["bg"], (900, 600))
        # load enemy state image, fallback to idle if missing
        self.assets["ce"] = self.loadImage(areas["states"].get(enemyState, areas["states"].get("idle")), (240, 300))
        if self.assets["ce"] is None:
            self.assets["ce"] = self.loadImage(areas["states"].get("idle"), (320, 400))

        self.canvas.itemconfig(self.ids["bg"], image=self.assets["cb"])
        self.canvas.itemconfig(self.ids["enemy"], image=self.assets["ce"])

        # ensure player image exists, fallback to idle
        player_img = self.assets.get(playerState) or self.assets.get("playerIdle")
        self.canvas.itemconfig(self.ids["player"], image=player_img)
        
        # Update HP Bars
        player_x, player_y = 240, 430   # SAME as player image position
        self.canvas.coords(
            self.playerHpBar,
            player_x - 100,
            player_y - 180,
            player_x - 100 + (2 * max(0, self.game.player["hp"])),
            player_y - 160
        )
        enemy_x, enemy_y = 450, 300   # SAME as enemy image position
        self.canvas.coords(
            self.enemyHpBar,
            enemy_x - 100,
            enemy_y - 200,
            enemy_x - 100 + (200 * max(0, self.game.enemy["hp"] / self.game.enemy["max"])),
            enemy_y - 180
        )
    
    #
    def loadSounds(self):
        sound_map = {
            "slash": "Slash.mp3",      
            "parry": "Parry.mp3",     
            "heal": "Heal.mp3",        
            "coin": "Coin.mp3",          # Minigame: Coin Flip
            "dice": "Dice.mp3",          # Minigame: Dice Roll
            "rps": "RPS.mp3",            # Minigame: Rock Paper Scissors
            "mc_hurt": "MCHurt.mp3", # Enemy takes damage
            "enemy_hurt": "EnemyHurt.mp3"# Player takes damage
        }

        audio_folder = ASSET_PATH / "Audio"
        
        for key, filename in sound_map.items():
            path = audio_folder / filename
            if path.exists():
                try:
                    # Load sound and set default volume
                    self.sounds[key] = pygame.mixer.Sound(str(path))
                    self.sounds[key].set_volume(0.4) 
                except Exception as e:
                    print(f"Error loading sound {filename}: {e}")
            else:
                print(f"Sound file missing: {path}")
    
    #Play sound
    def playSound(self, key):
        if key in self.sounds:
            try:
                self.sounds[key].play()
            except:
                pass

if __name__ == "__main__":
    root = tk.Tk()
    root.title("The Last Offering")
    StartScreen(root)
    root.mainloop()