# Chapter 2 — Core mapping tables

This chapter follows the modeling workflow: environment & model → variables → constraints → objective → solving & status → reading results → parameters → constants → file I/O. Each table stands on its own as a quick reference.

Three general rules explain most of the differences:

1. **Method names are mostly the same.** `addVar`, `addVars`, `addConstr`, `addConstrs`, `setObjective`, `getVars`, `getConstrs`, `computeIIS`, `write`, `read`, `remove`, `reset`, `tune` and many more share name and meaning on both sides. The most visible exception is `optimize()` → `solve()`.
2. **Attributes can be accessed in original case or all lowercase, but some attribute names differ.** The COPT documentation states that attribute names may be written in their original case (`m.ObjVal`) or in lowercase (`m.objval`), so attributes that share a name with Gurobi can stay as they are. What you must edit are attributes whose names differ — see 2.6.
3. **Status codes have different numeric values.** `GRB.OPTIMAL == 2` whereas `COPT.OPTIMAL == 1`. Any code that compares against literal numbers instead of constants will break after migration.

## 2.1 Environment and model lifecycle

| Operation | Gurobi | COPT | Notes |
|---|---|---|---|
| Import | `import gurobipy as gp` <br> `from gurobipy import GRB` | `import coptpy as cp` <br> `from coptpy import COPT` | |
| Create environment | `env = gp.Env()` (optional — `Model()` creates a default environment implicitly) | `env = cp.Envr()` | COPT always creates the environment explicitly, so license and resource ownership are obvious at a glance |
| Create model | `m = gp.Model("name", env=env)` | `m = env.createModel("name")` | Models are created from the environment |
| Model from file | `m = gp.read("model.mps")` | `m = env.createModel()` <br> `m.read("model.mps")` | COPT reads through the model object, so the loaded model belongs to a specific environment from the start |
| Copy a model | `m2 = m.copy()` | `m2 = m.clone()` | |
| Release resources | `m.dispose()` / `env.dispose()` <br> or `with gp.Env() as env, gp.Model(env=env) as m:` | No explicit release needed; objects are freed automatically by Python's garbage collector | COPT has no `dispose()`, and the documentation defines no `with` usage — simply let objects go out of scope. `env.close()` only disconnects from a floating / cluster license server |
| Synchronize changes | `m.update()` | Not needed while modeling | See note below |

!!! tip "Modeling in COPT has no `update()` step"

    Gurobi uses lazy updates: adding variables, changing bounds or removing items is queued until `m.update()` (or `optimize()` / `write()`) is called, and the Gurobi documentation warns that a forgotten call does not raise an error — queries simply return the values from the last update. COPT's official examples have no such step: add variables and constraints, set parameters, then solve and query directly. coptpy does provide `Model.update()`; the documentation defines its purpose as "update the model, including numerical ranges, removed variables and constraints", so it is only relevant when you need refreshed coefficient statistics after removing items. During migration you can usually delete every `m.update()` call.

!!! tip "Parameters are set in one place: the model"

    Gurobi parameters can live on an `Env` or on a `Model`; a model takes its own copy of the environment when it is created, and later changes to the original environment no longer affect it, so with two layers you have to keep that timing straight. COPT has a single location: all solver parameters are on the `Model`, while `Envr` is only responsible for licensing and resources, so you never have to trace back to an environment configuration when reading code. To share one parameter set across several models, use `m.read("settings.par")` or a small helper function.

## 2.2 Variables

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
| Change bounds | `x.LB = 0; x.UB = 5` | `x.lb = 0; x.ub = 5` | |
| Bulk read / write attributes | `m.getAttr("LB", vars)` / `m.setAttr("LB", vars, vals)` | `m.getInfo(COPT.Info.LB, vars)` / `m.setInfo(COPT.Info.LB, vars, vals)` | Gurobi uses attribute-name strings; COPT uses `COPT.Info.*` constants |

**Bounds and infinity**: `GRB.INFINITY` is `1e100`, `COPT.INFINITY` is `1e30`. According to the COPT documentation, a bound is treated as infinite once its absolute value reaches `1e30`, so a leftover `1e100` in old code is still recognized as unbounded. The reverse is not true: a `1e30` read from COPT and fed to Gurobi is a finite (large) number to Gurobi. Use the `COPT.INFINITY` constant everywhere.

