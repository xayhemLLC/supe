"""Transform system for buffer payloads.

This module implements the transform registry and execution engine for
AB buffers. Transforms are functions that process buffer payloads before
they are used in cognition. Each buffer can specify an ``exe`` field
containing one or more transform names.

Built-in transforms:
- ``identity``: No-op, returns payload unchanged
- ``len``: Returns the length of the payload as UTF-8 encoded string
- ``lower_text``: Lowercases text payload (UTF-8)
- ``upper_text``: Uppercases text payload (UTF-8)
- ``strip``: Strips whitespace from text payload

Transform chains are supported using pipe-delimited names:
    exe="lower_text|strip"
"""

from __future__ import annotations

from typing import Callable, Dict, Optional


# Type for transform functions: bytes -> bytes
TransformFunc = Callable[[bytes], bytes]


class TransformRegistry:
    """Registry for transform functions.

    Transforms are registered by name and can be looked up or executed
    on buffer payloads.
    """

    def __init__(self) -> None:
        self._transforms: Dict[str, TransformFunc] = {}
        self._register_builtins()

    def _register_builtins(self) -> None:
        """Register the built-in transforms."""
        self.register("identity", transform_identity)
        self.register("len", transform_len)
        self.register("lower_text", transform_lower_text)
        self.register("upper_text", transform_upper_text)
        self.register("strip", transform_strip)

    def register(self, name: str, func: TransformFunc) -> None:
        """Register a transform function by name.

        Args:
            name: The name to register the transform under.
            func: A callable that takes bytes and returns bytes.
        """
        self._transforms[name] = func

    def get(self, name: str) -> Optional[TransformFunc]:
        """Look up a transform by name.

        Returns:
            The transform function, or None if not found.
        """
        return self._transforms.get(name)

    def apply(self, name: str, payload: bytes) -> bytes:
        """Apply a single transform to a payload.

        Args:
            name: The transform name.
            payload: The payload bytes to transform.

        Returns:
            The transformed payload.

        Raises:
            ValueError: If the transform name is not registered.
        """
        func = self.get(name)
        if func is None:
            raise ValueError(f"Unknown transform: {name}")
        return func(payload)

    def apply_chain(self, exe: str, payload: bytes) -> bytes:
        """Apply a chain of transforms to a payload.

        Transform names are pipe-delimited. Each transform is applied
        in order from left to right.

        Args:
            exe: Pipe-delimited transform names (e.g., "lower_text|strip").
            payload: The payload bytes to transform.

        Returns:
            The transformed payload after all transforms are applied.
        """
        if not exe:
            return payload
        names = [n.strip() for n in exe.split("|") if n.strip()]
        result = payload
        for name in names:
            result = self.apply(name, result)
        return result

    def list_transforms(self) -> list:
        """Return a list of all registered transform names."""
        return list(self._transforms.keys())


# ---------------------------------------------------------------------------
# Built-in transform functions
# ---------------------------------------------------------------------------


def transform_identity(payload: bytes) -> bytes:
    """No-op transform: returns payload unchanged."""
    return payload


def transform_len(payload: bytes) -> bytes:
    """Returns the length of the payload as UTF-8 encoded number string."""
    length = len(payload)
    return str(length).encode("utf-8")


def transform_lower_text(payload: bytes) -> bytes:
    """Lowercases text payload (UTF-8)."""
    try:
        text = payload.decode("utf-8")
        return text.lower().encode("utf-8")
    except UnicodeDecodeError:
        # Not valid UTF-8, return unchanged
        return payload


def transform_upper_text(payload: bytes) -> bytes:
    """Uppercases text payload (UTF-8)."""
    try:
        text = payload.decode("utf-8")
        return text.upper().encode("utf-8")
    except UnicodeDecodeError:
        return payload


def transform_strip(payload: bytes) -> bytes:
    """Strips whitespace from text payload (UTF-8)."""
    try:
        text = payload.decode("utf-8")
        return text.strip().encode("utf-8")
    except UnicodeDecodeError:
        return payload


# ---------------------------------------------------------------------------
# Global registry instance
# ---------------------------------------------------------------------------

registry = TransformRegistry()


def apply_transform(exe: Optional[str], payload: bytes) -> bytes:
    """Convenience function to apply transforms using the global registry.

    Args:
        exe: Transform name(s), pipe-delimited for chains. None means no transform.
        payload: The payload bytes to transform.

    Returns:
        The transformed payload.
    """
    if exe is None or exe == "":
        return payload
    return registry.apply_chain(exe, payload)
