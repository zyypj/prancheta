from rich.table import Table

from config import DIVISOES, NIVEIS, REPUTACAO_MAXIMA
from elenco.escalacao import rotulo
from interface.campo import barra
from interface.entrada import confirmar, console, ler_opcao, pausar
from interface.telas import titulo
from liga.carreira import situacao_na_nova_copa
from liga.temporada import clube_do_jogador, meta_do_clube, posicao_atual
from mercado.transferencias import dinheiro


def estrelas(reputacao):
    """
    Desenha a reputação do técnico como estrelas cheias e vazias.

    Args:
        reputacao (int): Reputação, de 0 a REPUTACAO_MAXIMA.

    Returns:
        str: Estrelas com marcação do rich.
    """
    return f"[yellow]{'★' * reputacao}[/][dim]{'☆' * (REPUTACAO_MAXIMA - reputacao)}[/]"


def mostrar_virada(estado, fechamento):
    """
    Mostra quem foi campeão de cada divisão, quem subiu, quem caiu e os prêmios do fim da temporada.

    Args:
        estado (dict): Estado da carreira.
        fechamento (dict): Resultado de fechar_divisoes.
    """
    titulo("SOBE E DESCE")
    nomes = estado["clubes"]
    for divisao, clube_id in fechamento["campeoes"].items():
        clube = nomes[clube_id]
        console.print(f" Campeão da {DIVISOES[divisao]}: [bold {clube['cor']}]{clube['nome']}[/]")
    if fechamento["subiram"]:
        console.print(
            "\n [green]Sobem para a Série A:[/] " + ", ".join(nomes[c]["nome"] for c in fechamento["subiram"])
        )
    if fechamento["cairam"]:
        console.print(" [red]Caem para a Série B:[/] " + ", ".join(nomes[c]["nome"] for c in fechamento["cairam"]))
    if fechamento["premios"]:
        console.print("\n [bold]Prêmios do campeonato:[/]")
        for linha in fechamento["premios"]:
            console.print(f"  • {linha}")
    meu = estado["clube_id"]
    if meu in fechamento["subiram"]:
        console.print("\n [bold green]Seu clube conquistou o acesso![/]")
    elif meu in fechamento["cairam"]:
        console.print("\n [bold red]Seu clube foi rebaixado.[/]")
    pausar("Enter para continuar...")


def mostrar_decisao(estado, decisao):
    """
    Mostra a decisão da diretoria sobre o futuro do técnico e o que pesou nela.

    Args:
        estado (dict): Estado da carreira.
        decisao (dict): Resultado de avaliar_diretoria.
    """
    titulo("A DIRETORIA DECIDIU")
    clube = clube_do_jogador(estado)
    for linha in decisao["a_favor"]:
        console.print(f" [green]+ {linha}[/]")
    for linha in decisao["contra"]:
        console.print(f" [red]- {linha}[/]")
    if decisao["decisao"] == "renovado":
        console.print(f"\n [bold green]Contrato renovado! Você segue no {clube['nome']}.[/]")
    elif decisao["decisao"] == "segunda_chance":
        console.print(
            f"\n [bold yellow]A meta não veio, mas a diretoria gostou do trabalho e você segue no {clube['nome']}"
            f" (a chance era de {decisao['chance']}%).[/] A confiança começa mais baixa."
        )
    else:
        console.print(
            f"\n [bold red]A diretoria não ficou satisfeita e você foi demitido do {clube['nome']}"
            f" (a chance de ficar era de {decisao['chance']}%).[/]"
        )
    console.print(f" Reputação: {estrelas(estado.get('reputacao', 0))}")
    pausar("Enter para continuar...")


def escolher_proposta(estado, propostas, titulo_tela, texto_recusa, confirmar_recusa=None):
    """
    Mostra as propostas de outros clubes para o técnico e lê a escolhida.

    A tabela mostra a divisão, o nível, a força, a meta, o caixa e o motivo do interesse de cada clube. O
    número aceita a proposta; 0 recusa todas. Se houver uma pergunta de confirmação, ela é feita antes de
    recusar.

    Args:
        estado (dict): Estado da carreira.
        propostas (list[dict]): Propostas montadas por propostas_de_emprego.
        titulo_tela (str): Título da tela.
        texto_recusa (str): Texto da opção 0.
        confirmar_recusa (str | None): Pergunta feita antes de recusar todas. Padrão None.

    Returns:
        str | None: Identificador do clube escolhido, ou None se o técnico recusou todas.
    """
    while True:
        titulo(titulo_tela)
        console.print(f" Reputação: {estrelas(estado.get('reputacao', 0))}\n")
        tabela = Table(header_style="bold")
        for coluna in ("#", "Clube", "Divisão", "Nível", "Força", "Meta", "Caixa", "Interesse"):
            tabela.add_column(coluna)
        for numero, proposta in enumerate(propostas, start=1):
            clube = estado["clubes"][proposta["clube_id"]]
            tabela.add_row(
                str(numero),
                f"[bold {clube['cor']}]{clube['nome']}[/]",
                DIVISOES[clube.get("divisao", 1)],
                NIVEIS[clube["nivel"]]["nome"],
                str(clube["forca"]),
                meta_do_clube(clube)[0],
                dinheiro(clube.get("caixa", 0)),
                proposta["motivo"],
            )
        console.print(tabela)
        console.print(f" 0 - {texto_recusa}")
        escolha = ler_opcao(0, len(propostas))
        if escolha:
            return propostas[escolha - 1]["clube_id"]
        if not confirmar_recusa or confirmar(confirmar_recusa):
            return None


