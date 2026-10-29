"""
RecallOS Smart Model Router
Dynamic intent & complexity classification engine for NVIDIA Nemotron models on Nebius Token Factory.

Routes:
  - Simple / Everyday Tasks -> NVIDIA Nemotron Nano/Super (Low latency, high throughput)
  - Deep Reasoning / Planning -> NVIDIA Nemotron 3 Ultra (Multi-step reasoning, architectural synthesis)
"""

import time
import re
from typing import Any, Dict, List, Tuple
from app.core.config import settings
from app.core.nebius_client import nebius_client, NebiusClient


# Lexical and Semantic Indicators for Deep Reasoning
COMPLEX_REASONING_SIGNALS = [
    "architect",
    "architecture",
    "system design",
    "compare",
    "contrast",
    "versus",
    "vs",
    "analyze",
    "analysis",
    "trade-off",
    "tradeoffs",
    "trade-offs",
    "pros and cons",
    "dependencies",
    "dependency graph",
    "synthesize",
    "synthesis",
    "multi-step",
    "step-by-step",
    "execution strategy",
    "strategy",
    "roadmap",
    "milestones",
    "root cause",
    "decomposition",
    "evaluate",
    "evaluation",
    "benchmarking",
    "formal verification",
    "failover",
    "consensus",
]

CODE_AND_ANALYSIS_SIGNALS = [
    "debug",
    "refactor",
    "memory leak",
    "concurrency",
    "race condition",
    "deadlock",
    "optimize",
    "optimization",
    "big o",
    "distributed systems",
    "distributed",
    "regex",
    "sql query",
    "cte",
    "recursive",
    "stack trace",
    "segmentation fault",
    "encryption",
    "homomorphic",
    "security guarantees",
]

SIMPLE_EVERYDAY_SIGNALS = [
    "hello",
    "hi",
    "hey",
    "who is",
    "what is",
    "define",
    "summarize this in",
    "quick reminder",
    "remind me",
    "translate",
    "spell check",
    "list the",
    "thanks",
    "thank you",
]


def match_signals(signals_list: List[str], text: str) -> List[str]:
    """Matches signals using word boundaries so short tokens like 'hi' don't match inside 'this' or 'homomorphic'."""
    matched = []
    for sig in signals_list:
        pattern = r"\b" + re.escape(sig) + r"\b"
        if re.search(pattern, text, re.IGNORECASE):
            matched.append(sig)
    return matched


class SmartModelRouter:
    def __init__(self, client: NebiusClient = nebius_client):
        self.client = client
        self.threshold = settings.ROUTER_COMPLEXITY_THRESHOLD
        self.fast_model = settings.MODEL_FAST
        self.complex_model = settings.MODEL_COMPLEX

    def evaluate_complexity(self, prompt: str) -> Dict[str, Any]:
        """
        Analyzes prompt semantics, structure, and intent to compute a complexity score (0.0 to 1.0).
        Returns intent category, complexity score, signals detected, and target route.
        """
        if not prompt or not prompt.strip():
            return {
                "complexity_score": 0.0,
                "route": "fast",
                "target_model": self.fast_model,
                "category": "EMPTY_OR_TRIVIAL",
                "signals": [],
                "word_count": 0,
            }

        text = prompt.lower()
        words = re.findall(r"\b\w+\b", text)
        word_count = len(words)

        matched_reasoning = match_signals(COMPLEX_REASONING_SIGNALS, text)
        matched_code = match_signals(CODE_AND_ANALYSIS_SIGNALS, text)
        matched_simple = match_signals(SIMPLE_EVERYDAY_SIGNALS, text)

        # Check structural markers
        has_code_block = "```" in prompt or "def " in prompt or "class " in prompt
        has_numbered_list = bool(
            re.search(r"(\b1\..+?\b2\..+)", prompt, re.DOTALL)
        )
        has_multiple_questions = prompt.count("?") >= 2

        # Base scoring calculation
        keyword_score = (len(matched_reasoning) * 0.35) + (
            len(matched_code) * 0.30
        )

        length_score = min(0.35, word_count / 100.0)
        structure_score = 0.0
        if has_code_block:
            structure_score += 0.25
        if has_numbered_list:
            structure_score += 0.20
        if has_multiple_questions:
            structure_score += 0.15

        simple_discount = 0.0
        if not matched_reasoning and not matched_code:
            simple_discount = len(matched_simple) * 0.25

        raw_score = (
            keyword_score + length_score + structure_score - simple_discount
        )
        complexity_score = max(0.0, min(1.0, round(raw_score, 2)))

        signals = []
        if matched_reasoning:
            signals.extend(
                [f"Reasoning: {k}" for k in matched_reasoning[:3]]
            )
        if matched_code:
            signals.extend([f"Code: {k}" for k in matched_code[:3]])
        if has_code_block:
            signals.append("Code Block Detected")
        if word_count > 60:
            signals.append(f"Extended Length ({word_count} words)")

        if has_code_block or matched_code:
            category = "CODE_ANALYSIS_AND_DEBUGGING"
        elif matched_reasoning or has_numbered_list:
            category = "MULTI_STEP_REASONING_AND_PLANNING"
        elif complexity_score >= self.threshold:
            category = "DEEP_ANALYTICAL_INQUIRY"
        elif matched_simple:
            category = "CASUAL_OR_GREETING"
        else:
            category = "EVERYDAY_FACT_OR_TASK"

        is_complex = (
            complexity_score >= self.threshold
            or (len(matched_reasoning) >= 1 and word_count >= 15)
            or (len(matched_code) >= 1 and word_count >= 15)
        )

        target_model = self.complex_model if is_complex else self.fast_model
        route = "complex" if is_complex else "fast"

        return {
            "complexity_score": complexity_score,
            "route": route,
            "target_model": target_model,
            "category": category,
            "signals": signals if signals else ["Standard Low-Latency Query"],
            "word_count": word_count,
        }

    def route_and_generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 512,
        temperature: float = 0.7,
        system_prompt: str = "You are RecallOS, a privacy-first personal AI with persistent memory. Ground all answers accurately.",
    ) -> Dict[str, Any]:
        """
        Main pipeline: Evaluates prompt, selects optimal Nemotron model, executes call,
        measures precise latency, and returns full observability metadata.
        """
        user_prompt = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_prompt = m.get("content", "")
                break

        eval_result = self.evaluate_complexity(user_prompt)
        selected_model = eval_result["target_model"]
        route = eval_result["route"]

        prepared_messages = [
            {"role": "system", "content": system_prompt},
            *messages,
        ]

        start_time = time.perf_counter()
        completion_result = self.client.complete(
            model=selected_model,
            messages=prepared_messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        end_time = time.perf_counter()

        latency_ms = round((end_time - start_time) * 1000, 2)

        return {
            "content": completion_result.get("content", ""),
            "routing_metadata": {
                "model_selected": selected_model,
                "route": route,
                "category": eval_result["category"],
                "complexity_score": eval_result["complexity_score"],
                "signals": eval_result["signals"],
                "latency_ms": latency_ms,
                "token_usage": completion_result.get("usage", {}),
                "is_mock": completion_result.get("is_mock", False),
            },
        }


# Singleton instance
model_router = SmartModelRouter()

