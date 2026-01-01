"""Tests for ncatbot.plugin_system.rbac.rbac_trie module."""

import pytest


class TestTrieInit:
    """Tests for Trie initialization."""

    def test_init_default_case_sensitive(self):
        """Test default case sensitivity is True."""
        from ncatbot.plugin_system.rbac.rbac_trie import Trie

        trie = Trie()
        assert trie.case_sensitive is True
        assert trie.trie == {}

    def test_init_case_insensitive(self):
        """Test case insensitive initialization."""
        from ncatbot.plugin_system.rbac.rbac_trie import Trie

        trie = Trie(case_sensitive=False)
        assert trie.case_sensitive is False


class TestTrieFormatPath:
    """Tests for Trie format_path method."""

    def test_format_path_case_sensitive(self):
        """Test format_path preserves case when case_sensitive."""
        from ncatbot.plugin_system.rbac.rbac_trie import Trie
        from ncatbot.plugin_system.rbac.rbac_path import PermissionPath

        trie = Trie(case_sensitive=True)
        path = trie.format_path("Plugin.Command")
        assert path.row_path == "Plugin.Command"
        assert isinstance(path, PermissionPath)

    def test_format_path_case_insensitive(self):
        """Test format_path lowercases when case_insensitive."""
        from ncatbot.plugin_system.rbac.rbac_trie import Trie

        trie = Trie(case_sensitive=False)
        path = trie.format_path("Plugin.Command")
        assert path.row_path == "plugin.command"


class TestTrieAddPath:
    """Tests for Trie add_path method."""

    def test_add_single_path(self):
        """Test adding a single path."""
        from ncatbot.plugin_system.rbac.rbac_trie import Trie

        trie = Trie()
        trie.add_path("a.b.c")
        
        assert "a" in trie.trie
        assert "b" in trie.trie["a"]
        assert "c" in trie.trie["a"]["b"]

    def test_add_multiple_paths(self):
        """Test adding multiple paths."""
        from ncatbot.plugin_system.rbac.rbac_trie import Trie

        trie = Trie()
        trie.add_path("a.b.c")
        trie.add_path("a.b.d")
        trie.add_path("a.e")

        assert "c" in trie.trie["a"]["b"]
        assert "d" in trie.trie["a"]["b"]
        assert "e" in trie.trie["a"]

    def test_add_path_with_wildcard_raises_error(self):
        """Test adding path with * raises ValueError."""
        from ncatbot.plugin_system.rbac.rbac_trie import Trie

        trie = Trie()
        with pytest.raises(ValueError, match="不能使用"):
            trie.add_path("a.*.c")

    def test_add_path_with_double_wildcard_raises_error(self):
        """Test adding path with ** raises ValueError."""
        from ncatbot.plugin_system.rbac.rbac_trie import Trie

        trie = Trie()
        with pytest.raises(ValueError, match="不能使用"):
            trie.add_path("a.**")


class TestTrieCheckPath:
    """Tests for Trie check_path method."""

    def test_check_existing_path(self):
        """Test checking an existing path."""
        from ncatbot.plugin_system.rbac.rbac_trie import Trie

        trie = Trie()
        trie.add_path("a.b.c")
        
        assert trie.check_path("a.b.c") is True
        assert trie.check_path("a.b") is True
        assert trie.check_path("a") is True

    def test_check_non_existing_path(self):
        """Test checking a non-existing path."""
        from ncatbot.plugin_system.rbac.rbac_trie import Trie

        trie = Trie()
        trie.add_path("a.b.c")
        
        assert trie.check_path("a.b.d") is False
        assert trie.check_path("x.y.z") is False

    def test_check_path_complete_mode(self):
        """Test check_path with complete mode."""
        from ncatbot.plugin_system.rbac.rbac_trie import Trie

        trie = Trie()
        trie.add_path("a.b.c")
        
        # complete=True means path must be terminal (no children)
        assert trie.check_path("a.b.c", complete=True) is True
        assert trie.check_path("a.b", complete=True) is False

    def test_check_path_with_single_wildcard(self):
        """Test check_path with * wildcard."""
        from ncatbot.plugin_system.rbac.rbac_trie import Trie

        trie = Trie()
        trie.add_path("a.b.c")
        trie.add_path("a.d.e")
        
        # * matches any single node
        assert trie.check_path("a.*.c") is True
        assert trie.check_path("a.*.e") is True
        assert trie.check_path("a.*.x") is False

    def test_check_path_with_double_wildcard(self):
        """Test check_path with ** wildcard."""
        from ncatbot.plugin_system.rbac.rbac_trie import Trie

        trie = Trie()
        trie.add_path("a.b.c.d")
        
        # ** matches all remaining nodes
        assert trie.check_path("a.**") is True
        assert trie.check_path("a.b.**") is True


