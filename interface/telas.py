from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from config import (
    BONUS_DESAFIO,
    BONUS_OBJETIVO,
    CLASSIFICADOS_DIRETO_COPA,
    DIVISOES,
    ESTILOS,
    FORMACOES,
    NIVEIS,
    NOME_JOGO,
    NOMES_ESTILOS,
    PREMIO_CAMPEAO,
    PREMIO_TITULO_COPA,
    TOTAL_RODADAS,
    VAGAS_SERIE_B_COPA,
    VERSAO,
    ZONA_ACESSO,
    ZONA_G4,
    ZONA_REBAIXAMENTO,
)
from elenco.escalacao import (
    CRITERIOS_ESCALACAO,
    disponivel,
    escalar_automatico,
    escalar_por_criterio,
    rotulo,
    valor_de_mercado,
)
from elenco.treino import pode_treinar
from interface.campo import barra
from interface.entrada import console, ler_opcao, limpar, pausar
from liga.copa import situacao_do_clube
from liga.desafios import OBJETIVOS, desafio_da_etapa
from liga.financas import extrato
from liga.tabela import posicao_do_clube, saldo
from liga.temporada import (
    adversario_de,
    classificacao,
    clube_do_jogador,
    descricao_etapa,
    divisao_do_jogador,
    etapa_atual,
    jogo_do_jogador,
    jogo_neutro,
    jogos_da_rodada,
    mata_mata,
    meta_do_clube,
    posicao_atual,
    ultimos_resultados,
)
from mercado.transferencias import dinheiro
from partida.simulacao import plano_ia

OPCOES_MENU = ("Novo jogo", "Carregar", "Ranking", "Sair")
LARGURA_NOME_CHAVE = 13
LARGURA_VAGA = LARGURA_NOME_CHAVE + 7
FASES_DA_CHAVE = ("quartas", "semifinal", "final")
TITULOS_DA_CHAVE = ("QUARTAS", "SEMIFINAL", "FINAL (neutro)", "CAMPEÃO")
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

    Mostra uma tabela com o nome, a divisão, o nível, a força e a meta da diretoria de cada clube, além de um
    aviso sobre o multiplicador do ranking para clubes menores. O usuário escolhe um clube pelo número ou
    digita 0 para voltar.

    Args:
        clubes_base (list): Lista de clubes disponíveis para escolha.

    Returns:
        str | None: Identificador do clube escolhido ou None se o usuário voltar.
    """
    titulo("ESCOLHA SEU CLUBE")
    tabela = Table(header_style="bold")
    for coluna in ("#", "Clube", "Divisão", "Nível", "Força", "Meta da diretoria"):
        tabela.add_column(coluna)
    for numero, clube in enumerate(clubes_base, start=1):
        tabela.add_row(
            str(numero),
            f"[bold {clube['cor']}]{clube['nome']}[/]",
            DIVISOES[clube.get("divisao", 1)],
            NIVEIS[clube["nivel"]]["nome"],
            f"{nivel_de_forca(clube['forca'])} {clube['forca']}",
            meta_do_clube(clube)[0],
        )
    console.print(tabela)
    console.print(" [dim]Clubes menores pontuam mais no ranking (médio x1,3, pequeno x1,6).[/]")
    console.print(
        " [dim]A carreira segue por várias temporadas: os 2 últimos da Série A caem e os 2 primeiros da B sobem.[/]"
    )
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
    "Treino",
    "Classificação",
    "Copa",
    "Rodadas e histórico",
    "Mercado da bola",
    "Clubes",
    "Finanças e objetivos",
    "Carreira",
    "Salvar",
)


def mostrar_central(estado):
    """
    Exibe a central do clube e lê a opção escolhida.

    Mostra o técnico, a temporada, a divisão, a meta, a posição na liga, o caixa, a situação na copa, os
    últimos jogos, a confiança da diretoria e o próximo compromisso. Se o clube não joga na etapa atual da
    copa, a primeira opção passa a ser acompanhar a rodada da copa. Quando há jogo, mostra também o desafio da
    diretoria para ele. As opções vão de Próximo jogo até Salvar, e 0 volta ao menu; o Treino aparece apagado
    quando o elenco já treinou na semana.

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        int: Opção escolhida, de 0 a 12.
    """
    clube = clube_do_jogador(estado)
    titulo(f"CENTRAL DO CLUBE — {clube['nome'].upper()}")
    console.print(
        f" Técnico: [bold]{estado['tecnico']}[/]   Temporada {estado.get('temporada', 1)}"
        f" · [bold]{DIVISOES[clube.get('divisao', 1)]}[/]"
    )
    console.print(
        f" Meta: [bold]{meta_do_clube(clube)[0]}[/]   Posição na {DIVISOES[clube.get('divisao', 1)]}:"
        f" [bold]{posicao_atual(estado)}º[/]"
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
        console.print(f" {texto_desafio(desafio_da_etapa(estado))}")
    else:
        console.print(" [dim]Seu clube não joga nesta fase da copa.[/]")
    console.print()
    for numero, opcao in enumerate(OPCOES_CENTRAL, start=1):
        texto_opcao = opcao if numero != 1 or jogo else "Acompanhar a rodada da copa"
        if opcao == "Treino" and not pode_treinar(estado):
            texto_opcao = "[dim]Treino (já treinou esta semana)[/]"
        console.print(f" {numero} - {texto_opcao}")
    console.print(" 0 - Voltar ao menu")
    return ler_opcao(0, len(OPCOES_CENTRAL))


def texto_desafio(desafio):
    """
    Monta a linha que apresenta o desafio da diretoria para o próximo jogo.

    Args:
        desafio (dict): Desafio com texto, prêmio e confiança.

    Returns:
        str: Linha com marcação do rich.
    """
    return (
        f"[bold]Desafio da diretoria:[/] {desafio['texto']} "
        f"[green](+{dinheiro(desafio['premio'])} e +{desafio['confianca']} de confiança)[/]"
    )


def status_jogador(jogador, titulares):
    """
    Monta o texto de situação de um jogador para a tabela do elenco.

    Indica se o jogador é titular, se está lesionado, suspenso, em grande fase ou insatisfeito e quantos
    cartões amarelos tem.

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
    if jogador.get("insatisfeito", 0):
        partes.append(f"[magenta]insatisfeito ({jogador['insatisfeito']})[/]")
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


