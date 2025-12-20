"""Standalone test runner for the TASC core library.

This script contains a set of unit tests equivalent to those defined
in the pytest-based test suite, but without relying on external
dependencies. Running this script executes all tests and reports
whether they pass or if any failures occur. The script returns a
non-zero exit code on failure.

You can execute this file directly via ``python validate_tasc.py``.
"""

import sys

# Import the necessary TASC core classes and helpers
from tasc.varint import encode_varint, decode_varint
from tasc.atomtypes import (
    registry,
    AtomTypeRegistry,
    AtomType,
    _encode_string,
    _decode_string,
)
from tasc.atom import Atom, decode_atom
from tasc.u2 import U2
from tasc.ulist import UList
from tasc.uobj import UObject
from tasc.tasc import Tasc


def assert_equal(a, b, message=""):
    if a != b:
        raise AssertionError(message or f"Expected {a!r} == {b!r}")


def test_varint_roundtrip():
    for value in [0, 1, 2, 10, 127, 128, 255, 256, 16384, 2**32, 2**63 - 1]:
        encoded = encode_varint(value)
        decoded, offset = decode_varint(encoded, 0)
        assert_equal(decoded, value, f"varint decoded value mismatch for {value}")
        assert_equal(offset, len(encoded), f"varint offset incorrect for {value}")


def test_varint_negative_raises():
    try:
        encode_varint(-1)
    except ValueError:
        pass
    else:
        raise AssertionError("encode_varint did not raise for negative input")


def test_varint_truncated_buffer_raises():
    encoded = encode_varint(300)
    truncated = encoded[:-1]
    try:
        decode_varint(truncated, 0)
    except ValueError:
        pass
    else:
        raise AssertionError("decode_varint did not raise for truncated buffer")


def test_varint_offset_handling():
    v1, v2 = 123, 45678
    e1 = encode_varint(v1)
    e2 = encode_varint(v2)
    buf = e1 + e2
    d1, off1 = decode_varint(buf, 0)
    d2, off2 = decode_varint(buf, off1)
    assert_equal(d1, v1, "First varint decode mismatch")
    assert_equal(d2, v2, "Second varint decode mismatch")
    assert_equal(off2, len(buf), "Offset after decoding both varints incorrect")


def test_atomtypes_primitives_registered():
    for name in ["bool", "int64", "float64", "string", "binary", "ref"]:
        atom_type = registry.get_by_name(name)
        assert_equal(atom_type.name, name, f"AtomType {name} not registered")


def test_atomtypes_duplicate_registration_raises():
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
    try:
        reg.register(t1)
    except ValueError:
        pass
    else:
        raise AssertionError("Duplicate registration did not raise ValueError")


def test_atomtypes_unknown_lookup_raises():
    reg = AtomTypeRegistry()
    try:
        reg.get_by_index(999)
    except KeyError:
        pass
    else:
        raise AssertionError("Lookup by unknown pindex did not raise KeyError")
    try:
        reg.get_by_name("nonexistent")
    except KeyError:
        pass
    else:
        raise AssertionError("Lookup by unknown name did not raise KeyError")


def test_atom_string_roundtrip():
    string_type = registry.get_by_name("string")
    a = Atom.from_value(string_type, "hello world")
    encoded = a.encode()
    decoded_atom, offset = decode_atom(encoded, 0)
    assert_equal(offset, len(encoded), "Offset after decoding string atom incorrect")
    assert_equal(decoded_atom.pindex, a.pindex, "pindex mismatch for string atom")
    assert_equal(decoded_atom.decode_value(), "hello world", "Decoded string mismatch")


def test_atom_int64_roundtrip_edge_values():
    int_type = registry.get_by_name("int64")
    for v in [-(2**63), -1, 0, 1, 2**63 - 1]:
        atom = Atom.from_value(int_type, v)
        encoded = atom.encode()
        decoded_atom, offset = decode_atom(encoded, 0)
        assert_equal(offset, len(encoded), f"Offset mismatch for int64 value {v}")
        assert_equal(decoded_atom.decode_value(), v, f"Decoded int64 mismatch for {v}")


def test_atom_int64_overflow_raises():
    int_type = registry.get_by_name("int64")
    try:
        Atom.from_value(int_type, 2**63)
    except OverflowError:
        pass
    else:
        raise AssertionError("OverflowError not raised for too large int64 value")
    try:
        Atom.from_value(int_type, -(2**63) - 1)
    except OverflowError:
        pass
    else:
        raise AssertionError("OverflowError not raised for too small int64 value")


