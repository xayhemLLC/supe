# 🚀 Supe Docs - Quick Start Guide

**Don't know where to start?** Follow this path:

```
┌─────────────────────────────────────────────────────────────┐
│                    NEW TO SUPE?                              │
│                                                               │
│  1. Read README.md (5 min)                                   │
│     ↓                                                         │
│  2. Check MASTER_DOCS.md (10 min)                           │
│     ↓                                                         │
│  3. Try quickstart (15 min)                                  │
│     ↓                                                         │
│  4. Pick your path below ↓                                   │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 Choose Your Adventure

### Path 1: Build an AI Agent with Memory
```
┌──────────────────────────────────────┐
│ 1. docs/ab-memory-faq.md            │ ← Start here
│ 2. docs/tutorials/ai_agent_memory.md│
│ 3. docs/api/abmemory.md             │
│ 4. examples/ (try examples!)        │
└──────────────────────────────────────┘
```
**Time:** ~1 hour | **Difficulty:** ⭐⭐☆☆☆

### Path 2: Task Management & Tracking
```
┌──────────────────────────────────────┐
│ 1. docs/api/tasc.md                 │ ← Start here
│ 2. .agent/workflows/creating-       │
│    validatable-tascs.md             │
│ 3. Try: tasc save "my work"         │
└──────────────────────────────────────┘
```
**Time:** ~30 min | **Difficulty:** ⭐☆☆☆☆

### Path 3: AI Reasoning & Problem Solving
```
┌──────────────────────────────────────┐
│ 1. docs/REASONING_TAXONOMY.md       │ ← Start here
│ 2. supe/reasoning/scripts/README.md │ ← NEW!
│ 3. Try: python scripts/              │
│    solve_problem.py "problem"       │
│ 4. docs/ADAPTIVE_REASONING.md       │
└──────────────────────────────────────┘
```
**Time:** ~45 min | **Difficulty:** ⭐⭐⭐☆☆

### Path 4: AI Self-Learning System
```
┌──────────────────────────────────────┐
│ 1. docs/learning_system.md          │ ← Start here
│ 2. examples/learning/                │
│    discover_math_from_zero.py       │
│ 3. examples/learning/                │
│    learn_react_hooks.py             │
└──────────────────────────────────────┘
```
**Time:** ~1.5 hours | **Difficulty:** ⭐⭐⭐⭐☆

### Path 5: Browser Automation
```
┌──────────────────────────────────────┐
│ 1. docs/guides/browser_automation.md│ ← Start here
│ 2. examples/browser/                │
│ 3. scrape_hn.py (example)           │
└──────────────────────────────────────┘
```
**Time:** ~45 min | **Difficulty:** ⭐⭐⭐☆☆

### Path 6: Safe Command Execution
```
┌──────────────────────────────────────┐
│ 1. docs/tascer_plugins.md           │ ← Start here
│ 2. .agent/workflows/proof-of-work.md│
│ 3. Try: tascer check "command"      │
└──────────────────────────────────────┘
```
**Time:** ~30 min | **Difficulty:** ⭐⭐☆☆☆

## 📚 Essential Docs (Read These First)

1. **[README.md](README.md)** - Project overview (5 min)
2. **[MASTER_DOCS.md](MASTER_DOCS.md)** - Complete navigation (10 min) ⭐ **BOOKMARK THIS**
3. **[docs/quickstart.md](docs/quickstart.md)** - Get started (15 min)
4. **[.claude/CLAUDE.md](.claude/CLAUDE.md)** - For AI agents (5 min)

## 🗺️ Documentation Map

```
Supe Docs
│
├─── 📖 Start Here
│    ├── README.md ⭐ START
│    ├── MASTER_DOCS.md ⭐ NAVIGATION HUB
│    ├── docs/quickstart.md
│    └── docs/installation.md
│
├─── 🏗️ Core Systems
│    ├── AB Memory (docs/ab-memory-faq.md)
│    ├── Tasc (docs/api/tasc.md)
│    └── Tascer (docs/tascer_plugins.md)
│
├─── ⚡ Advanced Features
│    ├── Reasoning (docs/REASONING_TAXONOMY.md)
│    │   └── Capabilities ⭐ NEW (supe/reasoning/scripts/README.md)
│    └── Learning (docs/learning_system.md)
│
├─── 🎓 Tutorials & Examples
│    ├── docs/tutorials/
│    ├── examples/
│    └── .agent/workflows/
│
├─── 📖 API Reference
│    └── docs/api/
│
└─── 🔬 Specialized
     ├── ARC-AGI (docs/ARC_USER_GUIDE.md)
     ├── Browser (docs/guides/browser_automation.md)
     └── Math Learning (docs/guides/mathematical_journey.md)
