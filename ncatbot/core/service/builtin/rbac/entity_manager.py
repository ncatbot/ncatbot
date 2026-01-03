"""
RBAC 实体管理模块 - 处理权限、角色、用户的管理
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .service import RBACService


class EntityManager:
    """权限、角色、用户管理器"""

    def __init__(self, service: "RBACService"):
        self._service = service

    # ==========================================================================
    # 权限管理
    # ==========================================================================

    def add_permission(self, path: str) -> None:
        """添加权限"""
        if not self._service._permissions.exists(path, exact=True):
            self._service._permissions.add(path)
            self._service._clear_cache()

    def remove_permission(self, path: str) -> None:
        """移除权限"""
        self._service._permissions.remove(path)
        self._service._clear_cache()

    def permission_exists(self, path: str) -> bool:
        """检查权限是否存在"""
        return self._service._permissions.exists(path, exact=True)

    # ==========================================================================
    # 角色管理
    # ==========================================================================

    def add_role(self, role: str, exist_ok: bool = False) -> None:
        """添加角色"""
        if role in self._service._roles:
            if not exist_ok:
                raise ValueError(f"角色 {role} 已存在")
            return

        self._service._roles[role] = {"whitelist": set(), "blacklist": set()}
        self._service._role_users[role] = set()
        self._service._role_inheritance[role] = []

    def remove_role(self, role: str) -> None:
        """移除角色"""
        if role not in self._service._roles:
            raise ValueError(f"角色 {role} 不存在")

        # 从所有用户中移除该角色
        for user_data in self._service._users.values():
            if role in user_data["roles"]:
                user_data["roles"].remove(role)

        # 从继承链中移除
        for parent_roles in self._service._role_inheritance.values():
            if role in parent_roles:
                parent_roles.remove(role)

        del self._service._roles[role]
        del self._service._role_users[role]
        del self._service._role_inheritance[role]

    def role_exists(self, role: str) -> bool:
        """检查角色是否存在"""
        return role in self._service._roles

    def set_role_inheritance(self, role: str, parent: str) -> None:
        """设置角色继承"""
        if role not in self._service._roles:
            raise ValueError(f"角色 {role} 不存在")
        if parent not in self._service._roles:
            raise ValueError(f"父角色 {parent} 不存在")
        if role == parent:
            raise ValueError("不能继承自身")
        if self._would_create_cycle(role, parent):
            raise ValueError(f"检测到循环继承: {role} -> {parent}")

        if parent not in self._service._role_inheritance[role]:
            self._service._role_inheritance[role].append(parent)
            self._service._clear_cache()

    def _would_create_cycle(self, role: str, new_parent: str) -> bool:
        """检查是否会形成循环继承"""
        visited = set()

        def check(current: str) -> bool:
            if current == role:
                return True
            if current in visited:
                return False
            visited.add(current)
            for parent in self._service._role_inheritance.get(current, []):
                if check(parent):
                    return True
            return False

        return check(new_parent)

    # ==========================================================================
    # 用户管理
    # ==========================================================================

    def add_user(self, user: str, exist_ok: bool = False) -> None:
        """添加用户"""
        if user in self._service._users:
            if not exist_ok:
                raise ValueError(f"用户 {user} 已存在")
            return

        roles = [self._service._default_role] if self._service._default_role else []
        self._service._users[user] = {
            "whitelist": set(),
            "blacklist": set(),
            "roles": roles,
        }

        # 添加到默认角色的用户列表
        if (
            self._service._default_role
            and self._service._default_role in self._service._role_users
        ):
            self._service._role_users[self._service._default_role].add(user)

    def remove_user(self, user: str) -> None:
        """移除用户"""
        if user not in self._service._users:
            raise ValueError(f"用户 {user} 不存在")

        # 从所有角色的用户列表中移除
        for role, users in self._service._role_users.items():
            users.discard(user)

        del self._service._users[user]
        self._service._clear_cache()

    def user_exists(self, user: str) -> bool:
        """检查用户是否存在"""
        return user in self._service._users

    def user_has_role(self, user: str, role: str, create_user: bool = True) -> bool:
        """
        检查用户是否拥有指定角色（包括继承的角色）

        Args:
            user: 用户 ID
            role: 角色名
            create_user: 用户不存在时是否自动创建

        Returns:
            用户是否拥有该角色
        """
        if not self.user_exists(user):
            if create_user:
                self.add_user(user)
            else:
                return False

        # 获取用户所有角色（包括继承的）
        all_roles = set()

        def collect_roles(r: str):
            if r in all_roles:
                return
            all_roles.add(r)
            for parent in self._service._role_inheritance.get(r, []):
                collect_roles(parent)

        for r in self._service._users[user]["roles"]:
            collect_roles(r)

        return role in all_roles

    def assign_role(
        self,
        user: str,
        role: str,
        create_user: bool = True,
    ) -> None:
        """
        分配角色给用户

        Args:
            user: 用户名
            role: 角色名
            create_user: 用户不存在时是否自动创建
        """
        if role not in self._service._roles:
            raise ValueError(f"角色 {role} 不存在")

        if user not in self._service._users:
            if create_user:
                self.add_user(user)
            else:
                raise ValueError(f"用户 {user} 不存在")

        user_data = self._service._users[user]
        if role not in user_data["roles"]:
            user_data["roles"].append(role)

        if user not in self._service._role_users[role]:
            self._service._role_users[role].add(user)

        self._service._clear_cache()

    def unassign_role(self, user: str, role: str) -> None:
        """
        从用户移除角色

        Args:
            user: 用户名
            role: 角色名
        """
        if user not in self._service._users:
            raise ValueError(f"用户 {user} 不存在")

        if role not in self._service._roles:
            raise ValueError(f"角色 {role} 不存在")

        user_data = self._service._users[user]
        if role in user_data["roles"]:
            user_data["roles"].remove(role)

        self._service._role_users[role].discard(user)
        self._service._clear_cache()
