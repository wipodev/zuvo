"""
JSON format renderer implementation for 'zuvo docs'.
"""

from dataclasses import asdict
import json

from zuvo.core.inspector import AppDoc
from zuvo.docs.renderers.base import BaseRenderer


class JSONRenderer(BaseRenderer):
    """
    Renders structured AppDoc models into JSON string format.
    """

    def render(self, apps_docs: list[AppDoc]) -> str:
        """
        Generates a formatted JSON string from application docs metadata.

        Args:
            apps_docs (list[AppDoc]): List of inspected application documentation models.

        Returns:
            str: Formatted JSON string.
        """
        payload = {
            "generator": "zuvo docs",
            "apps": {
                app.app_name: [
                    {
                        "name": cmd.name,
                        "description": cmd.description,
                        "file_path": cmd.file_path,
                        "arguments": [asdict(arg) for arg in cmd.arguments],
                    }
                    for cmd in app.commands
                ]
                for app in apps_docs
            },
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)