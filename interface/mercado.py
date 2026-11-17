from rich.table import Table

from config import CONFIANCA_NEGOCIACAO_FRACASSADA, CONFIANCA_SEGURAR, CONFIANCA_VENDA, MAX_ELENCO, POSICOES
from elenco.escalacao import rotulo, valor_de_mercado
from interface.campo import barra
from interface.entrada import console, ler_opcao, ler_valor
from interface.telas import mostrar_mensagem, status_jogador, titulo
from liga.eventos import aceitar_oferta, qualidade_do_garoto, responder_contraproposta
from liga.temporada import clube_do_jogador
from mercado.transferencias import (
    contratar_livre,
    dinheiro,
    jogadores_a_venda,
    luvas,
    ofertas_por,
    pode_sair,
    preco_pedido,
    sugerir_contratacoes,
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
    console.print(
        f" Caixa: [bold]{dinheiro(clube.get('caixa', 0))}[/]   Elenco: {len(clube['elenco'])}/{MAX_ELENCO} jogadores\n"
    )


def escolher_posicao():
    """
    Pergunta ao usuário qual posição quer ver no mercado.

    As opções são goleiro, defensor, meia, atacante, todas as posições ou voltar.

    Returns:
        tuple: Par (seguir, posicao): seguir é False se o usuário escolheu voltar, e posicao é a sigla
            escolhida ou None para todas.
    """
    console.print(" Posição: 1 GOL   2 DEF   3 MEI   4 ATA   5 Todas   0 Voltar")
    escolha = ler_opcao(0, 5)
    if escolha == 0:
        return False, None
    return True, None if escolha == 5 else POSICOES[escolha - 1]


def comprar_de_clubes(estado):
    """
    Conduz a compra de um jogador de outro clube.

    O usuário filtra por posição e vê os 15 primeiros jogadores à venda, com clube, qualidade, idade, valor de
    mercado e preço pedido. Depois escolhe um jogador e digita uma proposta em milhões, ou 0 para cancelar, e
    vê se a compra foi aceita.

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
            str(numero),
            jogador["nome"],
            jogador["pos"],
            clube["nome"],
            str(jogador["qualidade"]),
            str(jogador.get("idade", "-")),
            dinheiro(valor_de_mercado(jogador)),
            dinheiro(preco_pedido(clube, jogador)),
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

    Lista os jogadores livres da maior para a menor qualidade, com posição, idade e luvas. O usuário escolhe
    um deles ou volta com 0, e vê se a contratação deu certo. Se não houver jogadores livres, apenas avisa.

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
        tabela.add_row(
            str(numero),
            jogador["nome"],
            jogador["pos"],
            str(jogador["qualidade"]),
            str(jogador.get("idade", "-")),
            dinheiro(luvas(jogador)),
        )
    console.print(tabela)
    console.print(" [bold]0[/] Voltar")
    escolha = ler_opcao(0, len(livres))
    if escolha:
        sucesso, mensagem = contratar_livre(estado, livres[escolha - 1])
        mostrar_mensagem(mensagem, "green" if sucesso else "red")


def vender_jogador(estado):
    """
    Conduz a venda de um jogador do elenco para outro clube.

    Lista o elenco ordenado por posição e qualidade, indicando os titulares. Se o jogador escolhido puder sair
    sem deixar o elenco ou a posição abaixo do mínimo e algum clube fizer proposta, mostra as ofertas e deixa
    o usuário aceitar uma delas ou recusar todas.

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
        tabela.add_row(
            str(numero),
            jogador["nome"],
            jogador["pos"],
            str(jogador["qualidade"]),
            str(jogador.get("idade", "-")),
            dinheiro(valor_de_mercado(jogador)),
            titular,
        )
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
    console.print(f"\n Propostas por {rotulo(jogador)}, valor de mercado {dinheiro(valor_de_mercado(jogador))}:")
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

    Exibe as cinco últimas notícias e a principal indicação do olheiro, e deixa o usuário comprar de outros
    clubes, contratar jogadores sem clube, vender um jogador ou ver as sugestões do olheiro, até escolher
    voltar.

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
        sugestoes = sugerir_contratacoes(estado, 1)
        if sugestoes:
            indicado = sugestoes[0]["jogador"]
            console.print(
                f" [yellow]Olheiro indica:[/] {rotulo(indicado)}, qualidade {indicado['qualidade']}"
                f" [dim]— {sugestoes[0]['motivo']}[/]\n"
            )
        console.print(
            " 1 - Comprar de outros clubes   2 - Jogadores sem clube   3 - Vender jogador"
            "   4 - Sugestões do olheiro   0 - Voltar"
        )
        escolha = ler_opcao(0, 4)
        if escolha == 0:
            return
        if escolha == 1:
            comprar_de_clubes(estado)
        elif escolha == 2:
            contratar_sem_clube(estado)
        elif escolha == 3:
            vender_jogador(estado)
        else:
            sugestoes_do_olheiro(estado)


def ficha_do_jogador(clube, jogador):
    """
    Monta uma tabela com os dados de um jogador do clube.

    Mostra posição, idade, qualidade, atributos (o reflexo só para goleiros), energia, gols na temporada,
    situação no elenco e valor de mercado.

    Args:
        clube (dict): Clube dono do jogador.
        jogador (dict): Jogador a ser mostrado.

    Returns:
        rich.table.Table: Tabela de uma linha pronta para imprimir.
    """
    tabela = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
    for coluna in ("Jogador", "Idade", "Qual", "Fin", "Pas", "Des", "Fís", "Ref", "Energia", "Gols", "Situação"):
        tabela.add_column(coluna)
    tabela.add_row(
        f"[bold]{rotulo(jogador)}[/]",
        str(jogador.get("idade", "-")),
        f"[bold]{jogador['qualidade']}[/]",
        str(jogador["fin"]),
        str(jogador["pas"]),
        str(jogador["des"]),
        str(jogador["fis"]),
        str(jogador["ref"]) if jogador["pos"] == "GOL" else "-",
        barra(jogador["energia"], 6),
        str(jogador["gols"]),
        status_jogador(jogador, clube["titulares"]) or "reserva",
    )
    return tabela


def quem_assume(clube, jogador):
    """
    Encontra o jogador da mesma posição que fica com a vaga se o atual for vendido.

    Args:
        clube (dict): Clube dono do jogador.
        jogador (dict): Jogador que pode ser vendido.

    Returns:
        dict | None: Companheiro de posição com maior qualidade, ou None se não houver nenhum.
    """
    mesma_posicao = [j for j in clube["elenco"] if j["pos"] == jogador["pos"] and j["id"] != jogador["id"]]
    return max(mesma_posicao, key=lambda j: j["qualidade"], default=None)


def tela_proposta(estado, evento):
    """
    Mostra a proposta de um clube do exterior ou do país e conduz a negociação.

    Exibe a ficha do jogador, o valor de mercado, a oferta atual com a porcentagem sobre o valor, como o caixa
    fica se vender, quem assume a vaga, a qualidade do garoto que sobe da base e o efeito de cada decisão na
    confiança da diretoria. O técnico pode aceitar, recusar ou pedir mais: cada contraproposta é respondida
    por responder_contraproposta, e o histórico aparece embaixo da oferta enquanto o clube continua
    negociando.

    Args:
        estado (dict): Estado atual da temporada.
        evento (dict): Evento preparado, com o jogador alvo e a negociação.

    Returns:
        str: Efeito a aplicar: "vender", "segurar" ou "negociacao_fracassou".
    """
    clube = clube_do_jogador(estado)
    jogador = next(j for j in clube["elenco"] if j["id"] == evento["jogador_id"])
    negociacao = evento["negociacao"]
    interessado = negociacao["clube"]
    substituto = quem_assume(clube, jogador)
    historico = []
    while True:
        titulo(evento.get("titulo", "EVENTO DA SEMANA — PROPOSTA DO EXTERIOR"))
        console.print(f" O [bold]{interessado}[/] quer contratar [bold]{rotulo(jogador)}[/].\n")
        console.print(ficha_do_jogador(clube, jogador))
        oferta = negociacao["oferta"]
        porcentagem = round(oferta / negociacao["valor"] * 100) if negociacao["valor"] else 100
        caixa = clube.get("caixa", 0)
        console.print(f"\n Valor de mercado:  {dinheiro(negociacao['valor'])}")
        console.print(f" Oferta atual:      [bold green]{dinheiro(oferta)}[/] ({porcentagem}% do valor de mercado)")
        console.print(f" Caixa do clube:    {dinheiro(caixa)} → [bold]{dinheiro(caixa + oferta)}[/] se vender")
        if substituto:
            console.print(f" Assume a vaga:     {rotulo(substituto)}, qualidade {substituto['qualidade']}")
        console.print(f" Sobe da base:      um {jogador['pos']} com qualidade {qualidade_do_garoto(jogador)}")
        console.print(
            f" Diretoria:         quer vender. Vender +{CONFIANCA_VENDA} de confiança · segurar"
            f" {CONFIANCA_SEGURAR} (jogador motivado) · clube desistir {CONFIANCA_NEGOCIACAO_FRACASSADA}"
        )
        for linha in historico:
            console.print(f" [yellow]{linha}[/]")
        console.print(f"\n 1 - Aceitar {dinheiro(oferta)}   2 - Pedir mais   3 - Recusar e segurar o jogador")
        escolha = ler_opcao(1, 3)
        if escolha == 1:
            aceitar_oferta(negociacao)
            return "vender"
        if escolha == 3:
            return "segurar"
        minimo = round(oferta + 0.1, 1)
        pedido = ler_valor(
            f" Quanto pedir, em milhões? (a partir de {minimo:.1f}; 0 volta) > ", minimo, round(oferta * 3, 1)
        )
        if not pedido:
            continue
        resposta = responder_contraproposta(negociacao, pedido)
        if resposta == "aceita":
            mostrar_mensagem(f"O {interessado} aceitou pagar {dinheiro(pedido)}!", "bold green")
            return "vender"
        if resposta == "desiste":
            mostrar_mensagem(f"O {interessado} achou caro demais e encerrou a negociação.", "bold red")
            return "negociacao_fracassou"
        if resposta == "mantem":
            historico.append(f"Você pediu {dinheiro(pedido)}. O {interessado} manteve a oferta: é pegar ou largar.")
        else:
            historico.append(
                f"Você pediu {dinheiro(pedido)}. O {interessado} subiu a oferta para {dinheiro(negociacao['oferta'])}."
            )


def sugestoes_do_olheiro(estado):
    """
    Mostra as sugestões de contratação do olheiro e conduz a contratação da escolhida.

    Lista até seis jogadores que cabem no caixa, com clube (ou "sem clube"), qualidade, idade, custo e o
    motivo da indicação. Ao escolher um jogador sem clube, contrata pagando as luvas; de outro clube, pede a
    proposta em milhões, sugerindo o preço pedido. Se o elenco estiver cheio ou não houver indicação, apenas
    avisa.

    Args:
        estado (dict): Estado atual da temporada.
    """
    cabecalho_mercado(estado, "SUGESTÕES DO OLHEIRO")
    sugestoes = sugerir_contratacoes(estado)
    if not sugestoes:
        clube = clube_do_jogador(estado)
        if len(clube["elenco"]) >= MAX_ELENCO:
            mostrar_mensagem("Seu elenco está cheio. Venda alguém para abrir vaga.", "yellow")
        else:
            mostrar_mensagem("O olheiro não achou ninguém que melhore o time e caiba no caixa agora.", "yellow")
        return
    tabela = Table(header_style="bold")
    for coluna in ("#", "Jogador", "Clube", "Qual", "Idade", "Custo", "Por quê"):
        tabela.add_column(coluna)
    for numero, item in enumerate(sugestoes, start=1):
        jogador = item["jogador"]
        tabela.add_row(
            str(numero),
            rotulo(jogador),
            item["vendedor"]["nome"] if item["vendedor"] else "[green]sem clube[/]",
            str(jogador["qualidade"]),
            str(jogador.get("idade", "-")),
            dinheiro(item["custo"]) + ("" if item["vendedor"] else " (luvas)"),
            item["motivo"],
        )
    console.print(tabela)
    console.print(" [bold]0[/] Voltar")
    escolha = ler_opcao(0, len(sugestoes))
    if not escolha:
        return
    item = sugestoes[escolha - 1]
    if item["vendedor"] is None:
        sucesso, mensagem = contratar_livre(estado, item["jogador"])
    else:
        oferta = ler_valor(f" Sua proposta em milhões (pedida {dinheiro(item['custo'])}, 0 cancela) > ", 0.1, 999)
        if not oferta:
            return
        sucesso, mensagem = tentar_comprar(estado, item["jogador"], item["vendedor"], oferta)
    mostrar_mensagem(mensagem, "green" if sucesso else "red")
