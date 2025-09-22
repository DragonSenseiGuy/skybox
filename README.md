# Tower Tetris (Skyscraper Edition)

A physics-based puzzle/arcade game where you build a skyscraper by stacking falling floor blocks. Use physics to ensure stability and avoid collapse!

## Installation

1. Ensure Python 3.8+ is installed.
2. Clone or navigate to the project directory.
3. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

   This installs Arcade (for rendering), Pymunk (for physics), and pyfxr (for sounds).

## Running the Game

1. Activate the virtual environment (if not already):

   On macOS/Linux:

   ```
   source .venv/bin/activate
   ```

   On Windows:

   ```
   .venv\Scripts\activate
   ```

2. Run the main script:

   ```
   python main.py
   ```

   Or directly with the venv executable:

   ```
   .venv/bin/python main.py
   ```

   (Adjust path for Windows: .venv\Scripts\python.exe main.py)

3. Controls:
   - Left/Right Arrow Keys: Move block horizontally.
   - Up Arrow Key: Rotate block 90 degrees.
   - Spacebar: Fast drop.
   - ESC: Close the game.

4. Gameplay:
   - Stack blocks to build a tall, stable tower.
   - Score points for placements, with bonuses for centering and shape combos.
   - Game over if a block falls below the screen.

## Packaging for Distribution

To create a standalone executable (e.g., for Windows/Mac/Linux):

1. Install PyInstaller:

   ```
   pip install pyinstaller
   ```

2. Package the game:

   ```
   pyinstaller --onefile --windowed main.py
   ```

   - `--onefile`: Bundles everything into a single executable.
   - `--windowed`: Hides the console window (suitable for games).

3. The executable will be in the `dist/` folder. Test it on target platforms.

Note: Packaging may require additional steps for platform-specific dependencies (e.g., SDL for Arcade). For cross-platform, consider using tools like Briefcase or building on each OS.

## Development

- Editor: Visual Studio Code recommended.
- Physics: Powered by Pymunk for realistic stacking and wobbling.
- Sounds: Retro effects via pyfxr.

## Future Features

- Difficulty progression (faster blocks, wind effects).
- Procedural city skyline background.
- High-score leaderboard.

Enjoy building your skyscraper!