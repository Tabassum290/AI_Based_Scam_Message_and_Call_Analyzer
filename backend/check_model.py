
from model_service import probs, LABELS, LEGIT, predict

test_messages = [
    "Hello, how are you?",
    "I will text you later.",
    "Good morning. Have a nice day.",
    "Thank you for your help.",
    "Your account is blocked. Send your OTP immediately.",
    "Congratulations! You won $1000. Claim your prize now."
]

print("\nMODEL LABEL INFORMATION")
print("-----------------------")
print("Labels:", LABELS)
print("Legit index:", LEGIT)

print("\nPREDICTION RESULTS")
print("=================")

for text in test_messages:
    probabilities = probs([text])[0]
    result = predict(text)

    print("\nMessage:", text)
    print("Verdict:", result["verdict"])
    print("Scam Score:", result["score"], "%")

    print("Class Probabilities:")
    for label, probability in zip(LABELS, probabilities):
        print(f"  {label}: {probability * 100:.2f}%")
