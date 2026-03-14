# 贡献指南

本文件仅面向开发者，说明从 fork 到提交 PR 的必要步骤。假定你已经将仓库 fork 到自己的 GitHub 账号，并从自己的 fork 克隆到本地。

## 贡献步骤

1. Fork 本仓库
2. clone 你 Fork 的仓库到本地
3. 准备开发环境
4. 开发并测试
5. 启用 pre-commit 钩子检查并提交
6. 推送到你自己 Fork 的 Repo
7. 开 Pull Request


## 环境准备

### clone 到本地

```bash
git clone https://github.com/<你的用户名>/ncatbot.git
cd ncatbot
```

### 准备开发环境

推荐使用 [uv](https://docs.astral.sh/uv/) 管理环境：

```bash
uv sync --extra dev
```

激活虚拟环境：

```bash
source .venv/bin/activate    # Linux/macOS
.venv\Scripts\activate.ps1   # Windows PowerShell
```

### 启用 pre-commit 钩子（只需执行一次）

```bash
uv run pre-commit install
```
- pre-commit 会在 `git commit` 时检查代码格式并做一定自动修复。若 pre-commit 自动修复了文件，请执行 `git add` 将修复后的文件重新暂存后再提交。
- 如果存在无法自动修复的错误，请尽量认真阅读错误描述并修复。若确有必要跳过本地检查（不推荐），可使用 `git commit --no-verify`。

## 开发


- 新建分支进行开发：

```bash
git checkout -b feat/描述性短名
```

- 使用 [Conventional Commits](https://www.conventionalcommits.org/zh-hans/v1.0.0/) 编写提交信息，例如：

```bash
git commit -m "feat: 添加消息撤回功能"
git commit -m "fix(api): 修复消息队列溢出问题 #123"
git commit -m "docs: 更新安装指南"
```

## 测试

运行测试：

```bash
uv run pytest
```

运行带覆盖率的测试：

```bash
uv run pytest --cov=ncatbot --cov-report=term-missing
```

### 多版本测试（可选）

如需在多个 Python 版本（3.12, 3.13）上运行测试，可使用 tox：

```bash
uv run tox
```

也可以只运行特定版本：

```bash
uv run tox -e py312
```

> 注意：多版本测试不是提交 PR 的必要条件，CI 会自动在多版本上运行测试。

## 依赖管理

本项目使用 uv 管理依赖，依赖锁定在 `uv.lock` 中：

- **pyproject.toml**：定义顶层依赖（宽泛版本）
- **uv.lock**：自动生成的锁定版本文件（已纳入版本控制）

### 更新依赖

如需添加或修改依赖：

1. 编辑 `pyproject.toml` 中的 `dependencies` 列表
2. 重新锁定：

```bash
uv lock
```

3. 将 `pyproject.toml` 和 `uv.lock` 一起提交

### 升级所有依赖到最新版本

```bash
uv lock --upgrade
```

## 提交 PR


```bash
git push origin feat/描述性短名
```

- 在 GitHub 上为上游仓库创建 Pull Request（目标仓库为原始仓库），在说明里写明变更内容并关联 Issue（如有）。

## 代码规范

代码规范（要点）
- 遵循 PEP8，**尽量添加类型注解**。
- 必要时添加清晰的 docstring，例如：

```python
def handle_event(event: Event):
    """处理机器人事件。

    Args:
        event: 继承自 BaseEvent 的事件对象。
    """
```
