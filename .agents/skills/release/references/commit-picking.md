# Commit 审查与挑选

从工作区 git 历史中筛选 commits，生成结构化 release notes。

## 前置：工作区变更编排（阶段 1）

如果工作区有未提交的变更，先完成 commit 编排：

### 步骤 0a：审查工作区状态

```powershell
git status --short
git diff --stat
```python

### 步骤 0b：ASK 用户确认纳入范围

使用 `vscode_askQuestions` 展示变更文件列表，询问：
- 哪些文件/改动需要纳入本次发布
- 哪些改动暂不提交

### 步骤 0c：ASK 用户确认 Commit 分组方案

建议按模块/功能将变更拆分为多个 conventional-commits，使用 `vscode_askQuestions` 确认分组方案。

建议格式示例：
```python
分组 1: fix(adapter): 修复 WebSocket 连接中断
  - ncatbot/adapter/ws.py
  - ncatbot/adapter/connection.py

分组 2: feat(plugin): 新增热重载支持
  - ncatbot/plugin/loader.py
  - ncatbot/plugin/watcher.py
```python

### 步骤 0d：执行 Commit

按确认的方案依次提交：
```powershell
git add <files>
git commit -m "type(scope): description"
```python

---

## 步骤 1：获取候选 Commits

```powershell
# 自动检测上一个 tag
$lastTag = git describe --tags --abbrev=0 2>$null
if (!$lastTag) { $lastTag = (git rev-list --max-parents=0 HEAD) }

# 列出候选 commits（排除 merge commits）
git log "$lastTag..HEAD" --oneline --no-merges
```python

如果用户指定了起止范围（如某个 commit hash 或 tag），使用用户指定的范围：

```powershell
git log "<from>..<to>" --oneline --no-merges
```python

## 步骤 2：解析与分类

Commit message 遵循 Conventional Commits 格式：`type(scope): description`

按以下规则分类：

| 类型前缀 | 分类 | 默认纳入 |
|----------|------|---------|
| `feat` | ✨ 新功能 | ✅ |
| `fix` | 🐛 修复 | ✅ |
| `refactor` | ♻️ 重构 | ✅ |
| `perf` | ⚡ 性能优化 | ✅ |
| `docs` | 📝 文档 | ❌ |
| `test` | ✅ 测试 | ❌ |
| `chore`, `build`, `ci` | 🔧 构建/维护 | ❌ |
| `style` | 🎨 代码风格 | ❌ |
| 含 `BREAKING CHANGE` 或 `!` | 💥 破坏性变更 | ✅ |
| 无法识别的前缀 | 🔖 其他 | ❌ |

### 破坏性变更检测

以下模式标记为破坏性变更：
- 类型后带 `!`：`feat!: xxx` 或 `feat(scope)!: xxx`
- commit body 中含 `BREAKING CHANGE:`（需要 `git log --format="%B"` 检查）

## 步骤 3：展示与交互

向用户展示分类后的 commit 列表，格式：

```text
=== 自 v5.0.0 以来共 15 个 commits ===

✨ 新功能 (3) [默认纳入]
  ☑ 9f78314 增强 API 和消息处理能力
  ☑ 2f2ccea 改进插件 loader 和 manifest
  ☑ 391bb76 新增 CLI 模块

🐛 修复 (1) [默认纳入]
  ☑ ...

📝 文档 (5) [默认跳过]
  ☐ 7242bb0 更新了一些手册内容
  ☐ ...

🔧 构建/维护 (2) [默认跳过]
  ☐ ...
```python

然后询问用户：
1. 是否调整默认选择（纳入/排除特定 commit）
2. 是否有需要手动补充的变更说明

## 步骤 4：生成 Release Notes

根据用户确认的 commits 生成 `release-notes.md`：

```markdown
## ✨ 新功能
- **scope**: 描述 (hash)
- 描述 (hash)

## 🐛 修复
- 描述 (hash)

## ♻️ 重构
- 描述 (hash)

## 💥 破坏性变更
- 描述 (hash)
```python

### 格式化规则

1. **移除前缀**：`feat(api): 增强消息处理` → `**api**: 增强消息处理`
2. **scope 标注**：有 scope 时加粗标注，无 scope 时直接写描述
3. **hash 链接**：使用短 hash（7 位）
4. **空类别省略**：不展示没有 commits 的分类
5. **排序**：破坏性变更始终排在最前

### release notes 输出

将生成的内容写入 `release-notes.md`（项目根目录），后续步骤通过 `--notes-file` 传给 `gh release create`。

## 版本号建议

根据纳入的 commits 自动建议版本递增：

```yaml
当前版本: 5.0.0
纳入的变更: 3 feat, 1 fix, 2 refactor
建议: 5.1.0 (minor — 包含新功能)
```text

决策树：
1. 有 feat（大型）或 BREAKING CHANGE → minor
2. 有多个 fix 或小 feat → patch
3. 仅 1 个 fix → post
4. 无法判断 → ASK 用户

> **major 不参与此决策**。major 版本由人类主动提出，AI 执行即可。

将建议展示给用户，由用户最终确认。
