"""Split the single-file Markdown sources into MkDocs pages.

Single-file sources: tools/source/gurobi-to-copt-{zh,en}.md (one file per
language, kept for the rich-text website). This script derives docs/<lang>/*.md for
the MkDocs Material site:

* one page per top-level chapter (index / chapter1 / chapter2);
* blockquote call-outs  (> **Title.** body)  ->  Material admonitions;
* "Gurobi / COPT" code-block pairs  ->  a two-column grid (stacks on narrow screens);
* the outline table gets links to the chapter pages;
* the two runnable examples are also exported to examples/*.py.

Usage:  python tools/build_docs.py  (run from the repository root)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = {
    "zh": ROOT / "tools" / "source" / "gurobi-to-copt-zh.md",
    "en": ROOT / "tools" / "source" / "gurobi-to-copt-en.md",
}
PAGES = ["index", "chapter1", "chapter2"]

OUTLINE_LINKS = {
    "zh": {
        "**第 1 章 十分钟快速上手**": "[第 1 章 十分钟快速上手](chapter1.md)",
        "**第 2 章 核心对照表**": "[第 2 章 核心对照表](chapter2.md)",
    },
    "en": {
        "**Chapter 1 — Up and running in ten minutes**": "[Chapter 1 — Up and running in ten minutes](chapter1.md)",
        "**Chapter 2 — Core mapping tables**": "[Chapter 2 — Core mapping tables](chapter2.md)",
    },
}

PAIR_RE = re.compile(
    r"\*\*Gurobi[：:]\*\*\n\n```python\n(.*?)```\n\n\*\*COPT[：:]\*\*\n\n```python\n(.*?)```",
    re.S,
)


def code_pairs_to_grid(text: str) -> str:
    def repl(m: re.Match) -> str:
        g, c = m.group(1), m.group(2)
        return (
            '<div class="grid side-by-side" markdown>\n\n'
            f'```python title="Gurobi"\n{g}```\n\n'
            f'```python title="COPT"\n{c}```\n\n'
            "</div>"
        )

    return PAIR_RE.sub(repl, text)


def callouts_to_admonitions(text: str) -> str:
    """Convert `> **Title.** body` blockquotes into `!!! tip "Title"` admonitions."""
    out, i, lines = [], 0, text.split("\n")
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^> \*\*(.+?)\*\*\s*(.*)$", line)
        if m and not line.startswith("> **适用") and not line.startswith("> **Versions") and not line.startswith("> **Audience"):
            title, first = m.group(1).rstrip("。.：:"), m.group(2)
            body = [first] if first else []
            i += 1
            while i < len(lines) and lines[i].startswith(">"):
                body.append(lines[i][2:] if lines[i].startswith("> ") else lines[i][1:])
                i += 1
            out.append(f'!!! tip "{title}"')
            out.append("")
            for b in body:
                out.append(("    " + b) if b.strip() else "")
            continue
        out.append(line)
        i += 1
    return "\n".join(out)


def preface_to_admonitions(text: str) -> str:
    """The two-paragraph preface blockquote (versions / audience) -> info admonitions."""
    def repl(m: re.Match) -> str:
        block = m.group(0)
        parts = re.findall(r"> \*\*(.+?)\*\*[：:]\s*(.+)", block)
        return "\n\n".join(f'!!! info "{t}"\n\n    {b}' for t, b in parts)

    return re.sub(r"(?:^>.*\n?)+", repl, text, count=1, flags=re.M)


def split_pages(text: str) -> dict[str, str]:
    """index = title + preface + outline; chapterN = each `## ` section."""
    text = text.replace("\n---\n", "\n")
    parts = re.split(r"^## ", text, flags=re.M)
    head, sections = parts[0], parts[1:]
    pages = {"index": head + "## " + sections[0]}  # outline section stays on index
    for n, sec in enumerate(sections[1:], start=1):
        # promote headings: `## Chapter` -> `# Chapter`, `### 1.1` -> `## 1.1`
        sec = "# " + sec
        sec = re.sub(r"^### ", "## ", sec, flags=re.M)
        pages[f"chapter{n}"] = sec
    return pages


def export_examples(text: str, lang: str) -> None:
    if lang != "zh":
        return
    blocks = re.findall(r"```python title=\"(Gurobi|COPT)\"\n(.*?)```", text, re.S)
    names = ["ex1_gurobi", "ex1_copt", "ex2_gurobi", "ex2_copt"]
    for name, (_, code) in zip(names, blocks[:4]):
        (ROOT / "examples" / f"{name}.py").write_text(code, encoding="utf-8")


def main() -> None:
    for lang, src in SRC.items():
        if not src.exists():
            sys.exit(f"missing source {src}")
        text = src.read_text(encoding="utf-8")
        for old, new in OUTLINE_LINKS[lang].items():
            text = text.replace(old, new)
        text = code_pairs_to_grid(text)
        text = callouts_to_admonitions(text)
        text = preface_to_admonitions(text)
        export_examples(text, lang)
        for name, body in split_pages(text).items():
            front = "---\nhide:\n  - toc\n---\n\n" if name == "chapter1" else ""
            (ROOT / "docs" / lang / f"{name}.md").write_text(front + body.strip() + "\n", encoding="utf-8")
        print(lang, "->", ", ".join(f"docs/{lang}/{p}.md" for p in PAGES))


if __name__ == "__main__":
    main()
