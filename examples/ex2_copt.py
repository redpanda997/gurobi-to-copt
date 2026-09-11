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
