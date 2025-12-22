# Terminal Recording Guide

Beautiful terminal demo with colors, progress bars, and animations!

## Quick Start

```bash
cd /Users/chriscabral/Desktop/super/supe
./record_terminal_demo.sh
```

Choose option 1 (asciinema) - it's the easiest!

---

## Option 1: asciinema (Recommended)

**Records terminal sessions and makes them shareable!**

### Record

```bash
# Install if needed
pip install asciinema

# Record the demo
asciinema rec cdp_demo.cast -c "source .venv/bin/activate && python examples/cdp_browser_terminal_demo.py"
```

### Replay Locally

```bash
asciinema play cdp_demo.cast
```

### Share Online

```bash
# Upload to asciinema.org (free, shareable link)
asciinema upload cdp_demo.cast

# You get a URL like: https://asciinema.org/a/xxxxx
```

### Convert to GIF

```bash
# Install agg (asciinema GIF generator)
cargo install --git https://github.com/asciinema/agg

# Convert to GIF
agg cdp_demo.cast cdp_demo.gif --speed 1.5
```

**Output:** Animated GIF perfect for GitHub, docs, social media!

---

## Option 2: Screen Recording → GIF

Record your terminal with macOS built-in recorder:

```bash
# 1. Press Cmd+Shift+5
# 2. Select terminal window area
# 3. Click Record
# 4. Run the demo:
source .venv/bin/activate
python examples/cdp_browser_terminal_demo.py

# 5. Stop recording
# 6. Convert MOV → GIF:

cd ~/Desktop
ffmpeg -i "Screen Recording*.mov" \
  -vf "fps=10,scale=800:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" \
  cdp_terminal_demo.gif
```

---

## Option 3: Just the Terminal Demo

Run without recording to test:

```bash
cd /Users/chriscabral/Desktop/super/supe
source .venv/bin/activate
python examples/cdp_browser_terminal_demo.py
```

---

## What Makes This Demo Cool?

✓ **Colors** - Cyan headers, green checkmarks, yellow steps
✓ **Progress Bar** - Browser initialization animation
✓ **Scroll Animation** - Shows scrolling in action
✓ **Real-time Output** - See each action as it happens
✓ **Professional Look** - Like a DevOps tool demo

---

## Sharing Options

### 1. **asciinema.org** (Best for devs)
- Terminal recording that can be copied/pasted
- Shareable URL
- Free hosting
- Example: `asciinema upload cdp_demo.cast`

### 2. **GIF** (Best for docs/social)
- Works everywhere (GitHub, Twitter, docs)
- File size: ~2-5 MB
- Auto-plays

### 3. **Video (MP4)** (Best for presentations)
- Professional quality
- Can add narration
- YouTube/Vimeo ready

---

## Pro Tips

### Make Terminal Look Better

```bash
# Increase font size for recording
# Cmd+Plus a few times before recording

# Use a clean theme
# Preferences → Profiles → Choose "Pro" or "Basic"

# Full screen terminal
# Cmd+Control+F before recording
```

### Timing

- Demo runs ~20 seconds with default settings
- Adjust sleep times in `cdp_browser_terminal_demo.py`
- Faster = more impressive, Slower = easier to follow

### File Locations

```
cdp_browser_terminal_demo.py  → The demo script (with colors!)
record_terminal_demo.sh        → Helper script (choose recording method)
cdp_browser_demo_30s.py       → Non-terminal version (visible browser)
```

---

## Example asciinema Command

```bash
# One-liner to record and upload
asciinema rec -c "source .venv/bin/activate && python examples/cdp_browser_terminal_demo.py" && \
asciinema upload $(ls -t *.cast | head -1)
```

Get a shareable URL instantly!

---

## Troubleshooting

**Colors not showing?**
- Make sure terminal supports 256 colors
- Try `echo $TERM` (should be `xterm-256color`)

**asciinema not found?**
- Install: `pip install asciinema`
- Or: `brew install asciinema`

**GIF too large?**
- Reduce FPS: `-vf "fps=8,..."`
- Reduce scale: `-vf "...,scale=600:-1,..."`
- Shorter recording

---

## Ready to Record?

```bash
./record_terminal_demo.sh
```

Choose option 1 and you'll have a shareable terminal recording in 30 seconds!
