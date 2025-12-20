"""Base Ability class - Tascers that create TascPlans.

An Ability represents a capability the agent has. Abilities:
1. Create TascPlans for structured work
2. Execute plans using plugins
3. Store results in AB Memory
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from tascer.llm_proof import TascPlan, PlanVerificationReport


class Ability(ABC):
    """Base class for agent abilities.
    
    An ability is a Tascer - it creates TascPlans for structured,
    validated work. Each ability defines:
    
    - What work it can plan (plan method)
    - How it executes that work (execute method)
    
    Example:
        class WebScraperAbility(Ability):
            def plan(self, urls: List[str]) -> TascPlan:
                return create_plan(...)
            
            async def execute(self, plan: TascPlan) -> PlanVerificationReport:
                # Execute each tasc
                ...
    """
    
    @abstractmethod
    def plan(self, **kwargs) -> TascPlan:
        """Create a TascPlan for this ability.
        
        Subclasses implement this to define the work structure.
        
        Returns:
            TascPlan with tascs to execute.
        """
        pass
    
    @abstractmethod
    async def execute(self, plan: TascPlan) -> PlanVerificationReport:
        """Execute a TascPlan and return verification results.
        
        This method should:
        1. Execute each tasc in order
        2. Store results in AB Memory
        3. Return a verification report
        
        Args:
            plan: TascPlan to execute.
        
        Returns:
            PlanVerificationReport with validation results.
        """
        pass
    
    def plan_and_execute(self, **kwargs) -> PlanVerificationReport:
        """Convenience method to plan and execute in one call.
        
        Creates a plan and executes it synchronously.
        """
        import asyncio
        plan = self.plan(**kwargs)
        return asyncio.run(self.execute(plan))
