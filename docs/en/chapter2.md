# Chapter 2 — Core mapping tables

This chapter follows the modeling workflow: environment & model → variables → constraints → objective & expressions → solving & status → reading results → parameters → constants → file I/O. Each section first shows the difference in a short piece of code, then gives the full mapping table; the tables stand on their own as a quick reference. The code snippets continue the conventions of Chapter 1: `gp`, `GRB`, `cp` and `COPT` are imported, `m` is the model, `x`, `y`, `z` are variables and `c` is a constraint.

The following three rules summarize the main differences between the two APIs:

1. **Method names are mostly the same.** `addVar`, `addVars`, `addConstr`, `addConstrs`, `setObjective`, `getVars`, `getConstrs`, `computeIIS`, `write`, `read`, `remove`, `reset`, `tune` and many more share name and meaning on both sides. The main exception is `optimize()` → `solve()`.
2. **Attributes can be accessed in original case or all lowercase, but some attribute names differ.** The COPT documentation states that attribute names may be written in their original case (`m.ObjVal`) or in lowercase (`m.objval`), so attributes that share a name with Gurobi can stay. Attributes whose names differ must be edited; see 2.6.
3. **Status codes have different numeric values.** `GRB.OPTIMAL == 2` whereas `COPT.OPTIMAL == 1`. Code that compares against literal numbers instead of constants fails after migration.

## 2.1 Environment and model lifecycle

A Gurobi model can be created directly; the environment object is optional. A COPT model is always created from an environment object:

<div class="grid side-by-side" markdown>

```python title="Gurobi"
env = gp.Env()                     # optional; Model() creates a default environment
m = gp.Model("demo", env=env)
```

```python title="COPT"
env = cp.Envr()
m = env.createModel("demo")
```

</div>

With a floating or cluster license, COPT specifies the license server through `EnvrConfig` before the environment is created:

```python
cfg = cp.EnvrConfig()
cfg.set(COPT.CLIENT_CLUSTER, "192.168.9.9")   # COPT.CLIENT_FLOATING for a floating license
env = cp.Envr(cfg)
m = env.createModel("demo")
```

| Operation | Gurobi | COPT | Notes |
|---|---|---|---|
| Import | `import gurobipy as gp` <br> `from gurobipy import GRB` | `import coptpy as cp` <br> `from coptpy import COPT` | |
| Create environment | `env = gp.Env()` (optional — `Model()` creates a default environment implicitly) | `env = cp.Envr()` | COPT requires an explicit environment; models are created from it |
| Create model | `m = gp.Model("name", env=env)` | `m = env.createModel("name")` | Models are created from the environment |
| Model from file | `m = gp.read("model.mps")` | `m = env.createModel()` <br> `m.read("model.mps")` | COPT reads files through the model object |
| Copy a model | `m2 = m.copy()` | `m2 = m.clone()` | |
| Release resources | `m.dispose()` / `env.dispose()` <br> or `with gp.Env() as env, gp.Model(env=env) as m:` | No explicit release needed; objects are freed automatically by Python's garbage collector | COPT has no `dispose()` and the documentation defines no `with` usage; objects are released when they go out of scope. `env.close()` only disconnects from a floating / cluster license server |
| Synchronize changes | `m.update()` | Not needed while modeling | See note below |

!!! tip "COPT does not need `update()`"

    Gurobi uses lazy updates: adding variables, changing bounds and removing items are queued until `m.update()`, `optimize()` or `write()` is called. The Gurobi documentation notes that a forgotten call does not raise an error; queries return the values from the last update. COPT's official examples have no such step: add variables and constraints, set parameters, then solve and query directly. coptpy provides `Model.update()`, defined in the documentation as "update the model, including numerical ranges, removed variables and constraints"; it is only needed to refresh coefficient statistics after removing items. During migration the `m.update()` calls can be deleted.

!!! tip "Parameters are set on the model only"

    Gurobi parameters can be set on an `Env` or on a `Model`; a model copies the environment's parameters when it is created, and later changes to the environment do not affect that model. In COPT all solver parameters are set on the `Model`; `Envr` only manages the license and resources. To share one parameter set across several models, read a parameter file with `m.read("settings.par")` or set the parameters in a helper function.

## 2.2 Variables

Single variables are created the same way on both sides. For bulk creation, Gurobi's `name` argument is called `nameprefix` in COPT; for bulk attribute reads, Gurobi's `getAttr` corresponds to COPT's `getInfo`. Both accept a list or a `tupledict` and return a container of the same type:

