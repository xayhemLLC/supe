# Installation

## Requirements

- Python 3.8 or higher
- No external dependencies (uses Python standard library)

## Install from Source

```bash
# Clone the repository
git clone https://github.com/user/supe.git
cd supe

# Install in development mode
pip install -e .
```

## Quick Verification

```python
from ab import ABMemory, Buffer

# Create in-memory database
memory = ABMemory(":memory:")

# Create a test card
card = memory.store_card(
    label="test",
    buffers=[Buffer(name="hello", payload=b"world", headers={})]
)

print(f"Created card {card.id}")
# Output: Created card 1
```

## Optional Dependencies

For full documentation support:

```bash
pip install mkdocs mkdocs-material mkdocstrings[python]
```

For running benchmarks:

```bash
# No additional dependencies required
python -c "from ab.benchmark import run_benchmarks; from ab import ABMemory; run_benchmarks(ABMemory(':memory:'))"
```
