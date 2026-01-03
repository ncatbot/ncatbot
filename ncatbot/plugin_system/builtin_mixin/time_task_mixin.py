"""
定时任务混入类

提供定时任务的注册接口，实际调度由 TimeTaskService 服务完成。
任务执行通过事件订阅机制实现解耦。
"""

import asyncio
from typing import (
    Callable,
    Optional,
    List,
    Tuple,
    Dict,
    Any,
    Union,
    final,
    TYPE_CHECKING,
)
from uuid import UUID

from ncatbot.utils import get_log

if TYPE_CHECKING:
    from ncatbot.core.service.builtin.time_task import TimeTaskService
    from ncatbot.core import NcatBotEvent


class TimeTaskMixin:
    """
    定时任务调度混入类，提供定时任务的管理功能。

    描述:
        该混入类提供了定时任务的添加、移除等管理功能。
        实际的任务调度由 TimeTaskService 服务完成。
        任务执行通过事件订阅机制：
        1. 服务发布 ncatbot.[plugin_name].[task_name] 事件
        2. 插件订阅该事件并执行任务函数

    属性:
        _time_task_jobs (dict): 当前插件注册的任务信息（名称 -> handler_id）

    特性:
        - 支持固定时间间隔的任务调度
        - 支持条件触发机制
        - 支持最大执行次数限制
        - 通过事件机制实现任务执行解耦
    """

    @property
    def _time_task_service(self) -> Optional["TimeTaskService"]:
        """获取定时任务服务实例"""
        # 通过 service_manager 获取服务
        if hasattr(self, "_service_manager") and self._service_manager:
            return self._service_manager.get("time_task")
        return None

    def _get_plugin_name(self) -> str:
        """获取插件名称"""
        return getattr(self, "name", "unknown")

    @final
    def add_scheduled_task(
        self,
        job_func: Callable,
        name: str,
        interval: Union[str, int, float],
        conditions: Optional[List[Callable[[], bool]]] = None,
        max_runs: Optional[int] = None,
        args: Optional[Tuple] = None,
        kwargs: Optional[Dict] = None,
        args_provider: Optional[Callable[[], Tuple]] = None,
        kwargs_provider: Optional[Callable[[], Dict[str, Any]]] = None,
    ) -> bool:
        """
        添加一个定时任务。

        通过事件订阅机制实现任务执行：
        1. 向 TimeTaskService 注册调度任务
        2. 订阅 ncatbot.[plugin_name].[task_name] 事件
        3. 事件触发时执行 job_func

        Args:
            job_func: 要执行的任务函数
            name: 任务名称
            interval: 任务执行的时间间隔，支持多种格式:
                - 一次性任务: 'YYYY-MM-DD HH:MM:SS'
                - 每日任务: 'HH:MM'
                - 间隔任务: '120s', '2h30m', '0.5d' 等
            conditions: 任务执行的条件列表，所有条件返回 True 时才执行
            max_runs: 任务的最大执行次数
            args: 任务函数的位置参数
            kwargs: 任务函数的关键字参数
            args_provider: 提供任务函数位置参数的函数
            kwargs_provider: 提供任务函数关键字参数的函数

        Returns:
            如果任务添加成功返回 True，否则返回 False
        """
        LOG = get_log("TimeTaskMixin")

        service = self._time_task_service
        if service is None:
            LOG.warning("定时任务服务不可用，无法添加任务")
            return False

        # 检查事件总线是否可用
        event_bus = getattr(self, "_event_bus", None)
        if event_bus is None:
            LOG.warning("事件总线不可用，无法添加任务")
            return False

        # 参数冲突检查
        if (args and args_provider) or (kwargs and kwargs_provider):
            raise ValueError("静态参数和动态参数生成器不能同时使用")

        # 初始化任务记录
        if not hasattr(self, "_time_task_jobs"):
            self._time_task_jobs: Dict[str, UUID] = {}

        plugin_name = self._get_plugin_name()
        event_type = f"ncatbot.{plugin_name}.{name}"

        # 创建事件处理器，包装任务函数
        async def task_handler(event: "NcatBotEvent") -> None:
            """事件处理器：执行实际的任务函数"""
            try:
                # 动态参数
                dyn_args = args_provider() if args_provider else ()
                dyn_kwargs = kwargs_provider() if kwargs_provider else {}

                # 合并参数（动态参数优先）
                final_args = dyn_args or args or ()
                final_kwargs = {**(kwargs or {}), **dyn_kwargs}

                # 执行任务函数
                if asyncio.iscoroutinefunction(job_func):
                    await job_func(*final_args, **final_kwargs)
                else:
                    job_func(*final_args, **final_kwargs)
            except Exception as e:
                LOG.error(f"定时任务执行失败 [{name}]: {e}")

        # 订阅事件
        handler_id = event_bus.subscribe(event_type, task_handler)
        self._time_task_jobs[name] = handler_id

        # 向服务注册调度任务
        result = service.add_job(
            name=name,
            interval=interval,
            conditions=conditions,
            max_runs=max_runs,
            plugin_name=plugin_name,
        )

        if not result:
            # 注册失败，取消事件订阅
            event_bus.unsubscribe(handler_id)
            del self._time_task_jobs[name]
            return False

        LOG.debug(f"已添加定时任务: {name}, 事件类型: {event_type}")
        return True

    @final
    def remove_scheduled_task(self, task_name: str) -> bool:
        """
        移除一个定时任务。

        Args:
            task_name: 要移除的任务名称

        Returns:
            如果任务移除成功返回 True，否则返回 False
        """
        service = self._time_task_service
        if service is None:
            return False

        # 取消事件订阅
        if hasattr(self, "_time_task_jobs") and task_name in self._time_task_jobs:
            handler_id = self._time_task_jobs[task_name]
            event_bus = getattr(self, "_event_bus", None)
            if event_bus:
                event_bus.unsubscribe(handler_id)
            del self._time_task_jobs[task_name]

        return service.remove_job(name=task_name)

    @final
    def get_scheduled_task_status(self, task_name: str) -> Optional[Dict[str, Any]]:
        """
        获取定时任务状态。

        Args:
            task_name: 任务名称

        Returns:
            任务状态信息字典，包含:
                - name: 任务名称
                - next_run: 下次运行时间
                - run_count: 已执行次数
                - max_runs: 最大允许次数
        """
        service = self._time_task_service
        if service is None:
            return None
        return service.get_job_status(task_name)

    @final
    def list_scheduled_tasks(self) -> List[str]:
        """
        列出当前插件注册的所有定时任务名称。

        Returns:
            任务名称列表
        """
        if hasattr(self, "_time_task_jobs"):
            return list(self._time_task_jobs.keys())
        return []

    @final
    def cleanup_scheduled_tasks(self) -> None:
        """
        清理当前插件注册的所有定时任务。

        通常在插件卸载时调用。
        """
        if hasattr(self, "_time_task_jobs"):
            for task_name in list(self._time_task_jobs):
                self.remove_scheduled_task(task_name)