```

## ⚡ Quick Commands

**See what's available:**
```bash
supe status                    # System overview
python scripts/list_capabilities.sh  # Reasoning capabilities
tasc list                      # Your tasks
tascer benchmark               # Available commands
```

**Try examples:**
```bash
# AI Learning
python examples/learning/discover_math_from_zero.py

# Problem Solving (NEW!)
python scripts/solve_problem.py "scan polymarket for opportunities"

# Browser Automation
python scrape_hn.py
```

## 🎯 By Role

### For Developers
1. [Installation](docs/installation.md)
2. [API Reference](docs/api/)
3. [Examples](examples/)

### For Researchers
1. [Learning System](docs/learning_system.md)
2. [ARC-AGI](docs/ARC_USER_GUIDE.md)
3. [Reasoning Taxonomy](docs/REASONING_TAXONOMY.md)

### For AI Agents
1. [.claude/CLAUDE.md](.claude/CLAUDE.md)
2. [Agent Workflows](.agent/workflows/)
3. [MASTER_DOCS.md](MASTER_DOCS.md)

### For Users
1. [README.md](README.md)
2. [Quickstart](docs/quickstart.md)
3. [Tutorials](docs/tutorials/)

## 🆘 Still Lost?

**I want to...**

- Build AI with memory → [Path 1](#path-1-build-an-ai-agent-with-memory)
- Manage tasks → [Path 2](#path-2-task-management--tracking)
- Solve problems → [Path 3](#path-3-ai-reasoning--problem-solving) ⭐ **NEW**
- Make AI learn → [Path 4](#path-4-ai-self-learning-system)
- Automate browsers → [Path 5](#path-5-browser-automation)
- Execute safely → [Path 6](#path-6-safe-command-execution)

**Help! I'm overwhelmed:**
1. Just read [README.md](README.md)
2. Try one CLI command: `supe status`
3. Come back when you need more

**I like exploring:**
Browse [MASTER_DOCS.md](MASTER_DOCS.md) - it has everything organized

**I want hands-on:**
Jump straight to [examples/](examples/) and run code

## 💡 Pro Tips

1. **Bookmark MASTER_DOCS.md** - It's your map
2. **Start with one path** - Don't try to learn everything at once
3. **Run examples** - Best way to understand
4. **Use the CLI** - See what's actually available
5. **Read summaries** - *_SUMMARY.md files explain implementations

## 📊 Documentation Stats

- **Total docs:** 90+ markdown files
- **Core systems:** 3 (AB, Tasc, Tascer)
- **Major features:** 6+ (Learning, Reasoning, Browser, etc.)
- **Examples:** 15+ working examples
- **Tutorials:** 10+ step-by-step guides
- **API docs:** Complete reference

**Most important files:**
1. MASTER_DOCS.md ⭐ **The Map**
2. README.md (Overview)
3. docs/quickstart.md (Get Started)
4. Your chosen path above

---

**Ready?** Pick a path above or head to [MASTER_DOCS.md](MASTER_DOCS.md) 🚀
