# AI-Assisted Patient Discharge Readiness & Follow-Up Planner

Clinical dashboard and multi-agent reasoning architecture for inpatient care teams, automating discharge readiness assessment, barrier identification with source-field citations, and 6th-grade patient-friendly follow-up plans.

## System Architecture

```
[React/Vite Frontend :5173] ──► [Auth Service :8003]           (Person 5)
        │                          (login, JWT issuing, RBAC roles)
        ▼
[Core Backend API :8000] ─────► [NLP / Synthetic Data :8002]   (Person 4)
   (Person 2)                      (entity extraction,
   - single-table DB                synthetic patients)
   - guardrail enforcement   ─────► [AI Orchestrator :8001]     (Person 3)
   - hospital ops aggregation        (multi-agent reasoning,
   - cache + audit persistence       deterministic aggregator,
                                      pre-generated cache)
```

## Services
- **`discharge-ai-orchestrator/`** (Person 3): Multi-Agent clinical reasoning engine on port 8001 with 4 concurrent domain agents (`asyncio.gather`), deterministic non-LLM aggregator, and 6th-grade patient summary synthesis.
