from typing import Any, Dict

from app.config import get_config


def calculate_meddpicc_score(methodology_json: Dict[str, Any], stage: str) -> Dict[str, Any]:
    """
    Calculates weighted deal health using separate score fields per dimension.
    Weights and health thresholds are read from config.yaml (meddpicc section).
    """
    cfg = get_config()["meddpicc"]
    status_map = cfg["status_map"]
    stage_weights = cfg["stage_weights"]
    default_weights = cfg["default_weights"]
    green_above = cfg["health_signal"]["green_above"]
    yellow_above = cfg["health_signal"]["yellow_above"]

    clean_stage = stage.split('/')[0].lower()
    weights = stage_weights.get(clean_stage, default_weights)
    dimensions = methodology_json.get("dimensions", {})

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