"""
RecallOS Model Routing & Latency Benchmark Suite
Evaluates dynamic model routing accuracy, latency distribution, and throughput
between NVIDIA Nemotron Nano/Super and Nemotron 3 Ultra on Nebius Token Factory.
"""

import sys
import os
import time
from pathlib import Path
from typing import List, Dict, Any

# Add backend directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.services.model_router import model_router


BENCHMARK_PROMPTS = [
    # --- Category A: Everyday Tasks & Low-Latency Queries (Expected: FAST) ---
    {
        "id": "FAST-01",
        "prompt": "Hello! How can RecallOS help me manage my day?",
        "expected_route": "fast",
        "category": "Greeting",
    },
    {
        "id": "FAST-02",
        "prompt": "What is the capital of Japan?",
        "expected_route": "fast",
        "category": "Fact Retrieval",
    },
    {
        "id": "FAST-03",
        "prompt": "Summarize this in one sentence: Machine learning algorithms build a model based on sample data.",
        "expected_route": "fast",
        "category": "Quick Summarization",
    },
    {
        "id": "FAST-04",
        "prompt": "Remind me to review the team pull request at 4 PM.",
        "expected_route": "fast",
        "category": "Task Capture",
    },
    {
        "id": "FAST-05",
        "prompt": "Translate 'Privacy is our top priority' into Spanish.",
        "expected_route": "fast",
        "category": "Translation",
    },
    {
        "id": "FAST-06",
        "prompt": "Define the term 'deterministic tokenization'.",
        "expected_route": "fast",
        "category": "Definition",
    },
    {
        "id": "FAST-07",
        "prompt": "List the top 3 principles of local-first software.",
        "expected_route": "fast",
        "category": "Simple List",
    },
    {
        "id": "FAST-08",
        "prompt": "What was the date of our last project sync?",
        "expected_route": "fast",
        "category": "Memory Query",
    },
    {
        "id": "FAST-09",
        "prompt": "Spell check and polish: 'We has completed the database migrashun.'",
        "expected_route": "fast",
        "category": "Proofreading",
    },
    {
        "id": "FAST-10",
        "prompt": "Thank you for the quick assistance!",
        "expected_route": "fast",
        "category": "Conversational",
    },
    # --- Category B: Multi-Step Reasoning, Architecture & Code (Expected: COMPLEX) ---
    {
        "id": "COMPLEX-01",
        "prompt": "Compare SQLite, ChromaDB, and PostgreSQL. Analyze the concurrency models, trade-offs, and recommend an execution strategy for RecallOS.",
        "expected_route": "complex",
        "category": "Architectural Synthesis",
    },
    {
        "id": "COMPLEX-02",
        "prompt": "Debug this concurrency race condition in our FastAPI background worker: ```python def worker(): lock.acquire() ``` and identify the root cause.",
        "expected_route": "complex",
        "category": "Code Debugging",
    },
    {
        "id": "COMPLEX-03",
        "prompt": "Break down our 6-month product roadmap into multi-step milestones, identify all inter-team dependencies, and formulate a risk mitigation plan.",
        "expected_route": "complex",
        "category": "Multi-Step Planning",
    },
    {
        "id": "COMPLEX-04",
        "prompt": "Synthesize these three project plans, evaluate why the database migration stalled, and outline a step-by-step refactoring architecture.",
        "expected_route": "complex",
        "category": "Decomposition & Synthesis",
    },
    {
        "id": "COMPLEX-05",
        "prompt": "Analyze the formal security guarantees of client-side PII scrubbing versus zero-knowledge homomorphic encryption in personal AI agents.",
        "expected_route": "complex",
        "category": "Security Analysis",
    },
    {
        "id": "COMPLEX-06",
        "prompt": "Optimize this nested SQL query with recursive CTEs for memory graphs, explaining Big-O complexity improvements step-by-step.",
        "expected_route": "complex",
        "category": "Algorithm Optimization",
    },
    {
        "id": "COMPLEX-07",
        "prompt": "Construct a distributed consensus roadmap comparing Raft vs Paxos for our multi-node agent state replication.",
        "expected_route": "complex",
        "category": "Distributed Systems",
    },
    {
        "id": "COMPLEX-08",
        "prompt": "Evaluate the trade-offs of embedding dimensionality in vector retrieval, balancing quantization loss against search recall rates.",
        "expected_route": "complex",
        "category": "Deep ML Evaluation",
    },
    {
        "id": "COMPLEX-09",
        "prompt": "Design an automated failover strategy across two Nebius regions with zero downtime and state synchronization.",
        "expected_route": "complex",
        "category": "Infrastructure Architecture",
    },
    {
        "id": "COMPLEX-10",
        "prompt": "Perform a root cause analysis on this stack trace involving deadlock between database connection pools and async threads.",
        "expected_route": "complex",
        "category": "Root Cause Analysis",
    },
]


