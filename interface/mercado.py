from rich.table import Table

from config import MAX_ELENCO, POSICOES
from elenco.escalacao import valor_de_mercado
from interface.entrada import console, ler_opcao, ler_valor
from interface.telas import mostrar_mensagem, titulo
from liga.temporada import clube_do_jogador
from mercado.transferencias import (
    contratar_livre,
    dinheiro,
    jogadores_a_venda,
    luvas,
    ofertas_por,
    pode_sair,
    preco_pedido,
    tentar_comprar,
    vender,
)

LIMITE_DA_LISTA = 15


def cabecalho_mercado(estado, subtitulo="MERCADO DA BOLA"):
    """
    Exibe o título de uma tela do mercado com o caixa e o tamanho do elenco.

    Args:
        estado (dict): Estado atual da temporada.
        subtitulo (str): Título da tela. Padrão "MERCADO DA BOLA".
    """
    clube = clube_do_jogador(estado)
    titulo(subtitulo)
    console.print(f" Caixa: [bold]{dinheiro(clube.get('caixa', 0))}[/]   Elenco: {len(clube['elenco'])}/{MAX_ELENCO} jogadores\n")


def escolher_posicao():
    """
    Pergunta ao usuário qual posição quer ver no mercado.

    As opções são goleiro, defensor, meia, atacante, todas as posições ou voltar.

    Returns:
        tuple: Par (seguir, posicao): seguir é False se o usuário escolheu voltar, e posicao é a sigla escolhida ou None para todas.
    """
    console.print(" Posição: 1 GOL   2 DEF   3 MEI   4 ATA   5 Todas   0 Voltar")
    escolha = ler_opcao(0, 5)
    if escolha == 0:
        return False, None
    return True, None if escolha == 5 else POSICOES[escolha - 1]


def comprar_de_clubes(estado):
    """
    Conduz a compra de um jogador de outro clube.

    O usuário filtra por posição e vê os 15 primeiros jogadores à venda, com clube, qualidade, idade, valor de mercado e preço pedido. Depois escolhe um jogador e digita uma proposta em milhões, ou 0 para cancelar, e vê se a compra foi aceita.

    Args:
        estado (dict): Estado atual da temporada.
    """
    cabecalho_mercado(estado, "COMPRAR DE OUTROS CLUBES")
    seguir, posicao = escolher_posicao()
    if not seguir:
        return
    opcoes = jogadores_a_venda(estado, posicao)[:LIMITE_DA_LISTA]
    cabecalho_mercado(estado, "COMPRAR DE OUTROS CLUBES")
    tabela = Table(header_style="bold")
    for coluna in ("#", "Jogador", "Pos", "Clube", "Qual", "Idade", "Valor", "Pedida"):
        tabela.add_column(coluna)
    for numero, (jogador, clube) in enumerate(opcoes, start=1):
        tabela.add_row(
            str(numero), jogador["nome"], jogador["pos"], clube["nome"], str(jogador["qualidade"]), str(jogador.get("idade", "-")),
            dinheiro(valor_de_mercado(jogador)), dinheiro(preco_pedido(clube, jogador)),
        )
    console.print(tabela)
    console.print(" [bold]0[/] Voltar")
    escolha = ler_opcao(0, len(opcoes))
    if not escolha:
        return
    jogador, vendedor = opcoes[escolha - 1]
    pedida = preco_pedido(vendedor, jogador)
    oferta = ler_valor(f" Sua proposta em milhões (pedida {dinheiro(pedida)}, 0 cancela) > ", 0.1, 999)
    if not oferta:
        return
    sucesso, mensagem = tentar_comprar(estado, jogador, vendedor, oferta)
    mostrar_mensagem(mensagem, "green" if sucesso else "red")


