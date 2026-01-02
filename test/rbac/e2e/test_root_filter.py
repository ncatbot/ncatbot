"""RootFilter 与 RBAC 集成 E2E 测试

测试 RootFilter 仅允许 root 角色通过。
"""

from ncatbot.utils.testing import E2ETestSuite
from ncatbot.utils.assets.literals import PermissionGroup

from .conftest import RBAC_PLUGIN_DIR, cleanup_modules


class TestRootFilterWithRBAC:
    """测试 RootFilter 与 RBAC 的联动"""
    
    def test_root_filter_allows_root_role(self, rbac_service_for_e2e):
        """测试 root 角色可以通过 RootFilter"""
        cleanup_modules()
        
        rbac = rbac_service_for_e2e
        
        # 添加 root 角色和用户
        rbac.add_role(PermissionGroup.ROOT.value, exist_ok=True)
        rbac.add_user("root_user")
        rbac.assign_role("user", "root_user", PermissionGroup.ROOT.value)
        
        with E2ETestSuite(skip_builtin_plugins=False) as suite:
            suite.index_plugin(str(RBAC_PLUGIN_DIR))
            suite.register_plugin_sync("rbac_test_plugin")
            
            # root 用户执行 root_cmd 应该成功
            suite.inject_group_message_sync(
                "/root_cmd",
                user_id="root_user",
                group_id="test_group"
            )
            suite.assert_reply_sent()
            
            calls = suite.get_api_calls("send_group_msg")
            msg = str(calls[-1].get("message", ""))
            assert "root_cmd executed" in msg
        
        cleanup_modules()
    
    def test_root_filter_denies_admin_role(self, rbac_service_for_e2e):
        """测试 admin 角色无法通过 RootFilter"""
        cleanup_modules()
        
        rbac = rbac_service_for_e2e
        
        # 添加 admin 角色和用户（没有 root）
        rbac.add_role(PermissionGroup.ADMIN.value, exist_ok=True)
        rbac.add_user("admin_user")
        rbac.assign_role("user", "admin_user", PermissionGroup.ADMIN.value)
        
        with E2ETestSuite(skip_builtin_plugins=False) as suite:
            suite.index_plugin(str(RBAC_PLUGIN_DIR))
            suite.register_plugin_sync("rbac_test_plugin")
            
            # admin 用户执行 root_cmd 应该被过滤
            suite.inject_group_message_sync(
                "/root_cmd",
                user_id="admin_user",
                group_id="test_group"
            )
            
            # 检查没有 root_cmd executed 的回复
            calls = suite.get_api_calls("send_group_msg")
            for call in calls:
                msg = str(call.get("message", ""))
                assert "root_cmd executed" not in msg
        
        cleanup_modules()
    
    def test_root_filter_denies_regular_user(self, rbac_service_for_e2e):
        """测试普通用户无法通过 RootFilter"""
        cleanup_modules()
        
        rbac = rbac_service_for_e2e
        
        rbac.add_user("normal_user")
        
        with E2ETestSuite(skip_builtin_plugins=False) as suite:
            suite.index_plugin(str(RBAC_PLUGIN_DIR))
            suite.register_plugin_sync("rbac_test_plugin")
            
            suite.inject_group_message_sync(
                "/root_cmd",
                user_id="normal_user",
                group_id="test_group"
            )
            
            calls = suite.get_api_calls("send_group_msg")
            for call in calls:
                msg = str(call.get("message", ""))
                assert "root_cmd executed" not in msg
        
        cleanup_modules()


class TestMultiLevelInheritance:
    """测试多级继承场景"""
    
    def test_deep_inheritance_chain(self, rbac_service_for_e2e):
        """测试深层继承链"""
        cleanup_modules()
        
        rbac = rbac_service_for_e2e
        
        # 创建继承链: level3 -> level2 -> level1 -> admin
        rbac.add_role(PermissionGroup.ADMIN.value, exist_ok=True)
        rbac.add_role("level1")
        rbac.add_role("level2")
        rbac.add_role("level3")
        
        rbac.set_role_inheritance("level1", PermissionGroup.ADMIN.value)
        rbac.set_role_inheritance("level2", "level1")
        rbac.set_role_inheritance("level3", "level2")
        
        # 用户只有 level3 角色
        rbac.add_user("deep_user")
        rbac.assign_role("user", "deep_user", "level3")
        
        with E2ETestSuite(skip_builtin_plugins=False) as suite:
            suite.index_plugin(str(RBAC_PLUGIN_DIR))
            suite.register_plugin_sync("rbac_test_plugin")
            
            # 应该可以执行 admin_cmd（通过深层继承获得 admin 角色）
            suite.inject_group_message_sync(
                "/admin_cmd",
                user_id="deep_user",
                group_id="test_group"
            )
            suite.assert_reply_sent()
            
            calls = suite.get_api_calls("send_group_msg")
            msg = str(calls[-1].get("message", ""))
            assert "admin_cmd executed" in msg
        
        cleanup_modules()
    
    def test_deep_root_inheritance(self, rbac_service_for_e2e):
        """测试深层 root 继承"""
        cleanup_modules()
        
        rbac = rbac_service_for_e2e
        
        # 创建继承链: super_super_admin -> super_admin -> root
        rbac.add_role(PermissionGroup.ROOT.value, exist_ok=True)
        rbac.add_role("super_admin")
        rbac.add_role("super_super_admin")
        
        rbac.set_role_inheritance("super_admin", PermissionGroup.ROOT.value)
        rbac.set_role_inheritance("super_super_admin", "super_admin")
        
        rbac.add_user("super_user")
        rbac.assign_role("user", "super_user", "super_super_admin")
        
        with E2ETestSuite(skip_builtin_plugins=False) as suite:
            suite.index_plugin(str(RBAC_PLUGIN_DIR))
            suite.register_plugin_sync("rbac_test_plugin")
            
            # 应该可以执行 root_cmd（通过深层继承获得 root 角色）
            suite.inject_group_message_sync(
                "/root_cmd",
                user_id="super_user",
                group_id="test_group"
            )
            suite.assert_reply_sent()
            
            calls = suite.get_api_calls("send_group_msg")
            msg = str(calls[-1].get("message", ""))
            assert "root_cmd executed" in msg
        
        cleanup_modules()

