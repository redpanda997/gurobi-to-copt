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
