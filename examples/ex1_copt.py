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
