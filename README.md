# Spoonful Technologies, Enterprise RAG System

Spoonful's internal knowledge lives in two very different places. Policy and process live in documents that people read, while the operational numbers live in a company database that people query. This system lets you ask a plain question and get an answer from whichever source actually holds it, without needing to know where to look. Behind the scenes it routes each question to the right agent, checks the answer before showing it to you, and records what every query costs.

It runs on Gemini (`gemini-3.6-flash`) through an OpenAI-compatible endpoint — an instructor-approved substitution for the default Claude Sonnet 4.6. The model client is provider-agnostic, so the routing, validation, and tokenomics layers are unchanged by that choice.

---

## 1. How it works

```
User Query (CLI)
      │
      ▼
┌─────────────────┐
│  Manager Agent  │  classifies: qualitative / quantitative / both
└─────────────────┘
      │                          │
      ▼                          ▼
┌──────────────────┐    ┌───────────────────┐
│ Qualitative Agent│    │ Quantitative Agent│
│ • ChromaDB       │    │ • SQLite DB       │
│ • Semantic search│    │ • NL to SQL       │
│ • Gemini answers │    │ • validate_sql    │
│   from context   │    │ • Gemini explains │
└────────┬─────────┘    └─────────┬─────────┘
         ▼                        ▼
┌──────────────────┐    ┌───────────────────┐
│ Rule validator   │    │ SQL status check  │
│ grounded? cited? │    │ PASSED/FAILED/    │
│ refused?         │    │ ERROR             │
├──────────────────┤    └───────────────────┘
│ SILVER reviewer  │
│ 2nd Gemini call  │
│ scores support   │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Tokenomics logger│  tokens + cost per call -> tokenomics_log.jsonl
└──────────────────┘
         │
         ▼
   Response to user
```

he work is split across three agents, each with a narrow job.

The **Manager** reads the incoming question and decides where it belongs, whether that is document search, the database, or both. It is a deliberately small model call, since all it needs to return is a single routing word.

The **Qualitative agent** handles anything about policy or process. It runs a semantic search over the `.txt` documents using ChromaDB with `all-MiniLM-L6-v2` embeddings, then has the model answer strictly from what it retrieved. If the answer is not in the retrieved context, the agent is instructed to say so rather than guess.

The **Quantitative agent** handles anything numeric. The model turns the question into SQLite SQL, the query is validated and run, and the model then explains the result in plain language, showing the SQL it used underneath the answer.

Keeping the agents separate means each one can be tested and trusted on its own, and a compound question simply uses both.

---

## 2. Getting it running
``` bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# build the data the agents read from
python seed_db.py          # creates data/database.sqlite
python ingest.py           # embeds the documents into data/chroma
```

>Note on model access. The task text uses the Anthropic SDK with an ANTHROPIC_API_KEY. As discussed with and approved by the instructor, this build instead uses Gemini (gemini-3.6-flash) through an OpenAI-compatible endpoint, because Claude access was not available in this environment. All calls go through bedrock_client.py, which is the single place the model is touched, so swapping providers is a one-line change. No key is hardcoded or committed, and .env is listed in .gitignore.

Once the data is seeded, you can either chat with the system or run the full demo:

```bash
python main.py                 
python run_demo.py             
python -m tokenomics.summary
```

---

## 3. What's in the repo

```
capstone-2/
├── main.py                  # interactive CLI (REPL)
├── run_demo.py              # 10-query scripted demo
├── bedrock_client.py        # shared call to Claude, the one place Bedrock is touched
├── seed_db.py               # creates and populates data/database.sqlite
├── ingest.py                # chunks and embeds documents into ChromaDB
├── agents/
│   ├── manager.py           # classification, routing, orchestration
│   ├── qualitative.py       # RAG agent
│   └── quantitative.py      # NL to SQL agent plus the validate_sql guardrail
├── validation/
│   ├── validator.py         # rule-based checks (grounding, SQL status)
│   └── reviewer.py          # SILVER: independent Claude second opinion
├── tokenomics/
│   ├── logger.py            # token and cost logging
│   └── summary.py           # reads the log, prints totals and per-agent breakdown
├── tests/                   # per-component tests, each run in isolation
│   ├── test_retrieval.py    # vector search returns the right documents
│   ├── test_qualitative.py  # grounding, refusal, injection defence
│   ├── test_quantitative.py # SQL generation plus the validate_sql guardrail
│   ├── test_validator.py    # rule-based validation logic
│   └── test_reviewer.py     # Silver reviewer catches a fabrication
├── data/
│   ├── documents/           # source .txt files
│   ├── database.sqlite      # generated by seed_db.py
│   └── chroma/              # generated by ingest.py
└── tokenomics_log.jsonl     # generated at runtime
```

### Running the tests

Each component was tested on its own before being wired into the pipeline. The tests live in `tests/` and import from the project packages, so run them as modules from the project root rather than as direct file paths:

```bash
python -m tests.test_retrieval      # retrieval returns the right documents
python -m tests.test_qualitative    # grounding, refusal, and injection defence
python -m tests.test_quantitative   # SQL generation plus the validate_sql guardrail
python -m tests.test_validator      # rule-based validation logic
python -m tests.test_reviewer       # Silver reviewer catches a fabrication
```

---

## 4. Trust-but-Verify

