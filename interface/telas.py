from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from config import (
    ESTILOS,
    FASES_COPA,
    FORMACOES,
    NIVEIS,
    NOME_JOGO,
    NOMES_ESTILOS,
    NOMES_FASES,
    TOTAL_RODADAS,
    VERSAO,
    ZONA_G4,
    ZONA_REBAIXAMENTO,
)
from elenco.escalacao import disponivel, escalar_automatico, rotulo, valor_de_mercado
from interface.campo import barra
from interface.entrada import console, ler_opcao, limpar, pausar
from liga.copa import situacao_do_clube
from liga.tabela import posicao_do_clube, saldo
from liga.temporada import (
    adversario_de,
    classificacao,
    clube_do_jogador,
    descricao_etapa,
    etapa_atual,
    jogo_do_jogador,
    jogo_neutro,
    jogos_da_rodada,
    mata_mata,
    posicao_atual,
    ultimos_resultados,
)
from mercado.transferencias import dinheiro
from partida.simulacao import plano_ia

OPCOES_MENU = ("Novo jogo", "Carregar", "Ranking", "Sair")
CORES_RESULTADO = {"V": "green", "E": "yellow", "D": "red"}


def titulo(texto):
    """
    Limpa a tela e exibe um título em destaque.

    Args:
        texto (str): Texto do título, mostrado em negrito dentro de um painel verde.
    """
    limpar()
    console.print(Panel.fit(f"[bold]{texto}[/]", border_style="green"))


