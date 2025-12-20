"""Utilities for encoding and decoding variable-length integers.

This module provides functions to encode and decode non-negative integers
using a little-endian continuation-bit format similar to Protocol
Buffers. Each byte encodes 7 bits of the integer, and the most
significant bit of each byte indicates whether there are more bytes to
come (1) or if it is the last byte (0). This allows small numbers to
use fewer bytes while still being able to represent arbitrarily large
integers (within reasonable limits).

The ``encode_varint`` function returns a ``bytes`` object
containing the varint representation. The ``decode_varint`` function
returns a two-tuple of the decoded integer and the next offset into
the buffer.
"""

from typing import Tuple


def encode_varint(value: int) -> bytes:
    """Encode a non-negative integer into varint format.

    Args:
        value: The integer to encode. Must be >= 0.

    Returns:
        A bytes object containing the varint-encoded value.

    Raises:
        ValueError: If ``value`` is negative.
    """
    if value < 0:
        raise ValueError("encode_varint only supports non-negative integers")
    out = bytearray()
    # Continue encoding 7 bits at a time until value is exhausted.
    while True:
        to_write = value & 0x7F
        value >>= 7
        # If more bits remain, set the continuation bit.
        if value:
            out.append(to_write | 0x80)
        else:
            out.append(to_write)
            break
    return bytes(out)


def decode_varint(buf: bytes, offset: int = 0) -> Tuple[int, int]:
    """Decode a varint from a buffer starting at ``offset``.

    Args:
        buf: The buffer containing the varint-encoded data.
        offset: The starting index within ``buf`` to begin decoding.

    Returns:
        A tuple containing the decoded integer and the next offset
        immediately after the varint.

    Raises:
        ValueError: If the buffer ends before the varint is fully
            decoded or if the varint appears to be unreasonably large.
    """
    shift = 0
    result = 0
    pos = offset
    # Loop until we encounter a byte without the continuation bit set.
    while True:
        if pos >= len(buf):
            raise ValueError("Buffer ended before varint was fully decoded")
        b = buf[pos]
        pos += 1
        # Accumulate the lower 7 bits of the byte.
        result |= ((b & 0x7F) << shift)
        # If the continuation bit is not set, we've reached the last byte.
        if not (b & 0x80):
            break
        shift += 7
        # Guard against shifting too far; unlikely in practice.
        if shift > 63:
            raise ValueError("Varint is too large")
    return result, pos