# Supe Examples

Comprehensive examples demonstrating Supe's browser automation and learning system capabilities.

## Directory Structure

```
examples/
├── browser/              # Browser automation (CDP - no Playwright!)
│   ├── demos/            # Ready-to-run browser demos
│   ├── mcp/              # MCP browser protocol examples
│   └── recording/        # Video/terminal recording scripts
└── learning/             # Learning system (INGEST + EXPLORE)
    ├── ingest/           # Learn from documentation
    ├── explore/          # Discover properties through experimentation
    │   └── mathematical/ # 20+ mathematical discovery examples
    └── tools/            # Learning system utilities
```

## Quick Start

### Browser Automation (No Playwright Required!)

```bash
# Run basic CDP browser demo
cd browser/demos
python basic_demo.py

# Run beautiful terminal demo with colors
python terminal_demo.py

# Record a demo video
cd ../recording
./record_demo_easy.sh
```

**📖 Full Guide:** [browser/README.md](browser/README.md)

### Learning System

```bash
# INGEST mode - Learn from documentation
cd learning/ingest
python learn_react_hooks.py

# EXPLORE mode - Discover mathematical properties
cd ../explore/mathematical/foundations
python discover_from_zero.py
```

**📖 Full Guide:** [learning/README.md](learning/README.md)

---

## Browser Automation (`/browser`)

Direct Chrome control via **Chrome DevTools Protocol (CDP)** - lightweight alternative to Playwright!

### Features

- ✅ Page navigation & content extraction
- ✅ JavaScript execution
- ✅ Form interaction & filling
- ✅ Screenshot capture
- ✅ Infinite scroll handling
- ✅ Cookie management
- ✅ **No Playwright dependency!**

### Demos Available

| Demo | Description | Duration |
|------|-------------|----------|
| `basic_demo.py` | All CDP features | ~30s |
| `terminal_demo.py` | Beautiful colored output | ~20s |
| `quick_demo.py` | Quick demonstration | ~30s |

### Recording Scripts

Create video demos automatically:
- `auto_record.py` - Automatic screen recording with ffmpeg
- `record_demo_easy.sh` - Interactive recording helper
- `record_terminal_demo.sh` - Terminal recording with asciinema

**Requirements:** `pip install websockets beautifulsoup4`

---

## Learning System (`/learning`)

Unified learning system with two complementary modes:

### INGEST Mode - Learn from Documentation

Extract knowledge from existing sources:
- Cornell-style notes (cue/notes/examples/summary)
- Concept extraction
- Question generation (4 types)
- Evidence collection with citations
- Self-testing validation

**Example:** `learning/ingest/learn_react_hooks.py`

### EXPLORE Mode - Discover Properties

Validate properties through formal experimentation:
- Parse testable claims
- Generate experiments
- Execute and validate
- Synthesize formal theorems
- Proof-of-work validation

**Example:** `learning/explore/mathematical/foundations/discover_from_zero.py`

### Mathematical Discovery Examples (20+)

Organized by mathematical domain:

```
explore/mathematical/
├── foundations/        # First principles, Peano axioms (4 examples)
├── arithmetic/         # Primes, modular arithmetic, number theory (3)
├── algebra/            # Abstract, linear, complex numbers (3)
├── geometry/           # Euclidean, trigonometry, topology (3)
├── analysis/           # Calculus, fractals (2)
├── discrete/           # Sets, graphs, information theory (3)
├── probability/        # Probability and statistics (1)
└── advanced/           # Higher-order patterns (1)
```

**Result Types:**
- **PROVEN** - High confidence (0.8-1.0)
- **CONJECTURE** - Likely true (0.5-0.8)
- **DISPROVEN** - Counterexample found
- **UNKNOWN** - Insufficient evidence

---

## Documentation

### Guides

| Guide | Description |
|-------|-------------|
| [Browser Automation](../docs/guides/browser_automation.md) | Complete CDP browser guide |
| [Terminal Recording](../docs/guides/terminal_recording.md) | Create terminal demos |
| [Mathematical Journey](../docs/guides/mathematical_journey.md) | Math discovery overview |
| [Geometry Guide](../docs/guides/geometry_guide.md) | Geometry exploration |
| [Modular Arithmetic](../docs/guides/modular_arithmetic_guide.md) | Modular math patterns |

### API Documentation

