"""
Top-level entrypoint forwarding to src.main for uvicorn runner compatibility.
"""

from src.main import app

if __name__ == "__main__":
    import uvicorn
    from src.config import settings

    uvicorn.run("src.main:app", host="0.0.0.0", port=settings.PORT, reload=True)
