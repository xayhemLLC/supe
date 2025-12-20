"""Definition of the universal pair (u2) type.

The universal pair is a simple two-field structure consisting of a
``key`` and a ``value``. Both the key and value are represented as
``Atom`` instances, allowing the pair to store any type that can be
encoded as an Atom, including primitive types, composite structures,
lists, or references. The ``u2`` is the building block of universal
objects (``uobj``) which are maps of keys to values.

This module defines the ``U2`` dataclass with methods to encode the
pair into raw bytes (by concatenating the encodings of the two atoms)
and to decode a pair from a bytes buffer. It also provides helper
methods to construct a pair from strings (for convenience) and to
decode the key or value as a string when appropriate.
"""

from dataclasses import dataclass
from typing import Any, Tuple

from .atom import Atom, decode_atom
from .atomtypes import registry


@dataclass
class U2:
    """Universal pair of two atoms: ``key`` and ``value``.

    Both the key and value are stored as ATOMs. Keys are often strings
    (e.g., field names in universal objects), but they can be any
    atomtype. Values may be of any type supported by the registry.
    """

    key: Atom
    value: Atom

    def encode(self) -> bytes:
        """Encode this pair into bytes.

        The encoding is simply the concatenation of the encoded key and
        the encoded value. Decoding must be aware of the two atom
        boundaries, which is why ``decode`` returns both the pair and
        the next offset.
        """
        return self.key.encode() + self.value.encode()

    @classmethod
    def decode(cls, buf: bytes, offset: int = 0) -> Tuple["U2", int]:
        """Decode a universal pair from a buffer starting at ``offset``.

        Returns the decoded pair and the next offset after both atoms.
        """
        key_atom, off1 = decode_atom(buf, offset)
        val_atom, off2 = decode_atom(buf, off1)
        return cls(key=key_atom, value=val_atom), off2

    @classmethod
    def from_strings(cls, key: str, value: str) -> "U2":
        """Helper to build a pair where both key and value are strings.

        This is convenient for constructing universal objects with
        simple string fields. In more complex scenarios, keys or values
        may be other atom types and should be constructed manually via
        ``Atom.from_value``.
        """
        str_type = registry.get_by_name("string")
        key_atom = Atom.from_value(str_type, key)
        val_atom = Atom.from_value(str_type, value)
        return cls(key=key_atom, value=val_atom)

    def decode_key_as_string(self) -> str:
        """Decode the key atom as a Python string.

        This convenience method assumes the key is a ``string`` atom
        type. If the key is not a string, this will raise a
        ``TypeError``.
        """
        val = self.key.decode_value()
        if not isinstance(val, str):
            raise TypeError(f"Key is not a string: {type(val)}")
        return val

    def decode_value_as_string(self) -> str:
        """Decode the value atom as a Python string.

        This is intended for values that are strings. For other types,
        this will raise a ``TypeError``.
        """
        val = self.value.decode_value()
        if not isinstance(val, str):
            raise TypeError(f"Value is not a string: {type(val)}")
        return val