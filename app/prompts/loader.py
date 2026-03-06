import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape

from app.utils.logger import get_logger

logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(handler)


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
    logger.info("Loading prompt: %s/%s", category, filename)
    if not filename.endswith(".md"):
        filename = f"{filename}.md"
    relative_path = f"{category}/{filename}"

    try:
        logger.info("Rendering template: %s", relative_path)
        template = jinja_env.get_template(relative_path)
        return template.render(**kwargs)

    except TemplateNotFound:
        logger.error("Template not found: %s", relative_path)
        raise FileNotFoundError(f"Prompt template not found at: {relative_path}")
    except Exception as e:
        logger.error("Error rendering template: %s", relative_path)
        raise RuntimeError(f"Error rendering template {relative_path}: {str(e)}")
