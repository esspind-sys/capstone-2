from validation.validator import validate_qualitative, validate_quantitative

chunks = [{"source": "security_policy.txt", "chunk": 0},
          {"source": "customer_support.txt", "chunk": 0}]

# Check A: a grounded answer that cites Source 1 -> should NOT flag
print("=== CHECK A: grounded + cited (expect flag=False) ===")
print(validate_qualitative("Per [Source 1] passwords must be 14 chars.", chunks))

# Check B: an ungrounded answer with no citation -> SHOULD flag
print("\n=== CHECK B: ungrounded, no citation (expect flag=True) ===")
print(validate_qualitative("Passwords should probably be strong.", chunks))

# Check C: a refusal -> should NOT flag (refusing is correct behaviour)
print("\n=== CHECK C: refusal (expect flag=False) ===")
print(validate_qualitative("I cannot find this information in the provided documents.", chunks))

# Check D: quantitative statuses
print("\n=== CHECK D: quantitative (PASSED ok, FAILED/ERROR flagged) ===")
print(validate_quantitative("ok", "SELECT * FROM sales", "PASSED"))
print(validate_quantitative("blocked", "DROP TABLE sales", "FAILED"))
print(validate_quantitative("error", "SELECT bad", "ERROR"))