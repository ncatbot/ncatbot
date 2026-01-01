"""
RBAC 权限系统集成测试

测试 RBACManager 的完整功能，包括：
- 用户/角色权限分配
- 权限检查
- 角色继承
- 黑白名单优先级
- 持久化
"""
import pytest
import tempfile
import os
from pathlib import Path

from ncatbot.plugin_system.rbac.rbac_manager import _RBACManager


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def rbac_manager():
    """创建新的 RBAC 管理器实例"""
    manager = _RBACManager(default_role="user")
    # 必须先创建默认角色
    manager.add_role("user")
    return manager


@pytest.fixture
def temp_rbac_file():
    """创建临时文件用于持久化测试"""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


# =============================================================================
# 基础权限管理测试
# =============================================================================

class TestRBACBasicIntegration:
    """基础 RBAC 集成测试"""
    
    def test_register_and_check_permission(self, rbac_manager):
        """测试注册权限并检查"""
        # 添加权限路径
        rbac_manager.add_permissions("plugin.greeter.send")
        
        # 添加用户
        rbac_manager.add_user("user1")
        
        # 分配权限给用户
        rbac_manager.assign_permissions_to_user("user1", "plugin.greeter.send", "white")
        
        # 检查权限
        assert rbac_manager.check_permission("user1", "plugin.greeter.send")
    
    def test_user_without_permission_denied(self, rbac_manager):
        """测试用户没有权限时被拒绝"""
        rbac_manager.add_permissions("plugin.admin.kick")
        rbac_manager.add_user("user1")
        
        # 未分配权限，应该被拒绝
        assert not rbac_manager.check_permission("user1", "plugin.admin.kick")
    
    def test_role_based_permission(self, rbac_manager):
        """测试基于角色的权限"""
        # 添加权限和角色
        rbac_manager.add_permissions("plugin.admin.kick")
        rbac_manager.add_role("moderator")
        
        # 给角色分配权限
        rbac_manager.assign_permissions_to_role("moderator", "plugin.admin.kick", "white")
        
        # 添加用户并分配角色
        rbac_manager.add_user("mod_user")
        rbac_manager.assign_role_to_user("moderator", "mod_user")
        
        # 用户应该通过角色获得权限
        assert rbac_manager.check_permission("mod_user", "plugin.admin.kick")


# =============================================================================
# 角色继承测试
# =============================================================================

class TestPermissionInheritance:
    """权限继承测试"""
    
    def test_role_inheritance(self, rbac_manager):
        """测试角色继承"""
        # 创建基础角色和高级角色
        rbac_manager.add_role("basic")
        rbac_manager.add_role("admin")
        
        # 添加权限
        rbac_manager.add_permissions("basic.read")
        rbac_manager.add_permissions("admin.write")
        
        # 给基础角色分配基础权限
        rbac_manager.assign_permissions_to_role("basic", "basic.read", "white")
        
        # 给管理员角色分配管理权限
        rbac_manager.assign_permissions_to_role("admin", "admin.write", "white")
        
        # 设置继承：admin 继承 basic
        rbac_manager.set_role_inheritance("admin", "basic")
        
        # 创建管理员用户
        rbac_manager.add_user("admin_user")
        rbac_manager.assign_role_to_user("admin", "admin_user")
        
        # 管理员应该有基础权限（继承）和管理权限
        assert rbac_manager.check_permission("admin_user", "basic.read")
        assert rbac_manager.check_permission("admin_user", "admin.write")
    
    def test_circular_inheritance_rejected(self, rbac_manager):
        """测试循环继承被拒绝"""
        rbac_manager.add_role("role_a")
        rbac_manager.add_role("role_b")
        rbac_manager.add_role("role_c")
        
        rbac_manager.set_role_inheritance("role_a", "role_b")
        rbac_manager.set_role_inheritance("role_b", "role_c")
        
        # role_c -> role_a 会形成循环 (role_a -> role_b -> role_c -> role_a)
        with pytest.raises(ValueError, match="循环继承"):
            rbac_manager.set_role_inheritance("role_c", "role_a")


# =============================================================================
# 黑名单测试
# =============================================================================

