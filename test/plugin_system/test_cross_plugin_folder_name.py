"""Tests for cross-plugin import by folder name.

This module tests that plugins can import from other plugins using
the folder name (which may differ from the plugin name).
For example: `from ..acm.plugin import xxx` when the plugin name is "ACM"
but the folder is named "acm".
"""

import sys
import pytest

from ncatbot.plugin_system.loader.importer import _ModuleImporter
from ncatbot.plugin_system.loader.finder import get_plugin_finder


class TestCrossPluginImportByFolderName:
    """Test cross-plugin import using folder name instead of plugin name."""

    @pytest.fixture
    def importer(self):
        return _ModuleImporter()

    @pytest.fixture
    def plugins_with_different_names(self, tmp_path):
        """Create plugins where folder name differs from plugin name."""
        plugin_root = tmp_path / "plugins"
        plugin_root.mkdir()

        # Base plugin: folder name is "acm" but plugin name is "ACM"
        base_folder = plugin_root / "acm"
        base_folder.mkdir()
        (base_folder / "manifest.toml").write_text(
            'name = "ACM"\nversion = "1.0.0"\nmain = "plugin"\n'
        )
        (base_folder / "__init__.py").write_text("")
        (base_folder / "plugin.py").write_text(
            """from ncatbot.plugin_system import NcatBotPlugin

SHARED_VALUE = "value_from_acm"

class ACMPlugin(NcatBotPlugin):
    name = "ACM"
    version = "1.0.0"
    shared = SHARED_VALUE
    async def on_load(self): pass
"""
        )

        # Consumer plugin: uses folder name "acm" to import
        consumer_folder = plugin_root / "consumer"
        consumer_folder.mkdir()
        (consumer_folder / "manifest.toml").write_text(
            'name = "Consumer"\nversion = "1.0.0"\nmain = "main"\n'
        )
        (consumer_folder / "main.py").write_text(
            """from ncatbot.plugin_system import NcatBotPlugin
# Import using folder name "acm" instead of plugin name "ACM"
from ..acm.plugin import SHARED_VALUE, ACMPlugin

class ConsumerPlugin(NcatBotPlugin):
    name = "Consumer"
    version = "1.0.0"
    imported_value = SHARED_VALUE
    imported_class = ACMPlugin
    async def on_load(self): pass
"""
        )

        return base_folder, consumer_folder

    @pytest.fixture
    def cleanup_sys_modules(self):
        original_modules = set(sys.modules.keys())
        _finder = get_plugin_finder()
        original_paths = dict(_finder._plugin_paths)
        original_folder_map = dict(_finder._folder_to_sanitized)
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
        _finder._folder_to_sanitized.clear()
        _finder._folder_to_sanitized.update(original_folder_map)

    def test_import_by_folder_name(
        self, importer, plugins_with_different_names, cleanup_sys_modules
    ):
        """Test that import using folder name works when it differs from plugin name."""
        sys.modules.pop("ncatbot_plugin", None)

        base_folder, consumer_folder = plugins_with_different_names

        # Index and load base plugin first
        base_name = importer._index_single_plugin(base_folder)
        assert base_name == "ACM"
        importer.load_plugin_module(base_name)

        # Now index and load consumer plugin
        consumer_name = importer._index_single_plugin(consumer_folder)
        consumer_module = importer.load_plugin_module(consumer_name)

        # Find the consumer plugin class
        plugin_class = None
        for attr_name in dir(consumer_module):
            attr = getattr(consumer_module, attr_name)
            if isinstance(attr, type) and getattr(attr, "name", None) == "Consumer":
                plugin_class = attr
                break

        assert plugin_class is not None, "Consumer plugin class not found"

        # Verify the import using folder name worked
        assert plugin_class.imported_value == "value_from_acm"
        assert plugin_class.imported_class.name == "ACM"

    def test_folder_name_registered_on_index(
        self, importer, plugins_with_different_names, cleanup_sys_modules
    ):
        """Test that folder name is registered in finder during indexing."""
        sys.modules.pop("ncatbot_plugin", None)

        base_folder, _ = plugins_with_different_names

        # Index the base plugin
        importer._index_single_plugin(base_folder)

        # Check that both the sanitized name and folder name are registered
        _finder = get_plugin_finder()
        registered = _finder.get_registered_plugins()

        # Both "ACM" (sanitized) and "acm" (folder) should be registered
        assert "ACM" in registered
        assert "acm" in registered

    def test_import_by_plugin_name_also_works(
        self, importer, plugins_with_different_names, cleanup_sys_modules
    ):
        """Test that import using plugin name (sanitized) also works."""
        sys.modules.pop("ncatbot_plugin", None)

        base_folder, consumer_folder = plugins_with_different_names

        # Index and load base plugin
        base_name = importer._index_single_plugin(base_folder)
        importer.load_plugin_module(base_name)

        # Modify consumer to use plugin name instead of folder name
        (consumer_folder / "main.py").write_text(
            """from ncatbot.plugin_system import NcatBotPlugin
# Import using plugin name "ACM" instead of folder name "acm"
from ..ACM.plugin import SHARED_VALUE

class ConsumerPlugin(NcatBotPlugin):
    name = "Consumer"
    version = "1.0.0"
    imported_value = SHARED_VALUE
    async def on_load(self): pass
"""
        )

        # Index and load consumer
        consumer_name = importer._index_single_plugin(consumer_folder)
        consumer_module = importer.load_plugin_module(consumer_name)

        # Find the consumer plugin class
        plugin_class = None
        for attr_name in dir(consumer_module):
            attr = getattr(consumer_module, attr_name)
            if isinstance(attr, type) and getattr(attr, "name", None) == "Consumer":
                plugin_class = attr
                break

        assert plugin_class is not None
        assert plugin_class.imported_value == "value_from_acm"
