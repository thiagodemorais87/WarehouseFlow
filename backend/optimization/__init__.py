"""Motor de otimização de rotas de picking (puro Python, sem I/O)."""

from optimization.engine import optimize_route
from optimization.types import Location, OptimizationResult

__all__ = ["Location", "OptimizationResult", "optimize_route"]
