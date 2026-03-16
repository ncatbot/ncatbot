"""自动为 Markdown 文件中未标注语言的代码块添加语言标识。

启发式规则：
- 含 def/class/import/from/async → python
- 含 [section]/key = → toml
- 含 $/.venv/pip/git/ncatbot → bash
- 含目录树字符（├└│─）→ text
- 其他 → text

用法：
    python .agents/skills/consistency-check/scripts/fix_code_blocks.py          # 预览模式
    python .agents/skills/consistency-check/scripts/fix_code_blocks.py --apply  # 实际修改文件
"""

import argparse
import re
from pathlib import Path


def _find_root() -> Path:
    """向上查找含 pyproject.toml 的目录作为项目根。"""
    here = Path(__file__).resolve()
    for p in [here, *here.parents]:
        if (p / "pyproject.toml").exists():
            return p
    raise RuntimeError("Cannot find project root (no pyproject.toml found)")


PROJECT_ROOT = _find_root()

SCAN_DIRS = [
    PROJECT_ROOT / "docs",
    PROJECT_ROOT / "examples",
    PROJECT_ROOT / ".agents" / "skills",
]

CODE_BLOCK_START = re.compile(r"^(\s*)```(\w*)(.*)$")


def guess_language(lines: list[str]) -> str:
    """根据代码块内容猜测语言。"""
    text = "\n".join(lines)

    python_signals = [
        r"\bdef\b",
        r"\bclass\b",
        r"\bimport\b",
        r"\bfrom\b",
        r"\basync\b",
        r"\bawait\b",
        r"\bself\b",
        r"\bNone\b",
        r"^\s*@",
        r"^\s*#\s*[^\!]",
        r"__\w+__",
        r"\.py\b",
    ]
    python_score = sum(1 for p in python_signals if re.search(p, text, re.MULTILINE))

    toml_signals = [
        r"^\s*\[[\w._-]+\]",
        r"^\s*\w+\s*=\s*",
        r"^\s*name\s*=",
        r"^\s*version\s*=",
    ]
    toml_score = sum(1 for p in toml_signals if re.search(p, text, re.MULTILINE))

    bash_signals = [
        r"^\s*\$\s",
        r"pip\s+install",
        r"ncatbot\b",
        r"\.venv",
        r"^\s*git\s",
        r"^\s*cd\s",
        r"^\s*#\s*!",
        r"activate",
    ]
    bash_score = sum(1 for p in bash_signals if re.search(p, text, re.MULTILINE))

    tree_signals = [r"[├└│─]", r"^\s*\w+/\s*$"]
    tree_score = sum(1 for p in tree_signals if re.search(p, text, re.MULTILINE))

    yaml_signals = [r"^\s*\w+:", r"^\s*-\s+\w"]
    yaml_score = sum(1 for p in yaml_signals if re.search(p, text, re.MULTILINE))

    json_signals = [r"^\s*\{", r'^\s*"']
    json_score = sum(1 for p in json_signals if re.search(p, text, re.MULTILINE))

    md_signals = [r"^#+\s", r"^\*\*"]
    md_score = sum(1 for p in md_signals if re.search(p, text, re.MULTILINE))

    scores = {
        "python": python_score,
        "toml": toml_score,
        "bash": bash_score,
        "text": tree_score,
        "yaml": yaml_score,
        "json": json_score,
        "markdown": md_score,
    }

    best = max(scores, key=scores.get)
    return "text" if scores[best] == 0 else best


def process_file(md: Path, apply: bool) -> list[dict]:
    """处理单个文件，返回修改记录。"""
    content = md.read_text(encoding="utf-8", errors="replace")
    lines = content.split("\n")
    changes = []

    i = 0
    new_lines = []
    while i < len(lines):
        match = CODE_BLOCK_START.match(lines[i])
        if match and not match.group(2):
            indent = match.group(1)
            rest = match.group(3)
            block_lines = []
            j = i + 1
            while j < len(lines):
                if re.match(rf"^{re.escape(indent)}```\s*$", lines[j]):
                    break
                block_lines.append(lines[j])
                j += 1

            lang = guess_language(block_lines)
            changes.append(
                {
                    "file": str(md.relative_to(PROJECT_ROOT)),
                    "line": i + 1,
                    "language": lang,
                }
            )
            new_lines.append(f"{indent}```{lang}{rest}")
        else:
            new_lines.append(lines[i])
        i += 1

    if apply and changes:
        md.write_text("\n".join(new_lines), encoding="utf-8")

    return changes


def main():
    parser = argparse.ArgumentParser(description="自动修复代码块语言标注")
    parser.add_argument("--apply", action="store_true", help="实际修改文件")
    args = parser.parse_args()

    md_files = []
    for d in SCAN_DIRS:
        if d.exists():
            md_files.extend(d.rglob("*.md"))

    total_changes = []
    for md in sorted(md_files):
        changes = process_file(md, args.apply)
        total_changes.extend(changes)

    if not total_changes:
        print("✅ 所有代码块已标注语言")
        return

    lang_counts: dict[str, int] = {}
    for c in total_changes:
        lang_counts[c["language"]] = lang_counts.get(c["language"], 0) + 1

    mode = "已修复" if args.apply else "待修复（预览模式，使用 --apply 执行）"
    print(f"\n{mode}: {len(total_changes)} 个代码块")
    print("\n语言分布:")
    for lang, count in sorted(lang_counts.items(), key=lambda x: -x[1]):
        print(f"  {lang}: {count}")

    if not args.apply:
        print("\n前 20 个修改:")
        for c in total_changes[:20]:
            print(f"  {c['file']}:{c['line']}  → {c['language']}")


if __name__ == "__main__":
    main()
