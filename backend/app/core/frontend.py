"""Optional same-origin static hosting for the reviewed combined image."""
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


def mount_frontend(app: FastAPI, directory: str | Path | None) -> None:
    if not directory:
        return
    root = Path(directory)
    if not (root / 'index.html').is_file():
        raise RuntimeError('Configured frontend build is missing')
    # Called after API registration. Hash routes need no arbitrary SPA fallback.
    app.mount('/', StaticFiles(directory=root, html=True), name='frontend')
