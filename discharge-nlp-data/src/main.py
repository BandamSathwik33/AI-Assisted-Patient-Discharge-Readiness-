"""
FastAPI Microservice for Clinical NLP Extraction & Synthetic Data Layer (Person 4).
Runs on port 8002.
"""

from typing import List
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.extractor import extract_all_entities
from src.generator import generate_synthetic_patients
from src.schemas import ExtractEntitiesRequest, ExtractEntitiesResponse, SyntheticPatient

app = FastAPI(
    title="Clinical NLP Extraction & Synthetic Data Layer",
    description="Deterministic clinical entity extraction and synthetic patient provider for Discharge Readiness Planner.",
    version="1.0.0",
)

# CORS middleware configured for frontend at :5173
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.CORS_ALLOWED_ORIGIN, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    """
    Standard health check endpoint. Returns {"status": "ok"}
    """
    return {"status": "ok"}


@app.get(
    "/synthetic-patients",
    response_model=List[SyntheticPatient],
    status_code=status.HTTP_200_OK,
    tags=["Synthetic Data"],
)
async def get_synthetic_patients():
    """
    Returns 14 clinically-grounded synthetic patient encounter records covering diverse discharge archetypes.
    """
    return generate_synthetic_patients()


@app.post(
    "/extract-entities",
    response_model=ExtractEntitiesResponse,
    status_code=status.HTTP_200_OK,
    tags=["NLP Extraction"],
)
async def extract_entities(payload: ExtractEntitiesRequest):
    """
    Extracts conditions, medications (with dose/frequency/access flags), vitals summary,
    pending labs, and de-identified text from unstructured clinical inputs.
    """
    return extract_all_entities(
        raw_note_text=payload.raw_note_text,
        medication_list_text=payload.medication_list_text,
        lab_summary_text=payload.lab_summary_text,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
