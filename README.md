![GitHub tag (with filter)](https://img.shields.io/github/v/tag/ImperialCollegeLondon/FINESSE)
[![GitHub](https://img.shields.io/github/license/ImperialCollegeLondon/FINESSE)](https://raw.githubusercontent.com/ImperialCollegeLondon/FINESSE/main/LICENCE.txt)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/ImperialCollegeLondon/FINESSE/main.svg)](https://results.pre-commit.ci/latest/github/ImperialCollegeLondon/FINESSE/main)
[![Test and build](https://github.com/ImperialCollegeLondon/FINESSE/actions/workflows/ci.yml/badge.svg)](https://github.com/ImperialCollegeLondon/FINESSE/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/ImperialCollegeLondon/FINESSE/graph/badge.svg?token=4UILYHPMJT)](https://codecov.io/gh/ImperialCollegeLondon/FINESSE)

# FINESSE

FINESSE is open-source graphical software to control a spectrometer system developed at
Imperial College London's [Space and Atmospheric Physics group].

Emissivity of the Earth's different surface types helps determine the efficiency with
which the planet radiatively cools to space and is a critical variable in climate
models. However, to date, most measurements of surface emissivity have been made in the
mid-infrared. The FINESSE project is novel in employing a ground-based system capable of
extending these datasets into the far-infrared. The system is tuned in particular for

targeting ice and snow, as the response of the climate to global warming is observed to
be most rapid in Arctic regions. Far-infrared emissivity data provided by FINESSE will
inform climate modelling studies seeking to better understand this rapid change. They
will also help to validate emissivity retrievals from upcoming satellite instruments
focusing on the far-infrared which will be deployed by ESA ([FORUM]) and NASA
([PREFIRE]).

The software was developed by Imperial's [RSE team]. It is written in Python and uses
the [PySide6 Qt bindings] for the GUI components. It provides a convenient interface for
controlling the various hardware components and viewing data produced, including a
[Bruker EM27 spectrometer], a stepper motor for controlling the mirror, two temperature
controllers and a separate temperature monitoring array.

This software is currently being adapted as part of a second project to deploy a
modified version of the equipment on the UK’s [Facility for Airborne Atmospheric
Measurements] aircraft.

[Space and Atmospheric Physics group]: https://www.imperial.ac.uk/physics/research/communities/space-plasma-climate/
[FORUM]: https://www.esa.int/Applications/Observing_the_Earth/FutureEO/FORUM
[PREFIRE]: https://science.nasa.gov/mission/prefire/
[RSE team]: https://www.imperial.ac.uk/admin-services/ict/self-service/research-support/rcs/service-offering/research-software-engineering/
[PySide6 Qt bindings]: https://pypi.org/project/PySide6/
[Bruker EM27 spectrometer]: https://www.bruker.com/en/products-and-solutions/infrared-and-raman/remote-sensing/em27-open-path-spectrometer.html
[Facility for Airborne Atmospheric Measurements]: https://www.faam.ac.uk/

## For developers

Technical documentation is available on [FINESSE's GitHub Pages site](https://imperialcollegelondon.github.io/FINESSE/).

This is a Python application that uses [poetry](https://python-poetry.org) for packaging
and dependency management. It also provides [pre-commit](https://pre-commit.com/) hooks
for various linters and formatters and automated tests using
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
