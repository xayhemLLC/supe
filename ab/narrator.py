"""LLM Narrator: Integrates GPT/Claude as observer and reward shaper.

The Narrator views system outputs, provides feedback, and shapes rewards.
"""

import os
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class NarratorFeedback:
    """Structured feedback from the Narrator."""
    score: float  # 0.0 to 1.0
    reasoning: str
    suggestions: List[str]
    reward_modifier: float  # Additive modifier to base reward


class NarratorBackend(ABC):
    """Abstract backend for LLM narrator."""
    
    @abstractmethod
    def evaluate(self, code: str, test_results: Dict[str, Any]) -> NarratorFeedback:
        """Evaluate code and test results."""
        pass
    
    @abstractmethod
    def narrate(self, session_events: List[Dict[str, Any]]) -> str:
        """Generate narrative summary of session."""
        pass


class MockNarratorBackend(NarratorBackend):
    """Mock narrator for testing without API keys."""
    
    def evaluate(self, code: str, test_results: Dict[str, Any]) -> NarratorFeedback:
        """Simple heuristic-based evaluation."""
        score = 0.5
        suggestions = []
        
        # Check code quality heuristics
        if "def " in code:
            score += 0.1
            
        if len(code) < 50:
            suggestions.append("Consider adding more logic")
            score -= 0.1
        elif len(code) > 500:
            suggestions.append("Consider simplifying the code")
            score -= 0.05
            
        if test_results.get("passed", False):
            score += 0.3
        else:
            suggestions.append("Fix failing tests")
            
        if test_results.get("time_ms", 1000) < 100:
            score += 0.1
            suggestions.append("Good performance!")
            
        score = max(0.0, min(1.0, score))
        
        return NarratorFeedback(
            score=score,
            reasoning=f"Mock evaluation based on code length ({len(code)} chars) and test results.",
            suggestions=suggestions,
            reward_modifier=(score - 0.5) * 20  # Convert to reward modifier
        )
    
    def narrate(self, session_events: List[Dict[str, Any]]) -> str:
        """Generate simple narrative."""
        if not session_events:
            return "No events recorded in this session."
        
        lines = ["## Session Summary", ""]
        for i, event in enumerate(session_events[-5:]):  # Last 5 events
            event_type = event.get("type", "unknown")
            lines.append(f"{i+1}. **{event_type}**: {event.get('summary', 'No summary')}")
        
        return "\n".join(lines)


class OpenAINarratorBackend(NarratorBackend):
    """OpenAI GPT-based narrator (requires API key)."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        
    def evaluate(self, code: str, test_results: Dict[str, Any]) -> NarratorFeedback:
        if not self.api_key:
            return MockNarratorBackend().evaluate(code, test_results)
        
        # Would make API call here
        # For now, fall back to mock
        return MockNarratorBackend().evaluate(code, test_results)
    
    def narrate(self, session_events: List[Dict[str, Any]]) -> str:
        if not self.api_key:
            return MockNarratorBackend().narrate(session_events)
        
        return MockNarratorBackend().narrate(session_events)


class AnthropicNarratorBackend(NarratorBackend):
    """Anthropic Claude-based narrator (requires API key)."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-haiku-20240307"):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model
        
    def evaluate(self, code: str, test_results: Dict[str, Any]) -> NarratorFeedback:
        if not self.api_key:
            return MockNarratorBackend().evaluate(code, test_results)
        
        return MockNarratorBackend().evaluate(code, test_results)
    
    def narrate(self, session_events: List[Dict[str, Any]]) -> str:
        if not self.api_key:
            return MockNarratorBackend().narrate(session_events)
        
        return MockNarratorBackend().narrate(session_events)


class Narrator:
    """Main Narrator class that interfaces with the system."""
    
    def __init__(self, backend: Optional[NarratorBackend] = None):
        self.backend = backend or MockNarratorBackend()
        self.session_events: List[Dict[str, Any]] = []
        
    def log_event(self, event_type: str, data: Dict[str, Any]):
        """Log an event for later narration."""
        self.session_events.append({
            "type": event_type,
            "data": data,
            "summary": data.get("summary", str(data)[:100])
        })
        
    def evaluate_code(self, code: str, test_results: Dict[str, Any]) -> NarratorFeedback:
        """Get LLM feedback on code."""
        feedback = self.backend.evaluate(code, test_results)
        
        self.log_event("evaluation", {
            "code_length": len(code),
            "score": feedback.score,
            "summary": f"Code evaluated: {feedback.score:.2f} score"
        })
        
        return feedback
    
    def shape_reward(self, base_reward: float, code: str, test_results: Dict[str, Any]) -> float:
        """Shape reward using LLM feedback."""
        feedback = self.evaluate_code(code, test_results)
        return base_reward + feedback.reward_modifier
    
    def get_session_narrative(self) -> str:
        """Generate narrative summary of the session."""
        return self.backend.narrate(self.session_events)
    
    def reset_session(self):
        """Reset session events."""
        self.session_events = []


def create_narrator(backend_type: str = "mock") -> Narrator:
    """Factory for creating narrators."""
    if backend_type == "openai":
        return Narrator(OpenAINarratorBackend())
    elif backend_type == "anthropic":
        return Narrator(AnthropicNarratorBackend())
    else:
        return Narrator(MockNarratorBackend())


if __name__ == "__main__":
    # Demo
    narrator = create_narrator("mock")
    
    code = """
def solve(input_data):
    result = sum(input_data)
    return result
"""
    
    test_results = {"passed": True, "time_ms": 50}
    
    feedback = narrator.evaluate_code(code, test_results)
    print(f"Score: {feedback.score}")
    print(f"Reasoning: {feedback.reasoning}")
    print(f"Suggestions: {feedback.suggestions}")
    print(f"Reward Modifier: {feedback.reward_modifier}")
    
    print("\n" + narrator.get_session_narrative())
