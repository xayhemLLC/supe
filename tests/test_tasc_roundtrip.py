"""Tests for round-tripping Tasc objects through encoding and decoding."""

import pytest

from tasc.tasc import Tasc
from tasc.atom import decode_atom, Atom
from tasc.atomtypes import registry


def test_tasc_basic_roundtrip() -> None:
    """A populated Tasc should encode and decode without loss."""
    original = Tasc(
        id="TASC-CORE-001",
        status="queued",
        title="Implement atomtype registry and prefix index",
        additional_notes="First foundational Tasc for ATOM engine.",
        testing_instructions="See user stories US-E1-01.",
        desired_outcome="Stable, persisted atomtype registry with round-trip tests.",
        dependencies=["META-IMPLEMENT-001", "US-E1-01"],
    )
    atom = original.to_atom()
    encoded = atom.encode()
    decoded_atom, offset = decode_atom(encoded, 0)
    assert offset == len(encoded)
    tasc_type = registry.get_by_name("tasc")
    assert decoded_atom.pindex == tasc_type.pindex
    reconstructed = Tasc.from_atom(decoded_atom)
    assert reconstructed == original


def test_tasc_empty_dependencies_and_minimal_fields() -> None:
    """A Tasc with minimal fields should round-trip correctly."""
    t = Tasc(
        id="TASC-MIN-001",
        status="draft",
        title="Minimal tasc",
        additional_notes="",
        testing_instructions="",
        desired_outcome="",
        dependencies=[],
    )
    atom = t.to_atom()
    decoded_atom, _ = decode_atom(atom.encode(), 0)
    reconstructed = Tasc.from_atom(decoded_atom)
    assert reconstructed == t


def test_tasc_missing_kind_raises() -> None:
    """Tampering with the 'kind' field should cause decoding to fail."""
    t = Tasc(
        id="TASC-KIND-ERR",
        status="draft",
        title="Should fail kind check",
        additional_notes="",
        testing_instructions="",
        desired_outcome="",
        dependencies=[],
    )
    atom = t.to_atom()
    decoded_atom, _ = decode_atom(atom.encode(), 0)
    # Decode to UList/UObject to modify the 'kind' field
    from tasc.ulist import UList
    from tasc.uobj import UObject
    ulist, _ = UList.decode(decoded_atom.payload, 0)
    uobj = UObject.from_ulist(ulist)
    data = uobj.to_dict_of_strings()
    data["kind"] = "not_tasc"
    tampered_uobj = UObject.from_dict_of_strings(data)
    tampered_ulist = tampered_uobj.to_ulist()
    payload = tampered_ulist.encode()
    tasc_type = registry.get_by_name("tasc")
    # Use Atom.from_value to build a tampered atom
    tampered_atom = Atom.from_value(tasc_type, payload)
    with pytest.raises(ValueError):
        Tasc.from_atom(tampered_atom)