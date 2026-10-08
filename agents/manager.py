from bedrock_client import call_claude
from agents import qualitative, quantitative
from validation.validator import validate_qualitative, validate_quantitative
from validation.reviewer import review_qualitative
from tokenomics.logger import log

def classify(query: str) -> str:
    result = call_claude(
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": f"""Classify this query as exactly one of: qualitative, quantitative, both.

qualitative = questions about policies, processes, procedures, explanations, documentation
quantitative = questions about numbers, metrics, trends, comparisons, SQL-queryable data
both = questions that need both document search and data analysis

Query: {query}

Reply with one word only: qualitative, quantitative, or both.""",
        }],
    )
    route = result["text"].strip().lower()
    log(query, "manager-classifier", result["input_tokens"], result["output_tokens"])
    return route if route in ["qualitative", "quantitative", "both"] else "qualitative"

def run(query: str):
    print(f"\nQuery: {query}")
    route = classify(query)
    print(f"Route: {route}")

    if route in ["qualitative", "both"]:
        qual_result = qualitative.run(query)
        validation = validate_qualitative(qual_result["answer"], qual_result["chunks"])
        log(query, "qualitative", qual_result["input_tokens"], qual_result["output_tokens"])

        # SILVER: independent second-opinion review (skipped when Claude refused)
        if not validation["refused_to_answer"]:
            review = review_qualitative(query, qual_result["answer"], qual_result["chunks"])
            log(query, "reviewer", review["review_input_tokens"], review["review_output_tokens"])
            if review.get("supported") is False:
                print(f"\n[FLAG] Reviewer: answer may not be supported -- {review.get('reason')}")
            else:
                print(f"\n[OK] Reviewer: supported (confidence {review.get('confidence')})")

        if validation["flag"]:
            print(f"\n[WARNING] VALIDATION: {validation['warning']}")
        print(f"\n[Qualitative]\n{qual_result['answer']}")

    if route in ["quantitative", "both"]:
        quant_result = quantitative.run(query)
        validation = validate_quantitative(
            quant_result["answer"],
            quant_result["sql"],
            quant_result["validation"],
        )
        log(query, "quantitative", quant_result["input_tokens"], quant_result["output_tokens"])
        if validation["flag"]:
            print(f"\n[WARNING] VALIDATION: {validation['warning']}")
        print(f"\n[Quantitative]\n{quant_result['answer']}")
        print(f"SQL used: {quant_result['sql']}")