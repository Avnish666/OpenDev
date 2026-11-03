"""Run explicit disposable-provider diagnostics without loading application dotenv."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.acceptance.providers import main
raise SystemExit(main())