def escalar_pelo_menu(clube):
    """
    Pergunta o critério da escalação automática e escala o time com ele.

    Args:
        clube (dict): Dados do clube, cujos titulares são alterados.

    Returns:
        str: Mensagem sobre o resultado, ou texto vazio se o usuário voltar sem escolher.
    """
    criterios = list(CRITERIOS_ESCALACAO)
    console.print(
        " "
        + "   ".join(f"[bold]{n}[/] {CRITERIOS_ESCALACAO[c]}" for n, c in enumerate(criterios, start=1))
        + "   [bold]0[/] Voltar"
    )
    opcao = ler_opcao(0, len(criterios))
    if not opcao:
        return ""
    criterio = criterios[opcao - 1]
    elenco = clube["elenco"]
    formacao = clube["plano"]["formacao"]
    clube["titulares"] = escalar_por_criterio(elenco, formacao, criterio)
    if criterio == "melhores":
        return "Escalados os melhores disponíveis, sem considerar o cansaço."
    if criterio == "descansados":
        return "Escalados os melhores, poupando quem está cansado."
    repetidos = len(set(clube["titulares"]) & set(escalar_por_criterio(elenco, formacao, "melhores")))
    if not repetidos:
        return "Escalados os reservas."
    verbo = "completa" if repetidos == 1 else "completam"
    return f"Escalados os reservas. {repetidos} do time principal {verbo} as posições sem reserva."


