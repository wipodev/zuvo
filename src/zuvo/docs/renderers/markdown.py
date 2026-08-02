"""
Markdown format renderer implementation for 'zuvo docs'.
"""

from zuvo.core.inspector import AppDoc
from zuvo.docs.renderers.base import BaseRenderer
from zuvo.i18n import t


class MarkdownRenderer(BaseRenderer):
    """
    Renders structured AppDoc models into Markdown format.
    """

    def render(self, apps_docs: list[AppDoc]) -> str:
        """
        Generates a Markdown document string from application docs metadata.

        Args:
            apps_docs (list[AppDoc]): List of inspected application documentation models.

        Returns:
            str: Formatted Markdown string.
        """
        # Retrieve main title and header translations
        title = t("docs_md_main_title")
        banner = t("docs_md_auto_generated")

        lines: list[str] = [f"# {title}\n"]
        lines.append(f"> {banner}\n")

        # Retrieve structural labels
        app_label = t("docs_md_label_application")
        file_label = t("docs_md_label_file")
        flags_label = t("docs_md_label_flags")

        # Retrieve table column header translations
        col_flag = t("docs_md_col_flag")
        col_desc = t("docs_md_col_desc")
        col_default = t("docs_md_col_default")
        col_choices = t("docs_md_col_choices")
        col_required = t("docs_md_col_required")

        # Retrieve boolean string representations
        val_yes = t("docs_md_val_yes")
        val_no = t("docs_md_val_no")

        for app in apps_docs:
            lines.append("---")
            lines.append(f"## {app_label}: `{app.app_name}`\n")

            for cmd in app.commands:
                lines.append(f"### `{cmd.name}`")
                lines.append(f"> {cmd.description}\n")

                if cmd.file_path:
                    lines.append(f"**{file_label}:** `{cmd.file_path}`\n")

                if cmd.arguments:
                    lines.append(f"**{flags_label}:**\n")
                    lines.append(
                        f"| {col_flag} | {col_desc} | {col_default} | {col_choices} | {col_required} |"
                    )
                    lines.append("| :--- | :--- | :---: | :---: | :---: |")

                    for arg in cmd.arguments:
                        flags_str = ", ".join(f"`{f}`" for f in arg.flags)
                        desc_str = arg.description or "-"
                        default_str = (
                            f"`{arg.default}`" if arg.default is not None else "-"
                        )
                        choices_str = (
                            ", ".join(f"`{c}`" for c in arg.choices)
                            if arg.choices
                            else "-"
                        )
                        req_str = val_yes if arg.required else val_no

                        lines.append(
                            f"| {flags_str} | {desc_str} | {default_str} | {choices_str} | {req_str} |"
                        )
                    lines.append("")

        return "\n".join(lines)