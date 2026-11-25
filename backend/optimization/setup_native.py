"""Wrapper: rode o build a partir de backend/ (evita sombrear stdlib `types`).

    cd backend
    python build_optimization_native.py build_ext --inplace
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
script = BACKEND / "build_optimization_native.py"
sys.argv = [str(script), "build_ext", "--inplace", *sys.argv[1:]]
# Executa com cwd=backend para o Extension resolver paths
import os

os.chdir(BACKEND)
runpy.run_path(str(script), run_name="__main__")