def editar_plano(clube):
    """
    Exibe a tela do plano de jogo e permite alterá-lo até o usuário voltar.

    Mostra a formação, o estilo, a ofensividade, a intensidade e o desenho dos titulares. As opções são trocar
    a formação (o time é reescalado automaticamente), trocar o estilo, ajustar a ofensividade e a intensidade
    de 1 a 5, fazer a escalação automática pelo critério escolhido, trocar um titular ou voltar com 0.

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
            mensagem = escalar_pelo_menu(clube)
        else:
            mensagem = trocar_titular(clube)


def estilo_na_tabela(estado, divisao, posicao, total, clube_id):
    """
    Escolhe o estilo da linha de um clube na classificação.

    O clube do técnico fica em amarelo. Na Série A, o líder fica em verde, o G4 em azul e a zona de
    rebaixamento em vermelho; na Série B, o líder e a zona de acesso ficam em verde.

    Args:
        estado (dict): Estado atual da temporada.
        divisao (int): Divisão da tabela.
        posicao (int): Posição do clube.
        total (int): Quantidade de clubes na divisão.
        clube_id (str): Identificador do clube.

    Returns:
        str: Estilo do rich, ou "" para a linha sem destaque.
    """
    if clube_id == estado["clube_id"]:
        return "bold yellow"
    if posicao == 1 or (divisao == 2 and posicao <= ZONA_ACESSO):
        return "green"
    if divisao == 1 and posicao <= ZONA_G4:
        return "blue"
    if divisao == 1 and posicao > total - ZONA_REBAIXAMENTO:
        return "red"
    return ""


def mostrar_classificacao(estado):
    """
    Exibe a tabela de classificação das divisões, começando pela do clube do técnico.

    Mostra pontos, jogos, vitórias, empates, derrotas, gols e saldo de cada clube, com as cores de
    estilo_na_tabela, a legenda e os critérios de desempate. A opção 1 troca para a outra divisão e 0 volta.

    Args:
        estado (dict): Estado atual da temporada.
    """
    divisao = divisao_do_jogador(estado)
    while True:
        outra = 2 if divisao == 1 else 1
        mostrar_tabela_da_divisao(estado, divisao)
        console.print(f"\n 1 - Ver a {DIVISOES[outra]}   0 - Voltar")
        if ler_opcao(0, 1) == 0:
            return
        divisao = outra


def mostrar_tabela_da_divisao(estado, divisao):
    """
    Desenha a classificação de uma divisão, com a legenda e os critérios de desempate.

    Args:
        estado (dict): Estado atual da temporada.
        divisao (int): Divisão a mostrar.
    """
    titulo(f"CLASSIFICAÇÃO — {DIVISOES[divisao].upper()}")
    tabela = Table(header_style="bold")
    for coluna in ("#", "Clube", "P", "J", "V", "E", "D", "GP", "GC", "SG"):
        tabela.add_column(coluna, justify="right" if coluna not in ("Clube",) else "left")
    ordenada = classificacao(estado, divisao)
    for posicao, linha in enumerate(ordenada, start=1):
        clube = estado["clubes"][linha["id"]]
        estilo = estilo_na_tabela(estado, divisao, posicao, len(ordenada), linha["id"])
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
    if divisao == 1:
        console.print(" [green]■[/] campeão  [blue]■[/] G4  [red]■[/] rebaixamento  [bold yellow]■[/] seu clube")
    else:
        console.print(" [green]■[/] acesso à Série A  [bold yellow]■[/] seu clube")
    console.print(
        " [dim]Desempate: pontos, vitórias, saldo, gols marcados, confronto direto, menos vermelhos, sorteio.[/]"
    )


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

    Pede o número da rodada a consultar. Se a rodada já foi jogada, mostra os placares da divisão do usuário
    e a súmula do jogo dele; se ainda não foi, mostra apenas os confrontos. O jogo do clube do usuário é
    marcado com uma seta. Digitar 0 volta.

    Args:
        estado (dict): Estado atual da temporada.
    """
    while True:
        titulo("RODADAS E HISTÓRICO")
        console.print(f" Rodada atual: {estado['rodada']}/{TOTAL_RODADAS}")
        numero = ler_opcao(0, TOTAL_RODADAS, " Qual rodada ver? (0 volta) > ")
        if numero == 0:
            return
        titulo(f"RODADA {numero} — {DIVISOES[divisao_do_jogador(estado)].upper()}")
        jogada = numero <= len(estado["historico"])
        if jogada:
            for jogo in estado["historico"][numero - 1]:
                if not da_minha_divisao(estado, jogo["mandante"]):
                    continue
                destaque = " [yellow]◄[/]" if estado["clube_id"] in (jogo["mandante"], jogo["visitante"]) else ""
                casa = estado["clubes"][jogo["mandante"]]
                fora = estado["clubes"][jogo["visitante"]]
                console.print(f" {casa['nome']:>22} [bold]{jogo['gm']} x {jogo['gv']}[/] {fora['nome']}{destaque}")
            console.print("\n [bold]Súmula do seu jogo:[/]")
            mostrar_sumula(estado["sumulas"].get(str(numero)))
        else:
            for jogo in jogos_da_rodada(estado, numero):
                if not da_minha_divisao(estado, jogo[0]):
                    continue
                destaque = " [yellow]◄[/]" if estado["clube_id"] in jogo else ""
                console.print(
                    f" {estado['clubes'][jogo[0]]['nome']:>22}   x   {estado['clubes'][jogo[1]]['nome']}{destaque}"
                )
        pausar()


def da_minha_divisao(estado, clube_id):
    """
    Indica se um clube joga na mesma divisão que o clube do técnico.

    Args:
        estado (dict): Estado atual da temporada.
        clube_id (str): Identificador do clube.

    Returns:
        bool: True se o clube é da divisão do técnico.
    """
    return estado["clubes"][clube_id].get("divisao", 1) == divisao_do_jogador(estado)