def test_decode_atom_with_truncated_payload_raises():
    string_type = registry.get_by_name("string")
    a = Atom.from_value(string_type, "abc")
    encoded = a.encode()
    truncated = encoded[:-1]
    try:
        decode_atom(truncated, 0)
    except ValueError:
        pass
    else:
        raise AssertionError("decode_atom did not raise on truncated payload")


def test_u2_string_pair_roundtrip():
    u2 = U2.from_strings("foo", "bar")
    encoded = u2.encode()
    decoded, offset = U2.decode(encoded, 0)
    assert_equal(offset, len(encoded), "Offset mismatch for U2 pair")
    assert_equal(decoded.decode_key_as_string(), "foo", "U2 key mismatch")
    assert_equal(decoded.decode_value_as_string(), "bar", "U2 value mismatch")


def test_ulist_roundtrip_multiple_atoms():
    string_type = registry.get_by_name("string")
    a1 = Atom.from_value(string_type, "one")
    a2 = Atom.from_value(string_type, "two")
    a3 = Atom.from_value(string_type, "three")
    ulist = UList(elements=[a1, a2, a3])
    encoded = ulist.encode()
    decoded_ulist, offset = UList.decode(encoded, 0)
    assert_equal(offset, len(encoded), "Offset mismatch for UList")
    vals = [atom.decode_value() for atom in decoded_ulist.elements]
    assert_equal(vals, ["one", "two", "three"], "UList values mismatch")


def test_uobject_from_dict_roundtrip():
    d = {"a": "1", "b": "2", "c": "three"}
    uobj = UObject.from_dict_of_strings(d)
    ulist = uobj.to_ulist()
    decoded_uobj = UObject.from_ulist(ulist)
    back = decoded_uobj.to_dict_of_strings()
    assert_equal(back, d, "UObject round-trip mismatch")


def test_tasc_basic_roundtrip():
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
    assert_equal(offset, len(encoded), "Offset mismatch for Tasc encoding")
    tasc_type = registry.get_by_name("tasc")
    assert_equal(decoded_atom.pindex, tasc_type.pindex, "pindex mismatch for Tasc")
    reconstructed = Tasc.from_atom(decoded_atom)
    # Dataclass implements __eq__ for field comparison
    assert_equal(reconstructed, original, "Tasc reconstruction mismatch")


def test_tasc_empty_dependencies_and_minimal_fields():
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
    assert_equal(reconstructed, t, "Minimal Tasc reconstruction mismatch")


def test_tasc_missing_kind_raises():
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
    from tasc.ulist import UList as UL
    from tasc.uobj import UObject as UObj
    ulist, _ = UL.decode(decoded_atom.payload, 0)
    uobj = UObj.from_ulist(ulist)
    data = uobj.to_dict_of_strings()
    data["kind"] = "not_tasc"
    tampered_uobj = UObj.from_dict_of_strings(data)
    tampered_ulist = tampered_uobj.to_ulist()
    payload = tampered_ulist.encode()
    tasc_type = registry.get_by_name("tasc")
    tampered_atom = Atom.from_value(tasc_type, payload)
    try:
        Tasc.from_atom(tampered_atom)
    except ValueError:
        pass
    else:
        raise AssertionError("Tampered kind did not raise ValueError")


def run_all_tests() -> None:
    tests = [
        test_varint_roundtrip,
        test_varint_negative_raises,
        test_varint_truncated_buffer_raises,
        test_varint_offset_handling,
        test_atomtypes_primitives_registered,
        test_atomtypes_duplicate_registration_raises,
        test_atomtypes_unknown_lookup_raises,
        test_atom_string_roundtrip,
        test_atom_int64_roundtrip_edge_values,
        test_atom_int64_overflow_raises,
        test_decode_atom_with_truncated_payload_raises,
        test_u2_string_pair_roundtrip,
        test_ulist_roundtrip_multiple_atoms,
        test_uobject_from_dict_roundtrip,
        test_tasc_basic_roundtrip,
        test_tasc_empty_dependencies_and_minimal_fields,
        test_tasc_missing_kind_raises,
    ]
    failures = []
    for test_func in tests:
        try:
            test_func()
        except Exception as exc:
            failures.append((test_func.__name__, exc))
    if failures:
        print("Some tests failed:")
        for name, exc in failures:
            print(f" - {name}: {exc}")
        sys.exit(1)
    print("All tests passed!")


if __name__ == "__main__":
    run_all_tests()