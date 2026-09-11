# Migrating from Gurobi to COPT: A Practical Guide for Python Users

> **Versions**: Every code sample in this guide was run and verified with gurobipy 13.0.3 and coptpy 8.0.6. APIs evolve; the [COPT documentation](https://guide.coap.online/copt/en-doc/) is the final authority.
>
> **Audience**: Developers who model with gurobipy and want to move existing code to COPT. If you use a modeling framework such as Pyomo, JuMP, CVXPY, PuLP, AMPL or GAMS, skip ahead to Chapter 5 — you usually only need to change the solver name.

---

## Outline

This guide has seven chapters. Chapters 1 and 2 are published now; the rest will follow.

| Chapter | Contents | Status |
|---|---|---|
| **Chapter 1 — Up and running in ten minutes** | Installation, licensing, a first model side by side, migration checklist | ✅ Published |
| **Chapter 2 — Core mapping tables** | Item-by-item mapping for environment & model, variables, constraints, objective, solving & status codes, reading results, parameters, constants, file I/O | ✅ Published |
| Chapter 3 — Where the APIs are not one-to-one | Two-sided constraints, MIP starts, class-based callbacks, modifying a model after solving, parameter semantics | In progress |
| Chapter 4 — Advanced topics | Matrix API, multi-objective, solution pool, IIS & feasibility relaxation, tuner, SOC/exponential cones, nonconvex (MI)QCQP and nonlinear | Planned |
| Chapter 5 — Switching inside a modeling framework | Before/after for Pyomo, JuMP, CVXPY, PuLP, AMPL, GAMS | Planned |
| Chapter 6 — Validation and performance | Confirming identical results, fair benchmarking, reading the COPT log, when to tune | Planned |
| Chapter 7 — Migration checklist and cheat sheet | One-page downloadable cheat sheet, FAQ | Planned |

---

## Chapter 1 — Up and running in ten minutes

The goal of this chapter is to get your first Gurobi model running on COPT within ten minutes, and to give you a feel for how close the two APIs are.

### 1.1 Installation

Both solvers ship as pip packages:

```bash
# Gurobi
pip install gurobipy

# COPT
pip install coptpy
```

The COPT documentation recommends installing and configuring COPT before using the Python interface: the full installer is available from the [COPT website](https://copt.shanshu.ai) and also provides the command-line tool `copt_cmd` and the C/C++/Java/C# interfaces.

Verify the installation:

```python
import coptpy as cp
from coptpy import COPT
print(COPT.VERSION_MAJOR, COPT.VERSION_MINOR, COPT.VERSION_TECHNICAL)   # e.g. 8 0 6
```

### 1.2 Licensing

| | Gurobi | COPT |
|---|---|---|
| License files | `gurobi.lic` (one file) | `license.dat` + `license.key` (two files, same directory) |
| Default search locations | Home directory, `/opt/gurobi` (Linux), `C:\gurobi` (Windows), `/Library/gurobi` (macOS) | A `copt/` folder in the home directory (e.g. `~/copt/`, `C:\Users\<name>\copt\`), or the directory of the COPT shared library / `copt_cmd` |
| Environment variable | `GRB_LICENSE_FILE` (points to the file) | `COPT_LICENSE_DIR` (points to the directory) |
| Floating / cluster licenses | Token Server | Floating / cluster license (clients point to the license server via `EnvrConfig` or the `client.ini` configuration file) |
| Cloud licensing | WLS (Web License Service) | Web license |
| Trial | The pip package includes a size-limited trial license (2000 variables × 2000 constraints) | Apply for a free personal license on the COPT website |

All examples in this guide are small models and run under any type of COPT license.

At startup COPT logs each location it checked for a license. When a license is not picked up, read these lines first:

```
[INFO] checks license for COPT v8.0.6 20260807
[WARN] no license files in current working folder: /home/laura/project
[WARN] no license files in HOME folder: /home/laura/copt
[INFO] empty environment variable: COPT_LICENSE_DIR
```

### 1.3 A first model, side by side

A minimal production-planning problem: two products A and B with unit profits 20 and 30; machine time 1 h for A and 2 h for B out of 100 h; raw material 3 kg for A and 2 kg for B out of 240 kg; demand for B is capped at 30 units; quantities are integers.

**Gurobi:**

```python
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

**COPT:**

```python
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

Both scripts print exactly the same result:

```
Profit = 1850
A = 70
B = 15
```

Line by line, only five things changed:

| # | Gurobi | COPT | Notes |
|---|---|---|---|
| 1 | `import gurobipy as gp` / `from gurobipy import GRB` | `import coptpy as cp` / `from coptpy import COPT` | Constant namespace `GRB` → `COPT` |
| 2 | `m = gp.Model("production")` | `env = cp.Envr()` <br> `m = env.createModel("production")` | COPT requires an explicit environment `Envr`; models are created from it |
| 3 | `m.optimize()` | `m.solve()` | Different method name |
| 4 | `GRB.OPTIMAL` | `COPT.OPTIMAL` | Same constant name, **different numeric value** (2 vs 1) — always use the constant, never the number |
| 5 | `v.VarName` / `v.X` | `v.name` / `v.x` | The name attribute is `name` and the solution value is `x`; `m.ObjVal` and `m.Status` work unchanged in COPT, see below |

Good news on item 5: the COPT documentation states that model attributes and variable / constraint information can be accessed either in their **original case** (`m.ObjVal`, `m.Status`, `x.LB`, `x.UB`, `x.Obj`, `c.Slack`) or in **all lowercase** (`m.objval`, `x.lb`). So wherever the two APIs use the same name, the Gurobi spelling can stay. What has to change are the attributes whose *names* differ: `VarName` → `name`, `X` → `x`, `RC` → `rc`, `Pi` → `pi`, `NumVars` → `cols`, `Runtime` → `solvingtime`, and so on; Chapter 2 has the full list. (In practice coptpy's attribute lookup is case-insensitive, so `x.X` and `c.Pi` also run — but this is not guaranteed by the documentation and this guide does not rely on it.) COPT code in this guide uses the lowercase spelling from the COPT documentation.

### 1.4 A more typical example: tupledict, quicksum and shadow prices

Real gurobipy code rarely has two variables. It is usually built from `addVars` + `tupledict` + `quicksum` + `addConstrs`. Here is a transportation problem that also sets a parameter and reads dual values:

**Gurobi:**

```python
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

**COPT:**

```python
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

Again the output is identical:

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

On top of the five changes from 1.3, this example introduces three more — the ones you will meet most often in a migration:

| Gurobi | COPT | Notes |
|---|---|---|
| `m.Params.TimeLimit = 60` | `m.setParam(COPT.Param.TimeLimit, 60)` <br> or `m.Param.TimeLimit = 60` | See 2.7 for parameters; most parameter **names** are identical, a few differ (e.g. `MIPGap` → `RelGap`) |
| `m.Params.OutputFlag = 0` | `m.setParam(COPT.Param.Logging, 0)` | The logging switch is called `Logging` |
| `addVars(..., name="ship")` <br> `addConstrs(..., name="supply")` | `addVars(..., nameprefix="ship")` <br> `addConstrs(..., nameprefix="supply")` | For bulk creation the keyword is `nameprefix` and COPT generates the names automatically; the generated format also differs: Gurobi `ship[P1,M1]`, COPT (as observed) `ship(P1,M1)` |

`tupledict` (with `.sum()` and `.prod()`), `quicksum`, `multidict` and `tuplelist` all exist under the same names in coptpy with the same behavior, so this part of your code normally needs no changes.

### 1.5 Chapter checklist

To move a gurobipy script to COPT, mechanically apply these seven steps first. Most small and medium scripts run after this:

1. `import gurobipy as gp` → `import coptpy as cp`; `GRB` → `COPT`
2. `gp.Model(...)` → `env = cp.Envr()` + `env.createModel(...)`
3. `m.optimize()` → `m.solve()`
4. Replace every hard-coded status number (e.g. `== 2`) with a constant such as `COPT.OPTIMAL`
5. `m.Params.X = v` → `m.Param.X = v` (singular `Param` instead of `Params`) or `m.setParam(COPT.Param.X, v)`, and check the parameter name (2.7)
6. `name=` → `nameprefix=` in `addVars` / `addConstrs`
7. Renamed attributes: `VarName`/`ConstrName` → `name`, `X` → `x`, `Pi` → `pi`, `RC` → `rc`, `NumVars`/`NumConstrs` → `cols`/`rows`, `Runtime` → `solvingtime`, `MIPGap` → `bestgap` (full list in 2.6)

If your code uses callbacks, MIP starts (`x.Start`), `addRange`, or modifies the model after solving, continue with Chapters 2 and 3.

---

## Chapter 2 — Core mapping tables

This chapter follows the modeling workflow: environment & model → variables → constraints → objective → solving & status → reading results → parameters → constants → file I/O. Each table stands on its own as a quick reference.

Three general rules explain most of the differences:

1. **Method names are mostly the same.** `addVar`, `addVars`, `addConstr`, `addConstrs`, `setObjective`, `getVars`, `getConstrs`, `computeIIS`, `write`, `read`, `remove`, `reset`, `tune` and many more share name and meaning on both sides. The most visible exception is `optimize()` → `solve()`.
2. **Attributes can be accessed in original case or all lowercase, but some attribute names differ.** The COPT documentation states that attribute names may be written in their original case (`m.ObjVal`) or in lowercase (`m.objval`), so attributes that share a name with Gurobi can stay as they are. What you must edit are attributes whose names differ — see 2.6.
3. **Status codes have different numeric values.** `GRB.OPTIMAL == 2` whereas `COPT.OPTIMAL == 1`. Any code that compares against literal numbers instead of constants will break after migration.

### 2.1 Environment and model lifecycle

| Operation | Gurobi | COPT | Notes |
|---|---|---|---|
| Import | `import gurobipy as gp` <br> `from gurobipy import GRB` | `import coptpy as cp` <br> `from coptpy import COPT` | |
| Create environment | `env = gp.Env()` (optional — `Model()` creates a default environment implicitly) | `env = cp.Envr()` | COPT always creates the environment explicitly, so license and resource ownership are obvious at a glance |
| Create model | `m = gp.Model("name", env=env)` | `m = env.createModel("name")` | Models are created from the environment |
| Model from file | `m = gp.read("model.mps")` | `m = env.createModel()` <br> `m.read("model.mps")` | COPT reads through the model object, so the loaded model belongs to a specific environment from the start |
| Copy a model | `m2 = m.copy()` | `m2 = m.clone()` | |
| Release resources | `m.dispose()` / `env.dispose()` <br> or `with gp.Env() as env, gp.Model(env=env) as m:` | No explicit release needed; objects are freed automatically by Python's garbage collector | COPT has no `dispose()`, and the documentation defines no `with` usage — simply let objects go out of scope. `env.close()` only disconnects from a floating / cluster license server |
| Synchronize changes | `m.update()` | Not needed while modeling | See note below |

> **Modeling in COPT has no `update()` step.** Gurobi uses lazy updates: adding variables, changing bounds or removing items is queued until `m.update()` (or `optimize()` / `write()`) is called, and the Gurobi documentation warns that a forgotten call does not raise an error — queries simply return the values from the last update. COPT's official examples have no such step: add variables and constraints, set parameters, then solve and query directly. coptpy does provide `Model.update()`; the documentation defines its purpose as "update the model, including numerical ranges, removed variables and constraints", so it is only relevant when you need refreshed coefficient statistics after removing items. During migration you can usually delete every `m.update()` call.

> **Parameters are set in one place: the model.** Gurobi parameters can live on an `Env` or on a `Model`; a model takes its own copy of the environment when it is created, and later changes to the original environment no longer affect it, so with two layers you have to keep that timing straight. COPT has a single location: all solver parameters are on the `Model`, while `Envr` is only responsible for licensing and resources, so you never have to trace back to an environment configuration when reading code. To share one parameter set across several models, use `m.read("settings.par")` or a small helper function.

### 2.2 Variables

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

### 2.3 Constraints

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

> **COPT constraints are two-sided by design.** A Gurobi linear constraint is described by a `Sense` (`<`/`>`/`=`) and an `RHS`; range constraints need the dedicated `addRange`, which Gurobi implements internally by adding an auxiliary variable. COPT represents every linear constraint uniformly as `lb ≤ expr ≤ ub`, described by `c.lb` and `c.ub`: `x + y <= 10` is stored as `lb = -COPT.INFINITY, ub = 10`; `x + y >= 1` as `lb = 1, ub = +COPT.INFINITY`; `x + y == 3` as `lb = ub = 3`. A range constraint is expressed directly with `addBoundConstr`, with no auxiliary variable, and both sides can be changed independently after solving. The corresponding edits during migration are:
>
> - Code that reads `c.RHS` reads `c.ub` (for ≤) or `c.lb` (for ≥) instead;
> - Code that changes a right-hand side after solving assigns to `c.lb` / `c.ub`;
> - `addRange` becomes `addBoundConstr`.

### 2.4 Objective

| Operation | Gurobi | COPT | Notes |
|---|---|---|---|
| Set the objective | `m.setObjective(expr, GRB.MAXIMIZE)` | `m.setObjective(expr, COPT.MAXIMIZE)` | Identical |
| Change only the sense | `m.ModelSense = GRB.MINIMIZE` | `m.objsense = COPT.MINIMIZE` or `m.setObjSense(COPT.MINIMIZE)` | |
| Objective constant | `m.ObjCon = 5` | `m.objconst = 5` or `m.setObjConst(5)` | |
| Read the objective expression | `m.getObjective()` | `m.getObjective()` | |
| Objective coefficient of a variable | `x.Obj` | `x.obj` | |
| Multiple objectives | `m.setObjectiveN(expr, index, priority, weight, ...)` | `m.setObjectiveN(index, expr, sense, priority, weight, ...)` | **Different argument order**, Chapter 4 |
| Matrix-form objective | `m.setMObjective(...)` | `m.setMObjective(...)` | Chapter 4 |

### 2.5 Solving and status codes

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

**Gurobi:**

```python
m.Params.TimeLimit = 60
m.optimize()
if m.Status == GRB.OPTIMAL or (m.Status == GRB.TIME_LIMIT and m.SolCount > 0):
    use(m.ObjVal, m.MIPGap)
```

**COPT:**

```python
m.setParam(COPT.Param.TimeLimit, 60)
m.solve()
if m.status == COPT.OPTIMAL or (m.status == COPT.TIMEOUT and m.hassol):
    use(m.objval, m.bestgap)
```

### 2.6 Reading results: attribute mapping

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

### 2.7 Parameters

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

> **Start from COPT's defaults.** COPT's algorithmic parameters (`LpMethod`, `Presolve`, `CutLevel`, `HeurLevel`, `Scaling`, the automatic mode of `Crossover`, …) default to -1, meaning the solver chooses based on the characteristics of the model. A parameter set tuned on Gurobi targets a different algorithmic implementation; carried over verbatim it is usually meaningless for COPT and can even slow the solve down. When migrating, keep only the limits your business requires (time limit, gap, threads) and run a first benchmark with defaults; leave performance parameters to the tuning workflow in Chapter 6, where COPT's built-in tuner (`m.tune()`) can search systematically.

### 2.8 Constants

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

### 2.9 File I/O

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

### 2.10 Not covered in this chapter

The following features exist on both sides but differ enough in design that a one-line mapping would mislead. They get their own treatment in later chapters:

- **MIP starts**: `x.Start` → `setMipStart` + `loadMipStart` (Chapter 3)
- **Callbacks**: Gurobi's function-style `optimize(callback)` → subclassing COPT's `CallbackBase` (Chapter 3)
- **Modifying a model after solving and re-solving**: two-sided constraints, parameter persistence, warm-start behavior (Chapter 3)
- **Matrix API**, **multiple objectives**, **solution pool**, **IIS and feasibility relaxation**, **tuner**, **conic constraints and nonconvex / nonlinear models** (Chapter 4)

---

*Chapter 3 and later chapters will be published progressively. If you hit a usage pattern this guide does not cover, please open an issue in the [GitHub repository](https://github.com/redpanda997/gurobi-to-copt/issues) — frequently asked questions will be folded into later chapters.*

