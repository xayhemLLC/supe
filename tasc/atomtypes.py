"""Definition and registry of Atom types.

The TASC core library relies on a flexible system for encoding and
decoding different data types into a binary format. Each data type is
represented by an ``AtomType`` instance which includes information
about its name, kind (primitive, composite, list, or ref), and optional
encoder/decoder functions. The ``AtomTypeRegistry`` class manages
registrations of these types and allows lookups by name or prefix
index (``pindex``).

In addition to the registry, this module defines a set of default
atomtypes used throughout the TASC engine, including booleans,
integers, floats, UTF-8 strings, binary blobs, references, and core
structured types such as universal lists, pairs, objects, and Tascs.

The module is deliberately self-contained and does not import any
application-specific code. Other modules (such as ``atom`` or
``uobj``) rely on the registry but do not register types
themselves. See ``init_default_atomtypes`` for the initialisation
routine invoked on import.
"""

from dataclasses import dataclass
from typing import Any, Dict, Callable, Optional

Encoder = Callable[[Any], bytes]
Decoder = Callable[[bytes], Any]


@dataclass
class AtomType:
    """A definition of a data type that can be encoded as an ATOM.

    Each ``AtomType`` defines how to interpret the payload bytes of an
    ``Atom``. Primitive types (e.g., booleans, integers) include
    encoder/decoder functions that map Python values to bytes and back.
    Composite types (e.g., ``u2``, ``ulist``, ``uobj``, ``tasc``)
    simply pass through raw bytes, as higher-level logic handles their
    composition.

    Attributes:
        pindex: A non-negative integer used as the prefix index in the
            varint encoding. Each registered type must have a unique
            ``pindex``.
        name: A human-readable identifier for the type.
        kind: One of ``"primitive"``, ``"composite"``, ``"list"``,
            or ``"ref"``. This field is informational only.
        params: A dictionary for additional type parameters. Not used
            by the core implementation but reserved for future
            extensions (e.g., fixed-length integers).
        version: Version number of the type definition. Currently unused.
        encoder: Optional callable to convert a Python value into
            bytes. Must be provided for primitive types.
        decoder: Optional callable to convert bytes back into a Python
            value. Must be provided for primitive types.
    """

    pindex: int
    name: str
    kind: str
    params: Dict[str, Any]
    version: int = 1
    encoder: Optional[Encoder] = None
    decoder: Optional[Decoder] = None


class AtomTypeRegistry:
    """Registry for looking up atom types by name or prefix index."""

    def __init__(self) -> None:
        self._by_index: Dict[int, AtomType] = {}
        self._by_name: Dict[str, AtomType] = {}

    def register(self, atom_type: AtomType) -> None:
        """Register an ``AtomType`` in the registry.

        Args:
            atom_type: The type definition to register. Its ``pindex`` and
                ``name`` must be unique within the registry.

        Raises:
            ValueError: If ``pindex`` or ``name`` has already been
                registered.
        """
        if atom_type.pindex in self._by_index:
            raise ValueError(f"pindex {atom_type.pindex} already registered")
        if atom_type.name in self._by_name:
            raise ValueError(f"name {atom_type.name} already registered")
        self._by_index[atom_type.pindex] = atom_type
        self._by_name[atom_type.name] = atom_type

    def get_by_index(self, pindex: int) -> AtomType:
        """Look up an ``AtomType`` by its prefix index.

        Args:
            pindex: The prefix index of the desired atom type.

        Returns:
            The corresponding ``AtomType``.

        Raises:
            KeyError: If no type is registered for ``pindex``.
        """
        if pindex not in self._by_index:
            raise KeyError(f"Unknown atomtype index {pindex}")
        return self._by_index[pindex]

    def get_by_name(self, name: str) -> AtomType:
        """Look up an ``AtomType`` by its name.

        Args:
            name: The name of the desired atom type.

        Returns:
            The corresponding ``AtomType``.

        Raises:
            KeyError: If no type with ``name`` is registered.
        """
        if name not in self._by_name:
            raise KeyError(f"Unknown atomtype name {name}")
        return self._by_name[name]


# Singleton registry instance used throughout the package.
registry = AtomTypeRegistry()


# Primitive type encoders/decoders
def _encode_bool(v: Any) -> bytes:
    return b"\x01" if bool(v) else b"\x00"


def _decode_bool(b: bytes) -> bool:
    if len(b) != 1:
        raise ValueError("bool atom must be exactly 1 byte")
    return b != b"\x00"


def _encode_int64(v: Any) -> bytes:
    iv = int(v)
    # signed 64-bit, big-endian
    if iv < -(1 << 63) or iv > (1 << 63) - 1:
        raise OverflowError("int64 out of range")
    return iv.to_bytes(8, byteorder="big", signed=True)