def contratar_sem_clube(estado):
    """
    Conduz a contratação de um jogador sem clube.

    Lista os jogadores livres da maior para a menor qualidade, com posição, idade e luvas. O usuário escolhe um deles ou volta com 0, e vê se a contratação deu certo. Se não houver jogadores livres, apenas avisa.

    Args:
        estado (dict): Estado atual da temporada.
    """
    cabecalho_mercado(estado, "JOGADORES SEM CLUBE")
    livres = sorted(estado["livres"], key=lambda jogador: jogador["qualidade"], reverse=True)
    if not livres:
        mostrar_mensagem("Não há jogadores livres no mercado.", "yellow")
        return
    tabela = Table(header_style="bold")
    for coluna in ("#", "Jogador", "Pos", "Qual", "Idade", "Luvas"):
        tabela.add_column(coluna)
    for numero, jogador in enumerate(livres, start=1):
        tabela.add_row(str(numero), jogador["nome"], jogador["pos"], str(jogador["qualidade"]), str(jogador.get("idade", "-")), dinheiro(luvas(jogador)))
    console.print(tabela)
    console.print(" [bold]0[/] Voltar")
    escolha = ler_opcao(0, len(livres))
    if escolha:
        sucesso, mensagem = contratar_livre(estado, livres[escolha - 1])
        mostrar_mensagem(mensagem, "green" if sucesso else "red")


def vender_jogador(estado):
    """
    Conduz a venda de um jogador do elenco para outro clube.

    Lista o elenco ordenado por posição e qualidade, indicando os titulares. Se o jogador escolhido puder sair sem deixar o elenco ou a posição abaixo do mínimo e algum clube fizer proposta, mostra as ofertas e deixa o usuário aceitar uma delas ou recusar todas.

    Args:
        estado (dict): Estado atual da temporada.
    """
    clube = clube_do_jogador(estado)
    cabecalho_mercado(estado, "VENDER JOGADOR")
    ordem = {"GOL": 0, "DEF": 1, "MEI": 2, "ATA": 3}
    elenco = sorted(clube["elenco"], key=lambda jogador: (ordem[jogador["pos"]], -jogador["qualidade"]))
    tabela = Table(header_style="bold")
    for coluna in ("#", "Jogador", "Pos", "Qual", "Idade", "Valor", "Titular"):
        tabela.add_column(coluna)
    for numero, jogador in enumerate(elenco, start=1):
        titular = "sim" if jogador["id"] in clube["titulares"] else ""
        tabela.add_row(str(numero), jogador["nome"], jogador["pos"], str(jogador["qualidade"]), str(jogador.get("idade", "-")), dinheiro(valor_de_mercado(jogador)), titular)
    console.print(tabela)
    console.print(" [bold]0[/] Voltar")
    escolha = ler_opcao(0, len(elenco))
    if not escolha:
        return
    jogador = elenco[escolha - 1]
    if not pode_sair(clube, jogador):
        mostrar_mensagem("Não dá para vender: o elenco ficaria sem reposição para a posição.", "red")
        return
    ofertas = ofertas_por(estado, jogador)
    if not ofertas:
        mostrar_mensagem("Nenhum clube fez proposta por esse jogador agora.", "yellow")
        return
    console.print(f"\n Propostas por {jogador['pos']} {jogador['nome']} (valor de mercado {dinheiro(valor_de_mercado(jogador))}):")
    for numero, (comprador, valor) in enumerate(ofertas, start=1):
        console.print(f" {numero} - {comprador['nome']}: [bold]{dinheiro(valor)}[/]")
    console.print(" 0 - Recusar todas")
    escolha = ler_opcao(0, len(ofertas))
    if escolha:
        comprador, valor = ofertas[escolha - 1]
        mostrar_mensagem(vender(estado, jogador, comprador, valor), "green")


def tela_mercado(estado):
    """
    Mostra o menu principal do mercado da bola.

    Exibe as cinco últimas notícias e deixa o usuário comprar de outros clubes, contratar jogadores sem clube ou vender um jogador, até escolher voltar.

    Args:
        estado (dict): Estado atual da temporada.
    """
    while True:
        cabecalho_mercado(estado)
        recentes = estado.get("noticias", [])[-5:]
        if recentes:
            console.print(" [bold]Últimas notícias:[/]")
            for texto in recentes:
                console.print(f"  • {texto}")
            console.print()
        console.print(" 1 - Comprar de outros clubes   2 - Jogadores sem clube   3 - Vender jogador   0 - Voltar")
        escolha = ler_opcao(0, 3)
        if escolha == 0:
            return
        if escolha == 1:
            comprar_de_clubes(estado)
        elif escolha == 2:
            contratar_sem_clube(estado)
        else:
            vender_jogador(estado)
