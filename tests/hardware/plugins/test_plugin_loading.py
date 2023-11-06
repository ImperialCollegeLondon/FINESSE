"""Tests for the plugin loading code."""
import sys
from unittest.mock import MagicMock, Mock, call, patch

from finesse.hardware.plugins import _import_recursively, load_all_plugins


@patch("finesse.hardware.plugins.import_module")
@patch("finesse.hardware.plugins.iter_modules")
def test_import_recursively(iter_modules_mock: Mock, import_mock: Mock) -> None:
    """Test the _import_recursively() function."""
    root_module = MagicMock()
    root_module.__path__ = "some/path/root"
    root_module.__name__ = "root"

    modinfos = []
    for i in range(2):
        modinfo_mock = MagicMock()
        modinfo_mock.name = f"mod{i}"
        modinfos.append(modinfo_mock)

    # Instead of returning actual modules, return a series of ints
    import_mock.side_effect = range(len(modinfos))

    iter_modules_mock.return_value = modinfos
    with patch(
        "finesse.hardware.plugins._import_recursively"
    ) as import_recursively_mock:
        expected = [f"root.{info.name}" for info in modinfos]
        import_recursively_mock.return_value = []
        assert list(_import_recursively(root_module)) == expected

        # Check that all submodules were imported
        import_mock.assert_has_calls([call(f"root.{info.name}") for info in modinfos])

        # Check that _import_recursively itself was invoked for each of the submodules
        import_recursively_mock.assert_has_calls(list(map(call, range(len(modinfos)))))


@patch("finesse.hardware.plugins._import_recursively")
def test_load_all_plugins(import_mock: Mock) -> None:
    """Test the load_all_plugins() function."""
    ret = load_all_plugins()

    # No plugins will be found because we're mocking _import_recursively
    assert len(ret) == 0

    import_mock.assert_called_once_with(sys.modules["finesse.hardware.plugins"])
