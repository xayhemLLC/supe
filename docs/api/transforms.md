# Transforms API Reference

Buffer payload transformation system.

## Core Functions

### apply_transform

Apply a transform (or chain) to payload data.

```python
from ab import apply_transform

# Single transform
result = apply_transform("lower_text", b"HELLO WORLD")
# b'hello world'

# Chained transforms (pipe-separated)
result = apply_transform("strip|lower_text", b"  HELLO  ")
# b'hello'
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `exe` | `str` | Transform name or chain |
| `payload` | `bytes` | Data to transform |

**Returns:** Transformed `bytes`

**Raises:** `ValueError` if transform not found

---

## Built-in Transforms

| Name | Description | Example |
|------|-------------|---------|
| `identity` | Returns payload unchanged | `b"hello"` → `b"hello"` |
| `len` | Returns byte length as string | `b"hello"` → `b"5"` |
| `lower_text` | Lowercase UTF-8 text | `b"HELLO"` → `b"hello"` |
| `upper_text` | Uppercase UTF-8 text | `b"hello"` → `b"HELLO"` |
| `strip` | Strip whitespace from text | `b"  hi  "` → `b"hi"` |

---

## Transform Registry

### TransformRegistry

Register and manage custom transforms.

```python
from ab import transform_registry

# List available transforms
names = transform_registry.list_transforms()
# ['identity', 'len', 'lower_text', 'upper_text', 'strip']

# Register a custom transform
def reverse_text(payload: bytes) -> bytes:
    return payload[::-1]

transform_registry.register("reverse", reverse_text)

# Use it
result = apply_transform("reverse", b"hello")
# b'olleh'
```

### Methods

| Method | Description |
|--------|-------------|
| `register(name, func)` | Add a new transform |
| `get(name)` | Get transform function |
| `list_transforms()` | List all names |
| `has(name)` | Check if exists |

---

## Transform Chains

Chains execute left-to-right, separated by `|`:

```python
# Strip whitespace, then lowercase
apply_transform("strip|lower_text", b"  HELLO  ")
# b'hello'

# Lowercase, then get length
apply_transform("lower_text|len", b"HELLO")
# b'5'
```

---

## Using with Cards

Transforms can be stored in buffer `exe` field:

```python
from ab import Buffer, ABMemory

memory = ABMemory(":memory:")

card = memory.store_card(
    label="text",
    buffers=[
        Buffer(
            name="content",
            payload=b"  RAW INPUT DATA  ",
            headers={},
            exe="strip|lower_text"  # Applied when processed
        )
    ]
)

# Manual application
buf = card.buffers[0]
if buf.exe:
    processed = apply_transform(buf.exe, buf.payload)
    # b'raw input data'
```

---

## Custom Transform Example

```python
from ab import transform_registry, apply_transform
import json

# JSON pretty-print transform
def json_pretty(payload: bytes) -> bytes:
    try:
        data = json.loads(payload.decode())
        return json.dumps(data, indent=2).encode()
    except json.JSONDecodeError:
        return payload

transform_registry.register("json_pretty", json_pretty)

# Use it
result = apply_transform("json_pretty", b'{"name":"test","value":123}')
# b'{\n  "name": "test",\n  "value": 123\n}'
```
