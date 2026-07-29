"""
Main entrypoint for the CLI application.
Delegates execution lifecycle to the Zuvo core engine.
"""

from zuvo.core.runner import run_app


def main() -> None:
    """Bootstraps the application via Zuvo engine."""
    run_app()


if __name__ == "__main__":
    main()