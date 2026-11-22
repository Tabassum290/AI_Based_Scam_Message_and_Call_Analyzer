
import os
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import db_mongo as db
from model_service import clean, predict


# ============================================================
# 1. APP CONFIGURATION
# ============================================================

app = FastAPI(
    title="FraudShield API",
    version="1.0.0",
    description="AI-Based Scam Message Detection API",
)


# Set FRONTEND_ORIGINS in deployment environment.
# Example:
# FRONTEND_ORIGINS=https://your-frontend.com,http://localhost:5173
origins = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:5173,"
    "http://localhost:5174,"
    "http://localhost:3000,"
    "http://127.0.0.1:5173,"
    "http://127.0.0.1:5174,"
    "http://127.0.0.1:3000",
)
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in origins.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# 2. DATABASE INITIALIZATION
# ============================================================

DB_READY = False

try:

    db.init()

    DB_READY = True

    print("MongoDB initialization successful")

except Exception as e:

    print("MongoDB initialization failed:", str(e))

    print(
        "WARNING: API will start, but database operations "
        "may not work."
    )


# ============================================================
# 3. REQUEST / RESPONSE SCHEMAS
# ============================================================

class ScanRequest(BaseModel):

    text: str


class Flag(BaseModel):

    label: str

    weight: int

    count: int


class ScanResponse(BaseModel):

    score: float

    verdict: str

    risk_level: str

    type: str

    type_label: str

    type_probability: float

    legit_probability: float

    flags: List[Flag]

    highlights: List[List[int]]

    message: str


class ReportIn(BaseModel):

    type: str

    source: str = ""

    description: str = ""

    amount: float = 0


# ============================================================
# 4. HOME
# ============================================================

@app.get("/")
def home():

    return {

        "message": "FraudShield API is running",

        "model": "XLM-RoBERTa",

        "database_connected": DB_READY,

    }


# ============================================================
# 5. DATABASE TEST
# ============================================================

@app.get("/api/test-db")
def test_db():

    try:

        db.ping()

        return {

            "message": "MongoDB Connected Successfully",

            "database": db.DATABASE_NAME,

        }

    except Exception as e:

        raise HTTPException(
            status_code=503,
            detail=f"MongoDB connection failed: {e}",
        )


# ============================================================
# 6. MESSAGE SCANNER
# ============================================================

@app.post(
    "/api/scan",
    response_model=ScanResponse,
)
def scan(req: ScanRequest):

    text = req.text.strip()

    if not text:

        raise HTTPException(
            status_code=400,
            detail="Text is empty",
        )

    if len(text) > 2000:

        raise HTTPException(
            status_code=413,
            detail="Message is too long (max 2000 characters)",
        )

    try:

        # Actual XLM-RoBERTa model prediction
        result = predict(text)

        # Save scan history.
        # Database failure should not stop prediction.

        try:

            db.log_scan(
                clean(text)[:60],
                result,
            )

        except Exception as e:

            print(
                "WARNING: Could not save scan:",
                str(e),
            )

        return result

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception as e:

        print(
            "Prediction Error:",
            str(e),
        )

        raise HTTPException(
            status_code=500,
            detail="Message prediction failed",
        )


# ============================================================
# 7. CREATE USER REPORT
# ============================================================

@app.post(
    "/api/reports",
    status_code=201,
)
def create_report(report: ReportIn):

    try:

        return db.add_report(
            report.model_dump()
        )

    except Exception as e:

        raise HTTPException(
            status_code=503,
            detail=f"Could not save the report: {e}",
        )


# ============================================================
# 8. GET REPORTS
# ============================================================

@app.get("/api/reports")
def list_reports():

    try:

        return db.list_reports()

    except Exception as e:

        raise HTTPException(
            status_code=503,
            detail=f"Could not load reports: {e}",
        )


# ============================================================
# 9. DASHBOARD STATISTICS
# ============================================================

@app.get("/api/stats")
def stats(tz_offset: int = 0):

    try:

        return db.stats(tz_offset)

    except Exception as e:

        raise HTTPException(
            status_code=503,
            detail=f"Could not load statistics: {e}",
        )
