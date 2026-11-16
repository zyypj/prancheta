from rich.table import Table

from config import ESTILOS, MAX_SUBSTITUICOES, NOMES_ESTILOS
from elenco.escalacao import rotulo
from elenco.substituicoes import sugerir_substituicoes
from interface.campo import barra, mostrar_partida
from interface.entrada import console, ler_opcao, ler_opcao_ou_letra, limpar, pausar
from partida.lances import (
    ACOES,
    CANTOS,
    DEFESAS,
    DESCRICAO_ZONAS,
    FORCAS_PENALTI,
    NOMES_ACOES,
    NOMES_DEFESAS,
    fazer_substituicao,
    outro,
)
from partida.simulacao import CONTROLE_IA

DESENHO_GOL = (
    "  ┌───────────────────────────────┐",
    "  │    1          2          3    │",
    "  │   ESQ        MEIO       DIR   │",
    "  └───────────────────────────────┘",
)


def revelar_chance(partida, time_id, nomes, chances, reveladas):
    """
    Gasta uma revelação para mostrar a chance de uma opção escolhida pelo jogador.

    Pergunta qual opção revelar; se ela ainda não foi revelada, desconta uma revelação do time e guarda a
    chance em reveladas.

    Args:
        partida (dict): Estado da partida em andamento.
        time_id (str): Identificador do clube do jogador.
        nomes (list): Textos das opções.
        chances (list[float]): Chance de cada opção dar certo, entre 0 e 1.
        reveladas (dict): Chances já reveladas nesta pergunta, por índice da opção; é atualizado.
    """
    indice = ler_opcao(1, len(nomes), " Revelar a chance de qual opção? > ") - 1
    if indice in reveladas:
        return
    partida["revelacoes"][time_id] -= 1
    reveladas[indice] = chances[indice]


def escolher_no_campo(partida, time_id, pergunta, nomes, chances=None):
    """
    Pergunta ao jogador uma opção com o campo da partida na tela.

    Mostra o campo com a pergunta e as opções numeradas. Quando a pergunta tem as chances de cada opção e o
    time ainda tem revelações, aparece a opção R: o jogador escolhe uma única opção para ver a porcentagem
    dela, que fica ao lado do nome, e depois escolhe o que fazer. Se o usuário digitar 0, abre o menu de
    pausa; ao voltar, se ele tiver passado a partida para simulação, desiste da pergunta, e senão pergunta de
    novo.

    Args:
        partida (dict): Estado da partida em andamento.
        time_id (str): Identificador do clube do jogador.
        pergunta (str): Texto da pergunta.
        nomes (list): Textos das opções, na ordem em que aparecem.
        chances (list[float] | None): Chance de cada opção dar certo, entre 0 e 1, ou None se a pergunta não
            permite revelação. Padrão None.

    Returns:
        int | None: Índice da opção escolhida, começando em 0, ou None se a partida passou a ser simulada.
    """
    reveladas = {}
    while True:
        restantes = partida.get("revelacoes", {}).get(time_id, 0)
        pode_revelar = bool(chances) and restantes > 0 and len(reveladas) < len(nomes)
        rotulos = [
            f"{nome} [bold cyan]({round(reveladas[indice] * 100)}%)[/]" if indice in reveladas else nome
            for indice, nome in enumerate(nomes)
        ]
        rodape = (
            f"[bold]R[/] Revelar chance ({restantes}) [dim]· em chutes, é a chance de gol[/]" if pode_revelar else None
        )
        mostrar_partida(partida, time_id, pergunta=pergunta, opcoes=rotulos, rodape=rodape)
        escolha = ler_opcao_ou_letra(0, len(nomes), ("r",) if pode_revelar else ())
        if escolha == "r":
            revelar_chance(partida, time_id, nomes, chances, reveladas)
            continue
        if escolha:
            return escolha - 1
        menu_pausa(partida, time_id)
        if partida["modo"] == "simular":
            return None


