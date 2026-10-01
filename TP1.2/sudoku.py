import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from pysmt.shortcuts import Symbol, Solver, And, LE, GE, Int, Equals, AllDifferent
    from pysmt.typing import INT
    import random

    return AllDifferent, And, Equals, GE, INT, Int, LE, Solver, Symbol, random


@app.cell
def _(AllDifferent, And, Equals, GE, INT, Int, LE, Solver, Symbol, random):
    # R1

    def print_matriz(n, m):
        if m is None:
            print("Sem solução")
            return 
        for c in range(n*n):
            for d in range(n):
                print(' ', end='')
                for e in range(n):
                    print(m[c][d * n + e], end=' ') if m[c][d * n + e] is not None else print("~", end=' ') 
                if(d + 1 != n):
                    print('|', end='')
            if (c + 1) % n == 0 and c + 1 < n * n:   
                print('\n' + '_' * (n*n*2 + n*2 - 1))
            else:
                print()
    class box:
 
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
            m = [["~"] * self.size for _ in range(self.size)]
            for (i, j), val in self.cells.items():
                if val is not None:
                    m[i][j] = val
                else:
                    m[i][j] = 0
            return m
 
 
    # R2
    class cube(box):
 
        def __init__(self, n, bi, bj):
            if not (0 <= bi < n and 0 <= bj < n):
                raise ValueError(f"Índices de bloco fora de [0, {n-1}]")
            super().__init__(n)
            for di in range(n):
                for dj in range(n):
                    self.add(bi * n + di, bj * n + dj)
 
    # R3
    class path(box):
 
        def __init__(self, n, inicio, fim):
            super().__init__(n)
            (i0, j0), (i1, j1) = inicio, fim
            if i0 != i1 and j0 != j1:
                raise ValueError("inicio e fim têm de estar na mesma linha ou coluna")
            di = (i1 > i0) - (i1 < i0)
            dj = (j1 > j0) - (j1 < j0)
            i, j = i0, j0
            self.add(i, j)
            while (i, j) != (i1, j1):
                i, j = i + di, j + dj
                self.add(i, j)

    # testes e cenas

    # cube1 = cube(2, 0, 0)
    # cube1.add(0,0,1)
    # print_matrix(cube1.n, cube1.to_matrix())

    # R4

    def box_aleatorio(n, k=None):
        b = box(n)
        rep = k if k is not None else n
        todas_coord = [(i,j) for i in range(b.size) for j in range(b.size)]
        for i, j in random.sample(todas_coord, rep):
            b.add(i, j, random.randint(1,b.size))
        return b

    # cenas
    # b = box_aleatorio(3, 81)
    # print_matriz(b.n, b.to_matrix())

    # R5
    class model:
        def __init__(self, n):
            self.size = n * n
            self.solver = Solver(name="z3")
            self.x = {(i, j): Symbol(f"x_{i}_{j}", INT)
                      for i in range(self.size) for j in range(self.size)}
            for s in self.x.values():
                self.solver.add_assertion(And(GE(s, Int(1)), LE(s, Int(self.size))))

        def add_groups(self, *boxes):
            for b in boxes:
                self.solver.add_assertion(AllDifferent([self.x[c] for c in b.cells]))
                for c, val in b.cells.items():
                    if val is not None:
                        self.solver.add_assertion(Equals(self.x[c], Int(val)))

        def solve(self):
            if not self.solver.solve():
                return None
            return [[self.solver.get_value(self.x[(i, j)]).constant_value()
                     for j in range(self.size)] for i in range(self.size)]

    # R6
    def criar_sudoku(n):
        s = n * n
        linhas  = [path(n, (i, 0), (i, s - 1)) for i in range(s)]
        colunas = [path(n, (0, j), (s - 1, j)) for j in range(s)]
        blocos  = [cube(n, i, j) for i in range(n) for j in range(n)]
        return linhas + colunas + blocos + [box_aleatorio(n)]

    N = 3
    m = model(N)
    m.add_groups(*criar_sudoku(N))
    print_matriz(N, m.solve())
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
