# 发布步骤详解

## 完整发布清单

### 阶段 0：工作区变更编排

如果工作区有未提交的变更（`git status` 非空）：

1. 展示变更文件列表，**ASK** 用户哪些纳入本次发布
2. 建议 commit 分组方案，**ASK** 用户确认/调整
3. 按确认方案依次 `git add` + `git commit`
4. 工作区无变更时自动跳过此阶段

> 详见 [commit-picking.md](commit-picking.md) 前置部分

### 阶段 1：Commit 审查与挑选

> 详见 [commit-picking.md](commit-picking.md)

1. 获取自上一个 tag 以来的所有 commits
2. 按类型分组展示给用户
3. **ASK** 用户确认纳入/排除
4. 生成 release notes 文件 `release-notes.md`

### 阶段 2：准备

1. 确认所有代码已合并到目标分支
2. 根据 commit 类型确定版本递增策略（版本格式：`X.Y.Z[.postN]`）：

   | 条件 | 版本递增 | 是否 ASK |
   |------|---------|--------|
   | 仅 1 个 `fix`（紧急热修复） | **post**（如 `5.1.0.post1`） | 自动 |
   | 多个 `fix` 或小的 `feat` 增加 | **patch**（如 `5.1.1`） | 自动 |
   | 大型 `feat` 或破坏性变更 | **minor**（如 `5.2.0`） | 自动 |
   | 无法归类（仅 refactor/docs 等） | — | **ASK** 用户 |

   > **major 不在 AI 决策范围内**，由人类主动发起，AI 不主动提及或建议。

3. 更新 `pyproject.toml` 中的 `version` 字段

### 阶段 3：构建

```powershell
# 激活虚拟环境
.venv\Scripts\activate.ps1

# 确保构建工具已安装
uv pip install build twine

# 清理旧产物
if (Test-Path dist) { Remove-Item dist -Recurse -Force }

# 构建
python -m build
```

构建产物：
- `dist/ncatbot5-{version}-py3-none-any.whl` — wheel 包
- `dist/ncatbot5-{version}.tar.gz` — 源码包

### 阶段 4：发布到 PyPI

```powershell
# 使用 API Token 上传（Token 通过 TWINE_PASSWORD 环境变量提供）
python -m twine upload dist/* -u __token__
```

验证发布：访问 https://pypi.org/project/ncatbot5/{version}/

### 阶段 5：打包用户参考资料

目标：将 `examples/`、`.agents/skills/`、`docs/` 打包为一个 zip 文件，供用户下载参考。

> `docs/` 是 Git submodule，打包前需确保已拉取内容。

```powershell
# 确保 docs submodule 内容已拉取
git submodule update --init

$ver = "{version}"
$zipPath = "dist\ncatbot5-$ver-user-reference.zip"
$tempDir = "dist\_pack_temp"

# 收集文件（排除 __pycache__）
$files = Get-ChildItem -Recurse examples, .agents\skills, docs -File |
    Where-Object { $_.FullName -notmatch '__pycache__' }

# 复制到临时目录（保持目录结构）
if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force }
foreach ($f in $files) {
    $rel = $f.FullName.Replace((Get-Location).Path + '\', '')
    $dest = Join-Path $tempDir $rel
    $destDir = Split-Path $dest
    if (!(Test-Path $destDir)) {
        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
    }
    Copy-Item $f.FullName $dest
}

# 压缩
Compress-Archive -Path "$tempDir\*" -DestinationPath $zipPath

# 清理临时目录
Remove-Item $tempDir -Recurse -Force
```

### 阶段 6：创建 GitHub Release

```powershell
$ver = "{version}"
gh release create "v$ver" `
    "dist/ncatbot5-$ver-user-reference.zip" `
    "dist/ncatbot5-$ver-py3-none-any.whl" `
    "dist/ncatbot5-$ver.tar.gz" `
    --title "v$ver" `
    --notes-file release-notes.md `
    --repo ncatbot/NcatBot
```

验证发布：访问 https://github.com/ncatbot/NcatBot/releases/tag/v{version}

发布完成后清理临时文件：

```powershell
if (Test-Path release-notes.md) { Remove-Item release-notes.md }
```

## 环境变量配置

| 变量 | 用途 | 配置位置 |
|------|------|---------|
| `TWINE_PASSWORD` | PyPI API Token | `.vscode/settings.json` → `terminal.integrated.env.windows` |

## 常见问题

### `No module named build`

安装构建工具：`uv pip install build twine`

### `gh: To get started with GitHub CLI, please run: gh auth login`

运行 `gh auth login --web` 进行浏览器认证。

### twine 上传 403

检查 Token 是否过期，重新生成后更新 `.vscode/settings.json` 中的 `TWINE_PASSWORD`。

### 版本号冲突

PyPI 不允许覆盖已发布的版本。如果版本号已存在，需要递增版本号。
