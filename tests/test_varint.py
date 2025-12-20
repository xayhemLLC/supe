"""Unit tests for varint encoding and decoding functions."""

import pytest

from tasc.varint import encode_varint, decode_varint


@pytest.mark.parametrize(
    "value",
    [0, 1, 2, 10, 127, 128, 255, 256, 16384, 2**32, 2**63 - 1],
)
def test_varint_roundtrip(value: int) -> None:
    """Round-trip encode and decode for various integer values."""
    encoded = encode_varint(value)
    decoded, offset = decode_varint(encoded, 0)
    assert decoded == value
    assert offset == len(encoded)


def test_varint_negative_raises() -> None:
    """Encoding a negative integer should raise a ValueError."""
    with pytest.raises(ValueError):
        encode_varint(-1)


def test_varint_truncated_buffer_raises() -> None:
    """Truncating the buffer should cause decode to raise ValueError."""
    encoded = encode_varint(300)
    truncated = encoded[:-1]
    with pytest.raises(ValueError):
        decode_varint(truncated, 0)


def test_varint_offset_handling() -> None:
    """Decoding multiple varints in sequence should handle offsets correctly."""
    v1, v2 = 123, 45678
    e1 = encode_varint(v1)
    e2 = encode_varint(v2)
    buf = e1 + e2
    d1, off1 = decode_varint(buf, 0)
    d2, off2 = decode_varint(buf, off1)
    assert d1 == v1
    assert d2 == v2
    assert off2 == len(buf)