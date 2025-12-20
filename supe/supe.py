"""Supe - The Main Orchestrator.

The Supe is the central agent with abilities. It provides a goal-oriented
async API for planning and executing work.

Key principles:
1. Input is always a GOAL, not explicit params
2. Recall starts at present moment, jumps through connections
3. Only top-level plans need human approval
4. Memory follows human-inspired model (episodic, semantic, procedural)

Example:
    supe = Supe()
    
    # Goal-oriented execution
    result = await supe.exe("Ingest Discord API docs")
    
    # Recall from memory
    answer = await supe.recall("How do Discord slash commands work?")
    
    # Plan first, review, then execute
    plan = await supe.plan("Build a todo app with React")
    # ... review and approve ...
    result = await supe.exe(plan)
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ab.abdb import ABMemory
from ab.models import Card, Moment


@dataclass
class RecallResult:
    """Result of a memory recall.
    
    Attributes:
        cards: Found memories.
        distances: Map of card_id -> jumps from present moment.
        path: Moment IDs traversed during recall.
        present_moment_id: Starting moment.
        query: Original query.
    """
    
    cards: List[Card]
    distances: Dict[int, int] = field(default_factory=dict)
    path: List[int] = field(default_factory=list)
    present_moment_id: Optional[int] = None
    query: str = ""
    
    def closest(self, n: int = 1) -> List[Card]:
        """Get N closest (easiest to recall) cards."""
        if not self.distances:
            return self.cards[:n]
        sorted_ids = sorted(self.distances, key=self.distances.get)
        return [c for c in self.cards if c.id in sorted_ids[:n]]
    
    def __len__(self) -> int:
        return len(self.cards)
    
    def __bool__(self) -> bool:
        return len(self.cards) > 0


@dataclass
class ExecutionResult:
    """Result of executing a goal or plan.
    
    Attributes:
        success: Whether execution succeeded.
        plan_id: ID of the executed plan.
        tascs_completed: Number of tascs completed.
        tascs_total: Total number of tascs.
        proof_hashes: Map of tasc_id -> proof_hash.
        error: Error message if failed.
    """
    
    success: bool
    plan_id: str = ""
    tascs_completed: int = 0
    tascs_total: int = 0
    proof_hashes: Dict[str, str] = field(default_factory=dict)
    error: Optional[str] = None
    
    @property
    def progress(self) -> float:
        """Completion percentage."""
        if self.tascs_total == 0:
            return 0.0
        return self.tascs_completed / self.tascs_total


class Supe:
    """The Supe - main orchestrator for agent abilities.
    
    Cognitive architecture with moment-based consciousness:
    - Sensory organs gather input
    - Step cycle: sense → awareness → output → narrate
    - Overlord provides final narration each moment
    
    Attributes:
        memory: AB Memory instance for long-term storage.
        abilities: Registered abilities (loaded from plugins).
        sensory: Sensory system with registered organs.
    """
    
    def __init__(
        self,
        db_path: Optional[str] = None,
        auto_load_plugins: bool = True,
    ):
        """Initialize Supe.
        
        Args:
            db_path: Path to SQLite database. Auto-determined if None.
            auto_load_plugins: Whether to auto-detect and load plugins.
        """
        self.memory = ABMemory(db_path or self._default_db_path())
        self._abilities: Dict[str, Any] = {}
        
        # Sensory system
        from .sensory import SensorySystem, BrowserOrgan
        self.sensory = SensorySystem()
        
        # Register default organs
        try:
            from tascer.plugins.browser import CDP_BROWSER_AVAILABLE
            if CDP_BROWSER_AVAILABLE:
                self.sensory.register(BrowserOrgan())
        except ImportError:
            pass
        
        if auto_load_plugins:
            self._load_plugins()
    
    def _default_db_path(self) -> str:
        """Get default database path."""
        supe_dir = Path.home() / ".supe"
        supe_dir.mkdir(exist_ok=True)
        return str(supe_dir / "memory.sqlite")
    
    def _load_plugins(self):
        """Auto-detect and load available plugins."""
        # Load browser plugin if available
        try:
            from tascer.plugins.browser import CDP_BROWSER_AVAILABLE
            if CDP_BROWSER_AVAILABLE:
                from tascer.abilities import WebScraperAbility
                self._abilities["scrape"] = WebScraperAbility(self.memory)
        except ImportError:
            pass
    
    # ------------------------------------------------------------------
    # Master State (operators update this, downstream sensing follows)
    # ------------------------------------------------------------------
    
    def set_state(self, **kwargs) -> None:
        """Update master state - drives downstream sensing.
        
        Operators call this to set what the Supe should focus on.
        Then call `next()` to process.
        
        Example:
            supe.set_state(
                url="https://discord.com/developers/docs/change-log",
                focus="What's new in Discord API?",
            )
            moment = await supe.next()
        """
        self._state = {**getattr(self, '_state', {}), **kwargs}
    
    def get_state(self) -> Dict[str, Any]:
        """Get current master state."""
        return getattr(self, '_state', {})
    
    def clear_state(self) -> None:
        """Clear master state."""
        self._state = {}
    
    async def next(self) -> Moment:
        """Execute next moment cycle based on master state.
        
        Simplified API - no need to specify organs explicitly.
        The Supe decides what to sense based on state.
        
        Returns:
            The new Moment created.
        
        Example:
            supe.set_state(url="https://discord.com/developers/docs")
            moment = await supe.next()  # Auto-senses with browser
        """
        state = self.get_state()
        
        # Determine sensory kwargs from state
        sensory_kwargs = {}
        
        # URL -> browser organ
        if "url" in state:
            sensory_kwargs["browser"] = {
                "url": state["url"],
                "wait_ms": state.get("wait_ms", 3000),
            }
        
        # path -> file organ
        if "path" in state:
            sensory_kwargs["file"] = {"path": state["path"]}
        
        # command -> terminal organ
        if "command" in state:
            sensory_kwargs["terminal"] = {
                "command": state["command"],
                "cwd": state.get("cwd"),
            }
        
        # prompt -> claude organ
        if "prompt" in state:
            sensory_kwargs["claude"] = {
                "prompt": state["prompt"],
                "system_prompt": state.get("system_prompt"),
            }
        
        # Execute step with detected sensory needs
        moment = await self.step(sensory_kwargs)
        
        # Run Learner subself on the awareness card
        if moment.awareness_card_id and state.get("learn", True):
            await self._run_learner(moment.awareness_card_id)
        
        return moment
    
    async def _run_learner(self, awareness_card_id: int) -> None:
        """Run Learner subself on awareness card."""
        try:
            from .subselves import LearnerSubself
            learner = LearnerSubself(self.memory)
            awareness_card = self.memory.get_card(awareness_card_id)
            notes = await learner.learn(awareness_card)
            # Notes are stored automatically
        except Exception as e:
            # Log but don't fail
            pass
    
    async def step(
        self,
        sensory_kwargs: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Moment:
        """Execute one moment cycle (vibration).
        
        The consciousness cycle:
        1. Gather sensory input from organs (flushed after use)
        2. Get previous moment's output
        3. Create awareness state
        4. Produce output
        5. Overlord narration (final note)
        6. Create new moment
        
        Args:
            sensory_kwargs: Dict of organ_name -> kwargs for sensing.
        
        Returns:
            The new Moment created.
        
        Example:
            moment = await supe.step({
                "browser": {"url": "https://discord.com/developers/docs/change-log"}
            })
        """
        from ab.models import Buffer
        
        # Get current state for content decisions
        state = self.get_state()
        
        # 1. Gather sensory input (ephemeral - flushed after)
        sensory_inputs = []
        if sensory_kwargs:
            sensory_inputs = await self.sensory.gather_all(**{
                name: kwargs for name, kwargs in sensory_kwargs.items()
            })
        
        # 2. Get previous moment's output
        prev_moment = self.memory.get_latest_moment()
        prev_output = ""
        if prev_moment and prev_moment.master_output:
            prev_output = prev_moment.master_output
        
        # 3. Create awareness state (combine sensory + previous)
        awareness_data = {
            "sensory_count": len(sensory_inputs),
            "sensory_types": [s.input_type for s in sensory_inputs],
            "previous_output": prev_output[:500] if prev_output else None,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Store awareness card
        awareness_buffers = [
            Buffer(
                name="state",
                headers={"type": "awareness_state"},
                payload=json.dumps(awareness_data).encode(),
            ),
        ]
        
        # Add sensory data (full content if learning, else summary)
        for si in sensory_inputs:
            # Store full content for learning, summary otherwise
            max_bytes = 500000 if state.get("learn", True) else 1000
            awareness_buffers.append(Buffer(
                name=f"sensory_{si.organ_name}",
                headers=si.metadata,
                payload=si.data[:max_bytes],
            ))
        
        awareness_card = self.memory.store_card(
            label="awareness",
            buffers=awareness_buffers,
            track="awareness",
        )
        
        # 4. Produce output (what this moment accomplished)
        output = self._produce_output(sensory_inputs, prev_output)
        
        # 5. Overlord narration (final note on consciousness state)
        narration = self._overlord_narrate(awareness_data, output, sensory_inputs)
        
        # 6. Create new moment
        new_moment = self.memory.create_moment(
            master_input=json.dumps(awareness_data),
            master_output=output,
            awareness_card_id=awareness_card.id,
        )
        
        # Store narration (need to update moment)
        self._update_moment_narration(new_moment.id, narration)
        
        # Sensory inputs are now flushed (not stored permanently)
        return new_moment
    
    def _produce_output(
        self,
        sensory_inputs: List,
        prev_output: str,
    ) -> str:
        """Produce output for this moment."""
        parts = []
        if sensory_inputs:
            parts.append(f"Processed {len(sensory_inputs)} sensory inputs")
            for si in sensory_inputs:
                parts.append(f"  - {si.organ_name}: {si.input_type} ({len(si.data)} bytes)")
        if prev_output:
            parts.append(f"Continued from: {prev_output[:100]}...")
        return "\n".join(parts) if parts else "Awaiting input"
    
    def _overlord_narrate(
        self,
        awareness: Dict,
        output: str,
        sensory_inputs: List,
    ) -> str:
        """Overlord's narration of consciousness state.
        
        This is the final note summarizing this moment.
        """
        narration_parts = [
            f"[Moment at {awareness.get('timestamp', 'unknown')}]",
        ]
        
        if sensory_inputs:
            narration_parts.append(f"Received {len(sensory_inputs)} sensory input(s).")
            for si in sensory_inputs:
                title = si.metadata.get("title") or si.metadata.get("url", si.organ_name)
                narration_parts.append(f"  - Sensed: {title}")
        
        if awareness.get("previous_output"):
            narration_parts.append("Continuing from previous moment.")
        
        narration_parts.append(f"Output: {output[:200]}")
        
        return "\n".join(narration_parts)
    
    def _update_moment_narration(self, moment_id: int, narration: str) -> None:
        """Update a moment's overlord narration."""
        cur = self.memory.conn.cursor()
        cur.execute(
            "UPDATE moments SET overlord_narration = ? WHERE id = ?",
            (narration, moment_id)
        )
        self.memory.conn.commit()
    
    async def exe(
        self, 
        goal_or_plan: Union[str, "TascPlan"],
    ) -> ExecutionResult:
        """Execute a goal or plan.
        
        If string: Parse goal → Create plan → Execute
        If TascPlan: Execute directly (should be approved)
        
        Args:
            goal_or_plan: Natural language goal OR approved TascPlan.
        
        Returns:
            ExecutionResult with completion status and proof hashes.
        
        Example:
            result = await supe.exe("Scrape top 5 HN stories")
        """
        from tascer.llm_proof import TascPlan
        
        if isinstance(goal_or_plan, str):
            plan = await self.plan(goal_or_plan)
            return await self._execute(plan)
        elif isinstance(goal_or_plan, TascPlan):
            return await self._execute(goal_or_plan)
        else:
            raise TypeError(f"Expected str or TascPlan, got {type(goal_or_plan)}")
    
    async def plan(self, goal: str) -> "TascPlan":
        """Create a TascPlan from a natural language goal.
        
        Analyzes the goal and determines which ability to use.
        
        Args:
            goal: Natural language description of what to accomplish.
        
        Returns:
            TascPlan ready for review or execution.
        
        Example:
            plan = await supe.plan("Ingest Discord API documentation")
        """
        from tascer.llm_proof import create_plan
        
        # Simple goal parsing (can be made smarter with LLM)
        goal_lower = goal.lower()
        
        if any(kw in goal_lower for kw in ["scrape", "ingest", "get", "fetch"]):
            # Extract URL if present
            import re
            urls = re.findall(r'https?://[^\s]+', goal)
            if urls:
                return self._abilities["scrape"].plan(urls=urls, description=goal)
        
        # Default: create a simple plan
        return create_plan(
            title=goal[:80],
            description=goal,
            tascs=[{"id": "main", "title": goal, "testing_instructions": goal}],
        )
    
    async def recall(
        self, 
        query: str,
        max_jumps: int = 5,
        style: str = "semantic",
        limit: int = 10,
    ) -> RecallResult:
        """Recall from memory, starting at present moment.
        
        Like consciousness: starts at "now", follows connections.
        Distance = number of jumps. Closer = easier to recall.
        
        Args:
            query: What to recall.
            max_jumps: Max connection hops (difficulty threshold).
            style: Recall style - 'semantic', 'keyword', 'temporal', 'graph'.
            limit: Max results to return.
        
        Returns:
            RecallResult with cards, distances, and path.
        
        Example:
            result = await supe.recall("How do Discord slash commands work?")
            for card in result.closest(3):
                print(card.master_output)
        """
        # Get current moment
        present = self.memory.get_latest_moment()
        present_id = present.id if present else None
        
        # Perform recall based on style
        if style == "keyword":
            cards = self._keyword_recall(query, limit)
        elif style == "temporal":
            cards = self._temporal_recall(query, limit)
        elif style == "graph":
            cards = await self._graph_recall(query, max_jumps, limit)
        else:  # semantic (default)
            cards = self._semantic_recall(query, limit)
        
        # Compute distances from present
        distances = {}
        for card in cards:
            distances[card.id] = self._compute_distance(present_id, card.moment_id)
        
        return RecallResult(
            cards=cards,
            distances=distances,
            present_moment_id=present_id,
            query=query,
        )
    
    def _semantic_recall(self, query: str, limit: int) -> List[Card]:
        """Semantic recall - search by meaning."""
        # Simple implementation: text search in master fields
        # TODO: Add embedding-based search
        return self.memory.search_cards(query, limit=limit)
    
    def _keyword_recall(self, query: str, limit: int) -> List[Card]:
        """Keyword recall - exact text match."""
        return self.memory.search_cards(query, limit=limit, exact=True)
    
    def _temporal_recall(self, query: str, limit: int) -> List[Card]:
        """Temporal recall - most recent first."""
        cards = self.memory.search_cards(query, limit=limit * 2)
        # Sort by created_at descending
        cards.sort(key=lambda c: c.created_at, reverse=True)
        return cards[:limit]
    
    async def _graph_recall(
        self, 
        query: str, 
        max_jumps: int, 
        limit: int,
    ) -> List[Card]:
        """Graph recall - follow connections from present moment."""
        # Start from present
        present = self.memory.get_latest_moment()
        if not present:
            return []
        
        # BFS through connections
        visited = set()
        results = []
        queue = [(present.id, 0)]  # (moment_id, depth)
        
        while queue and len(results) < limit:
            moment_id, depth = queue.pop(0)
            if depth > max_jumps:
                continue
            if moment_id in visited:
                continue
            visited.add(moment_id)
            
            # Get cards at this moment
            cards = self.memory.get_cards_by_moment(moment_id)
            for card in cards:
                if self._matches_query(card, query):
                    results.append(card)
            
            # Add connected moments
            connections = self.memory.get_moment_connections(moment_id)
            for conn_id in connections:
                queue.append((conn_id, depth + 1))
        
        return results
    
    def _compute_distance(
        self, 
        from_moment: Optional[int], 
        to_moment: Optional[int],
    ) -> int:
        """Compute jump distance between moments."""
        if from_moment is None or to_moment is None:
            return 999  # Unknown distance
        if from_moment == to_moment:
            return 0
        # Simple heuristic: difference in IDs as proxy for distance
        return abs(from_moment - to_moment)
    
    def _matches_query(self, card: Card, query: str) -> bool:
        """Check if card matches query."""
        query_lower = query.lower()
        if card.master_input and query_lower in card.master_input.lower():
            return True
        if card.master_output and query_lower in card.master_output.lower():
            return True
        if query_lower in card.label.lower():
            return True
        return False
    
    async def traverse_moments(
        self, 
        direction: str = "back",
        count: int = 10,
    ) -> List[Moment]:
        """Walk through the moments ledger.
        
        Like reviewing a timeline of consciousness.
        
        Args:
            direction: 'back' (older) or 'forward' (newer).
            count: Number of moments to retrieve.
        
        Returns:
            List of Moments in order.
        """
        return self.memory.get_moments(direction=direction, limit=count)

    async def learn(
        self,
        question: str,
        mode: str = "ingest",
    ) -> Dict[str, Any]:
        """Learn by answering a question using the unified learning system.

        Uses the new LearningStateMachine to learn through either INGEST
        (document learning) or EXPLORE (experimental validation) modes.

        This method orchestrates a complete learning session:
        1. Creates a LearningStateMachine with the specified mode
        2. Runs the state machine through completion
        3. Stores the session with full context to AB Memory
        4. Creates Tasc validation with proof hashes
        5. Returns comprehensive results

        Args:
            question: Natural language question to learn about.
            mode: Learning mode - 'ingest' (document learning) or
                  'explore' (experimental validation). Case-insensitive.

        Returns:
            Dict with learning results:
                - session_id: Unique session identifier
                - question: The original question
                - mode: Learning mode used
                - beliefs_count: Number of beliefs created
                - evidence_count: Number of evidence items collected
                - gaps_count: Number of knowledge gaps identified
                - confidence: Average confidence score (0.0-1.0)
                - validated: Whether Tasc validation passed
                - proof_hash: Cryptographic proof hash
                - beliefs: List of belief dictionaries

        Example:
            result = await supe.learn("How do React hooks work?", mode="ingest")
            print(f"Learned {result['beliefs_count']} beliefs with "
                  f"{result['confidence']:.2f} confidence")

            result = await supe.learn("Is addition commutative?", mode="explore")
            print(f"Validation: {result['validated']}, Proof: {result['proof_hash']}")
        """
        from .learning import LearningStateMachine, Mode
        from .learning.tasc_integration import process_learning_session_as_tasc
        from .learning.storage import store_learning_session_full

        # Create learning state machine with appropriate mode
        mode_enum = Mode.INGEST if mode.lower() == "ingest" else Mode.EXPLORE
        sm = LearningStateMachine(self.memory, mode=mode_enum, debug=False)

        # Run learning session
        await sm.initialize(question)
        await sm.run(max_steps=50)

        # Get session summary
        summary = sm.get_summary()
        beliefs = sm.get_beliefs()

        # Store session with full context if state machine has context
        session_card_id = None
        tasc_result = {}

        if sm.context:
            # Store complete learning session to AB Memory
            storage_result = store_learning_session_full(self.memory, sm.context)
            session_card_id = storage_result["context_card_id"]

            # Create Tasc validation for proof-of-work
            tasc_result = process_learning_session_as_tasc(
                self.memory,
                sm.context,
                session_card_id
            )

        # Calculate average confidence
        avg_confidence = 0.0
        if beliefs:
            avg_confidence = sum(b.confidence for b in beliefs) / len(beliefs)

        # Return comprehensive results
        return {
            "session_id": summary["session_id"],
            "question": question,
            "mode": mode,
            "beliefs_count": summary["beliefs_count"],
            "evidence_count": summary["evidence_count"],
            "gaps_count": summary["gaps_count"],
            "confidence": avg_confidence,
            "validated": tasc_result.get("success", False),
            "proof_hash": tasc_result.get("proof_hash", ""),
            "beliefs": [b.to_dict() for b in beliefs],
        }

    async def _execute(self, plan: "TascPlan") -> ExecutionResult:
        """Execute a TascPlan.
        
        Args:
            plan: TascPlan to execute.
        
        Returns:
            ExecutionResult with status.
        """
        from tascer.llm_proof import verify_plan_completion
        
        try:
            # Find matching ability
            for name, ability in self._abilities.items():
                if hasattr(ability, 'execute'):
                    report = await ability.execute(plan)
                    return ExecutionResult(
                        success=report.all_validated,
                        plan_id=plan.id,
                        tascs_completed=report.validated_count,
                        tascs_total=report.total_count,
                        proof_hashes={
                            tid: v.proof_hash 
                            for tid, v in plan.validations.items()
                        },
                    )
            
            # No ability found - return pending
            return ExecutionResult(
                success=False,
                error="No matching ability found for this plan",
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=str(e),
            )


