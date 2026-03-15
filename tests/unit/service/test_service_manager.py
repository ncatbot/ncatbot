"""
ServiceManager 规范测试

规范:
  S-01: register() 注册服务类
  S-02: load() 加载并返回服务实例
  S-03: load_all() 按拓扑排序加载
  S-04: 循环依赖抛 ValueError
  S-05: close_all() 关闭所有已加载服务
  S-06: get() 返回已加载服务实例
  S-07: has() 判断服务是否已加载
  S-08: register_builtin() 注册内置服务
"""

import pytest

from ncatbot.service.base import BaseService
from ncatbot.service.manager import ServiceManager

pytestmark = pytest.mark.asyncio


# ---- 测试用服务 ----


class DummyServiceA(BaseService):
    name = "service_a"
    dependencies = []

    async def on_load(self):
        self._loaded_flag = True

    async def on_close(self):
        self._loaded_flag = False


class DummyServiceB(BaseService):
    name = "service_b"
    dependencies = ["service_a"]

    async def on_load(self):
        pass

    async def on_close(self):
        pass


class DummyServiceC(BaseService):
    name = "service_c"
    dependencies = ["service_b"]

    async def on_load(self):
        pass

    async def on_close(self):
        pass


class CycleA(BaseService):
    name = "cycle_a"
    dependencies = ["cycle_b"]

    async def on_load(self):
        pass

    async def on_close(self):
        pass


class CycleB(BaseService):
    name = "cycle_b"
    dependencies = ["cycle_a"]

    async def on_load(self):
        pass

    async def on_close(self):
        pass


# ---- S-01: register ----


def test_register_service():
    """S-01: register() 记录服务类"""
    mgr = ServiceManager()
    mgr.register(DummyServiceA)
    assert "service_a" in mgr._service_classes


# ---- S-02: load ----


async def test_load_service():
    """S-02: load() 加载并返回服务实例"""
    mgr = ServiceManager()
    mgr.register(DummyServiceA)
    svc = await mgr.load("service_a")
    assert svc.is_loaded
    assert svc.name == "service_a"


async def test_load_nonexistent_raises():
    """S-02 补充: 未注册的服务 → KeyError"""
    mgr = ServiceManager()
    with pytest.raises(KeyError, match="未注册"):
        await mgr.load("nonexistent")


async def test_load_idempotent():
    """S-02 补充: 已加载的服务 → 直接返回"""
    mgr = ServiceManager()
    mgr.register(DummyServiceA)
    svc1 = await mgr.load("service_a")
    svc2 = await mgr.load("service_a")
    assert svc1 is svc2


# ---- S-03: load_all 拓扑排序 ----


async def test_load_all_topological():
    """S-03: load_all() 按拓扑排序加载 (A → B → C)"""
    mgr = ServiceManager()
    # 注册顺序故意倒序
    mgr.register(DummyServiceC)
    mgr.register(DummyServiceA)
    mgr.register(DummyServiceB)

    await mgr.load_all()

    assert mgr.has("service_a")
    assert mgr.has("service_b")
    assert mgr.has("service_c")


# ---- S-04: 循环依赖 ----


async def test_circular_dependency_raises():
    """S-04: 循环依赖 → ValueError"""
    mgr = ServiceManager()
    mgr.register(CycleA)
    mgr.register(CycleB)

    with pytest.raises(ValueError, match="循环依赖"):
        await mgr.load_all()


# ---- S-05: close_all ----


async def test_close_all():
    """S-05: close_all() 关闭所有已加载服务"""
    mgr = ServiceManager()
    mgr.register(DummyServiceA)
    await mgr.load("service_a")

    assert mgr.has("service_a")
    await mgr.close_all()
    assert not mgr.has("service_a")


# ---- S-06: get ----


async def test_get_loaded_service():
    """S-06: get() 返回已加载的服务实例"""
    mgr = ServiceManager()
    mgr.register(DummyServiceA)
    await mgr.load("service_a")

    svc = mgr.get("service_a")
    assert svc is not None
    assert svc.name == "service_a"


def test_get_unloaded_returns_none():
    """S-06 补充: 未加载的服务 → None"""
    mgr = ServiceManager()
    assert mgr.get("nonexistent") is None


# ---- S-07: has ----


async def test_has():
    """S-07: has() 判断服务是否已加载"""
    mgr = ServiceManager()
    mgr.register(DummyServiceA)

    assert not mgr.has("service_a")
    await mgr.load("service_a")
    assert mgr.has("service_a")


# ---- S-08: register_builtin ----


def test_register_builtin():
    """S-08: register_builtin() 注册 rbac, file_watcher, time_task"""
    mgr = ServiceManager()
    mgr.register_builtin()

    assert "rbac" in mgr._service_classes
    assert "file_watcher" in mgr._service_classes
    assert "time_task" in mgr._service_classes
