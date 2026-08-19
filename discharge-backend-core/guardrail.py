"""
The non-negotiable safety guardrail. Person 3's AI orchestrator implements
this exact same rule independently -- that duplication is intentional defense
in depth, not a bug. This copy is the backend's final say: it runs on every
/evaluate response, whether the data just came back live from the AI or was
pulled from the cache fallback, so a stale or buggy upstream can never
silently produce an unsafe "Ready" result.
"""
from models import DischargeReadinessEvaluation, ReadinessTier, Severity


def apply_guardrail(evaluation: DischargeReadinessEvaluation) -> DischargeReadinessEvaluation:
    has_critical = any(b.severity == Severity.CRITICAL for b in evaluation.clinical_barriers)
    if has_critical:
        evaluation.readiness_tier = ReadinessTier.HIGH_RISK_BLOCKED
        evaluation.readiness_score = min(evaluation.readiness_score, 30)
    return evaluation
