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


@app.cell
def _():
    disciplinas = pd.read_csv("dados/disciplinas.csv")
    disponibilidade_execoes = pd.read_csv("dados/disponibilidade_excecoes.csv")
    salas = pd.read_csv("dados/salas.csv")
    turmas = pd.read_csv("dados/turmas.csv")

    print(disciplinas)
    return


if __name__ == "__main__":
    app.run()
