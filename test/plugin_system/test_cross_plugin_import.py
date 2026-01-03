"""Tests for cross-plugin import support in plugin system.

This module tests that plugins can import from other plugins using
relative imports like `from ..another_plugin import xxx`.
"""

import sys
import pytest

from ncatbot.plugin_system.loader.importer import _ModuleImporter
from ncatbot.plugin_system.loader.finder import get_plugin_finder


class TestMultiplePluginsSharedTopPackage:
    """Test that multiple plugins share the same top-level package."""

    @pytest.fixture
    def importer(self):
        return _ModuleImporter()

    @pytest.fixture
    def two_plugins(self, tmp_path):
        """Create two plugins to test shared namespace."""
        plugin_root = tmp_path / "plugins"
        plugin_root.mkdir()

        # Plugin 1
        plugin1 = plugin_root / "plugin_one"
        plugin1.mkdir()
        (plugin1 / "manifest.toml").write_text(
            'name = "plugin_one"\nversion = "1.0.0"\nmain = "main"\n'
        )
        (plugin1 / "main.py").write_text(
            """from ncatbot.plugin_system import NcatBotPlugin

class PluginOne(NcatBotPlugin):
    name = "plugin_one"
    version = "1.0.0"
    async def on_load(self): pass
"""
        )

        # Plugin 2
        plugin2 = plugin_root / "plugin_two"
        plugin2.mkdir()
        (plugin2 / "manifest.toml").write_text(
            'name = "plugin_two"\nversion = "1.0.0"\nmain = "main"\n'
        )
        (plugin2 / "main.py").write_text(
            """from ncatbot.plugin_system import NcatBotPlugin

class PluginTwo(NcatBotPlugin):
    name = "plugin_two"
    version = "1.0.0"
    async def on_load(self): pass
"""
        )

        return plugin1, plugin2

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

    def test_shared_top_level_package(self, importer, two_plugins, cleanup_sys_modules):
        """Test that both plugins use the same ncatbot_plugin namespace."""
        sys.modules.pop("ncatbot_plugin", None)

        plugin1, plugin2 = two_plugins

        # Load first plugin
        name1 = importer._index_single_plugin(plugin1)
        importer.load_plugin_module(name1)

        # Get reference to top-level package
        top_pkg_first = sys.modules.get("ncatbot_plugin")
        assert top_pkg_first is not None

        # Load second plugin
        name2 = importer._index_single_plugin(plugin2)
        importer.load_plugin_module(name2)

        # Top-level package should be the same object
        top_pkg_second = sys.modules.get("ncatbot_plugin")
        assert top_pkg_second is top_pkg_first


class TestCrossPluginImport:
    """Test that plugins can import from other plugins."""

    @pytest.fixture
    def importer(self):
        return _ModuleImporter()

    @pytest.fixture
    def cross_import_plugins(self, tmp_path):
        """Create plugins that import from each other."""
        plugin_root = tmp_path / "plugins"
        plugin_root.mkdir()

        # Base plugin (provides shared utilities)
        base_plugin = plugin_root / "base_utils"
        base_plugin.mkdir()
        (base_plugin / "manifest.toml").write_text(
            'name = "base_utils"\nversion = "1.0.0"\nmain = "main"\n'
        )
        (base_plugin / "__init__.py").write_text("")
        (base_plugin / "shared.py").write_text(
            """# Shared utilities for other plugins

SHARED_CONSTANT = "shared_value_from_base"

def shared_function():
    return "function_from_base"

class SharedClass:
    name = "SharedClassFromBase"
"""
        )
        (base_plugin / "main.py").write_text(
            """from ncatbot.plugin_system import NcatBotPlugin
from .shared import SHARED_CONSTANT, shared_function, SharedClass

class BaseUtilsPlugin(NcatBotPlugin):
    name = "base_utils"
    version = "1.0.0"

    constant = SHARED_CONSTANT
    func = shared_function
    cls = SharedClass

    async def on_load(self):
        pass
"""
        )

        # Consumer plugin (imports from base_utils)
        consumer_plugin = plugin_root / "consumer"
        consumer_plugin.mkdir()
        (consumer_plugin / "manifest.toml").write_text(
            'name = "consumer"\nversion = "1.0.0"\nmain = "main"\n'
        )
        (consumer_plugin / "main.py").write_text(
            """from ncatbot.plugin_system import NcatBotPlugin
# Cross-plugin import using relative import
from ..base_utils.shared import SHARED_CONSTANT, shared_function, SharedClass

class ConsumerPlugin(NcatBotPlugin):
    name = "consumer"
    version = "1.0.0"

    # Store imported values for testing
    imported_constant = SHARED_CONSTANT
    imported_function = shared_function
    imported_class = SharedClass

    async def on_load(self):
        pass
"""
        )

        return base_plugin, consumer_plugin

    @pytest.fixture
    def cleanup_sys_modules(self):
        original_modules = set(sys.modules.keys())
        _finder = get_plugin_finder()
        original_paths = dict(_finder._plugin_paths)
        yield
        modules_to_remove = [
            k
            for k in sys.modules.keys()
            if k not in original_modules and k.startswith("ncatbot_plugin")
        ]
        for mod in modules_to_remove:
            sys.modules.pop(mod, None)
        # Restore finder state
        _finder._plugin_paths.clear()
        _finder._plugin_paths.update(original_paths)

    def test_cross_plugin_import(
        self, importer, cross_import_plugins, cleanup_sys_modules
    ):
        """Test that consumer plugin can import from base_utils plugin."""
        sys.modules.pop("ncatbot_plugin", None)

        base_plugin, consumer_plugin = cross_import_plugins

        # Load base plugin first
        base_name = importer._index_single_plugin(base_plugin)
        importer.load_plugin_module(base_name)

        # Load consumer plugin that imports from base
        consumer_name = importer._index_single_plugin(consumer_plugin)
        consumer_module = importer.load_plugin_module(consumer_name)

        # Find the consumer plugin class
        plugin_class = None
        for attr_name in dir(consumer_module):
            attr = getattr(consumer_module, attr_name)
            if isinstance(attr, type) and getattr(attr, "name", None) == "consumer":
                plugin_class = attr
                break

        assert plugin_class is not None, "Consumer plugin class not found"

        # Verify cross-plugin import worked
        assert plugin_class.imported_constant == "shared_value_from_base"
        assert plugin_class.imported_function() == "function_from_base"
        assert plugin_class.imported_class.name == "SharedClassFromBase"

    def test_cross_plugin_import_order_matters(
        self, importer, cross_import_plugins, cleanup_sys_modules
    ):
        """Test that base plugin must be loaded before consumer."""
        sys.modules.pop("ncatbot_plugin", None)

        base_plugin, consumer_plugin = cross_import_plugins

        # Try to load consumer plugin without base plugin
        consumer_name = importer._index_single_plugin(consumer_plugin)

        # This should fail because base_utils is not loaded
        with pytest.raises(Exception):
            importer.load_plugin_module(consumer_name)
