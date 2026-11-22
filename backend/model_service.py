
import json
import os
import re
from pathlib import Path
from typing import List

import numpy as np
import torch

from huggingface_hub import snapshot_download
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
)


# ============================================================
# 1. MODEL CONFIGURATION
# ============================================================

HF_MODEL_REPO = os.getenv(
    "HF_MODEL_REPO",
    "tabassum02/fraudshield-model"
)

# Newly uploaded model commit
HF_REVISION = os.getenv(
    "HF_REVISION",
    "19c379df32d7cc70a8b4282f8bbfd8f0728dc1ec"
)

HF_TOKEN = os.getenv("HF_TOKEN") or None

# Default model source is Hugging Face.
# Set MODEL_SOURCE=local only when using a local model.
MODEL_SOURCE = os.getenv("MODEL_SOURCE", "hf").lower()

LOCAL_MODEL_DIR = Path(
    os.getenv(
        "MODEL_DIR",
        str(Path(__file__).parent / "xlm-roberta-base")
    )
)

DEVICE = torch.device("cpu")
torch.set_num_threads(1)


# ============================================================
# 2. FIND MODEL DIRECTORY
# ============================================================

if MODEL_SOURCE == "hf":

    print("Downloading FraudShield model from Hugging Face...")
    print("Repository:", HF_MODEL_REPO)
    print("Revision:", HF_REVISION)

    MODEL_DIR = Path(
        snapshot_download(
            repo_id=HF_MODEL_REPO,
            revision=HF_REVISION,
            token=HF_TOKEN,
        )
    )

    print("Model downloaded:", MODEL_DIR)

elif MODEL_SOURCE == "local":

    if not (LOCAL_MODEL_DIR / "config.json").exists():
        raise FileNotFoundError(
            f"Local model not found: {LOCAL_MODEL_DIR}"
        )

    MODEL_DIR = LOCAL_MODEL_DIR
    print("Loading local model:", MODEL_DIR)

else:

    raise ValueError(
        "MODEL_SOURCE must be 'hf' or 'local'"
    )


# Verify model files

for filename in ["config.json", "scamdetect.json"]:

    if not (MODEL_DIR / filename).is_file():
        raise FileNotFoundError(
            f"Missing model file: {filename}"
        )

if not (
    (MODEL_DIR / "model.safetensors").exists()
    or (MODEL_DIR / "pytorch_model.bin").exists()
):
    raise FileNotFoundError("Model weights not found.")


# ============================================================
# 3. LOAD MODEL METADATA
# ============================================================

META_FILE = MODEL_DIR / "scamdetect.json"

META = json.loads(
    META_FILE.read_text(encoding="utf-8")
)

MAX_LEN = int(META.get("max_len", 128))

USE_BANGLA_NORMALIZER = bool(
    META.get("normalize", False)
)

THRESHOLD = float(
    os.getenv("SCAM_THRESHOLD", "0.50")
)

if not 0 <= THRESHOLD <= 1:
    raise ValueError("SCAM_THRESHOLD must be between 0 and 1")


# ============================================================
# 4. TEXT CLEANING
# Same preprocessing used during training
# ============================================================

BN = "\u0980-\u09FF"

URL_RE = re.compile(
    r"https?://\S+"
    r"|\b\w+\.(?:com|io|xyz|top|click|online)\S*"
    r"|\b(?:bit\.ly|t\.me|wa\.me|cutt\.ly)/\S+"
)

PHONE_RE = re.compile(r"01[3-9]\d{8}")

BN_DIGITS = str.maketrans(
    "০১২৩৪৫৬৭৮৯",
    "0123456789"
)


def clean(text: str) -> str:

    text = str(text).translate(BN_DIGITS).lower()

    text = URL_RE.sub(" urltoken ", text)

    text = PHONE_RE.sub(" phonetoken ", text)

    text = re.sub(r"\d+", " num ", text)

    text = re.sub(
        rf"[^\w\s{BN}]",
        " ",
        text
    )

    return re.sub(r"\s+", " ", text).strip()


