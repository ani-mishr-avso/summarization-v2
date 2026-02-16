from typing import Any

from app.config import get_meddpicc_config
from app.utils.stage import normalize_ae_stage


def _dimensions_to_dict(dimensions: Any) -> dict[str, dict[str, Any]]:
    """
    Normalize dimensions to a dict keyed by dimension name.
    Accepts: list of {dimension, score, ...} or dict keyed by dimension name.
    """
    raw = dimensions if dimensions is not None else {}
    if isinstance(raw, list):
        return {
            item["dimension"]: item
            for item in raw
            if isinstance(item, dict) and item.get("dimension") is not None
        }
    if isinstance(raw, dict):
        return raw
    return {}


def calculate_meddpicc_score(methodology_json: dict[str, Any], stage: str) -> dict[str, Any]:
    """
    Calculates weighted deal health using separate score fields per dimension.
    Weights and health thresholds are read from config.yaml (meddpicc section).
    methodology_json["dimensions"] may be a list of {dimension, score, ...} or a dict keyed by dimension.
    """
    cfg = get_meddpicc_config()
    status_map = cfg["status_map"]
    stage_weights = cfg["stage_weights"]
    default_weights = cfg["default_weights"]
    green_above = cfg["health_signal"]["green_above"]
    yellow_above = cfg["health_signal"]["yellow_above"]

    clean_stage = normalize_ae_stage(stage)
    weights = stage_weights.get(clean_stage, default_weights)
    dimensions = _dimensions_to_dict(methodology_json.get("dimensions"))

    weighted_total = 0.0
    breakdown = {}

    for dim, weight in weights.items():
        dim_data = dimensions.get(dim, {})

        maturity = dim_data.get("score", 0)
        dimension_score = weight * (maturity / 5.0)
        weighted_total += dimension_score

        breakdown[dim] = {
            "maturity": maturity,
            "status": status_map.get(maturity, "missing"),
            "contribution": round(dimension_score * 100, 2)
        }

    if weighted_total > green_above:
        health_signal = "green"
    elif weighted_total > yellow_above:
        health_signal = "yellow"
    else:
        health_signal = "red"

    return {
        "overall_score": round(weighted_total * 100, 2),
        "health_signal": health_signal,
        "breakdown": breakdown
    }