<div class="grid side-by-side" markdown>

```python title="Gurobi"
x = m.addVars(3, 2, vtype=GRB.BINARY, name="x")
m.optimize()
vals = m.getAttr("X", x)                 # tupledict with the same keys as x
```

```python title="COPT"
x = m.addVars(3, 2, vtype=COPT.BINARY, nameprefix="x")
m.solve()
vals = m.getInfo(COPT.Info.Value, x)     # tupledict with the same keys as x
```

</div>

| Operation | Gurobi | COPT | Notes |
|---|---|---|---|
| Single variable | `m.addVar(lb=0, ub=GRB.INFINITY, obj=0, vtype=GRB.CONTINUOUS, name="x")` | `m.addVar(lb=0, ub=COPT.INFINITY, obj=0, vtype=COPT.CONTINUOUS, name="x")` | Identical signature |
| Bulk variables | `m.addVars(I, J, vtype=GRB.BINARY, name="x")` | `m.addVars(I, J, vtype=COPT.BINARY, nameprefix="x")` | `name` → `nameprefix`; name format `x[i,j]` → `x(i,j)` |
| Matrix variable | `m.addMVar(shape, lb=..., ub=..., name=...)` | `m.addMVar(shape, lb=..., ub=..., nameprefix=...)` | Chapter 4 |
| Look up by name | `m.getVarByName("x")` | `m.getVarByName("x")` | |
| All variables | `m.getVars()` (returns a list) | `m.getVars()` (returns a `VarArray`, iterable with a plain for loop; `.getAll()` converts to a list, `.getSize()` gives the count) | |
| Number of variables | `m.NumVars` | `m.cols` | |
| Delete a variable | `m.remove(x)` | `m.remove(x)` | |
| Change type | `x.VType = GRB.INTEGER` | `x.vtype = COPT.INTEGER` or `m.setVarType(x, COPT.INTEGER)` | |
| Change bounds | `x.LB = 0; x.UB = 5` | `x.LB = 0; x.UB = 5` | Same name |
| Bulk read / write attributes | `m.getAttr("LB", vars)` / `m.setAttr("LB", vars, vals)` | `m.getInfo(COPT.Info.LB, vars)` / `m.setInfo(COPT.Info.LB, vars, vals)` | Gurobi uses attribute-name strings; COPT uses `COPT.Info.*` constants |

**Bounds and infinity**: `GRB.INFINITY` is `1e100`, `COPT.INFINITY` is `1e30`. According to the COPT documentation, a bound is treated as infinite once its absolute value reaches `1e30`, so a `1e100` left in old code is also recognized as unbounded by COPT. The reverse does not hold: a `1e30` read from COPT is a finite value to Gurobi. Use the `COPT.INFINITY` constant throughout.

**The variable `tupledict`**: `addVars` returns a `tupledict` on both sides, supporting `.sum(...)`, `.prod(coeff_dict)` and the usual dict methods with the same behavior.

## 2.3 Constraints

Constraints written with comparison operators, and bulk creation with `addConstrs` and a generator, are the same on both sides. The differences are in the internal representation of range constraints and in the attributes used to read the right-hand side.

A range constraint `lb ≤ expr ≤ ub` can be written as `expr == [lb, ub]` on both sides, and both have a dedicated method:

<div class="grid side-by-side" markdown>

```python title="Gurobi"
m.addRange(x + y, 1, 5, name="r1")
m.addConstr(x + y == [1, 5], name="r2")   # equivalent to the line above
```

```python title="COPT"
m.addBoundConstr(x + y, 1, 5, name="r1")
m.addConstr(x + y == [1, 5], name="r2")   # equivalent to the line above
```

</div>

Gurobi stores a range constraint as an equality with an auxiliary variable, so the variable count of the model increases by one; COPT stores it directly as `lb ≤ expr ≤ ub` without adding a variable.

To read the right-hand side of a constraint, Gurobi uses `Sense` and `RHS`, COPT uses `lb` and `ub`:

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

