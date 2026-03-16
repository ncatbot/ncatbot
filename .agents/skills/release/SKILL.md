---
name: release
description: "发布 NcatBot 新版本到 PyPI 和 GitHub Release。包含 commit 审查挑选、changelog 生成、构建打包、发布的完整流程。Use when: 发版、release、发布、changelog、版本号、pick commits、挑选提交、release notes。"
license: MIT
---

# 技能指令

你是 NcatBot 发布助手。帮助用户完成版本发布的完整流程：commit 审查挑选 → changelog 生成 → 版本号更新 → 构建打包 → PyPI 发布 → GitHub Release 创建。

## 前置条件

- Python 虚拟环境已激活（`.venv\Scripts\activate.ps1`）
- 已安装 `build` 和 `twine`（`uv pip install build twine`）
- PyPI API Token 已配置为环境变量 `TWINE_PASSWORD`（见 `.vscode/settings.json`）
- GitHub CLI（`gh`）已登录（`gh auth login --web`）

## 发布流程总览

```
Commit 审查 → Changelog 生成 → 版本号更新 → 构建 → PyPI → 参考资料打包 → GitHub Release
```

### 1. Commit 审查与挑选

> 详细参考：[references/commit-picking.md](references/commit-picking.md)

1. **获取候选 commits**：列出自上一个 tag 以来的所有 commits
2. **分类展示**：按 conventional-commits 类型分组呈现给用户
3. **用户挑选**：让用户确认哪些 commit 纳入本次 release notes
4. **生成 changelog**：根据挑选结果生成结构化 release notes

```powershell
# 获取上一个 tag
$lastTag = git describe --tags --abbrev=0 2>$null
if (!$lastTag) { $lastTag = (git rev-list --max-parents=0 HEAD) }

# 列出自上一个 tag 以来的 commits
git log "$lastTag..HEAD" --oneline --no-merges
```

将 commits 按以下类别分组展示：

| 类别 | 前缀 | Emoji |
|------|-------|-------|
| 新功能 | `feat` | ✨ |
| 修复 | `fix` | 🐛 |
| 重构 | `refactor` | ♻️ |
| 文档 | `docs` | 📝 |
| 测试 | `test` | ✅ |
| 构建/依赖 | `chore`, `build`, `ci` | 🔧 |
| 破坏性变更 | 含 `BREAKING CHANGE` 或 `!` | 💥 |

向用户展示分类列表，让用户 **逐类确认或排除** 特定 commit。默认纳入 `feat`、`fix`、`refactor` 和破坏性变更。

### 2. 生成 Release Notes

基于挑选的 commits 生成 Markdown 格式的 release notes：

```markdown
## ✨ 新功能
- <commit message> (<short hash>)

## 🐛 修复
- <commit message> (<short hash>)

## ♻️ 重构
- <commit message> (<short hash>)

## 💥 破坏性变更
- <commit message> (<short hash>)
```

规则：
- 移除 commit message 中的 `type(scope):` 前缀，只保留描述
- scope 非空时以 **粗体** 标注：`- **scope**: 描述 (hash)`
- 空类别不展示
- 让用户审阅并可手动编辑最终 notes

### 3. 更新版本号

> 详细参考：[references/release-steps.md](references/release-steps.md)

根据 commit 类型建议版本号递增策略：

| 条件 | 版本递增 | 示例 |
|------|---------|------|
| 含破坏性变更 | major | 5.0.0 → 6.0.0 |
| 含 `feat` | minor | 5.0.0 → 5.1.0 |
| 仅含 `fix` | patch | 5.0.0 → 5.0.1 |

向用户确认版本号后修改 `pyproject.toml` 中的 `version` 字段。

### 4. 构建发行包

```powershell
if (Test-Path dist) { Remove-Item dist -Recurse -Force }
python -m build
```

### 5. 发布到 PyPI

```powershell
python -m twine upload dist/* -u __token__
```

`twine` 会自动读取 `TWINE_PASSWORD` 环境变量中的 API Token。

### 6. 打包用户参考资料

将 `examples/`、`.agents/skills/`、`docs/` 打包为 zip（排除 `__pycache__`）：

```powershell
$ver = "X.Y.Z"  # 替换为实际版本
$zipPath = "dist\ncatbot5-$ver-user-reference.zip"
$tempDir = "dist\_pack_temp"

$files = Get-ChildItem -Recurse examples, skills, docs -File |
    Where-Object { $_.FullName -notmatch '__pycache__' }

if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force }
foreach ($f in $files) {
    $rel = $f.FullName.Replace((Get-Location).Path + '\', '')
    $dest = Join-Path $tempDir $rel
    $destDir = Split-Path $dest
    if (!(Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
    Copy-Item $f.FullName $dest
}
Compress-Archive -Path "$tempDir\*" -DestinationPath $zipPath
Remove-Item $tempDir -Recurse -Force
```

### 7. 创建 GitHub Release

使用步骤 2 生成的 release notes 作为 `--notes` 内容：

```powershell
$ver = "X.Y.Z"
gh release create "v$ver" `
    "dist/ncatbot5-$ver-user-reference.zip" `
    "dist/ncatbot5-$ver-py3-none-any.whl" `
    "dist/ncatbot5-$ver.tar.gz" `
    --title "v$ver" `
    --notes-file release-notes.md `
    --repo ncatbot/NcatBot
```

## 关键约束

- **先挑选 commit，再定版本号** — 版本号递增策略取决于本次包含的变更类型
- 发布前确认版本号已正确更新
- 构建前必须清理旧 `dist/` 目录
- 打包参考资料时排除 `__pycache__` 目录
- PyPI Token **不要**提交到版本控制
- 生成的 `release-notes.md` 是临时文件，发布完成后可删除
