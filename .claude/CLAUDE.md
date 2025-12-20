# Supe Project - Claude Memory

## Project Overview

Supe is a cognitive memory system for AI agents with task management, learning, and proof-of-work validation. It combines structured memory (AB), task management (Tasc), safe command execution (Tascer), and a unified learning system into a complete AI agent framework.

**Key Components:**
- **AB Memory**: Structured storage with moments, cards, and buffers for cognitive memory
- **Tasc**: Task management system with plans and tracking
- **Tascer**: Safe command execution with proof generation and validation
- **Learning System**: Unified INGEST (documents) and EXPLORE (experiments) modes
- **LLM Proof-of-Work**: Validates AI agent actions through structured proofs
- **Browser Automation**: CDP-based browser control for web interactions

## Architecture

```
supe/
├── ab/              # AB Memory Engine (storage, search, agents)
│   ├── abdb.py      # Database layer
│   ├── models.py    # Data models
├── tasc/            # Task management (CLI, TUI, atoms)
├── tascer/          # Validation framework
│   ├── llm_proof.py       # LLM proof-of-work system
│   ├── proofs/            # Proof generators
│   ├── gates/             # Validation gates
│   ├── primitives/        # Observation primitives
│   ├── overlord/          # Decision loop
│   ├── plugins/browser/   # Browser automation
│   ├── action_registry.py # Action registry
│   ├── contracts.py       # Type contracts
│   └── ab_storage.py      # AB storage integration
├── supe/            # Unified CLI and core systems
│   ├── __init__.py  # Core initialization
│   ├── supe.py      # Main entry point
│   ├── learning/    # Learning system (INGEST + EXPLORE modes)
│   │   ├── models.py      # Data models (Question, Evidence, Belief, etc.)
│   │   ├── types.py       # Enums and types
│   │   ├── state_machine.py  # State machine orchestrator
│   │   ├── storage.py     # AB Memory integration
│   │   ├── modes/         # Mode-specific utilities
│   │   │   ├── ingest.py  # Cornell notes, concept extraction
│   │   │   └── explore.py # Theorem synthesis, experiments
│   │   ├── states/        # State implementations
│   │   │   ├── ingest_doc.py    # Document learning
│   │   │   ├── explore_env.py   # Experimental validation
│   │   │   ├── self_test.py     # Recall testing
│   │   │   ├── evaluate.py      # Confidence adjustment
│   │   │   ├── generate_followup.py  # Follow-up questions
│   │   │   └── schedule_review.py    # Spaced repetition
│   │   └── tasc_integration.py  # Proof-of-work validation
│   ├── learner.py   # Legacy learning system (deprecated)
│   ├── self_teach.py # Legacy self-teaching (deprecated)
│   ├── sensory.py   # Sensory input processing
│   └── subselves.py # Sub-agent management
└── scripts/         # Install/uninstall scripts
```

## Learning System

The unified learning system supports two complementary modes:

### INGEST Mode
Learn from existing documentation and knowledge sources:
- Extracts concepts from text and code
- Generates 4 types of questions (core, operational, constraint, impact)
- Creates Cornell-style notes with examples
- Evidence collection with citations
- Self-testing for validation

**Use Cases:**
- Learning from documentation
- Understanding codebases
- API usage patterns
- Conceptual knowledge

**Example:**
```python
result = await supe.learn("How do React hooks work?", mode="ingest")
# Returns: Cornell notes with cue/notes/examples/summaries
```

### EXPLORE Mode
Discover properties through experimentation and formal proof:
- Parses mathematical/testable claims
- Generates and executes experiments
- Validates properties (commutative, associative, etc.)
- Synthesizes theorems with formal proofs
- Identifies counterexamples

**Use Cases:**
- Mathematical property discovery
- Algorithm behavior validation
- System property testing
- Hypothesis validation

**Example:**
```python
result = await supe.learn("Is addition commutative?", mode="explore")
# Returns: Theorem with PROVEN/DISPROVEN/CONJECTURE status
```

### State Machine Architecture

Complete learning workflow (11 states):
```
INIT → SELECT_FOCUS_QUESTION → PLAN_EVIDENCE_STRATEGY →
├─ INGEST_DOC (docs/APIs) →
└─ EXPLORE_ENV (experiments) →
INTEGRATE_KNOWLEDGE → SELF_TEST → EVALUATE_CONFIDENCE →
GENERATE_FOLLOWUP_QUESTIONS → SCHEDULE_REVIEW → IDLE
```

