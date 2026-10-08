import json
import re
from bedrock_client import call_claude

def review_qualitative(query: str, answer: str, chunks: list[dict]) -> dict:
    context = "\n\n".join(f"[{c['source']}] {c['content']}" for c in chunks)

    result = call_claude(
        max_tokens=256,
        messages=[{
            "role": "user",
            "content": f"""You are an independent reviewer. Judge whether the ANSWER is fully supported by the CONTEXT.

CONTEXT:
{context}

QUESTION: {query}
ANSWER: {answer}

Respond in JSON only:
{{"supported": true/false, "confidence": 0-100, "reason": "one sentence"}}""",
        }],
    )

    review = _parse_json(result["text"])
    review["review_input_tokens"] = result["input_tokens"]
    review["review_output_tokens"] = result["output_tokens"]
    return review

def _parse_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return {"supported": None, "confidence": 0, "reason": "Could not parse reviewer response"}