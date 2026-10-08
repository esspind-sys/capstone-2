from agents.quantitative import run, validate_sql

# Check A: a normal analytical question -> expect PASSED + an interpretation
r = run("What is the total revenue by region?")
print("=== CHECK A: answerable ===")
print("SQL:", r["sql"])
print("Validation:", r["validation"])
print("Answer:", r["answer"])
print(f"(tokens in/out: {r['input_tokens']}/{r['output_tokens']})\n")

# Check B: validate_sql in isolation -> a dangerous query must be blocked
print("=== CHECK B: validator blocks non-SELECT ===")
print(validate_sql("DROP TABLE sales;"))
print(validate_sql("DELETE FROM customers;"))
print(validate_sql("SELECT * FROM sales;"))
print()

# Check C: another real question to confirm consistency
r = run("Which department has the highest average employee satisfaction?")
print("=== CHECK C: aggregation question ===")
print("SQL:", r["sql"])
print("Validation:", r["validation"])
print("Answer:", r["answer"])