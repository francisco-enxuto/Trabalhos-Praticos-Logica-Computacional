import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from pysmt.shortcuts import Symbol, Solver, And, LE, GE, Int, Equals, AllDifferent
    from pysmt.typing import INT

    return


@app.class_definition
class Box:
    def __init__(self, n, cells=None):
        self.n = n
        self.size = n * n
        self.cells = {}
        for (i, j), val in (cells or {}).items():
            self.add(i, j, val)
 
    def add(self, i, j, val=None):
        if not (0 <= i < self.size and 0 <= j < self.size):
            raise ValueError(f"Célula ({i}, {j}) fora da grelha {self.size}x{self.size}")
        if val is not None and not (1 <= val <= self.size):
            raise ValueError(f"Valor {val} fora de [1, {self.size}]")
        self.cells[(i, j)] = val

    def to_matrix(self):
        m = []
        for _ in range(self.size):
            m.append([0] * self.size)
        for (i,j), val in self.cells.items():
            if val is not None:
                m[i][j] = val
        return m


if __name__ == "__main__":
    app.run()
