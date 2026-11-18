"""Detecta se a extensão Cython do motor está disponível."""

from __future__ import annotations

try:
    from optimization import _native as _native_mod

    NATIVE_COMPILED = bool(getattr(_native_mod, "is_compiled", lambda: True)())
except ImportError:
    try:
        import _native as _native_mod  # inplace build no mesmo diretório

        NATIVE_COMPILED = bool(getattr(_native_mod, "is_compiled", lambda: True)())
    except ImportError:
        NATIVE_COMPILED = False


def native_compiled() -> bool:
    return NATIVE_COMPILED