def humano_ataque(partida, time_id, zona, portador):
    """
    Deixa o jogador escolher a jogada de ataque de quem está com a bola.

    Mostra as ações possíveis na zona em que a bola está, como tocar, driblar, cruzar ou chutar, com as
    chances calculadas pelo motor para as revelações. Quando a partida está sendo simulada, ou o jogador passa
    a simular durante a pergunta, a decisão fica com o controle da IA.

    Args:
        partida (dict): Estado da partida em andamento.
        time_id (str): Identificador do clube do jogador.
        zona (str): Zona do campo onde está a bola: meio, ataque ou area.
        portador (dict): Jogador que está com a bola.

    Returns:
        str: Chave da ação de ataque escolhida.
    """
    if partida["modo"] == "simular":
        return CONTROLE_IA["ataque"](partida, time_id, zona, portador)
    acoes = ACOES[zona]
    local = DESCRICAO_ZONAS[zona]
    chances_da_vez = partida.get("chances")
    chances = [chances_da_vez[a] for a in acoes] if chances_da_vez else None
    indice = escolher_no_campo(
        partida,
        time_id,
        f"{rotulo(portador)} está com a bola {local}. O que fazer?",
        [NOMES_ACOES[a] for a in acoes],
        chances,
    )
    if indice is None:
        return CONTROLE_IA["ataque"](partida, time_id, zona, portador)
    return acoes[indice]


def humano_defesa(partida, time_id):
    """
    Deixa o jogador escolher como defender o próximo ataque do adversário.

    Mostra as defesas possíveis, como dar o bote, pressão alta ou recuar. Quando a partida está sendo
    simulada, ou o jogador passa a simular durante a pergunta, a decisão fica com o controle da IA.

    Args:
        partida (dict): Estado da partida em andamento.
        time_id (str): Identificador do clube do jogador.

    Returns:
        str: Chave da defesa escolhida.
    """
    if partida["modo"] == "simular":
        return CONTROLE_IA["defesa"](partida, time_id)
    adversario = partida["times"][outro(partida, time_id)]
    indice = escolher_no_campo(
        partida, time_id, f"O {adversario['nome']} vai atacar. Como defender?", [NOMES_DEFESAS[d] for d in DEFESAS]
    )
    if indice is None:
        return CONTROLE_IA["defesa"](partida, time_id)
    return DEFESAS[indice]


def humano_escolha(partida, time_id, pergunta, opcoes):
    """
    Deixa o jogador responder a uma pergunta genérica do lance.

    Mostra os nomes das opções no campo. Quando a partida está sendo simulada, ou o jogador passa a simular
    durante a pergunta, a decisão fica com o controle da IA, que sorteia pelos pesos.

    Args:
        partida (dict): Estado da partida em andamento.
        time_id (str): Identificador do clube do jogador.
        pergunta (str): Texto da pergunta.
        opcoes (list): Tuplas (chave, nome, peso) de cada opção, ou (chave, nome, peso, chance) quando a
            chance pode ser revelada.

    Returns:
        str: Chave da opção escolhida.
    """
    if partida["modo"] == "simular":
        return CONTROLE_IA["escolha"](partida, time_id, pergunta, opcoes)
    chances = [opcao[3] for opcao in opcoes] if all(len(opcao) > 3 for opcao in opcoes) else None
    indice = escolher_no_campo(partida, time_id, pergunta, [opcao[1] for opcao in opcoes], chances)
    if indice is None:
        return CONTROLE_IA["escolha"](partida, time_id, pergunta, opcoes)
    return opcoes[indice][0]


def tela_penalti(partida, time_id, titulo):
    """
    Mostra a tela de cobrança de pênalti.

    Exibe o campo da partida, o título da cobrança e o desenho do gol com os cantos numerados de 1 a 3.

    Args:
        partida (dict): Estado da partida em andamento.
        time_id (str): Identificador do clube do jogador.
        titulo (str): Texto que anuncia a cobrança.
    """
    mostrar_partida(partida, time_id)
    console.print(f"\n [bold yellow]{titulo}[/]")
    for linha in DESENHO_GOL:
        console.print(linha)


