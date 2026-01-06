# Claude Plan Generation for Tasc

**Updated:** 2026-01-06

Supe now uses **Claude (Anthropic API)** for AI-powered TascPlan generation instead of Codex.

---

## 🎯 What Changed

### Before
- Documentation mentioned "Codex, Cursor, Gemini" as examples
- No direct LLM integration for plan generation
- Users had to manually write TascPlans or integrate their own LLM

### After
- **Claude is now the default and recommended LLM** for plan generation
- Direct API integration via `anthropic` Python package
- Simple one-line function to generate complete, validatable plans
- CLI command for generating plans from the terminal
- Comprehensive documentation with examples

---

## 🚀 Quick Start

### Python API

```python
from tascer import generate_plan

# Generate a plan using Claude
result = generate_plan(
    goal="Fix the 500 error on the login endpoint",
    context="FastAPI app with JWT authentication",
    constraints=["Must maintain backwards compatibility"],
)

print(f"Plan: {result.plan.title}")
print(f"Confidence: {result.confidence:.0%}")

for tasc in result.plan.tascs:
    print(f"  - {tasc.title}")
```

### CLI Command

```bash
# Generate a plan from command line
tascer plan "Add dark mode to settings page" \
  --context "React app with TailwindCSS" \
  --constraint "Must work in all browsers" \
  --verbose

# Save the plan to file
tascer plan "Implement user authentication" \
  --context "Express.js API" \
  --save \
  --output .tascer/plans
```

---

## 📦 Installation

```bash
# Install anthropic package
pip install anthropic

# Set API key
export ANTHROPIC_API_KEY=your-key-here
```

---

## 🔧 Features

### 1. **Automatic Prompt Engineering**
Claude handles all the complexity of generating well-structured plans:
- Decomposes goals into executable steps
- Creates proper validation tests for each step
- Manages dependencies between tasks
- Adds approval gates for risky operations

### 2. **Confidence Scoring**
Every plan includes a confidence score (0-100%) and reasoning about the approach.

### 3. **Citation Support**
Plans can cite previous work and build on proven solutions.

### 4. **Customizable**
Fine-tune generation with parameters:
- `temperature`: Control creativity (0.0-1.0)
- `max_tascs`: Limit plan complexity
- `constraints`: Enforce requirements
- `context`: Provide codebase info

### 5. **CLI Integration**
Generate plans without writing any code:
```bash
tascer plan "your goal" --save --verbose --json
```

---

## 📄 Files Changed

### New Files
- `tascer/claude_planner.py` - Claude API integration
  - `ClaudePlanner` class
  - `generate_plan_with_claude()` convenience function
  - Streaming support

### Modified Files
- `tascer/llm_planner.py` - Added `generate_plan()` main entry point
- `tascer/__init__.py` - Export `generate_plan`
- `tascer/cli.py` - Added `tascer plan` command
- `.agent/workflows/llm-plan-generation.md` - Updated docs to reference Claude

---

## 🎓 Examples

### Example 1: Simple Plan Generation

```python
from tascer import generate_plan

plan = generate_plan(
    goal="Add pagination to the API",
    context="FastAPI REST API",
)

# Plan automatically includes:
# - Model/schema creation
# - Utility functions
# - Endpoint updates
# - Tests
# - Human approval gate
```

### Example 2: With Constraints

```python
plan = generate_plan(
    goal="Refactor authentication module",
    context="Express.js with JWT",
    constraints=[
        "Must maintain backwards compatibility",
        "Cannot break existing tests",
        "Must use existing database schema",
    ],
    max_tascs=6,
)
```

### Example 3: CLI with Full Options

```bash
tascer plan \
  "Implement rate limiting for API" \
  --context "FastAPI with Redis" \
  --constraint "Must handle 1000 req/sec" \
  --constraint "Should use sliding window" \
  --max-tascs 5 \
  --temperature 0.8 \
  --save \
  --verbose \
  --json
```

