import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
    PORT: int = int(os.getenv("PORT", "8002"))
    CORS_ALLOWED_ORIGIN: str = os.getenv("CORS_ALLOWED_ORIGIN", "http://localhost:5173")


settings = Settings()
