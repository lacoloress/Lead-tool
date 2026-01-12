"""Main entry point for Lead Tool."""

import subprocess
import sys


def main() -> None:
    """Run the Lead Tool Streamlit application."""
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", "lead_tool/ui/app.py"],
        check=True,
    )


if __name__ == "__main__":
    main()
