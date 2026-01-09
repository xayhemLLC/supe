# Contributing to Supe

Thanks for your interest in contributing to Supe!

## Quick Start

```bash
# Clone and setup
git clone https://github.com/xayhemLLC/supe.git
cd supe
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Run tests
pytest tests/test_sdk_wrapper.py -v

# Run linter
ruff check .
```

## Ways to Contribute

### Report Bugs
Open an issue with:
- What you expected to happen
- What actually happened
- Steps to reproduce
- Python version and OS

### Suggest Features
Open an issue describing:
- The problem you're trying to solve
- Your proposed solution
- Any alternatives you considered

### Submit Code

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Run linter (`ruff check .`)
6. Commit with a clear message
7. Push and open a PR

## Code Style

- Python 3.10+ features are welcome
- Use type hints
- Follow existing patterns in the codebase
- Keep functions focused and modular

## Areas We'd Love Help With

- **More validation gates** - Command whitelists, rate limiting, cost tracking
- **Integrations** - LangChain, LlamaIndex, OpenAI SDK wrappers
- **Documentation** - Tutorials, examples, API docs
- **Testing** - Edge cases, integration tests

## Questions?

Open an issue or start a discussion. We're friendly!
