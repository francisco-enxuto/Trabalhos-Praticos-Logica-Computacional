# /// script
# dependencies = ["marimo"]
# requires-python = ">=3.14"
# ///

import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium")

with app.setup:
    import marimo as mo
    import pandas as pd
    from pysmt.shortcuts import Symbol, LE, GE, Int, And, Equals, Plus, Solver, is_sat, get_model, Not
    from pysmt.typing import INT, BOOL


@app.cell
def _():
    disciplinas = pd.read_csv("dados/disciplinas.csv")
    disponibilidade_execoes = pd.read_csv("dados/disponibilidade_excecoes.csv")
    salas = pd.read_csv("dados/salas.csv")
    turmas = pd.read_csv("dados/turmas.csv")

    dia = ["Seg", "Ter", "Qua", "Qui", "Sex"]
    periodo = [1, 2, 3, 4, 5]

    turma = []
    for t in turmas["turma"]:
        turma.append(t)

    variaveis = {}

    for t in turma:
        for c in range(len(disciplinas)):
            for d in dia:
                for p in periodo:
                    nome = f"{t}_{disciplinas['disciplina'][c]}_{d}_{p}"
                    variaveis[(t, disciplinas['disciplina'][c], d, p)] = Symbol(nome, BOOL)

    s = Solver(name="z3")

    # R1
    for t in turma:
        for c in range(len(disciplinas)-1):
            for d in dia:
                for p in periodo:
                    s.add_assertion(Not(And(variaveis[(t, disciplinas['disciplina'][c], d, p)], variaveis[(t, disciplinas['disciplina'][c+1], d, p)])))

    s.is_sat
    print(is_sat(s))

    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
