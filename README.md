# FINESSE

A graphical user interface for controlling and monitoring an interferometer device.

---

![GitHub tag (with filter)](https://img.shields.io/github/v/tag/ImperialCollegeLondon/FINESSE)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![GitHub](https://img.shields.io/github/license/ImperialCollegeLondon/FINESSE)](https://raw.githubusercontent.com/ImperialCollegeLondon/FINESSE/main/LICENCE.txt)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/e7f3a4626b724c1fad00d8b670647a10)](https://app.codacy.com/gh/ImperialCollegeLondon/FINESSE/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/ImperialCollegeLondon/FINESSE/main.svg)](https://results.pre-commit.ci/latest/github/ImperialCollegeLondon/FINESSE/main)
[![Test and build](https://github.com/ImperialCollegeLondon/FINESSE/actions/workflows/ci.yml/badge.svg)](https://github.com/ImperialCollegeLondon/FINESSE/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/ImperialCollegeLondon/FINESSE/graph/badge.svg?token=4UILYHPMJT)](https://codecov.io/gh/ImperialCollegeLondon/FINESSE)

## For developers

Technical documentation is available on [FINESSE's GitHub Pages site](https://imperialcollegelondon.github.io/FINESSE/).

This is a Python application that uses [poetry](https://python-poetry.org) for packaging
and dependency management. It also provides [pre-commit](https://pre-commit.com/) hooks
(for [Black](https://black.readthedocs.io/en/stable/) and
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

1. Build the user guide:

   1. Install [pandoc](https://pandoc.org/installing.html)

   1. ```bash
      python docs/gen_user_guide.py
      ```