def pre_jogo(estado):
    """
    Exibe a tela de pré-jogo e lê a opção escolhida.

    Mostra o confronto, o local, a força dos dois clubes, o aviso de pênaltis em mata-mata, o plano de jogo do
    usuário, os titulares cansados ou insatisfeitos e o desafio da diretoria. As opções são jogar lance a
    lance, simular assistindo, simular rápido, ver só o resultado, ver o adversário, ajustar o plano, treinar
    (uma vez por semana) ou voltar com 0.

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        int: Opção escolhida, de 0 a 7.
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
    insatisfeitos = [rotulo(j) for j in titulares if j.get("insatisfeito", 0)]
    if insatisfeitos:
        console.print(f" [magenta]Titulares insatisfeitos (rendem menos): {', '.join(insatisfeitos)}[/]")
    console.print(f" {texto_desafio(desafio_da_etapa(estado))}")
    console.print("\n 1 - Jogar lance a lance   2 - Simular assistindo (Enter avança)   3 - Simular rápido")
    treino = "7 - Treinar" if pode_treinar(estado) else "[dim]7 - Treinar (já treinou)[/]"
    console.print(f" 4 - Só o resultado   5 - Ver adversário   6 - Ajustar plano   {treino}   0 - Voltar")
    return ler_opcao(0, 7)


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

    Mostra os placares (numa rodada da liga, separados por divisão, começando pela do usuário) e, conforme as
    informações recebidas, se o clube do usuário foi campeão, avançou ou foi eliminado da copa, a variação da
    confiança da diretoria, os desfalques substituídos na escalação, quem do elenco fez aniversário e as
    notícias do mercado da bola. Espera o usuário pressionar Enter.

    Args:
        estado (dict): Estado atual da temporada.
        titulo_tela (str): Título exibido no topo da tela.
        resultados (list): Resultados das partidas.
        informacao (dict): Dados do jogo do usuário, como "jogo", "letra", "variacao" e "trocados".
        noticias (list): Notícias do mercado da bola.
    """
    titulo(titulo_tela)
    if etapa_atual(estado)[0] == "liga":
        minha = divisao_do_jogador(estado)
        for divisao in sorted(DIVISOES, key=lambda d: d != minha):
            jogos = [r for r in resultados if estado["clubes"][r["mandante"]].get("divisao", 1) == divisao]
            if jogos:
                console.print(
                    f" [bold]{DIVISOES[divisao]}[/]" if divisao == minha else f"\n [dim]{DIVISOES[divisao]}[/]"
                )
            for resultado in jogos:
                console.print(linha_de_resultado(estado, resultado))
    else:
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
    desafio = informacao.get("desafio")
    if desafio:
        if desafio["cumpriu"]:
            console.print(
                f" [green]Desafio cumprido: {desafio['texto']} (+{dinheiro(desafio['premio'])},"
                f" +{desafio['confianca']} de confiança)[/]"
            )
        else:
            console.print(f" [red]Desafio não cumprido: {desafio['texto']}[/]")
    for texto_objetivo in informacao.get("objetivos", []):
        console.print(f" [bold green]Objetivo da temporada alcançado: {texto_objetivo}![/]")
    if informacao.get("aniversarios"):
        festa = " · ".join(f"{rotulo(j)} faz {j['idade']} anos" for j in informacao["aniversarios"])
        console.print(f" Aniversário no elenco: {festa}")
    receitas = {}
    for categoria, valor in estado.get("extrato_etapa", []):
        receitas[categoria] = round(receitas.get(categoria, 0) + valor, 1)
    if receitas:
        partes = [
            f"{categoria} {'+' if valor >= 0 else '-'}{dinheiro(abs(valor))}" for categoria, valor in receitas.items()
        ]
        console.print(f"\n [bold]Dinheiro da semana:[/] {' · '.join(partes)}")
        console.print(f" Caixa: [bold]{dinheiro(clube_do_jogador(estado).get('caixa', 0))}[/]")
    if noticias:
        console.print("\n [bold]Mercado da bola:[/]")
        for texto_noticia in noticias:
            console.print(f"  • {texto_noticia}")
    pausar("Enter para continuar...")