def humano_bater_penalti(partida, time_id, batedor, goleiro):
    """
    Deixa o jogador cobrar um pênalti a favor.

    Mostra a tela do pênalti e pede o canto (esquerda, meio ou direita) e a força da batida: colocado, que
    quase nunca sai, forte, que é difícil de pegar mas pode ir para fora, ou paradinha, que engana o goleiro
    a não ser que ele espere.

    Args:
        partida (dict): Estado da partida em andamento.
        time_id (str): Identificador do clube do jogador.
        batedor (dict): Jogador que vai cobrar.
        goleiro (dict | None): Goleiro adversário, ou None se não houver.

    Returns:
        tuple: Canto e força escolhidos.
    """
    nome_goleiro = rotulo(goleiro) if goleiro else "ninguém"
    tela_penalti(partida, time_id, f"PÊNALTI A FAVOR! {rotulo(batedor)} contra {nome_goleiro}.")
    canto = CANTOS[ler_opcao(1, 3, " Canto (1-3) > ") - 1]
    console.print(
        " [bold]1[/] Colocado (quase nunca sai)   [bold]2[/] Forte (difícil de pegar, pode ir pra fora)"
        "   [bold]3[/] Paradinha (engana o goleiro, mas ele pode esperar)"
    )
    forca = FORCAS_PENALTI[ler_opcao(1, 3, " Força > ") - 1]
    return canto, forca


def humano_defender_penalti(partida, time_id, batedor, goleiro):
    """
    Deixa o jogador escolher para onde o goleiro pula num pênalti contra.

    Mostra a tela do pênalti e pede o canto do pulo, entre esquerda, meio e direita.

    Args:
        partida (dict): Estado da partida em andamento.
        time_id (str): Identificador do clube do jogador.
        batedor (dict): Jogador adversário que vai cobrar.
        goleiro (dict | None): Goleiro do jogador, ou None se o time estiver sem goleiro.

    Returns:
        str: Canto escolhido para o pulo.
    """
    nome_goleiro = rotulo(goleiro) if goleiro else "o goleiro improvisado"
    tela_penalti(partida, time_id, f"PÊNALTI CONTRA! {rotulo(batedor)} na bola. Para onde {nome_goleiro} pula?")
    return CANTOS[ler_opcao(1, 3, " Canto (1-3) > ") - 1]


def tabela_jogadores(jogadores, titulo):
    """
    Monta uma tabela numerada de jogadores.

    Cada linha mostra o número para escolha, o nome, a posição, a qualidade e a barra de energia.

    Args:
        jogadores (list): Jogadores a listar.
        titulo (str): Título da tabela.

    Returns:
        Table: Tabela do rich pronta para imprimir.
    """
    tabela = Table(title=titulo, title_style="bold", header_style="bold")
    for coluna in ("#", "Jogador", "Pos", "Qual", "Energia"):
        tabela.add_column(coluna)
    for numero, jogador in enumerate(jogadores, start=1):
        tabela.add_row(
            str(numero), jogador["nome"], jogador["pos"], str(jogador["qualidade"]), barra(jogador["energia"])
        )
    return tabela


def escolher_entrada(time, mensagem):
    """
    Pede ao jogador o reserva que vai entrar em campo.

    Se o banco estiver vazio ou o limite de substituições já tiver sido atingido, avisa e espera o Enter. Caso
    contrário, mostra a tabela do banco e deixa escolher um jogador ou cancelar com 0.

    Args:
        time (dict): Time do jogador na partida.
        mensagem (str): Título mostrado na tabela do banco.

    Returns:
        dict | None: Reserva escolhido, ou None se não houver substituição possível ou o usuário cancelar.
    """
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
    """
    Deixa o jogador repor um atleta que se lesionou.

    Avisa que o jogador saiu de campo e pede quem entra no lugar dele; se alguém for escolhido, faz a
    substituição. Enquanto isso a partida fica marcada como em pausa, e depois volta ao estado de pausa que
    tinha antes.

    Args:
        partida (dict): Estado da partida em andamento.
        time_id (str): Identificador do clube do jogador.
        lesionado (dict): Jogador que se lesionou.
    """
    time = partida["times"][time_id]
    mostrar_partida(partida, time_id, pergunta=f"{rotulo(lesionado)} saiu de campo e não pode voltar.")
    pausado = partida.get("em_pausa", False)
    partida["em_pausa"] = True
    entra = escolher_entrada(time, f"Quem entra no lugar de {rotulo(lesionado)}?")
    if entra:
        fazer_substituicao(partida, time_id, None, entra["id"], rotulo(lesionado))
    partida["em_pausa"] = pausado


