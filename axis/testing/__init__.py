"""
Testing package for golden vector verification
Ensures cross-platform determinism
"""

from .test_runner import GoldenVectorGenerator, GoldenVectorRunner

__all__ = ["GoldenVectorGenerator", "GoldenVectorRunner"]
