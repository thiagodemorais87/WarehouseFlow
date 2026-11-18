"""Compila a extensão Cython do motor (inplace em optimization/).

Uso (a partir de backend/):

    pip install cython
    python build_optimization_native.py build_ext --inplace
"""

from __future__ import annotations

from pathlib import Path

from setuptools import Extension, setup

try:
    from Cython.Build import cythonize
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Cython não instalado. Rode: pip install cython\n"
        f"Detalhe: {exc}"
    ) from exc

HERE = Path(__file__).resolve().parent
PYX = HERE / "optimization" / "_native.pyx"

extensions = [
    Extension(
        name="optimization._native",
        sources=[str(PYX)],
    )
]

setup(
    name="warehouseflow-optimization-native",
    ext_modules=cythonize(extensions, language_level="3"),
)
