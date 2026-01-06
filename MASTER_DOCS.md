# 🎯 Supe Master Documentation

**The complete guide to everything in Supe.**

This is your central hub for navigating all of Supe's capabilities. Start here, then dive into specific topics.

> 💡 **Feeling overwhelmed?** Try [DOCS_QUICK_START.md](DOCS_QUICK_START.md) for guided learning paths!

---

## 📚 Table of Contents

1. [**Start Here**](#start-here) - New to Supe? Begin here
2. [**Core Systems**](#core-systems) - The three pillars of Supe
3. [**Advanced Features**](#advanced-features) - Power user capabilities
4. [**Reasoning & Learning**](#reasoning--learning) - AI reasoning systems
5. [**Integration Guides**](#integration-guides) - Connect Supe with other tools
6. [**API Reference**](#api-reference) - Detailed API documentation
7. [**Examples & Tutorials**](#examples--tutorials) - Learn by doing
8. [**Specialized Topics**](#specialized-topics) - Deep dives

---

## 🚀 Start Here

**New to Supe?** Read these first:

- [**README.md**](README.md) - Overview, quick install, and basic CLI usage
- [**docs/quickstart.md**](docs/quickstart.md) - Get up and running in 5 minutes
- [**docs/installation.md**](docs/installation.md) - Detailed installation guide
- [**.claude/CLAUDE.md**](.claude/CLAUDE.md) - Project overview for AI agents

**Quick decision guide:**
- 💾 Need memory for AI agents? → [AB Memory](#ab-memory)
- 📋 Need task management? → [Tasc](#tasc)
- ✅ Need validated execution? → [Tascer](#tascer)
- 🧠 Building reasoning systems? → [Reasoning System](#reasoning-system)
- 🎓 Want AI to learn? → [Learning System](#learning-system)

---

## 🏗️ Core Systems

Supe has three main pillars:

### AB Memory
**Cognitive memory system for AI agents**

- [**docs/ab-memory-faq.md**](docs/ab-memory-faq.md) - Common questions and answers
- [**docs/api/abmemory.md**](docs/api/abmemory.md) - API reference
- [**docs/api/models.md**](docs/api/models.md) - Data models (Moment, Card, Buffer)
- [**docs/tutorials/ai_agent_memory.md**](docs/tutorials/ai_agent_memory.md) - Tutorial: AI agent memory
- [**docs/tutorials/knowledge_graph.md**](docs/tutorials/knowledge_graph.md) - Tutorial: Knowledge graphs

**What it does:**
- Structured storage (moments, cards, buffers)
- Memory physics (strength-based recall with decay)
- Semantic search and similarity
- Knowledge graph traversal
- Self-agents for cognitive behaviors

### Tasc
**Task management with structured tracking**

- [**docs/api/tasc.md**](docs/api/tasc.md) - API reference
- [**.agent/workflows/creating-validatable-tascs.md**](.agent/workflows/creating-validatable-tascs.md) - Creating TASCs
- CLI: `tasc save`, `tasc list`, `tasc recall`, `tasc ui`

**What it does:**
- Save and track work sessions
- Organize tasks hierarchically
- Recall past work by semantic search
- Interactive TUI for task management
- Integration with AB Memory

### Tascer
**Safe command execution with proof-of-work**

- [**docs/tascer_plugins.md**](docs/tascer_plugins.md) - Plugin system
- [**.agent/workflows/proof-of-work.md**](.agent/workflows/proof-of-work.md) - Proof-of-work validation
- [**docs/guides/browser_automation.md**](docs/guides/browser_automation.md) - Browser automation plugin
- CLI: `tascer run`, `tascer check`, `tascer benchmark`

**What it does:**
- Validate commands before execution
- Generate cryptographic proofs of execution
- Plugin system for capabilities
- Browser automation (CDP-based)
- Checkpoint/rollback system

---

## ⚡ Advanced Features

### Reasoning System
**Structured problem-solving with TASC format**

- [**docs/REASONING_TAXONOMY.md**](docs/REASONING_TAXONOMY.md) - Types of reasoning
- [**docs/ADAPTIVE_REASONING.md**](docs/ADAPTIVE_REASONING.md) - Adaptive reasoning
- [**supe/reasoning/scripts/README.md**](supe/reasoning/scripts/README.md) - Capability scripts ⭐ **NEW**
- [**reasoning_journal.md**](reasoning_journal.md) - Development journal

**Components:**
- **Problem Solver**: Decomposes and solves problems step-by-step
- **Critiquer**: Reviews reasoning for errors and gaps
- **Evidence Collector**: Gathers and validates evidence
- **Capabilities System**: Extensible scripts for specialized tasks ⭐ **NEW**

**Try it:**
```bash
python scripts/solve_problem.py "your problem" --verbose
python scripts/list_capabilities.sh  # See available capabilities
```

### Learning System
**AI self-teaching with evidence-based validation**

- [**docs/learning_system.md**](docs/learning_system.md) - Complete guide
- [**LEARNING_SYSTEM_SUMMARY.md**](LEARNING_SYSTEM_SUMMARY.md) - Implementation summary
- [**docs/evidence_based_validation.md**](docs/evidence_based_validation.md) - Evidence validation
- [**examples/learning/**](examples/learning/) - Working examples

**Two modes:**
1. **INGEST Mode**: Learn from documentation and code
   - Cornell-style notes
   - Concept extraction
   - Self-testing

2. **EXPLORE Mode**: Discover properties through experimentation
   - Mathematical property discovery
   - Theorem synthesis with proofs
   - Hypothesis validation

**State machine:**
```
INIT → SELECT_FOCUS_QUESTION → PLAN_EVIDENCE_STRATEGY →
├─ INGEST_DOC (docs/APIs) →
└─ EXPLORE_ENV (experiments) →
INTEGRATE_KNOWLEDGE → SELF_TEST → EVALUATE_CONFIDENCE →
GENERATE_FOLLOWUP_QUESTIONS → SCHEDULE_REVIEW → IDLE
```

**Examples:**
- `examples/discover_math_from_zero.py` - Learn math from first principles
- `examples/learn_react_hooks.py` - INGEST mode demo
- `examples/compare_modes.py` - Side-by-side comparison

---

## 🔌 Integration Guides

### Claude Integration
- [**docs/cursor-claude-integration.md**](docs/cursor-claude-integration.md) - Cursor/Claude setup
- [**.agent/how-agents-work.md**](.agent/how-agents-work.md) - Agent architecture
- [**.agent/README.md**](.agent/README.md) - Agent workflows

### MCP (Model Context Protocol)
- [**docs/MCP_INTEGRATION.md**](docs/MCP_INTEGRATION.md) - MCP server integration
- Enables cross-IDE agent memory

### Cloud Deployment
- [**docs/cloud-deployment.md**](docs/cloud-deployment.md) - Docker, Kubernetes, cloud setup

---

## 📖 API Reference

### Core APIs
- [**docs/api/abmemory.md**](docs/api/abmemory.md) - ABMemory class
- [**docs/api/models.md**](docs/api/models.md) - Data models
- [**docs/api/tasc.md**](docs/api/tasc.md) - Task management
- [**docs/api/search.md**](docs/api/search.md) - Search and similarity
- [**docs/api/self_agents.md**](docs/api/self_agents.md) - Cognitive agents
- [**docs/api/transforms.md**](docs/api/transforms.md) - Buffer transforms

### Python API Examples
```python
# AB Memory
from ab import ABMemory, Buffer
memory = ABMemory("db.sqlite")
card = memory.store_card(label="note", buffers=[...])

# Tasc
from tasc import TaskManager
tm = TaskManager(memory)
task = tm.create_task("implement auth")

# Reasoning
from supe.reasoning.subagents import ReasoningPipeline
pipeline = ReasoningPipeline(memory)
result = await pipeline.run(problem_text="...")
```

---

## 🎓 Examples & Tutorials

### Tutorials
- [**docs/tutorials/index.md**](docs/tutorials/index.md) - Tutorial index
- [**docs/tutorials/ai_agent_memory.md**](docs/tutorials/ai_agent_memory.md) - Build AI agent memory
- [**docs/tutorials/knowledge_graph.md**](docs/tutorials/knowledge_graph.md) - Knowledge graphs
- [**docs/tutorials/image_recall.md**](docs/tutorials/image_recall.md) - Store and recall images

### Working Examples
- [**examples/**](examples/) - All examples
- [**examples/learning/**](examples/learning/) - Learning system demos
- [**examples/browser/**](examples/browser/) - Browser automation
- Browser automation: HackerNews scraping (`scrape_hn*.py`)

### Agent Workflows
- [**.agent/workflows/ab-memory.md**](.agent/workflows/ab-memory.md) - Memory workflows
- [**.agent/workflows/browser-plugin.md**](.agent/workflows/browser-plugin.md) - Browser automation
- [**.agent/workflows/codebase-analysis.md**](.agent/workflows/codebase-analysis.md) - Code analysis
- [**.agent/workflows/debug-mode.md**](.agent/workflows/debug-mode.md) - Debugging
- [**.agent/workflows/llm-plan-generation.md**](.agent/workflows/llm-plan-generation.md) - Plan generation
- [**.agent/workflows/run-tests.md**](.agent/workflows/run-tests.md) - Test execution

---

## 🔬 Specialized Topics

### ARC-AGI Challenge
**AI reasoning benchmark implementation**

- [**docs/ARC_USER_GUIDE.md**](docs/ARC_USER_GUIDE.md) - User guide ⭐ **Start here**
- [**docs/ARC_AGI_APPROACH.md**](docs/ARC_AGI_APPROACH.md) - Overall approach
- [**docs/ARC_PROGRESS_SUMMARY.md**](docs/ARC_PROGRESS_SUMMARY.md) - Progress summary
- Phase implementations:
  - [ARC_PHASE1_COMPLETE.md](docs/ARC_PHASE1_COMPLETE.md)
  - [ARC_PHASE2_COMPLETE.md](docs/ARC_PHASE2_COMPLETE.md)
  - [ARC_PHASE3_COMPLETE.md](docs/ARC_PHASE3_COMPLETE.md)
  - [ARC_PHASE4_COMPLETE.md](docs/ARC_PHASE4_COMPLETE.md)
  - [ARC_PHASE5_COMPLETE.md](docs/ARC_PHASE5_COMPLETE.md)
- [**docs/ARC_REAL_WORLD_RESULTS.md**](docs/ARC_REAL_WORLD_RESULTS.md) - Real-world results
- [**docs/ARC_SESSION_SUMMARY.md**](docs/ARC_SESSION_SUMMARY.md) - Session summary

### Mathematical Learning
- [**docs/guides/mathematical_journey.md**](docs/guides/mathematical_journey.md) - Math learning journey
- [**docs/guides/modular_arithmetic_guide.md**](docs/guides/modular_arithmetic_guide.md) - Modular arithmetic
- [**docs/guides/geometry_guide.md**](docs/guides/geometry_guide.md) - Geometry guide

### Card Relations & Validation
- [**docs/card_relations_proposal.md**](docs/card_relations_proposal.md) - Card relations design
- [**CARD_RELATIONS_IMPLEMENTATION.md**](CARD_RELATIONS_IMPLEMENTATION.md) - Implementation
- [**VALIDATION_AND_RELATIONS_SUMMARY.md**](VALIDATION_AND_RELATIONS_SUMMARY.md) - Summary

### Terminal Recording
- [**docs/guides/terminal_recording.md**](docs/guides/terminal_recording.md) - Record terminal sessions

### System Architecture
- [**docs/SYSTEM_ARCHITECTURE_VISUAL.txt**](docs/SYSTEM_ARCHITECTURE_VISUAL.txt) - ASCII architecture diagram
- [**docs/factory_v0_spec.md**](docs/factory_v0_spec.md) - Factory pattern spec

---

## 📊 Implementation Summaries

Development journey docs (chronological):

1. [**REORGANIZATION_SUMMARY.md**](REORGANIZATION_SUMMARY.md) - Codebase reorganization
2. [**COMPLETE_IMPLEMENTATION_SUMMARY.md**](COMPLETE_IMPLEMENTATION_SUMMARY.md) - Complete implementation
3. [**LEARNING_SYSTEM_SUMMARY.md**](LEARNING_SYSTEM_SUMMARY.md) - Learning system
4. [**EVIDENCE_VALIDATION_IMPLEMENTATION.md**](EVIDENCE_VALIDATION_IMPLEMENTATION.md) - Evidence validation
5. [**CARD_RELATIONS_IMPLEMENTATION.md**](CARD_RELATIONS_IMPLEMENTATION.md) - Card relations
6. [**VALIDATION_AND_RELATIONS_SUMMARY.md**](VALIDATION_AND_RELATIONS_SUMMARY.md) - Validation summary
7. [**PHASES_6_2_AND_7_IMPLEMENTATION.md**](PHASES_6_2_AND_7_IMPLEMENTATION.md) - Phases 6.2-7
8. [**CONTINUOUS_LEARNING_SUMMARY.md**](CONTINUOUS_LEARNING_SUMMARY.md) - Continuous learning
9. [**REASONING_CAPABILITIES_IMPLEMENTATION.md**](REASONING_CAPABILITIES_IMPLEMENTATION.md) - Reasoning capabilities

---

## 🎯 Quick Navigation by Use Case

### "I want to..."

**Build an AI agent with memory**
→ [AB Memory](#ab-memory) + [AI Agent Memory Tutorial](docs/tutorials/ai_agent_memory.md)

**Track tasks and work sessions**
→ [Tasc](#tasc) + [Creating TASCs](.agent/workflows/creating-validatable-tascs.md)

**Execute commands safely with validation**
→ [Tascer](#tascer) + [Proof-of-Work](.agent/workflows/proof-of-work.md)

**Build a reasoning system**
→ [Reasoning System](#reasoning-system) + [Reasoning Taxonomy](docs/REASONING_TAXONOMY.md)

**Make AI learn from documentation**
→ [Learning System](#learning-system) INGEST mode + [Examples](examples/learning/)

**Discover mathematical properties**
→ [Learning System](#learning-system) EXPLORE mode + [Math Journey](docs/guides/mathematical_journey.md)

**Automate browser tasks**
→ [Browser Plugin](docs/guides/browser_automation.md) + [Examples](examples/browser/)

**Add specialized problem-solving capabilities** ⭐ **NEW**
→ [Capability Scripts](supe/reasoning/scripts/README.md)

**Solve ARC-AGI challenges**
→ [ARC User Guide](docs/ARC_USER_GUIDE.md)

**Deploy to production**
→ [Cloud Deployment](docs/cloud-deployment.md)

---

## 🔍 Search Tips

**Finding specific topics:**
```bash
# Search all docs
grep -r "your topic" docs/

# List all markdown files
find docs/ -name "*.md"

# View doc structure
tree docs/
```

**Common searches:**
- Memory storage → `ab-memory-faq.md`, `api/abmemory.md`
- Task management → `api/tasc.md`
- Proof generation → `workflows/proof-of-work.md`
- Learning modes → `learning_system.md`
- Browser automation → `guides/browser_automation.md`
- API usage → `api/` directory

---

## 🆘 Still Lost?

**Start with the basics:**
1. Read [README.md](README.md) - 5 minutes
2. Try [docs/quickstart.md](docs/quickstart.md) - 10 minutes
3. Check [.claude/CLAUDE.md](.claude/CLAUDE.md) - Project overview

**For specific needs:**
- Memory? → [AB Memory FAQ](docs/ab-memory-faq.md)
- Tasks? → [Tasc API](docs/api/tasc.md)
- Learning? → [Learning System](docs/learning_system.md)
- Reasoning? → [Reasoning Taxonomy](docs/REASONING_TAXONOMY.md)
- Examples? → [examples/](examples/)

**Get hands-on:**
```bash
# Try the CLI
supe status
tasc list
tascer benchmark

# Run examples
python examples/learning/discover_math_from_zero.py
python scripts/solve_problem.py "your problem"

# List capabilities
python scripts/list_capabilities.sh
```

---

## 📝 Documentation Status

- ✅ Complete: Core systems (AB, Tasc, Tascer)
- ✅ Complete: Learning system
- ✅ Complete: Reasoning system
- ✅ Complete: Capability scripts ⭐ **NEW**
- ✅ Complete: ARC-AGI implementation
- ✅ Complete: Browser automation
- 🚧 In Progress: Additional tutorials
- 📋 Planned: Video tutorials
- 📋 Planned: Interactive examples

---

**Last Updated:** 2026-01-06
**Version:** 1.0.0
**Maintained by:** Supe Development Team

---

## 💡 Pro Tips

1. **Bookmark this file** - It's your map to everything
2. **Start small** - Pick one system and master it before moving on
3. **Run examples** - The `examples/` directory is your friend
4. **Use the CLI** - Fastest way to understand capabilities
5. **Check summaries** - Implementation summaries explain the "why"
6. **Agent workflows** - `.agent/workflows/` shows practical patterns

**Most useful docs for beginners:**
1. [README.md](README.md) - Project overview
2. [docs/quickstart.md](docs/quickstart.md) - Get started fast
3. [docs/ab-memory-faq.md](docs/ab-memory-faq.md) - Memory basics
4. [examples/](examples/) - Working code
5. [supe/reasoning/scripts/README.md](supe/reasoning/scripts/README.md) - Capability scripts

**Most useful docs for advanced users:**
1. [docs/learning_system.md](docs/learning_system.md) - Full learning system
2. [docs/REASONING_TAXONOMY.md](docs/REASONING_TAXONOMY.md) - Reasoning types
3. [docs/ARC_USER_GUIDE.md](docs/ARC_USER_GUIDE.md) - ARC-AGI guide
4. [.agent/workflows/](..agent/workflows/) - Agent patterns
5. [docs/api/](docs/api/) - Full API reference

---

**Happy exploring! 🚀**
