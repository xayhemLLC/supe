#!/usr/bin/env python3
"""Register a new capability with the problem solver."""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from supe.reasoning.scripts.capability_manager import Capability, CapabilityManager


def register_prediction_markets():
    """Register the prediction markets scanning capability."""
    manager = CapabilityManager()

    capability = Capability(
        id="scan_prediction_markets",
        name="Prediction Markets Scanner",
        description=(
            "Scans Polymarket and Kalshi for trading opportunities including "
            "arbitrage, value bets, and high-momentum markets"
        ),
        script_path="scan_prediction_markets.py",
        problem_patterns=[
            "polymarket",
            "kalshi",
            "prediction market",
            "betting market",
            "trading opportunity",
            "arbitrage",
            "market analysis",
            "profit",
            "expected value",
        ],
        input_format='JSON: {"budget": float, "risk_level": "low|medium|high"}',
        output_format="JSON: List of opportunities with expected returns",
        tags=["markets", "finance", "trading", "analysis"],
        metadata={
            "platforms": ["polymarket", "kalshi"],
            "analysis_types": ["arbitrage", "value", "momentum"],
            "requires_api": False,  # Currently uses mock data
        },
    )

    manager.register(capability)
    print(f"✅ Registered capability: {capability.name}")
    print(f"   ID: {capability.id}")
    print(f"   Matches: {', '.join(capability.problem_patterns[:5])}")


def main():
    """Main entry point."""
    print("Registering capabilities...")
    register_prediction_markets()
    print("\nDone! View all capabilities with:")
    print("  python -m supe.reasoning.scripts.list_capabilities")


if __name__ == "__main__":
    main()