| Operation | Gurobi | COPT | Notes |
|---|---|---|---|
| Linear constraint (expression form) | `m.addConstr(x + y <= 10, name="c")` | `m.addConstr(x + y <= 10, name="c")` | Identical |
| Linear constraint (explicit form) | `m.addLConstr(x + y, GRB.LESS_EQUAL, 10, name="c")` | `m.addConstr(x + y, COPT.LESS_EQUAL, 10, name="c")` | COPT's `addConstr` accepts both forms |
| Bulk constraints | `m.addConstrs((expr_i <= b_i for i in I), name="c")` | `m.addConstrs((expr_i <= b_i for i in I), nameprefix="c")` | `name` → `nameprefix` |
| Range constraint | `m.addRange(expr, lb, ub, name="r")` | `m.addBoundConstr(expr, lb, ub, name="r")` | See the "two-sided" note below |
| Quadratic constraint | `m.addQConstr(...)` | `m.addQConstr(...)` | Identical |
| SOS constraint | `m.addSOS(GRB.SOS_TYPE1, vars, weights)` | `m.addSOS(COPT.SOS_TYPE1, vars, weights)` | Identical |
| Indicator constraint | `m.addGenConstrIndicator(z, True, x + y <= 5)` | `m.addGenConstrIndicator(z, True, x + y <= 5)` | Identical (COPT has an extra optional `type` argument, default if-then) |
| Other general constraints | `addGenConstrAbs / Max / Min / And / Or / PWL` | Same names | Identical |
| Nonlinear constraint | `m.addGenConstrNL(...)` with `nlfunc` | `m.addNlConstr(...)` with `cp.nl` | Chapter 4 |
| Matrix constraint | `m.addMConstr(A, x, sense, b)` | `m.addMConstr(A, x, sense, b)` | Chapter 4 |
| Look up by name | `m.getConstrByName("c")` | `m.getConstrByName("c")` | |
| All constraints | `m.getConstrs()` | `m.getConstrs()` (returns a `ConstrArray`) | |
| Number of constraints | `m.NumConstrs` | `m.rows` | |
| Delete a constraint | `m.remove(c)` | `m.remove(c)` | |
| Change a coefficient | `m.chgCoeff(c, x, 2.0)` | `m.setCoeff(c, x, 2.0)` | |
| Read coefficient / row / column | `m.getCoeff(c, x)` / `m.getRow(c)` / `m.getCol(x)` | Same names | |
| Read the coefficient matrix | `m.getA()` | `m.getA()` | Both return a SciPy sparse matrix |

!!! tip "COPT constraints are two-sided"

    A Gurobi linear constraint is described by a `Sense` (`<`/`>`/`=`) and an `RHS`; range constraints require `addRange`, which Gurobi implements internally by adding an auxiliary variable. COPT represents every linear constraint as `lb ≤ expr ≤ ub`, described by `c.lb` and `c.ub`: `x + y <= 10` is stored as `lb = -COPT.INFINITY, ub = 10`; `x + y >= 1` as `lb = 1, ub = +COPT.INFINITY`; `x + y == 3` as `lb = ub = 3`. A range constraint is written directly with `addBoundConstr`, without an auxiliary variable; `lb` and `ub` can be changed separately after solving. The corresponding edits during migration:

    - Code that reads `c.RHS` reads `c.ub` (for ≤) or `c.lb` (for ≥) instead;
    - Code that changes a right-hand side after solving assigns to `c.lb` / `c.ub`;
    - `addRange` becomes `addBoundConstr`.

## 2.4 Objective and expressions

`setObjective` is used the same way, and expressions built with operators and `quicksum` need no changes. When terms are added to a `LinExpr` by method calls, the argument order differs: Gurobi's `addTerms` takes the coefficient first, then the variable; COPT's `addTerm`/`addTerms` take the variable first, then the coefficient:

<div class="grid side-by-side" markdown>

```python title="Gurobi"
expr = gp.LinExpr(1.0)                    # constant term 1.0
expr.addTerms(2.0, x)                     # coefficient first, variable second
expr.addTerms([3.0, 4.0], [y, z])
m.setObjective(expr, GRB.MINIMIZE)
```

```python title="COPT"
expr = cp.LinExpr(1.0)
expr.addTerm(x, 2.0)                      # variable first, coefficient second
expr.addTerms([y, z], [3.0, 4.0])
m.setObjective(expr, COPT.MINIMIZE)
```

</div>

