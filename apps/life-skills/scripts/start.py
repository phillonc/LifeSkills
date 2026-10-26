"""Create runtime folders and start the app without installing packages."""
from pathlib import Path
import os
import runpy

app = Path(__file__).resolve().parents[1]
(app / 'data').mkdir(exist_ok=True)
os.chdir(app)
runpy.run_path(str(app / 'server.py'), run_name='__main__')
