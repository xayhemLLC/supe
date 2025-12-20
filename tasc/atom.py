"""Definition of the Atom class and decoding helpers.

Atoms are the fundamental binary units used in the Tasc engine. Each
``Atom`` consists of a prefix index identifying its ``AtomType`` and a
payload of raw bytes. The prefix index is encoded as a varint
(see ``tasc.varint``) and indicates how to interpret the payload
via the ``AtomTypeRegistry`` defined in ``tasc.atomtypes``.

This module defines the ``Atom`` dataclass with methods to encode
itself into bytes and to decode its payload using the registered
codec. It also provides a helper function ``decode_atom`` to parse
an Atom from a byte buffer and return the remaining offset.
"""

from dataclasses import dataclass
from typing import Any, Tuple

from .atomtypes import registry, AtomType
from .varint import encode_varint, decode_varint


@dataclass
class Atom:
    """A binary-encoded value with a prefix index and payload.

    The ``pindex`` field identifies which ``AtomType`` should be used
    to interpret the payload. The ``payload`` contains the raw bytes
    representing the value. For primitive types, the payload is the
    encoded representation of a Python value. For composite types, the
    payload is itself an encoded sequence of nested ATOMs or custom
    binary structures.

    The ``encode`` method serialises the Atom into bytes using varint
    encoding for the prefix and payload length, followed by the raw
    payload. The ``decode_value`` method uses the ``AtomType``'s
    decoder to convert the payload back into a Python value.
    """

    pindex: int
    payload: bytes

    def encode(self) -> bytes:
        """Serialise this Atom into bytes.

        The result is the concatenation of the prefix index (varint),
        the payload length (varint), and the raw payload bytes.
        """
        prefix = encode_varint(self.pindex)
        length = encode_varint(len(self.payload))
        return prefix + length + self.payload

    def decode_value(self) -> Any:
        """Decode the payload into a Python value using the AtomType codec.

        Returns:
            The decoded Python value.

        Raises:
            ValueError: If no decoder is defined for the AtomType.
        """
        atom_type: AtomType = registry.get_by_index(self.pindex)
        if atom_type.decoder is None:
            raise ValueError(f"No decoder defined for atomtype {atom_type.name}")
        return atom_type.decoder(self.payload)

    @classmethod
    def from_value(cls, atom_type: AtomType, value: Any) -> "Atom":
        """Construct an Atom from a Python value and an AtomType.

        Args:
            atom_type: The AtomType corresponding to the value. Must
                provide an encoder function for primitive types.
            value: The Python value to encode.

        Returns:
            A new ``Atom`` instance.

        Raises:
            ValueError: If no encoder is defined for the given AtomType.
        """
        if atom_type.encoder is None:
            raise ValueError(f"No encoder defined for atomtype {atom_type.name}")
        payload = atom_type.encoder(value)
        return cls(pindex=atom_type.pindex, payload=payload)


def decode_atom(buf: bytes, offset: int = 0) -> Tuple[Atom, int]:
    """Decode an Atom from a byte buffer starting at ``offset``.

    Args:
        buf: A buffer containing zero or more encoded Atoms.
        offset: The index within ``buf`` to begin decoding.

    Returns:
        A tuple containing the decoded ``Atom`` and the next offset
        immediately after the end of the atom.

    Raises:
        ValueError: If the buffer ends unexpectedly or the payload
            length extends beyond the buffer.
    """
    pindex, off1 = decode_varint(buf, offset)
    length, off2 = decode_varint(buf, off1)
    if off2 + length > len(buf):
        raise ValueError("Payload length extends beyond buffer")
    payload = buf[off2 : off2 + length]
    return Atom(pindex=pindex, payload=payload), off2 + length