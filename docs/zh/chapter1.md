---
hide:
  - toc
---

# 第 1 章 十分钟快速上手

本章介绍安装、许可证配置和两个完整示例，说明如何把一个 Gurobi 模型改为在 COPT 上运行，以及两套 API 的对应关系。

## 1.1 安装

两者都提供 pip 包，安装方式一致：

```bash
# Gurobi
pip install gurobipy

# COPT
pip install coptpy
```

官方文档建议在使用 Python 接口前先安装并配置好 COPT：完整安装包可从 [COPT 官网](https://copt.shanshu.ai) 下载，它同时提供命令行工具 `copt_cmd` 以及 C/C++/Java/C# 接口。

验证安装：

```python
import coptpy as cp
from coptpy import COPT
print(COPT.VERSION_MAJOR, COPT.VERSION_MINOR, COPT.VERSION_TECHNICAL)   # 例如 8 0 6
```

## 1.2 许可证

| | Gurobi | COPT |
|---|---|---|
| 许可证文件 | `gurobi.lic`（单个文件） | `license.dat` + `license.key`（两个文件，需放在同一目录） |
| 默认查找位置 | 用户主目录、`/opt/gurobi`（Linux）、`C:\gurobi`（Windows）、`/Library/gurobi`（macOS） | 用户主目录下的 `copt/` 文件夹（如 `~/copt/`、`C:\Users\<用户名>\copt\`），或 COPT 动态库 / `copt_cmd` 所在目录 |
| 环境变量 | `GRB_LICENSE_FILE`（指向文件） | `COPT_LICENSE_DIR`（指向目录） |
| 浮动 / 集群许可 | Token Server | 浮动 / 集群许可（客户端通过 `EnvrConfig` 或配置文件 `client.ini` 指向许可服务器） |
| 云端许可 | WLS（Web License Service） | Web 许可 |
| 试用 | pip 版自带规模受限的试用许可（2000 变量 × 2000 约束） | 在官网申请免费的个人许可 |

本文所有示例都是小规模模型，任何类型的 COPT 许可证都可以运行。

COPT 启动时会在日志中逐行打印检查过的许可证位置，排查许可证问题时可以先查看这几行：

```
[INFO] checks license for COPT v8.0.6 20260807
[WARN] no license files in current working folder: /home/laura/project
[WARN] no license files in HOME folder: /home/laura/copt
[INFO] empty environment variable: COPT_LICENSE_DIR
```

## 1.3 第一个模型：并排对照

一个最小的生产计划问题：两种产品 A、B，单件利润 20 和 30；机器工时 A 需 1 小时、B 需 2 小时，共 100 小时；原料 A 需 3 kg、B 需 2 kg，共 240 kg；B 的需求上限 30 件；产量为整数。

<div class="grid side-by-side" markdown>

```python title="Gurobi"
import gurobipy as gp
from gurobipy import GRB

m = gp.Model("production")

a = m.addVar(vtype=GRB.INTEGER, name="A")
b = m.addVar(vtype=GRB.INTEGER, ub=30, name="B")

m.addConstr(a + 2 * b <= 100, name="machine_hours")
m.addConstr(3 * a + 2 * b <= 240, name="raw_material")

m.setObjective(20 * a + 30 * b, GRB.MAXIMIZE)

m.optimize()

if m.Status == GRB.OPTIMAL:
    print(f"Profit = {m.ObjVal:g}")
    for v in m.getVars():
        print(f"{v.VarName} = {v.X:g}")
```

```python title="COPT"
import coptpy as cp
from coptpy import COPT

env = cp.Envr()
m = env.createModel("production")

a = m.addVar(vtype=COPT.INTEGER, name="A")
b = m.addVar(vtype=COPT.INTEGER, ub=30, name="B")

m.addConstr(a + 2 * b <= 100, name="machine_hours")
m.addConstr(3 * a + 2 * b <= 240, name="raw_material")

m.setObjective(20 * a + 30 * b, COPT.MAXIMIZE)

m.solve()

if m.status == COPT.OPTIMAL:
    print(f"Profit = {m.objval:g}")
    for v in m.getVars():
        print(f"{v.name} = {v.x:g}")
```

</div>

两段代码的输出完全一致：

```
Profit = 1850
A = 70
B = 15
```

两段代码逐行对照，共有五处不同：

| # | Gurobi | COPT | 说明 |
|---|---|---|---|
| 1 | `import gurobipy as gp` / `from gurobipy import GRB` | `import coptpy as cp` / `from coptpy import COPT` | 常量命名空间 `GRB` → `COPT` |
| 2 | `m = gp.Model("production")` | `env = cp.Envr()` <br> `m = env.createModel("production")` | COPT 需要先显式创建环境 `Envr`，再由环境创建模型 |
| 3 | `m.optimize()` | `m.solve()` | 求解方法名不同 |
| 4 | `GRB.OPTIMAL` | `COPT.OPTIMAL` | 状态常量名相同，但**数值不同**（2 与 1），应使用常量，不要写数字 |
| 5 | `v.VarName` / `v.X` | `v.name` / `v.x` | 变量名属性叫 `name`，解值叫 `x`；`m.ObjVal`、`m.Status` 在 COPT 里可以原样使用，见下文 |

第 5 点需要补充说明。COPT 文档规定，模型属性和变量 / 约束信息既可以按**原始大小写**访问（`m.ObjVal`、`m.Status`、`x.LB`、`x.UB`、`x.Obj`、`c.Slack`），也可以按**全小写**访问（`m.objval`、`x.lb`）。因此两边名称相同的属性，Gurobi 写法可以保留；需要修改的是名称本身不同的属性，如 `VarName` → `name`、`X` → `x`、`RC` → `rc`、`Pi` → `pi`、`NumVars` → `cols`、`Runtime` → `solvingtime`，完整对照见第 2 章。实测中 coptpy 对属性名的匹配不区分大小写，`x.X`、`c.Pi` 也能运行，但文档未作此保证，本文不依赖这一行为。本文的 COPT 代码统一使用文档中的小写写法。

## 1.4 一个更典型的例子：tupledict、quicksum 与影子价格

实际项目中的 gurobipy 代码通常使用 `addVars`、`tupledict`、`quicksum` 和 `addConstrs` 批量建模。下面以一个运输问题为例，同时展示参数设置和对偶值的读取。

<div class="grid side-by-side" markdown>

```python title="Gurobi"
import gurobipy as gp
from gurobipy import GRB

plants = ["P1", "P2"]
markets = ["M1", "M2", "M3"]
supply = {"P1": 60, "P2": 90}
demand = {"M1": 40, "M2": 50, "M3": 60}
cost = {("P1", "M1"): 4, ("P1", "M2"): 6, ("P1", "M3"): 9,
        ("P2", "M1"): 5, ("P2", "M2"): 3, ("P2", "M3"): 7}

m = gp.Model("transport")
m.Params.TimeLimit = 60
m.Params.OutputFlag = 0

ship = m.addVars(plants, markets, name="ship")

m.addConstrs((ship.sum(p, "*") <= supply[p] for p in plants),
             name="supply")
dem = m.addConstrs((ship.sum("*", k) >= demand[k] for k in markets),
                   name="demand")

obj = gp.quicksum(cost[p, k] * ship[p, k]
                  for p in plants for k in markets)
m.setObjective(obj, GRB.MINIMIZE)
m.optimize()

if m.Status == GRB.OPTIMAL:
    print(f"Total cost = {m.ObjVal:g}")
    for (p, k), v in ship.items():
        if v.X > 1e-6:
            print(f"  {p} -> {k}: {v.X:g}")
    for k in markets:
        print(f"  shadow price {k}: {dem[k].Pi:g}")
```

```python title="COPT"
import coptpy as cp
from coptpy import COPT

plants = ["P1", "P2"]
markets = ["M1", "M2", "M3"]
supply = {"P1": 60, "P2": 90}
demand = {"M1": 40, "M2": 50, "M3": 60}
cost = {("P1", "M1"): 4, ("P1", "M2"): 6, ("P1", "M3"): 9,
        ("P2", "M1"): 5, ("P2", "M2"): 3, ("P2", "M3"): 7}

env = cp.Envr()
m = env.createModel("transport")
m.setParam(COPT.Param.TimeLimit, 60)
m.setParam(COPT.Param.Logging, 0)

ship = m.addVars(plants, markets, nameprefix="ship")

m.addConstrs((ship.sum(p, "*") <= supply[p] for p in plants),
             nameprefix="supply")
dem = m.addConstrs((ship.sum("*", k) >= demand[k] for k in markets),
                   nameprefix="demand")

obj = cp.quicksum(cost[p, k] * ship[p, k]
                  for p in plants for k in markets)
m.setObjective(obj, COPT.MINIMIZE)
m.solve()

if m.status == COPT.OPTIMAL:
    print(f"Total cost = {m.objval:g}")
    for (p, k), v in ship.items():
        if v.x > 1e-6:
            print(f"  {p} -> {k}: {v.x:g}")
    for k in markets:
        print(f"  shadow price {k}: {dem[k].pi:g}")
```

</div>

输出同样一致：

```
Total cost = 770
  P1 -> M1: 40
  P1 -> M3: 20
  P2 -> M2: 50
  P2 -> M3: 40
  shadow price M1: 4
  shadow price M2: 5
  shadow price M3: 9
```

除 1.3 节的五处外，这个例子还有三处差异，也是迁移中最常遇到的：

| Gurobi | COPT | 说明 |
|---|---|---|
| `m.Params.TimeLimit = 60` | `m.setParam(COPT.Param.TimeLimit, 60)` <br> 或 `m.Param.TimeLimit = 60` | 参数设置见 2.7 节；参数**名字**大多相同，少数不同（如 `MIPGap` → `RelGap`） |
| `m.Params.OutputFlag = 0` | `m.setParam(COPT.Param.Logging, 0)` | 关闭日志的参数叫 `Logging` |
| `addVars(..., name="ship")` <br> `addConstrs(..., name="supply")` | `addVars(..., nameprefix="ship")` <br> `addConstrs(..., nameprefix="supply")` | 批量创建时关键字参数叫 `nameprefix`，名字由 COPT 自动生成；生成的格式也不同：Gurobi 为 `ship[P1,M1]`，COPT 实测为 `ship(P1,M1)` |

`tupledict`（含 `.sum()`、`.prod()`）、`quicksum`、`multidict`、`tuplelist` 在 coptpy 中都有同名实现，用法一致，这部分代码一般不需要改动。

## 1.5 本章检查清单

迁移一段 gurobipy 代码时，先做以下七项基本替换。其中除第 3 项外，其余六项与 COPT 团队维护的对照表 [COPTPY-GUROBIPY](https://github.com/leavesgrp/COPTPY-GUROBIPY) 列出的核心规则相同：

1. `import gurobipy as gp` → `import coptpy as cp`
2. `GRB` → `COPT`
3. `gp.Model(...)` → `env = cp.Envr()` + `env.createModel(...)`
4. `addVars`/`addConstrs` 的 `name=` → `nameprefix=`
5. `m.optimize()` → `m.solve()`
6. `m.getAttr("X", vars)` → `m.getInfo(COPT.Info.Value, vars)`
7. `VarName`/`ConstrName` → `name`

然后检查三项：

8. 硬编码的状态码数字（如 `== 2`）改为常量 `COPT.OPTIMAL` 等
9. `m.Params.X = v` → `m.Param.X = v`（`Params` 改为单数 `Param`）或 `m.setParam(COPT.Param.X, v)`，并核对参数名（2.7 节）
10. 其他改名的属性：`X` → `x`，`Pi` → `pi`，`RC` → `rc`，`NumVars`/`NumConstrs` → `cols`/`rows`，`Runtime` → `solvingtime`，`MIPGap` → `bestgap`（完整列表见 2.6 节）

多数中小型脚本完成这十项后即可运行。如果代码用到了回调、MIP 初始解（`x.Start`）、`addRange`、手工构造的 `LinExpr` 或求解后修改模型，请继续阅读第 2、3 章。
