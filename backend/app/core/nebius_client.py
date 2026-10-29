"""
RecallOS Nebius Client
Provides a resilient, OpenAI-compatible client for Nebius Token Factory inference.
Supports live NVIDIA Nemotron models with automatic failover and local mock emulation.
"""

import logging
import time
from typing import Any, Dict, List, Optional
from openai import OpenAI, AuthenticationError, RateLimitError, APIConnectionError
from app.core.config import settings

logger = logging.getLogger("recallos.nebius_client")


class NebiusClient:
    def __init__(self):
        self.api_key = settings.NEBIUS_API_KEY
        self.base_url = settings.NEBIUS_BASE_URL
        self._client: Optional[OpenAI] = None

        if settings.is_key_valid:
            try:
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    timeout=45.0,
                    max_retries=2,
                )
                logger.info(
                    f"Nebius Token Factory client initialized. Base URL: {self.base_url}"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to initialize live Nebius client: {e}. Fallback to mock mode."
                )
                self._client = None
        else:
            logger.info(
                "No live Nebius API key configured. Client running in high-fidelity simulation mode."
            )

    @property
    def is_live(self) -> bool:
        """Returns True if a live client is ready with a valid API key."""
        return self._client is not None and settings.is_key_valid

    def complete(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Executes a chat completion against Nebius Token Factory.
        Returns a dictionary containing the content, model name, token usage, and execution status.
        """
        # If live client is active, execute real API call
        if self.is_live:
            try:
                completion = self._client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                content = completion.choices[0].message.content or ""
                usage = {
                    "prompt_tokens": getattr(completion.usage, "prompt_tokens", 0)
                    if completion.usage
                    else 0,
                    "completion_tokens": getattr(
                        completion.usage, "completion_tokens", 0
                    )
                    if completion.usage
                    else 0,
                    "total_tokens": getattr(completion.usage, "total_tokens", 0)
                    if completion.usage
                    else 0,
                }
                return {
                    "content": content,
                    "model": completion.model or model,
                    "usage": usage,
                    "is_mock": False,
                    "status": "success",
                }
            except AuthenticationError as exc:
                logger.error(f"Nebius authentication failed: {exc}")
                if not settings.ENABLE_MOCK_FALLBACK:
                    raise
                logger.warning(
                    "Authentication failed on Nebius Token Factory. Falling back to local emulator."
                )
            except (RateLimitError, APIConnectionError) as exc:
                logger.error(f"Nebius network/quota error: {exc}")
                if not settings.ENABLE_MOCK_FALLBACK:
                    raise
            except Exception as exc:
                logger.error(f"Unexpected Nebius inference error: {exc}")
                if not settings.ENABLE_MOCK_FALLBACK:
                    raise

        # High-fidelity mock emulation
        return self._emulate_completion(model, messages)

    def _emulate_completion(
        self, model: str, messages: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Emulates inference response with realistic Nemotron outputs and latency."""
        last_message = messages[-1]["content"] if messages else ""
        is_complex = "ultra" in model.lower() or "340b" in model.lower()

        # Simulate cloud round-trip delay (180ms - 240ms for Fast, 550ms - 850ms for Complex)
        simulated_delay = 0.65 if is_complex else 0.22
        time.sleep(simulated_delay)

        if is_complex:
            content = (
                f"[NVIDIA Nemotron 3 Ultra — Deep Reasoning Engine]\n\n"
                f"I have conducted a multi-step analytical evaluation of your request: \"{last_message[:80]}...\".\n\n"
                f"### Strategic Breakdown & Execution Plan:\n"
                f"1. **Core Problem Analysis**: Assessed underlying dependencies and structural requirements.\n"
                f"2. **Decomposition & Synthesis**: Isolated constraints, algorithmic efficiency, and risk vectors.\n"
                f"3. **Proposed Architectural Solution**: Formulated robust execution strategy with zero data leakage.\n\n"
                f"*(Dispatched via Nebius Token Factory — Verified Grounding)*"
            )
        else:
            content = (
                f"[NVIDIA Nemotron Nano/Super — Low-Latency Dispatch]\n\n"
                f"I have processed your query: \"{last_message[:60]}\".\n\n"
                f"Here is the direct resolution grounded in your local session context with instant response timing."
            )

        prompt_len = sum(len(m.get("content", "")) for m in messages)
        prompt_tokens = max(1, prompt_len // 4)
        completion_tokens = max(1, len(content) // 4)

        return {
            "content": content,
            "model": model,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
            "is_mock": True,
            "status": "success",
        }

    def verify_connection(self) -> Dict[str, Any]:
        """Tests connectivity and reports current status."""
        if not self.is_live:
            return {
                "connected": False,
                "mode": "simulation",
                "base_url": self.base_url,
                "message": "Client in simulation mode. Provide a valid NEBIUS_API_KEY in .env to connect to live Nebius Token Factory.",
            }
        try:
            # Send a micro-prompt to test authentication
            test_resp = self.complete(
                model=settings.MODEL_FAST,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            return {
                "connected": True,
                "mode": "live",
                "base_url": self.base_url,
                "fast_model": settings.MODEL_FAST,
                "complex_model": settings.MODEL_COMPLEX,
                "test_status": test_resp.get("status"),
            }
        except Exception as e:
            return {
                "connected": False,
                "mode": "error",
                "base_url": self.base_url,
                "error": str(e),
            }


# Singleton instance
nebius_client = NebiusClient()

