# ⚡ RecallOS Smart Model Router Specification

> **Nebius × NVIDIA Hackathon 2026**  
> **Author**: Member 1 (AI & Model Lead — Cloud & Inference)  
> **Target Models**: NVIDIA Nemotron Nano/Super & NVIDIA Nemotron 3 Ultra  
> **Infrastructure**: Nebius Token Factory & Nebius AI Cloud

---

## 1. System Overview

The **Smart Model Router** is the dynamic inference gateway for RecallOS. It inspects all egress prompts—after PII scrubbing by the Member 3 Privacy Shield—and determines the optimal NVIDIA Nemotron model based on semantic depth, computational complexity, and latency requirements.

```
                  ┌──────────────────────────────────────────────┐
                  │ Scrubbed User Prompt (Zero PII Egress)       │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │          Smart Model Router Engine           │
                  │   • Lexical Reasoning Triggers               │
                  │   • Code & Debugging Syntax Analysis         │
                  │   • Length & Structural Complexity Scoring   │
                  └──────────────┬───────────────────────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 │ Score < 0.40                  │ Score >= 0.40
                 ▼                               ▼
  ┌─────────────────────────────┐ ┌─────────────────────────────┐
  │  NVIDIA Nemotron Nano/Super │ │   NVIDIA Nemotron 3 Ultra   │
  │     (Fast Route ~220ms)     │ │   (Deep Reasoning ~650ms)   │
  │   • Summaries, Quick Facts  │ │   • Multi-Step Planning     │
  │   • Greetings, Reminders    │ │   • Architecture & Code     │
  └──────────────┬──────────────┘ └──────────────┬──────────────┘
                 │                               │
                 └───────────────┬───────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────────────────────┐
                  │  Execution Observability Payload             │
                  │  • Answer Text                               │
                  │  • Model Selected                            │
                  │  • Round-Trip Latency (ms)                   │
                  │  • Complexity Score                          │
                  └──────────────────────────────────────────────┘
```

---

## 2. API Contract for Teammates

### A. Member 2 (Agent & Tools Loop)
Member 2 can invoke the model router without needing database session management:

* **Endpoint**: `POST /api/router/generate`
* **Request Payload**:
```json
{
  "prompt": "Compare three vector databases and recommend an architecture.",
  "context": "User prefers SQLite and ChromaDB on local machine.",
  "system_prompt": "You are RecallOS, a privacy-first assistant.",
  "max_tokens": 512,
  "temperature": 0.7
}
```

* **Response Payload**:
```json
{
  "content": "Analysis of vector databases...",
  "routing_metadata": {
    "model_selected": "nvidia/Nemotron-3-Ultra-550b-a55b",
    "route": "complex",
    "category": "DEEP_ANALYTICAL_INQUIRY",
    "complexity_score": 0.85,
    "signals": ["Reasoning: compare", "Reasoning: architecture"],
    "latency_ms": 650.4,
    "token_usage": {
      "prompt_tokens": 24,
      "completion_tokens": 112,
      "total_tokens": 136
    },
    "is_mock": false
  }
}
```

### B. Member 4 (Frontend UI & Privacy Audit Drawer)
Member 4 can query the classifier for live UI badges before or during streaming:

* **Endpoint**: `POST /api/router/classify`
* **Request Payload**:
```json
{
  "prompt": "Summarize this email in 2 lines."
}
```
* **Response Payload**:
```json
{
  "prompt": "Summarize this email in 2 lines.",
  "route": "fast",
  "target_model": "nvidia/llama-3.1-nemotron-70b-instruct",
  "complexity_score": 0.0,
  "category": "EVERYDAY_FACT_OR_TASK",
  "signals": ["Standard Low-Latency Query"],
  "word_count": 6
}
```

---

## 3. Configuration Parameters (`.env`)

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `NEBIUS_API_KEY` | *(Secret)* | Nebius Token Factory authorization key |
| `NEBIUS_BASE_URL` | `https://api.tokenfactory.nebius.com/v1/` | Base URL for OpenAI-compatible completions |
| `MODEL_FAST` | `nvidia/llama-3.1-nemotron-70b-instruct` | Fast route model (low latency) |
| `MODEL_COMPLEX` | `nvidia/Nemotron-3-Ultra-550b-a55b` | Complex route model (deep reasoning) |
| `ROUTER_COMPLEXITY_THRESHOLD` | `0.40` | Threshold above which queries escalate to Ultra |
| `ENABLE_MOCK_FALLBACK` | `true` | Allows local development without valid key |

