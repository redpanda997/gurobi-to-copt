# 第 2 章 核心对照表

本章按建模流程的顺序展开：环境与模型 → 变量 → 约束 → 目标与表达式 → 求解与状态 → 结果读取 → 参数 → 常量 → 文件读写。每节先用一两段代码说明该环节的差别在哪里，再给出完整的对照表；表格可以单独作为速查表使用。本章的代码片段承接第 1 章的写法：`gp`、`GRB`、`cp`、`COPT` 已导入，`m` 是模型，`x`、`y`、`z` 是变量，`c` 是约束。

以下三条规则概括了两套 API 的主要差异：

1. **方法名基本相同。** `addVar`、`addVars`、`addConstr`、`addConstrs`、`setObjective`、`getVars`、`getConstrs`、`computeIIS`、`write`、`read`、`remove`、`reset`、`tune` 等在两边同名同义。主要例外是 `optimize()` → `solve()`。
2. **属性可以用原始大小写或全小写访问，但部分属性名不同。** COPT 文档规定属性名可写成原始大小写（`m.ObjVal`）或全小写（`m.objval`），因此与 Gurobi 同名的属性可以保留。需要修改的是名称不同的属性，见 2.6 节。
3. **状态码数值不同。** `GRB.OPTIMAL == 2` 而 `COPT.OPTIMAL == 1`。代码中直接写数字而不是常量的判断，迁移后会失效。

## 2.1 环境与模型生命周期

Gurobi 的模型可以直接创建，环境对象是可选的；COPT 的模型必须由环境对象创建：

<div class="grid side-by-side" markdown>

```python title="Gurobi"
env = gp.Env()                     # 可省略，Model() 会隐式创建默认环境
m = gp.Model("demo", env=env)
```

```python title="COPT"
env = cp.Envr()
m = env.createModel("demo")
```

</div>

使用浮动或集群许可时，COPT 在创建环境前用 `EnvrConfig` 指定许可服务器：

```python
cfg = cp.EnvrConfig()
cfg.set(COPT.CLIENT_CLUSTER, "192.168.9.9")   # 浮动许可改用 COPT.CLIENT_FLOATING
env = cp.Envr(cfg)
m = env.createModel("demo")
```

| 操作 | Gurobi | COPT | 说明 |
|---|---|---|---|
| 导入 | `import gurobipy as gp` <br> `from gurobipy import GRB` | `import coptpy as cp` <br> `from coptpy import COPT` | |
| 创建环境 | `env = gp.Env()`（可省略，`Model()` 会隐式创建默认环境） | `env = cp.Envr()` | COPT 需要显式创建环境，模型通过环境创建 |
| 创建模型 | `m = gp.Model("name", env=env)` | `m = env.createModel("name")` | 模型由环境创建 |
| 从文件创建模型 | `m = gp.read("model.mps")` | `m = env.createModel()` <br> `m.read("model.mps")` | COPT 通过模型对象读取文件 |
| 复制模型 | `m2 = m.copy()` | `m2 = m.clone()` | |
| 释放资源 | `m.dispose()` / `env.dispose()` <br> 或 `with gp.Env() as env, gp.Model(env=env) as m:` | 不需要显式释放，对象随 Python 垃圾回收自动销毁 | COPT 没有 `dispose()`，文档也未定义 `with` 用法，对象随作用域结束自动回收。`env.close()` 只用于断开浮动 / 集群许可服务器的连接 |
| 同步修改 | `m.update()` | 建模过程中不需要 | 见下方说明 |

!!! tip "COPT 不需要 `update()`"

    Gurobi 采用惰性更新：添加变量、修改边界、删除元素等操作会先排队，在调用 `m.update()`、`optimize()` 或 `write()` 时才生效。Gurobi 文档指出，忘记调用 `update()` 不会报错，查询返回的是上一次更新时的值。COPT 的官方示例中没有这一步骤：添加变量和约束、设置参数后可以直接求解和查询。coptpy 提供的 `Model.update()` 按文档定义用于"更新模型的数值范围以及已删除的变量和约束"，只在删除元素后需要读取系数范围等统计量时才需要调用。迁移时可以删除代码中的 `m.update()` 调用。

!!! tip "参数只在模型层设置"

    Gurobi 的参数可以设在 `Env` 上，也可以设在 `Model` 上；模型在创建时复制当前环境的参数，之后对环境的修改不再影响该模型。COPT 的求解参数全部设在 `Model` 上，`Envr` 只管理许可证和资源。多个模型共用一套参数时，可以用 `m.read("settings.par")` 读入参数文件，或用一个函数统一设置。

## 2.2 变量

