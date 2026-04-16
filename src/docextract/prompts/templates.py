"""Jinja2 prompt templates for document extraction."""

from jinja2 import Template


def render_prompt(template_str: str, **context) -> str:
    """Render a Jinja2 template string with the given context.

    Args:
        template_str: Jinja2 template string.
        **context: Variables to inject into the template.

    Returns:
        Rendered prompt string.
    """
    template = Template(template_str)
    return template.render(**context)
