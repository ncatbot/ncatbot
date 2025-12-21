import sys
import importlib
import toml
from pathlib import Path
import re
import copy
from types import ModuleType
from typing import Dict, List, Optional

from ncatbot.utils import get_log

from ..config import config
from ..packhelper import PackageHelper

LOG = get_log("ModuleImporter")
_AUTO_INSTALL = config.auto_install_pip_pack


class _ModuleImporter:
    """把「目录->模块对象」的细节收敛到这里，方便做单元测试。"""

    def __init__(self, directory: str):
        self.directory = Path(directory).resolve()
        # 存储每个插件解析出的 manifest 数据： name -> dict
        self._manifests: Dict[str, dict] = {}
        self._plugin_folders: Dict[str, str] = {}
        # 原始插件名 -> sanitized 名称（用于生成合法的包名）
        self._sanitized_names: Dict[str, str] = {}
        self._used_sanitized: set = set()

    def _ensure_sanitized(self, plugin_name: str) -> str:
        """Generate and record a sanitized package-friendly name for a plugin.

        The sanitized name contains only ASCII letters, digits and underscores,
        and will not start with a digit. If a collision occurs the name will be
        suffixed with `_1`, `_2`, ... to ensure uniqueness. Returns the
        sanitized name.
        """
        if plugin_name in self._sanitized_names:
            return self._sanitized_names[plugin_name]

        base_sanitized = re.sub(r"[^0-9a-zA-Z_]", "_", plugin_name)
        if base_sanitized and base_sanitized[0].isdigit():
            base_sanitized = f"_{base_sanitized}"
        if not base_sanitized:
            base_sanitized = "_plugin"
        sanitized = base_sanitized
        idx = 1
        while sanitized in self._used_sanitized:
            sanitized = f"{base_sanitized}_{idx}"
            idx += 1
        self._used_sanitized.add(sanitized)
        self._sanitized_names[plugin_name] = sanitized
        LOG.debug("插件名映射: %s -> %s", plugin_name, sanitized)
        return sanitized

    def _ensure_entry(self, plugin_dir: Path, main_field: str) -> bool:
        """Check whether the manifest 'main' entry exists under `plugin_dir`.

        Supports values with or without a `.py` suffix. Returns True if the
        entry file exists, False otherwise.
        """
        main_path = Path(plugin_dir) / main_field
        if main_path.exists():
            return True
        # 如果未带 .py 后缀，再尝试添加 .py
        if (
            not main_field.endswith(".py")
            and (Path(plugin_dir) / (main_field + ".py")).exists()
        ):
            return True
        LOG.warning(
            "文件夹 %s 的 manifest 'main' 指向的入口文件未找到: %s，跳过",
            plugin_dir.name,
            main_field,
        )
        return False

    def inspect_all(self) -> List[str]:
        """返回所有合法的插件名"""
        for entry in self.directory.iterdir():
            manifest_path = entry / "manifest.toml"
            if entry.is_dir() and manifest_path.exists():
                try:
                    manifest = toml.load(manifest_path)
                    # 基本校验：必须包含 name/version/main
                    if (
                        not manifest.get("name")
                        or not manifest.get("version")
                        or not manifest.get("main")
                    ):
                        LOG.warning("插件 %s 的 manifest 缺少必填字段，跳过", entry)
                        continue
                    plugin_name = manifest.get("name")
                    self._ensure_sanitized(plugin_name)
                    main_field = manifest.get("main")
                    if not self._ensure_entry(entry, main_field):
                        continue

                    if plugin_name in self._plugin_folders:
                        LOG.warning("插件 %s 已存在，跳过加载", plugin_name)
                        LOG.info(
                            "文件夹 %s 和文件夹 %s 下存在同名插件 %s",
                            self._plugin_folders[plugin_name],
                            entry.name,
                            plugin_name,
                        )
                        LOG.info("跳过 %s 的载入", entry.name)
                        continue
                    self._plugin_folders[plugin_name] = entry.name
                    self._manifests[plugin_name] = manifest
                except Exception:
                    LOG.exception("解析 manifest 失败: %s", manifest_path)
                    continue
            else:
                LOG.debug("跳过非插件文件/目录或缺少 manifest: %s", entry)
        return list(self._plugin_folders.keys())

    def get_plugin_name_by_folder(self, folder_name):
        plugin_folder_name = self._plugin_folders
        for plugin_name, _folder_name in plugin_folder_name.items():
            if _folder_name == folder_name:
                return plugin_name

    def get_plugin_manifests(self) -> Dict[str, Dict]:
        if not self._manifests:
            self.inspect_all()
        return copy.copy(self._manifests)

    def unload_plugin_module(self, plugin_name: str) -> bool:
        """卸载指定模块及其所有子模块"""
        if not plugin_name or not isinstance(plugin_name, str):
            LOG.warning("无效的模块名称: %s", plugin_name)
            return False

        pkg_name = self._get_plugin_pkg_name(plugin_name)

        # Collect candidates: modules that are the plugin package or its submodules.
        # Also keep backward-compatible check for modules named by plugin_name (if ever used).
        modules_to_remove = []
        for module_name in list(sys.modules.keys()):
            if module_name == pkg_name or module_name.startswith(f"{pkg_name}."):
                modules_to_remove.append(module_name)

        if not modules_to_remove:
            LOG.debug("模块 %s 未加载，无需卸载", plugin_name)
            return True

        removed_count = 0
        for module_name in modules_to_remove:
            try:
                del sys.modules[module_name]
                removed_count += 1
                LOG.debug("已卸载模块: %s", module_name)
            except KeyError:
                # already removed concurrently; ignore
                pass

        # Invalidate import caches in case files change on disk later
        try:
            importlib.invalidate_caches()
        except Exception:
            LOG.debug("invalidate_caches failed for %s", plugin_name)

        LOG.info("成功卸载模块 %s (共 %d 个模块)", plugin_name, removed_count)
        return True

    def load_plugin_module(self, plugin_name: str) -> Optional[ModuleType]:
        original_sys_path = sys.path.copy()
        created_pkg = False
        created_module = False
        try:
            plugin_path = str(self._get_plugin_dir(plugin_name))
            sys.path.insert(0, plugin_path)

            pkg_name = self._get_plugin_pkg_name(plugin_name)
            module_name = self._get_plugin_main_module_name(plugin_name)

            if pkg_name not in sys.modules:
                # 创建一个空的模块作为包
                pkg_module = importlib.util.module_from_spec(
                    importlib.machinery.ModuleSpec(pkg_name, None, is_package=True)
                )
                pkg_module.__path__ = [plugin_path]
                sys.modules[pkg_name] = pkg_module
                created_pkg = True

            entry_file = self._get_plugin_entry_file(plugin_name)
            spec = importlib.util.spec_from_file_location(module_name, entry_file)
            if spec is None or spec.loader is None:
                LOG.exception(
                    "无法为插件 %s 创建模块 spec 或 loader 缺失: %s",
                    plugin_name,
                    entry_file,
                )
                raise ImportError(
                    f"Cannot load plugin {plugin_name}: spec or loader is None for {entry_file}"
                )
            module = importlib.util.module_from_spec(spec)
            # 明确保存 spec，便于调试/反射
            module.__spec__ = spec

            # 显式指定包名，确保相对导入 (from . import xxx) 正常工作
            module.__package__ = pkg_name

            # 注册模块对象（如果 exec 失败，需要回滚）
            sys.modules[module_name] = module
            created_module = True

            try:
                spec.loader.exec_module(module)
            except Exception:
                # 回滚我们对此次导入所做的 sys.modules 修改（仅回滚此函数中新建的项）
                if created_module:
                    sys.modules.pop(module_name, None)
                if created_pkg:
                    sys.modules.pop(pkg_name, None)
                raise

            return module
        except Exception as e:
            LOG.error("导入模块 %s 时出错: %s", plugin_name, e)
            raise
        finally:
            sys.path = original_sys_path

    def _get_plugin_dir(self, name: str) -> Path:
        return Path(self.directory) / self._plugin_folders[name]

    def _get_plugin_pkg_name(self, name: str) -> str:
        # 使用 sanitized 名称生成包名，若未记录则退回到原始 name（兼容老数据）
        sanitized = self._sanitized_names.get(name, name)
        return f"ncatbot_plugin.{sanitized}"

    def _get_plugin_entry_stem(self, name: str) -> str:
        """手滑把 .py 漏了也无所谓了"""
        filename: str = self.get_plugin_manifest(name).get("main")
        if filename.endswith(".py"):
            return filename[:-3]
        return filename

    def _get_plugin_entry_file(self, name: str) -> str:
        # 使用插件目录作为基准来查找入口文件，返回字符串形式以兼容现有调用处
        return str(
            self._get_plugin_dir(name) / (self._get_plugin_entry_stem(name) + ".py")
        )

    def _get_plugin_main_module_name(self, name: str) -> str:
        return f"{self._get_plugin_pkg_name(name)}.{self._get_plugin_entry_stem(name)}"

    def get_plugin_manifest(self, plugin_name: str) -> Optional[dict]:
        """返回已解析的 manifest（若 inspect_all 已解析过）。

        注意：如果未调用 `inspect_all` 此方法可能返回 `None`。
        """
        return self._manifests.get(plugin_name)

    def _maybe_install_deps(self, plugin_path: Path) -> None:
        if not _AUTO_INSTALL:
            return

        def ensure_req_from_requirements():
            req_file = (
                plugin_path / "requirements.txt"
                if plugin_path.is_dir()
                else plugin_path.with_suffix(".requirements.txt")
            )
            if not req_file.exists():
                return

            for line in req_file.read_text(encoding="utf-8").splitlines():
                req = line.strip()
                if not req or req.startswith("#") or req.startswith("-"):
                    continue
                self._ensure_package(req)

        def ensure_req_from_pyproject():
            pyproject = (
                plugin_path / "pyproject.toml"
                if plugin_path.is_dir()
                else plugin_path.with_suffix(".pyproject.toml")
            )
            if not pyproject.exists():
                return
            data = toml.load(pyproject)
            requires = data.get("project", {}).get("dependencies", [])
            for req in requires:
                self._ensure_package(req)

        ensure_req_from_pyproject()
        ensure_req_from_requirements()

    def _ensure_package(self, req: str) -> None:
        """检查包是否存在，不存在则安装。"""
        PackageHelper.ensure(req)
