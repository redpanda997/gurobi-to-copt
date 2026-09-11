---
hide:
  - toc
---

# Chapter 1 — Up and running in ten minutes

This chapter covers installation, license configuration and two complete examples. It shows how to run a Gurobi model on COPT and how the two APIs correspond.

## 1.1 Installation

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

## 1.2 Licensing

| | Gurobi | COPT |
|---|---|---|
| License files | `gurobi.lic` (one file) | `license.dat` + `license.key` (two files, same directory) |
| Default search locations | Home directory, `/opt/gurobi` (Linux), `C:\gurobi` (Windows), `/Library/gurobi` (macOS) | A `copt/` folder in the home directory (e.g. `~/copt/`, `C:\Users\<name>\copt\`), or the directory of the COPT shared library / `copt_cmd` |
| Environment variable | `GRB_LICENSE_FILE` (points to the file) | `COPT_LICENSE_DIR` (points to the directory) |
| Floating / cluster licenses | Token Server | Floating / cluster license (clients point to the license server via `EnvrConfig` or the `client.ini` configuration file) |
| Cloud licensing | WLS (Web License Service) | Web license |
| Trial | The pip package includes a size-limited trial license (2000 variables × 2000 constraints) | Apply for a free personal license on the COPT website |

All examples in this guide are small models and run under any type of COPT license.

At startup COPT logs each location it checked for a license. When a license is not found, these lines are the first thing to check:

```
[INFO] checks license for COPT v8.0.6 20260807
[WARN] no license files in current working folder: /home/laura/project
[WARN] no license files in HOME folder: /home/laura/copt
[INFO] empty environment variable: COPT_LICENSE_DIR
```

## 1.3 A first model, side by side

A minimal production-planning problem: two products A and B with unit profits 20 and 30; machine time 1 h for A and 2 h for B out of 100 h; raw material 3 kg for A and 2 kg for B out of 240 kg; demand for B is capped at 30 units; quantities are integers.

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

Both scripts print exactly the same result:

```
Profit = 1850
A = 70
B = 15
```

Compared line by line, the two scripts differ in five places:

| # | Gurobi | COPT | Notes |
|---|---|---|---|
| 1 | `import gurobipy as gp` / `from gurobipy import GRB` | `import coptpy as cp` / `from coptpy import COPT` | Constant namespace `GRB` → `COPT` |
| 2 | `m = gp.Model("production")` | `env = cp.Envr()` <br> `m = env.createModel("production")` | COPT requires an explicit environment `Envr`; models are created from it |
| 3 | `m.optimize()` | `m.solve()` | Different method name |
| 4 | `GRB.OPTIMAL` | `COPT.OPTIMAL` | Same constant name, **different numeric value** (2 vs 1); use the constant, not the number |
| 5 | `v.VarName` / `v.X` | `v.name` / `v.x` | The name attribute is `name` and the solution value is `x`; `m.ObjVal` and `m.Status` work unchanged in COPT, see below |

Item 5 needs a note. The COPT documentation states that model attributes and variable / constraint information can be accessed either in their **original case** (`m.ObjVal`, `m.Status`, `x.LB`, `x.UB`, `x.Obj`, `c.Slack`) or in **all lowercase** (`m.objval`, `x.lb`). Attributes that share a name on both sides can therefore keep the Gurobi spelling. What has to change are the attributes whose names differ, such as `VarName` → `name`, `X` → `x`, `RC` → `rc`, `Pi` → `pi`, `NumVars` → `cols` and `Runtime` → `solvingtime`; Chapter 2 has the full list. In practice coptpy's attribute lookup is case-insensitive, so `x.X` and `c.Pi` also run, but the documentation does not guarantee this and this guide does not rely on it. COPT code in this guide uses the lowercase spelling from the documentation.

## 1.4 A more typical example: tupledict, quicksum and shadow prices

gurobipy code in real projects is usually built with `addVars`, `tupledict`, `quicksum` and `addConstrs`. The following transportation problem uses these, and also sets a parameter and reads dual values.

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

Besides the five changes from 1.3, this example has three more differences, which are also the most common ones in a migration:

| Gurobi | COPT | Notes |
|---|---|---|
| `m.Params.TimeLimit = 60` | `m.setParam(COPT.Param.TimeLimit, 60)` <br> or `m.Param.TimeLimit = 60` | See 2.7 for parameters; most parameter **names** are identical, a few differ (e.g. `MIPGap` → `RelGap`) |
| `m.Params.OutputFlag = 0` | `m.setParam(COPT.Param.Logging, 0)` | The logging switch is called `Logging` |
| `addVars(..., name="ship")` <br> `addConstrs(..., name="supply")` | `addVars(..., nameprefix="ship")` <br> `addConstrs(..., nameprefix="supply")` | For bulk creation the keyword is `nameprefix` and COPT generates the names automatically; the generated format also differs: Gurobi `ship[P1,M1]`, COPT (as observed) `ship(P1,M1)` |

`tupledict` (with `.sum()` and `.prod()`), `quicksum`, `multidict` and `tuplelist` all exist under the same names in coptpy with the same behavior, so this part of your code normally needs no changes.

## 1.5 Chapter checklist

To migrate a gurobipy script, apply the following seven basic replacements first. Except for item 3, they are the core rules listed in the [COPTPY-GUROBIPY](https://github.com/leavesgrp/COPTPY-GUROBIPY) comparison table maintained by the COPT team:

1. `import gurobipy as gp` → `import coptpy as cp`
2. `GRB` → `COPT`
3. `gp.Model(...)` → `env = cp.Envr()` + `env.createModel(...)`
4. `name=` → `nameprefix=` in `addVars` / `addConstrs`
5. `m.optimize()` → `m.solve()`
6. `m.getAttr("X", vars)` → `m.getInfo(COPT.Info.Value, vars)`
7. `VarName`/`ConstrName` → `name`

Then check three more points:

8. Replace every hard-coded status number (e.g. `== 2`) with a constant such as `COPT.OPTIMAL`
9. `m.Params.X = v` → `m.Param.X = v` (singular `Param` instead of `Params`) or `m.setParam(COPT.Param.X, v)`, and check the parameter name (2.7)
10. Other renamed attributes: `X` → `x`, `Pi` → `pi`, `RC` → `rc`, `NumVars`/`NumConstrs` → `cols`/`rows`, `Runtime` → `solvingtime`, `MIPGap` → `bestgap` (full list in 2.6)

Most small and medium scripts run after these ten items. If the code uses callbacks, MIP starts (`x.Start`), `addRange`, hand-built `LinExpr` objects, or modifies the model after solving, continue with Chapters 2 and 3.