单个变量的创建方式两边相同。批量创建时，Gurobi 的 `name` 参数在 COPT 中叫 `nameprefix`；批量读取属性时，Gurobi 的 `getAttr` 对应 COPT 的 `getInfo`。两者都接受 list 或 `tupledict`，并返回同类型的容器：

<div class="grid side-by-side" markdown>

```python title="Gurobi"
x = m.addVars(3, 2, vtype=GRB.BINARY, name="x")
m.optimize()
vals = m.getAttr("X", x)                 # tupledict，键与 x 相同
```

```python title="COPT"
x = m.addVars(3, 2, vtype=COPT.BINARY, nameprefix="x")
m.solve()
vals = m.getInfo(COPT.Info.Value, x)     # tupledict，键与 x 相同
```

</div>

| 操作 | Gurobi | COPT | 说明 |
|---|---|---|---|
| 单个变量 | `m.addVar(lb=0, ub=GRB.INFINITY, obj=0, vtype=GRB.CONTINUOUS, name="x")` | `m.addVar(lb=0, ub=COPT.INFINITY, obj=0, vtype=COPT.CONTINUOUS, name="x")` | 签名一致 |
| 批量变量 | `m.addVars(I, J, vtype=GRB.BINARY, name="x")` | `m.addVars(I, J, vtype=COPT.BINARY, nameprefix="x")` | `name` → `nameprefix`；名字格式 `x[i,j]` → `x(i,j)` |
| 矩阵变量 | `m.addMVar(shape, lb=..., ub=..., name=...)` | `m.addMVar(shape, lb=..., ub=..., nameprefix=...)` | 第 4 章 |
| 按名字查找 | `m.getVarByName("x")` | `m.getVarByName("x")` | |
| 所有变量 | `m.getVars()`（返回 list） | `m.getVars()`（返回 `VarArray`，可直接 for 迭代；`.getAll()` 转为 list，`.getSize()` 取个数） | |
| 变量个数 | `m.NumVars` | `m.cols` | |
| 删除变量 | `m.remove(x)` | `m.remove(x)` | |
| 修改类型 | `x.VType = GRB.INTEGER` | `x.vtype = COPT.INTEGER` 或 `m.setVarType(x, COPT.INTEGER)` | |
| 修改边界 | `x.LB = 0; x.UB = 5` | `x.LB = 0; x.UB = 5` | 同名 |
| 批量读 / 写属性 | `m.getAttr("LB", vars)` / `m.setAttr("LB", vars, vals)` | `m.getInfo(COPT.Info.LB, vars)` / `m.setInfo(COPT.Info.LB, vars, vals)` | Gurobi 用字符串属性名，COPT 用 `COPT.Info.*` 常量 |

**边界与无穷大**：`GRB.INFINITY` 是 `1e100`，`COPT.INFINITY` 是 `1e30`。按 COPT 文档，绝对值达到 `1e30` 的边界即被视为无穷，因此旧代码中的 `1e100` 在 COPT 中同样被识别为无界。反向则不成立：从 COPT 读出的 `1e30` 传给 Gurobi 时会被当作有限值。建议统一使用 `COPT.INFINITY` 常量。

**变量的 `tupledict`**：`addVars` 返回的对象在两边都是 `tupledict`，支持 `.sum(...)`、`.prod(coeff_dict)` 以及普通 dict 的方法，用法相同。

## 2.3 约束

用比较运算符写约束的方式两边相同，`addConstrs` 加生成器的批量写法也相同。差别在两处：区间约束的内部表示，以及读取右端项的属性。

区间约束 `lb ≤ expr ≤ ub` 两边都可以写成 `expr == [lb, ub]`，也都有专用方法：

<div class="grid side-by-side" markdown>

```python title="Gurobi"
m.addRange(x + y, 1, 5, name="r1")
m.addConstr(x + y == [1, 5], name="r2")   # 与上一行等价
```

```python title="COPT"
m.addBoundConstr(x + y, 1, 5, name="r1")
m.addConstr(x + y == [1, 5], name="r2")   # 与上一行等价
```

</div>

Gurobi 把区间约束存成等式约束并增加一个辅助变量，模型的变量数因此加一；COPT 直接存为 `lb ≤ expr ≤ ub`，不增加变量。

读取约束的右端项时，Gurobi 用 `Sense` 和 `RHS`，COPT 用 `lb` 和 `ub`：

<div class="grid side-by-side" markdown>

```python title="Gurobi"
c = m.addConstr(x + y <= 10, name="c")
m.update()
print(c.Sense, c.RHS)                     # < 10.0
```

```python title="COPT"
c = m.addConstr(x + y <= 10, name="c")
print(c.lb, c.ub)                         # -1e+30 10.0
```

</div>

