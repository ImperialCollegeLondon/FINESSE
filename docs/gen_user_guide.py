"""Generate the User Guide."""
import subprocess
from pathlib import Path

subprocess.run(
    [
        "pandoc",
        "-f",
        "markdown",
        "-t",
        "html5",
        "-o",
        "user_guide.html",
        f"{Path(__file__).parent}/user_guide.md",
    ],
    check=True,
)
