# 从 Gurobi 迁移到 COPT · Migrating from Gurobi to COPT

Python 用户从 Gurobi (gurobipy) 迁移到 COPT (coptpy) 的实用指南，中英双语。
在线阅读：https://redpanda997.github.io/gurobi-to-copt/ （中文） · https://redpanda997.github.io/gurobi-to-copt/en/ （English）

A bilingual, hands-on guide for moving Python optimization models from Gurobi to COPT.
Every code sample is run against gurobipy 13.0.3 and coptpy 8.0.6.

## 仓库结构 · Layout

```
docs/
  zh/            中文页面（index / chapter1 / chapter2 …）
  en/            English pages, same structure
  assets/        自定义样式（左右并排代码块等）
examples/        文中两个完整示例的可运行脚本（Gurobi 版与 COPT 版）
tools/build_docs.py   从单文件 Markdown 源（tools/source/）生成 docs/ 页面的脚本（见下）
mkdocs.yml       MkDocs Material 配置（含中英文切换）
.github/workflows/deploy.yml   推送到 main 后自动构建并发布到 GitHub Pages
```

## 本地预览 · Preview locally

```bash
pip install -r requirements.txt
mkdocs serve          # http://127.0.0.1:8000
```

## 编辑内容 · Editing

直接修改 `docs/zh/*.md` 和 `docs/en/*.md` 即可，推送到 `main` 后约一分钟自动上线。

页面使用了两个 MkDocs Material 写法：

* 说明框：`!!! tip "标题"` 后接缩进四格的正文；
* Gurobi / COPT 并排代码：

  ````markdown
  <div class="grid side-by-side" markdown>

  ```python title="Gurobi"
  ...
  ```

  ```python title="COPT"
  ...
  ```

  </div>
  ````

`tools/source/` 里保留了单文件版本（`gurobi-to-copt-zh.md` / `-en.md`，用于粘贴到富文本网站），
`python tools/build_docs.py` 会把它们拆成上述页面并覆盖 `docs/`。两种维护方式选一种即可：
直接维护 `docs/`（推荐，此时删掉 `tools/`），或维护单文件源后重新运行脚本。

## 发布设置 · GitHub Pages setup（只需做一次）

1. 推送本目录到 `main`；
2. 等待 Actions 中的 **Deploy docs** 首次运行成功（它会创建 `gh-pages` 分支）；
3. 仓库 **Settings → Pages → Build and deployment → Source** 选 *Deploy from a branch*，
   分支选 `gh-pages` / `(root)`，保存；
4. 一两分钟后站点在 `https://redpanda997.github.io/gurobi-to-copt/` 上线。
   若日后把仓库转移到其他账号或组织，只需改 `mkdocs.yml` 里的 `site_url` / `repo_url` / `repo_name`。

## License

文档内容版权归 Cardinal Operations 所有；示例代码可自由使用。
