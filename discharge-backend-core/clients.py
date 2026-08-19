import os
from typing import Any, Dict

import httpx

NLP_SERVICE_URL = os.getenv("NLP_SERVICE_URL", "http://localhost:8002")
AI_ORCHESTRATOR_URL = os.getenv("AI_ORCHESTRATOR_URL", "http://localhost:8001")


class UpstreamError(Exception):
    """Raised for any failure talking to NLP or the AI orchestrator --
    connection refused, timeout, non-2xx status, or unparseable body.
    main.py catches this single type and falls back to cache."""


async def extract_entities(
    raw_note_text: str, medication_list_text: str, lab_summary_text: str
) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{NLP_SERVICE_URL}/extract-entities",
                json={
                    "raw_note_text": raw_note_text,
                    "medication_list_text": medication_list_text,
                    "lab_summary_text": lab_summary_text,
                },
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        raise UpstreamError(f"NLP service returned {e.response.status_code}") from e
    except httpx.RequestError as e:
        raise UpstreamError(f"NLP service unreachable/timed out: {e}") from e
    except ValueError as e:  # JSON decode failure
        raise UpstreamError(f"NLP service returned invalid JSON: {e}") from e


async def orchestrate_evaluation(
    patient_id: str, structured_clinical_data: Dict[str, Any], raw_context: Dict[str, Any]
) -> Dict[str, Any]:
    try:
        # 20s timeout per the team contract -- the orchestrator runs 4 concurrent
        # agents plus a synthesis call, so it legitimately needs more headroom
        # than the NLP service.
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{AI_ORCHESTRATOR_URL}/orchestrate/evaluate",
                json={
                    "patient_id": patient_id,
                    "structured_clinical_data": structured_clinical_data,
                    "raw_context": raw_context,
                },
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        raise UpstreamError(f"AI orchestrator returned {e.response.status_code}") from e
    except httpx.RequestError as e:
        raise UpstreamError(f"AI orchestrator unreachable/timed out: {e}") from e
    except ValueError as e:
        raise UpstreamError(f"AI orchestrator returned invalid JSON: {e}") from e
