"""Reward computation for RL training.

Multi-component reward function with configurable weights.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from .runners.base import RunResult, CompileResult


@dataclass
class RewardComponents:
    """Individual components of the reward."""
    
    test_passed: float = 0.0
    test_failed: float = 0.0
    correct_answer: float = 0.0
    compile_error: float = 0.0
    runtime_error: float = 0.0
    timeout: float = 0.0
    step_penalty: float = 0.0
    efficiency_bonus: float = 0.0
    
    @property
    def total(self) -> float:
        return (
            self.test_passed +
            self.test_failed +
            self.correct_answer +
            self.compile_error +
            self.runtime_error +
            self.timeout +
            self.step_penalty +
            self.efficiency_bonus
        )
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "test_passed": self.test_passed,
            "test_failed": self.test_failed,
            "correct_answer": self.correct_answer,
            "compile_error": self.compile_error,
            "runtime_error": self.runtime_error,
            "timeout": self.timeout,
            "step_penalty": self.step_penalty,
            "efficiency_bonus": self.efficiency_bonus,
            "total": self.total,
        }


@dataclass
class RewardConfig:
    """Configuration for reward computation."""
    
    # Positive rewards
    test_pass_reward: float = 1.0
    correct_answer_bonus: float = 100.0
    efficiency_bonus_max: float = 10.0  # Bonus for fast solutions
    
    # Penalties
    test_fail_penalty: float = -0.5
    compile_error_penalty: float = -5.0
    runtime_error_penalty: float = -2.0
    timeout_penalty: float = -3.0
    step_penalty: float = -0.1
    
    # Efficiency thresholds (in ms)
    fast_threshold_ms: float = 100.0
    medium_threshold_ms: float = 1000.0


class RewardComputer:
    """Computes rewards for RL training.
    
    Uses a multi-component reward function that incentivizes:
    - Passing tests (+1 per test)
    - Correct final answer (+100)
    - Fast execution (up to +10 bonus)
    
    And penalizes:
    - Failed tests (-0.5)
    - Compilation errors (-5)
    - Runtime errors (-2)
    - Timeouts (-3)
    - Each step taken (-0.1)
    """
    
    def __init__(self, config: Optional[RewardConfig] = None):
        self.config = config or RewardConfig()
    
    def compute(
        self,
        compile_result: Optional[CompileResult],
        run_result: Optional[RunResult],
        tests_passed: int = 0,
        tests_failed: int = 0,
        is_correct: bool = False,
        step_number: int = 0,
    ) -> RewardComponents:
        """Compute reward for an action.
        
        Args:
            compile_result: Result of compilation (if applicable).
            run_result: Result of execution.
            tests_passed: Number of tests passed.
            tests_failed: Number of tests failed.
            is_correct: Whether the final answer is correct.
            step_number: Current step number in episode.
        
        Returns:
            RewardComponents with all reward details.
        """
        reward = RewardComponents()
        
        # Step penalty (always applies)
        reward.step_penalty = self.config.step_penalty
        
        # Compilation check
        if compile_result and not compile_result.success:
            reward.compile_error = self.config.compile_error_penalty
            return reward
        
        # Run result checks
        if run_result:
            if run_result.timed_out:
                reward.timeout = self.config.timeout_penalty
                return reward
            
            if not run_result.success and run_result.exit_code != 0:
                reward.runtime_error = self.config.runtime_error_penalty
        
        # Test results
        reward.test_passed = tests_passed * self.config.test_pass_reward
        reward.test_failed = tests_failed * self.config.test_fail_penalty
        
        # Correct answer bonus
        if is_correct:
            reward.correct_answer = self.config.correct_answer_bonus
            
            # Efficiency bonus for fast correct solutions
            if run_result and run_result.duration_ms < self.config.fast_threshold_ms:
                reward.efficiency_bonus = self.config.efficiency_bonus_max
            elif run_result and run_result.duration_ms < self.config.medium_threshold_ms:
                # Linear interpolation
                ratio = 1 - (run_result.duration_ms - self.config.fast_threshold_ms) / (
                    self.config.medium_threshold_ms - self.config.fast_threshold_ms
                )
                reward.efficiency_bonus = self.config.efficiency_bonus_max * ratio
        
        return reward
    
    def compute_episode_reward(
        self,
        episode_rewards: List[RewardComponents],
    ) -> float:
        """Compute total reward for an episode."""
        return sum(r.total for r in episode_rewards)
    
    def get_shaped_reward(
        self,
        current_state: Dict[str, Any],
        next_state: Dict[str, Any],
        action_reward: RewardComponents,
    ) -> float:
        """Compute shaped reward with potential-based shaping.
        
        Uses potential-based reward shaping to provide denser
        learning signal without changing optimal policy.
        
        Potential function: number of tests passed
        """
        gamma = 0.99  # Discount factor
        
        current_potential = current_state.get("tests_passed", 0)
        next_potential = next_state.get("tests_passed", 0)
        
        shaping = gamma * next_potential - current_potential
        
        return action_reward.total + shaping