**The variable `tupledict`**: `addVars` returns a `tupledict` on both sides, supporting `.sum(...)`, `.prod(coeff_dict)` and the usual dict methods with the same behavior.

## 2.3 Constraints

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

!!! tip "COPT constraints are two-sided by design"

    A Gurobi linear constraint is described by a `Sense` (`<`/`>`/`=`) and an `RHS`; range constraints need the dedicated `addRange`, which Gurobi implements internally by adding an auxiliary variable. COPT represents every linear constraint uniformly as `lb ≤ expr ≤ ub`, described by `c.lb` and `c.ub`: `x + y <= 10` is stored as `lb = -COPT.INFINITY, ub = 10`; `x + y >= 1` as `lb = 1, ub = +COPT.INFINITY`; `x + y == 3` as `lb = ub = 3`. A range constraint is expressed directly with `addBoundConstr`, with no auxiliary variable, and both sides can be changed independently after solving. The corresponding edits during migration are:

    - Code that reads `c.RHS` reads `c.ub` (for ≤) or `c.lb` (for ≥) instead;
    - Code that changes a right-hand side after solving assigns to `c.lb` / `c.ub`;
    - `addRange` becomes `addBoundConstr`.

## 2.4 Objective

| Operation | Gurobi | COPT | Notes |
|---|---|---|---|
| Set the objective | `m.setObjective(expr, GRB.MAXIMIZE)` | `m.setObjective(expr, COPT.MAXIMIZE)` | Identical |
| Change only the sense | `m.ModelSense = GRB.MINIMIZE` | `m.objsense = COPT.MINIMIZE` or `m.setObjSense(COPT.MINIMIZE)` | |
| Objective constant | `m.ObjCon = 5` | `m.objconst = 5` or `m.setObjConst(5)` | |
| Read the objective expression | `m.getObjective()` | `m.getObjective()` | |
| Objective coefficient of a variable | `x.Obj` | `x.obj` | |
| Multiple objectives | `m.setObjectiveN(expr, index, priority, weight, ...)` | `m.setObjectiveN(index, expr, sense, priority, weight, ...)` | **Different argument order**, Chapter 4 |
| Matrix-form objective | `m.setMObjective(...)` | `m.setMObjective(...)` | Chapter 4 |

## 2.5 Solving and status codes

| Operation | Gurobi | COPT |
|---|---|---|
| Solve | `m.optimize()` | `m.solve()` |
| Solve the LP relaxation / an LP only | `m.relax().optimize()` | `m.solveLP()` (ignores integrality and solves the LP) |
| Interrupt | `m.terminate()` | `m.interrupt()` |
| Clear the solution | `m.reset()` / `m.reset(1)` | `m.reset()` / `m.resetAll()` (the latter also clears additional information such as MIP starts and the IIS) |
| Read the status | `m.Status` | `m.status` |
| Is a solution available? | `m.SolCount > 0` | `m.hassol` (the older `hasmipsol` / `haslpsol` are marked deprecated in the 8.0 documentation) |

Status code mapping (use constants on both sides, **never hard-code the numbers**):

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

A common pattern — "time limit hit, but use the solution if there is one":

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

The COPT column shows the lowercase spelling used in the COPT documentation. **Bold** rows are attributes whose names actually differ and must be edited; the other rows share the same name on both sides and, per the COPT documentation, can be accessed in original case or lowercase — so the Gurobi spelling can stay.

**Variable attributes**

