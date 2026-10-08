from validation.reviewer import review_qualitative

chunks = [{
    "source": "security_policy.txt",
    "content": "Passwords must be at least 14 characters and rotated every 90 days. All employees must use MFA.",
    "chunk": 0,
}]

# Check A: a faithful answer -> reviewer should say supported=True, high confidence
print("=== CHECK A: faithful answer (expect supported=True) ===")
print(review_qualitative(
    "What is the password policy?",
    "Passwords must be at least 14 characters and rotated every 90 days. [Source 1]",
    chunks,
))

# Check B: a fabricated answer -> reviewer should say supported=False
print("\n=== CHECK B: fabricated answer (expect supported=False) ===")
print(review_qualitative(
    "What is the password policy?",
    "Passwords must be at least 8 characters and never need to be changed. [Source 1]",
    chunks,
))