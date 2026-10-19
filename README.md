# TheLastOffering
A turn-based dark fantasy mini-game built with Python (Tkinter) where player actions are decided through minigames, and enemies adapt using a lightweight predictive AI.

## Overview
The Last Offering is a single-player strategy game where each combat decision must be earned by completing a minigame.
Enemies learn from your previous actions and attempt to predict your next move.

## Action
Attack - Deal 1.0x damage x multiplier
Parry - Fully block enemy attack and counter with 1.5x damage x multiplier
Heal - Restore HP based on minigame multiplier

## Features
Animated minigame reveals
Area-based enemies and backgrounds
Dynamic HP bars
Sound effects (attack, parry, heal, minigames)
Adaptive enemy behavior

## Project Structure
Assets/
├── Background/
├── Enemy/
├── MC/
├── ActionButton/
├── Minigame/
├── Audio/
main.py
README.md

## How to run
pip install pillow pygame numpy tensorflow
python main.py

## Author
Built by:
- Leeman Pierpont Lawrence
- Joey Jeffrey (DSC2409076)
- Shaikamal Bekbolat
- Gunadi Gideon
- Zhang Yi Jun