### Example 4: Streaming (Advanced)

```python
from tascer.claude_planner import ClaudePlanner

planner = ClaudePlanner()

for chunk in planner.generate_plan_streaming(request):
    if isinstance(chunk, str):
        # Print chunks as they arrive
        print(chunk, end="", flush=True)
    else:
        # Final result
        plan = chunk
```

---

## 🔍 How It Works

1. **User provides goal** - Natural language description
2. **Context gathering** - Optional codebase info, constraints
3. **Claude generation** - API call with structured prompt
4. **Parsing & validation** - Parse JSON, create TascPlan
5. **Return result** - Complete plan with confidence score

### Under the Hood

```
User Goal
    ↓
generate_plan()
    ↓
claude_planner.ClaudePlanner
    ↓
anthropic.messages.create()
    ↓
Parse JSON response
    ↓
create_plan()
    ↓
GeneratedPlan with TascPlan
```

---

## 🧪 Testing

Test the integration:

```bash
# Dry run (no API key required)
python test_claude_plan.py

# With API key
export ANTHROPIC_API_KEY=your-key
python test_claude_plan.py

# CLI test
tascer plan "your goal here"
```

Example output:
```
✅ Plan generated: Add Dark Mode Toggle to Settings Page
📊 Confidence: 92%
💭 Reasoning: This plan implements a complete dark mode solution...

📋 Tascs (6):
  1. Create dark mode context and provider
  2. Configure Tailwind CSS for dark mode
  3. Create dark mode toggle component
  4. Add system preference detection
  5. Integrate into settings page
  6. Human review before completion
```

---

## 📚 Documentation

- **Main API docs**: `.agent/workflows/llm-plan-generation.md`
- **Claude integration**: `tascer/claude_planner.py` (docstrings)
- **LLM planner**: `tascer/llm_planner.py` (docstrings)
- **CLI help**: `tascer plan --help`

---

## 🔮 Future Enhancements

Potential improvements:
- [ ] Support for other LLMs (GPT-4, Gemini) through same interface
- [ ] Plan templates for common patterns
- [ ] Interactive plan refinement
- [ ] Plan execution tracking and optimization
- [ ] Automatic plan improvement based on execution results
- [ ] Integration with AB Memory for learning from past plans

---

## 🎯 Why Claude?

**Claude Sonnet 4.5** was chosen because:

1. **Strong reasoning** - Excels at structured problem decomposition
2. **Long context** - Can handle large codebases (200k tokens)
3. **Instruction following** - Reliably generates valid JSON
4. **Safety** - Good at identifying risky operations
5. **Up-to-date** - Latest models with best capabilities

---

## 💡 Tips

1. **Provide context** - More context = better plans
2. **Use constraints** - Enforce requirements explicitly
3. **Start small** - Use `max_tascs=3-5` for simple goals
4. **Review plans** - Always review before executing
5. **Save plans** - Use `--save` for reusable templates
6. **Iterate** - Refine goal description if plan isn't right

---

## ❓ FAQ

**Q: Do I need an Anthropic API key?**
A: Yes. Set `ANTHROPIC_API_KEY` environment variable.

**Q: Can I use a different LLM?**
A: Yes, set `use_claude=False` and implement your own. The prompt generation is LLM-agnostic.

**Q: How much does it cost?**
A: Claude Sonnet 4.5 costs ~$3 per million input tokens, ~$15 per million output tokens. A typical plan generation uses ~2k input + 1k output tokens = $0.02.

**Q: Can I customize the prompt?**
A: Yes, edit `generate_plan_prompt()` in `llm_planner.py` or provide your own prompt template.

**Q: What models are supported?**
A: Default is `claude-sonnet-4-5-20250929`. You can specify any Claude model via the `model` parameter.

---

## 📝 License

Same as Supe (MIT)

---

**Questions?** Check the docs or file an issue!
