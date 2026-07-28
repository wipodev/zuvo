import sys, importlib
from pathlib import Path
from typing import List, Tuple
from unittest.mock import patch
import pytest
from _pytest.capture import CaptureFixture

import zuvo.core.project
from zuvo.core.runner import run_app
from zuvo.i18n import i18n


@pytest.fixture
def cli_runner(capsys: CaptureFixture):
    """
    Fixture que simula ejecuciones CLI parcheando directamente 'project.py'
    y apuntando la carga de comandos al paquete del template.
    """
    def _run_cli(args: List[str], prog_name: str = "cli_template") -> Tuple[int, str, str]:
        old_argv = list(sys.argv)

        # 1. Configuración simulada de project.json
        mock_project_data = {
            "name": "my-zuvo-cli",
            "executable_name": "mycli",
            "title": "My Zuvo CLI Application",
            "version": "0.1.0",
            "description": "CLI Application built with Zuvo Framework",
            "author": "Developer Name",
            "copyright": "© 2026 All rights reserved.",
            "type": "standard",
            "commands": ["install", "create"],
            "files": []
        }

        # 2. Aplicamos los parches:
        # - read_json_safe para recargar project.py
        # - Apuntamos la carga de comandos a 'zuvo.template.src.app.commands'
        with patch("zuvo.core.project.read_json_safe", return_value=mock_project_data):
            importlib.reload(zuvo.core.project)
            
            # En la estructura real, los comandos del template están bajo el paquete importable:
            # zuvo.template.src.app.commands
            with patch("zuvo.core.runner.COMMANDS_CONFIG", ["install", "create"]):
                
                # Modificamos temporalmente sys.argv
                sys.argv = [prog_name] + args

                exit_code = 0
                try:
                    # Si package_path en runner.py es "src.app.commands", lo mapeamos al paquete real de zuvo
                    with patch("zuvo.core.runner.load_command_modules") as mock_load:
                        # Hacemos que cargue los módulos reales importándolos desde 'zuvo.template.src.app.commands'
                        def side_effect_load(cmd_list, pkg_path):
                            commands = {}
                            for cmd in cmd_list:
                                mod_path = f"zuvo.template.src.app.commands.{cmd}"
                                try:
                                    mod = importlib.import_module(mod_path)
                                    commands[cmd] = mod
                                except Exception as e:
                                    pass
                            return commands

                        mock_load.side_effect = side_effect_load

                        run_app()

                except SystemExit as e:
                    exit_code = e.code if isinstance(e.code, int) else 1
                finally:
                    sys.argv = old_argv

        captured = capsys.readouterr()
        return exit_code, captured.out, captured.err

    return _run_cli


@pytest.fixture
def set_language():
    """Fixture to dynamically change the language during tests using template locales."""
    original_lang = i18n.current_lang
    original_locales_dir = i18n.locales_dir

    # Apuntamos los locales a la carpeta real de traducciones del template
    template_locales = (Path(__file__).parent.parent / "src" / "zuvo" / "template" / "locales").resolve()
    i18n.locales_dir = template_locales

    def _change_lang(lang_code: str):
        i18n.current_lang = lang_code
        i18n.reload()

    yield _change_lang

    # Teardown: Restaurar idioma y directorio original
    i18n.current_lang = original_lang
    i18n.locales_dir = original_locales_dir
    i18n.reload()