### Key Features

- **Evidence-Based**: All beliefs require citations and validation
- **Spaced Repetition**: Automatic review scheduling (SM-2 algorithm)
- **Proof of Work**: Cryptographic validation via Tascer integration
- **Confidence Scoring**: Multi-factor confidence (0.0-1.0)
- **Cross-Session**: Persistent question queues and knowledge graphs

### Documentation & Examples

- **Full docs**: `docs/learning_system.md`
- **Examples**: `examples/` directory
  - `discover_math_from_zero.py` - Learn math from first principles
  - `learn_react_hooks.py` - INGEST mode with documentation
  - `compare_modes.py` - Side-by-side comparison

### Testing

```bash
# Run all learning tests (89 tests)
pytest tests/test_learning*.py tests/test_supe_learning_integration.py -v

# Quick validation
python examples/discover_math_from_zero.py
```

## Development Guidelines

### Code Style
- Python 3.10+ features are available
- Use type hints consistently
- Follow functional programming patterns where appropriate
- Keep functions focused and modular

### Testing
- Tests live in `tests/` directory
- Run tests with: `pytest`
- Linting: `ruff check .`

### Key Technologies
- **Database**: SQLite with structured schema (AB Memory)
- **Browser**: Chrome DevTools Protocol (CDP) via playwright
- **CLI**: Multiple entry points (supe, tasc, tascer)
- **Validation**: Proof-of-work system for AI agent actions

## Recent Work

### Modified Files
- `ab/abdb.py`: Database implementation
- `ab/models.py`: Data models
- `supe/__init__.py`: Core initialization
- `tascer/ab_storage.py`: AB storage integration
- `tascer/action_registry.py`: Action registry
- `tascer/contracts.py`: Type contracts
- `tascer/plugins/browser/__init__.py`: Browser plugin
- `tascer/plugins/browser/cdp_browser.py`: CDP browser implementation

### Recent Features
- Cosine similarity normalization fix
- Card stats initialization on store
- Browser automation with screenshot capabilities
- HackerNews scraping implementations

### New Files (Untracked)
- `scrape_hn.py`, `scrape_hn_full.py`, `scrape_hn_tasc.py`: HN scraping experiments
- `supe/learner.py`, `supe/self_teach.py`, `supe/sensory.py`, `supe/subselves.py`, `supe/supe.py`: New core systems
- `tascer/abilities/`: New abilities directory

## Installation

```bash
# With uv (recommended)
uv venv && source .venv/bin/activate
uv pip install -e .

# With pip
python -m venv .venv && source .venv/bin/activate
pip install -e .

# Quick install
./scripts/install.sh
```

## Common Tasks

### CLI Commands
```bash
# Supe - Unified interface
supe status              # System status
supe prove "pytest"      # Execute with proof
supe verify <proof-id>   # Verify a proof
supe run "npm test"      # Safe command execution

# Tasc - Task management
tasc save "description"  # Save work as a tasc
tasc list                # List all tascs
tasc recall "search"     # Find past work
tasc plan file.md        # Track a plan
tasc ui                  # Launch interactive TUI

# Tascer - Safety & validation
tascer run "command"     # Run with safety checks
tascer check "command"   # Check if command is safe
tascer checkpoint        # Create checkpoint
tascer rollback          # Rollback changes
tascer sandbox enter     # Enter sandbox mode
tascer benchmark         # Run capability benchmarks
```

### Development
```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check .

# Build docs
uv pip install -e ".[docs]"
mkdocs serve
```

## Important Considerations

### Security
- Commands run through Tascer are validated and sandboxed
- Proof-of-work ensures AI agents follow structured plans
- Browser automation runs in controlled environments

### Performance
- AB Memory uses efficient cosine similarity search
- Browser operations capture screenshots for debugging
- Task storage optimized for quick recall

### Git
- Main branch: `main`
- Working directory data stored in `.tascer/`
- Screenshots saved to `.tascer/screenshots/`
- Consider adding `.tascer/` to `.gitignore` if not already present

## Notes

This project implements a novel approach to AI agent memory and validation. The combination of structured memory (AB), task tracking (Tasc), and proof-of-work validation (Tascer) provides a robust foundation for reliable AI agent systems.

The browser automation capabilities via CDP enable web scraping and interaction tasks, as demonstrated by the HackerNews scraping implementations.