def apply_optional_normalizer(texts: List[str]) -> List[str]:

    if not USE_BANGLA_NORMALIZER:
        return texts

    try:
        from normalizer import normalize as bn_normalize

    except ImportError as exc:
        raise RuntimeError(
            "Bangla normalizer is required but not installed."
        ) from exc

    return [
        bn_normalize(text)
        for text in texts
    ]


# ============================================================
# 5. LOAD TRAINED XLM-ROBERTA MODEL
# ============================================================

print("Loading tokenizer...")

tokenizer = AutoTokenizer.from_pretrained(
    str(MODEL_DIR)
)

print("Loading classification model...")

model = AutoModelForSequenceClassification.from_pretrained(
    str(MODEL_DIR)
)

model = model.to(DEVICE).float().eval()


# Verify architecture

if model.config.model_type != "xlm-roberta":

    raise ValueError(
        f"Wrong model architecture: {model.config.model_type}"
    )

if model.config.num_labels != 9:

    raise ValueError(
        f"Expected 9 classes, found {model.config.num_labels}"
    )

print("Verified architecture: XLM-RoBERTa")
print("Verified classes:", model.config.num_labels)
print("Model loaded into CPU memory.")


# ============================================================
# 6. LOAD AND VERIFY LABELS
# ============================================================

raw_id2label = model.config.id2label

LABELS = [
    raw_id2label.get(
        i,
        raw_id2label.get(str(i))
    )
    for i in range(model.config.num_labels)
]

EXPECTED_LABELS = {
    "legit",
    "bank_phishing",
    "mobile_money_fraud",
    "prize_lottery",
    "job_scam",
    "loan_investment_fraud",
    "govt_impersonation",
    "parcel_delivery_scam",
    "romance_sextortion",
}

if len(LABELS) != 9 or set(LABELS) != EXPECTED_LABELS:

    raise ValueError(
        f"Model labels are incorrect: {LABELS}"
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
# 7. SEXTORTION DETECTION
# ============================================================

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
            re.IGNORECASE
        )
        for pattern in SEXTORTION_PATTERNS
    )


# ============================================================
# 8. MODEL PROBABILITIES
# ============================================================

@torch.inference_mode()
def probs(
    texts: List[str],
    batch_size: int = 32
) -> np.ndarray:

    if not texts:

        return np.empty(
            (0, len(LABELS)),
            dtype=np.float32
        )

    texts = [
        clean(text)
        for text in texts
    ]

    texts = apply_optional_normalizer(texts)

    results = []

    for start in range(0, len(texts), batch_size):

        batch = texts[start:start + batch_size]

        encoded = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=MAX_LEN,
            return_tensors="pt"
        )

        encoded = {
            key: value.to(DEVICE)
            for key, value in encoded.items()
        }

        logits = model(**encoded).logits.float()

        probabilities = torch.softmax(
            logits,
            dim=-1
        )

        results.append(
            probabilities.cpu().numpy()
        )

    return np.concatenate(results, axis=0)


# ============================================================
# 9. SCAM HIGHLIGHTS
# ============================================================

WORD = re.compile(r"\S+")


