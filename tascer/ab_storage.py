"""AB Memory integration for Tascer.

Store Tascer artifacts (Context, ActionSpec, ActionResult, ValidationReport)
as Cards in AB Memory.
"""

import json
from typing import Optional

from .contracts import Context, ActionResult, ActionSpec, ValidationReport


def store_context(memory, context: Context, moment_id: Optional[int] = None) -> int:
    """Store a Context snapshot as a Card in AB Memory.
    
    Args:
        memory: ABMemory instance.
        context: Context to store.
        moment_id: Optional moment ID to associate with.
    
    Returns:
        Card ID of the stored context.
    """
    from ab.models import Buffer
    
    # Serialize context to JSON
    context_json = json.dumps(context.to_dict(), indent=2).encode("utf-8")
    
    buf = Buffer(
        name="context",
        headers={
            "run_id": context.run_id,
            "tasc_id": context.tasc_id,
            "type": "tascer_context",
        },
        payload=context_json,
    )
    
    card = memory.store_card(
        label="tascer_context",
        buffers=[buf],
        moment_id=moment_id,
    )
    return card.id


def store_action_result(
    memory,
    result: ActionResult,
    run_id: str,
    tasc_id: str,
    moment_id: Optional[int] = None,
) -> int:
    """Store an ActionResult as a Card in AB Memory.
    
    Args:
        memory: ABMemory instance.
        result: ActionResult to store.
        run_id: Run identifier.
        tasc_id: Tasc identifier.
        moment_id: Optional moment ID.
    
    Returns:
        Card ID of the stored result.
    """
    from ab.models import Buffer
    
    result_json = json.dumps(result.to_dict(), indent=2).encode("utf-8")
    
    buf = Buffer(
        name="action_result",
        headers={
            "run_id": run_id,
            "tasc_id": tasc_id,
            "type": "tascer_action_result",
            "status": result.status,
        },
        payload=result_json,
    )
    
    card = memory.store_card(
        label="tascer_action_result",
        buffers=[buf],
        moment_id=moment_id,
    )
    return card.id


def store_validation_report(
    memory,
    report: ValidationReport,
    moment_id: Optional[int] = None,
) -> int:
    """Store a full ValidationReport as a Card in AB Memory.
    
    Creates a card with multiple buffers:
    - report: Full JSON report
    - context: Context snapshot
    - summary: Human-readable summary
    
    Args:
        memory: ABMemory instance.
        report: ValidationReport to store.
        moment_id: Optional moment ID.
    
    Returns:
        Card ID of the stored report.
    """
    from ab.models import Buffer
    
    # Full report buffer
    report_json = json.dumps(report.to_dict(), indent=2).encode("utf-8")
    report_buf = Buffer(
        name="report",
        headers={
            "run_id": report.run_id,
            "tasc_id": report.tasc_id,
            "type": "tascer_validation_report",
            "status": report.overall_status,
            "gates_passed": len(report.gates_passed),
            "gates_failed": len(report.gates_failed),
        },
        payload=report_json,
    )
    
    # Summary buffer (text)
    summary_buf = Buffer(
        name="summary",
        headers={"type": "text"},
        payload=report.summary.encode("utf-8"),
    )
    
    # Context buffer
    context_json = json.dumps(report.context.to_dict(), indent=2).encode("utf-8")
    context_buf = Buffer(
        name="context",
        headers={"type": "tascer_context"},
        payload=context_json,
    )
    
    card = memory.store_card(
        label="tascer_report",
        buffers=[report_buf, summary_buf, context_buf],
        moment_id=moment_id,
        master_input=report.action_spec.op_ref,
        master_output=report.overall_status,
    )
    return card.id


def load_validation_report(memory, card_id: int) -> ValidationReport:
    """Load a ValidationReport from AB Memory.
    
    Args:
        memory: ABMemory instance.
        card_id: ID of the card to load.
    
    Returns:
        Decoded ValidationReport.
    
    Raises:
        ValueError: If card doesn't contain a valid report.
    """
    card = memory.get_card(card_id)
    
    if card.label != "tascer_report":
        raise ValueError(f"Card {card_id} is not a tascer_report (label={card.label})")
    
    # Find report buffer
    report_buf = None
    for buf in card.buffers:
        if buf.name == "report":
            report_buf = buf
            break
    
    if report_buf is None:
        raise ValueError(f"Card {card_id} does not contain a report buffer")
    
    report_data = json.loads(report_buf.payload.decode("utf-8"))
    return ValidationReport.from_dict(report_data)


def find_reports_by_tasc(memory, tasc_id: str) -> list:
    """Find all validation reports for a given tasc ID.
    
    Args:
        memory: ABMemory instance.
        tasc_id: Tasc identifier to search for.
    
    Returns:
        List of (card_id, report_summary) tuples.
    """
    cards = memory.find_cards_by_label("tascer_report")
    results = []
    
    for card in cards:
        for buf in card.buffers:
            if buf.name == "report":
                headers = buf.headers
                if headers.get("tasc_id") == tasc_id:
                    results.append((
                        card.id,
                        {
                            "run_id": headers.get("run_id"),
                            "status": headers.get("status"),
                            "gates_passed": headers.get("gates_passed"),
                            "gates_failed": headers.get("gates_failed"),
                        }
                    ))
                break
    
    return results
