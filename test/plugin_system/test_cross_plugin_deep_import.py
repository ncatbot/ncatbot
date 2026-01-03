"""Tests for deep nested cross-plugin imports.

This module tests that plugins can import deeply nested modules
from other plugins using relative imports.
"""

import sys
import pytest

from ncatbot.plugin_system.loader.importer import _ModuleImporter
from ncatbot.plugin_system.loader.finder import get_plugin_finder


class TestCrossPluginDeepImport:
    """Test cross-plugin imports with nested module structures."""

    @pytest.fixture
    def importer(self):
        return _ModuleImporter()

    @pytest.fixture
    def deep_cross_import_plugins(self, tmp_path):
        """Create plugins with deep nested cross imports."""
        plugin_root = tmp_path / "plugins"
        plugin_root.mkdir()

        # Library plugin with nested structure
        lib_plugin = plugin_root / "lib_plugin"
        lib_plugin.mkdir()
        (lib_plugin / "manifest.toml").write_text(
            'name = "lib_plugin"\nversion = "1.0.0"\nmain = "main"\n'
        )
        (lib_plugin / "__init__.py").write_text("")

        # Create nested structure: utils/helpers/common.py
        utils = lib_plugin / "utils"
        utils.mkdir()
        (utils / "__init__.py").write_text("")

        helpers = utils / "helpers"
        helpers.mkdir()
        (helpers / "__init__.py").write_text("")

        (helpers / "common.py").write_text(
            """DEEP_VALUE = "deep_nested_cross_import"

class DeepSharedClass:
    value = DEEP_VALUE
"""
        )

        (lib_plugin / "main.py").write_text(
            """from ncatbot.plugin_system import NcatBotPlugin

class LibPlugin(NcatBotPlugin):
    name = "lib_plugin"
    version = "1.0.0"
    async def on_load(self): pass
"""
        )

        # Consumer plugin with deep cross import
        consumer = plugin_root / "deep_consumer"
        consumer.mkdir()
        (consumer / "manifest.toml").write_text(
            'name = "deep_consumer"\nversion = "1.0.0"\nmain = "main"\n'
        )
        (consumer / "main.py").write_text(
            """from ncatbot.plugin_system import NcatBotPlugin
from ..lib_plugin.utils.helpers.common import DEEP_VALUE, DeepSharedClass

class DeepConsumerPlugin(NcatBotPlugin):
    name = "deep_consumer"
    version = "1.0.0"

    deep_value = DEEP_VALUE
    deep_class = DeepSharedClass

    async def on_load(self): pass
"""
        )

        return lib_plugin, consumer

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
        _finder._plugin_paths.clear()
        _finder._plugin_paths.update(original_paths)

    def test_deep_cross_plugin_import(
        self, importer, deep_cross_import_plugins, cleanup_sys_modules
    ):
        """Test cross-plugin import with deeply nested modules."""
        sys.modules.pop("ncatbot_plugin", None)

        lib_plugin, consumer = deep_cross_import_plugins

        # Load library plugin first
        lib_name = importer._index_single_plugin(lib_plugin)
        importer.load_plugin_module(lib_name)

        # Load consumer plugin
        consumer_name = importer._index_single_plugin(consumer)
        consumer_module = importer.load_plugin_module(consumer_name)

        # Find plugin class
        plugin_class = None
        for attr_name in dir(consumer_module):
            attr = getattr(consumer_module, attr_name)
            if (
                isinstance(attr, type)
                and getattr(attr, "name", None) == "deep_consumer"
            ):
                plugin_class = attr
                break

        assert plugin_class is not None
        assert plugin_class.deep_value == "deep_nested_cross_import"
        assert plugin_class.deep_class.value == "deep_nested_cross_import"
