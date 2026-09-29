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
    from ortools.sat.python import cp_model


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

    modelo = cp_model.CpModel()
    variaveis = {}

    for t in turma:
        for c in range(len(disciplinas)):
            for d in dia:
                for p in periodo:
                    nome = f"{t}_{disciplinas['disciplina'][c]}_{d}_{p}"
                    variaveis[(t, disciplinas['disciplina'][c], d, p)] = modelo.NewIntVar(0, 1, nome)


    # R1
    for t in turma:
        for d in dia:
            for p in periodo:
                # Recolhe todas as disciplinas desta turma neste dia e período
                aulas_no_tempo = [variaveis[(t, disciplinas['disciplina'][c], d, p)] for c in range(len(disciplinas))]
                modelo.Add(sum(aulas_no_tempo) <= 1)

    # R2
    for t in turma:
        for c in range(len(disciplinas)):
            disc = disciplinas['disciplina'][c]
            carga = int(disciplinas['carga_semanal'][c])
            soma_semanal = sum(variaveis[(t, disc, d, p)] for d in dia for p in periodo)
            modelo.Add(soma_semanal == carga)

    for t in turma:
        for c in range(len(disciplinas)):
            disciplina_analizar = disciplinas["disciplina"][c]
            e_duplo = str(disciplinas["duplo_periodo"][c]).strip().lower() == "sim"

            for d in dia:
                vars_dia = [variaveis[(t, disciplina_analizar, d, p)] for p in periodo]

                if not e_duplo:
                    modelo.Add(sum(vars_dia) <= 1)
                else:
                    # O CP-SAT permite forçar que os 5 períodos do dia correspondam a um padrão exato
                    padroes_validos = [
                        [0, 0, 0, 0, 0], # Zero aulas
                        [1, 1, 0, 0, 0], # Aulas nos tempos 1 e 2
                        [0, 1, 1, 0, 0], # Aulas nos tempos 2 e 3
                        [0, 0, 1, 1, 0], # Aulas nos tempos 3 e 4
                        [0, 0, 0, 1, 1]  # Aulas nos tempos 4 e 5
                    ]
                    modelo.AddAllowedAssignments(vars_dia, padroes_validos)

    disciplinas_por_professor = {}
    for i in range(len(disciplinas)):
        prof = disciplinas["professor"][i]
        disc = disciplinas["disciplina"][i]

        if prof not in disciplinas_por_professor:
            disciplinas_por_professor[prof] = []

        disciplinas_por_professor[prof].append(disc)

    # R5
    for prof, discs in disciplinas_por_professor.items():
        for d in dia:
            for p in periodo:
                aulas_prof = []
                for disc in discs:
                    for t in turma:
                        aulas_prof.append(variaveis[(t, disc, d, p)])
                modelo.Add(sum(aulas_prof) <= 1)
    #R6
    for i in range(len(disponibilidade_execoes)):
        # Lemos o professor, dia e período do DataFrame
        prof_indisponivel = str(disponibilidade_execoes["professor"][i]).strip()
        dia_indisp = str(disponibilidade_execoes["dia"][i]).strip()
        periodo_indisp = int(disponibilidade_execoes["periodo"][i]) 

        # 1. Procurar nas disciplinas quais são dadas por este professor
        for c in range(len(disciplinas)):
            prof_da_disciplina = str(disciplinas["professor"][c]).strip()

            if prof_da_disciplina == prof_indisponivel:
                disciplina_do_prof = disciplinas["disciplina"][c]

                # 2. Bloquear esta aula para TODAS as turmas nesse tempo
                for t in turma:  
                    v = variaveis[(t, disciplina_do_prof, dia_indisp, periodo_indisp)]
                    modelo.Add(v == 0) # Força a variável a 0 (Falso)



    # R7 - Capacidade das Salas
    for d in dia:
        for p in periodo:

            for idx_sala in range(len(salas)):
                tipo_sala_atual = salas.loc[idx_sala, "tipo"]
                capacidade_maxima = int(salas.loc[idx_sala, "quantidade"])

                # Lista para guardar as variáveis das disciplinas que usam ESTA sala, NESTE tempo
                aulas_a_decorrer_neste_tipo_de_sala = []

                for disci in range(len(disciplinas)):
                    # 1. Ver qual a sala que esta disciplina exige
                    tipo_sala_disci = str(disciplinas.loc[disci, "sala_especial"]).strip()
    
                    if not tipo_sala_disci or tipo_sala_disci.lower() == "nan":
                        tipo_sala_disci = "normal"
    
                    # 2. Se a disciplina precisar DESTE tipo de sala
                    if tipo_sala_disci == tipo_sala_atual:
                        disciplina_nome = disciplinas.loc[disci, "disciplina"]
        
                        for t in turma:            
                            v = variaveis[(t, disciplina_nome, d, p)]
                            aulas_a_decorrer_neste_tipo_de_sala.append(v)


                if len(aulas_a_decorrer_neste_tipo_de_sala) > 0:
                    # A soma das variáveis (1 ou 0) não pode exceder o número de salas
                    modelo.Add(sum(aulas_a_decorrer_neste_tipo_de_sala) <= capacidade_maxima)



    def imprimir_horarios(solver, variaveis, turma, dia, periodo, disciplinas):
        # Definir uma largura maior para a coluna para caber "Disciplina (Professor)"
        largura_col = 12

        # Iterar por cada turma para desenhar a sua tabela
        for t in turma:
            print(f"\n{'='*110}")
            print(f" HORÁRIO DA TURMA: {t}")
            print(f"{'='*75}")

            # Desenhar o cabeçalho com os dias da semana
            cabecalho = f"{'Período':<10}"
            for d in dia:
                cabecalho += f"| {d:<{largura_col}}"
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
    
                        # solver.Value(v) devolve 1 se o solver decidiu colocar a aula aqui
                        if solver.Value(v) == 1:
                            aula_neste_tempo = disciplina_nome
                            break  # Já encontrámos a aula

                    linha += f"| {aula_neste_tempo[:11]:<12}"

                print(linha)
            
    def imprimir_horarios_professores(solver, variaveis, turma, dia, periodo, disciplinas_por_professor):
        # Definir uma largura de coluna um pouco maior para caber "Turma (Disciplina)"
        largura_col = 16 

        # Iterar por cada professor
        for prof, discs in disciplinas_por_professor.items():
            print(f"\n{'='*110}")
            print(f" HORÁRIO DO PROFESSOR: {prof}")
            print(f"{'='*75}")

            # Desenhar o cabeçalho com os dias da semana
            cabecalho = f"{'Período':<10}"
            for d in dia:
                cabecalho += f"| {d:<{largura_col}}"
            print(cabecalho)
            print("-" * len(cabecalho))

            # Desenhar cada linha de período
            for p in periodo:
                linha = f"{p:<10}"

                for d in dia:
                    aula_neste_tempo = "---"  # Por omissão, o tempo está livre

                    # Procura nas disciplinas que este professor dá
                    for disc in discs:
                        # Verifica em qual turma ele está a dar esta disciplina neste momento
                        for t in turma:
                            v = variaveis[(t, disc, d, p)]
                        
                            if solver.Value(v) == 1:
                                # Formata como "7ºA (Mat)"
                                aula_neste_tempo = f"{t} ({disc[:3]})" 
                                break  # Já encontrámos a aula para este tempo
                            
                        if aula_neste_tempo != "---":
                            break # Se já encontrou a turma, passa para o próximo dia

                    # [:largura_col-1] garante que o texto não desalinha a tabela se for muito grande
                    linha += f"| {aula_neste_tempo[:largura_col-1]:<{largura_col}}"

                print(linha)
    solver = cp_model.CpSolver()
    resultado = solver.Solve(modelo)

    # O CP-SAT retorna status específicos que devem ser validados
    if resultado == cp_model.OPTIMAL or resultado == cp_model.FEASIBLE:
        print("Solução encontrada com sucesso!\n")
        # Passamos 'solver' em vez do antigo 's'
        imprimir_horarios(solver, variaveis, turma, dia, periodo, disciplinas)
        imprimir_horarios_professores(solver, variaveis, turma, dia, periodo, disciplinas_por_professor)
    else:
        print("O problema não tem solução (UNSAT). Verifique se as restrições são possíveis.")
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
