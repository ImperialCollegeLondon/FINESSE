"""Generate the User Guide."""
import subprocess

subprocess.run(
    "pandoc -f markdown -t html5 -o user_guide.html docs/user_guide.md", check=True
)
