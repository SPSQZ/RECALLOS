"""
RecallOS Core Configuration
Manages Nebius Token Factory settings, NVIDIA model routes, and router thresholds.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Ensure .env is loaded from backend directory or project root
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent.parent
env_path = backend_dir / ".env"

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()


class Settings:
    # Nebius Token Factory Credentials & Endpoints
    NEBIUS_API_KEY: str = os.getenv("NEBIUS_API_KEY", "").strip()
    NEBIUS_BASE_URL: str = os.getenv(
        "NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1/"
    ).strip()

    # NVIDIA Model Stack Routes
    # Fast Route: NVIDIA Nemotron Nano / Super (Low latency everyday tasks)
    MODEL_FAST: str = os.getenv(
        "MODEL_FAST", "nvidia/llama-3.1-nemotron-70b-instruct"
    ).strip()

    # Complex Route: NVIDIA Nemotron 3 Ultra (Deep multi-step reasoning & planning)
    MODEL_COMPLEX: str = os.getenv(
        "MODEL_COMPLEX", "nvidia/Nemotron-3-Ultra-550b-a55b"
    ).strip()

    # Smart Router Complexity Threshold (0.0 to 1.0)
    # Queries scoring above this threshold escalate to the Complex Model
    ROUTER_COMPLEXITY_THRESHOLD: float = float(
        os.getenv("ROUTER_COMPLEXITY_THRESHOLD", "0.40")
    )

    # Fallback to simulated high-fidelity mock if no valid key is present
    ENABLE_MOCK_FALLBACK: bool = os.getenv(
        "ENABLE_MOCK_FALLBACK", "true"
    ).lower() in ("1", "true", "yes")

    @property
    def is_key_valid(self) -> bool:
        """Checks if the configured API key is a non-placeholder key."""
        if not self.NEBIUS_API_KEY:
            return False
        placeholder_indicators = [
            "your_actual",
            "your_key",
            "replace_me",
            "sk-placeholder",
        ]
        return not any(
            ph in self.NEBIUS_API_KEY.lower() for ph in placeholder_indicators
        )


settings = Settings()

