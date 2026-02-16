from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape

BASE_DIR = Path(__file__).resolve().parent
template_loader = FileSystemLoader(str(BASE_DIR))
jinja_env = Environment(
    loader=template_loader,
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


def load_prompt(category: str, filename: str, **kwargs) -> str:
    """
    Thread-safe prompt loader using Jinja2.
    Assembles prompt paths dynamically and injects variables.

    Args:
        category: The sub-folder (e.g., 'summarization/ae' or 'voss_framework')
        filename: The markdown file name (without .md extension)
        **kwargs: Variables to inject into the template (transcript, methodology_name, etc.)
    """
    if not filename.endswith(".md"):
        filename = f"{filename}.md"
    relative_path = f"{category}/{filename}"

    try:
        template = jinja_env.get_template(relative_path)
        return template.render(**kwargs)

    except TemplateNotFound:
        raise FileNotFoundError(f"Prompt template not found at: {relative_path}")
    except Exception as e:
        raise RuntimeError(f"Error rendering template {relative_path}: {str(e)}")
