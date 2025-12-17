"""Tiny declarative compiler for RAI semantics models.

Goal:
- Declare schema once (Python class with fields)
- Generate semantic Concepts/Properties/Relationships and source bindings
- Make the common case easy; allow overrides for exceptions

This is intentionally minimal (v0) and currently used only for Observation.
"""

from .dsl import EntitySpec, Key, Prop, Ref
from .compile import compile_entity

__all__ = ["EntitySpec", "Key", "Prop", "Ref", "compile_entity"]
