#!/usr/bin/env python3
"""
SUPE HTTP Service for Stella Integration
Provides REST API for learning system, validation, and council mode.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Literal
import uvicorn
import asyncio
from pathlib import Path

# Import SUPE core
from supe.supe import Supe

# Server configuration
SUPE_DB_PATH = Path(__file__).parent / "stella_supe.db"
app = FastAPI(
    title="SUPE Learning Service",
    description="Cognitive learning system for Stella Supercore",
    version="1.0.0"
)

# CORS for Stella orchestrator
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to Stella's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global SUPE instance
supe: Optional[Supe] = None


# Request/Response Models
class LearnRequest(BaseModel):
    question: str = Field(..., description="Question to learn about")
    mode: Literal["ingest", "explore"] = Field(
        default="ingest",
        description="Learning mode: ingest (docs) or explore (experiments)"
    )


class Belief(BaseModel):
    statement: str
    confidence: float
    proof_hash: Optional[str] = None


class Evidence(BaseModel):
    text: str
    source: str
    citations: list[str] = []


class LearnResponse(BaseModel):
    session_id: str
    question: str
    mode: str
    status: str
    confidence: float
    beliefs: list[dict]
    evidence: list[dict]
    proof_hash: str
    summary: Optional[dict] = None


class ValidationRequest(BaseModel):
    session_id: str


class ValidationResponse(BaseModel):
    session_id: str
    validated: bool
    proof_hash: str
    confidence: float


class CouncilRequest(BaseModel):
    question: str
    agents: list[str] = Field(default=["claude"], description="Agent names")
    mode: Literal["ingest", "explore"] = "explore"


class CouncilResponse(BaseModel):
    question: str
    consensus: dict
    agent_beliefs: list[dict]
    overall_confidence: float


class HealthResponse(BaseModel):
    status: str
    service: str
    db_path: str
    ready: bool


# Startup/Shutdown
@app.on_event("startup")
async def startup():
    """Initialize SUPE instance."""
    global supe
    supe = Supe(db_path=str(SUPE_DB_PATH))
    print(f"SUPE initialized with database: {SUPE_DB_PATH}")


@app.on_event("shutdown")
async def shutdown():
    """Clean shutdown."""
    global supe
    if supe:
        pass
    print("SUPE service shutdown")


# API Endpoints
@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="SUPE Learning System",
        db_path=str(SUPE_DB_PATH),
        ready=supe is not None
    )


@app.post("/api/learn", response_model=LearnResponse)
async def learn(request: LearnRequest):
    """
    Learn from a question using INGEST or EXPLORE mode.

    - **INGEST**: Learn from documentation, create Cornell notes
    - **EXPLORE**: Discover properties through experiments, prove theorems

    Returns learning results with beliefs, evidence, and cryptographic proof hash.
    """
    if not supe:
        raise HTTPException(status_code=503, detail="SUPE not initialized")

    try:
        result = await supe.learn(
            question=request.question,
            mode=request.mode
        )

        session_id = result.get('session_id', 'unknown')
        beliefs = result.get('beliefs', [])
        evidence = result.get('evidence', [])
        confidence = result.get('confidence', 0.0)
        proof_hash = result.get('proof_hash', '')
        summary = result.get('summary', {})

        beliefs_data = []
        for b in beliefs:
            if isinstance(b, dict):
                beliefs_data.append(b)
            elif hasattr(b, 'dict'):
                beliefs_data.append(b.dict())
            elif hasattr(b, 'to_dict'):
                beliefs_data.append(b.to_dict())
            else:
                beliefs_data.append({'statement': str(b), 'confidence': confidence})

        evidence_data = []
        for e in evidence:
            if isinstance(e, dict):
                evidence_data.append(e)
            elif hasattr(e, 'dict'):
                evidence_data.append(e.dict())
            elif hasattr(e, 'to_dict'):
                evidence_data.append(e.to_dict())
            else:
                evidence_data.append({'text': str(e), 'source': 'unknown'})

        return LearnResponse(
            session_id=session_id,
            question=request.question,
            mode=request.mode,
            status="completed",
            confidence=confidence,
            beliefs=beliefs_data,
            evidence=evidence_data,
            proof_hash=proof_hash,
            summary=summary if isinstance(summary, dict) else {}
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Learning failed: {str(e)}"
        )


@app.post("/api/validate", response_model=ValidationResponse)
async def validate(request: ValidationRequest):
    """
    Validate a learning session's proof hash.

    Returns validation status and confidence score.
    """
    if not supe:
        raise HTTPException(status_code=503, detail="SUPE not initialized")

    try:
        session_label = f"session_{request.session_id}"
        cards = supe.memory.search_cards(session_label, limit=1)

        if not cards:
            raise HTTPException(
                status_code=404,
                detail=f"Session {request.session_id} not found"
            )

        card = cards[0]
        metadata = card.get('metadata', {})
        proof_hash = metadata.get('proof_hash', '')
        confidence = metadata.get('confidence', 0.0)

        return ValidationResponse(
            session_id=request.session_id,
            validated=bool(proof_hash),
            proof_hash=proof_hash,
            confidence=confidence
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session details and beliefs."""
    if not supe:
        raise HTTPException(status_code=503, detail="SUPE not initialized")

    try:
        session_label = f"session_{session_id}"
        cards = supe.memory.search_cards(session_label, limit=10)

        if not cards:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )

        return {
            "session_id": session_id,
            "cards": cards,
            "count": len(cards)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session: {str(e)}"
        )


@app.post("/api/council", response_model=CouncilResponse)
async def council(request: CouncilRequest):
    """
    Multi-agent council decision with learning consensus.

    Each agent learns independently, then beliefs are synthesized.
    """
    if not supe:
        raise HTTPException(status_code=503, detail="SUPE not initialized")

    try:
        agent_results = []

        for agent_name in request.agents:
            result = await supe.learn(
                question=f"[Agent: {agent_name}] {request.question}",
                mode=request.mode
            )
            agent_results.append({
                "agent": agent_name,
                "beliefs": result.get('beliefs', []),
                "confidence": result.get('confidence', 0.0),
                "proof_hash": result.get('proof_hash', '')
            })

        all_beliefs = []
        total_confidence = 0.0

        for result in agent_results:
            all_beliefs.extend(result['beliefs'])
            total_confidence += result['confidence']

        avg_confidence = total_confidence / len(request.agents) if request.agents else 0.0

        consensus = {
            "agreement_level": avg_confidence,
            "total_agents": len(request.agents),
            "belief_count": len(all_beliefs)
        }

        return CouncilResponse(
            question=request.question,
            consensus=consensus,
            agent_beliefs=agent_results,
            overall_confidence=avg_confidence
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Council failed: {str(e)}"
        )


# Main
if __name__ == "__main__":
    print("Starting SUPE Learning Service...")
    print(f"   Database: {SUPE_DB_PATH}")
    print(f"   Listening on: http://0.0.0.0:5050")
    print()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5050,
        log_level="info"
    )