class TestBlacklistPermission:
    """黑名单权限测试"""
    
    def test_blacklist_overrides_whitelist(self, rbac_manager):
        """测试黑名单覆盖白名单"""
        rbac_manager.add_permissions("plugin.danger.execute")
        rbac_manager.add_user("user1")
        
        # 同时添加到白名单和黑名单
        rbac_manager.assign_permissions_to_user("user1", "plugin.danger.execute", "white")
        rbac_manager.assign_permissions_to_user("user1", "plugin.danger.execute", "black")
        
        # 黑名单优先，应该被拒绝
        assert not rbac_manager.check_permission("user1", "plugin.danger.execute")
    
    def test_role_blacklist_overrides_role_whitelist(self, rbac_manager):
        """测试角色黑名单覆盖角色白名单"""
        rbac_manager.add_permissions("action.dangerous")
        rbac_manager.add_role("mixed_role")
        
        # 添加到角色的白名单和黑名单
        rbac_manager.assign_permissions_to_role("mixed_role", "action.dangerous", "white")
        rbac_manager.assign_permissions_to_role("mixed_role", "action.dangerous", "black")
        
        rbac_manager.add_user("user1")
        rbac_manager.assign_role_to_user("mixed_role", "user1")
        
        # 黑名单优先
        assert not rbac_manager.check_permission("user1", "action.dangerous")


# =============================================================================
# 动态权限管理测试
# =============================================================================

class TestDynamicPermissionManagement:
    """动态权限管理测试"""
    
    def test_grant_revoke_permission(self, rbac_manager):
        """测试授予和撤销权限"""
        rbac_manager.add_permissions("plugin.test.action")
        rbac_manager.add_user("user1")
        
        # 授予权限
        rbac_manager.assign_permissions_to_user("user1", "plugin.test.action", "white")
        assert rbac_manager.check_permission("user1", "plugin.test.action")
        
        # 撤销权限
        rbac_manager.unassign_permissions_to_user("user1", "plugin.test.action")
        assert not rbac_manager.check_permission("user1", "plugin.test.action")
    
    def test_add_remove_role(self, rbac_manager):
        """测试添加和移除角色"""
        rbac_manager.add_permissions("role.perm")
        rbac_manager.add_role("temp_role")
        rbac_manager.assign_permissions_to_role("temp_role", "role.perm", "white")
        
        rbac_manager.add_user("user1")
        
        # 添加角色
        rbac_manager.assign_role_to_user("temp_role", "user1")
        assert rbac_manager.check_permission("user1", "role.perm")
        
        # 移除角色
        rbac_manager.unassign_role_to_user("temp_role", "user1")
        assert not rbac_manager.check_permission("user1", "role.perm")


# =============================================================================
# 持久化测试
# =============================================================================

class TestRBACPersistence:
    """RBAC 持久化测试"""
    
    def test_save_and_load(self, temp_rbac_file):
        """测试保存和加载"""
        import json
        
        # 创建并配置 manager
        manager1 = _RBACManager(default_role="user")
        manager1.add_role("user")  # 必须先创建默认角色
        manager1.add_permissions("plugin.test.action")
        manager1.add_role("tester")
        manager1.assign_permissions_to_role("tester", "plugin.test.action", "white")
        manager1.add_user("user1")
        manager1.assign_role_to_user("tester", "user1")
        
        # 保存
        with open(temp_rbac_file, "w", encoding="utf-8") as f:
            json.dump(manager1.to_dict(), f)
        
        # 加载到新实例
        with open(temp_rbac_file, "r", encoding="utf-8") as f:
            manager2 = _RBACManager.from_dict(json.load(f))
        
        # 验证权限保持一致
        assert manager2.check_permission("user1", "plugin.test.action")
    
    def test_load_preserves_inheritance(self, temp_rbac_file):
        """测试加载保留继承关系"""
        import json
        
        manager1 = _RBACManager(default_role="base")  # 使用 base 作为默认角色
        manager1.add_role("base")
        manager1.add_role("derived")
        manager1.add_permissions("base.perm")
        manager1.assign_permissions_to_role("base", "base.perm", "white")
        manager1.set_role_inheritance("derived", "base")
        manager1.add_user("user1")
        manager1.assign_role_to_user("derived", "user1")
        
        # 保存和加载
        with open(temp_rbac_file, "w", encoding="utf-8") as f:
            json.dump(manager1.to_dict(), f)
        
        with open(temp_rbac_file, "r", encoding="utf-8") as f:
            manager2 = _RBACManager.from_dict(json.load(f))
        
        # 继承的权限应该保留
        assert manager2.check_permission("user1", "base.perm")


# =============================================================================
# 边界条件测试
# =============================================================================

