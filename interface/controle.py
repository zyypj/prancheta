from rich.table import Table

from config import ESTILOS, MAX_SUBSTITUICOES, NOMES_ESTILOS
from interface.campo import barra, mostrar_partida
from interface.entrada import console, ler_opcao, limpar, pausar
from partida.lances import ACOES, CANTOS, DEFESAS, DESCRICAO_ZONAS, FORCAS_PENALTI, NOMES_ACOES, NOMES_DEFESAS, \
    fazer_substituicao, outro
from partida.simulacao import CONTROLE_IA

DESENHO_GOL = (
    "  ┌───────────────────────────────┐",
    "  │    1          2          3    │",
    "  │   ESQ        MEIO       DIR   │",
    "  └───────────────────────────────┘",
)


def escolher_no_campo(partida, time_id, pergunta, nomes):
    while True:
        mostrar_partida(partida, time_id, pergunta=pergunta, opcoes=nomes)
        escolha = ler_opcao(0, len(nomes))
        if escolha:
            return escolha - 1
        menu_pausa(partida, time_id)
        if partida["modo"] == "simular":
            return None


def humano_ataque(partida, time_id, zona, portador):
    if partida["modo"] == "simular":
        return CONTROLE_IA["ataque"](partida, time_id, zona, portador)
    acoes = ACOES[zona]
    local = DESCRICAO_ZONAS[zona]
    indice = escolher_no_campo(partida, time_id, f"{portador['nome']} está com a bola {local}. O que fazer?",
                               [NOMES_ACOES[a] for a in acoes])
    if indice is None:
        return CONTROLE_IA["ataque"](partida, time_id, zona, portador)
    return acoes[indice]


def humano_defesa(partida, time_id):
    if partida["modo"] == "simular":
        return CONTROLE_IA["defesa"](partida, time_id)
    adversario = partida["times"][outro(partida, time_id)]
    indice = escolher_no_campo(partida, time_id, f"O {adversario['nome']} vai atacar. Como defender?",
                               [NOMES_DEFESAS[d] for d in DEFESAS])
    if indice is None:
        return CONTROLE_IA["defesa"](partida, time_id)
    return DEFESAS[indice]


def humano_escolha(partida, time_id, pergunta, opcoes):
    if partida["modo"] == "simular":
        return CONTROLE_IA["escolha"](partida, time_id, pergunta, opcoes)
    indice = escolher_no_campo(partida, time_id, pergunta, [nome for _, nome, _ in opcoes])
    if indice is None:
        return CONTROLE_IA["escolha"](partida, time_id, pergunta, opcoes)
    return opcoes[indice][0]


def tela_penalti(partida, time_id, titulo):
    mostrar_partida(partida, time_id)
    console.print(f"\n [bold yellow]{titulo}[/]")
    for linha in DESENHO_GOL:
        console.print(linha)


def humano_bater_penalti(partida, time_id, batedor, goleiro):
    nome_goleiro = goleiro["nome"] if goleiro else "ninguém"
    tela_penalti(partida, time_id, f"PÊNALTI A FAVOR! {batedor['nome']} contra {nome_goleiro}.")
    canto = CANTOS[ler_opcao(1, 3, " Canto (1-3) > ") - 1]
    console.print(" [bold]1[/] Colocado (quase nunca sai)   [bold]2[/] Forte (difícil de pegar, pode ir pra fora)")
    forca = FORCAS_PENALTI[ler_opcao(1, 2, " Força > ") - 1]
    return canto, forca


def humano_defender_penalti(partida, time_id, batedor, goleiro):
    nome_goleiro = goleiro["nome"] if goleiro else "o goleiro improvisado"
    tela_penalti(partida, time_id, f"PÊNALTI CONTRA! {batedor['nome']} na bola. Para onde {nome_goleiro} pula?")
    return CANTOS[ler_opcao(1, 3, " Canto (1-3) > ") - 1]


def tabela_jogadores(jogadores, titulo):
    tabela = Table(title=titulo, title_style="bold", header_style="bold")
    for coluna in ("#", "Jogador", "Pos", "Qual", "Energia"):
        tabela.add_column(coluna)
    for numero, jogador in enumerate(jogadores, start=1):
        tabela.add_row(str(numero), jogador["nome"], jogador["pos"], str(jogador["qualidade"]),
                       barra(jogador["energia"]))
    return tabela


def escolher_entrada(time, mensagem):
    if not time["banco"] or time["subs"] >= MAX_SUBSTITUICOES:
        console.print(" [red]Sem substituições disponíveis.[/]")
        pausar("Enter para continuar...")
        return None
    limpar()
    console.print(tabela_jogadores(time["banco"], mensagem))
    console.print(" [bold]0[/] Cancelar")
    escolha = ler_opcao(0, len(time["banco"]))
    return time["banco"][escolha - 1] if escolha else None


def humano_lesao(partida, time_id, lesionado):
    time = partida["times"][time_id]
    mostrar_partida(partida, time_id, pergunta=f"{lesionado['nome']} saiu de campo e não pode voltar.")
    pausado = partida.get("em_pausa", False)
    partida["em_pausa"] = True
    entra = escolher_entrada(time, f"Quem entra no lugar de {lesionado['nome']}?")
    if entra:
        fazer_substituicao(partida, time_id, None, entra["id"], lesionado["nome"])
    partida["em_pausa"] = pausado


