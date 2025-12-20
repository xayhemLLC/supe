"""Tests for the AtomType and AtomTypeRegistry functionality."""

import pytest

from tasc.atomtypes import (
    AtomType,
    AtomTypeRegistry,
    registry,
    init_default_atomtypes,
    _encode_string,
    _decode_string,
)


def test_primitives_registered() -> None:
    """Default primitive types should be registered on import."""
    for name in ["bool", "int64", "float64", "string", "binary", "ref"]:
        atom_type = registry.get_by_name(name)
        assert atom_type.name == name


def test_duplicate_registration_raises() -> None:
    """Registering the same pindex or name twice should raise ValueError."""
    reg = AtomTypeRegistry()
    t1 = AtomType(
        pindex=0,
        name="string",
        kind="primitive",
        params={},
        encoder=_encode_string,
        decoder=_decode_string,
    )
    reg.register(t1)
    # Duplicate name and index
    with pytest.raises(ValueError):
        reg.register(t1)


def test_unknown_lookup_raises() -> None:
    """Lookup of unknown types by name or index should raise KeyError."""
    reg = AtomTypeRegistry()
    with pytest.raises(KeyError):
        reg.get_by_index(999)
    with pytest.raises(KeyError):
        reg.get_by_name("nonexistent")