"""Web Scraper Ability - A Tascer for web scraping work.

This ability demonstrates the Tascer pattern:
1. Creates TascPlans for web scraping work
2. Executes using the browser plugin
3. Stores content in awareness track, executions in execution track
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ab.abdb import ABMemory
from ab.models import Buffer

from tascer.llm_proof import (
    TascPlan,
    PlanVerificationReport,
    create_plan,
    verify_plan_completion,
    compute_proof_hash,
)
from tascer.contracts import TascValidation, GateResult
from tascer.ab_storage import store_tasc_execution, store_plan_execution

from .base import Ability


class WebScraperAbility(Ability):
    """Web scraping ability - a Tascer that creates TascPlans for scraping.
    
    This is a Tascer: it creates structured, validated work plans for
    web scraping tasks.
    
    Example:
        ability = WebScraperAbility(memory)
        
        # Create plan
        plan = ability.plan(
            urls=["https://news.ycombinator.com"],
            description="Daily HN digest",
        )
        
        # Execute with full validation
        report = await ability.execute(plan)
        
        # Results are now in AB Memory:
        # - Awareness track: ingested article content
        # - Execution track: tasc validations with proof hashes
    """
    
    def __init__(
        self, 
        memory: ABMemory,
        screenshot_dir: str = ".tascer/screenshots",
    ):
        self.memory = memory
        self.screenshot_dir = screenshot_dir
    
    def plan(
        self, 
        urls: List[str],
        description: str = "",
        selectors: Optional[Dict[str, str]] = None,
    ) -> TascPlan:
        """Create a TascPlan for scraping the given URLs.
        
        Args:
            urls: List of URLs to scrape.
            description: Optional description of the scrape task.
            selectors: Optional CSS selectors for extraction.
        
        Returns:
            TascPlan with one tasc per URL.
        """
        default_selectors = selectors or {
            "title": "title",
            "content": "article, main, .content, body",
        }
        
        tascs = []
        for i, url in enumerate(urls):
            tascs.append({
                "id": f"scrape_{i+1}",
                "title": f"Scrape: {url[:60]}",
                "testing_instructions": f"browser.scrape {url}",
                "desired_outcome": "Content extracted and ingested",
                "dependencies": [] if i == 0 else [f"scrape_{i}"],
            })
        
        return create_plan(
            title=f"Web Scrape: {len(urls)} URLs",
            description=description or f"Scrape {len(urls)} URLs and ingest content",
            tascs=tascs,
        )
    
    async def execute(self, plan: TascPlan) -> PlanVerificationReport:
        """Execute the scraping plan using the browser plugin.
        
        For each tasc:
        1. Scrape the URL using CDPBrowser
        2. Ingest content into awareness track
        3. Store execution in execution track
        4. Link execution → awareness
        
        Args:
            plan: TascPlan to execute.
        
        Returns:
            PlanVerificationReport with validation results.
        """
        from tascer.plugins.browser import CDPBrowser, CDP_BROWSER_AVAILABLE
        
        if not CDP_BROWSER_AVAILABLE:
            raise RuntimeError("CDPBrowser not available. Install websockets: pip install websockets")
        
        async with CDPBrowser(screenshot_dir=self.screenshot_dir) as browser:
            for tasc in plan.tascs:
                # Parse URL from testing_instructions
                url = tasc.testing_instructions.replace("browser.scrape ", "").strip()
                
                try:
                    # Execute browser action
                    result = await browser.get(url, wait_time_ms=3000, take_screenshot=True)
                    
                    # Ingest content into awareness track
                    awareness_card_id = self._ingest_content(
                        url=url,
                        html=result.text,
                        title=result.soup.title.string if result.soup.title else url,
                        screenshot_path=result.screenshot_path,
                    )
                    
                    # Create validation
                    validation = self._create_validation(
                        tasc_id=tasc.id,
                        success=result.ok,
                        evidence={"url": url, "html_length": len(result.text)},
                    )
                    
                    # Store execution in execution track, linked to awareness
                    store_tasc_execution(
                        self.memory,
                        tasc_id=tasc.id,
                        validation=validation,
                        plan_id=plan.id,
                        linked_awareness_id=awareness_card_id,
                    )
                    
                    # Update plan with validation
                    plan.validations[tasc.id] = validation
                    tasc.status = "validated"
                    tasc.proof_hash = validation.proof_hash
                    tasc.validated_at = validation.timestamp
                    
                except Exception as e:
                    # Create failed validation
                    validation = self._create_validation(
                        tasc_id=tasc.id,
                        success=False,
                        error=str(e),
                    )
                    plan.validations[tasc.id] = validation
                    tasc.status = "failed"
        
        # Store complete plan execution
        store_plan_execution(self.memory, plan)
        
        return verify_plan_completion(plan)
    
    def _ingest_content(
        self,
        url: str,
        html: str,
        title: str,
        screenshot_path: Optional[str] = None,
    ) -> int:
        """Ingest scraped content into the awareness track.
        
        Creates a card with the scraped content for future recall.
        
        Returns:
            Card ID of the ingested content.
        """
        buffers = [
            Buffer(
                name="url",
                headers={"type": "url"},
                payload=url.encode("utf-8"),
            ),
            Buffer(
                name="title",
                headers={"type": "title"},
                payload=title.encode("utf-8"),
            ),
            Buffer(
                name="html",
                headers={"type": "html", "length": len(html)},
                payload=html.encode("utf-8"),
            ),
            Buffer(
                name="scraped_at",
                headers={"type": "timestamp"},
                payload=datetime.now().isoformat().encode("utf-8"),
            ),
        ]
        
        if screenshot_path:
            buffers.append(Buffer(
                name="screenshot_path",
                headers={"type": "path"},
                payload=screenshot_path.encode("utf-8"),
            ))
        
        card = self.memory.store_card(
            label="ingested_content",
            buffers=buffers,
            master_input=url,
            master_output=title,
            track="awareness",  # Awareness track!
        )
        
        return card.id
    
    def _create_validation(
        self,
        tasc_id: str,
        success: bool,
        evidence: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> TascValidation:
        """Create a TascValidation with proof hash.
        
        Returns:
            TascValidation with computed proof hash.
        """
        gate_result = GateResult(
            gate_name="browser_scrape",
            passed=success,
            message="Content extracted" if success else f"Failed: {error}",
            evidence=evidence or {},
        )
        
        # Build validation data for hashing
        validation_data = {
            "tasc_id": tasc_id,
            "validated": success,
            "timestamp": datetime.now().isoformat(),
            "gate_results": [gate_result.to_dict()],
        }
        
        return TascValidation(
            tasc_id=tasc_id,
            validated=success,
            proof_hash=compute_proof_hash(validation_data),
            timestamp=validation_data["timestamp"],
            gate_results=[gate_result],
            error_message=error,
        )