| 操作 | Gurobi | COPT | 说明 |
|---|---|---|---|
| 线性约束（表达式写法） | `m.addConstr(x + y <= 10, name="c")` | `m.addConstr(x + y <= 10, name="c")` | 一致 |
| 线性约束（显式写法） | `m.addLConstr(x + y, GRB.LESS_EQUAL, 10, name="c")` | `m.addConstr(x + y, COPT.LESS_EQUAL, 10, name="c")` | COPT 的 `addConstr` 同时接受两种写法 |
| 批量约束 | `m.addConstrs((expr_i <= b_i for i in I), name="c")` | `m.addConstrs((expr_i <= b_i for i in I), nameprefix="c")` | `name` → `nameprefix` |
| 区间约束 | `m.addRange(expr, lb, ub, name="r")` | `m.addBoundConstr(expr, lb, ub, name="r")` | 见下方"两侧界"说明 |
| 二次约束 | `m.addQConstr(...)` | `m.addQConstr(...)` | 一致 |
| SOS 约束 | `m.addSOS(GRB.SOS_TYPE1, vars, weights)` | `m.addSOS(COPT.SOS_TYPE1, vars, weights)` | 一致 |
| 指示约束 | `m.addGenConstrIndicator(z, True, x + y <= 5)` | `m.addGenConstrIndicator(z, True, x + y <= 5)` | 一致（COPT 多一个可选参数 `type`，默认为 if-then） |
| 其它通用约束 | `addGenConstrAbs / Max / Min / And / Or / PWL` | 同名 | 一致 |
| 非线性约束 | `m.addGenConstrNL(...)` 及 `nlfunc` | `m.addNlConstr(...)` 及 `cp.nl` | 第 4 章 |
| 矩阵约束 | `m.addMConstr(A, x, sense, b)` | `m.addMConstr(A, x, sense, b)` | 第 4 章 |
| 按名字查找 | `m.getConstrByName("c")` | `m.getConstrByName("c")` | |
| 所有约束 | `m.getConstrs()` | `m.getConstrs()`（返回 `ConstrArray`） | |
| 约束个数 | `m.NumConstrs` | `m.rows` | |
| 删除约束 | `m.remove(c)` | `m.remove(c)` | |
| 修改系数 | `m.chgCoeff(c, x, 2.0)` | `m.setCoeff(c, x, 2.0)` | |
| 读取系数 / 行 / 列 | `m.getCoeff(c, x)` / `m.getRow(c)` / `m.getCol(x)` | 同名 | |
| 读取系数矩阵 | `m.getA()` | `m.getA()` | 均返回 SciPy 稀疏矩阵 |

!!! tip "COPT 的约束统一为两侧界形式"

    Gurobi 的线性约束由 `Sense`（`<`/`>`/`=`）和 `RHS` 描述，区间约束需要用 `addRange`，Gurobi 内部通过引入辅助变量实现。COPT 把每条线性约束统一表示为 `lb ≤ expr ≤ ub`，用 `c.lb` 和 `c.ub` 描述：`x + y <= 10` 存储为 `lb = -COPT.INFINITY, ub = 10`；`x + y >= 1` 为 `lb = 1, ub = +COPT.INFINITY`；`x + y == 3` 为 `lb = ub = 3`。区间约束用 `addBoundConstr` 直接表示，不引入辅助变量；求解后可以分别修改 `lb` 和 `ub`。迁移时的对应修改：

    - 读 `c.RHS` 的代码改成读 `c.ub`（≤ 约束）或 `c.lb`（≥ 约束）；
    - 求解后"改右端项"的代码改成给 `c.lb` / `c.ub` 赋值；
    - `addRange` 改为 `addBoundConstr`。

## 2.4 目标函数与表达式

`setObjective` 的用法相同，用运算符和 `quicksum` 构造的表达式也不需要改动。手工调用 `LinExpr` 的方法逐项添加时要注意参数顺序：Gurobi 的 `addTerms` 先写系数再写变量，COPT 的 `addTerm`/`addTerms` 先写变量再写系数：

<div class="grid side-by-side" markdown>

```python title="Gurobi"
expr = gp.LinExpr(1.0)                    # 常数项 1.0
expr.addTerms(2.0, x)                     # 系数在前，变量在后
expr.addTerms([3.0, 4.0], [y, z])
m.setObjective(expr, GRB.MINIMIZE)
```

```python title="COPT"
expr = cp.LinExpr(1.0)
expr.addTerm(x, 2.0)                      # 变量在前，系数在后
expr.addTerms([y, z], [3.0, 4.0])
m.setObjective(expr, COPT.MINIMIZE)
```

</div>

