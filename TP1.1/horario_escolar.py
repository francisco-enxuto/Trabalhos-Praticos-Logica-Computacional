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
    from pysmt.shortcuts import Or,Symbol, LE, GE, Int, And, Equals, Plus, Solver, is_sat, get_model, Not, Ite
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

    for t in turma:
        for c in range(len(disciplinas)):
            disciplina_analizar = disciplinas["disciplina"][c]
    
            # Verifica se a disciplina é de duplo período (ajuste conforme o seu CSV)
            e_duplo = str(disciplinas["duplo_periodo"][c]).strip().lower() == "sim"

            for d in dia:
                # Recolhe as variáveis booleanas dos 5 períodos deste dia numa lista
                # Assumindo que periodo = [1, 2, 3, 4, 5]
                vars_dia = [variaveis[(t, disciplina_analizar, d, p)] for p in periodo]

                if not e_duplo:
                    # REGRA 3 (Período Simpl if notes): No máximo 1 aula por dia
                    aulas_no_dia = [Ite(v, Int(1), Int(0)) for v in vars_dia]
                    s.add_assertion(LE(Plus(aulas_no_dia), Int(1)))

                else:
                    # REGRAS 3 e 4 (Duplo Período): Exatamente 0 aulas OU 2 aulas consecutivas
            
                    # Padrão 1: Zero aulas neste dia
                    padrao_zero = And([Not(v) for v in vars_dia])
                    padroes_validos = [padrao_zero]
            
                    # Padrões de 2 aulas consecutivas
                    # Desliza uma "janela" de 2 períodos ao longo do dia
                    for i in range(len(periodo) - 1):
                        padrao_consecutivo = []
                        for j in range(len(periodo)):
                            if j == i or j == i + 1:
                                padrao_consecutivo.append(vars_dia[j]) # Aula ocorre
                            else:
                                padrao_consecutivo.append(Not(vars_dia[j])) # Aula não ocorre
                
                        padroes_validos.append(And(padrao_consecutivo))
            
                    # O dia obrigatoriamente tem de corresponder a UM dos padrões válidos
                    s.add_assertion(Or(padroes_validos))


    def imprimir_horarios(s, variaveis, turma, dia, periodo, disciplinas):
        # 1. Obter o modelo (a solução) do solver
        modelo = s.get_model()

        if modelo is None:
            print("Não foi possível gerar um horário (UNSAT).")
            return

        # 2. Iterar por cada turma para desenhar a sua tabela
        for t in turma:
            print(f"\n{'='*75}")
            print(f" HORÁRIO DA TURMA: {t}")
            print(f"{'='*75}")
    
            # Desenhar o cabeçalho com os dias da semana
            cabecalho = f"{'Período':<10}"
            for d in dia:
                cabecalho += f"| {d:<12}"
            print(cabecalho)
            print("-" * len(cabecalho))
    
            # Desenhar cada linha de período
            for p in periodo:
                linha = f"{p:<10}"
        
                for d in dia:
                    aula_neste_tempo = "---"  # Por omissão, o tempo está livre/vago
            
                    # Procura qual disciplina está marcada para este dia/período
                    for c in range(len(disciplinas)):
                        disciplina_nome = disciplinas["disciplina"][c]
                        v = variaveis[(t, disciplina_nome, d, p)]
                
                        # get_py_value devolve True se o solver decidiu colocar a aula aqui
                        if modelo.get_py_value(v):
                            aula_neste_tempo = disciplina_nome
                            break  # Já encontrámos a aula, não precisamos ver o resto das disciplinas
            
                    linha += f"| {aula_neste_tempo[:11]:<12}" # [:11] corta nomes muito grandes
            
                print(linha)
    disciplinas_por_professor = {}
 
    for i in range(len(disciplinas)):
        prof = disciplinas["professor"][i]
        disc = disciplinas["disciplina"][i]

        if prof not in disciplinas_por_professor:
            disciplinas_por_professor[prof] = []

        disciplinas_por_professor[prof].append(disc)

    # R5
    for prof, discs in disciplinas_por_professor.items():
        for i in range(len(discs)):
            for j in range(i, len(discs)):
                disc1 = discs[i]
                disc2 = discs[j]
                for t1 in turma:
                    for t2 in turma:
                        if t1 != t2:
                            for d in dia:
                                for p in periodo:
                                    var1 = variaveis[(t1, disc1, d, p)]
                                    var2 = variaveis[(t2, disc2, d, p)]
                                    s.add_assertion(Not(And(var1, var2)))
    resultado = s.solve()

    if resultado:
        print("Solução encontrada com sucesso!\n")
        imprimir_horarios(s, variaveis, turma, dia, periodo, disciplinas)
    else:
        print("O problema não tem solução (UNSAT). Verifique se as restrições são possíveis.")
    return


if __name__ == "__main__":
    app.run()
