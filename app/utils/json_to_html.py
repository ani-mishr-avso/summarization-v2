"""
Convert a nested dict (or list) to the same HTML structure as the JSON viewer.
Usage:
  from app.utils.json_to_html import json_to_html
  html = json_to_html({"a": 1, "b": {"c": [2, 3]}})
"""

import html as html_module
import re
from typing import Any

__all__ = ["json_to_html"]


def _type_of(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    raise TypeError(f"Unsupported type for JSON HTML: {type(value)}")


def _to_title_case(s: str) -> str:
    s = str(s)
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", s)
    s = re.sub(r"[_-]+", " ", s)
    return " ".join(word.capitalize() for word in s.split()).strip()


def _heading_tag(depth: int) -> str:
    return f"h{min(depth + 2, 6)}"


def _build_doc(data: Any, depth: int) -> str:
    t = _type_of(data)

    if t == "object":
        parts = []
        for k, v in data.items():
            key_str = str(k)
            child_type = _type_of(v)
            is_array_of_primitives = (
                child_type == "array"
                and all(
                    _type_of(x) not in ("object", "array") for x in v
                )
            )
            is_nested = child_type == "object" or (
                child_type == "array" and not is_array_of_primitives
            )
            tag = _heading_tag(depth)
            heading = f'<{tag} class="json-doc-heading">{html_module.escape(_to_title_case(key_str))}</{tag}>'
            if is_nested:
                body = _build_doc(v, depth + 1)
                parts.append(
                    f'<section class="json-doc-section">'
                    f'<details class="json-doc-details" open>'
                    f"<summary>{heading}</summary>"
                    f'<div class="json-doc-body">{body}</div>'
                    f"</details></section>"
                )
            else:
                body = _build_doc(v, depth + 1)
                parts.append(
                    f'<section class="json-doc-section">{heading}{body}</section>'
                )
        return "".join(parts)

    if t == "array":
        all_primitive = all(
            _type_of(x) not in ("object", "array") for x in data
        )
        if all_primitive:
            items = []
            for v in data:
                vt = _type_of(v)
                if vt == "string":
                    text = html_module.escape(str(v))
                elif vt == "null":
                    text = "null"
                else:
                    text = html_module.escape(str(v))
                items.append(
                    f'<li class="json-value value-{vt}">{text}</li>'
                )
            return f'<ul class="json-doc-list">{"".join(items)}</ul>'
        parts = []
        for i, item in enumerate(data):
            item_type = _type_of(item)
            is_nested = item_type in ("object", "array")
            tag = _heading_tag(depth)
            label = f"Item {i}"
            heading = f'<{tag} class="json-doc-heading">{html_module.escape(_to_title_case(label))}</{tag}>'
            if is_nested:
                body = _build_doc(item, depth + 1)
                parts.append(
                    f'<section class="json-doc-section">'
                    f'<details class="json-doc-details" open>'
                    f"<summary>{heading}</summary>"
                    f'<div class="json-doc-body">{body}</div>'
                    f"</details></section>"
                )
            else:
                body = _build_doc(item, depth + 1)
                parts.append(
                    f'<section class="json-doc-section">{heading}{body}</section>'
                )
        return "".join(parts)

    # primitive
    if t == "string":
        text = html_module.escape(str(data))
    elif t == "null":
        text = "null"
    else:
        text = html_module.escape(str(data))
    return f'<p class="json-value value-{t}">{text}</p>'


def json_to_html(data: Any) -> str:
    """
    Convert a nested dict, list, or primitive to the JSON viewer HTML structure.

    Args:
        data: A dict, list, or JSON-serializable primitive (str, int, float, bool, None).

    Returns:
        HTML string starting with <div class="json-doc">...</div>, matching
        the structure produced by the browser viewer (sections, title case,
        details, no quotes around strings). Use with the same CSS as the viewer.

    Raises:
        TypeError: If data contains an unsupported type (e.g. set, custom class).
    """
    inner = _build_doc(data, 0)
    return f'<div class="json-doc">{inner}</div>'
