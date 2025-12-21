from collections import defaultdict, deque
from typing import Dict, List, Set, Any

from ..pluginsys_err import PluginCircularDependencyError, PluginNameConflictError


class _DependencyResolver:
    """把「依赖图 -> 加载顺序」的逻辑独立出来，方便测试。"""

    def __init__(self) -> None:
        self._graph: Dict[str, Set[str]] = {}
        self._constraints: Dict[str, Dict[str, str]] = {}

    def build(self, plugin_manifests: Dict[str, Dict[str, Any]]) -> None:
        self._graph.clear()
        self._constraints.clear()
        # plugin_classes 必须为 name -> (Type[BasePlugin], manifest_dict)
        for name, manifest in plugin_manifests.items():
            deps = manifest.get("dependencies", {}) or {}
            self._graph[name] = set(deps.keys())
            self._constraints[name] = deps

    def resolve(self) -> List[str]:
        """返回按依赖排序后的插件名；出错抛异常。"""
        self._check_duplicate_names()
        in_degree = {k: 0 for k in self._graph}
        adj = defaultdict(list)
        for cur, deps in self._graph.items():
            for d in deps:
                adj[d].append(cur)
                in_degree[cur] += 1

        q = deque([k for k, v in in_degree.items() if v == 0])
        order = []
        while q:
            cur = q.popleft()
            order.append(cur)
            for nxt in adj[cur]:
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    q.append(nxt)

        if len(order) != len(self._graph):
            raise PluginCircularDependencyError(set(self._graph) - set(order))
        return order

    # ------------------------------------------------------------------
    # 私有
    # ------------------------------------------------------------------
    def _check_duplicate_names(self) -> None:
        seen = set()
        for name in self._graph:
            if name in seen:
                raise PluginNameConflictError(name)
            seen.add(name)
