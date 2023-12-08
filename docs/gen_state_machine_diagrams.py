"""Make diagrams for all state machine classes."""
import inspect
from collections.abc import Iterable
from importlib import import_module
from pathlib import Path
from pkgutil import iter_modules
from types import ModuleType

from statemachine import StateMachine
from statemachine.contrib.diagram import DotGraphMachine

import finesse

DIAGRAM_DIR = Path(__file__).parent


def get_all_modules(module: ModuleType) -> Iterable[ModuleType]:
    """Recursively import module's submodules."""
    if not hasattr(module, "__path__"):
        return

    for modinfo in iter_modules(module.__path__):
        package = import_module(f"{module.__name__}.{modinfo.name}")
        yield package
        yield from get_all_modules(package)


def write_diagram(sm: type[StateMachine]):
    """Write state machine diagram to disk."""
    graph = DotGraphMachine(sm)
    graph().write_png(str(DIAGRAM_DIR / f"{sm.__name__}.png"))


def get_all_state_machines() -> Iterable[type[StateMachine]]:
    """Get all the state machine classes in FINESSE."""
    for module in get_all_modules(finesse):
        for _, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and issubclass(obj, StateMachine)
                and obj is not StateMachine
            ):
                yield obj


def main():
    """Make diagrams for all state machine classes."""
    for sm in get_all_state_machines():
        write_diagram(sm)


main()
