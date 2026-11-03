"""Seed the guarded synthetic demo; never loads production configuration first."""
from pathlib import Path
import os
import sys
os.environ["PYTHON_DOTENV_DISABLED"]="1"
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.acceptance.demo import main
raise SystemExit(main())