| Operation | Gurobi | COPT | Notes |
|---|---|---|---|
| Set the objective | `m.setObjective(expr, GRB.MAXIMIZE)` | `m.setObjective(expr, COPT.MAXIMIZE)` | Identical |
| **Change only the sense** | **`m.ModelSense = GRB.MINIMIZE`** | **`m.ObjSense = COPT.MINIMIZE`** or `m.setObjSense(COPT.MINIMIZE)` | |
| **Objective constant** | **`m.ObjCon = 5`** | **`m.ObjConst = 5`** or `m.setObjConst(5)` | |
| Read the objective expression | `m.getObjective()` | `m.getObjective()` | |
| Objective coefficient of a variable | `x.Obj` | `x.Obj` | Same name |
| Multiple objectives | `m.setObjectiveN(expr, index, priority, weight, ...)` | `m.setObjectiveN(index, expr, sense, priority, weight, ...)` | **Different argument order**, Chapter 4 |
| Matrix-form objective | `m.setMObjective(...)` | `m.setMObjective(...)` | Chapter 4 |
| Add terms to a linear expression | `expr.addTerms(coeffs, vars)` | `expr.addTerm(var, coeff)` / `expr.addTerms(vars, coeffs)` | **Reversed argument order**, see above |
| Constant term of an expression | `gp.LinExpr(1.0)` / `expr.getConstant()` | `cp.LinExpr(1.0)` / `expr.getConstant()` | Identical |

## 2.5 Solving and status codes

The solve method has a different name (`optimize()` vs `solve()`), the status constants share names but not values, and the attribute that tells whether a usable solution exists differs:

| Operation | Gurobi | COPT |
|---|---|---|
| Solve | `m.optimize()` | `m.solve()` |
| Solve the LP relaxation / an LP only | `m.relax().optimize()` | `m.solveLP()` (ignores integrality and solves the LP) |
| Interrupt | `m.terminate()` | `m.interrupt()` |
| Clear the solution | `m.reset()` / `m.reset(1)` | `m.reset()` / `m.resetAll()` (the latter also clears additional information such as MIP starts and the IIS) |
| Read the status | `m.Status` | `m.Status` |
| Is a solution available? | `m.SolCount > 0` | `m.HasSol` (the older `HasMipSol` / `HasLpSol` are marked deprecated in the 8.0 documentation) |

Status code mapping. Use constants on both sides; do not write the numeric values:

| Meaning | Gurobi constant (value) | COPT constant (value) | Notes |
|---|---|---|---|
| Not yet solved | `GRB.LOADED` (1) | `COPT.UNSTARTED` (0) | |
| Optimal | `GRB.OPTIMAL` (2) | `COPT.OPTIMAL` (1) | |
| Infeasible | `GRB.INFEASIBLE` (3) | `COPT.INFEASIBLE` (2) | |
| Infeasible or unbounded | `GRB.INF_OR_UNBD` (4) | `COPT.INF_OR_UNB` (4) | |
| Unbounded | `GRB.UNBOUNDED` (5) | `COPT.UNBOUNDED` (3) | |
| Numerical trouble | `GRB.NUMERIC` (12) | `COPT.NUMERICAL` (5) | |
| Node limit reached | `GRB.NODE_LIMIT` (8) | `COPT.NODELIMIT` (6) | |
| Time limit reached | `GRB.TIME_LIMIT` (9) | `COPT.TIMEOUT` (8) | |
| Iteration limit reached | `GRB.ITERATION_LIMIT` (7) | `COPT.ITERLIMIT` (11) | |
| Interrupted by user | `GRB.INTERRUPTED` (11) | `COPT.INTERRUPTED` (10) | |
| Solution not to required accuracy | `GRB.SUBOPTIMAL` (13) | `COPT.IMPRECISE` (7) | Similar meaning: a solution is returned but tolerances were not met |
| Unfinished due to internal error | None | `COPT.UNFINISHED` (9) | |
| Local optimum / local infeasibility of a nonconvex or nonlinear problem | `GRB.LOCALLY_OPTIMAL` (18) / `GRB.LOCALLY_INFEASIBLE` (19) | `COPT.LOCAL_OPTIMAL` (20) / `COPT.LOCAL_INFEASIBLE` (21) | New in Gurobi 13; Chapter 4 |

A common pattern: the time limit is reached but a feasible solution exists, so the solution is used:

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

## 2.6 Reading results: attribute mapping

Results of a single variable or constraint are read as attributes; bulk reads go through model methods. Gurobi's `getAttr` corresponds to COPT's `getInfo`, and COPT also has argument-free shortcuts such as `getValues` and `getDuals`:

<div class="grid side-by-side" markdown>