class TestTrieDelPath:
    """Tests for Trie del_path method."""

    def test_del_single_path(self):
        """Test deleting a single path."""
        from ncatbot.plugin_system.rbac.rbac_trie import Trie

        trie = Trie()
        trie.add_path("a.b.c")
        trie.del_path("a.b.c")
        
        assert trie.check_path("a.b.c") is False

    def test_del_path_with_max_mod(self):
        """Test deleting with max_mod removes empty parents."""
        from ncatbot.plugin_system.rbac.rbac_trie import Trie

        trie = Trie()
        trie.add_path("a.b.c")
        trie.del_path("a.b.c", max_mod=True)
        
        # With max_mod, entire chain should be removed
        assert trie.trie == {}

    def test_del_path_preserves_siblings(self):
        """Test deleting preserves sibling paths."""
        from ncatbot.plugin_system.rbac.rbac_trie import Trie

        trie = Trie()
        trie.add_path("a.b.c")
        trie.add_path("a.b.d")
        trie.del_path("a.b.c")
        
        assert trie.check_path("a.b.c") is False
        assert trie.check_path("a.b.d") is True

    def test_del_path_with_wildcard(self):
        """Test deleting with * wildcard."""
        from ncatbot.plugin_system.rbac.rbac_trie import Trie

        trie = Trie()
        trie.add_path("a.b.c")
        trie.add_path("a.d.c")
        trie.del_path("a.*.c")
        
        assert trie.check_path("a.b.c") is False
        assert trie.check_path("a.d.c") is False

    def test_del_path_with_double_wildcard(self):
        """Test deleting with ** wildcard."""
        from ncatbot.plugin_system.rbac.rbac_trie import Trie

        trie = Trie()
        trie.add_path("a.b.c")
        trie.add_path("a.b.d.e")
        trie.add_path("a.b.f")
        trie.del_path("a.b.**")
        
        # All children of a.b should be deleted
        assert trie.check_path("a.b.c") is False
        assert trie.check_path("a.b.d.e") is False
        assert trie.check_path("a.b.f") is False


class TestTrieCaseSensitivity:
    """Tests for Trie case sensitivity behavior."""

    def test_case_sensitive_add_and_check(self):
        """Test case sensitive trie differentiates case."""
        from ncatbot.plugin_system.rbac.rbac_trie import Trie

        trie = Trie(case_sensitive=True)
        trie.add_path("Plugin.Command")
        
        assert trie.check_path("Plugin.Command") is True
        assert trie.check_path("plugin.command") is False

    def test_case_insensitive_add_and_check(self):
        """Test case insensitive trie ignores case."""
        from ncatbot.plugin_system.rbac.rbac_trie import Trie

        trie = Trie(case_sensitive=False)
        trie.add_path("Plugin.Command")
        
        assert trie.check_path("Plugin.Command") is True
        assert trie.check_path("plugin.command") is True
        assert trie.check_path("PLUGIN.COMMAND") is True