def mostrar_titulo(estado, informacao):
    """
    Anuncia o título conquistado pelo clube do usuário na etapa que acabou de terminar.

    Na copa, mostra o placar da final e o prêmio já recebido. Na liga, informa se o título veio na última
    rodada ou com rodadas de antecedência e quando o prêmio será pago. Espera o usuário pressionar Enter.

    Args:
        estado (dict): Estado atual da temporada.
        informacao (dict): Dados da etapa, com "titulo" ("liga" ou "copa") e, na copa, o "jogo" da final.
    """
    clube = clube_do_jogador(estado)
    titulo("CAMPEÃO!")
    if informacao["titulo"] == "copa":
        console.print(f" [bold {clube['cor']}]{clube['nome']} é campeão da Copa Prancheta![/]\n")
        console.print(linha_de_resultado(estado, informacao["jogo"]))
        console.print(f"\n Prêmio de {dinheiro(PREMIO_TITULO_COPA)} já está no caixa.")
    else:
        divisao = divisao_do_jogador(estado)
        pontos = estado["tabela"][clube["id"]]["pontos"]
        restantes = TOTAL_RODADAS - len(estado["historico"])
        console.print(f" [bold {clube['cor']}]{clube['nome']} é campeão da {DIVISOES[divisao]}![/]\n")
        if restantes:
            faltam = "1 rodada" if restantes == 1 else f"{restantes} rodadas"
            console.print(f" Faltando {faltam}, ninguém alcança mais os seus {pontos} pontos.")
        else:
            console.print(f" Título confirmado na última rodada, com {pontos} pontos.")
        console.print(f" O prêmio de {dinheiro(PREMIO_CAMPEAO[divisao])} entra no caixa no fim da temporada.")
    pausar("Enter para continuar...")


