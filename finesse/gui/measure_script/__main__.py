"""Some test code allowing users to run measure scripts standalone."""
import sys
from pathlib import Path

from .parse import Script, parse_script

if __name__ == "__main__":
    path = Path(sys.argv[1])

    with open(path, "r") as f:
        script = Script(path, **parse_script(f))

    script.run()