def sugestoes_da_partida(partida, time_id):
    """
    Pede ao auxiliar as sugestões de substituição para o momento da partida.

    Args:
        partida (dict): Estado da partida em andamento.
        time_id (str): Identificador do clube do jogador.

    Returns:
        list[dict]: Sugestões, como em sugerir_substituicoes.
    """
    time = partida["times"][time_id]
    diferenca = time["gols"] - partida["times"][outro(partida, time_id)]["gols"]
    return sugerir_substituicoes(time, partida["minuto"], diferenca)


def texto_sugestao(sugestao):
    """
    Monta a linha de uma sugestão de substituição.

    Args:
        sugestao (dict): Sugestão com quem sai, quem entra e o motivo.

    Returns:
        str: Linha com marcação do rich.
    """
    return f"sai {rotulo(sugestao['sai'])}, entra {rotulo(sugestao['entra'])} [dim]— {sugestao['motivo']}[/]"


def menu_substituicao(partida, time_id):
    """
    Abre o menu de substituições durante a pausa.

    Mostra os jogadores em campo e o número de substituições feitas, pede quem sai e depois quem entra, e faz
    a troca. Repete até o usuário voltar com 0 ou até não haver mais substituições possíveis, mostrando o
    resultado da última troca no topo.

    Args:
        partida (dict): Estado da partida em andamento.
        time_id (str): Identificador do clube do jogador.
    """
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
            tabela_jogadores(time["em_campo"], f"Em campo ({time['subs']}/{MAX_SUBSTITUICOES} substituições)")
        )
        sugestoes = sugestoes_da_partida(partida, time_id)
        letras = "abc"[: len(sugestoes)]
        if sugestoes:
            console.print("\n [bold]Sugestões do auxiliar:[/]")
            for letra, sugestao in zip(letras, sugestoes):
                console.print(f"  [bold]{letra.upper()}[/] {texto_sugestao(sugestao)}")
        console.print("\n [bold]0[/] Voltar à pausa")
        rotulo_pergunta = " Quem sai? (número, ou a letra de uma sugestão) > " if sugestoes else " Quem sai? > "
        escolha = ler_opcao_ou_letra(0, len(time["em_campo"]), tuple(letras), rotulo_pergunta)
        if escolha in tuple(letras):
            sugestao = sugestoes[letras.index(escolha)]
            sai, entra = sugestao["sai"], sugestao["entra"]
            if fazer_substituicao(partida, time_id, sai["id"], entra["id"]):
                mensagem = f"Saiu {rotulo(sai)}, entrou {rotulo(entra)} ({time['subs']}/{MAX_SUBSTITUICOES})."
            continue
        if not escolha:
            return
        sai = time["em_campo"][escolha - 1]
        entra = escolher_entrada(time, f"Quem entra no lugar de {rotulo(sai)}?")
        if entra and fazer_substituicao(partida, time_id, sai["id"], entra["id"]):
            mensagem = f"Saiu {rotulo(sai)}, entrou {rotulo(entra)} ({time['subs']}/{MAX_SUBSTITUICOES})."
        else:
            mensagem = ""