def menu_substituicao(partida, time_id):
    time = partida["times"][time_id]
    mensagem = ""
    while True:
        limpar()
        if mensagem:
            console.print(f" [green]{mensagem}[/]\n")
        if time["subs"] >= MAX_SUBSTITUICOES or not time["banco"]:
            console.print(" [red]Sem substituições disponíveis.[/]")
            pausar("Enter para voltar à pausa...")
            return
        console.print(
            tabela_jogadores(time["em_campo"], f"Em campo ({time['subs']}/{MAX_SUBSTITUICOES} substituições)"))
        console.print(" [bold]0[/] Voltar à pausa")
        escolha = ler_opcao(0, len(time["em_campo"]), " Quem sai? > ")
        if not escolha:
            return
        sai = time["em_campo"][escolha - 1]
        entra = escolher_entrada(time, f"Quem entra no lugar de {sai['nome']}?")
        if entra and fazer_substituicao(partida, time_id, sai["id"], entra["id"]):
            mensagem = f"Saiu {sai['nome']}, entrou {entra['nome']} ({time['subs']}/{MAX_SUBSTITUICOES})."
        else:
            mensagem = ""


def menu_plano_partida(partida, time_id):
    plano = partida["times"][time_id]["plano"]
    console.print(" [bold]1[/] Estilo   [bold]2[/] Ofensividade   [bold]3[/] Intensidade   [bold]0[/] Voltar")
    escolha = ler_opcao(0, 3)
    if escolha == 1:
        console.print(" " + "   ".join(
            f"[bold]{n}[/] {NOMES_ESTILOS[e]}" for n, e in enumerate(ESTILOS, start=1)) + "   [bold]0[/] Voltar")
        novo = ler_opcao(0, len(ESTILOS))
        if novo:
            plano["estilo"] = ESTILOS[novo - 1]
    elif escolha == 2:
        plano["ofensividade"] = ler_opcao(0, 5, " Ofensividade (1 retranca a 5 tudo ao ataque, 0 mantém) > ") or plano[
            "ofensividade"]
    elif escolha == 3:
        plano["intensidade"] = ler_opcao(0, 5, " Intensidade (1 a 5, 0 mantém) > ") or plano["intensidade"]


def mostrar_estatisticas(partida):
    tabela = Table(header_style="bold")
    casa = partida["times"][partida["casa"]]
    fora = partida["times"][partida["fora"]]
    total = max(1, casa["posse"] + fora["posse"])
    tabela.add_column("")
    tabela.add_column(casa["sigla"], justify="center")
    tabela.add_column(fora["sigla"], justify="center")
    tabela.add_row("Posse", f"{round(100 * casa['posse'] / total)}%", f"{round(100 * fora['posse'] / total)}%")
    tabela.add_row("Finalizações", str(casa["chutes"]), str(fora["chutes"]))
    tabela.add_row("No alvo", str(casa["no_alvo"]), str(fora["no_alvo"]))
    tabela.add_row("Faltas", str(casa["faltas"]), str(fora["faltas"]))
    console.print(tabela)


def menu_pausa(partida, time_id, motivo="pausa"):
    partida["em_pausa"] = True
    try:
        opcoes_da_pausa(partida, time_id, motivo)
    finally:
        partida["em_pausa"] = False


def opcoes_da_pausa(partida, time_id, motivo):
    titulos = {"intervalo": "INTERVALO", "expulsao": "EXPULSÃO! Jogo parado.", "pausa": "JOGO PAUSADO"}
    while True:
        mostrar_partida(partida, time_id, pergunta=titulos.get(motivo, "JOGO PAUSADO"))
        if motivo == "intervalo":
            mostrar_estatisticas(partida)
        outro_modo = "Simular o resto" if partida["modo"] == "jogar" else "Assumir o controle (lance a lance)"
        velocidade = "automático rápido" if partida["velocidade"] == "normal" else "manual (Enter)"
        console.print(
            f" [bold]1[/] Continuar   [bold]2[/] Substituição   [bold]3[/] Mudar plano   "
            f"[bold]4[/] {outro_modo}   [bold]5[/] Avanço {velocidade}"
        )
        escolha = ler_opcao(1, 5)
        if escolha == 1:
            return
        if escolha == 2:
            menu_substituicao(partida, time_id)
        elif escolha == 3:
            menu_plano_partida(partida, time_id)
        elif escolha == 4:
            partida["modo"] = "simular" if partida["modo"] == "jogar" else "jogar"
        else:
            partida["velocidade"] = "rapida" if partida["velocidade"] == "normal" else "normal"


def humano_pausa(partida, time_id, motivo):
    menu_pausa(partida, time_id, motivo)


def humano_ajuste(partida, time_id):
    return None


CONTROLE_HUMANO = {
    "ataque": humano_ataque,
    "defesa": humano_defesa,
    "escolha": humano_escolha,
    "bater_penalti": humano_bater_penalti,
    "defender_penalti": humano_defender_penalti,
    "lesao": humano_lesao,
    "pausa": humano_pausa,
    "ajuste": humano_ajuste,
}
