"""MongoDB Atlas storage for scans and reports (same five functions as db.py)."""
import os
import certifi
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME")
if not MONGODB_URL or not DATABASE_NAME:
    raise ValueError("MongoDB environment variables are missing! Set MONGODB_URL and DATABASE_NAME in backend/.env")

client = MongoClient(
    MONGODB_URL,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=10000
)
db = client[DATABASE_NAME]
scan_collection = db["scan"]
reports_collection = db["reports"]


def _now():
    return datetime.now(timezone.utc)


def _iso(dt):
    """MongoDB returns UTC datetimes without a timezone; mark them as UTC for the browser."""
    return dt.isoformat() + "Z" if dt.tzinfo is None else dt.isoformat()


def _report_out(doc: dict) -> dict:
    out = dict(doc)
    out["id"] = str(out.pop("_id"))          # ObjectId is not JSON serializable
    if isinstance(out.get("created_at"), datetime):
        out["created_at"] = _iso(out["created_at"])
    return out


def ping():
    client.admin.command("ping")


def init():
    """Create indexes once at startup. If Atlas is unreachable, warn instead of crashing."""
    try:
        scan_collection.create_index("created_at")
        reports_collection.create_index("created_at")
        # Optional privacy: delete scan records automatically after 30 days
        # scan_collection.create_index("created_at", expireAfterSeconds=60 * 60 * 24 * 30)
    except Exception as e:
        print(f"WARNING: could not reach MongoDB at startup: {e}")


def log_scan(summary: str, result: dict):
    scan_collection.insert_one({
        "created_at": _now(),
        "summary": summary,                 # masked snippet only, never the raw message
        "score": result["score"],
        "verdict": result["verdict"],
        "type": result["type"],
        "type_label": result["type_label"],
        "type_probability": result["type_probability"],
    })


def add_report(r: dict) -> dict:
    doc = {**r, "status": "Under review", "created_at": _now()}
    reports_collection.insert_one(doc)      # adds doc["_id"] (ObjectId)
    return _report_out(doc)


def list_reports(limit: int = 200) -> list:
    return [_report_out(d) for d in reports_collection.find().sort("_id", -1).limit(limit)]


def stats(tz_offset_minutes: int = 0) -> dict:
    """tz_offset_minutes is JavaScript's getTimezoneOffset() (e.g. -360 for UTC+6),
    so 'today' and the weekday labels match the user's own clock."""
    checks = scan_collection.count_documents({})
    scams = scan_collection.count_documents({"verdict": "SCAM"})
    reports = reports_collection.count_documents({})

    # last 7 days: group in Python so it works the same on every MongoDB version
    per_day = {}
    cutoff = _now() - timedelta(days=8)
    for d in scan_collection.find({"verdict": "SCAM", "created_at": {"$gte": cutoff}}, {"created_at": 1, "_id": 0}):
        local = (d["created_at"].replace(tzinfo=timezone.utc) - timedelta(minutes=tz_offset_minutes)).date()
        per_day[local.isoformat()] = per_day.get(local.isoformat(), 0) + 1

    today = (_now() - timedelta(minutes=tz_offset_minutes)).date()
    week = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        week.append({"day": day.strftime("%a"), "count": per_day.get(day.isoformat(), 0)})

    by_type = [
        {"label": r["_id"], "count": r["n"]}
        for r in scan_collection.aggregate([
            {"$match": {"verdict": "SCAM"}},
            {"$group": {"_id": "$type_label", "n": {"$sum": 1}}},
            {"$sort": {"n": -1}},
        ])
    ]
    recent = [
        {
            "id": str(d["_id"]),
            "summary": d.get("summary") or "(older scan)",
            "score": d["score"],
            "type": d["type"],
            "type_label": d["type_label"],
        }
        for d in scan_collection.find().sort("_id", -1).limit(6)
    ]
    return {
        "checks": checks, "scams": scams, "reports": reports,
        "scams_week": sum(w["count"] for w in week),
        "week": week, "by_type": by_type, "recent": recent,
    }