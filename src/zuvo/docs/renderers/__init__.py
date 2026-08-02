"""
Docs renderers module registry and factory function.
"""

from zuvo.docs.renderers.base import BaseRenderer
from zuvo.docs.renderers.json_renderer import JSONRenderer
from zuvo.docs.renderers.markdown import MarkdownRenderer

RENDERERS: dict[str, type[BaseRenderer]] = {
    "markdown": MarkdownRenderer,
    "json": JSONRenderer,
}


def get_renderer(fmt: str) -> BaseRenderer:
    """
    Factory function to retrieve a renderer instance by format name.

    Args:
        fmt (str): Format key ('markdown', 'json').

    Returns:
        BaseRenderer: Concrete renderer instance.

    Raises:
        ValueError: If format is not supported.
    """
    renderer_cls = RENDERERS.get(fmt.lower())
    if not renderer_cls:
        raise ValueError(f"Unsupported documentation format: {fmt}")
    return renderer_cls()