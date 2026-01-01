"""Tests for ncatbot.plugin_system.rbac.rbac_path module."""

import pytest


class TestPermissionPathInit:
    """Tests for PermissionPath initialization."""

    def test_init_from_string(self):
        """Test creating PermissionPath from string."""
        from ncatbot.plugin_system.rbac.rbac_path import PermissionPath

        path = PermissionPath("plugin.command.execute")
        assert path.row_path == "plugin.command.execute"
        assert path.path == ("plugin", "command", "execute")

    def test_init_from_list(self):
        """Test creating PermissionPath from list."""
        from ncatbot.plugin_system.rbac.rbac_path import PermissionPath

        path = PermissionPath(["plugin", "command", "execute"])
        assert path.row_path == "plugin.command.execute"
        assert path.path == ("plugin", "command", "execute")

    def test_init_from_tuple(self):
        """Test creating PermissionPath from tuple."""
        from ncatbot.plugin_system.rbac.rbac_path import PermissionPath

        path = PermissionPath(("plugin", "command", "execute"))
        assert path.row_path == "plugin.command.execute"
        assert path.path == ("plugin", "command", "execute")

    def test_init_from_permission_path(self):
        """Test creating PermissionPath from another PermissionPath."""
        from ncatbot.plugin_system.rbac.rbac_path import PermissionPath

        original = PermissionPath("plugin.command")
        copy = PermissionPath(original)
        assert copy.row_path == original.row_path
        assert copy.path == original.path

    def test_init_invalid_type_raises_error(self):
        """Test that invalid type raises ValueError."""
        from ncatbot.plugin_system.rbac.rbac_path import PermissionPath

        with pytest.raises(ValueError, match="未知类型"):
            PermissionPath(12345)


class TestPermissionPathMagicMethods:
    """Tests for PermissionPath magic methods."""

    def test_repr(self):
        """Test __repr__ method."""
        from ncatbot.plugin_system.rbac.rbac_path import PermissionPath

        path = PermissionPath("a.b.c")
        repr_str = repr(path)
        assert "PermissionPath" in repr_str
        assert "a.b.c" in repr_str

    def test_str(self):
        """Test __str__ method."""
        from ncatbot.plugin_system.rbac.rbac_path import PermissionPath

        path = PermissionPath("a.b.c")
        assert str(path) == "a.b.c"

    def test_eq_with_permission_path(self):
        """Test equality with another PermissionPath."""
        from ncatbot.plugin_system.rbac.rbac_path import PermissionPath

        path1 = PermissionPath("a.b.c")
        path2 = PermissionPath("a.b.c")
        path3 = PermissionPath("a.b.d")

        assert path1 == path2
        assert not (path1 == path3)

    def test_eq_with_string(self):
        """Test equality with string."""
        from ncatbot.plugin_system.rbac.rbac_path import PermissionPath

        path = PermissionPath("a.b.c")
        assert path == "a.b.c"
        assert not (path == "a.b.d")

    def test_eq_with_tuple(self):
        """Test equality with tuple."""
        from ncatbot.plugin_system.rbac.rbac_path import PermissionPath

        path = PermissionPath("a.b.c")
        assert path == ("a", "b", "c")
        assert not (path == ("a", "b", "d"))

    def test_eq_with_list(self):
        """Test equality with list."""
        from ncatbot.plugin_system.rbac.rbac_path import PermissionPath

        path = PermissionPath("a.b.c")
        assert path == ["a", "b", "c"]
        assert not (path == ["a", "b", "d"])

    def test_eq_with_incompatible_type(self):
        """Test equality with incompatible type returns False."""
        from ncatbot.plugin_system.rbac.rbac_path import PermissionPath

        path = PermissionPath("a.b.c")
        assert not (path == 123)
        assert not (path == None)

    def test_len(self):
        """Test __len__ method."""
        from ncatbot.plugin_system.rbac.rbac_path import PermissionPath

        assert len(PermissionPath("a")) == 1
        assert len(PermissionPath("a.b")) == 2
        assert len(PermissionPath("a.b.c.d.e")) == 5

    def test_getitem(self):
        """Test __getitem__ method."""
        from ncatbot.plugin_system.rbac.rbac_path import PermissionPath

        path = PermissionPath("a.b.c")
        assert path[0] == "a"
        assert path[1] == "b"
        assert path[2] == "c"
        assert path[-1] == "c"

    def test_iter(self):
        """Test __iter__ method."""
        from ncatbot.plugin_system.rbac.rbac_path import PermissionPath

        path = PermissionPath("a.b.c")
        parts = list(path)
        assert parts == ["a", "b", "c"]

    def test_contains(self):
        """Test __contains__ method."""
        from ncatbot.plugin_system.rbac.rbac_path import PermissionPath

        path = PermissionPath("a.b.c")
        assert "a" in path
        assert "b" in path
        assert "d" not in path

    def test_call(self):
        """Test __call__ method creates new PermissionPath."""
        from ncatbot.plugin_system.rbac.rbac_path import PermissionPath

        path = PermissionPath("a.b")
        new_path = path("x.y.z")
        assert new_path.row_path == "x.y.z"
        assert isinstance(new_path, PermissionPath)


