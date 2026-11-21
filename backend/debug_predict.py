"""Find where a wrong prediction comes from.
Usage:  python debug_predict.py "your message here"
Compare the numbers with your notebook's check function for the SAME message."""
import sys

from model_service import LABELS, LEGIT, MAX_LEN, THRESHOLD, clean, predict, probs, tokenizer

text = " ".join(sys.argv[1:]) or input("Message: ")

cleaned = clean(text)
n_tokens = len(tokenizer(cleaned, truncation=False)["input_ids"])
p = probs([text])[0]          # probs() cleans the text itself

print("\n1) cleaned text :", cleaned)
print(f"2) length       : {n_tokens} tokens (the model reads only the first {MAX_LEN})",
      "<-- TRUNCATED" if n_tokens > MAX_LEN else "")
print("3) class probabilities:")
for label, prob in sorted(zip(LABELS, p), key=lambda x: -x[1]):
    print(f"   {label:24s} {prob * 100:6.2f}%")
print(f"4) scam score    : {round((1 - p[LEGIT]) * 100)}  (verdict is SCAM at {THRESHOLD * 100:.0f} or more)")
print("5) full API result:", predict(text))