```python title="Gurobi"
print(x.X, c.Pi, m.ObjVal)
vals = m.getAttr("X", m.getVars())
duals = m.getAttr("Pi", m.getConstrs())
```

```python title="COPT"
print(x.x, c.pi, m.objval)
vals = m.getValues()        # or m.getInfo(COPT.Info.Value, m.getVars())
duals = m.getDuals()        # or m.getInfo(COPT.Info.Dual, m.getConstrs())
```

</div>

MIP starts are given differently. Gurobi assigns the `Start` attribute of each variable; COPT sets them with `setMipStart` and loads them once with `loadMipStart`:

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

The COPT column lists attribute names in the original case used by the COPT documentation (model attributes such as `ObjVal` and `BestGap`, variable / constraint information items such as `Value`, `RedCost` and `Dual`). Per the COPT documentation these names can also be accessed in all lowercase (`m.objval`, `x.value`); `x.x`, `x.rc`, `c.pi` and `name`, `vtype`, `basis`, `index` are additional shorthand attributes from the documentation that exist only in lowercase. **Bold** rows are attributes whose names actually differ and must be edited; the other rows share the same name on both sides, so the Gurobi spelling can stay.

**Variable attributes**

| Meaning | Gurobi | COPT | Notes |
|---|---|---|---|
| **Solution value** | **`x.X`** | **`x.Value`** (shorthand `x.x`) | |
| **Name** | **`x.VarName`** | **`x.name`** | |
| Lower / upper bound | `x.LB` / `x.UB` | `x.LB` / `x.UB` | |
| Objective coefficient | `x.Obj` | `x.Obj` | |
| **Type** | **`x.VType`** | **`x.vtype`** | |
| **Reduced cost (LP)** | **`x.RC`** | **`x.RedCost`** (shorthand `x.rc`) | Available for LPs or when an LP solution exists |
| **Basis status** | **`x.VBasis`** | **`x.basis`** | Different encoding (see 2.8) |
| **MIP start** | **`x.Start = v`** | **`m.setMipStart(x, v)` + `m.loadMipStart()`** | Chapter 3 |
| **k-th solution from the pool** | **`m.Params.SolutionNumber = k; x.PoolNX`** | **`m.getPoolSolution(k, vars)`** | `Xn` is deprecated since Gurobi 13 in favor of `PoolNX`; Chapter 4 |
| Sensitivity analysis | `x.SAObjLow/Up`, `x.SALBLow/Up`, `x.SAUBLow/Up` | `x.SAObjLow/Up`, `x.SALBLow/Up`, `x.SAUBLow/Up` | Same names; not computed by default in COPT, set `ReqSensitivity = 1` to enable |
| **Unbounded ray** | **`x.UnbdRay`** | **`x.PrimalRay`** | Must be enabled on both sides: Gurobi `InfUnbdInfo = 1`, COPT `ReqFarkasRay = 1` |
| **IIS membership** | **`x.IISLB` / `x.IISUB`** | **`x.getLowerIIS()` / `x.getUpperIIS()`** | After `computeIIS()` |
| Index | `x.index` | `x.index` | |

**Constraint attributes**

| Meaning | Gurobi | COPT | Notes |
|---|---|---|---|
| **Name** | **`c.ConstrName`** | **`c.name`** | |
| **Right-hand side / sense** | **`c.RHS` / `c.Sense`** | **`c.LB` / `c.UB`** | Two-sided representation, see 2.3 |
| **Dual value (shadow price)** | **`c.Pi`** | **`c.Dual`** (shorthand `c.pi`) | Available for LPs or when an LP solution exists |
| Slack | `c.Slack` | `c.Slack` | |
| **Basis status** | **`c.CBasis`** | **`c.basis`** | |
| **Farkas dual** | **`c.FarkasDual`** | **`c.DualFarkas`** | Must be enabled on both sides: Gurobi `InfUnbdInfo = 1`, COPT `ReqFarkasRay = 1` |
| **IIS membership** | **`c.IISConstr`** | **`c.getLowerIIS()` / `c.getUpperIIS()`** | COPT distinguishes whether the lower or the upper bound is in the IIS |
| Index | `c.index` | `c.index` | |

**Model attributes**

