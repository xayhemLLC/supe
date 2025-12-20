"""Tests for the Atom class and decoding helpers."""

import pytest

from tasc.atom import Atom, decode_atom
from tasc.atomtypes import registry


def test_atom_string_roundtrip() -> None:
    """Encoding and decoding a string atom should round-trip correctly."""
    string_type = registry.get_by_name("string")
    a = Atom.from_value(string_type, "hello world")
    encoded = a.encode()
    decoded_atom, offset = decode_atom(encoded, 0)
    assert offset == len(encoded)
    assert decoded_atom.pindex == a.pindex
    assert decoded_atom.decode_value() == "hello world"


def test_atom_int64_roundtrip_edge_values() -> None:
    """Round-trip encoding/decoding of boundary values for int64."""
    int_type = registry.get_by_name("int64")
    for v in [-(2**63), -1, 0, 1, 2**63 - 1]:
        atom = Atom.from_value(int_type, v)
        encoded = atom.encode()
        decoded_atom, offset = decode_atom(encoded, 0)
        assert offset == len(encoded)
        assert decoded_atom.decode_value() == v


def test_atom_int64_overflow_raises() -> None:
    """Values outside the 64-bit range should raise OverflowError."""
    int_type = registry.get_by_name("int64")
    with pytest.raises(OverflowError):
        Atom.from_value(int_type, 2**63)
    with pytest.raises(OverflowError):
        Atom.from_value(int_type, -(2**63) - 1)


def test_decode_atom_with_truncated_payload_raises() -> None:
    """Truncating the payload should raise a ValueError during decoding."""
    string_type = registry.get_by_name("string")
    a = Atom.from_value(string_type, "abc")
    encoded = a.encode()
    truncated = encoded[:-1]
    with pytest.raises(ValueError):
        decode_atom(truncated, 0)