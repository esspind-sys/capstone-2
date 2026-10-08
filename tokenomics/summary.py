import json
from collections import defaultdict

LOG_PATH = "tokenomics_log.jsonl"

def load(path):
    entries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries

def summarise(entries):
    total_cost = sum(e["cost_usd"] for e in entries)
    total_in = sum(e["input_tokens"] for e in entries)
    total_out = sum(e["output_tokens"] for e in entries)

    per_agent = defaultdict(lambda: {"calls": 0, "in": 0, "out": 0, "cost": 0.0})
    for e in entries:
        a = per_agent[e["agent"]]
        a["calls"] += 1
        a["in"] += e["input_tokens"]
        a["out"] += e["output_tokens"]
        a["cost"] += e["cost_usd"]

    unique_queries = len({e["query"] for e in entries})

    print(f"Total Claude calls logged : {len(entries)}")
    print(f"Unique user queries       : {unique_queries}")
    print(f"Total input tokens        : {total_in:,}")
    print(f"Total output tokens       : {total_out:,}")
    print(f"Total cost (USD)          : ${total_cost:.4f}")
    print(f"Avg cost per user query   : ${total_cost / max(unique_queries, 1):.4f}")
    print("\nPer-agent breakdown:")
    print(f"{'agent':<20}{'calls':>7}{'in':>10}{'out':>8}{'cost($)':>12}")
    for name, a in sorted(per_agent.items(), key=lambda x: -x[1]["cost"]):
        print(f"{name:<20}{a['calls']:>7}{a['in']:>10,}{a['out']:>8,}{a['cost']:>12.4f}")

if __name__ == "__main__":
    summarise(load(LOG_PATH))