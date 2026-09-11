# 从 Gurobi 迁移到 COPT · Migrating from Gurobi to COPT

**在线阅读：** [中文](https://redpanda997.github.io/gurobi-to-copt/) · [English](https://redpanda997.github.io/gurobi-to-copt/en/)

这是一份写给 Python 用户的求解器迁移教程：如果你手头有一堆用 gurobipy 写的优化模型，想换到 COPT (coptpy) 上跑，这份教程告诉你哪些代码可以原样保留、哪些必须改、改成什么，以及两个求解器在设计上真正不同的地方在哪里。

教程以并排对照的方式展开——每个概念左边是 Gurobi 写法，右边是 COPT 写法——并尽量避免"照着改就行"式的敷衍：凡是两边不一一对应的地方，都解释了为什么，以及迁移时该怎么处理。

## 内容

| 章节 | 内容 | 状态 |
|---|---|---|
| 第 1 章 十分钟快速上手 | 安装、许可证、第一个模型的并排对照、七步迁移检查清单 | 已发布 |
| 第 2 章 核心对照表 | 环境与模型、变量、约束、目标、求解与状态码、结果读取、参数、常量、文件读写的逐项对照 | 已发布 |
| 第 3 章 不是一一对应的地方 | 两侧界约束、MIP 初始解、回调、求解后修改模型、参数语义差异 | 编写中 |
| 第 4 章 进阶专题 | 矩阵接口、多目标、解池、IIS、调参器、锥约束与非线性 | 计划中 |
| 第 5 章 在建模框架中切换 | Pyomo、JuMP、CVXPY、PuLP、AMPL、GAMS | 计划中 |
| 第 6 章 验证与性能 | 结果一致性、公平对比、读日志、何时调参 | 计划中 |
| 第 7 章 速查表与常见问题 | 一页纸速查表、FAQ | 计划中 |

## 关于准确性

文中所有代码都在 gurobipy 13.0.3 和 coptpy 8.0.6 上实际运行过，两边输出一致。对照表里的每一条表述都对照过两家的官方文档，凡是文档没有记载、只是实测可行的行为，文中都明确标注为"实测"。API 会随版本演进，发现过时或错误之处欢迎提 issue 或 PR。

## 目录结构

```
docs/zh/       中文页面
docs/en/       英文页面（与中文逐节对应）
examples/      文中两个完整示例的可运行脚本（Gurobi 版与 COPT 版）
mkdocs.yml     网站配置（MkDocs Material，含中英文切换）
```

网站由 GitHub Actions 自动构建发布；本地预览：

```bash
pip install -r requirements.txt
mkdocs serve
```

## 贡献

欢迎通过 [Issues](https://github.com/redpanda997/gurobi-to-copt/issues) 反馈错误、提出想看到的内容，或直接提 PR 修改 `docs/` 下的 Markdown。

---

*A bilingual, hands-on guide for moving Python optimization models from Gurobi to COPT. Every code sample is verified against gurobipy 13.0.3 and coptpy 8.0.6, and every statement in the mapping tables is checked against both vendors' official documentation. Issues and pull requests are welcome.*