def mostrar_evento(evento, titulo_tela="EVENTO DA SEMANA"):
    """
    Exibe o evento da semana e, se houver opções, lê a escolha do usuário.

    Mostra o texto do evento. Se ele não tiver opções, devolve o efeito direto; caso contrário, lista as
    opções numeradas a partir de 1.

    Args:
        evento (dict): Evento preparado, com texto, efeito e opções.
        titulo_tela (str): Título da tela. Padrão "EVENTO DA SEMANA".

    Returns:
        str: Efeito do evento ou da opção escolhida.
    """
    titulo(titulo_tela)
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
    temporada = resumo.get("temporada", 1)
    titulo(f"FIM DA TEMPORADA {temporada}" if "demitido" not in resumo["desfecho"] else "VOCÊ FOI DEMITIDO")
    cor = "green" if resumo["venceu"] else "red"
    console.print(
        f" [bold {cor}]{'META CUMPRIDA' if resumo['venceu'] else 'META NÃO CUMPRIDA'}: {resumo['desfecho']}[/]\n"
    )
    console.print(f" Clube: {resumo['clube']} ({DIVISOES[resumo.get('divisao', 1)]})   Meta: {resumo['meta']}")
    console.print(f" Posição final: {resumo['posicao']}º   Pontos: {resumo['pontos']}   Saldo: {resumo['saldo']:+d}")
    if resumo.get("copa"):
        console.print(" [bold green]Campeão da copa: bônus de 250 na pontuação.[/]")
    if resumo.get("desafios"):
        console.print(f" Desafios da diretoria cumpridos: {resumo['desafios']} (+{resumo['desafios'] * BONUS_DESAFIO})")
    if resumo.get("objetivos"):
        console.print(f" Objetivos da temporada: {resumo['objetivos']} (+{resumo['objetivos'] * BONUS_OBJETIVO})")
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

    Mostra uma tabela com técnico, clube, temporada, rodada e data de cada jogo salvo. Se não houver saves,
    mostra um aviso. O usuário escolhe pelo número ou digita 0 para voltar.

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
    for coluna in ("#", "Técnico", "Clube", "Temporada", "Rodada", "Salvo em"):
        tabela.add_column(coluna)
    for numero, save in enumerate(saves, start=1):
        tabela.add_row(
            str(numero),
            save["tecnico"],
            save["clube"],
            str(save.get("temporada", 1)),
            str(min(save["rodada"], TOTAL_RODADAS)),
            save["salvo_em"],
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
        divisao = clube.get("divisao", 1)
        posicao = posicao_do_clube(classificacao(estado, divisao), clube_id)
        console.print(
            f" Nível: {nivel['nome']}   Força: {nivel_de_forca(clube['forca'])} {clube['forca']}"
            f"   {DIVISOES[divisao]}: {posicao}º com {linha['pontos']} pontos"
            f"   Copa: {situacao_do_clube(estado['copa'], clube_id)}"
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
        console.print(" Destaques: " + " · ".join(f"{rotulo(j)}, qualidade {j['qualidade']}" for j in destaques))
        artilheiro = max(clube["elenco"], key=lambda j: j["gols"])
        if artilheiro["gols"]:
            console.print(f" Artilheiro: {rotulo(artilheiro)} com {artilheiro['gols']} gol(s)")
        desfalques = [
            f"{rotulo(j)}, {'lesionado' if j['lesao'] else 'suspenso'}" for j in clube["elenco"] if not disponivel(j)
        ]
        console.print(" Desfalques: " + (", ".join(desfalques) if desfalques else "nenhum"))
        console.print("\n 1 - Ver elenco completo   0 - Voltar")
        if ler_opcao(0, 1) == 0:
            return
        mostrar_elenco(clube)


def escolher_clube_para_ver(estado):
    """
    Lista os clubes das duas divisões, cada uma na ordem da classificação, para o usuário ver a ficha de um
    deles.

    Mostra o nome e a força de cada clube, com destaque para o clube do usuário. Ao escolher um número, abre a
    ficha do clube; 0 volta.

    Args:
        estado (dict): Estado atual da temporada.
    """
    while True:
        titulo("CLUBES")
        ordenada = []
        for divisao in DIVISOES:
            console.print(f" [bold]{DIVISOES[divisao]}[/]")
            for linha in classificacao(estado, divisao):
                ordenada.append(linha)
                mostrar_clube_na_lista(estado, len(ordenada), linha["id"])
        console.print(" 0 - Voltar")
        escolha = ler_opcao(0, len(ordenada))
        if escolha == 0:
            return
        mostrar_clube(estado, ordenada[escolha - 1]["id"])


def mostrar_clube_na_lista(estado, numero, clube_id):
    """
    Imprime a linha de um clube na lista de clubes.

    Args:
        estado (dict): Estado atual da temporada.
        numero (int): Número da opção.
        clube_id (str): Identificador do clube.
    """
    clube = estado["clubes"][clube_id]
    marca = " [yellow]◄ seu clube[/]" if clube_id == estado["clube_id"] else ""
    console.print(f" {numero:>2} - [bold {clube['cor']}]{clube['nome']}[/]  [dim]força {clube['forca']}[/]{marca}")


def nome_na_chave(clube):
    """
    Devolve o nome do clube num tamanho que cabe na chave da copa.

    Nomes de até LARGURA_NOME_CHAVE (13) caracteres ficam inteiros; os mais longos ficam só com a primeira
    palavra, como "Tropeiros" para "Tropeiros de Gravataí".

    Args:
        clube (dict): Clube a ser mostrado.

    Returns:
        str: Nome curto do clube.
    """
    nome = clube["nome"]
    return nome if len(nome) <= LARGURA_NOME_CHAVE else nome.split()[0]


def resultado_entre(resultados, time_a, time_b):
    """
    Procura o resultado do jogo entre dois clubes, em qualquer ordem de mando.

    Args:
        resultados (list[dict]): Resultados de uma fase da copa.
        time_a (str): Identificador de um dos clubes.
        time_b (str): Identificador do outro clube.

    Returns:
        dict | None: Resultado do confronto ou None se ele ainda não foi jogado.
    """
    return next((r for r in resultados if {r["mandante"], r["visitante"]} == {time_a, time_b}), None)


def placar_na_chave(resultado, clube_id):
    """
    Monta o placar de um clube num confronto da chave, com os pênaltis entre parênteses.

    Args:
        resultado (dict | None): Resultado do confronto, ou None se ainda não foi jogado.
        clube_id (str): Clube cujo placar será mostrado.

    Returns:
        str: Gols do clube (ex.: "2" ou "1 (4)"), ou texto vazio se o jogo ainda não aconteceu.
    """
    if not resultado:
        return ""
    gols = resultado["gm"] if resultado["mandante"] == clube_id else resultado["gv"]
    penaltis = resultado.get("penaltis")
    return f"{gols} ({penaltis[clube_id]})" if penaltis else str(gols)


def vaga_na_chave(estado, clube_id, resultado=None, vazio="a definir"):
    """
    Monta o texto e o estilo de uma vaga da chave da copa.

    A vaga tem largura fixa (LARGURA_VAGA): uma seta para o clube do usuário, o nome curto e o placar. Quem
    venceu o confronto aparece em negrito na cor do clube, quem caiu aparece apagado e uma vaga ainda sem
    clube mostra o texto de vazio.

    Args:
        estado (dict): Estado atual da temporada.
        clube_id (str | None): Clube que ocupa a vaga, ou None se ela ainda não foi definida.
        resultado (dict | None): Resultado do confronto que o clube jogou nessa fase. Padrão None.
        vazio (str): Texto para a vaga sem clube. Padrão "a definir".

    Returns:
        tuple: (texto, estilo) da vaga, com o estilo no formato do rich.
    """
    if clube_id is None:
        return f" {vazio}".ljust(LARGURA_VAGA), "dim"
    clube = estado["clubes"][clube_id]
    marca = "►" if clube_id == estado["clube_id"] else " "
    texto = f"{marca}{nome_na_chave(clube):<{LARGURA_NOME_CHAVE}} {placar_na_chave(resultado, clube_id):>5}"
    if resultado and resultado["vencedor"] != clube_id:
        return texto, "dim"
    if resultado:
        return texto, f"bold {clube['cor']}"
    return texto, clube["cor"]


def desenhar_chave(colunas, titulos):
    """
    Desenha uma chave de mata-mata em texto, com as linhas ligando cada confronto ao vencedor.

    Cada coluna é uma fase. Na primeira, as vagas ficam a cada duas linhas; nas seguintes, cada vaga fica na
    altura do meio do confronto que a alimenta, ligada por "┐", "│", "├" e "┘". As vagas são encaixadas
    por cima da grade de linhas, com o estilo de cada uma.

    Args:
        colunas (list[list[tuple]]): Vagas de cada fase, como (texto, estilo); cada coluna tem metade das
            vagas da anterior.
        titulos (tuple[str]): Título de cada coluna.

    Returns:
        list[str]: Linhas prontas para imprimir, com marcação do rich.
    """
    passo = LARGURA_VAGA + 5
    alturas = [list(range(0, 2 * len(colunas[0]) - 1, 2))]
    for coluna in colunas[1:]:
        anterior = alturas[-1]
        alturas.append([(anterior[2 * j] + anterior[2 * j + 1]) // 2 for j in range(len(coluna))])
    total_linhas = 2 * len(colunas[0]) - 1
    largura = passo * len(colunas)
    grade = [[" "] * largura for _ in range(total_linhas)]
    vagas = {}
    for k, coluna in enumerate(colunas):
        inicio = k * passo
        for j, vaga in enumerate(coluna):
            vagas[(alturas[k][j], inicio)] = vaga
        if k + 1 == len(colunas):
            continue
        borda = inicio + LARGURA_VAGA + 1
        for j, meio in enumerate(alturas[k + 1]):
            cima, baixo = alturas[k][2 * j], alturas[k][2 * j + 1]
            grade[cima][borda], grade[cima][borda + 1] = "─", "┐"
            grade[baixo][borda], grade[baixo][borda + 1] = "─", "┘"
            for linha in range(cima + 1, baixo):
                grade[linha][borda + 1] = "│"
            grade[meio][borda + 1], grade[meio][borda + 2], grade[meio][borda + 3] = "├", "─", "─"
    cabecalho = "".join(f"{titulo_coluna:<{passo}}" for titulo_coluna in titulos).rstrip()
    saida = [f" [bold]{cabecalho}[/]"]
    for linha in range(total_linhas):
        partes = []
        posicao = 0
        for (linha_vaga, inicio), (texto, estilo) in sorted(vagas.items(), key=lambda item: item[0][1]):
            if linha_vaga != linha:
                continue
            partes.append(f"[dim]{''.join(grade[linha][posicao:inicio])}[/]")
            partes.append(f"[{estilo}]{escape(texto)}[/]")
            posicao = inicio + len(texto)
        partes.append(f"[dim]{''.join(grade[linha][posicao:]).rstrip()}[/]")
        saida.append(" " + "".join(partes))
    return saida


def colunas_da_chave_principal(estado):
    """
    Monta as vagas das quartas, da semifinal, da final e do campeão a partir dos confrontos e resultados.

    As quartas seguem a ordem do sorteio, e cada vaga das fases seguintes é ocupada pelo vencedor do confronto
    correspondente da fase anterior, como manda a chave. Antes do sorteio, as quartas aparecem como "a
    sortear".

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        list[list[tuple]]: Quatro colunas de vagas (8, 4, 2 e 1), como (texto, estilo).
    """
    copa = estado["copa"]
    confrontos = copa["confrontos"].get("quartas")
    clubes = [clube for jogo in confrontos for clube in jogo] if confrontos else [None] * 8
    colunas = []
    for fase in FASES_DA_CHAVE:
        resultados = copa["resultados"].get(fase, [])
        vazio = "a sortear" if fase == "quartas" else "a definir"
        coluna = []
        vencedores = []
        for j in range(0, len(clubes), 2):
            time_a, time_b = clubes[j], clubes[j + 1]
            resultado = resultado_entre(resultados, time_a, time_b) if time_a and time_b else None
            coluna.append(vaga_na_chave(estado, time_a, resultado, vazio))
            coluna.append(vaga_na_chave(estado, time_b, resultado, vazio))
            vencedores.append(resultado["vencedor"] if resultado else None)
        colunas.append(coluna)
        clubes = vencedores
    campeao = clubes[0]
    if campeao:
        clube = estado["clubes"][campeao]
        colunas.append([(f" {clube['nome']}", f"bold {clube['cor']}")])
    else:
        colunas.append([(" a definir", "dim")])
    return colunas


def colunas_da_preliminar(estado):
    """
    Monta as vagas da fase preliminar e dos dois classificados para as quartas.

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        list[list[tuple]]: Duas colunas de vagas (4 e 2), como (texto, estilo).
    """
    copa = estado["copa"]
    resultados = copa["resultados"].get("preliminar", [])
    coluna = []
    classificados = []
    for time_a, time_b in copa["confrontos"]["preliminar"]:
        resultado = resultado_entre(resultados, time_a, time_b)
        coluna.append(vaga_na_chave(estado, time_a, resultado))
        coluna.append(vaga_na_chave(estado, time_b, resultado))
        classificados.append(vaga_na_chave(estado, resultado["vencedor"] if resultado else None))
    return [coluna, classificados]


def mostrar_copa(estado):
    """
    Exibe a Copa Prancheta como uma chave de mata-mata.

    Mostra primeiro a fase preliminar com os dois classificados e depois a chave principal, das quartas ao
    campeão, ligando cada confronto ao vencedor. Vencedores aparecem em negrito, eliminados apagados e o
    clube do usuário marcado com "►"; os pênaltis vão entre parênteses. Antes do sorteio das quartas, lista
    os clubes já garantidos. No fim, mostra a situação do clube do usuário e as regras da copa, e espera o
    usuário pressionar Enter.

    Args:
        estado (dict): Estado atual da temporada.
    """
    copa = estado["copa"]
    titulo("COPA PRANCHETA")
    console.print()
    for linha in desenhar_chave(colunas_da_preliminar(estado), ("FASE PRELIMINAR", "VAI ÀS QUARTAS")):
        console.print(linha)
    console.print()
    for linha in desenhar_chave(colunas_da_chave_principal(estado), TITULOS_DA_CHAVE):
        console.print(linha)
    if "quartas" not in copa["confrontos"]:
        garantidos = ", ".join(estado["clubes"][clube_id]["nome"] for clube_id in copa["classificados"])
        console.print(f"\n [dim]Já garantidos nas quartas, que serão sorteadas: {garantidos}[/]")
    if copa["campeao"]:
        console.print(f"\n [bold green]Campeão: {estado['clubes'][copa['campeao']]['nome']}[/]")
    console.print(f"\n Seu clube: {situacao_do_clube(copa, estado['clube_id'])}")
    console.print(
        f" [dim]Os {CLASSIFICADOS_DIRETO_COPA} primeiros da Série A na última temporada (na primeira, os mais fortes)"
        " vão direto às quartas; só os piores colocados da Série A e os"
        f" {VAGAS_SERIE_B_COPA} melhores da Série B disputam a preliminar."
        " Jogo único, empate vai para os pênaltis e a final é em campo neutro.[/]"
    )
    pausar()


def mostrar_financas(estado):
    """
    Exibe as finanças do clube e os objetivos da temporada.

    Mostra o caixa, o extrato da temporada por categoria (receitas em verde, despesas em vermelho), o total de
    desafios da diretoria cumpridos e a lista de objetivos da temporada, com o que já foi alcançado. Espera o
    usuário pressionar Enter.

    Args:
        estado (dict): Estado atual da temporada.
    """
    clube = clube_do_jogador(estado)
    titulo("FINANÇAS E OBJETIVOS")
    console.print(f" Caixa atual: [bold]{dinheiro(clube.get('caixa', 0))}[/]\n")
    linhas = extrato(estado)
    if linhas:
        tabela = Table(title="Extrato da temporada", title_justify="left", header_style="bold")
        tabela.add_column("Categoria")
        tabela.add_column("Valor", justify="right")
        for categoria, valor in linhas:
            cor = "green" if valor >= 0 else "red"
            tabela.add_row(categoria, f"[{cor}]{'+' if valor >= 0 else '-'}{dinheiro(abs(valor))}[/]")
        console.print(tabela)
    else:
        console.print(" [dim]Nenhuma entrada ou saída de dinheiro ainda.[/]")
    console.print(
        "\n Receitas de cada jogo: bilheteria nos jogos em casa (maior quando o time vem vencendo), cota de TV"
        " por rodada da liga e prêmio por resultado."
    )
    cumpridos = estado.get("desafios_cumpridos", 0)
    console.print(f"\n [bold]Desafios da diretoria cumpridos:[/] {cumpridos} (+{BONUS_DESAFIO} pontos cada no ranking)")
    console.print(f"\n [bold]Objetivos da temporada[/] (+{BONUS_OBJETIVO} pontos e +R$ 2,0 mi cada):")
    feitos = estado.get("objetivos", [])
    for chave, texto in OBJETIVOS.items():
        marca = "[green]✓[/]" if chave in feitos else "[dim]·[/]"
        console.print(f"  {marca} {texto}")
    pausar()