| Meaning | Gurobi | COPT | Notes |
|---|---|---|---|
| Solve status | `m.Status` | `m.Status` | |
| Objective value | `m.ObjVal` | `m.ObjVal` | |
| Objective bound | `m.ObjBound` | `m.ObjBound` | The older `BestBnd` is marked deprecated in the 8.0 documentation |
| **Relative gap** | **`m.MIPGap`** | **`m.BestGap`** | |
| **Solve time** | **`m.Runtime`** | **`m.SolvingTime`** | |
| **Node count** | **`m.NodeCount`** | **`m.NodeCnt`** | |
| **Simplex iterations** | **`m.IterCount`** | **`m.SimplexIter`** | |
| **Barrier iterations** | **`m.BarIterCount`** | **`m.BarrierIter`** | |
| **Number of pool solutions** | **`m.SolCount`** | **`m.PoolSols`** | |
| **Number of variables / constraints / nonzeros** | **`m.NumVars` / `m.NumConstrs` / `m.NumNZs`** | **`m.Cols` / `m.Rows` / `m.Elems`** | |
| **Number of integer / binary variables** | **`m.NumIntVars` / `m.NumBinVars`** | **`m.Ints` / `m.Bins`** | |
| **Number of quadratic constraints / SOS** | **`m.NumQConstrs` / `m.NumSOS`** | **`m.QConstrs` / `m.Soss`** | |
| Is a MIP | `m.IsMIP` | `m.IsMIP` | |
| **Has a quadratic objective** | **`m.IsQP`** | **`m.HasQObj`** | |
| **Objective sense / constant** | **`m.ModelSense` / `m.ObjCon`** | **`m.ObjSense` / `m.ObjConst`** | |
| **Solution available** | **`m.SolCount > 0`** | **`m.HasSol`** | |
| **Coefficient ranges** | **`m.MaxCoeff/MinCoeff`, `m.MaxRHS/MinRHS`, `m.MaxObjCoeff/MinObjCoeff`** | **`m.MaxElem/MinElem`, `m.MaxRHS/MinRHS`, `m.MaxCost/MinCost`** | |

**Bulk reads**

| Gurobi | COPT |
|---|---|
| `m.getAttr("X", m.getVars())` | `m.getValues()` or `m.getInfo(COPT.Info.Value, vars)` |
| `m.getAttr("Pi", m.getConstrs())` | `m.getDuals()` or `m.getInfo(COPT.Info.Dual, constrs)` |
| `m.getAttr("RC", m.getVars())` | `m.getRedcosts()` or `m.getInfo(COPT.Info.RedCost, vars)` |
| `m.getAttr("Slack", m.getConstrs())` | `m.getSlacks()` or `m.getInfo(COPT.Info.Slack, constrs)` |
| — | `m.getLpSolution()`: returns `(values, slacks, duals, redcosts)` in one call |

## 2.7 Parameters

Most parameter names are the same. Both sides support attribute style, constant style and string style:

<div class="grid side-by-side" markdown>

```python title="Gurobi"
m.Params.TimeLimit = 60
m.setParam(GRB.Param.MIPGap, 1e-3)
m.setParam("Threads", 4)
```

```python title="COPT"
m.Param.TimeLimit = 60                # m.param.timelimit = 60 also works
m.setParam(COPT.Param.RelGap, 1e-3)   # MIPGap is called RelGap in COPT
m.setParam("Threads", 4)
```

</div>

**How to set them**

