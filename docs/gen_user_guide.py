"""Generate the User Guide."""
import subprocess
from pathlib import Path
docs_dir = Path(__file__).parent
subprocess.run(
    [
        "pandoc",
        "-f",
        "markdown",
        "-t",
        "html5",
        "-o",
        f"{docs_dir}/user_guide.html",
        f"{docs_dir}/user_guide.md",
    ],
    check=True,
)