| 操作 | Gurobi | COPT | 说明 |
|---|---|---|---|
| 设置目标 | `m.setObjective(expr, GRB.MAXIMIZE)` | `m.setObjective(expr, COPT.MAXIMIZE)` | 一致 |
| **只改方向** | **`m.ModelSense = GRB.MINIMIZE`** | **`m.ObjSense = COPT.MINIMIZE`** 或 `m.setObjSense(COPT.MINIMIZE)` | |
| **目标常数项** | **`m.ObjCon = 5`** | **`m.ObjConst = 5`** 或 `m.setObjConst(5)` | |
| 读取目标表达式 | `m.getObjective()` | `m.getObjective()` | |
| 变量的目标系数 | `x.Obj` | `x.Obj` | 同名 |
| 多目标 | `m.setObjectiveN(expr, index, priority, weight, ...)` | `m.setObjectiveN(index, expr, sense, priority, weight, ...)` | **参数顺序不同**，第 4 章 |
| 矩阵形式目标 | `m.setMObjective(...)` | `m.setMObjective(...)` | 第 4 章 |
| 线性表达式逐项添加 | `expr.addTerms(coeffs, vars)` | `expr.addTerm(var, coeff)` / `expr.addTerms(vars, coeffs)` | **参数顺序相反**，见上文 |
| 表达式常数项 | `gp.LinExpr(1.0)` / `expr.getConstant()` | `cp.LinExpr(1.0)` / `expr.getConstant()` | 一致 |

## 2.5 求解与状态码

求解方法名不同（`optimize()` 与 `solve()`），状态常量同名但数值不同，判断是否已有可用解的属性也不同：

| 操作 | Gurobi | COPT |
|---|---|---|
| 求解 | `m.optimize()` | `m.solve()` |
| 只解 LP 松弛 / LP 问题 | `m.relax().optimize()` | `m.solveLP()`（忽略整数性，直接求解 LP） |
| 中断 | `m.terminate()` | `m.interrupt()` |
| 清除解 | `m.reset()` / `m.reset(1)` | `m.reset()` / `m.resetAll()`（后者同时清除 MIP 初始解、IIS 等附加信息） |
| 读取状态 | `m.Status` | `m.Status` |
| 是否有可用解 | `m.SolCount > 0` | `m.HasSol`（旧属性 `HasMipSol` / `HasLpSol` 在 8.0 文档中已标记为弃用） |

状态码对照如下。两边都应使用常量，不要写数值：

| 含义 | Gurobi 常量（值） | COPT 常量（值） | 说明 |
|---|---|---|---|
| 未开始求解 | `GRB.LOADED` (1) | `COPT.UNSTARTED` (0) | |
| 最优 | `GRB.OPTIMAL` (2) | `COPT.OPTIMAL` (1) | |
| 不可行 | `GRB.INFEASIBLE` (3) | `COPT.INFEASIBLE` (2) | |
| 不可行或无界 | `GRB.INF_OR_UNBD` (4) | `COPT.INF_OR_UNB` (4) | |
| 无界 | `GRB.UNBOUNDED` (5) | `COPT.UNBOUNDED` (3) | |
| 数值困难 | `GRB.NUMERIC` (12) | `COPT.NUMERICAL` (5) | |
| 达到节点数上限 | `GRB.NODE_LIMIT` (8) | `COPT.NODELIMIT` (6) | |
| 达到时间上限 | `GRB.TIME_LIMIT` (9) | `COPT.TIMEOUT` (8) | |
| 达到迭代上限 | `GRB.ITERATION_LIMIT` (7) | `COPT.ITERLIMIT` (11) | |
| 用户中断 | `GRB.INTERRUPTED` (11) | `COPT.INTERRUPTED` (10) | |
| 解精度不足 | `GRB.SUBOPTIMAL` (13) | `COPT.IMPRECISE` (7) | 含义相近：返回了解，但未满足精度要求 |
| 内部错误导致未完成 | 无 | `COPT.UNFINISHED` (9) | |
| 非凸 / 非线性问题的局部最优、局部不可行 | `GRB.LOCALLY_OPTIMAL` (18) / `GRB.LOCALLY_INFEASIBLE` (19) | `COPT.LOCAL_OPTIMAL` (20) / `COPT.LOCAL_INFEASIBLE` (21) | Gurobi 13 新增；第 4 章 |

常见写法：达到时间上限但已有可行解时，使用该解：

<div class="grid side-by-side" markdown>

```python title="Gurobi"
m.Params.TimeLimit = 60
m.optimize()
if m.Status == GRB.OPTIMAL or (m.Status == GRB.TIME_LIMIT and m.SolCount > 0):
    use(m.ObjVal, m.MIPGap)
```

```python title="COPT"
m.setParam(COPT.Param.TimeLimit, 60)
m.solve()
if m.status == COPT.OPTIMAL or (m.status == COPT.TIMEOUT and m.hassol):
    use(m.objval, m.bestgap)
```

</div>

