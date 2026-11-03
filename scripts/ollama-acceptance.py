"""Loopback diagnostics; never installs a runtime, pulls models or exposes an endpoint."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.acceptance.ollama import main
raise SystemExit(main())
