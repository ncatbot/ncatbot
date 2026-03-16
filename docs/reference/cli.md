# CLI 命令参考

> `ncatbot` 命令行工具完整 API 参考。基于 [Click](https://click.palletsprojects.com/) 构建。

## Quick Start

```bash
ncatbot --help          # 查看所有命令
ncatbot <command> --help  # 查看单个命令帮助
```toml

## 入口点

```toml
# pyproject.toml
[project.scripts]
ncatbot = "ncatbot.cli:main"
```bash

也可通过模块方式调用：

```bash
python -m ncatbot.cli
```python

---

## 顶层命令

```bash
ncatbot [OPTIONS] [COMMAND]
```python

| 选项 | 说明 |
|------|------|
| `--version` | 显示版本号 |
| `--help` | 显示帮助信息 |

无子命令时进入交互模式（REPL）。

## init

```bash
ncatbot init [OPTIONS]
```python

初始化项目，创建 `config.yaml`、`plugins/` 目录，以及一个以当前计算机用户名命名的模板插件。

| 选项 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--dir` | `str` | `.` | 目标目录 |

交互式提示：

| 提示 | 说明 |
|------|------|
| 请输入机器人 QQ 号 | 写入 `bot_uin` |
| 请输入管理员 QQ 号 | 写入 `root` |

若 `config.yaml` 已存在，提示是否覆盖。

生成的模板插件位于 `plugins/{username}/`，包含 `manifest.toml` 和 `plugin.py`，实现群聊/私聊发送 `hello` 回复 `hi`。若模板插件目录已存在则跳过。

## run

```bash
ncatbot run [OPTIONS]
```python

启动 NcatBot（连接 NapCat + 加载插件 + 监听事件）。

| 选项 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--debug` | flag | `False` | 启用调试模式 |
| `--no-hot-reload` | flag | `False` | 禁用插件热重载 |
| `--plugin-dir` | `str` | `plugins` | 插件目录路径 |

## dev

```bash
ncatbot dev [OPTIONS]
```python

以开发模式启动（`debug=True` + 热重载）。

| 选项 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--plugin-dir` | `str` | `plugins` | 插件目录路径 |

## config

```bash
ncatbot config COMMAND
```python

配置管理命令组。

### config show

```bash
ncatbot config show
```python

以 YAML 格式显示当前全部配置。

### config get

```bash
ncatbot config get CONFIG_KEY
```python

| 参数 | 类型 | 说明 |
|------|------|------|
| `CONFIG_KEY` | `str` | 配置项路径，支持点分（如 `napcat.ws_uri`） |

### config set

```bash
ncatbot config set CONFIG_KEY CONFIG_VALUE
```python

| 参数 | 类型 | 说明 |
|------|------|------|
| `CONFIG_KEY` | `str` | 配置项路径，支持点分 |
| `CONFIG_VALUE` | `str` | 值（自动类型转换） |

类型转换规则：

| 输入值 | 转换类型 |
|--------|----------|
| `true` / `yes` | `bool (True)` |
| `false` / `no` | `bool (False)` |
| 纯数字字符串 | `int` |
| `[...]` JSON 格式 | `list` |
| 其它 | `str` |

### config check

```bash
ncatbot config check
```python

检查配置安全性和必填项，输出问题列表。

## plugin

```bash
ncatbot plugin COMMAND
```python

插件管理命令组。

### plugin list

```bash
ncatbot plugin list
```python

列出已安装插件，显示名称、版本、作者、状态。读取每个插件目录下的 `manifest.toml`。

### plugin create

```bash
ncatbot plugin create NAME
```python

| 参数 | 类型 | 说明 |
|------|------|------|
| `NAME` | `str` | 插件名（字母开头，仅字母/数字/下划线） |

在插件目录下生成标准脚手架，包含 `__init__.py`、`manifest.toml`、`plugin.py`、`README.md`。

### plugin info

```bash
ncatbot plugin info NAME
```python

| 参数 | 类型 | 说明 |
|------|------|------|
| `NAME` | `str` | 插件名 |

显示插件 `manifest.toml` 元数据。

### plugin enable

```bash
ncatbot plugin enable NAME
```python

启用插件：从黑名单移除，若白名单存在则加入白名单。

### plugin disable

```bash
ncatbot plugin disable NAME
```python

禁用插件：从白名单移除，加入黑名单。

### plugin remove

```bash
ncatbot plugin remove NAME
```text

| 参数 | 类型 | 说明 |
|------|------|------|
| `NAME` | `str` | 插件名 |

删除插件目录（含所有文件），并从黑名单/白名单中移除。
