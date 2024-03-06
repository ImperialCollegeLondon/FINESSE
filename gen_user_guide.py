"""Generate the User Guide."""
import subprocess
from pathlib import Path


def generate_html() -> None:
    """Converts user_guide.md to html format."""
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


if __name__ == "__main__":
    generate_html()
