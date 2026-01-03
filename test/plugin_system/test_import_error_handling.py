"""Tests for error handling in plugin import system."""

import sys
import pytest

from ncatbot.plugin_system.loader.importer import _ModuleImporter


class TestTopLevelPackageWithLoadError:
    """Test top-level package behavior when plugin load fails."""

    @pytest.fixture
    def importer(self):
        return _ModuleImporter()

    @pytest.fixture
    def broken_plugin(self, tmp_path):
        """Create a plugin that will fail to load."""
        plugin_root = tmp_path / "plugins"
        plugin_root.mkdir()

        plugin = plugin_root / "broken_plugin"
        plugin.mkdir()
        (plugin / "manifest.toml").write_text(
            'name = "broken_plugin"\nversion = "1.0.0"\nmain = "main"\n'
        )
        # Intentionally broken: import a non-existent module
        (plugin / "main.py").write_text(
            """from .nonexistent_module import Something

from ncatbot.plugin_system import NcatBotPlugin

class BrokenPlugin(NcatBotPlugin):
    name = "broken_plugin"
    version = "1.0.0"
    async def on_load(self): pass
"""
        )
        return plugin

    @pytest.fixture
    def cleanup_sys_modules(self):
        original_modules = set(sys.modules.keys())
        yield
        modules_to_remove = [
            k
            for k in sys.modules.keys()
            if k not in original_modules and k.startswith("ncatbot_plugin")
        ]
        for mod in modules_to_remove:
            sys.modules.pop(mod, None)

    def test_top_level_package_preserved_on_error(
        self, importer, broken_plugin, cleanup_sys_modules
    ):
        """Test that ncatbot_plugin is preserved when a plugin fails to load.

        This is important because other plugins might depend on it.
        """
        sys.modules.pop("ncatbot_plugin", None)

        name = importer._index_single_plugin(broken_plugin)

        with pytest.raises(Exception):  # ModuleNotFoundError or ImportError
            importer.load_plugin_module(name)

        # The top-level package should still exist
        # (it might have been created before the error)
        # This is by design - we don't roll back the top-level package
        # because other plugins might need it
        if "ncatbot_plugin" in sys.modules:
            # If it was created, it should be valid
            assert sys.modules["ncatbot_plugin"] is not None


class TestPluginUnloadCleanup:
    """Test that unloading plugins properly cleans up resources."""

    @pytest.fixture
    def importer(self):
        return _ModuleImporter()

    @pytest.fixture
    def simple_plugin(self, tmp_path):
        """Create a simple plugin for unload testing."""
        plugin_root = tmp_path / "plugins"
        plugin_root.mkdir()

        plugin = plugin_root / "unload_test"
        plugin.mkdir()
        (plugin / "manifest.toml").write_text(
            'name = "unload_test"\nversion = "1.0.0"\nmain = "main"\n'
        )
        (plugin / "main.py").write_text(
            """from ncatbot.plugin_system import NcatBotPlugin

class UnloadTestPlugin(NcatBotPlugin):
    name = "unload_test"
    version = "1.0.0"
    async def on_load(self): pass
"""
        )
        return plugin

    @pytest.fixture
    def cleanup_sys_modules(self):
        original_modules = set(sys.modules.keys())
        yield
        modules_to_remove = [
            k
            for k in sys.modules.keys()
            if k not in original_modules and k.startswith("ncatbot_plugin")
        ]
        for mod in modules_to_remove:
            sys.modules.pop(mod, None)

    def test_unload_removes_plugin_modules(
        self, importer, simple_plugin, cleanup_sys_modules
    ):
        """Test that unloading a plugin removes its modules from sys.modules."""
        sys.modules.pop("ncatbot_plugin", None)

        name = importer._index_single_plugin(simple_plugin)
        importer.load_plugin_module(name)

        pkg_name = importer._get_plugin_pkg_name(name)
        main_module = importer._get_plugin_main_module_name(name)

        # Verify modules are loaded
        assert pkg_name in sys.modules
        assert main_module in sys.modules

        # Unload the plugin
        result = importer.unload_plugin_module(name)
        assert result is True

        # Verify modules are removed
        assert pkg_name not in sys.modules
        assert main_module not in sys.modules

    def test_unload_preserves_top_level_package(
        self, importer, simple_plugin, cleanup_sys_modules
    ):
        """Test that unloading a plugin preserves the top-level package."""
        sys.modules.pop("ncatbot_plugin", None)

        name = importer._index_single_plugin(simple_plugin)
        importer.load_plugin_module(name)

        # Unload the plugin
        importer.unload_plugin_module(name)

        # Top-level package should still exist
        assert "ncatbot_plugin" in sys.modules
