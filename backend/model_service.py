
import json
import os
import re
from pathlib import Path
from typing import List
from huggingface_hub import snapshot_download
import numpy as np
import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
)


# ============================================================
# 1. MODEL CONFIGURATION
# ============================================================

MODEL_DIR = Path(
    os.getenv(
        "MODEL_DIR",
        str(Path(__file__).parent / "xlm-roberta-base"),
    )
)

META_FILE = MODEL_DIR / "scamdetect.json"

if not MODEL_DIR.exists():
    raise FileNotFoundError(
        f"Model directory not found: {MODEL_DIR}"
    )

META = (
    json.loads(META_FILE.read_text(encoding="utf-8"))
    if META_FILE.exists()
    else {}
)

MAX_LEN = int(META.get("max_len", 128))

THRESHOLD = float(
    os.getenv("SCAM_THRESHOLD", "0.50")
)

DEVICE = torch.device("cpu")


# ============================================================
# 2. TEXT CLEANING
# ============================================================

BN = "\u0980-\u09FF"

URL_RE = re.compile(
    r"https?://\S+"
    r"|www\.\S+"
    r"|\b\w+\.(?:com|io|xyz|top|click|online|net|org|info|biz)\S*"
    r"|\b(?:bit\.ly|t\.me|wa\.me|cutt\.ly|tinyurl\.com)/\S*",
    re.IGNORECASE,
)

PHONE_RE = re.compile(r"01[3-9]\d{8}")

BN_DIGITS = str.maketrans(
    "০১২৩৪৫৬৭৮৯",
    "0123456789",
)


def clean(text: str) -> str:
    """
    Normalize message before model inference.

    IMPORTANT:
    This preprocessing must match the preprocessing
    used during model training.
    """

    text = str(text).translate(BN_DIGITS).lower()

    text = URL_RE.sub(" urltoken ", text)

    text = PHONE_RE.sub(" phonetoken ", text)

    text = re.sub(r"\d+", " num ", text)

    text = re.sub(
        rf"[^\w\s{BN}]",
        " ",
        text,
    )

    text = re.sub(r"\s+", " ", text).strip()

    return text


# ============================================================
# 3. LOAD TRAINED XLM-ROBERTA MODEL
# ============================================================

tokenizer = AutoTokenizer.from_pretrained(
    str(MODEL_DIR)
)

model = AutoModelForSequenceClassification.from_pretrained(
    str(MODEL_DIR)
)

model = model.to(DEVICE).float().eval()

id2label = model.config.id2label

LABELS = [
    id2label[i] if i in id2label else id2label[str(i)]
    for i in range(model.config.num_labels)
]

if len(LABELS) != 9:
    raise ValueError(
        f"Expected 9 classes, found {len(LABELS)}"
    )

if "legit" not in LABELS:
    raise ValueError(
        f"'legit' label missing: {LABELS}"
    )

LEGIT = LABELS.index("legit")


TYPE_NAMES = {
    "legit": "Looks legitimate",
    "bank_phishing": "Bank or account phishing",
    "mobile_money_fraud": "Mobile money fraud",
    "prize_lottery": "Prize or lottery scam",
    "job_scam": "Job scam",
    "loan_investment_fraud": "Loan or investment fraud",
    "govt_impersonation": "Government impersonation",
    "parcel_delivery_scam": "Parcel or delivery scam",
    "romance_sextortion": "Romance or sextortion scam",
}


# ============================================================
# 4. SEXTORTION DETECTION
# ============================================================

# This detector is used only for additional warning flags.
# It DOES NOT override the ML model prediction.

