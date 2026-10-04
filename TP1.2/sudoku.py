import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from pysmt.shortcuts import Symbol, Solver, And, LE, GE, Int, Equals, AllDifferent
    from pysmt.typing import INT
    import random
    from ortools.sat.python import cp_model

    return (
        AllDifferent,
        And,
        Equals,
        GE,
        INT,
        Int,
        LE,
        Solver,
        Symbol,
        cp_model,
        random,
    )


@app.cell
def _(
    AllDifferent,
    And,
    Equals,
    GE,
    INT,
    Int,
    LE,
    Solver,
    Symbol,
    cp_model,
    random,
):
    def print_matriz(n, m):
        w = len(str(n*n))
        for c in range(n*n):
            for d in range(n):
                print(' ', end='')
                for e in range(n):
                    print(f"{m[c][d * n + e]:{w}}", end=' ')
                if(d + 1 != n):
                    print('|', end='')
            if (c + 1) % n == 0 and c + 1 < n * n:   
                print('\n' + '_' * ((n+1)*n + (n-1) + (n*n*w)))
            else:
                print()

    # R1
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

    # R4

    def box_aleatorio(n, k=None):
        b = box(n)
        rep = k if k is not None else n
        todas_coord = [(i,j) for i in range(b.size) for j in range(b.size)]
        for i, j in random.sample(todas_coord, rep):
            b.add(i, j, random.randint(1,b.size))
        return b

    # R5
    class model:
        def __init__(self, n, solver=""):
            self.size = n * n
            self.box_inicial = None
            self.solver_name = solver
        
            if self.solver_name == "z3":
                self.solver = Solver(name="z3")
                self.x = {(i, j): Symbol(f"x_{i}_{j}", INT) for i in range(self.size) for j in range(self.size)}
                for s in self.x.values():
                    self.solver.add_assertion(And(GE(s, Int(1)), LE(s, Int(self.size))))   
            else:
                self.model = cp_model.CpModel()
                self.solver = cp_model.CpSolver()
                self.x = {
                    (i, j): self.model.NewIntVar(1, self.size, f"x_{i}_{j}")
                    for i in range(self.size)
                    for j in range(self.size)
                }
        
           

        def add_groups(self, boxes):
            for b in boxes:
                if self.solver_name == "z3":
                    if isinstance(b, (path, cube)):
                        self.solver.add_assertion(AllDifferent([self.x[c] for c in b.cells]))
                    else:
                        self.box_inicial = b
                    for c, val in b.cells.items():
                        if val is not None:
                            self.solver.add_assertion(Equals(self.x[c], Int(val)))
                else:
                    if isinstance(b, (path, cube)):
                        self.model.AddAllDifferent([self.x[c] for c in b.cells])
                    else:
                        self.box_inicial = b
                    for c, val in b.cells.items():
                        if val is not None:
                            self.model.Add(self.x[c] == val)

        def solve(self):
            if self.solver_name == "z3":
                if not self.solver.solve():
                    return None
                return [[self.solver.get_value(self.x[(i, j)]).constant_value()
                         for j in range(self.size)] for i in range(self.size)]
            else:
                status = self.solver.Solve(self.model)
                if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                    return [[self.solver.Value(self.x[(i,j)]) for j in range(self.size)] for i in range(self.size)]
                else:
                    return None

        def imprime_box_aleatorio(self, N):
            print("Pista aleatória")
            print_matriz(N, self.box_inicial.to_matrix())
            print()


    # R6
    def criar_sudoku(n):
        s = n * n
        linhas  = [path(n, (i, 0), (i, s - 1)) for i in range(s)]
        colunas = [path(n, (0, j), (s - 1, j)) for j in range(s)]
        blocos  = [cube(n, i, j) for i in range(n) for j in range(n)]
        return linhas + colunas + blocos + [box_aleatorio(n)]


    return criar_sudoku, model, print_matriz


@app.function
def verificar_sudoku(n, sudoku, box):
    ok = True
    size = n*n
    # verificar linhas e colunas
    for c in range(size):
        linhas = []
        colunas = []
        for d in range(size):
            # linhas
            if (co := sudoku[c][d]) in linhas:
                print(f"Valor {co} repetido na linha {c}")
                ok = False
            linhas.append(co)
    
            # colunas
            if (li := sudoku[d][c]) in colunas:
                print(f"Valor {li} repetido na coluna {c}")
                ok = False
            colunas.append(li)

    # cubes
    for c in range(n):
        for d in range(n):
            cube = []
            for e in range(n):
                for f in range(n):
                    if (val := sudoku[e + c*n][f + d*n]) in cube:
                        print(f"Valor {val} repetido no cube {c*n + d}")
                        ok = False
                    cube.append(val)

    # verificar valores do box inicial
    for (i,j), val in box.cells.items():
        if val != (atual := sudoku[i][j]):
            print(f"Valor inicial {val}  nas coordenadas ({i},{j}) alterado para {atual}")
            ok = False

    # verificar se os valores do sudoku são válidos
    for c in range(size):
        for d in range(size):
            if not 1 <= (val := sudoku[c][d]) <= size:
                print(f"Valor {val} inválido em ({c},{d})")
                ok = False
                
    return ok


@app.cell
def _(criar_sudoku, model, print_matriz):
    N = 3
    m = model(N)
    m.add_groups(criar_sudoku(N))
    m.imprime_box_aleatorio(N)
    sudoku = m.solve()
    if sudoku is not None:
        print("Solução")
        print_matriz(N, sudoku)
        if verificar_sudoku(N, sudoku, m.box_inicial):
            print("Sudoku sem valores repetidos")
    else:
        print("Sem solução")
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
