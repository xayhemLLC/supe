"""Tests for universal pair, list and object structures."""

from tasc.atomtypes import registry
from tasc.atom import Atom
from tasc.u2 import U2
from tasc.ulist import UList
from tasc.uobj import UObject


def test_u2_string_pair_roundtrip() -> None:
    """Ensure a u2 of strings encodes and decodes correctly."""
    u2 = U2.from_strings("foo", "bar")
    encoded = u2.encode()
    decoded, offset = U2.decode(encoded, 0)
    assert offset == len(encoded)
    assert decoded.decode_key_as_string() == "foo"
    assert decoded.decode_value_as_string() == "bar"


def test_ulist_roundtrip_multiple_atoms() -> None:
    """A UList of several string atoms should round-trip without loss."""
    string_type = registry.get_by_name("string")
    a1 = Atom.from_value(string_type, "one")
    a2 = Atom.from_value(string_type, "two")
    a3 = Atom.from_value(string_type, "three")
    ulist = UList(elements=[a1, a2, a3])
    encoded = ulist.encode()
    decoded_ulist, offset = UList.decode(encoded, 0)
    assert offset == len(encoded)
    vals = [atom.decode_value() for atom in decoded_ulist.elements]
    assert vals == ["one", "two", "three"]


def test_uobject_from_dict_roundtrip() -> None:
    """UObject should correctly round-trip from dict → ulist → dict."""
    d = {"a": "1", "b": "2", "c": "three"}
    uobj = UObject.from_dict_of_strings(d)
    ulist = uobj.to_ulist()
    decoded_uobj = UObject.from_ulist(ulist)
    back = decoded_uobj.to_dict_of_strings()
    assert back == d