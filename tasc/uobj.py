"""Universal object (UObject) implementation.

Universal objects provide a simple key/value map abstraction built on
top of universal pairs (``u2``) and universal lists (``ulist``).
Keys are always strings in this implementation, while values are
stored as ``Atom`` instances. The object is encoded as a list of
``u2`` atoms; each pair is itself encoded into a ``u2`` atom whose
payload contains the concatenated encodings of its key and value.

When decoding a ``uobj``, the list of ``u2`` atoms is converted back
into a Python ``dict`` of strings to Atom values. Convenience methods
are provided to construct a ``UObject`` from a dictionary of strings
and to produce such a dictionary when all values decode to strings.
"""

from dataclasses import dataclass
from typing import Dict, Any

from .atom import Atom
from .atomtypes import registry
from .u2 import U2
from .ulist import UList


@dataclass
class UObject:
    """Universal object storing string keys and Atom values."""

    pairs: Dict[str, Atom]

    def to_ulist(self) -> UList:
        """Convert this object into a ``UList`` of ``u2`` atoms.

        Each key/value pair in the object becomes a ``u2`` atom whose
        payload is the encoded concatenation of its key and value atoms.
        The resulting list is unordered (dict iteration order) but
        deterministic within a single run.
        """
        u2_type = registry.get_by_name("u2")
        str_type = registry.get_by_name("string")
        items = []
        for key, value_atom in self.pairs.items():
            key_atom = Atom.from_value(str_type, key)
            u2 = U2(key=key_atom, value=value_atom)
            u2_bytes = u2.encode()
            u2_atom = Atom.from_value(u2_type, u2_bytes)
            items.append(u2_atom)
        return UList(elements=items)

    @classmethod
    def from_ulist(cls, ulist: UList) -> "UObject":
        """Decode a ``UObject`` from a ``UList`` of ``u2`` atoms."""
        result: Dict[str, Atom] = {}
        for u2_atom in ulist.elements:
            # The payload of a u2 atom is the raw encoding of the pair
            u2_bytes = u2_atom.payload
            u2, _ = U2.decode(u2_bytes, 0)
            key_str = u2.decode_key_as_string()
            result[key_str] = u2.value
        return cls(pairs=result)

    @classmethod
    def from_dict_of_strings(cls, d: Dict[str, str]) -> "UObject":
        """Create a ``UObject`` from a mapping of strings to strings."""
        str_type = registry.get_by_name("string")
        pairs: Dict[str, Atom] = {}
        for key, val in d.items():
            pairs[key] = Atom.from_value(str_type, val)
        return cls(pairs=pairs)

    def to_dict_of_strings(self) -> Dict[str, str]:
        """Return the object as a mapping of strings to strings.

        All values must decode to strings; otherwise a ``TypeError`` is raised.
        """
        out: Dict[str, str] = {}
        for key, atom_val in self.pairs.items():
            val = atom_val.decode_value()
            if not isinstance(val, str):
                raise TypeError(f"Value for key {key} is not a string: {type(val)}")
            out[key] = val
        return out