| Meaning | Gurobi | COPT | Notes |
|---|---|---|---|
| **Solution value** | **`x.X`** | **`x.x` (or `x.value`)** | Corresponds to the COPT information item `Value` |
| **Name** | **`x.VarName`** | **`x.name`** | |
| Lower / upper bound | `x.LB` / `x.UB` | `x.lb` / `x.ub` | |
| Objective coefficient | `x.Obj` | `x.obj` | |
| **Type** | **`x.VType`** | **`x.vtype`** | |
| **Reduced cost (LP)** | **`x.RC`** | **`x.rc`** | Information item `RedCost`; available for LPs or when an LP solution exists |
| **Basis status** | **`x.VBasis`** | **`x.basis`** | Different encoding (see 2.8) |
| **MIP start** | **`x.Start = v`** | **`m.setMipStart(x, v)` + `m.loadMipStart()`** | Chapter 3 |
| **k-th solution from the pool** | **`m.Params.SolutionNumber = k; x.PoolNX`** | **`m.getPoolSolution(k, vars)`** | `Xn` is deprecated since Gurobi 13 in favor of `PoolNX`; Chapter 4 |
| Sensitivity analysis | `x.SAObjLow/Up`, `x.SALBLow/Up`, `x.SAUBLow/Up` | `x.saobjlow/up`, `x.salblow/up`, `x.saublow/up` | Computed on demand in COPT: available after setting `ReqSensitivity = 1`, no overhead when not needed |
| **Unbounded ray** | **`x.UnbdRay`** | **`x.primalray`** | Must be enabled on both sides: Gurobi `InfUnbdInfo = 1`, COPT `ReqFarkasRay = 1` |
| **IIS membership** | **`x.IISLB` / `x.IISUB`** | **`x.getLowerIIS()` / `x.getUpperIIS()`** | After `computeIIS()` |
| Index | `x.index` | `x.index` | |

**Constraint attributes**

| Meaning | Gurobi | COPT | Notes |
|---|---|---|---|
| **Name** | **`c.ConstrName`** | **`c.name`** | |
| **Right-hand side / sense** | **`c.RHS` / `c.Sense`** | **`c.lb` / `c.ub`** | Two-sided representation, see 2.3 |
| **Dual value (shadow price)** | **`c.Pi`** | **`c.pi` (or `c.dual`)** | Information item `Dual`; available for LPs or when an LP solution exists |
| Slack | `c.Slack` | `c.slack` | |
| **Basis status** | **`c.CBasis`** | **`c.basis`** | |
| **Farkas dual** | **`c.FarkasDual`** | **`c.dualfarkas`** | Must be enabled on both sides: Gurobi `InfUnbdInfo = 1`, COPT `ReqFarkasRay = 1` |
| **IIS membership** | **`c.IISConstr`** | **`c.getLowerIIS()` / `c.getUpperIIS()`** | COPT distinguishes whether the lower or the upper bound is in the IIS |
| Index | `c.index` | `c.index` | |

**Model attributes**

| Meaning | Gurobi | COPT | Notes |
|---|---|---|---|
| Solve status | `m.Status` | `m.status` | |
| Objective value | `m.ObjVal` | `m.objval` | |
| Objective bound | `m.ObjBound` | `m.objbound` | The older `bestbnd` is marked deprecated in the 8.0 documentation |
| **Relative gap** | **`m.MIPGap`** | **`m.bestgap`** | |
| **Solve time** | **`m.Runtime`** | **`m.solvingtime`** | |
| **Node count** | **`m.NodeCount`** | **`m.nodecnt`** | |
| **Simplex iterations** | **`m.IterCount`** | **`m.simplexiter`** | |
| **Barrier iterations** | **`m.BarIterCount`** | **`m.barrieriter`** | |
| **Number of pool solutions** | **`m.SolCount`** | **`m.poolsols`** | |
| **Number of variables / constraints / nonzeros** | **`m.NumVars` / `m.NumConstrs` / `m.NumNZs`** | **`m.cols` / `m.rows` / `m.elems`** | |
| **Number of integer / binary variables** | **`m.NumIntVars` / `m.NumBinVars`** | **`m.ints` / `m.bins`** | |
| **Number of quadratic constraints / SOS** | **`m.NumQConstrs` / `m.NumSOS`** | **`m.qconstrs` / `m.soss`** | |
| Is a MIP | `m.IsMIP` | `m.ismip` | |
| **Has a quadratic objective** | **`m.IsQP`** | **`m.hasqobj`** | |
| **Objective sense / constant** | **`m.ModelSense` / `m.ObjCon`** | **`m.objsense` / `m.objconst`** | |
| **Solution available** | **`m.SolCount > 0`** | **`m.hassol`** | |
| **Coefficient ranges** | **`m.MaxCoeff/MinCoeff`, `m.MaxRHS/MinRHS`, `m.MaxObjCoeff/MinObjCoeff`** | **`m.maxelem/minelem`, `m.maxrhs/minrhs`, `m.maxcost/mincost`** | |

