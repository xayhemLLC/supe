# Problem Solver Capabilities

This directory contains scripts that extend the problem solver's abilities. Each script represents a **capability** - a specialized tool the problem solver can invoke to tackle specific types of problems.

## Architecture

```
scripts/
├── __init__.py                      # Package initialization
├── README.md                        # This file
├── capabilities.json                # Capability registry
├── capability_manager.py            # Manages capability lifecycle
├── register_capability.py           # Registration utility
├── list_capabilities.py             # List all capabilities
└── scan_prediction_markets.py       # Example capability
```

## How It Works

1. **Problem Detection**: When solving a problem, the ProblemSolver checks if any registered capabilities match the problem text
2. **Capability Selection**: The best matching capability (highest score) is selected
3. **Execution**: The capability script is executed with problem data as JSON input
4. **Integration**: The script output is integrated into the TASC reasoning chain

## Creating a New Capability

### 1. Write Your Script

Create a Python script that:
- Reads JSON input from stdin
- Performs specialized analysis/computation
- Outputs JSON results to stdout

```python
#!/usr/bin/env python3
"""Your capability description."""

import json
import sys

def main():
    # Read input
    input_data = sys.stdin.read()
    params = json.loads(input_data) if input_data.strip() else {}

    # Your logic here
    result = analyze(params)

    # Output JSON
    print(json.dumps({
        "status": "success",
        "data": result
    }))

if __name__ == "__main__":
    main()
```

### 2. Register the Capability

Edit `register_capability.py` to add your capability:

```python
capability = Capability(
    id="your_capability_id",
    name="Your Capability Name",
    description="What this capability does",
    script_path="your_script.py",
    problem_patterns=[
        "keyword1",
        "keyword2",
        "phrase to match",
    ],
    input_format='JSON: {"param": type}',
    output_format="JSON: result structure",
    tags=["category1", "category2"],
)

manager.register(capability)
```

### 3. Test It

```bash
# Test the script directly
echo '{"test": "data"}' | python3 supe/reasoning/scripts/your_script.py

# Register it
cd /path/to/supe
python3 -c "import sys; sys.path.insert(0, '.'); from supe.reasoning.scripts.register_capability import main; main()"

# List all capabilities
python3 -c "import sys; sys.path.insert(0, '.'); from supe.reasoning.scripts.list_capabilities import main; main()"

# Use it via problem solver
python3 scripts/solve_problem.py "your problem text that matches patterns" --verbose
```

## Registered Capabilities

### 1. Prediction Markets Scanner

**ID**: `scan_prediction_markets`
**Script**: `scan_prediction_markets.py`

Scans Polymarket and Kalshi for trading opportunities including arbitrage, value bets, and high-momentum markets.

**Matches**:
- polymarket
- kalshi
- prediction market
- betting market
- trading opportunity
- arbitrage
- market analysis
- profit
- expected value

**Input**:
```json
{
  "budget": 100,
  "risk_level": "medium"
}
```

**Output**:
```json
{
  "status": "success",
  "opportunities": [...],
  "summary": {
    "total_expected_return": 18.0,
    "total_allocated": 75.99
  }
}
```

**Example**:
```bash
problem "scan polymarket and kalshi for best opportunities with $100" --find "top trades"
```

## Capability Lifecycle

### Registration
```python
from supe.reasoning.scripts.capability_manager import Capability, CapabilityManager

manager = CapabilityManager()
manager.register(your_capability)
```

### Discovery
```python
capabilities = manager.find_capabilities("problem text", threshold=0.3)
```

### Execution
```python
result = manager.execute_capability(
    capability_id="scan_prediction_markets",
    input_data='{"budget": 100}'
)
```

### Statistics
```python
stats = manager.get_stats()
# {
#   "total": 1,
#   "avg_success_rate": 1.0,
#   "total_usage": 5,
#   "most_used": "Prediction Markets Scanner"
# }
```

## Usage Tracking

The capability system automatically tracks:
- **Usage count**: How many times each capability has been invoked
- **Success rate**: Percentage of successful executions
- **Last used**: Timestamp of most recent use
- **Performance**: Helps identify the most useful capabilities

## Best Practices

### 1. Clear Problem Patterns
Use specific keywords that uniquely identify problems your capability can solve:
```python
problem_patterns=[
    "polymarket",           # ✅ Specific
    "prediction market",    # ✅ Specific
    "analyze",             # ❌ Too generic
]
```

### 2. Robust Error Handling
Always return valid JSON, even on errors:
```python
try:
    result = risky_operation()
    print(json.dumps({"status": "success", "data": result}))
except Exception as e:
    print(json.dumps({"status": "error", "error": str(e)}))
```

### 3. Meaningful Metadata
Add metadata to help users understand what your capability does:
```python
metadata={
    "platforms": ["polymarket", "kalshi"],
    "requires_api": False,
    "complexity": "medium",
}
```

### 4. Testing
Test your capability both standalone and integrated:
```bash
# Standalone
echo '{"test": "input"}' | python3 your_script.py

# Integrated
python3 scripts/solve_problem.py "problem that triggers your capability"
```

## Future Capabilities (Ideas)

- **Code Analysis**: Analyze complexity, find bugs, suggest refactors
- **Math Solver**: Solve equations, calculus, linear algebra
- **Data Analysis**: Statistical analysis, visualization, trends
- **API Integration**: Fetch real-time data from external services
- **Web Scraping**: Extract structured data from websites
- **Document Processing**: Parse PDFs, extract information
- **Language Translation**: Translate between languages
- **Image Analysis**: Analyze images, extract text (OCR)

## CLI Commands

```bash
# List all capabilities
python3 scripts/list_capabilities.sh

# Use the problem solver with capabilities
python3 scripts/solve_problem.py "your problem" --verbose

# View capability stats in output
python3 scripts/solve_problem.py "problem" --verbose | grep capability
```

## API Reference

See `capability_manager.py` for the full API documentation.

Key classes:
- `Capability`: Represents a single capability
- `CapabilityManager`: Manages the capability lifecycle
- Methods: `register()`, `find_capabilities()`, `execute_capability()`, `get_stats()`
