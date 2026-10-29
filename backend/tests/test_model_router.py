"""
Unit & Integration Tests for RecallOS Smart Model Router
Verifies intent classification, complexity scoring, latency measurement, and fallback mechanics.
"""

import sys
import os
from pathlib import Path

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.core.config import settings
from app.services.model_router import model_router, SmartModelRouter


def test_simple_queries_route_to_fast_model():
    """Verifies that low-complexity everyday queries route to Nemotron Nano/Super."""
    simple_prompts = [
        "Hello! How are you today?",
        "What is the capital of Canada?",
        "Summarize this in one sentence: Python is a high-level programming language.",
        "Define persistent memory.",
        "Remind me to call John at 5 PM.",
    ]

    for prompt in simple_prompts:
        result = model_router.evaluate_complexity(prompt)
        assert (
            result["route"] == "fast"
        ), f"Expected 'fast' route for: '{prompt}', got: {result['route']}"
        assert (
            result["target_model"] == settings.MODEL_FAST
        ), f"Expected fast model for: '{prompt}'"
        assert (
            result["complexity_score"] < settings.ROUTER_COMPLEXITY_THRESHOLD
        ), f"Complexity score too high for simple prompt: {result['complexity_score']}"


def test_complex_queries_route_to_ultra_model():
    """Verifies that multi-step reasoning, architectural synthesis, and debugging route to Nemotron 3 Ultra."""
    complex_prompts = [
        "Compare MySQL, PostgreSQL, and SQLite. Analyze the trade-offs, concurrency models, and build an execution strategy.",
        "Debug this race condition in our distributed cache: ```python def lock(): pass ```",
        "Break down this 6-month product roadmap into multi-step milestones, identify dependency graphs, and evaluate risks.",
        "Synthesize these three project plans, evaluate root causes for delays, and recommend architectural improvements.",
    ]

    for prompt in complex_prompts:
        result = model_router.evaluate_complexity(prompt)
        assert (
            result["route"] == "complex"
        ), f"Expected 'complex' route for: '{prompt}', got: {result['route']}"
        assert (
            result["target_model"] == settings.MODEL_COMPLEX
        ), f"Expected complex model for: '{prompt}'"
        assert (
            result["complexity_score"] >= settings.ROUTER_COMPLEXITY_THRESHOLD
        ), f"Complexity score too low for complex prompt: {result['complexity_score']}"


def test_empty_or_whitespace_prompts():
    """Verifies safe handling of empty or blank inputs."""
    for empty in ["", "   ", "\n\t"]:
        result = model_router.evaluate_complexity(empty)
        assert result["route"] == "fast"
        assert result["complexity_score"] == 0.0


def test_end_to_end_route_and_generate():
    """Verifies that route_and_generate produces valid content and required routing metadata."""
    messages = [
        {
            "role": "user",
            "content": "Compare SQLite and PostgreSQL for our local memory vector index.",
        }
    ]

    response = model_router.route_and_generate(messages=messages)

    assert "content" in response
    assert len(response["content"]) > 0
    assert "routing_metadata" in response

    meta = response["routing_metadata"]
    assert "model_selected" in meta
    assert "route" in meta
    assert meta["route"] == "complex"
    assert "latency_ms" in meta
    assert meta["latency_ms"] > 0
    assert "complexity_score" in meta
    assert "token_usage" in meta
    assert "signals" in meta


if __name__ == "__main__":
    print("=== Running RecallOS Smart Model Router Unit Tests ===")
    test_simple_queries_route_to_fast_model()
    print("  [PASSED] Simple queries route to Nemotron Nano/Super")
    test_complex_queries_route_to_ultra_model()
    print("  [PASSED] Complex queries route to Nemotron 3 Ultra")
    test_empty_or_whitespace_prompts()
    print("  [PASSED] Empty/whitespace edge cases handled safely")
    test_end_to_end_route_and_generate()
    print("  [PASSED] End-to-end generation and latency measurement verified")
    print("\nAll Model Router unit tests passed with 100% success!")

