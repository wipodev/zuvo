from pathlib import Path
from zuvo.core.runner import run_app


def main() -> None:
    """Entry point for the Zuvo CLI itself."""
    zuvo_root = Path(__file__).resolve().parent.parent.parent
    run_app(project_root=zuvo_root)


if __name__ == "__main__":
    main()