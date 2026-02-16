#!/usr/bin/env python3
"""
Render a JSON file as a standalone HTML page using the JSON viewer.
Usage:
  python -m app.tools.render_json <input.json> [output.html]
  python -m app.tools.render_json transcripts/example/example-domains.json
  python -m app.tools.render_json data.json out.html
"""

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render a JSON file as HTML using the JSON viewer with data pre-loaded."
    )
    parser.add_argument(
        "json_path",
        type=Path,
        help="Path to the JSON file to display",
    )
    parser.add_argument(
        "output_path",
        type=Path,
        nargs="?",
        default=None,
        help="Path for the output HTML file (default: same as input with .html extension)",
    )
    args = parser.parse_args()

    json_path = args.json_path.resolve()
    if not json_path.exists():
        print(f"Error: file not found: {json_path}", file=sys.stderr)
        sys.exit(1)

    if args.output_path is not None:
        output_path = args.output_path.resolve()
    else:
        output_path = json_path.with_suffix(".html")

    viewer_path = Path(__file__).parent / "json_viewer.html"
    if not viewer_path.exists():
        print(f"Error: viewer not found: {viewer_path}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(json_path, encoding="utf-8") as f:
            json_text = f.read()
        # Validate and normalize
        data = json.loads(json_text)
        json_text = json.dumps(data, indent=2)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in {json_path}: {e}", file=sys.stderr)
        sys.exit(1)

    with open(viewer_path, encoding="utf-8") as f:
        viewer_html = f.read()

    # Embed INITIAL_JSON so the viewer auto-loads it (script runs before body content)
    init_script = f'  <script>var INITIAL_JSON = {json.dumps(json_text)};</script>\n'
    if "<body>" in viewer_html:
        viewer_html = viewer_html.replace("<body>", "<body>\n" + init_script, 1)
    else:
        viewer_html = viewer_html.replace("<body ", init_script + "  <body ", 1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(viewer_html)

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
