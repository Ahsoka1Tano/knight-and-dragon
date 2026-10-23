"""Direct-file and PyInstaller entrypoint; works from any working directory."""
import os
from pathlib import Path
import sys

os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')
if not getattr(sys,'frozen',False):
    sys.path.insert(0,str(Path(__file__).resolve().parent.parent))

from pixel_knight_dragon.game import main

if __name__=='__main__':
    main()