SEXTORTION_PATTERNS = [

    (
        r"(expose|leak|publish|share|post).{0,60}"
        r"(private|intimate|nude|naked|personal).{0,30}"
        r"(photo|picture|video|image)s?"
    ),

    (
        r"(private|intimate|nude|naked).{0,30}"
        r"(photo|picture|video|image)s?.{0,60}"
        r"(expose|leak|publish|share|post)"
    ),

    (
        r"(pay|send|give).{0,30}(money|cash).{0,60}"
        r"(leak|expose|publish|share)"
    ),

    r"(blackmail|sextortion)",

    (
        r"(recorded|saved).{0,40}"
        r"(private|intimate).{0,30}"
        r"(video|photo|picture).{0,60}"
        r"(leak|expose|publish)"
    ),

]


def is_sextortion(text: str) -> bool:

    normalized = clean(text)

    return any(
        re.search(
            pattern,
            normalized,
            re.IGNORECASE,
        )
        for pattern in SEXTORTION_PATTERNS
    )


# ============================================================
# 5. MODEL PROBABILITIES
# ============================================================

@torch.inference_mode()
def probs(texts: List[str], batch_size: int = 32):

    if not texts:
        return np.empty(
            (0, len(LABELS)),
            dtype=np.float32,
        )

    texts = [
        clean(text)
        for text in texts
    ]

    results = []

    for i in range(0, len(texts), batch_size):

        batch = texts[i:i + batch_size]

        encoded = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=MAX_LEN,
            return_tensors="pt",
        )

        encoded = {
            key: value.to(DEVICE)
            for key, value in encoded.items()
        }

        logits = model(**encoded).logits.float()

        probabilities = torch.softmax(
            logits,
            dim=-1,
        )

        results.append(
            probabilities.cpu().numpy()
        )

    return np.concatenate(results, axis=0)


# ============================================================
# 6. SCAM HIGHLIGHTS
# ============================================================

WORD = re.compile(r"\S+")


def highlights(
    text: str,
    max_words: int = 60,
    cutoff: float = 0.35,
    top_k: int = 4,
):

    words = list(WORD.finditer(text))[:max_words]

    if len(words) < 2:
        return []

    variants = [text] + [
        text[:word.start()] + text[word.end():]
        for word in words
    ]

    scam = np.clip(
        1 - probs(variants)[:, LEGIT],
        1e-6,
        1 - 1e-6,
    )

    logits = np.log(
        scam / (1 - scam)
    )

    drop = np.maximum(
        logits[0] - logits[1:],
        0,
    )

    if drop.size == 0 or drop.max() <= 0:
        return []

    weights = drop / drop.max()

    selected = sorted(
        np.argsort(-weights)[:top_k]
    )

    spans = [
        [words[i].start(), words[i].end()]
        for i in selected
        if weights[i] >= cutoff
    ]

    merged = []

    for start, end in spans:

        if merged and start - merged[-1][1] <= 1:
            merged[-1][1] = end

        else:
            merged.append([start, end])

    return merged


# ============================================================
# 7. RULE-BASED WARNING FLAGS
# ============================================================

RULES = [

    (
        r"urgent(ly)?|immediately|act now|last warning|"
        r"within \d+ (hours?|minutes?)",
        18,
        "Pressure to act fast",
    ),

    (
        r"\botp\b|\bpin\b|password|\bcvv\b|"
        r"one[- ]time (code|password)",
        30,
        "Asks for a secret code",
    ),

    (
        r"https?://\S+|www\.\S+|"
        r"\b\w+\.(com|net|org|xyz|top|click|online)\S*",
        15,
        "Contains a link",
    ),

    (
        r"suspend(ed)?|blocked|locked|verify your account|"
        r"unusual activity",
        18,
        "Threat to your account",
    ),

    (
        r"\bwon\b|prize|lottery|reward|gift card|claim your",
        20,
        "Prize or reward bait",
    ),

    (
        r"send (money|funds)|wire|bitcoin|crypto|transfer",
        15,
        "Asks for money",
    ),

    (
        r"blackmail|sextortion|intimate photos|"
        r"private pictures|nude photos",
        30,
        "Sexual blackmail or sextortion",
    ),

]