## 2.6 结果读取：属性对照

单个变量或约束的结果按属性读取，批量读取用模型方法。Gurobi 的 `getAttr` 对应 COPT 的 `getInfo`，COPT 另有 `getValues`、`getDuals` 等不带参数的快捷方法：

<div class="grid side-by-side" markdown>

```python title="Gurobi"
print(x.X, c.Pi, m.ObjVal)
vals = m.getAttr("X", m.getVars())
duals = m.getAttr("Pi", m.getConstrs())
```

```python title="COPT"
print(x.x, c.pi, m.objval)
vals = m.getValues()        # 或 m.getInfo(COPT.Info.Value, m.getVars())
duals = m.getDuals()        # 或 m.getInfo(COPT.Info.Dual, m.getConstrs())
```

</div>

给 MIP 提供初始解的写法不同。Gurobi 给变量的 `Start` 属性赋值；COPT 用 `setMipStart` 设置，最后调用一次 `loadMipStart` 载入：

<div class="grid side-by-side" markdown>

```python title="Gurobi"
x.Start = 1.0
y.Start = 0.0
```

```python title="COPT"
m.setMipStart([x, y], [1.0, 0.0])
m.loadMipStart()
```

</div>

下表 COPT 列按 COPT 文档中的原始大小写给出属性名（模型属性如 `ObjVal`、`BestGap`，变量 / 约束信息项如 `Value`、`RedCost`、`Dual`）。按 COPT 文档，这些名称也可以全小写访问（`m.objval`、`x.value`）；`x.x`、`x.rc`、`c.pi` 以及 `name`、`vtype`、`basis`、`index` 是文档另外给出的简写属性，只有小写形式。**加粗**的行是名字本身不同、必须修改的属性；其余行两边同名，Gurobi 写法可以直接保留。

**变量属性**

| 含义 | Gurobi | COPT | 备注 |
|---|---|---|---|
| **解值** | **`x.X`** | **`x.Value`**（简写 `x.x`） | |
| **变量名** | **`x.VarName`** | **`x.name`** | |
| 下界 / 上界 | `x.LB` / `x.UB` | `x.LB` / `x.UB` | |
| 目标系数 | `x.Obj` | `x.Obj` | |
| **类型** | **`x.VType`** | **`x.vtype`** | |
| **检验数（LP）** | **`x.RC`** | **`x.RedCost`**（简写 `x.rc`） | 仅 LP 或有 LP 解时可用 |
| **基状态** | **`x.VBasis`** | **`x.basis`** | 值的编码不同（见 2.8 节） |
| **MIP 初始解** | **`x.Start = v`** | **`m.setMipStart(x, v)` + `m.loadMipStart()`** | 第 3 章 |
| **解池中第 k 个解** | **`m.Params.SolutionNumber = k; x.PoolNX`** | **`m.getPoolSolution(k, vars)`** | Gurobi 13 起 `Xn` 已弃用，改为 `PoolNX`；第 4 章 |
| 灵敏度分析 | `x.SAObjLow/Up`、`x.SALBLow/Up`、`x.SAUBLow/Up` | `x.SAObjLow/Up`、`x.SALBLow/Up`、`x.SAUBLow/Up` | 同名；COPT 默认不计算，需要时设置 `ReqSensitivity = 1` 开启 |
| **无界方向** | **`x.UnbdRay`** | **`x.PrimalRay`** | 两边都需显式开启：Gurobi `InfUnbdInfo = 1`，COPT `ReqFarkasRay = 1` |
| **IIS 成员** | **`x.IISLB` / `x.IISUB`** | **`x.getLowerIIS()` / `x.getUpperIIS()`** | 需先 `computeIIS()` |
| 索引 | `x.index` | `x.index` | |

**约束属性**

| 含义 | Gurobi | COPT | 备注 |
|---|---|---|---|
| **约束名** | **`c.ConstrName`** | **`c.name`** | |
| **右端项 / 方向** | **`c.RHS` / `c.Sense`** | **`c.LB` / `c.UB`** | 两侧界表示，见 2.3 节 |
| **对偶值（影子价格）** | **`c.Pi`** | **`c.Dual`**（简写 `c.pi`） | 仅 LP 或有 LP 解时可用 |
| 松弛量 | `c.Slack` | `c.Slack` | |
| **基状态** | **`c.CBasis`** | **`c.basis`** | |
| **Farkas 对偶** | **`c.FarkasDual`** | **`c.DualFarkas`** | 两边都需显式开启：Gurobi `InfUnbdInfo = 1`，COPT `ReqFarkasRay = 1` |
| **IIS 成员** | **`c.IISConstr`** | **`c.getLowerIIS()` / `c.getUpperIIS()`** | COPT 区分是下界还是上界参与了 IIS |
| 索引 | `c.index` | `c.index` | |

