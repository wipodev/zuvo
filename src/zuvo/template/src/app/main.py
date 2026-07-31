"""
Main entrypoint for the CLI application.

---
ZUVO ENTRYPOINT OVERVIEW:
This file serves as the minimal executable launcher for your CLI app.
Zuvo automatically handles argument parsing, command discovery, i18n, 
and execution dispatching inside `run_app()`.

Custom initialization logic (e.g., loading environment variables, 
global error hooks, or logging setup) should be placed inside `main()`
before calling `run_app()`.
"""

from zuvo.core.runner import run_app


def main() -> None:
    """Bootstraps the application via Zuvo engine."""
    # Place optional pre-run setup here (e.g., custom logging or env initialization)
    run_app()


if __name__ == "__main__":
    main()