def mostrar_nova_temporada(estado, relatorio):
    """
    Apresenta a nova temporada: clube, divisão, meta, confiança, entrada na copa e o que mudou no elenco.

    Mostra a força antiga e a nova, quem se aposentou, os garotos que subiram da base, quem mais evoluiu, quem
    mais caiu com a idade e, se houver, quantos jogadores novos chegaram ao mercado.

    Args:
        estado (dict): Estado da carreira, já na nova temporada.
        relatorio (dict): Resultado de nova_temporada.
    """
    clube = clube_do_jogador(estado)
    titulo(f"TEMPORADA {estado['temporada']}")
    console.print(
        f" [bold {clube['cor']}]{clube['nome']}[/] na {DIVISOES[clube.get('divisao', 1)]}"
        f"   Meta: [bold]{meta_do_clube(clube)[0]}[/]"
    )
    console.print(f" Confiança da diretoria: {barra(estado['confianca'], 20)}")
    console.print(f" Copa: {situacao_na_nova_copa(estado)}")
    antes, depois = relatorio["forca"]
    cor = "green" if depois > antes else ("red" if depois < antes else "yellow")
    console.print(f" Força do elenco: {antes} → [{cor}]{depois}[/]")
    if relatorio["aposentados"]:
        nomes = ", ".join(f"{rotulo(j)} ({j['idade'] + 1} anos)" for j in relatorio["aposentados"])
        console.print(f"\n [bold]Penduraram as chuteiras:[/] {nomes}")
    if relatorio["revelados"]:
        console.print("\n [bold]Subiram da base:[/]")
        for jogador in relatorio["revelados"]:
            console.print(f"  • {rotulo(jogador)}, {jogador['idade']} anos, qualidade {jogador['qualidade']}")
    if relatorio["evoluiram"]:
        texto = ", ".join(f"{rotulo(j)} [green]+{v}[/]" for j, v in relatorio["evoluiram"])
        console.print(f"\n Mais evoluíram: {texto}")
    if relatorio["cairam"]:
        texto = ", ".join(f"{rotulo(j)} [red]{v}[/]" for j, v in relatorio["cairam"])
        console.print(f" Sentiram a idade: {texto}")
    if relatorio["novos_no_mercado"]:
        console.print(f"\n [dim]{relatorio['novos_no_mercado']} jogadores novos chegaram ao mercado sem clube.[/]")
    pausar("Enter para continuar...")


def mostrar_carreira(estado):
    """
    Mostra o histórico da carreira do técnico, temporada por temporada, e a reputação atual.

    Args:
        estado (dict): Estado da carreira.
    """
    titulo("CARREIRA")
    clube = clube_do_jogador(estado)
    console.print(f" Técnico: [bold]{estado['tecnico']}[/]   Reputação: {estrelas(estado.get('reputacao', 0))}")
    console.print(" [dim]A reputação sobe com metas e títulos e cai com demissões; ela decide quem te contrata.[/]\n")
    tabela = Table(header_style="bold")
    for coluna in ("Temp.", "Clube", "Divisão", "Posição", "Desfecho", "Pontuação"):
        tabela.add_column(coluna)
    for linha in estado.get("carreira", []):
        tabela.add_row(
            str(linha["temporada"]),
            linha["clube"],
            DIVISOES[linha["divisao"]],
            f"{linha['posicao']}º",
            linha["desfecho"],
            str(linha["pontuacao"]),
        )
    tabela.add_row(
        str(estado.get("temporada", 1)),
        clube["nome"],
        DIVISOES[clube.get("divisao", 1)],
        f"{posicao_atual(estado)}º",
        "[dim]em andamento[/]",
        "-",
    )
    console.print(tabela)
    pausar()