class TestRBACEdgeCases:
    """边界条件测试"""
    
    def test_non_existent_user_raises_error(self, rbac_manager):
        """测试不存在的用户抛出错误"""
        rbac_manager.add_permissions("test.perm")
        
        with pytest.raises(ValueError, match="不存在"):
            rbac_manager.check_permission("ghost_user", "test.perm")
    
    def test_non_existent_role_raises_error(self, rbac_manager):
        """测试不存在的角色抛出错误"""
        rbac_manager.add_user("user1")
        
        with pytest.raises(IndexError, match="不存在"):
            rbac_manager.assign_role_to_user("ghost_role", "user1")
    
    def test_non_existent_permission_path_raises_error(self, rbac_manager):
        """测试不存在的权限路径抛出错误"""
        rbac_manager.add_user("user1")
        
        with pytest.raises(ValueError, match="不存在"):
            rbac_manager.assign_permissions_to_user("user1", "ghost.permission", "white")
    
    def test_duplicate_user_raises_error(self, rbac_manager):
        """测试重复添加用户抛出错误"""
        rbac_manager.add_user("user1")
        
        with pytest.raises(IndexError, match="已经存在"):
            rbac_manager.add_user("user1")
    
    def test_duplicate_role_raises_error(self, rbac_manager):
        """测试重复添加角色抛出错误"""
        rbac_manager.add_role("role1")
        
        with pytest.raises(IndexError, match="已经存在"):
            rbac_manager.add_role("role1")


# =============================================================================
# 多用户多角色场景测试
# =============================================================================

class TestMultiUserMultiRole:
    """多用户多角色场景测试"""
    
    def test_multiple_users_same_role(self, rbac_manager):
        """测试多个用户共享角色"""
        rbac_manager.add_permissions("shared.action")
        rbac_manager.add_role("shared_role")
        rbac_manager.assign_permissions_to_role("shared_role", "shared.action", "white")
        
        for i in range(5):
            rbac_manager.add_user(f"user{i}")
            rbac_manager.assign_role_to_user("shared_role", f"user{i}")
        
        for i in range(5):
            assert rbac_manager.check_permission(f"user{i}", "shared.action")
    
    def test_user_multiple_roles(self, rbac_manager):
        """测试用户拥有多个角色"""
        rbac_manager.add_permissions("role1.perm")
        rbac_manager.add_permissions("role2.perm")
        rbac_manager.add_permissions("role3.perm")
        
        rbac_manager.add_role("role1")
        rbac_manager.add_role("role2")
        rbac_manager.add_role("role3")
        
        rbac_manager.assign_permissions_to_role("role1", "role1.perm", "white")
        rbac_manager.assign_permissions_to_role("role2", "role2.perm", "white")
        rbac_manager.assign_permissions_to_role("role3", "role3.perm", "white")
        
        rbac_manager.add_user("multi_role_user")
        rbac_manager.assign_role_to_user("role1", "multi_role_user")
        rbac_manager.assign_role_to_user("role2", "multi_role_user")
        rbac_manager.assign_role_to_user("role3", "multi_role_user")
        
        assert rbac_manager.check_permission("multi_role_user", "role1.perm")
        assert rbac_manager.check_permission("multi_role_user", "role2.perm")
        assert rbac_manager.check_permission("multi_role_user", "role3.perm")
    
    def test_complex_inheritance_chain(self, rbac_manager):
        """测试复杂的继承链"""
        # 创建继承链: root -> admin -> moderator -> user
        rbac_manager.add_role("user_role")
        rbac_manager.add_role("moderator")
        rbac_manager.add_role("admin")
        rbac_manager.add_role("root")
        
        rbac_manager.add_permissions("user.read")
        rbac_manager.add_permissions("mod.ban")
        rbac_manager.add_permissions("admin.config")
        rbac_manager.add_permissions("root.all")
        
        rbac_manager.assign_permissions_to_role("user_role", "user.read", "white")
        rbac_manager.assign_permissions_to_role("moderator", "mod.ban", "white")
        rbac_manager.assign_permissions_to_role("admin", "admin.config", "white")
        rbac_manager.assign_permissions_to_role("root", "root.all", "white")
        
        rbac_manager.set_role_inheritance("moderator", "user_role")
        rbac_manager.set_role_inheritance("admin", "moderator")
        rbac_manager.set_role_inheritance("root", "admin")
        
        rbac_manager.add_user("root_user")
        rbac_manager.assign_role_to_user("root", "root_user")
        
        # root 用户应该拥有所有权限
        assert rbac_manager.check_permission("root_user", "user.read")
        assert rbac_manager.check_permission("root_user", "mod.ban")
        assert rbac_manager.check_permission("root_user", "admin.config")
        assert rbac_manager.check_permission("root_user", "root.all")
