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
    from pysmt.shortcuts import Symbol, LE, GE, Int, And, Equals, Plus, Solver, is_sat, get_model, Not, Ite
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
        for c1 in range(len(disciplinas)):
            for c2 in range(c1+1, len(disciplinas)):
                for d in dia:
                    for p in periodo:
                        s.add_assertion(Not(And(variaveis[(t, disciplinas['disciplina'][c1], d, p)], variaveis[(t, disciplinas['disciplina'][c2], d, p)])))

    # R2
    for t in turma:
        for c in range(len(disciplinas)):
            disc = disciplinas['disciplina'][c]
            carga = int(disciplinas['carga_semanal'][c])

            soma = Plus([
                Ite(variaveis[(t, disc, d, p)], Int(1), Int(0))
                for d in dia for p in periodo
            ])

            s.add_assertion(Equals(soma, Int(carga)))

    resultado = s.solve()
    print(resultado)
    if resultado:
        modelo = s.get_model()
        print(modelo)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