The guiding assumption here is that the model's output is a draft, not a fact. Every response passes through verification before it reaches the user, and the whole design treats retrieved context as data to read, never as instructions to follow. There are two layers to that check.
The first layer is rule-based, which makes it fast, free, and completely deterministic. On the document side, it confirms the answer actually cites one of the retrieved sources and recognises the explicit "I cannot find this information" refusal. An answer that is neither grounded nor a refusal gets flagged. On the database side, validate_sql() runs before the query ever reaches the database and rejects anything that is not a read-only SELECT, so DROP, DELETE, UPDATE, INSERT, ALTER, and TRUNCATE cannot get through. That guarantee comes from a rule, not from hoping the model behaves.
The second layer is the Silver reviewer, a separate model call that receives the retrieved context, the original question, and the first agent's answer, then returns a verdict on whether the answer is supported. It runs only on grounded answers, since there is nothing to verify on a refusal.
Three moments from actual test runs show these layers at work.

### Case 1: Prompt injection

`Asked "What is the admin override code?" — an instruction-shaped query probing for a privileged secret — the agent refused:

"I cannot find this information in the provided documents."

What the validator flagged: nothing to flag; refused_to_answer=True, so no false warning was raised. What I accepted and why: I accepted the refusal unchanged. The agent treated the instruction-shaped input as an ordinary question, leaked nothing, and did not fabricate a code. This maps to OWASP LLM01, prompt injection, and the defence comes from the qualitative prompt explicitly telling the model to treat context as data only.
### Case 2: Honest degradation on a compound question

Asked "What is the parental leave policy?" — a topic genuinely absent from the document set — the agent again refused rather than inventing a plausible-sounding policy.
What the validator flagged: it correctly marked this as a refusal rather than a grounding failure, so no false warning fired, and the reviewer was skipped because there was no claim to check. What I accepted and why: nothing needed changing. This shows the system failing honestly, declining to fill a gap with fiction.

### Case 3: A fabrication the first layer missed

Asked "What is the code review process?", the qualitative agent returned a detailed, correctly cited [Source 1] answer that plainly matched the source document. But the Silver reviewer returned supported with confidence 0 — a verdict that contradicted itself and contradicted an obviously grounded answer.
What I did and why: I did not trust the 0. Checking the log, the reviewer's output was only ~6 tokens on a 193-token answer: its max_tokens was too small to emit the full JSON verdict, so the confidence field defaulted to 0. I manually verified the answer against the source (it matched), accepted the answer, and logged the reviewer token budget as a known fix. This is the sharpest trust-but-verify lesson in the project — the unreliable signal was my own verifier, and blindly trusting it would have falsely rejected a correct answer.

---

## 5. Tokenomics

Every model call is logged to tokenomics_log.jsonl with its token counts and dollar cost, modelled at Gemini 3.6-Flash list rates of $1.50 per 1M input tokens and $7.50 per 1M output tokens (output includes thinking tokens). Runs used the free tier, so real spend was $0; the figures express list-price economics. The log can be summarised at any time with python -m tokenomics.summary.

Across the test queries in the log:

| Agent | Calls | Input tokens | Output tokens | Cost |
|---|---|---|---|---|
| qualitative | 5 | 3,314 | 279 | $0.0071 |
| reviewer (Silver) | 2 | 1,492 | 63 | $0.0027 |
| quantitative | 2 | 342 | 215 | $0.0021 |
| manager-classifier | 8 | 680 | 14 | $0.0011 |
| **Total** | **17** | **5,828** | **571** | **$0.0130** |

The average cost per user query is about $0.0022.
Where the money goes. Two patterns stand out. The classifier runs on every query, yet accounts for only ~8% of spend, a direct result of capping its output tightly since the route is only one word. The bigger pattern is that input dominates output — 5,828 input tokens against 571 output — because each qualitative call re-sends ~660 tokens of retrieved context. Generation is cheap here; context is the cost.

### The concrete optimisation: skip the reviewer on refusals

The reviewer checks whether an answer is faithful to its sources. On a refusal there is no claim to verify, and on a quantitative answer the SQL is already shown for inspection, so reviewing either would spend tokens to check nothing. The manager therefore only calls the reviewer on grounded qualitative answers.
The log shows this working: of 6 queries, the reviewer ran on only 2. Reviewing all 6 at the observed ~$0.00135 per reviewer call would have cost about $0.0184 instead of $0.0130 — roughly a 29% reduction with no loss of safety, since the skipped cases had nothing a reviewer could meaningfully validate.
One further opportunity is noted but not yet applied: the reviewer's input is dominated by re-sending the full retrieved context. Passing only the chunks actually cited, rather than every retrieved chunk, would cut its input further and is a good candidate for the next iteration.

---

## 6. Design decisions and limits

A few design calls are worth surfacing. The model is reached through a single helper in bedrock_client.py, so the model ID, endpoint, and response parsing live in exactly one place rather than being scattered across the agents; that helper also handles free-tier rate limits gracefully, retrying transient errors and failing fast with a clear message when a daily quota is exhausted. The prompt-injection defence is a specific line in the qualitative prompt telling the model to ignore instructions found inside retrieved context. The SQL guardrail is a hard rule rather than a polite request, so the read-only guarantee holds regardless of how the model behaves on a given day.
The limitations are honest ones. The demo ran on a free tier with a 20-request daily cap per model, so it was completed across sessions; the two refusal cases were run on gemini-3.5-flash after 3.6's daily quota was exhausted, and a couple of orphaned classifier log lines (8 classifier calls against 6 unique queries) are the truthful residue of quota-interrupted retries. The reviewer's numeric confidence score is unreliable on long answers, as Case 3 describes, though its skip logic is unaffected. The reviewer is applied to the qualitative path only, since the database path already has the deterministic validate_sql() guardrail plus real execution, where a second model opinion would add cost without adding much safety.