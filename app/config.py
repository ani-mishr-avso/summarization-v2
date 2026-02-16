"""
Load runtime configuration from config.yaml.
Config path: project root config.yaml, or APP_CONFIG env var for override.
"""

import os
from pathlib import Path

import yaml

_CONFIG = None


def _config_path() -> Path:
    if os.getenv("APP_CONFIG"):
        return Path(os.environ["APP_CONFIG"])
    return Path(__file__).resolve().parent.parent / "config.yaml"


def get_config() -> dict:
    """Load and cache config from config.yaml."""
    global _CONFIG
    if _CONFIG is None:
        path = _config_path()
        with open(path) as f:
            _CONFIG = yaml.safe_load(f)
    return _CONFIG


def get_routing_config() -> dict:
    """Routing section (confidence_threshold, min_word_count, call_type_to_path)."""
    return get_config()["routing"]


def get_csm_config() -> dict:
    """CSM section (qbr_duration_minutes, qbr_template, general_template)."""
    return get_config()["csm"]


def get_fallback_config() -> dict:
    """Fallback section (prompt_category, prompt_name, expert_type_label)."""
    return get_config()["fallback"]


def get_meddpicc_config() -> dict:
    """MEDDPICC section (health_signal, status_map, stage_weights, default_weights)."""
    return get_config()["meddpicc"]


def get_methodology_config() -> dict:
    """Methodology section (default_sales_methodology, etc.)."""
    return get_config()["methodology"]


def get_llm():
    """Build ChatGroq from config and GROQ_API_KEY env."""
    from dotenv import load_dotenv
    from langchain_groq import ChatGroq

    load_dotenv()
    cfg = get_config()["llm"]
    api_key = os.getenv("GROQ_API_KEY")
    return ChatGroq(
        model_name=cfg["model_name"],
        temperature=cfg["temperature"],
        api_key=api_key,
        reasoning_effort=cfg["reasoning_effort"],
        service_tier=cfg["service_tier"],
    )