def run_benchmark():
    print("=" * 80)
    print("  RECALLOS MODEL ROUTER BENCHMARK SUITE")
    print("  Nebius Token Factory / NVIDIA Nemotron Dual-Model Infrastructure")
    print("=" * 80)
    print(f"Fast Model Target    : {settings.MODEL_FAST}")
    print(f"Complex Model Target : {settings.MODEL_COMPLEX}")
    print(f"Routing Threshold    : {settings.ROUTER_COMPLEXITY_THRESHOLD}")
    print(
        f"Mode                 : {'LIVE (Nebius Token Factory)' if settings.is_key_valid else 'HIGH-FIDELITY SIMULATION'}"
    )
    print("-" * 80)

    results = []
    correct_routes = 0

    for item in BENCHMARK_PROMPTS:
        messages = [{"role": "user", "content": item["prompt"]}]
        gen_result = model_router.route_and_generate(messages=messages)
        meta = gen_result["routing_metadata"]

        is_correct = meta["route"] == item["expected_route"]
        if is_correct:
            correct_routes += 1

        record = {
            "id": item["id"],
            "prompt": item["prompt"],
            "category": item["category"],
            "expected_route": item["expected_route"],
            "actual_route": meta["route"],
            "model_selected": meta["model_selected"],
            "score": meta["complexity_score"],
            "latency_ms": meta["latency_ms"],
            "is_correct": is_correct,
            "tokens": meta.get("token_usage", {}).get("total_tokens", 0),
        }
        results.append(record)

        status_sym = "[PASS]" if is_correct else "[FAIL]"
        print(
            f"{status_sym} {item['id']:<10} | Exp: {item['expected_route']:<7} | Act: {meta['route']:<7} | "
            f"Latency: {meta['latency_ms']:>6.1f}ms | Score: {meta['complexity_score']:>4.2f} | {item['category']}"
        )

    total_tests = len(results)
    accuracy = (correct_routes / total_tests) * 100

    fast_latencies = [r["latency_ms"] for r in results if r["actual_route"] == "fast"]
    complex_latencies = [
        r["latency_ms"] for r in results if r["actual_route"] == "complex"
    ]

    avg_fast = (
        sum(fast_latencies) / len(fast_latencies) if fast_latencies else 0.0
    )
    avg_complex = (
        sum(complex_latencies) / len(complex_latencies)
        if complex_latencies
        else 0.0
    )
    speedup = (avg_complex / avg_fast) if avg_fast > 0 else 1.0

    print("=" * 80)
    print("  BENCHMARK SUMMARY & PERFORMANCE METRICS")
    print("=" * 80)
    print(f"Total Test Prompts       : {total_tests}")
    print(f"Routing Accuracy         : {accuracy:.1f}% ({correct_routes}/{total_tests})")
    print(
        f"Avg Fast Route Latency   : {avg_fast:.2f} ms ({settings.MODEL_FAST})"
    )
    print(
        f"Avg Complex Route Latency: {avg_complex:.2f} ms ({settings.MODEL_COMPLEX})"
    )
    print(
        f"Dynamic Speedup Ratio    : {speedup:.2f}x faster execution for everyday queries"
    )
    print("=" * 80)

    save_markdown_report(
        results, accuracy, avg_fast, avg_complex, speedup, total_tests
    )
    return results


def save_markdown_report(
    results, accuracy, avg_fast, avg_complex, speedup, total_tests
):
    docs_dir = root_dir / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    report_path = docs_dir / "MODEL_ROUTER_BENCHMARKS.md"

    table_rows = []
    for r in results:
        status_badge = "✅ Pass" if r["is_correct"] else "❌ Fail"
        table_rows.append(
            f"| `{r['id']}` | {r['category']} | `{r['expected_route']}` | `{r['actual_route']}` | {r['score']} | **{r['latency_ms']:.1f} ms** | {r['tokens']} | {status_badge} |"
        )
    table_str = "\n".join(table_rows)

    content = f"""# 📊 RecallOS Model Routing & Latency Benchmark Report

> **Nebius × NVIDIA Hackathon 2026 — Member 1 Deliverable**  
> **Infrastructure**: Nebius Token Factory & NVIDIA Nemotron Models  
> **Generated on**: {time.strftime('%Y-%m-%d %H:%M:%S')}

---

## 🚀 Executive Summary

RecallOS employs a **Smart Model Router** to optimize inference cost, latency, and reasoning depth. Rather than dispatching every query to a monolithic LLM, requests are dynamically categorized into:
1. **Low-Latency Everyday Execution**: Routed to **`{settings.MODEL_FAST}`** for near-instant responses.
2. **Deep Multi-Step Reasoning**: Escalated to **`{settings.MODEL_COMPLEX}`** for architecture, planning, and debugging.

### Key Performance Indicators (KPIs)
* **Routing Intent Accuracy**: **{accuracy:.1f}%** ({sum(1 for r in results if r['is_correct'])} / {total_tests} test cases)
* **Average Fast Route Latency**: **{avg_fast:.2f} ms**
* **Average Complex Route Latency**: **{avg_complex:.2f} ms**
* **Inference Speedup Factor**: **{speedup:.2f}x** reduction in latency for everyday tasks
* **Zero PII Exposure**: Sanitized upstream by RecallOS Privacy Engine prior to cloud dispatch

---

## 📈 Latency Comparison

```plaintext
Fast Route (Nemotron Nano/Super)   : ████░░░░░░░░░░░░░░░░░░░░  {avg_fast:.1f} ms
Complex Route (Nemotron 3 Ultra)   : ████████████████████████  {avg_complex:.1f} ms
```

---

## 🧪 Comprehensive Evaluation Dataset

| ID | Category | Expected Route | Selected Route | Complexity Score | Latency | Tokens | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
{table_str}

---

## ⚙️ Routing Logic & Methodology

The router uses a composite scoring function:
`Score = min(1.0, W_keywords + W_length + W_syntax - W_simple)`

* **Reasoning Keywords**: Words like *compare*, *architect*, *trade-offs*, *dependencies* (+0.35 each).
* **Code Signals**: *debug*, *memory leak*, *race condition*, code blocks (+0.25 to +0.30).
* **Length Weight**: Scaled proportionally to prompt length beyond 50 words.
* **Escalation Threshold**: Prompts with score >= {settings.ROUTER_COMPLEXITY_THRESHOLD} route to Nemotron 3 Ultra; otherwise Nemotron Nano.

---
*Report automatically generated by `evaluation/benchmark_router.py`.*
"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\n[REPORT SAVED] Markdown benchmark report written to: {report_path}")


if __name__ == "__main__":
    run_benchmark()