def _decode_int64(b: bytes) -> int:
    if len(b) != 8:
        raise ValueError("int64 atom must be exactly 8 bytes")
    return int.from_bytes(b, byteorder="big", signed=True)


def _encode_float64(v: Any) -> bytes:
    import struct
    fv = float(v)
    return struct.pack(">d", fv)


def _decode_float64(b: bytes) -> float:
    import struct
    if len(b) != 8:
        raise ValueError("float64 atom must be exactly 8 bytes")
    return struct.unpack(">d", b)[0]


def _encode_string(v: Any) -> bytes:
    s = str(v)
    return s.encode("utf-8")


def _decode_string(b: bytes) -> str:
    return b.decode("utf-8")


def _encode_binary(v: Any) -> bytes:
    if isinstance(v, (bytes, bytearray)):
        return bytes(v)
    raise TypeError("binary atom expects bytes/bytearray")


def _decode_binary(b: bytes) -> bytes:
    return b


# Composite types simply pass through raw bytes; encoding/decoding is
# handled at a higher level (e.g., ``u2`` or ``ulist`` classes).
def _encode_passthrough_bytes(v: Any) -> bytes:
    if isinstance(v, (bytes, bytearray)):
        return bytes(v)
    raise TypeError("composite atom expects raw bytes payload")


def _decode_passthrough_bytes(b: bytes) -> bytes:
    return b


def init_default_atomtypes() -> None:
    """Initialise the registry with the core atomtype definitions.

    This function registers primitive types for booleans, signed
    64-bit integers, 64-bit floats, UTF-8 strings, binary blobs,
    references (treated as strings), and reserved composite types for
    universal lists, pairs, objects, and Tasc objects.
    """
    # Primitive types
    registry.register(
        AtomType(
            pindex=0,
            name="bool",
            kind="primitive",
            params={},
            encoder=_encode_bool,
            decoder=_decode_bool,
        )
    )
    registry.register(
        AtomType(
            pindex=1,
            name="int64",
            kind="primitive",
            params={},
            encoder=_encode_int64,
            decoder=_decode_int64,
        )
    )
    registry.register(
        AtomType(
            pindex=2,
            name="float64",
            kind="primitive",
            params={},
            encoder=_encode_float64,
            decoder=_decode_float64,
        )
    )
    registry.register(
        AtomType(
            pindex=3,
            name="string",
            kind="primitive",
            params={},
            encoder=_encode_string,
            decoder=_decode_string,
        )
    )
    registry.register(
        AtomType(
            pindex=4,
            name="binary",
            kind="primitive",
            params={},
            encoder=_encode_binary,
            decoder=_decode_binary,
        )
    )
    # References to other objects are encoded as strings (IDs).
    registry.register(
        AtomType(
            pindex=5,
            name="ref",
            kind="ref",
            params={},
            encoder=_encode_string,
            decoder=_decode_string,
        )
    )
    # Core structured types. These are stored as raw bytes; higher-level
    # constructs encode their fields into bytes and wrap them in ATOMs of
    # these types.
    registry.register(
        AtomType(
            pindex=6,
            name="ulist",
            kind="list",
            params={},
            encoder=_encode_passthrough_bytes,
            decoder=_decode_passthrough_bytes,
        )
    )
    registry.register(
        AtomType(
            pindex=7,
            name="u2",
            kind="composite",
            params={},
            encoder=_encode_passthrough_bytes,
            decoder=_decode_passthrough_bytes,
        )
    )
    registry.register(
        AtomType(
            pindex=8,
            name="uobj",
            kind="composite",
            params={},
            encoder=_encode_passthrough_bytes,
            decoder=_decode_passthrough_bytes,
        )
    )
    registry.register(
        AtomType(
            pindex=9,
            name="tasc",
            kind="composite",
            params={},
            encoder=_encode_passthrough_bytes,
            decoder=_decode_passthrough_bytes,
        )
    )
    # Evidence validation types
    registry.register(
        AtomType(
            pindex=10,
            name="evidence",
            kind="composite",
            params={},
            encoder=_encode_passthrough_bytes,
            decoder=_decode_passthrough_bytes,
        )
    )
    registry.register(
        AtomType(
            pindex=11,
            name="evidence_collection",
            kind="composite",
            params={},
            encoder=_encode_passthrough_bytes,
            decoder=_decode_passthrough_bytes,
        )
    )
    # Relation types for semantic network capabilities
    registry.register(
        AtomType(
            pindex=12,
            name="relation",
            kind="composite",
            params={},
            encoder=_encode_passthrough_bytes,
            decoder=_decode_passthrough_bytes,
        )
    )


# Invoke initialisation on import so the default types are available
init_default_atomtypes()