**模型属性**

| 含义 | Gurobi | COPT | 备注 |
|---|---|---|---|
| 求解状态 | `m.Status` | `m.Status` | |
| 目标值 | `m.ObjVal` | `m.ObjVal` | |
| 目标界 | `m.ObjBound` | `m.ObjBound` | 旧属性 `BestBnd` 在 8.0 文档中已标记为弃用 |
| **相对 gap** | **`m.MIPGap`** | **`m.BestGap`** | |
| **求解时间** | **`m.Runtime`** | **`m.SolvingTime`** | |
| **节点数** | **`m.NodeCount`** | **`m.NodeCnt`** | |
| **单纯形迭代数** | **`m.IterCount`** | **`m.SimplexIter`** | |
| **内点法迭代数** | **`m.BarIterCount`** | **`m.BarrierIter`** | |
| **解池中的解个数** | **`m.SolCount`** | **`m.PoolSols`** | |
| **变量 / 约束 / 非零元个数** | **`m.NumVars` / `m.NumConstrs` / `m.NumNZs`** | **`m.Cols` / `m.Rows` / `m.Elems`** | |
| **整数 / 二元变量个数** | **`m.NumIntVars` / `m.NumBinVars`** | **`m.Ints` / `m.Bins`** | |
| **二次约束 / SOS 个数** | **`m.NumQConstrs` / `m.NumSOS`** | **`m.QConstrs` / `m.Soss`** | |
| 是否 MIP | `m.IsMIP` | `m.IsMIP` | |
| **是否有二次目标** | **`m.IsQP`** | **`m.HasQObj`** | |
| **目标方向 / 常数项** | **`m.ModelSense` / `m.ObjCon`** | **`m.ObjSense` / `m.ObjConst`** | |
| **是否有解** | **`m.SolCount > 0`** | **`m.HasSol`** | |
| **系数范围** | **`m.MaxCoeff/MinCoeff`、`m.MaxRHS/MinRHS`、`m.MaxObjCoeff/MinObjCoeff`** | **`m.MaxElem/MinElem`、`m.MaxRHS/MinRHS`、`m.MaxCost/MinCost`** | |

**批量读取**

| Gurobi | COPT |
|---|---|
| `m.getAttr("X", m.getVars())` | `m.getValues()` 或 `m.getInfo(COPT.Info.Value, vars)` |
| `m.getAttr("Pi", m.getConstrs())` | `m.getDuals()` 或 `m.getInfo(COPT.Info.Dual, constrs)` |
| `m.getAttr("RC", m.getVars())` | `m.getRedcosts()` 或 `m.getInfo(COPT.Info.RedCost, vars)` |
| `m.getAttr("Slack", m.getConstrs())` | `m.getSlacks()` 或 `m.getInfo(COPT.Info.Slack, constrs)` |
| — | `m.getLpSolution()`：一次返回 `(values, slacks, duals, redcosts)` |

## 2.7 参数

参数名大多相同，设置方式有三种，两边都支持属性式、常量式和字符串式：

<div class="grid side-by-side" markdown>

```python title="Gurobi"
m.Params.TimeLimit = 60
m.setParam(GRB.Param.MIPGap, 1e-3)
m.setParam("Threads", 4)
```

```python title="COPT"
m.Param.TimeLimit = 60                # 也可写作 m.param.timelimit = 60
m.setParam(COPT.Param.RelGap, 1e-3)   # MIPGap 在 COPT 中叫 RelGap
m.setParam("Threads", 4)
```

</div>

**设置方式**

| Gurobi | COPT | 说明 |
|---|---|---|
| `m.Params.TimeLimit = 60` | `m.Param.TimeLimit = 60` | 属性式（Gurobi 是 `Params`，COPT 是 `Param`；COPT 团队的对照表中写作 `m.param.timelimit`，同样有效） |
| `m.setParam(GRB.Param.TimeLimit, 60)` | `m.setParam(COPT.Param.TimeLimit, 60)` | 常量式，两边文档的推荐写法 |
| `m.setParam("TimeLimit", 60)` | `m.setParam("TimeLimit", 60)` | 两边写法相同。Gurobi 文档明确支持字符串形式；COPT 侧为实测结果（`COPT.Param.TimeLimit` 的值即字符串 `"TimeLimit"`） |
| `m.Params.TimeLimit`（读取） | `m.Param.TimeLimit` 或 `m.getParam(COPT.Param.TimeLimit)` | |
| `m.getParamInfo("TimeLimit")` | `m.getParamInfo(COPT.Param.TimeLimit)` | 同名，但返回的元组结构不同：Gurobi 为 (名称, 类型, 当前值, 最小值, 最大值, 默认值)；COPT 为 (名称, 当前值, 默认值, 最小值, 最大值)（依据 coptpy 方法的文档字符串） |
| `m.resetParams()` | `m.resetParam()` | |
| `m.read("x.prm")` / `m.write("x.prm")` | `m.read("x.par")` / `m.write("x.par")` | 参数文件后缀不同 |

