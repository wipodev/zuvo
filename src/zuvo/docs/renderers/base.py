"""
Abstract Base Class for documentation renderers.
"""

from abc import ABC, abstractmethod
from zuvo.core.inspector import AppDoc


class BaseRenderer(ABC):
    """
    Base contract for documentation renderers.
    """

    @abstractmethod
    def render(self, apps_docs: list[AppDoc]) -> str:
        """
        Renders structured AppDoc models into output string format.
        """
        pass