def menu_plano_partida(partida, time_id):
    """
    Deixa o jogador mudar o plano de jogo durante a partida.

    O usuário escolhe mudar o estilo, a ofensividade ou a intensidade. O estilo vem de uma lista numerada, e a
    ofensividade e a intensidade vão de 1 a 5; digitar 0 mantém o valor atual.

    Args:
        partida (dict): Estado da partida em andamento.
        time_id (str): Identificador do clube do jogador.
    """
    plano = partida["times"][time_id]["plano"]
    console.print(" [bold]1[/] Estilo   [bold]2[/] Ofensividade   [bold]3[/] Intensidade   [bold]0[/] Voltar")
    escolha = ler_opcao(0, 3)
    if escolha == 1:
        console.print(
            " "
            + "   ".join(f"[bold]{n}[/] {NOMES_ESTILOS[e]}" for n, e in enumerate(ESTILOS, start=1))
            + "   [bold]0[/] Voltar"
        )
        novo = ler_opcao(0, len(ESTILOS))
        if novo:
            plano["estilo"] = ESTILOS[novo - 1]
    elif escolha == 2:
        plano["ofensividade"] = (
            ler_opcao(0, 5, " Ofensividade (1 retranca a 5 tudo ao ataque, 0 mantém) > ") or plano["ofensividade"]
        )
    elif escolha == 3:
        plano["intensidade"] = ler_opcao(0, 5, " Intensidade (1 a 5, 0 mantém) > ") or plano["intensidade"]


def mostrar_estatisticas(partida):
    """
    Exibe as estatísticas da partida dos dois times.

    Mostra uma tabela com a posse de bola em porcentagem, as finalizações, as finalizações no alvo e as faltas
    de cada time.

    Args:
        partida (dict): Estado da partida em andamento.
    """
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
    """
    Pausa a partida e abre as opções da pausa.

    Marca a partida como em pausa enquanto o menu está aberto e desmarca ao sair, mesmo se ocorrer um erro.

    Args:
        partida (dict): Estado da partida em andamento.
        time_id (str): Identificador do clube do jogador.
        motivo (str): Motivo da pausa: pausa, intervalo ou expulsao. Padrão "pausa".
    """
    partida["em_pausa"] = True
    try:
        opcoes_da_pausa(partida, time_id, motivo)
    finally:
        partida["em_pausa"] = False


def opcoes_da_pausa(partida, time_id, motivo):
    """
    Mostra o menu da pausa até o jogador decidir continuar.

    Exibe o campo com o título conforme o motivo e, no intervalo, as estatísticas. O usuário pode continuar,
    fazer substituição, mudar o plano, alternar entre jogar lance a lance e simular o resto, e alternar o
    avanço entre manual (Enter) e automático rápido.

    Args:
        partida (dict): Estado da partida em andamento.
        time_id (str): Identificador do clube do jogador.
        motivo (str): Motivo da pausa: pausa, intervalo ou expulsao.
    """
    titulos = {"intervalo": "INTERVALO", "expulsao": "EXPULSÃO! Jogo parado.", "pausa": "JOGO PAUSADO"}
    while True:
        mostrar_partida(partida, time_id, pergunta=titulos.get(motivo, "JOGO PAUSADO"))
        if motivo == "intervalo":
            mostrar_estatisticas(partida)
        sugestoes = sugestoes_da_partida(partida, time_id)
        if sugestoes:
            console.print(f" [yellow]Auxiliar sugere:[/] {texto_sugestao(sugestoes[0])}")
            if len(sugestoes) > 1:
                console.print(f" [dim]Mais {len(sugestoes) - 1} sugestão(ões) em Substituição.[/]")
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
    """
    Abre o menu de pausa quando a partida para, como no intervalo ou numa expulsão.

    Args:
        partida (dict): Estado da partida em andamento.
        time_id (str): Identificador do clube do jogador.
        motivo (str): Motivo da parada: intervalo ou expulsao.
    """
    menu_pausa(partida, time_id, motivo)


def humano_ajuste(partida, time_id):
    """
    Não faz ajustes automáticos, pois o jogador humano muda o time pelo menu de pausa.

    Args:
        partida (dict): Estado da partida em andamento.
        time_id (str): Identificador do clube do jogador.
    """
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
