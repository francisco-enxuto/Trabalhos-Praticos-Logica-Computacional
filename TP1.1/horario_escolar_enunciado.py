# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "marimo>=0.24.2",
# ]
# ///

import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md(r"""
    # Trabalho Prático: Gerador de Horário Escolar

    ## Contexto

    Uma escola precisa de gerar automaticamente o horário semanal de um
    conjunto de turmas, respeitando a carga letiva de cada disciplina, a
    disponibilidade dos professores e as salas (normais e especiais,
    partilhadas e em número limitado). Além disso, a escola quer poder
    reagir rapidamente a pequenas alterações de recursos (um professor
    fica indisponível, uma sala avaria, entra uma turma nova) sem ter de
    recomeçar o planeamento do zero.

    Este é um problema de **satisfação e otimização de restrições**
    (CSP/CP). Cabe-te a ti escolher e justificar a técnica de modelação
    e as ferramentas — o enunciado não fornece código de modelação nem
    de apresentação de resultados.

    ## Objetivo

    Construir, num ou mais notebooks Marimo, um sistema que:

    1. importa os dados de entrada de ficheiros (secção "Dados de
       entrada"),
    2. gera um horário que respeite os **requisitos obrigatórios**
       (secção seguinte) e otimize o **objetivo** (buracos),
    3. seja capaz de, a partir de um horário já gerado, produzir
       eficientemente um novo horário válido quando os recursos mudam
       ligeiramente (secção "Construção incremental").

    O código, a escolha de bibliotecas (OR-Tools/CP-SAT é a sugestão da
    disciplina, mas podes justificar outra abordagem), a forma de
    importar os dados e a forma de apresentar os resultados são
    decisões tuas — ver secção "O que é deixado ao teu critério".
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Dados de entrada

    Os dados de exemplo estão nos ficheiros CSV em `dados/`. O teu
    notebook **não pode ter os dados escritos diretamente no código**
    (nada de dicionários/listas Python com os valores) — tem de os ler
    destes ficheiros, e continuar a funcionar se estes forem
    substituídos por outro conjunto de dados no mesmo formato (mais
    turmas, mais disciplinas, outros professores, etc.).

    **`turmas.csv`** — uma turma por linha.

    | turma |
    |---|
    | 7ºA |
    | 7ºB |

    **`disciplinas.csv`** — currículo. `carga_semanal` é o número de
    tempos letivos por semana. `duplo_periodo` (`sim`/`nao`) indica que
    a disciplina tem de ser dada em blocos de 2 tempos consecutivos, no
    mesmo dia (ex.: uma disciplina com `carga_semanal=4` e
    `duplo_periodo=sim` corresponde a 2 blocos duplos por semana, em
    dias diferentes). `sala_especial`, quando preenchida, é o tipo de
    sala (ver `salas.csv`) que a disciplina exige; quando vazia, a
    disciplina usa uma sala normal qualquer.

    | disciplina | professor | carga_semanal | duplo_periodo | sala_especial |
    |---|---|---|---|---|
    | Matemática | Prof. Ana | 4 | nao | |
    | Português | Prof. Bruno | 4 | nao | |
    | Ciências | Prof. Carla | 3 | nao | Laboratório |
    | História | Prof. Diana | 2 | nao | |
    | Inglês | Prof. Diana | 2 | nao | |
    | Educação Física | Prof. Eduardo | 2 | sim | Ginásio |

    **`salas.csv`** — tipos de sala disponíveis e quantas existem em
    simultâneo. `tipo` é `normal` ou `especial`; para `especial`, o
    nome da sala liga-se ao `sala_especial` de `disciplinas.csv`.

    | sala | tipo | quantidade |
    |---|---|---|
    | Sala Normal | normal | 6 |
    | Laboratório | especial | 1 |
    | Ginásio | especial | 1 |

    **`disponibilidade_excecoes.csv`** — por omissão todos os
    professores estão disponíveis em todos os tempos da semana (5
    dias × 5 tempos); este ficheiro lista só as *exceções*, isto é, os
    (professor, dia, período) em que **não** estão disponíveis. `dia`
    usa `Seg`/`Ter`/`Qua`/`Qui`/`Sex`; `periodo` é 1 a 5.

    | professor | dia | periodo |
    |---|---|---|
    | Prof. Eduardo | Seg | 1 |
    | Prof. Eduardo | Seg | 2 |
    | Prof. Eduardo | Seg | 3 |
    | … | … | … |

    (o ficheiro completo lista o Prof. Eduardo como indisponível nos
    primeiros 3 tempos de todos os dias — só dá aulas nos últimos 2
    tempos de cada dia).
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Requisitos obrigatórios

    O horário gerado tem sempre de respeitar:

    - **R1.** Uma turma não pode ter duas aulas em simultâneo.
    - **R2.** Cada disciplina cumpre *exatamente* a carga semanal
      definida em `disciplinas.csv`, para cada turma.
    - **R3.** No máximo uma aula da mesma disciplina por dia, por
      turma — exceto disciplinas de duplo período (ver R4), em que o
      bloco de 2 tempos conta como uma só ocorrência nesse dia.
    - **R4.** Disciplinas marcadas `duplo_periodo=sim` só podem ser
      dadas em blocos de 2 tempos consecutivos, no mesmo dia (nunca um
      tempo isolado).
    - **R5.** Um professor não pode dar duas aulas em simultâneo, mesmo
      que sejam a turmas ou disciplinas diferentes.
    - **R6.** Um professor só pode dar aulas nos tempos em que está
      disponível (`disponibilidade_excecoes.csv`).
    - **R7.** Cada aula ocupa uma sala. Disciplinas com `sala_especial`
      só podem usar salas desse tipo; as restantes usam salas
      `normal`. Em nenhum tempo o número de aulas a decorrer num tipo
      de sala pode exceder a `quantidade` desse tipo definida em
      `salas.csv`.
    - **R8.** Os dados de entrada são sempre lidos dos ficheiros CSV —
      ver secção anterior — nunca escritos diretamente no código.

    ## Objetivo (a otimizar)

    - **O1.** Minimizar o número total de "buracos" no horário de cada
      professor — um buraco é um tempo livre, no meio do dia, entre a
      primeira e a última aula desse professor nesse dia.

    Não precisas de encontrar sempre a solução ótima de O1 — ver
    também os limites de tempo referidos em "Construção incremental".
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Construção incremental (R9)

    Numa escola real, o horário raramente é gerado do zero: é ajustado
    depois de já existir um, quando algum recurso muda ligeiramente.
    Resolver o problema completo outra vez, sempre que isso acontece,
    é caro e pode alterar aulas que não precisavam de mudar.

    - **R9.** O teu notebook tem de suportar o seguinte fluxo:
        1. Gerar um horário válido `H0` a partir de um conjunto de
           dados inicial (`dados/`).
        2. Dada uma pequena alteração aos recursos — por exemplo, a
           que está em `dados_v2/` (o Prof. Eduardo continua limitado
           às tardes, mas a Prof. Ana passa a estar indisponível às
           sextas-feiras nos 2 últimos tempos) — gerar um novo horário
           válido `H1` que respeite R1–R8 com os novos dados.
        3. `H1` deve ser produzido **de forma eficiente** (mais rápido
           do que resolver `H1` do zero, sem usar `H0`) e **minimizando
           o número de aulas que mudam de tempo/sala** entre `H0` e
           `H1` — `H1` não precisa de ser ótimo em relação a O1.

    Tens de justificar e demonstrar a tua abordagem (ex.: reaproveitar
    `H0` como ponto de partida/*hint* para o solver, fixar as partes do
    horário não afetadas pela mudança e resolver só o subproblema das
    turmas/professores/salas afetados, ou outra técnica à tua escolha).
    Deves apresentar evidência de que a tua construção incremental é de
    facto mais rápida e/ou muda menos aulas do que resolver `H1` do
    zero, para os dados fornecidos (ex.: medindo o tempo de execução e
    o número de aulas alteradas nos dois casos).

    Outros tipos de alteração de recursos que o teu notebook deve
    conseguir tratar da mesma forma (não precisas de ficheiros de dados
    para todos — basta que o teu código não assuma que só o cenário de
    `dados_v2/` pode acontecer):

    - um professor deixa de estar disponível nalguns tempos, ou fica
      disponível em mais tempos;
    - uma sala fica temporariamente indisponível (ex.: avaria);
    - uma turma nova é criada a meio do ano;
    - um professor é substituído por outro, na mesma disciplina.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## O que é deixado ao teu critério

    O enunciado define **o que** o horário tem de satisfazer, não
    **como** o deves implementar. Ficam ao teu critério, desde que
    justificadas no notebook:

    - a técnica e biblioteca de modelação (CP-SAT do OR-Tools é a
      sugestão da disciplina, mas és livre de escolher outra
      abordagem de Lógica Computacional, justificando a escolha);
    - a forma de ler e estruturar os dados dos ficheiros CSV (podes
      usar `pandas`, `csv` da biblioteca standard, ou outra forma —
      justifica a escolha se não usares pandas);
    - a forma de representar e apresentar o horário resultante (podes
      usar tabelas, texto, gráficos, `mo.ui` — o que achares mais
      claro).

    ## Como testar/validar

    - Escreve, no teu notebook ou num ficheiro de testes à parte, uma
      verificação automática de que um horário gerado respeita R1–R8
      (não precisa de ser exaustiva, mas cobre pelo menos um caso de
      cada restrição).
    - Corre o fluxo completo da secção "Construção incremental" com os
      dados fornecidos (`dados/` → `dados_v2/`) e mostra os resultados
      (tempo de execução, nº de aulas alteradas) diretamente no
      notebook.
    - Testa com pelo menos um conjunto de dados diferente do fornecido
      (mais uma turma, mais uma disciplina, outra exceção de
      disponibilidade) para confirmares que não há nada "hardcoded".



    ## Entrega

    - Começe por criar uma estrutura "Git" na directoria local  TP1.1 que vai conter todos os elenetos no trabalho. Se ainda não tiver crie um utilizador GitHub para onde deve enviar ("push") os "commits" locais. No GitHub  o repositório deve ser  "clonable" após a data de entrega do trabalho.
    - Relatório na forma de um ou mais notebooks Marimo; o notebook principal "horario_escolar.py" constrói-se editando o notebook anexo.
    - Versão PDF do relatório


    ## Extensões opcionais (bónus)

    - **Preferências dos professores**: acrescenta mais termos à
      função objetivo (ex.: penalizar aulas à primeira hora para quem
      prefere não ter).
    - **Escala**: mostra que a tua abordagem (incremental ou não)
      continua a funcionar com um número de turmas/professores bem
      maior do que o exemplo fornecido, e discute os limites que
      encontraste.
    """)
    return


if __name__ == "__main__":
    app.run()