| Gurobi | COPT | Notes |
|---|---|---|
| `m.Params.TimeLimit = 60` | `m.Param.TimeLimit = 60` | Attribute style (`Params` in Gurobi, `Param` in COPT; the COPT team's comparison table writes `m.param.timelimit`, which also works) |
| `m.setParam(GRB.Param.TimeLimit, 60)` | `m.setParam(COPT.Param.TimeLimit, 60)` | Constant style — the form recommended by both documentations |
| `m.setParam("TimeLimit", 60)` | `m.setParam("TimeLimit", 60)` | Identical on both sides. Explicitly documented for Gurobi; observed for COPT (the constant `COPT.Param.TimeLimit` evaluates to the string `"TimeLimit"`) |
| `m.Params.TimeLimit` (read) | `m.Param.TimeLimit` or `m.getParam(COPT.Param.TimeLimit)` | |
| `m.getParamInfo("TimeLimit")` | `m.getParamInfo(COPT.Param.TimeLimit)` | Same name, different tuple layout: Gurobi returns (name, type, current, min, max, default); COPT returns (name, current, default, min, max) (per the coptpy method docstring) |
| `m.resetParams()` | `m.resetParam()` | |
| `m.read("x.prm")` / `m.write("x.prm")` | `m.read("x.par")` / `m.write("x.par")` | Different file extension |

**Common parameters**

The "Semantics" column states whether the values and their meaning coincide. Parameters marked "differ" cannot be copied over by value.

| Purpose | Gurobi | COPT | Semantics |
|---|---|---|---|
| Time limit (seconds) | `TimeLimit` | `TimeLimit` | Same |
| Time limit after a feasible solution is found | None | `SolTimeLimit` | COPT only |
| Relative MIP gap | `MIPGap` (default 1e-4) | `RelGap` (default 1e-4) | Same |
| Absolute MIP gap | `MIPGapAbs` (default 1e-10) | `AbsGap` (default 1e-6) | Same meaning, **different default** |
| Primal feasibility tolerance | `FeasibilityTol` (1e-6) | `FeasTol` (1e-6) | Same |
| Dual feasibility tolerance | `OptimalityTol` (1e-6) | `DualTol` (1e-6) | Same |
| Integrality tolerance | `IntFeasTol` (1e-5) | `IntTol` (1e-6) | Same meaning, **different default** |
| Threads | `Threads` (0 = automatic) | `Threads` (-1 = automatic) | Different value for "automatic" |
| LP algorithm | `Method` | `LpMethod` | **Values differ**: Gurobi 0 primal simplex / 1 dual simplex / 2 barrier / 3 concurrent / 4 deterministic concurrent / 6 PDHG (first-order method, new in 13.0); COPT 1 dual simplex / 2 barrier / 3 crossover / 4 concurrent / 5 automatic choice / 6 first-order method (PDLP). -1 is automatic on both |
| Crossover | `Crossover` | `Crossover` | Same meaning, different value range |
| Presolve | `Presolve` (-1/0/1/2) | `Presolve` (-1/0/1/2/3/4) | COPT has two more aggressive levels |
| Scaling | `ScaleFlag` | `Scaling` | |
| Cut aggressiveness | `Cuts` | `CutLevel` (-1/0/1/2/3) | Similar |
| Heuristic effort | `Heuristics` (fraction of time, 0–1) | `HeurLevel` (level -1/0/1/2/3) | **Semantics differ** |
| Node limit | `NodeLimit` | `NodeLimit` | Same |
| Barrier iteration limit | `BarIterLimit` | `BarIterLimit` | Same |
| Memory limit | `MemLimit` / `SoftMemLimit` | `MemLimit` | **Different units**: Gurobi in GB, COPT in MB |
| Lazy constraints switch | `LazyConstraints` | `LazyConstraints` | Same |
| Nonconvex handling | `NonConvex` | `NonConvex` | Similar meaning, different values (Chapter 4) |
| IIS algorithm | `IISMethod` | `IISMethod` | Values differ |
| Logging switch | `OutputFlag` | `Logging` | |
| Log to console | `LogToConsole` | `LogToConsole` | Same |
| Log file | `LogFile` | No parameter; use `m.setLogFile("x.log")` | |
| MIP start handling | `StartNodeLimit` | `MipStartMode` / `MipStartNodeLimit` | Chapter 3 |
| Tuner time limit | `TuneTimeLimit` | `TuneTimeLimit` | Same |
| Sensitivity analysis | Always available | `ReqSensitivity = 1` | Off by default in COPT; enable when needed |
| Farkas certificate / unbounded ray | `InfUnbdInfo = 1` | `ReqFarkasRay = 1` | |

!!! tip "Start from COPT's defaults"

    COPT's algorithmic parameters (`LpMethod`, `Presolve`, `CutLevel`, `HeurLevel`, `Scaling`, …) default to -1, meaning the solver chooses based on the characteristics of the model. A parameter set tuned on Gurobi targets Gurobi's algorithmic implementation; copied to COPT it is usually meaningless and can reduce performance. When migrating, keep only the limits the application requires (time limit, gap, threads) and run a first benchmark with defaults. Performance parameters are covered in Chapter 6; COPT's tuner (`m.tune()`) can be used there.

## 2.8 Constants

Constant names are largely the same; the value of `INFINITY` and the encoding of basis statuses differ:

| Meaning | Gurobi | COPT | Notes |
|---|---|---|---|
| Continuous / binary / integer | `GRB.CONTINUOUS` (`'C'`) / `GRB.BINARY` (`'B'`) / `GRB.INTEGER` (`'I'`) | `COPT.CONTINUOUS` / `COPT.BINARY` / `COPT.INTEGER` | Same names; the COPT documentation lists the constants without literal values — use the constants |
| Minimize / maximize | `GRB.MINIMIZE` (1) / `GRB.MAXIMIZE` (-1) | `COPT.MINIMIZE` / `COPT.MAXIMIZE` | Same names; use the constants |
| Infinity | `GRB.INFINITY` (1e100) | `COPT.INFINITY` (1e30) | **Different values**, see 2.2 |
| Constraint sense | `GRB.LESS_EQUAL` (`'<'`) / `GRB.GREATER_EQUAL` (`'>'`) / `GRB.EQUAL` (`'='`) | `COPT.LESS_EQUAL` / `COPT.GREATER_EQUAL` / `COPT.EQUAL` | Same names; use the constants |
| SOS type | `GRB.SOS_TYPE1` / `GRB.SOS_TYPE2` | `COPT.SOS_TYPE1` / `COPT.SOS_TYPE2` | |
| Basis status | `GRB.BASIC` (0) / `NONBASIC_LOWER` (-1) / `NONBASIC_UPPER` (-2) / `SUPERBASIC` (-3) | `COPT.BASIS_LOWER` (0) / `BASIS_BASIC` (1) / `BASIS_UPPER` (2) / `BASIS_SUPERBASIC` (3) / `BASIS_FIXED` (4) | **Completely different encoding** |
| Parameter / attribute / info namespaces | `GRB.Param.*` / `GRB.Attr.*` | `COPT.Param.*` / `COPT.Attr.*` (model level) / `COPT.Info.*` (variable and constraint level) | COPT splits model attributes and variable/constraint information into two namespaces |
| Callback contexts | `GRB.Callback.MIPSOL` etc. | `COPT.CBCONTEXT_MIPSOL` etc. | Chapter 3 |

## 2.9 File I/O

`m.write(filename)` picks the format from the extension on both sides. Reading differs: Gurobi reads model files with the module-level `gp.read()`, while `m.read()` only reads auxiliary files (basis, MIP start, parameters, …); COPT uses `m.read()` for everything, model and auxiliary files alike, recognized by extension.

| Content | Gurobi extension | COPT extension | Notes |
|---|---|---|---|
| Model (text) | `.lp`, `.mps`, `.rew`, `.rlp` | `.lp`, `.mps` | |
| Model (binary) | None | `.bin` | COPT only |
| Conic model | None | `.cbf` | |
| Solution | `.sol`, `.json` | `.sol`; JSON via `writeJsonSol()` / `readJsonSol()` | |
| MIP start | `.mst` | `.mst` | |
| Basis | `.bas` | `.bas` | |
| Branching priorities | `.ord` (read only) | `.ord` | |
| Parameters | `.prm` | `.par` | **Different extension** |
| IIS | `.ilp` | `.iis` (via `writeIIS()`) | Run `computeIIS()` first |
| Feasibility-relaxation problem | None | `.relax` (via `writeRelax()`) | After `feasRelax` |
| Dual problem | `.dua`, `.dlp` | Set parameter `WriteDualProb` to 1 when writing `.lp` / `.mps` / `.bin` | |

Besides extension-based `write`/`read`, COPT also offers explicit-format methods (`writeLp`, `writeMps`, `writeBin`, `writeSol`, `writeMst`, `writeBasis`, `writeParam`, `writeIIS`, `writeRelax`, `readMps`, `readLp`, `readSol`, `readMst`, `readBasis`, `readParam`, …) with the same behavior.

## 2.10 Not covered in this chapter

The following features exist on both sides but differ substantially in interface design. They are covered in later chapters:

- **MIP starts**: `x.Start` → `setMipStart` + `loadMipStart` (Chapter 3)
- **Callbacks**: Gurobi's function-style `optimize(callback)` → subclassing COPT's `CallbackBase` (Chapter 3)
- **Modifying a model after solving and re-solving**: two-sided constraints, parameter persistence, warm-start behavior (Chapter 3)
- **Matrix API**, **multiple objectives**, **solution pool**, **IIS and feasibility relaxation**, **tuner**, **conic constraints and nonconvex / nonlinear models** (Chapter 4)


*Chapter 3 and later chapters will be published progressively. If you hit a usage pattern this guide does not cover, please open an issue in the [GitHub repository](https://github.com/redpanda997/gurobi-to-copt/issues) — frequently asked questions will be folded into later chapters.*