**常用参数对照**

"语义"列标注两边的取值和含义是否一致；标"不同"的参数不能直接照搬数值。

| 用途 | Gurobi | COPT | 语义 |
|---|---|---|---|
| 时间上限（秒） | `TimeLimit` | `TimeLimit` | 一致 |
| 找到可行解后的时间上限 | 无 | `SolTimeLimit` | COPT 特有 |
| 相对 MIP gap | `MIPGap`（默认 1e-4） | `RelGap`（默认 1e-4） | 一致 |
| 绝对 MIP gap | `MIPGapAbs`（默认 1e-10） | `AbsGap`（默认 1e-6） | 含义一致，**默认值不同** |
| 原始可行容差 | `FeasibilityTol`（1e-6） | `FeasTol`（1e-6） | 一致 |
| 对偶可行容差 | `OptimalityTol`（1e-6） | `DualTol`（1e-6） | 一致 |
| 整数容差 | `IntFeasTol`（1e-5） | `IntTol`（1e-6） | 含义一致，**默认值不同** |
| 线程数 | `Threads`（0 = 自动） | `Threads`（-1 = 自动） | "自动"的取值不同 |
| LP 算法 | `Method` | `LpMethod` | **取值不同**：Gurobi 0 原始单纯形 / 1 对偶单纯形 / 2 内点法 / 3 并发 / 4 确定性并发 / 6 PDHG（一阶方法，13.0 新增）；COPT 1 对偶单纯形 / 2 内点法 / 3 交叉 / 4 并发 / 5 自动选择 / 6 一阶方法 (PDLP)。两边 -1 均为自动 |
| 交叉（crossover） | `Crossover` | `Crossover` | 含义一致，取值范围不同 |
| 预处理 | `Presolve`（-1/0/1/2） | `Presolve`（-1/0/1/2/3/4） | COPT 多两个更激进的级别 |
| 缩放 | `ScaleFlag` | `Scaling` | |
| 割平面强度 | `Cuts` | `CutLevel`（-1/0/1/2/3） | 含义相近 |
| 启发式强度 | `Heuristics`（占用时间比例，0–1） | `HeurLevel`（级别 -1/0/1/2/3） | **语义不同** |
| 节点数上限 | `NodeLimit` | `NodeLimit` | 一致 |
| 内点法迭代上限 | `BarIterLimit` | `BarIterLimit` | 一致 |
| 内存上限 | `MemLimit` / `SoftMemLimit` | `MemLimit` | **单位不同**：Gurobi 以 GB 计，COPT 以 MB 计 |
| 懒约束开关 | `LazyConstraints` | `LazyConstraints` | 一致 |
| 非凸处理 | `NonConvex` | `NonConvex` | 含义相近，取值不同（第 4 章） |
| IIS 算法 | `IISMethod` | `IISMethod` | 取值不同 |
| 日志开关 | `OutputFlag` | `Logging` | |
| 日志到控制台 | `LogToConsole` | `LogToConsole` | 一致 |
| 日志文件 | `LogFile` | 无参数，用 `m.setLogFile("x.log")` | |
| 初始解处理 | `StartNodeLimit` | `MipStartMode` / `MipStartNodeLimit` | 第 3 章 |
| 调参器时间 | `TuneTimeLimit` | `TuneTimeLimit` | 一致 |
| 灵敏度分析 | 自动可用 | `ReqSensitivity = 1` | COPT 默认关闭，需要时开启 |
| Farkas 证书 / 无界方向 | `InfUnbdInfo = 1` | `ReqFarkasRay = 1` | |

!!! tip "从 COPT 默认参数开始"

    COPT 的算法类参数（`LpMethod`、`Presolve`、`CutLevel`、`HeurLevel`、`Scaling` 等）默认值为 -1，表示由求解器根据模型特征自动选择。在 Gurobi 上调好的参数组合针对的是 Gurobi 的算法实现，直接照搬到 COPT 通常没有意义，也可能降低性能。建议迁移时只保留业务上必需的限制（时间上限、gap、线程数），先用默认参数运行基准测试；性能参数的调整见第 6 章，可以使用 COPT 的调参器 `m.tune()`。

## 2.8 常量

常量名称基本一致，需要注意的是 `INFINITY` 的数值和基状态的编码不同：