def nivel_de_forca(forca):
    """
    Converte a força de um clube em uma barra de 1 a 5 blocos.

    Args:
        forca (int): Força do clube.

    Returns:
        str: Barra com marcação do rich, com blocos verdes preenchidos e o restante esmaecido.
    """
    quantidade = max(1, min(5, (forca - 50) // 7))
    return f"[green]{'█' * quantidade}[/][dim]{'░' * (5 - quantidade)}[/]"


def mostrar_menu_inicial():
    """
    Exibe o menu inicial do jogo e lê a opção escolhida.

    Mostra o nome e a versão do jogo e as opções Novo jogo, Carregar, Ranking e Sair.

    Returns:
        int: Opção escolhida, de 1 a 4.
    """
    limpar()
    console.print(Panel.fit(f"[bold green]{' '.join(NOME_JOGO)}[/]  [dim]v{VERSAO}[/]", border_style="green"))
    for numero, opcao in enumerate(OPCOES_MENU, start=1):
        console.print(f" {numero} - {opcao}")
    return ler_opcao(1, len(OPCOES_MENU))


def escolher_clube(clubes_base):
    """
    Exibe a tela de escolha do clube para um novo jogo.

    Mostra uma tabela com o nome, o nível, a força e a meta da diretoria de cada clube, além de um aviso sobre
    o multiplicador do ranking para clubes menores. O usuário escolhe um clube pelo número ou digita 0 para
    voltar.

    Args:
        clubes_base (list): Lista de clubes disponíveis para escolha.

    Returns:
        str | None: Identificador do clube escolhido ou None se o usuário voltar.
    """
    titulo("ESCOLHA SEU CLUBE")
    tabela = Table(header_style="bold")
    for coluna in ("#", "Clube", "Nível", "Força", "Meta da diretoria"):
        tabela.add_column(coluna)
    for numero, clube in enumerate(clubes_base, start=1):
        nivel = NIVEIS[clube["nivel"]]
        tabela.add_row(
            str(numero),
            f"[bold {clube['cor']}]{clube['nome']}[/]",
            nivel["nome"],
            f"{nivel_de_forca(clube['forca'])} {clube['forca']}",
            nivel["meta"],
        )
    console.print(tabela)
    console.print(" [dim]Clubes menores pontuam mais no ranking (médio x1,3, pequeno x1,6).[/]")
    console.print(" [bold]0[/] Voltar")
    escolha = ler_opcao(0, len(clubes_base))
    return clubes_base[escolha - 1]["id"] if escolha else None


def texto_jogo(estado, jogo):
    """
    Monta o texto de um confronto no formato "Mandante x Visitante".

    Args:
        estado (dict): Estado atual da temporada.
        jogo (tuple): Par com os identificadores do mandante e do visitante.

    Returns:
        str: Texto com marcação do rich, com o nome de cada clube na sua cor.
    """
    casa = estado["clubes"][jogo[0]]
    fora = estado["clubes"][jogo[1]]
    return f"[bold {casa['cor']}]{casa['nome']}[/] x [bold {fora['cor']}]{fora['nome']}[/]"


def texto_ultimos(letras):
    """
    Formata a sequência dos últimos resultados com uma cor para cada letra.

    Args:
        letras (list): Letras dos resultados, sendo "V" vitória, "E" empate e "D" derrota.

    Returns:
        str: Letras coloridas separadas por espaço, ou "-" se não houver resultados.
    """
    return " ".join(f"[{CORES_RESULTADO[letra]}]{letra}[/]" for letra in letras) or "-"


def local_do_jogo(estado, jogo, clube_id):
    """
    Informa onde o clube vai jogar a partida.

    Args:
        estado (dict): Estado atual da temporada.
        jogo (tuple): Par com os identificadores do mandante e do visitante.
        clube_id (str): Identificador do clube de referência.

    Returns:
        str: "campo neutro", "em casa" ou "fora de casa".
    """
    if jogo_neutro(estado):
        return "campo neutro"
    return "em casa" if jogo[0] == clube_id else "fora de casa"


OPCOES_CENTRAL = (
    "Próximo jogo",
    "Elenco",
    "Plano de jogo",
    "Classificação",
    "Copa",
    "Rodadas e histórico",
    "Mercado da bola",
    "Clubes",
    "Salvar",
)


def mostrar_central(estado):
    """
    Exibe a central do clube e lê a opção escolhida.

    Mostra o técnico, a meta, a posição na liga, o caixa, a situação na copa, os últimos jogos, a confiança da
    diretoria e o próximo compromisso. Se o clube não joga na etapa atual da copa, a primeira opção passa a
    ser acompanhar a rodada da copa. As opções vão de Próximo jogo até Salvar, e 0 volta ao menu.

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        int: Opção escolhida, de 0 a 9.
    """
    clube = clube_do_jogador(estado)
    nivel = NIVEIS[clube["nivel"]]
    titulo(f"CENTRAL DO CLUBE — {clube['nome'].upper()}")
    console.print(
        f" Técnico: [bold]{estado['tecnico']}[/]   Meta: [bold]{nivel['meta']}[/]"
        f"   Posição na liga: [bold]{posicao_atual(estado)}º[/]"
    )
    console.print(
        f" Caixa: [bold]{dinheiro(clube.get('caixa', 0))}[/]   Copa: {situacao_do_clube(estado['copa'], clube['id'])}"
        f"   Últimos jogos: {texto_ultimos(estado['ultimos'])}"
    )
    console.print(f" Confiança da diretoria: {barra(estado['confianca'], 20)}")
    console.print(f"\n Próximo compromisso: [bold]{descricao_etapa(etapa_atual(estado))}[/]")
    jogo = jogo_do_jogador(estado)
    if jogo:
        adversario = estado["clubes"][adversario_de(jogo, clube["id"])]
        console.print(
            f" {texto_jogo(estado, jogo)} ({local_do_jogo(estado, jogo, clube['id'])})"
            f"  [dim]força {adversario['forca']}[/]"
        )
    else:
        console.print(" [dim]Seu clube não joga nesta fase da copa.[/]")
    console.print()
    for numero, opcao in enumerate(OPCOES_CENTRAL, start=1):
        texto_opcao = opcao if numero != 1 or jogo else "Acompanhar a rodada da copa"
        console.print(f" {numero} - {texto_opcao}")
    console.print(" 0 - Voltar ao menu")
    return ler_opcao(0, len(OPCOES_CENTRAL))


def status_jogador(jogador, titulares):
    """
    Monta o texto de situação de um jogador para a tabela do elenco.

    Indica se o jogador é titular, se está lesionado, suspenso ou em grande fase e quantos cartões amarelos
    tem.

    Args:
        jogador (dict): Dados do jogador.
        titulares (list): Identificadores dos jogadores titulares.

    Returns:
        str: Situações com marcação do rich separadas por espaço, ou texto vazio se não houver nenhuma.
    """
    partes = []
    if jogador["id"] in titulares:
        partes.append("[green]titular[/]")
    if jogador["lesao"]:
        partes.append(f"[red]lesionado ({jogador['lesao']})[/]")
    if jogador["suspenso"]:
        partes.append("[red]suspenso[/]")
    if jogador["fase"]:
        partes.append("[cyan]grande fase[/]")
    if jogador["amarelos"]:
        partes.append(f"[yellow]{jogador['amarelos']} amarelo(s)[/]")
    return " ".join(partes)


def tabela_elenco(clube):
    """
    Monta a tabela com todos os jogadores do elenco.

    Os jogadores são ordenados por posição (goleiro, defesa, meio e ataque) e, dentro de cada posição, da
    maior para a menor qualidade. A tabela mostra os atributos, a energia, os gols, o valor de mercado e a
    situação de cada um; a coluna de reflexo só é preenchida para goleiros.

    Args:
        clube (dict): Dados do clube.

    Returns:
        tuple: Tabela pronta para imprimir (rich.table.Table) e a lista de jogadores na mesma ordem das
            linhas.
    """
    tabela = Table(header_style="bold")
    for coluna in (
        "#",
        "Jogador",
        "Pos",
        "Qual",
        "Idade",
        "Fin",
        "Pas",
        "Des",
        "Fís",
        "Ref",
        "Energia",
        "Gols",
        "Valor",
        "Situação",
    ):
        tabela.add_column(coluna)
    ordem = {"GOL": 0, "DEF": 1, "MEI": 2, "ATA": 3}
    jogadores = sorted(clube["elenco"], key=lambda j: (ordem[j["pos"]], -j["qualidade"]))
    for numero, jogador in enumerate(jogadores, start=1):
        referencia = str(jogador["ref"]) if jogador["pos"] == "GOL" else "-"
        tabela.add_row(
            str(numero),
            jogador["nome"],
            jogador["pos"],
            str(jogador["qualidade"]),
            str(jogador.get("idade", "-")),
            str(jogador["fin"]),
            str(jogador["pas"]),
            str(jogador["des"]),
            str(jogador["fis"]),
            referencia,
            barra(jogador["energia"], 6),
            str(jogador["gols"]),
            dinheiro(valor_de_mercado(jogador)),
            status_jogador(jogador, clube["titulares"]),
        )
    return tabela, jogadores


def mostrar_elenco(clube):
    """
    Exibe a tabela do elenco do clube e espera o usuário pressionar Enter.

    Args:
        clube (dict): Dados do clube.
    """
    titulo(f"ELENCO — {clube['nome'].upper()}")
    tabela, _ = tabela_elenco(clube)
    console.print(tabela)
    pausar()


def trocar_titular(clube):
    """
    Troca um titular por um reserva escolhido pelo usuário.

    Mostra a tabela do elenco e pede o número do titular que sai e depois o do reserva que entra. O reserva
    precisa estar disponível e não pode já ser titular; a troca é feita na mesma posição da lista de
    titulares.

    Args:
        clube (dict): Dados do clube, cuja lista de titulares é alterada.

    Returns:
        str: Mensagem sobre o resultado da troca, ou texto vazio se o usuário cancelar em qualquer uma das
            duas perguntas.
    """
    limpar()
    tabela, jogadores = tabela_elenco(clube)
    console.print(tabela)
    console.print(" [bold]0[/] Cancelar")
    sai = ler_opcao(0, len(jogadores), " Número do titular que sai > ")
    if not sai:
        return ""
    if jogadores[sai - 1]["id"] not in clube["titulares"]:
        return "Escolha um jogador que seja titular."
    entra = ler_opcao(0, len(jogadores), " Número do reserva que entra > ")
    if not entra:
        return ""
    reserva = jogadores[entra - 1]
    if reserva["id"] in clube["titulares"] or not disponivel(reserva):
        return "Esse jogador já é titular ou não está disponível."
    indice = clube["titulares"].index(jogadores[sai - 1]["id"])
    clube["titulares"][indice] = reserva["id"]
    return f"{rotulo(reserva)} entra no time titular."


def nome_curto(nome):
    """
    Abrevia o nome de um jogador para a inicial do primeiro nome e o último sobrenome.

    Args:
        nome (str): Nome completo do jogador.

    Returns:
        str: Nome abreviado (ex.: "J. Silva"), ou o próprio nome se tiver uma só palavra.
    """
    partes = nome.split()
    return nome if len(partes) == 1 else f"{partes[0][0]}. {partes[-1]}"


def estilo_do_titular(jogador):
    """
    Define o estilo do nome de um titular no desenho da formação.

    Args:
        jogador (dict): Dados do jogador.

    Returns:
        str: "bold red" se o jogador não estiver disponível, "bold yellow" se a energia estiver abaixo de 50 e
            "bold bright_white" nos demais casos.
    """
    if not disponivel(jogador):
        return "bold red"
    if jogador["energia"] < 50:
        return "bold yellow"
    return "bold bright_white"


def linha_do_setor(desenho, rotulo, celulas, larguras, largura):
    """
    Acrescenta ao desenho uma linha de um setor do campo.

    Escreve o rótulo do setor à esquerda e centraliza as células na largura disponível, separadas por cinco
    espaços.

    Args:
        desenho (rich.text.Text): Texto do desenho, alterado no lugar.
        rotulo (str): Rótulo do setor, como "ATA" ou "GOL"; pode ser vazio.
        celulas (list): Pares de texto e estilo de cada célula.
        larguras (list): Largura de cada célula, na mesma ordem.
        largura (int): Largura total da linha.
    """
    tamanho = sum(larguras) + 5 * max(0, len(larguras) - 1)
    desenho.append(f"{rotulo:<5}", style="dim")
    desenho.append(" " * max(0, (largura - 5 - tamanho) // 2))
    for numero, ((texto, estilo), tamanho_celula) in enumerate(zip(celulas, larguras)):
        if numero:
            desenho.append("     ")
        desenho.append(texto.center(tamanho_celula), style=estilo)
    desenho.append("\n")


def desenho_formacao(clube, largura=88):
    """
    Desenha os titulares do clube dispostos por setor do campo.

    Os setores aparecem de cima para baixo: ataque, meio, defesa e goleiro. Cada jogador mostra o nome
    abreviado e, abaixo, a qualidade e a energia; o nome fica amarelo se ele estiver cansado e vermelho se
    estiver indisponível. A formação aparece no título do painel.

    Args:
        clube (dict): Dados do clube.
        largura (int): Largura do desenho, sem contar a borda e o espaçamento interno. Padrão: 88.

    Returns:
        rich.panel.Panel: Painel pronto para imprimir.
    """
    titulares = [j for j in clube["elenco"] if j["id"] in clube["titulares"]]
    desenho = Text()
    for indice, posicao in enumerate(("ATA", "MEI", "DEF", "GOL")):
        do_setor = [j for j in titulares if j["pos"] == posicao]
        nomes = [(nome_curto(j["nome"]), estilo_do_titular(j)) for j in do_setor]
        detalhes = [(f"{j['qualidade']} · {round(j['energia'])}%", "dim") for j in do_setor]
        larguras = [max(len(nome), len(detalhe)) for (nome, _), (detalhe, _) in zip(nomes, detalhes)]
        if indice:
            desenho.append("\n\n")
        linha_do_setor(desenho, posicao, nomes, larguras, largura)
        linha_do_setor(desenho, "", detalhes, larguras, largura)
    desenho.rstrip()
    return Panel(
        desenho,
        title=f"[bold]{clube['plano']['formacao']}[/]",
        subtitle="[dim]qualidade · energia   amarelo: cansado[/]",
        width=largura + 6,
        padding=(1, 2),
        border_style="green",
    )


def editar_plano(clube):
    """
    Exibe a tela do plano de jogo e permite alterá-lo até o usuário voltar.

    Mostra a formação, o estilo, a ofensividade, a intensidade e o desenho dos titulares. As opções são trocar
    a formação (o time é reescalado automaticamente), trocar o estilo, ajustar a ofensividade e a intensidade
    de 1 a 5, fazer a escalação automática, trocar um titular ou voltar com 0.

    Args:
        clube (dict): Dados do clube, cujo plano e titulares são alterados.
    """
    mensagem = ""
    while True:
        titulo("PLANO DE JOGO")
        plano = clube["plano"]
        console.print(f" Formação: [bold]{plano['formacao']}[/]   Estilo: [bold]{NOMES_ESTILOS[plano['estilo']]}[/]")
        console.print(
            f" Ofensividade: [bold]{plano['ofensividade']}[/]/5   Intensidade: [bold]{plano['intensidade']}[/]/5"
        )
        console.print(desenho_formacao(clube))
        if mensagem:
            console.print(f" [yellow]{mensagem}[/]")
        console.print(
            "\n 1 - Formação  2 - Estilo  3 - Ofensividade  4 - Intensidade"
            "  5 - Escalação automática  6 - Trocar titular  0 - Voltar"
        )
        escolha = ler_opcao(0, 6)
        mensagem = ""
        if escolha == 0:
            return
        if escolha == 1:
            nomes = list(FORMACOES)
            console.print(
                " " + "   ".join(f"[bold]{n}[/] {f}" for n, f in enumerate(nomes, start=1)) + "   [bold]0[/] Voltar"
            )
            nova = ler_opcao(0, len(nomes))
            if nova:
                plano["formacao"] = nomes[nova - 1]
                clube["titulares"] = escalar_automatico(clube["elenco"], plano["formacao"])
                mensagem = "Time reescalado para a nova formação."
        elif escolha == 2:
            console.print(
                " "
                + "   ".join(f"[bold]{n}[/] {NOMES_ESTILOS[e]}" for n, e in enumerate(ESTILOS, start=1))
                + "   [bold]0[/] Voltar"
            )
            novo = ler_opcao(0, len(ESTILOS))
            if novo:
                plano["estilo"] = ESTILOS[novo - 1]
        elif escolha == 3:
            plano["ofensividade"] = (
                ler_opcao(0, 5, " Ofensividade (1 retranca a 5 tudo ao ataque, 0 mantém) > ") or plano["ofensividade"]
            )
        elif escolha == 4:
            plano["intensidade"] = (
                ler_opcao(0, 5, " Intensidade (1 a 5, mais alta cansa mais, 0 mantém) > ") or plano["intensidade"]
            )
        elif escolha == 5:
            clube["titulares"] = escalar_automatico(clube["elenco"], plano["formacao"])
            mensagem = "Escalados os melhores disponíveis."
        else:
            mensagem = trocar_titular(clube)


def mostrar_classificacao(estado):
    """
    Exibe a tabela de classificação da liga.

    Mostra pontos, jogos, vitórias, empates, derrotas, gols e saldo de cada clube. O líder aparece em verde, o
    G4 em azul, a zona de rebaixamento em vermelho e o clube do jogador em amarelo. Abaixo da tabela aparecem
    a legenda e os critérios de desempate. Espera o usuário pressionar Enter.

    Args:
        estado (dict): Estado atual da temporada.
    """
    titulo("CLASSIFICAÇÃO")
    tabela = Table(header_style="bold")
    for coluna in ("#", "Clube", "P", "J", "V", "E", "D", "GP", "GC", "SG"):
        tabela.add_column(coluna, justify="right" if coluna not in ("Clube",) else "left")
    ordenada = classificacao(estado)
    for posicao, linha in enumerate(ordenada, start=1):
        clube = estado["clubes"][linha["id"]]
        if linha["id"] == estado["clube_id"]:
            estilo = "bold yellow"
        elif posicao == 1:
            estilo = "green"
        elif posicao <= ZONA_G4:
            estilo = "blue"
        elif posicao > len(ordenada) - ZONA_REBAIXAMENTO:
            estilo = "red"
        else:
            estilo = ""
        tabela.add_row(
            str(posicao),
            clube["nome"],
            str(linha["pontos"]),
            str(linha["jogos"]),
            str(linha["vitorias"]),
            str(linha["empates"]),
            str(linha["derrotas"]),
            str(linha["gp"]),
            str(linha["gc"]),
            f"{saldo(linha):+d}",
            style=estilo,
        )
    console.print(tabela)
    console.print(" [green]■[/] campeão  [blue]■[/] G4  [red]■[/] rebaixamento  [bold yellow]■[/] seu clube")
    console.print(
        " [dim]Desempate: pontos, vitórias, saldo, gols marcados, confronto direto, menos vermelhos, sorteio.[/]"
    )
    pausar()


def mostrar_sumula(linhas):
    """
    Imprime os lances da súmula de uma partida, um por linha.

    Args:
        linhas (list | None): Lances registrados; se vazio ou None, mostra "Sem lances registrados.".
    """
    for linha in linhas or ["Sem lances registrados."]:
        console.print(f"  {linha}")


def mostrar_rodadas(estado):
    """
    Exibe a tela de rodadas e histórico até o usuário voltar.

    Pede o número da rodada a consultar. Se a rodada já foi jogada, mostra os placares e a súmula do jogo do
    usuário; se ainda não foi, mostra apenas os confrontos. O jogo do clube do usuário é marcado com uma seta.
    Digitar 0 volta.

    Args:
        estado (dict): Estado atual da temporada.
    """
    while True:
        titulo("RODADAS E HISTÓRICO")
        console.print(f" Rodada atual: {estado['rodada']}/{TOTAL_RODADAS}")
        numero = ler_opcao(0, TOTAL_RODADAS, " Qual rodada ver? (0 volta) > ")
        if numero == 0:
            return
        titulo(f"RODADA {numero}")
        jogada = numero <= len(estado["historico"])
        if jogada:
            for jogo in estado["historico"][numero - 1]:
                destaque = " [yellow]◄[/]" if estado["clube_id"] in (jogo["mandante"], jogo["visitante"]) else ""
                casa = estado["clubes"][jogo["mandante"]]
                fora = estado["clubes"][jogo["visitante"]]
                console.print(f" {casa['nome']:>22} [bold]{jogo['gm']} x {jogo['gv']}[/] {fora['nome']}{destaque}")
            console.print("\n [bold]Súmula do seu jogo:[/]")
            mostrar_sumula(estado["sumulas"].get(str(numero)))
        else:
            for jogo in jogos_da_rodada(estado, numero):
                destaque = " [yellow]◄[/]" if estado["clube_id"] in jogo else ""
                console.print(
                    f" {estado['clubes'][jogo[0]]['nome']:>22}   x   {estado['clubes'][jogo[1]]['nome']}{destaque}"
                )
        pausar()


def pre_jogo(estado):
    """
    Exibe a tela de pré-jogo e lê a opção escolhida.

    Mostra o confronto, o local, a força dos dois clubes, o aviso de pênaltis em mata-mata, o plano de jogo do
    usuário e os titulares cansados. As opções são jogar lance a lance, simular assistindo, simular rápido,
    ver só o resultado, ver o adversário, ajustar o plano ou voltar com 0.

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        int: Opção escolhida, de 0 a 6.
    """
    clube = clube_do_jogador(estado)
    jogo = jogo_do_jogador(estado)
    adversario = estado["clubes"][adversario_de(jogo, clube["id"])]
    titulo(f"PRÉ-JOGO — {descricao_etapa(etapa_atual(estado)).upper()}")
    console.print(f" {texto_jogo(estado, jogo)} ({local_do_jogo(estado, jogo, clube['id'])})")
    console.print(f" Força: {clube['nome']} {clube['forca']}  x  {adversario['nome']} {adversario['forca']}")
    if mata_mata(estado):
        console.print(" [yellow]Mata-mata: se empatar, a vaga é decidida nos pênaltis.[/]")
    plano = clube["plano"]
    console.print(
        f" Seu plano: {plano['formacao']} · {NOMES_ESTILOS[plano['estilo']]}"
        f" · Ofensividade {plano['ofensividade']} · Intensidade {plano['intensidade']}"
    )
    titulares = [j for j in clube["elenco"] if j["id"] in clube["titulares"]]
    cansados = [rotulo(j) for j in titulares if j["energia"] < 50]
    if cansados:
        console.print(f" [yellow]Titulares cansados: {', '.join(cansados)}[/]")
    console.print("\n 1 - Jogar lance a lance   2 - Simular assistindo (Enter avança)   3 - Simular rápido")
    console.print(" 4 - Só o resultado   5 - Ver adversário   6 - Ajustar plano   0 - Voltar")
    return ler_opcao(0, 6)


def texto_penaltis_resultado(estado, resultado):
    """
    Monta o placar da disputa de pênaltis de uma partida.

    Args:
        estado (dict): Estado atual da temporada.
        resultado (dict): Resultado da partida.

    Returns:
        str: Texto no formato "pênaltis SIGLA n x n SIGLA", ou texto vazio se não houve pênaltis.
    """
    if not resultado.get("penaltis"):
        return ""
    casa = estado["clubes"][resultado["mandante"]]["sigla"]
    fora = estado["clubes"][resultado["visitante"]]["sigla"]
    pen = resultado["penaltis"]
    return f"pênaltis {casa} {pen[resultado['mandante']]} x {pen[resultado['visitante']]} {fora}"


def mostrar_fim_de_jogo(estado, resultado):
    """
    Exibe a tela de fim de jogo.

    Mostra o placar, o resultado dos pênaltis e quem avançou (quando houver), uma tabela com posse de bola,
    finalizações, chutes no alvo e faltas de cada clube, e a súmula da partida. Espera o usuário pressionar
    Enter.

    Args:
        estado (dict): Estado atual da temporada.
        resultado (dict): Resultado da partida, com estatísticas e súmula.
    """
    casa = estado["clubes"][resultado["mandante"]]
    fora = estado["clubes"][resultado["visitante"]]
    titulo("FIM DE JOGO")
    console.print(
        f" [bold {casa['cor']}]{casa['nome']}[/] [bold]{resultado['gm']} x {resultado['gv']}[/]"
        f" [bold {fora['cor']}]{fora['nome']}[/]"
    )
    if resultado.get("penaltis"):
        vencedor = estado["clubes"][resultado["vencedor"]]["nome"]
        console.print(f" [bold yellow]{texto_penaltis_resultado(estado, resultado)} — {vencedor} avança![/]")
    console.print()
    estatisticas = resultado["estatisticas"]
    tabela = Table(header_style="bold")
    tabela.add_column("")
    tabela.add_column(casa["sigla"], justify="center")
    tabela.add_column(fora["sigla"], justify="center")
    for chave, nome in (("posse", "Posse %"), ("chutes", "Finalizações"), ("no_alvo", "No alvo"), ("faltas", "Faltas")):
        tabela.add_row(nome, str(estatisticas[casa["id"]][chave]), str(estatisticas[fora["id"]][chave]))
    console.print(tabela)
    console.print(" [bold]Súmula:[/]")
    mostrar_sumula(resultado["sumula"])
    pausar("Enter para continuar...")


def linha_de_resultado(estado, resultado):
    """
    Monta a linha de placar de uma partida para as listas de resultados.

    Inclui o placar dos pênaltis entre parênteses, quando houver, e uma seta se o clube do usuário participou
    do jogo.

    Args:
        estado (dict): Estado atual da temporada.
        resultado (dict): Resultado da partida.

    Returns:
        str: Linha com marcação do rich.
    """
    casa = estado["clubes"][resultado["mandante"]]
    fora = estado["clubes"][resultado["visitante"]]
    destaque = " [yellow]◄[/]" if estado["clube_id"] in (casa["id"], fora["id"]) else ""
    penaltis = texto_penaltis_resultado(estado, resultado)
    extra = f" [dim]({penaltis})[/]" if penaltis else ""
    return f" {casa['nome']:>22} [bold]{resultado['gm']} x {resultado['gv']}[/] {fora['nome']}{extra}{destaque}"


def mostrar_resultados(estado, titulo_tela, resultados, informacao, noticias):
    """
    Exibe os resultados de uma rodada ou fase.

    Mostra os placares e, conforme as informações recebidas, se o clube do usuário foi campeão, avançou ou foi
    eliminado da copa, a variação da confiança da diretoria, os desfalques substituídos na escalação e as
    notícias do mercado da bola. Espera o usuário pressionar Enter.

    Args:
        estado (dict): Estado atual da temporada.
        titulo_tela (str): Título exibido no topo da tela.
        resultados (list): Resultados das partidas.
        informacao (dict): Dados do jogo do usuário, como "jogo", "letra", "variacao" e "trocados".
        noticias (list): Notícias do mercado da bola.
    """
    titulo(titulo_tela)
    for resultado in resultados:
        console.print(linha_de_resultado(estado, resultado))
    jogo = informacao.get("jogo")
    if jogo:
        if estado["copa"]["campeao"] == estado["clube_id"]:
            console.print("\n [bold green]CAMPEÃO DA COPA![/]")
        elif jogo["vencedor"] == estado["clube_id"]:
            console.print("\n [bold green]Seu clube avançou na copa![/]")
        else:
            console.print("\n [bold red]Seu clube foi eliminado da copa.[/]")
    if informacao.get("letra"):
        sinal = f"{informacao['variacao']:+d}"
        cor = "green" if informacao["variacao"] > 0 else ("red" if informacao["variacao"] < 0 else "yellow")
        console.print(f"\n Confiança da diretoria: [{cor}]{sinal}[/] → {barra(estado['confianca'], 20)}")
    if informacao.get("trocados"):
        console.print(f" [yellow]Desfalques substituídos na escalação: {', '.join(informacao['trocados'])}[/]")
    if noticias:
        console.print("\n [bold]Mercado da bola:[/]")
        for texto_noticia in noticias:
            console.print(f"  • {texto_noticia}")
    pausar("Enter para continuar...")


def mostrar_evento(evento):
    """
    Exibe o evento da semana e, se houver opções, lê a escolha do usuário.

    Mostra o texto do evento. Se ele não tiver opções, devolve o efeito direto; caso contrário, lista as
    opções numeradas a partir de 1.

    Args:
        evento (dict): Evento preparado, com texto, efeito e opções.

    Returns:
        str: Efeito do evento ou da opção escolhida.
    """
    titulo("EVENTO DA SEMANA")
    console.print(f" {evento['texto']}\n")
    if not evento["opcoes"]:
        return evento["efeito"]
    for numero, opcao in enumerate(evento["opcoes"], start=1):
        console.print(f" {numero} - {opcao['texto']}")
    return evento["opcoes"][ler_opcao(1, len(evento["opcoes"])) - 1]["efeito"]


def mostrar_mensagem(texto, estilo="bold"):
    """
    Exibe uma mensagem e espera o usuário pressionar Enter.

    Args:
        texto (str): Mensagem a exibir.
        estilo (str): Estilo do rich aplicado à mensagem. Padrão: "bold".
    """
    console.print(f"\n [{estilo}]{texto}[/]")
    pausar("Enter para continuar...")


def mostrar_final(resumo):
    """
    Exibe a tela de fim da temporada ou de demissão.

    Mostra se o técnico venceu ou perdeu e o desfecho, o clube, a meta, a posição final, os pontos, o saldo, o
    bônus de campeão da copa (quando houver) e a pontuação no ranking. Espera o usuário pressionar Enter.

    Args:
        resumo (dict): Resumo da temporada.
    """
    titulo("FIM DA TEMPORADA" if "demitido" not in resumo["desfecho"] else "VOCÊ FOI DEMITIDO")
    cor = "green" if resumo["venceu"] else "red"
    console.print(f" [bold {cor}]{'VITÓRIA' if resumo['venceu'] else 'DERROTA'}: {resumo['desfecho']}[/]\n")
    console.print(f" Clube: {resumo['clube']}   Meta: {resumo['meta']}")
    console.print(f" Posição final: {resumo['posicao']}º   Pontos: {resumo['pontos']}   Saldo: {resumo['saldo']:+d}")
    if resumo.get("copa"):
        console.print(" [bold green]Campeão da copa: bônus de 250 na pontuação.[/]")
    console.print(f" Pontuação no ranking: [bold]{resumo['pontuacao']}[/]")
    pausar("Enter para continuar...")


def mostrar_ranking(linhas):
    """
    Exibe o ranking de técnicos.

    Mostra uma tabela com técnico, clube, posição, pontos, pontuação, desfecho e data de cada temporada
    registrada, ou um aviso se ninguém terminou uma temporada. Espera o usuário pressionar Enter.

    Args:
        linhas (list): Registros do ranking.
    """
    titulo("RANKING DE TÉCNICOS")
    if not linhas:
        console.print(" Ninguém terminou uma temporada ainda.")
    else:
        tabela = Table(header_style="bold")
        for coluna in ("#", "Técnico", "Clube", "Pos", "Pts", "Pontuação", "Desfecho", "Data"):
            tabela.add_column(coluna)
        for numero, linha in enumerate(linhas, start=1):
            tabela.add_row(
                str(numero),
                *[
                    str(linha.get(campo) or "-")
                    for campo in ("tecnico", "clube", "posicao", "pontos", "pontuacao", "desfecho", "data")
                ],
            )
        console.print(tabela)
    pausar()


def escolher_save(saves):
    """
    Exibe a tela de carregar jogo e lê o save escolhido.

    Mostra uma tabela com técnico, clube, rodada e data de cada jogo salvo. Se não houver saves, mostra um
    aviso. O usuário escolhe pelo número ou digita 0 para voltar.

    Args:
        saves (list): Jogos salvos disponíveis.

    Returns:
        pathlib.Path | None: Caminho do arquivo do save escolhido, ou None se não houver saves ou o usuário
            voltar.
    """
    titulo("CARREGAR JOGO")
    if not saves:
        mostrar_mensagem("Nenhum jogo salvo encontrado.", "yellow")
        return None
    tabela = Table(header_style="bold")
    for coluna in ("#", "Técnico", "Clube", "Rodada", "Salvo em"):
        tabela.add_column(coluna)
    for numero, save in enumerate(saves, start=1):
        tabela.add_row(
            str(numero), save["tecnico"], save["clube"], str(min(save["rodada"], TOTAL_RODADAS)), save["salvo_em"]
        )
    console.print(tabela)
    console.print(" [bold]0[/] Voltar")
    escolha = ler_opcao(0, len(saves))
    return saves[escolha - 1]["caminho"] if escolha else None


def plano_provavel(estado, clube):
    """
    Indica o plano de jogo provável de um clube.

    Para o clube do usuário, devolve o próprio plano; para os outros, calcula o plano da IA contra o clube do
    usuário, considerando se o clube joga em casa no próximo jogo do usuário.

    Args:
        estado (dict): Estado atual da temporada.
        clube (dict): Dados do clube.

    Returns:
        dict: Plano de jogo com formação, estilo, ofensividade e intensidade.
    """
    if clube["id"] == estado["clube_id"]:
        return clube["plano"]
    jogo = jogo_do_jogador(estado)
    em_casa = bool(jogo) and jogo[0] == clube["id"] and not jogo_neutro(estado)
    return plano_ia(clube, clube_do_jogador(estado), em_casa)


def mostrar_clube(estado, clube_id):
    """
    Exibe a ficha de um clube até o usuário voltar.

    Mostra o nível, a força, a posição e os pontos na liga, a situação na copa, o caixa, os últimos jogos, o
    plano provável, o desenho dos titulares, os três jogadores de maior qualidade, o artilheiro e os
    desfalques. O usuário pode abrir o elenco completo com 1 ou voltar com 0.

    Args:
        estado (dict): Estado atual da temporada.
        clube_id (str): Identificador do clube a exibir.
    """
    clube = estado["clubes"][clube_id]
    nivel = NIVEIS[clube["nivel"]]
    while True:
        titulo(clube["nome"].upper())
        linha = estado["tabela"][clube_id]
        posicao = posicao_do_clube(classificacao(estado), clube_id)
        console.print(
            f" Nível: {nivel['nome']}   Força: {nivel_de_forca(clube['forca'])} {clube['forca']}"
            f"   Liga: {posicao}º com {linha['pontos']} pontos   Copa: {situacao_do_clube(estado['copa'], clube_id)}"
        )
        console.print(
            f" Caixa: {dinheiro(clube.get('caixa', 0))}"
            f"   Últimos jogos: {texto_ultimos(ultimos_resultados(estado, clube_id))}"
        )
        plano = plano_provavel(estado, clube)
        console.print(
            f" Plano provável: {plano['formacao']} · {NOMES_ESTILOS[plano['estilo']]}"
            f" · Ofensividade {plano['ofensividade']} · Intensidade {plano['intensidade']}"
        )
        console.print(desenho_formacao(clube))
        destaques = sorted(clube["elenco"], key=lambda j: j["qualidade"], reverse=True)[:3]
        console.print(" Destaques: " + ", ".join(f"{rotulo(j)} ({j['qualidade']})" for j in destaques))
        artilheiro = max(clube["elenco"], key=lambda j: j["gols"])
        if artilheiro["gols"]:
            console.print(f" Artilheiro: {rotulo(artilheiro)} com {artilheiro['gols']} gol(s)")
        desfalques = [
            f"{rotulo(j)} ({'lesionado' if j['lesao'] else 'suspenso'})" for j in clube["elenco"] if not disponivel(j)
        ]
        console.print(" Desfalques: " + (", ".join(desfalques) if desfalques else "nenhum"))
        console.print("\n 1 - Ver elenco completo   0 - Voltar")
        if ler_opcao(0, 1) == 0:
            return
        mostrar_elenco(clube)


def escolher_clube_para_ver(estado):
    """
    Lista os clubes na ordem da classificação para o usuário ver a ficha de um deles.

    Mostra o nome e a força de cada clube, com destaque para o clube do usuário. Ao escolher um número, abre a
    ficha do clube; 0 volta.

    Args:
        estado (dict): Estado atual da temporada.
    """
    while True:
        titulo("CLUBES")
        ordenada = classificacao(estado)
        for numero, linha in enumerate(ordenada, start=1):
            clube = estado["clubes"][linha["id"]]
            marca = " [yellow]◄ seu clube[/]" if clube["id"] == estado["clube_id"] else ""
            console.print(
                f" {numero:>2} - [bold {clube['cor']}]{clube['nome']}[/]  [dim]força {clube['forca']}[/]{marca}"
            )
        console.print(" 0 - Voltar")
        escolha = ler_opcao(0, len(ordenada))
        if escolha == 0:
            return
        mostrar_clube(estado, ordenada[escolha - 1]["id"])


def mostrar_copa(estado):
    """
    Exibe o chaveamento da copa.

    Para cada fase, mostra os resultados com o clube que avançou, os confrontos ainda não jogados ou "a
    definir". Depois mostra o campeão (quando houver), a situação do clube do usuário e as regras da copa.
    Espera o usuário pressionar Enter.

    Args:
        estado (dict): Estado atual da temporada.
    """
    copa = estado["copa"]
    titulo("COPA PRANCHETA")
    for fase in FASES_COPA:
        console.print(f"\n [bold]{NOMES_FASES[fase]}[/]")
        resultados = copa["resultados"].get(fase)
        if resultados:
            for resultado in resultados:
                vencedor = estado["clubes"][resultado["vencedor"]]["sigla"]
                console.print(linha_de_resultado(estado, resultado) + f"  [green]→ {vencedor}[/]")
        elif copa["confrontos"].get(fase):
            for jogo in copa["confrontos"][fase]:
                console.print(f"  {texto_jogo(estado, jogo)}")
        else:
            console.print("  [dim]a definir[/]")
    if copa["campeao"]:
        console.print(f"\n [bold green]Campeão: {estado['clubes'][copa['campeao']]['nome']}[/]")
    console.print(f"\n Seu clube: {situacao_do_clube(copa, estado['clube_id'])}")
    console.print(
        " [dim]Os 4 clubes de menor força disputam a preliminar."
        " Jogo único, empate vai para os pênaltis e a final é em campo neutro.[/]"
    )
    pausar()