class AgentPort:
    """Interface for AI agents to consume Supe capabilities.
    
    Provides structured responses optimized for LLM consumption.
    
    Example:
        port = AgentPort(supe)
        response = await port.query("How do I register slash commands?")
        print(response.answer_context)
    """
    
    def __init__(self, supe: Supe):
        self.supe = supe
    
    async def query(self, question: str) -> "AgentResponse":
        """Process a query and return LLM-friendly response.
        
        Args:
            question: Natural language question.
        
        Returns:
            AgentResponse with context and sources.
        """
        recall_result = await self.supe.recall(question)
        
        context = self._format_for_llm(recall_result.cards)
        
        return AgentResponse(
            answer_context=context,
            sources=[card.master_input or card.label for card in recall_result.cards],
            confidence=self._compute_confidence(recall_result),
            cards_found=len(recall_result.cards),
        )
    
    async def learn(
        self,
        question: str,
        mode: str = "ingest",
    ) -> Dict[str, Any]:
        """Learn by answering a question using the unified learning system.

        Uses the new LearningStateMachine to learn through either INGEST
        (document learning) or EXPLORE (experimental validation) modes.

        Args:
            question: The question to learn about.
            mode: Learning mode - "ingest" or "explore" (default: "ingest").

        Returns:
            Dictionary with learning results:
            {
                "session_id": str,
                "question": str,
                "mode": str,
                "beliefs_count": int,
                "evidence_count": int,
                "gaps_count": int,
                "confidence": float,
                "beliefs": List[Dict],
            }

        Example:
            result = await supe.learn("How do React hooks work?")
            print(f"Learned with {result['beliefs_count']} beliefs")
        """
        from .learning import LearningStateMachine, Mode
        from .learning.tasc_integration import process_learning_session_as_tasc
        from .learning.storage import store_learning_session_full

        # Create learning state machine
        mode_enum = Mode.INGEST if mode.lower() == "ingest" else Mode.EXPLORE

        sm = LearningStateMachine(self.memory, mode=mode_enum, debug=False)

        # Run learning session
        await sm.initialize(question)
        await sm.run(max_steps=50)

        # Store session with full context
        if sm.context:
            storage_result = store_learning_session_full(
                self.memory,
                sm.context,
            )
            session_card_id = storage_result["context_card_id"]

            # Create Tasc validation
            tasc_result = process_learning_session_as_tasc(
                self.memory,
                sm.context,
                session_card_id,
            )
        else:
            tasc_result = {"success": False}

        # Get summary
        summary = sm.get_summary()
        beliefs = sm.get_beliefs()

        # Calculate average confidence
        avg_confidence = 0.0
        if beliefs:
            avg_confidence = sum(float(b.confidence) for b in beliefs) / len(beliefs)

        return {
            "session_id": summary["session_id"],
            "question": question,
            "mode": mode,
            "beliefs_count": summary["beliefs_count"],
            "evidence_count": summary["evidence_count"],
            "gaps_count": summary["gaps_count"],
            "followup_questions_count": summary["followup_questions_count"],
            "confidence": avg_confidence,
            "validated": tasc_result.get("success", False),
            "proof_hash": tasc_result.get("proof_hash", ""),
            "beliefs": [b.to_dict() for b in beliefs],
        }

    def _format_for_llm(self, cards: List[Card]) -> str:
        """Format cards as LLM-consumable context."""
        if not cards:
            return "No relevant information found in memory."

        sections = []
        for card in cards[:5]:  # Limit context size
            title = card.master_output or card.label
            content = self._extract_text(card)
            sections.append(f"## {title}\n\n{content}\n")

        return "\n---\n".join(sections)
    
    def _extract_text(self, card: Card) -> str:
        """Extract readable text from card buffers."""
        texts = []
        for buf in card.buffers:
            if buf.name in ("summary", "content", "html", "text"):
                try:
                    texts.append(buf.payload.decode("utf-8")[:500])
                except:
                    pass
        return "\n\n".join(texts) if texts else "(No text content)"
    
    def _compute_confidence(self, result: RecallResult) -> float:
        """Compute confidence score based on recall quality."""
        if not result.cards:
            return 0.0
        
        # Factors: number of results, distances
        base = min(len(result.cards) / 5, 1.0)
        
        # Closer results = higher confidence
        if result.distances:
            avg_distance = sum(result.distances.values()) / len(result.distances)
            distance_factor = 1.0 / (1.0 + avg_distance / 10)
        else:
            distance_factor = 0.5
        
        return base * 0.6 + distance_factor * 0.4


@dataclass
class AgentResponse:
    """Response formatted for AI agent consumption."""
    
    answer_context: str       # LLM-friendly text
    sources: List[str]        # Citation info
    confidence: float         # 0-1 confidence score
    cards_found: int = 0
