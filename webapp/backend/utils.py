"""Shared utilities for backend routers."""


def h3_int_to_hex(index: int) -> str:
    """Convert an H3 integer index to its hex string representation for h3-js."""
    return format(index, "x")