- [Learning System](../docs/learning_system.md) - Complete system docs
- [AB Memory](../docs/api/abmemory.md) - Memory system API
- [Tasc](../docs/api/tasc.md) - Task management

### System Overview

- [Learning System Summary](../LEARNING_SYSTEM_SUMMARY.md) - Quick overview
- [Main README](../README.md) - Project overview

---

## Installation

```bash
# Full installation with all dependencies
pip install -e .

# Or use uv (recommended)
uv pip install -e .

# Browser automation only
pip install websockets beautifulsoup4
```

---

## Example Output

### Browser Demo (Terminal)

```
══════════════════════════════════════════════════════════
                    CDP BROWSER DEMO
          Browser Automation Without Playwright!
══════════════════════════════════════════════════════════

[STEP 1] Navigate & Extract Content
  → Loading example.com...
  ✓ Page loaded successfully
  URL: https://example.com
  Title: Example Domain

[STEP 2] Execute JavaScript
  → Running document.title...
  ✓ Result: Example Domain
  ✓ Window: {"width":1200,"height":830}
```

### Learning Demo (EXPLORE Mode)

```python
Theorem: Addition is Commutative
Status: PROVEN
Confidence: 1.00

Proof:
  For all tested pairs (a, b) in domain N:
    a + b = b + a

  Verified through 50 experiments
  No counterexamples found

Evidence:
  - 1 + 2 = 2 + 1 = 3
  - 5 + 7 = 7 + 5 = 12
  - 100 + 200 = 200 + 100 = 300
```

---

## Running Examples

### Individual Example

```bash
python examples/browser/demos/terminal_demo.py
```

### Category

```bash
# Run all foundational math examples
cd examples/learning/explore/mathematical/foundations
for f in *.py; do python "$f"; done
```

### With Testing

```bash
pytest examples/ -v
```

---

## Custom Examples

### Browser Automation

```python
from tascer.plugins.browser import CDPBrowser

async with CDPBrowser(headless=True) as browser:
    result = await browser.get("https://example.com")
    print(result.soup.title.string)

    # Execute JavaScript
    title = await browser.evaluate("document.title")

    # Take screenshot
    await browser.get("https://example.com", take_screenshot=True)
```

### Learning System

```python
from supe import Supe

supe = Supe()

# INGEST: Learn from docs
result = await supe.learn(
    "How do React hooks work?",
    mode="ingest"
)

# EXPLORE: Test properties
result = await supe.learn(
    "Is addition commutative?",
    mode="explore"
)
```

---

## Contributing Examples

When adding new examples:

1. **Place** in appropriate directory (`browser/` or `learning/`)
2. **Document** with docstring explaining purpose
3. **Include** usage example in file header
4. **Update** relevant README.md
5. **Test** that it runs successfully

---

## Troubleshooting

### Browser: Black screen recordings

macOS requires Screen Recording permission. Use built-in recorder:
1. Press **Cmd+Shift+5**
2. Select recording area
3. Click Record
4. Run the demo
5. Stop recording

### Learning: No beliefs created

```python
# Check evidence collection
if result['evidence_count'] == 0:
    # Store source material first
    supe.memory.store_card(...)
```

### EXPLORE: Not finding properties

Ensure question is testable:
- ✅ Good: "Is addition commutative?"
- ❌ Bad: "Tell me about addition"

---

## Next Steps

1. 🌐 **Try browser automation** - `cd browser/demos && python terminal_demo.py`
2. 📚 **Explore learning** - `cd learning/explore/mathematical/foundations`
3. 🎥 **Record a demo** - `cd browser/recording && ./record_demo_easy.sh`
4. 📖 **Read the docs** - See [docs/learning_system.md](../docs/learning_system.md)
5. 🧪 **Run tests** - `pytest tests/test_learning*.py -v`
6. 🔨 **Build your own** - Use these examples as templates

---

## Key Features Summary

### Browser Automation
- ✅ No Playwright - Direct CDP control
- ✅ Lightweight - Minimal dependencies
- ✅ Fast - Direct WebSocket communication
- ✅ Full-featured - Navigation, JS, forms, screenshots

### Learning System
- ✅ Evidence-based - All beliefs require validation
- ✅ Cryptographic proof - Tascer validation
- ✅ Spaced repetition - SM-2 algorithm
- ✅ Cross-session - Persistent AB Memory
- ✅ Confidence scoring - Multi-factor (0.0-1.0)
- ✅ Formal proofs - Mathematical notation

Happy exploring! 🚀
