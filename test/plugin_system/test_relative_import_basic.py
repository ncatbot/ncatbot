"""Tests for basic relative import support in plugin system.

This module tests that the plugin system correctly creates the virtual
top-level package 'ncatbot_plugin' to support relative imports within plugins.
"""

import sys
import pytest

from ncatbot.plugin_system.loader.importer import _ModuleImporter


class TestVirtualTopLevelPackage:
    """Tests for virtual top-level package creation (ncatbot_plugin)."""

    @pytest.fixture
    def importer(self):
        """Create a fresh ModuleImporter instance."""
        return _ModuleImporter()

    @pytest.fixture
    def plugin_dir(self, tmp_path):
        """Create a temporary plugin directory with relative import."""
        plugin_root = tmp_path / "plugins"
        plugin_root.mkdir()

        # Create plugin directory
        plugin_folder = plugin_root / "relative_import_test"
        plugin_folder.mkdir()

        # Create manifest.toml
        manifest = plugin_folder / "manifest.toml"
        manifest.write_text(
            """name = "relative_import_test"
version = "1.0.0"
main = "main"
description = "Test plugin for relative import"
"""
        )

        # Create submodule directory
        submodules = plugin_folder / "submodules"
        submodules.mkdir()

        # Create submodule __init__.py
        (submodules / "__init__.py").write_text('"""Submodules package."""\n')

        # Create helper.py in submodules
        (submodules / "helper.py").write_text(
            '''"""Helper module for testing relative imports."""

def get_helper_message():
    """Return a test message."""
    return "Helper module loaded successfully!"

class Helper:
    """Helper class for testing."""
    name = "TestHelper"
'''
        )

        # Create main.py with relative import
        (plugin_folder / "main.py").write_text(
            '''"""Test plugin with relative imports."""
from .submodules.helper import Helper, get_helper_message

from ncatbot.plugin_system import NcatBotPlugin


class RelativeImportTestPlugin(NcatBotPlugin):
    """Test plugin that uses relative imports."""

    name = "relative_import_test"
    version = "1.0.0"

    # Store imported values for testing
    helper_class = Helper
    helper_message = get_helper_message()

    async def on_load(self):
        pass
'''
        )

        return plugin_folder

    @pytest.fixture
    def cleanup_sys_modules(self):
        """Clean up sys.modules after test."""
        original_modules = set(sys.modules.keys())
        yield
        # Remove any modules added during the test
        modules_to_remove = [
            k
            for k in sys.modules.keys()
            if k not in original_modules and k.startswith("ncatbot_plugin")
        ]
        for mod in modules_to_remove:
            sys.modules.pop(mod, None)

    def test_top_level_package_created(self, importer, plugin_dir, cleanup_sys_modules):
        """Test that the top-level 'ncatbot_plugin' package is created."""
        # Ensure clean state
        sys.modules.pop("ncatbot_plugin", None)

        # Index the plugin
        plugin_name = importer._index_single_plugin(plugin_dir)
        assert plugin_name == "relative_import_test"

        # Load the plugin module
        importer.load_plugin_module(plugin_name)

        # Verify top-level package exists
        assert "ncatbot_plugin" in sys.modules
        assert sys.modules["ncatbot_plugin"] is not None

    def test_top_level_package_is_namespace_package(
        self, importer, plugin_dir, cleanup_sys_modules
    ):
        """Test that ncatbot_plugin is a proper namespace package."""
        sys.modules.pop("ncatbot_plugin", None)

        plugin_name = importer._index_single_plugin(plugin_dir)
        importer.load_plugin_module(plugin_name)

        top_pkg = sys.modules["ncatbot_plugin"]
        # Namespace package should have __path__ attribute
        assert hasattr(top_pkg, "__path__")
        # It's a namespace package so it doesn't need a file
        assert top_pkg.__spec__.origin is None

    def test_relative_import_works(self, importer, plugin_dir, cleanup_sys_modules):
        """Test that relative imports work correctly in plugin."""
        sys.modules.pop("ncatbot_plugin", None)

        plugin_name = importer._index_single_plugin(plugin_dir)
        module = importer.load_plugin_module(plugin_name)

        # Find the plugin class
        plugin_class = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and hasattr(attr, "name")
                and attr.name == "relative_import_test"
            ):
                plugin_class = attr
                break

        assert plugin_class is not None, "Plugin class not found"

        # Verify the relative import worked
        assert plugin_class.helper_class is not None
        assert plugin_class.helper_class.name == "TestHelper"
        assert plugin_class.helper_message == "Helper module loaded successfully!"

    def test_submodule_registered_in_sys_modules(
        self, importer, plugin_dir, cleanup_sys_modules
    ):
        """Test that submodules are accessible via sys.modules."""
        sys.modules.pop("ncatbot_plugin", None)

        plugin_name = importer._index_single_plugin(plugin_dir)
        importer.load_plugin_module(plugin_name)

        # The plugin package should be in sys.modules
        pkg_name = importer._get_plugin_pkg_name(plugin_name)
        assert pkg_name in sys.modules

        # The main module should be in sys.modules
        main_module_name = importer._get_plugin_main_module_name(plugin_name)
        assert main_module_name in sys.modules


class TestDeepNestedRelativeImport:
    """Test relative imports with deeper nesting."""

    @pytest.fixture
    def importer(self):
        return _ModuleImporter()

    @pytest.fixture
    def deep_nested_plugin(self, tmp_path):
        """Create a plugin with deeply nested modules."""
        plugin_root = tmp_path / "plugins"
        plugin_root.mkdir()

        plugin = plugin_root / "deep_nested"
        plugin.mkdir()
        (plugin / "manifest.toml").write_text(
            'name = "deep_nested"\nversion = "1.0.0"\nmain = "main"\n'
        )

        # Create deep nested structure: handlers/core/utils.py
        handlers = plugin / "handlers"
        handlers.mkdir()
        (handlers / "__init__.py").write_text("")

        core = handlers / "core"
        core.mkdir()
        (core / "__init__.py").write_text("")

        (core / "utils.py").write_text(
            """NESTED_VALUE = "deeply_nested_import_works"

class DeepHelper:
    value = NESTED_VALUE
"""
        )

        # Main file imports from deep nested module
        (plugin / "main.py").write_text(
            """from .handlers.core.utils import DeepHelper, NESTED_VALUE

from ncatbot.plugin_system import NcatBotPlugin


class DeepNestedPlugin(NcatBotPlugin):
    name = "deep_nested"
    version = "1.0.0"

    deep_helper = DeepHelper
    nested_value = NESTED_VALUE

    async def on_load(self):
        pass
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

    def test_deep_nested_relative_import(
        self, importer, deep_nested_plugin, cleanup_sys_modules
    ):
        """Test that deeply nested relative imports work."""
        sys.modules.pop("ncatbot_plugin", None)

        name = importer._index_single_plugin(deep_nested_plugin)
        module = importer.load_plugin_module(name)

        # Find the plugin class
        plugin_class = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and getattr(attr, "name", None) == "deep_nested":
                plugin_class = attr
                break

        assert plugin_class is not None
        assert plugin_class.nested_value == "deeply_nested_import_works"
        assert plugin_class.deep_helper.value == "deeply_nested_import_works"
