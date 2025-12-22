# Browser Automation Examples

Browser automation using **Chrome DevTools Protocol (CDP)** - no Playwright required!

## Directory Structure

```
browser/
├── demos/          # Ready-to-run demos
├── mcp/            # MCP browser protocol examples
└── recording/      # Recording scripts for creating demos
```

## Quick Start

### Run Basic Demo

```bash
cd examples/browser/demos
python basic_demo.py
```

### Run Terminal Demo (with colors!)

```bash
python terminal_demo.py
```

### Record a Demo

```bash
cd examples/browser/recording
./record_demo_easy.sh
```

## Demos

### `/demos` - Ready-to-Run Examples

| File | Description | Duration |
|------|-------------|----------|
| `basic_demo.py` | Complete demo of all CDP features | ~30s |
| `terminal_demo.py` | Beautiful terminal output with colors | ~20s |
| `quick_demo.py` | Quick 30-second demo | ~30s |
| `recording_demo.py` | Demo optimized for screen recording | ~35s |

### `/mcp` - Model Context Protocol

| File | Description |
|------|-------------|
| `mcp_demo.py` | MCP browser tool examples |
| `mcp_experiment.py` | MCP browser experimentation |
| `mcp_live_demo.py` | Live MCP demo template |
| `test_mcp.py` | MCP browser tests |

### `/recording` - Create Video Demos

| File | Description |
|------|-------------|
| `auto_record.py` | Automatic screen recording with ffmpeg |
| `record_demo_easy.sh` | Interactive recording helper |
| `record_macos.sh` | macOS-specific recording |
| `record_simple.sh` | Simple recording wrapper |
| `record_terminal_demo.sh` | Terminal recording with asciinema |

## Features Demonstrated

- ✅ Page navigation
- ✅ JavaScript execution
- ✅ Content scraping with BeautifulSoup
- ✅ Infinite scroll handling
- ✅ Form interaction
- ✅ Screenshot capture
- ✅ Cookie management

## Documentation

See [docs/guides/browser_automation.md](../../docs/guides/browser_automation.md) for complete documentation.

For terminal recording guide, see [docs/guides/terminal_recording.md](../../docs/guides/terminal_recording.md).

## Requirements

```bash
pip install websockets beautifulsoup4
```

## Key Advantages

- **No Playwright** - Direct Chrome control via CDP
- **Lightweight** - Minimal dependencies
- **Fast** - Direct WebSocket communication
- **Full-featured** - Everything you need for automation
