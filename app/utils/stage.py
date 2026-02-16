"""AE stage normalization for prompt paths and config lookups."""


def normalize_ae_stage(stage: str) -> str:
    """
    Normalize an AE stage string to a config key (e.g. 'Discovery/Custom' -> 'discovery').
    """
    if not stage:
        return ""
    return stage.split("/")[0].strip().lower()
