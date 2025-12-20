"""Universal list (ulist) definition.

The universal list is a homogenous sequence of ATOMs. Each element
may itself be any data type encoded as an ATOM. The list is encoded
as a varint representing the number of elements, followed by the
encoding of each element in sequence. Decoding reverses this process
and returns both the constructed ``UList`` and the offset after the
entire list.

Lists are used for encoding arrays of ATOMs, storing sequences in
universal objects, or as the top-level payload of a Tasc. This
structure deliberately avoids specifying the type of the list’s
elements, leaving that to the consumer or to richer metadata in
surrounding structures.
"""

from dataclasses import dataclass
from typing import List, Tuple

from .atom import Atom, decode_atom
from .varint import encode_varint, decode_varint


@dataclass
class UList:
    """A sequence of ``Atom`` elements encoded with a length prefix."""

    elements: List[Atom]

    def encode(self) -> bytes:
        """Encode this list into bytes.

        The encoding is the varint-encoded count of elements followed
        by the encoded form of each element.
        """
        out = bytearray()
        out += encode_varint(len(self.elements))
        for atom in self.elements:
            out += atom.encode()
        return bytes(out)

    @classmethod
    def decode(cls, buf: bytes, offset: int = 0) -> Tuple["UList", int]:
        """Decode a universal list from a buffer starting at ``offset``.

        Args:
            buf: The buffer containing one or more lists.
            offset: The starting index within ``buf`` to decode from.

        Returns:
            A tuple of the decoded ``UList`` and the next offset after
            the list.
        """
        count, off = decode_varint(buf, offset)
        elements: List[Atom] = []
        for _ in range(count):
            atom, off = decode_atom(buf, off)
            elements.append(atom)
        return cls(elements=elements), off