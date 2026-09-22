"""Runtime configuration, read from environment variables (optionally via a .env file).

Nothing institution-specific lives in code: the API key, and therefore the account,
its ranges and its data, all come from the environment.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_API_URL = "https://api.horizon.delta90.com"

# HORIZON sits behind Cloudflare WAF, which rejects the default User-Agent of most
# HTTP libraries (error 1010, HTML 403). This browser-like UA is verified to pass.
# A descriptive UA such as "horizon-mcp/0.1 (+https://github.com/mesalles/horizon-mcp)"
# has NOT been verified yet; override with HORIZON_USER_AGENT once it is.
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"
)


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True, slots=True)
class Settings:
    api_key: str
    api_url: str = DEFAULT_API_URL
    user_agent: str = DEFAULT_USER_AGENT
    timeout_seconds: float = 60.0
    # Minimum spacing between two requests to HORIZON (polite rate limiting).
    min_request_interval: float = 0.5
    # Default cap on rows returned to the model by list tools.
    default_max_rows: int = 200
    # Hard cap a caller can request.
    hard_max_rows: int = 1000
    # Smallest IPv4 prefix length accepted as a target (a /16 is the usual institution range).
    min_prefix_len: int = 16


def load_settings(env_file: Path | None = None) -> Settings:
    """Load settings from the environment.

    A ``.env`` file is loaded first if present: the explicit *env_file*, else the
    project root (two levels above this package), else the current directory.
    Real environment variables always win over the file.
    """
    candidates = [env_file] if env_file else [
        Path(__file__).resolve().parents[2] / ".env",
        Path.cwd() / ".env",
    ]
    for candidate in candidates:
        if candidate and candidate.is_file():
            load_dotenv(candidate, override=False)
            break

    api_key = os.getenv("HORIZON_API_KEY", "").strip()
    if not api_key:
        raise ConfigError(
            "HORIZON_API_KEY is not set. Put it in the environment or in a .env file "
            "(see .env.example). The key is shown in the HORIZON web UI under "
            "user menu > Mi perfil > Información."
        )

    def _float(name: str, default: float) -> float:
        raw = os.getenv(name)
        try:
            return float(raw) if raw else default
        except ValueError as exc:
            raise ConfigError(f"{name} must be a number, got {raw!r}") from exc

    def _int(name: str, default: int) -> int:
        raw = os.getenv(name)
        try:
            return int(raw) if raw else default
        except ValueError as exc:
            raise ConfigError(f"{name} must be an integer, got {raw!r}") from exc

    return Settings(
        api_key=api_key,
        api_url=os.getenv("HORIZON_API_URL", DEFAULT_API_URL).rstrip("/"),
        user_agent=os.getenv("HORIZON_USER_AGENT", DEFAULT_USER_AGENT),
        timeout_seconds=_float("HORIZON_TIMEOUT", 60.0),
        min_request_interval=_float("HORIZON_MIN_INTERVAL", 0.5),
        default_max_rows=_int("HORIZON_MAX_ROWS", 200),
    )
