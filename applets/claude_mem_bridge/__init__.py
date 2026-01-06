"""Claude-Mem Bridge Applet.

A mini-app that bridges claude-mem's SQLite database with Tree-Web memory
structures, enabling neural-style memory traversal and semantic search.

Components:
- bridge.py: Main ClaudeMemBridge class for importing/searching
- neural.py: NeuralMemory with Hebbian learning
- buffers.py: Buffer handling with proper text normalization
- tui.py: Terminal UI for browsing cards
- web.py: Web UI for browsing cards

Usage:
    # Python API
    from applets.claude_mem_bridge import ClaudeMemBridge, NeuralMemory

    bridge = ClaudeMemBridge()
    bridge.import_all(limit=100)
    results = bridge.hybrid_search("OAuth authentication")

    # Terminal UI
    python -m applets.claude_mem_bridge tui

    # Web UI
    python -m applets.claude_mem_bridge web
"""

from .bridge import ClaudeMemBridge, ClaudeMemConfig
from .neural import NeuralMemory, NeuralCard, NeuralLink

__all__ = [
    "ClaudeMemBridge",
    "ClaudeMemConfig",
    "NeuralMemory",
    "NeuralCard",
    "NeuralLink",
]
