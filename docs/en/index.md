# Migrating from Gurobi to COPT: A Practical Guide for Python Users

!!! info "Versions"

    Every code sample in this guide was run and verified with gurobipy 13.0.3 and coptpy 8.0.6. APIs evolve; the [Gurobi documentation](https://docs.gurobi.com/) and the [COPT documentation](https://guide.coap.online/copt/en-doc/) are the final authority.

!!! info "Audience"

    Developers who model with gurobipy and want to move existing code to COPT. If you work through a modeling framework rather than calling the solver API directly, see Chapter 5; usually only the solver name needs to change.

## Outline

This guide has seven chapters. Chapters 1 and 2 are published now; the rest will follow. The basic replacement rules follow the comparison table [COPTPY-GUROBIPY](https://github.com/leavesgrp/COPTPY-GUROBIPY) maintained by the COPT team, extended here with item-by-item mappings for parameters, status codes, attributes and file formats.

| Chapter | Contents | Status |
|---|---|---|
| [Chapter 1 — Up and running in ten minutes](chapter1.md) | Installation, licensing, a first model side by side, migration checklist | ✅ Published |
| [Chapter 2 — Core mapping tables](chapter2.md) | Item-by-item mapping for environment & model, variables, constraints, objective, solving & status codes, reading results, parameters, constants, file I/O | ✅ Published |
| Chapter 3 — Where the APIs are not one-to-one | Two-sided constraints, MIP starts, class-based callbacks, modifying a model after solving, parameter semantics | In progress |
| Chapter 4 — Advanced topics | Matrix API, multi-objective, solution pool, IIS & feasibility relaxation, tuner, SOC/exponential cones, nonconvex (MI)QCQP and nonlinear | Planned |
| Chapter 5 — Switching inside a modeling framework | Before/after for Pyomo, JuMP, CVXPY, PuLP, AMPL, GAMS | Planned |
| Chapter 6 — Validation and performance | Confirming identical results, fair benchmarking, reading the COPT log, when to tune | Planned |
| Chapter 7 — Migration checklist and cheat sheet | One-page downloadable cheat sheet, FAQ | Planned |
