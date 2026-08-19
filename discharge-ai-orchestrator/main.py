"""
AI Multi-Agent Orchestrator Service (Port 8001).
FastAPI application for multi-agent clinical reasoning and discharge readiness evaluation.
"""

import os
import time
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Load environment variables
load_dotenv()

try:
    from .models import EvaluateRequest, DischargeReadinessEvaluation
    from .agents import AIOrchestrationPipeline
except ImportError:
    from models import EvaluateRequest, DischargeReadinessEvaluation
    from agents import AIOrchestrationPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [AI-ORCHESTRATOR] %(message)s"
)
logger = logging.getLogger("ai_orchestrator")

pipeline: AIOrchestrationPipeline = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    model_id = os.getenv("MODEL_ID", "claude-sonnet-5")
    pipeline = AIOrchestrationPipeline(api_key=api_key, model_id=model_id)
    logger.info(f"AI Orchestrator Pipeline initialized (Model: {pipeline.model_id})")
    yield
    logger.info("AI Orchestrator shutting down")


app = FastAPI(
    title="AI Discharge Readiness Orchestrator",
    description="Multi-Agent Reasoning Core for Clinical Discharge Evaluation",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Configuration
cors_origin = os.getenv("CORS_ALLOWED_ORIGIN", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[cors_origin, "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", summary="Health Check")
async def health():
    """Health check endpoint for service monitoring and orchestration sweeps."""
    return {"status": "ok"}


@app.post(
    "/orchestrate/evaluate",
    response_model=DischargeReadinessEvaluation,
    summary="Evaluate Patient Discharge Readiness",
    status_code=status.HTTP_200_OK,
)
async def evaluate_patient(request: EvaluateRequest) -> DischargeReadinessEvaluation:
    """
    Executes the 4-agent concurrent reasoning pipeline, deterministic aggregator,
    and synthesis agent to produce a clinical-grade DischargeReadinessEvaluation.
    """
    start_time = time.perf_counter()
    logger.info(f"Received evaluation request for patient_id='{request.patient_id}'")

    try:
        result = await pipeline.evaluate(request)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"Completed evaluation for '{request.patient_id}' in {elapsed_ms:.1f}ms | "
            f"Score: {result.readiness_score} | Tier: {result.readiness_tier} | "
            f"Barriers: {len(result.clinical_barriers)}"
        )
        return result
    except Exception as e:
        logger.error(f"Error during orchestration for '{request.patient_id}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI Orchestration evaluation error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    uvicorn.run("discharge-ai-orchestrator.main:app", host="0.0.0.0", port=port, reload=True)