def rule_flags(text: str):

    flags = []

    for pattern, weight, label in RULES:

        count = len(
            re.findall(
                pattern,
                text,
                re.IGNORECASE,
            )
        )

        if count:

            flags.append({
                "label": label,
                "weight": weight,
                "count": count,
            })

    return flags


# ============================================================
# 8. MAIN PREDICTION FUNCTION
# ============================================================

def predict(text: str) -> dict:

    text = str(text).strip()

    if not text:
        raise ValueError(
            "Message cannot be empty"
        )

    if len(text) > 2000:
        raise ValueError(
            "Message is too long"
        )

    # --------------------------------------------------------
    # A. GET MODEL PROBABILITIES
    # --------------------------------------------------------

    probabilities = probs([text])[0]

    legit_probability = float(
        probabilities[LEGIT]
    )

    # Total probability of all scam classes
    scam_probability = 1.0 - legit_probability

    # --------------------------------------------------------
    # B. MODEL-BASED CLASSIFICATION
    # --------------------------------------------------------

    is_scam = scam_probability >= THRESHOLD

    scam_indices = [
        i
        for i, label_name in enumerate(LABELS)
        if label_name != "legit"
    ]

    best_scam_index = max(
        scam_indices,
        key=lambda i: probabilities[i],
    )

    if is_scam:

        best_index = best_scam_index

        label = LABELS[best_index]

    else:

        best_index = LEGIT

        label = "legit"

    # The selected class probability comes directly
    # from the trained model.
    type_probability = float(
        probabilities[best_index]
    )

    # --------------------------------------------------------
    # C. SCAM SCORE
    # --------------------------------------------------------

    score = round(
        scam_probability * 100,
        2,
    )

    # --------------------------------------------------------
    # D. ADDITIONAL WARNING FLAGS
    # --------------------------------------------------------

    flags = rule_flags(text)

    if is_sextortion(text):

        sextortion_flag_exists = any(
            flag["label"] == "Sexual blackmail or sextortion"
            for flag in flags
        )

        if not sextortion_flag_exists:

            flags.append({
                "label": "Sexual blackmail or sextortion",
                "weight": 30,
                "count": 1,
            })

    if is_scam:

        main_label = TYPE_NAMES.get(
            label,
            label,
        )

        if not any(
            flag["label"] == main_label
            for flag in flags
        ):

            flags.insert(0, {
                "label": main_label,
                "weight": 30,
                "count": 1,
            })

    # --------------------------------------------------------
    # E. HIGHLIGHTS
    # --------------------------------------------------------

    highlighted_words = (
        highlights(text)
        if is_scam
        else []
    )

    # --------------------------------------------------------
    # F. RISK LEVEL
    # --------------------------------------------------------

    if score >= 61:

        risk_level = "High Risk"

    elif score >= 31:

        risk_level = "Medium Risk"

    else:

        risk_level = "Low Risk"

    # --------------------------------------------------------
    # G. FINAL MESSAGE
    # --------------------------------------------------------

    if is_scam:

        message = (
            "This message contains suspicious patterns. "
            "Be careful before responding."
        )

    else:

        message = (
            "This message looks legitimate. "
            "Nothing suspicious was detected."
        )

    # --------------------------------------------------------
    # H. API RESPONSE
    # --------------------------------------------------------

    return {

        "score": score,

        "verdict": (
            "SCAM" if is_scam else "NOT SCAM"
        ),

        "risk_level": risk_level,

        "type": label,

        "type_label": TYPE_NAMES.get(
            label,
            label,
        ),

        "type_probability": round(
            type_probability * 100,
            2,
        ),

        "legit_probability": round(
            legit_probability * 100,
            2,
        ),

        "flags": flags,

        "highlights": highlighted_words,

        "message": message,

    }


# ============================================================
# 9. MODEL WARM-UP
# ============================================================

predict("hello")

print(
    "XLM-RoBERTa Scam Detector Loaded Successfully"
)

print("Model directory:", MODEL_DIR)

print("Labels:", LABELS)

print("Threshold:", THRESHOLD)

print("Device:", DEVICE)