def highlights(
    text: str,
    max_words: int = 60,
    cutoff: float = 0.35,
    top_k: int = 4
):

    words = list(
        WORD.finditer(text)
    )[:max_words]

    if len(words) < 2:
        return []

    variants = [text] + [
        text[:word.start()] + text[word.end():]
        for word in words
    ]

    scam = np.clip(
        1 - probs(variants)[:, LEGIT],
        1e-6,
        1 - 1e-6
    )

    logits = np.log(
        scam / (1 - scam)
    )

    drop = np.maximum(
        logits[0] - logits[1:],
        0
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
# 10. RULE-BASED WARNING FLAGS
# These flags do not change the model prediction.
# ============================================================

RULES = [

    (
        r"urgent(ly)?|immediately|act now|last warning|"
        r"within \d+ (hours?|minutes?)",
        18,
        "Pressure to act fast"
    ),

    (
        r"\botp\b|\bpin\b|password|\bcvv\b|"
        r"one[- ]time (code|password)",
        30,
        "Asks for a secret code"
    ),

    (
        r"https?://\S+|www\.\S+|"
        r"\b\w+\.(com|net|org|xyz|top|click|online)\S*",
        15,
        "Contains a link"
    ),

    (
        r"suspend(ed)?|blocked|locked|verify your account|"
        r"unusual activity",
        18,
        "Threat to your account"
    ),

    (
        r"\bwon\b|prize|lottery|reward|gift card|claim your",
        20,
        "Prize or reward bait"
    ),

    (
        r"send (money|funds)|wire|bitcoin|crypto|transfer",
        15,
        "Asks for money"
    ),

    (
        r"blackmail|sextortion|intimate photos|"
        r"private pictures|nude photos",
        30,
        "Sexual blackmail or sextortion"
    ),

]


def rule_flags(text: str):

    flags = []

    for pattern, weight, label in RULES:

        count = len(
            re.findall(
                pattern,
                text,
                re.IGNORECASE
            )
        )

        if count:

            flags.append({
                "label": label,
                "weight": weight,
                "count": count
            })

    return flags


# ============================================================
# 11. MAIN PREDICTION FUNCTION
# ============================================================

def predict(text: str) -> dict:

    text = str(text).strip()

    if not text:
        raise ValueError("Message cannot be empty")

    if len(text) > 2000:
        raise ValueError("Message is too long")


    # A. Model probabilities

    probabilities = probs([text])[0]

    legit_probability = float(
        probabilities[LEGIT]
    )

    scam_probability = 1.0 - legit_probability


    # B. Scam or legitimate classification

    is_scam = scam_probability >= THRESHOLD

    scam_indices = [
        i
        for i, label_name in enumerate(LABELS)
        if label_name != "legit"
    ]

    best_scam_index = max(
        scam_indices,
        key=lambda i: probabilities[i]
    )

    if is_scam:

        best_index = best_scam_index
        label = LABELS[best_index]

    else:

        best_index = LEGIT
        label = "legit"

    type_probability = float(
        probabilities[best_index]
    )


    # C. Scam score

    score = round(
        scam_probability * 100,
        2
    )


    # D. Warning flags

    flags = rule_flags(text)

    if is_sextortion(text):

        if not any(
            flag["label"] == "Sexual blackmail or sextortion"
            for flag in flags
        ):

            flags.append({
                "label": "Sexual blackmail or sextortion",
                "weight": 30,
                "count": 1
            })

    if is_scam:

        main_label = TYPE_NAMES.get(label, label)

        if not any(
            flag["label"] == main_label
            for flag in flags
        ):

            flags.insert(0, {
                "label": main_label,
                "weight": 30,
                "count": 1
            })


    # E. Highlights

    highlighted_words = (
        highlights(text)
        if is_scam
        else []
    )


    # F. Risk level

    if score >= 61:
        risk_level = "High Risk"

    elif score >= 31:
        risk_level = "Medium Risk"

    else:
        risk_level = "Low Risk"


    # G. Final message

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


    # H. API response
    # Keep the existing frontend response structure unchanged.

    return {

        "score": score,

        "verdict": (
            "SCAM" if is_scam else "NOT SCAM"
        ),

        "risk_level": risk_level,

        "type": label,

        "type_label": TYPE_NAMES.get(label, label),

        "type_probability": round(
            type_probability * 100,
            2
        ),

        "legit_probability": round(
            legit_probability * 100,
            2
        ),

        "flags": flags,

        "highlights": highlighted_words,

        "message": message,

    }


# ============================================================
# 12. MODEL WARM-UP
# ============================================================

predict("hello")

print("FraudShield XLM-RoBERTa model loaded successfully.")

print("Model repository:", HF_MODEL_REPO)

print(
    "Model revision:",
    HF_REVISION if MODEL_SOURCE == "hf" else "local"
)

print("Model directory:", MODEL_DIR)

print("Labels:", LABELS)

print("Threshold:", THRESHOLD)

print("Device:", DEVICE)