class TestPermissionPathMethods:
    """Tests for PermissionPath instance methods."""

    def test_join_single_path(self):
        """Test join with single path."""
        from ncatbot.plugin_system.rbac.rbac_path import PermissionPath

        path = PermissionPath("a.b")
        joined = path.join("c")
        assert joined.row_path == "a.b.c"

    def test_join_multiple_paths(self):
        """Test join with multiple paths."""
        from ncatbot.plugin_system.rbac.rbac_path import PermissionPath

        path = PermissionPath("a")
        joined = path.join("b", "c", "d")
        assert joined.row_path == "a.b.c.d"

    def test_join_empty_path(self):
        """Test join with empty string."""
        from ncatbot.plugin_system.rbac.rbac_path import PermissionPath

        path = PermissionPath("a.b")
        joined = path.join("")
        assert joined.row_path == "a.b"

    def test_split(self):
        """Test split method returns tuple."""
        from ncatbot.plugin_system.rbac.rbac_path import PermissionPath

        path = PermissionPath("a.b.c")
        split = path.split()
        assert split == ("a", "b", "c")
        assert isinstance(split, tuple)

    def test_get_valid_index(self):
        """Test get with valid index."""
        from ncatbot.plugin_system.rbac.rbac_path import PermissionPath

        path = PermissionPath("a.b.c")
        assert path.get(0) == "a"
        assert path.get(1) == "b"
        assert path.get(2) == "c"

    def test_get_invalid_index_returns_default(self):
        """Test get with invalid index returns default."""
        from ncatbot.plugin_system.rbac.rbac_path import PermissionPath

        path = PermissionPath("a.b.c")
        assert path.get(10) is None
        assert path.get(10, "default") == "default"


class TestPermissionPathMatching:
    """Tests for PermissionPath matching_path method."""

    def test_exact_match(self):
        """Test exact path matching."""
        from ncatbot.plugin_system.rbac.rbac_path import PermissionPath

        path = PermissionPath("a.b.c")
        assert path.matching_path("a.b.c") is True
        assert path.matching_path("a.b.d") is False

    def test_wildcard_star_in_pattern(self):
        """Test * wildcard in pattern."""
        from ncatbot.plugin_system.rbac.rbac_path import PermissionPath

        path = PermissionPath("plugin.command.execute")
        pattern = PermissionPath("plugin.*.execute")
        assert pattern.matching_path("plugin.command.execute") is True

    def test_wildcard_double_star(self):
        """Test ** wildcard matches all remaining."""
        from ncatbot.plugin_system.rbac.rbac_path import PermissionPath

        path = PermissionPath("a.b.c.d.e")
        pattern = PermissionPath("a.**")
        assert pattern.matching_path("a.b.c.d.e") is True

    def test_both_wildcards_raises_error(self):
        """Test that both paths having wildcards raises error."""
        from ncatbot.plugin_system.rbac.rbac_path import PermissionPath

        path1 = PermissionPath("a.*.c")
        with pytest.raises(ValueError, match="不能同时使用通配符"):
            path1.matching_path("a.*.d")

    def test_matching_shorter_path(self):
        """Test matching with shorter path."""
        from ncatbot.plugin_system.rbac.rbac_path import PermissionPath

        path = PermissionPath("a.b.c")
        # When matching shorter path against longer, behavior depends on implementation
        assert path.matching_path("a.b") is True  # Partial match allowed
        # complete=True checks if pattern fully covers target
        assert path.matching_path("a.b", complete=True) is True  # a.b is prefix of a.b.c
