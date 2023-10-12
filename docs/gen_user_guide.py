"""Generate the User Guide."""
import os

os.system(
    r"""pandoc -f markdown -t html5 -o user_guide.html docs\user_guide.md -c style
    .css"""
)