**Bulk reads**

| Gurobi | COPT |
|---|---|
| `m.getAttr("X", m.getVars())` | `m.getValues()` or `m.getInfo(COPT.Info.Value, vars)` |
| `m.getAttr("Pi", m.getConstrs())` | `m.getDuals()` or `m.getInfo(COPT.Info.Dual, constrs)` |
| `m.getAttr("RC", m.getVars())` | `m.getRedcosts()` or `m.getInfo(COPT.Info.RedCost, vars)` |
| `m.getAttr("Slack", m.getConstrs())` | `m.getSlacks()` or `m.getInfo(COPT.Info.Slack, constrs)` |
| — | `m.getLpSolution()`: returns `(values, slacks, duals, redcosts)` in one call |

## 2.7 Parameters

**How to set them**

| Gurobi | COPT | Notes |
|---|---|---|
| `m.Params.TimeLimit = 60` | `m.Param.TimeLimit = 60` | Attribute style (note `Params` in Gurobi vs `Param` in COPT) |
| `m.setParam(GRB.Param.TimeLimit, 60)` | `m.setParam(COPT.Param.TimeLimit, 60)` | Constant style — the form recommended by both documentations |
| `m.setParam("TimeLimit", 60)` | `m.setParam("TimeLimit", 60)` | The string form is identical on both sides, convenient for a parameter mapping table (explicitly documented for Gurobi; for COPT the constant `COPT.Param.TimeLimit` evaluates to the string `"TimeLimit"`, as observed) |
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
| Sensitivity analysis | Always available | `ReqSensitivity = 1` | Enabled on demand in COPT, avoiding unnecessary computation |
| Farkas certificate / unbounded ray | `InfUnbdInfo = 1` | `ReqFarkasRay = 1` | |

!!! tip "Start from COPT's defaults"

    COPT's algorithmic parameters (`LpMethod`, `Presolve`, `CutLevel`, `HeurLevel`, `Scaling`, the automatic mode of `Crossover`, …) default to -1, meaning the solver chooses based on the characteristics of the model. A parameter set tuned on Gurobi targets a different algorithmic implementation; carried over verbatim it is usually meaningless for COPT and can even slow the solve down. When migrating, keep only the limits your business requires (time limit, gap, threads) and run a first benchmark with defaults; leave performance parameters to the tuning workflow in Chapter 6, where COPT's built-in tuner (`m.tune()`) can search systematically.

## 2.8 Constants

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

`m.write(filename)` picks the format from the extension on both sides. Reading differs slightly: Gurobi reads model files with the module-level `gp.read()`, while `m.read()` only reads auxiliary files (basis, MIP start, parameters, …); COPT uses `m.read()` for everything, model and auxiliary files alike, recognized by extension.

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

The following features exist on both sides but differ enough in design that a one-line mapping would mislead. They get their own treatment in later chapters:

- **MIP starts**: `x.Start` → `setMipStart` + `loadMipStart` (Chapter 3)
- **Callbacks**: Gurobi's function-style `optimize(callback)` → subclassing COPT's `CallbackBase` (Chapter 3)
- **Modifying a model after solving and re-solving**: two-sided constraints, parameter persistence, warm-start behavior (Chapter 3)
- **Matrix API**, **multiple objectives**, **solution pool**, **IIS and feasibility relaxation**, **tuner**, **conic constraints and nonconvex / nonlinear models** (Chapter 4)


*Chapter 3 and later chapters will be published progressively. If you hit a usage pattern this guide does not cover, please open an issue in the [GitHub repository](https://github.com/redpanda997/gurobi-to-copt/issues) — frequently asked questions will be folded into later chapters.*
