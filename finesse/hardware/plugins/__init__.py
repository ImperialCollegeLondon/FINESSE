"""Plugins for the hardware module."""
import sys
from importlib import import_module
from pkgutil import iter_modules
from types import ModuleType


def _import_recursively(module: ModuleType) -> None:
    """Recursively import module's submodules."""
    if hasattr(module, "__path__"):
        for modinfo in iter_modules(module.__path__):
            _import_recursively(import_module(f"{module.__name__}.{modinfo.name}"))


def load_all_plugins() -> None:
    """Load all the device types from this module and its submodules."""
    _import_recursively(sys.modules[__name__])
