import os
import time
from openai import OpenAI, RateLimitError, InternalServerError
from dotenv import load_dotenv

load_dotenv()

_client = OpenAI(
    api_key=os.environ["GEMINI_API_KEY"],
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

MODEL_ID = "gemini-3.5-flash"   # fresh daily quota vs exhausted 3.5

# Free tier: 5 req/min AND 20 req/day. Space calls to respect the per-minute cap.
_MIN_INTERVAL = 15.0
_last_call_time = [0.0]


def _throttle():
    elapsed = time.time() - _last_call_time[0]
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _last_call_time[0] = time.time()


def call_claude(prompt=None, messages=None, system=None,
                max_tokens=500, temperature=0.2, **kwargs):
    """
    Gemini via the OpenAI-compatible endpoint. Accepts a plain `prompt` string
    OR a `messages` list, plus optional `system`. Throttles to the per-minute
    free-tier limit. Retries per-minute 429s and transient 503s. Fails fast on
    the per-DAY quota. Return keys match the old Claude helper.
    """
    oai_messages = []
    if system:
        oai_messages.append({"role": "system", "content": system})

    if messages is not None:
        for m in messages:
            content = m.get("content", "")
            if isinstance(content, list):
                content = " ".join(
                    block.get("text", "") for block in content
                    if isinstance(block, dict)
                )
            oai_messages.append({"role": m.get("role", "user"), "content": content})
    elif prompt is not None:
        oai_messages.append({"role": "user", "content": prompt})
    else:
        raise ValueError("call_claude needs either `prompt` or `messages`.")

    resp = None
    for attempt in range(6):
        try:
            _throttle()
            resp = _client.chat.completions.create(
                model=MODEL_ID,
                messages=oai_messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            break
        except RateLimitError as e:
            msg = str(e)
            # Per-DAY quota is hopeless to retry (resets in hours). Bail loudly.
            if "PerDay" in msg or "per day" in msg.lower():
                raise RuntimeError(
                    "Daily free-tier quota (20 req/day) exhausted for this model. "
                    "Switch MODEL_ID to another gemini model or use a new Google "
                    "account/key for a fresh quota."
                ) from e
            if attempt == 5:
                raise
            wait = 20 * (attempt + 1)   # per-minute 429 backoff
            print(f"[rate-limit] waiting {wait}s then retrying...")
            time.sleep(wait)
        except InternalServerError:
            # 503 "high demand" — transient server overload, retry a few times.
            if attempt == 5:
                raise
            wait = 10 * (attempt + 1)   # 10s, 20s, 30s...
            print(f"[server-busy 503] waiting {wait}s then retrying...")
            time.sleep(wait)

    usage = resp.usage
    text = resp.choices[0].message.content
    return {
        "text": text if text is not None else "",
        "input_tokens": usage.prompt_tokens if usage else 0,
        "output_tokens": usage.completion_tokens if usage else 0,
    }