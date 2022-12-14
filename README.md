# FINESSE

A graphical user interface for controlling and monitoring an interferometer device.

## For developers

Technical documentation is available on [FINESSE's GitHub Pages site](https://imperialcollegelondon.github.io/FINESSE/).

This is a Python 3.9 application that uses [poetry](https://python-poetry.org) for
packaging and dependency management. It also provides
[pre-commit](https://pre-commit.com/) hooks (for
[Black](https://black.readthedocs.io/en/stable/) and
[Flake8](https://flake8.pycqa.org/en/latest/)) and automated tests using
[pytest](https://pytest.org/) and [GitHub Actions](https://github.com/features/actions).
Pre-commit hooks are automatically kept updated with a dedicated GitHub Action.

To get started:

1. [Download and install Poetry](https://python-poetry.org/docs/#installation) following the instructions for your OS.
1. Clone this repository and make it your working directory
1. Set up the virtual environment:

   ```bash
   poetry install
   ```

1. Activate the virtual environment (alternatively, ensure any python-related command is preceded by `poetry run`):

   ```bash
   poetry shell
   ```

1. Install the git hooks:

   ```bash
   pre-commit install
   ```

1. Run the main app:

   ```bash
   python -m finesse
   ```

1. Run the tests:

   ```bash
   pytest
   ```