| 含义 | Gurobi | COPT | 说明 |
|---|---|---|---|
| 连续 / 二元 / 整数 | `GRB.CONTINUOUS` (`'C'`) / `GRB.BINARY` (`'B'`) / `GRB.INTEGER` (`'I'`) | `COPT.CONTINUOUS` / `COPT.BINARY` / `COPT.INTEGER` | 同名；COPT 文档只给常量名不给字面值，请使用常量 |
| 最小化 / 最大化 | `GRB.MINIMIZE` (1) / `GRB.MAXIMIZE` (-1) | `COPT.MINIMIZE` / `COPT.MAXIMIZE` | 同名；请使用常量 |
| 无穷大 | `GRB.INFINITY` (1e100) | `COPT.INFINITY` (1e30) | **值不同**，见 2.2 节 |
| 约束方向 | `GRB.LESS_EQUAL` (`'<'`) / `GRB.GREATER_EQUAL` (`'>'`) / `GRB.EQUAL` (`'='`) | `COPT.LESS_EQUAL` / `COPT.GREATER_EQUAL` / `COPT.EQUAL` | 同名；请使用常量 |
| SOS 类型 | `GRB.SOS_TYPE1` / `GRB.SOS_TYPE2` | `COPT.SOS_TYPE1` / `COPT.SOS_TYPE2` | |
| 基状态 | `GRB.BASIC` (0) / `NONBASIC_LOWER` (-1) / `NONBASIC_UPPER` (-2) / `SUPERBASIC` (-3) | `COPT.BASIS_LOWER` (0) / `BASIS_BASIC` (1) / `BASIS_UPPER` (2) / `BASIS_SUPERBASIC` (3) / `BASIS_FIXED` (4) | **编码完全不同** |
| 参数 / 属性 / 信息 命名空间 | `GRB.Param.*` / `GRB.Attr.*` | `COPT.Param.*` / `COPT.Attr.*`（模型级）/ `COPT.Info.*`（变量与约束级） | COPT 把模型属性和变量/约束信息分成两个命名空间 |
| 回调触发点 | `GRB.Callback.MIPSOL` 等 | `COPT.CBCONTEXT_MIPSOL` 等 | 第 3 章 |

## 2.9 文件读写

两边的 `m.write(filename)` 都按后缀判断格式。读取时有区别：Gurobi 的模型文件要用模块级 `gp.read()`，`m.read()` 只读基、初始解、参数等辅助文件；COPT 统一用 `m.read()`，模型与辅助文件都按后缀识别。

| 内容 | Gurobi 后缀 | COPT 后缀 | 说明 |
|---|---|---|---|
| 模型（文本） | `.lp`、`.mps`、`.rew`、`.rlp` | `.lp`、`.mps` | |
| 模型（二进制） | 无 | `.bin` | COPT 特有 |
| 锥规划模型 | 无 | `.cbf` | |
| 解 | `.sol`、`.json` | `.sol`；JSON 格式通过 `writeJsonSol()` / `readJsonSol()` | |
| MIP 初始解 | `.mst` | `.mst` | |
| 基 | `.bas` | `.bas` | |
| 分支优先级 | `.ord`（仅读取） | `.ord` | |
| 参数 | `.prm` | `.par` | **后缀不同** |
| IIS | `.ilp` | `.iis`（通过 `writeIIS()` 输出） | 需先 `computeIIS()` |
| 可行性松弛问题 | 无 | `.relax`（通过 `writeRelax()` 输出） | 需先 `feasRelax` |
| 对偶问题 | `.dua`、`.dlp` | 写 `.lp` / `.mps` / `.bin` 时把参数 `WriteDualProb` 设为 1 | |

除了按后缀自动判断的 `write`/`read`，COPT 还提供明确格式的方法（`writeLp`、`writeMps`、`writeBin`、`writeSol`、`writeMst`、`writeBasis`、`writeParam`、`writeIIS`、`writeRelax`、`readMps`、`readLp`、`readSol`、`readMst`、`readBasis`、`readParam` 等），行为相同。

## 2.10 本章未覆盖的内容

以下功能两边都提供，但接口设计差异较大，将在后续章节单独说明：

- **MIP 初始解**：`x.Start` → `setMipStart` + `loadMipStart`（第 3 章）
- **回调**：Gurobi 的函数式回调 `optimize(callback)` → COPT 继承 `CallbackBase` 类（第 3 章）
- **求解后修改模型再求解**：两侧界约束、参数保留、热启动行为（第 3 章）
- **矩阵接口**、**多目标**、**解池**、**IIS 与可行性松弛**、**调参器**、**锥约束与非凸/非线性**（第 4 章）


*第 3 章及后续章节陆续发布。如果你在迁移中遇到本文未覆盖的用法，欢迎在 [GitHub 仓库](https://github.com/redpanda997/gurobi-to-copt/issues) 提 issue，高频问题会补进后续章节。*
