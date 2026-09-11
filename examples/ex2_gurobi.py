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
