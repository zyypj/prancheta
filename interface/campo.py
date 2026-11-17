import time

from rich.text import Text

from config import NOMES_ESTILOS, PAUSA_RAPIDA
from elenco.escalacao import limitar, rotulo
from interface.entrada import TECLADO_REAL, TERMINAL_REAL, console, desenhar_no_lugar, limpar, tecla_pressionada
from partida.lances import minuto_texto

LARGURA_ZONA = 17
LARGURA_CAMPO = LARGURA_ZONA * 3 + 4
SEPARADORES = (0, LARGURA_ZONA + 1, 2 * LARGURA_ZONA + 2, LARGURA_CAMPO - 1)
ALTURA_CAMPO = 7
LARGURA_AREA = 7
LINHAS_FAIXA = {0: 1, 1: 3, 2: 5}
LINHAS_FAIXA_AREA = {0: 2, 1: 3, 2: 4}
COLUNAS_ZONA = {
    "saida": LARGURA_AREA // 2 + 1,
    "defesa": (LARGURA_AREA + 1 + SEPARADORES[1]) // 2,
    "meio": LARGURA_CAMPO // 2,
    "intermediaria": SEPARADORES[2] - 3,
    "linha_de_fundo": LARGURA_CAMPO - 3,
    "ataque": (SEPARADORES[2] + LARGURA_CAMPO - 2 - LARGURA_AREA) // 2,
    "area": LARGURA_CAMPO - 2 - LARGURA_AREA // 2,
    "gol": LARGURA_CAMPO - 2,
}
GRAMADO = "on dark_green"
PAUSAS_LONGAS = ("gol", "penalti_fim", "vermelho", "intervalo", "fim", "var", "lesao", "trave", "oportunidade")


def barra(valor, tamanho=10):
    """
    Monta uma barra de progresso colorida para um valor percentual.

    A parte cheia é proporcional ao valor, limitado entre 0 e 100, e fica verde a partir de 60, amarela a
    partir de 35 e vermelha abaixo disso. Ao lado da barra aparece o valor arredondado com o símbolo de
    porcentagem.

    Args:
        valor (float): Valor percentual a representar, como a energia de um jogador.
        tamanho (int): Quantidade de caracteres da barra. Padrão 10.

    Returns:
        str: Barra formatada com marcação do rich.
    """
    cheio = round(limitar(valor, 0, 100) / 100 * tamanho)
    cor = "green" if valor >= 60 else ("yellow" if valor >= 35 else "red")
    return f"[{cor}]{'█' * cheio}[/][dim]{'░' * (tamanho - cheio)}[/] {round(valor)}%"


def posicao_alvo(partida, clube_jogador):
    """
    Calcula onde a bola deve aparecer no desenho do campo.

    A coluna vem da zona da bola (saída, campo de defesa, meio, intermediária, entrada da área, linha de
    fundo, área ou gol), usando o meio-campo quando nenhum time tem a posse, e a linha vem da faixa do campo;
    na linha de fundo, a bola fica colada na lateral de cima ou de baixo. Como o campo é desenhado com o clube
    do jogador atacando para a direita, a coluna é espelhada quando a bola está com o adversário.

    Args:
        partida (dict): Estado da partida em andamento.
        clube_jogador (str): Identificador do clube controlado pelo jogador.

    Returns:
        tuple: Coluna e linha da bola na grade do campo.
    """
    bola = partida["bola"]
    faixa = bola.get("faixa", 1)
    zona = bola["zona"] if bola["time"] is not None else "meio"
    if zona == "gol":
        linha = 3
    elif zona == "linha_de_fundo":
        linha = ALTURA_CAMPO - 1 if faixa == 2 else 0
    elif zona == "area":
        linha = LINHAS_FAIXA_AREA[faixa]
    else:
        linha = LINHAS_FAIXA[faixa]
    coluna = COLUNAS_ZONA[zona]
    if bola["time"] is not None and bola["time"] != clube_jogador:
        coluna = LARGURA_CAMPO - 1 - coluna
    return coluna, linha


def gramado_vazio():
    """
    Cria a grade de caracteres do campo sem a bola.

    Desenha as divisórias entre as zonas, as traves nas duas pontas, as grandes áreas, as marcas de pênalti e
    a marca do centro do campo.

    Returns:
        list: Lista de linhas, cada uma uma lista de caracteres do gramado.
    """
    grade = [[" "] * LARGURA_CAMPO for _ in range(ALTURA_CAMPO)]
    for linha in grade:
        for separador in SEPARADORES:
            linha[separador] = "│"
    for linha in (2, 3, 4):
        grade[linha][0] = "▌"
        grade[linha][-1] = "▐"
    esquerda = LARGURA_AREA + 1
    direita = LARGURA_CAMPO - 2 - LARGURA_AREA
    for coluna in range(1, esquerda):
        grade[1][coluna] = grade[5][coluna] = "─"
    for coluna in range(direita + 1, LARGURA_CAMPO - 1):
        grade[1][coluna] = grade[5][coluna] = "─"
    grade[1][esquerda], grade[5][esquerda] = "┐", "┘"
    grade[1][direita], grade[5][direita] = "┌", "└"
    for linha in (2, 3, 4):
        grade[linha][esquerda] = "│"
        grade[linha][direita] = "│"
    grade[3][LARGURA_AREA // 2 + 1] = "·"
    grade[3][LARGURA_CAMPO - 2 - LARGURA_AREA // 2] = "·"
    grade[3][LARGURA_CAMPO // 2] = "·"
    return grade


def desenhar_campo(coluna, linha):
    """
    Monta o desenho completo do campo com a bola na posição indicada.

    Coloca a moldura superior e inferior, pinta o gramado de verde, troca o caractere da posição informada
    pela bola e acrescenta embaixo os rótulos das zonas de defesa, meio e ataque.

    Args:
        coluna (int): Coluna da bola na grade do campo.
        linha (int): Linha da bola na grade do campo.

    Returns:
        Text: Texto do rich com o campo pronto para imprimir.
    """
    topo = "┌" + "┬".join("─" * LARGURA_ZONA for _ in range(3)) + "┐"
    base = "└" + "┴".join("─" * LARGURA_ZONA for _ in range(3)) + "┘"
    campo = Text()
    campo.append(topo + "\n", style=f"white {GRAMADO}")
    for indice_linha, caracteres in enumerate(gramado_vazio()):
        for indice, caractere in enumerate(caracteres):
            if indice_linha == linha and indice == coluna:
                campo.append("●", style=f"bold bright_white {GRAMADO}")
            else:
                campo.append(caractere, style=f"white {GRAMADO}")
        campo.append("\n")
    campo.append(base + "\n", style=f"white {GRAMADO}")
    rotulos = "DEFESA".center(LARGURA_ZONA + 1) + "MEIO".center(LARGURA_ZONA + 1) + "ATAQUE".center(LARGURA_ZONA + 1)
    campo.append(" " + rotulos, style="dim")
    return campo


def cabecalho(partida, clube_jogador):
    """
    Exibe o placar e o resumo do plano de jogo no topo da tela da partida.

    A primeira linha mostra os clubes nas suas cores, o placar, o tempo, o minuto e o aviso de chuva forte
    quando houver. A segunda mostra a formação, o estilo, a ofensividade, a intensidade, as substituições
    feitas pelo jogador e se a partida está sendo jogada lance a lance ou simulada.

    Args:
        partida (dict): Estado da partida em andamento.
        clube_jogador (str): Identificador do clube controlado pelo jogador.
    """
    casa = partida["times"][partida["casa"]]
    fora = partida["times"][partida["fora"]]
    tempo = "1º TEMPO" if partida["tempo"] == 1 else "2º TEMPO"
    clima = "  [cyan]chuva forte[/]" if partida["chuva"] else ""
    console.print(
        f" [bold {casa['cor']}]{casa['nome']}[/] [bold]{casa['gols']} x {fora['gols']}[/]"
        f" [bold {fora['cor']}]{fora['nome']}[/]"
        f"   [dim]{tempo}[/] [bold]{minuto_texto(partida)}[/]{clima}"
    )
    meu = partida["times"][clube_jogador]
    plano = meu["plano"]
    ritmo = "rápido" if partida["velocidade"] == "rapida" else "assistindo"
    modo = "jogando lance a lance" if partida["modo"] == "jogar" else f"simulando ({ritmo})"
    console.print(
        f" [dim]{plano['formacao']} · {NOMES_ESTILOS[plano['estilo']]} · Ofensividade {plano['ofensividade']}"
        f" · Intensidade {plano['intensidade']} · Substituições {meu['subs']}/5 · {modo}[/]"
    )


def desenhar_quadro(partida, clube_jogador, coluna, linha, pergunta, opcoes, destaque, rodape=None, aviso=None):
    """
    Imprime um quadro completo da tela da partida.

    Mostra o cabeçalho, o campo com a bola, as últimas linhas da narração com a mais recente em destaque e,
    quando algum time tem a posse, quem está com a bola, sua qualidade e sua energia. Por fim, mostra o
    destaque, a pergunta e as opções numeradas, sempre com a opção 0 para pausar.

    Args:
        partida (dict): Estado da partida em andamento.
        clube_jogador (str): Identificador do clube controlado pelo jogador.
        coluna (int): Coluna da bola na grade do campo.
        linha (int): Linha da bola na grade do campo.
        pergunta (str | None): Pergunta feita ao jogador, ou None para não mostrar.
        opcoes (list | None): Textos das opções de resposta, ou None para não mostrar.
        destaque (str | None): Mensagem de destaque, como o aviso de gol, ou None.
        rodape (str | None): Texto extra no fim da linha de opções, como o aviso das revelações. Padrão None.
        aviso (str | None): Linha apagada no pé da tela, como as teclas da simulação rápida. Padrão None.
    """
    cabecalho(partida, clube_jogador)
    console.print(desenhar_campo(coluna, linha))
    linhas = partida["narracao"]
    for indice, texto in enumerate(linhas):
        estilo = "bold" if indice == len(linhas) - 1 else "dim"
        console.print(f" [{estilo}]{texto}[/]")
    portador = partida.get("portador")
    if portador and partida["bola"]["time"]:
        dono = partida["times"][partida["bola"]["time"]]
        console.print(
            f"\n Bola com: [bold {dono['cor']}]{rotulo(portador)}[/] · qualidade {portador['qualidade']}"
            f"   Energia {barra(portador['energia'])}"
        )
    if destaque:
        console.print(f"\n {destaque}")
    if pergunta:
        console.print(f"\n [bold yellow]{pergunta}[/]")
    if opcoes:
        console.print(
            " "
            + "   ".join(f"[bold]{numero}[/] {texto}" for numero, texto in enumerate(opcoes, start=1))
            + "   [bold]0[/] Pausar"
            + (f"   {rodape}" if rodape else "")
        )
    if aviso:
        console.print(f"\n [dim]{aviso}[/]")


def mostrar_partida(
    partida, clube_jogador, pergunta=None, opcoes=None, animar=False, destaque=None, rodape=None, aviso=None
):
    """
    Atualiza a tela da partida, levando a bola até a posição atual.

    Na primeira chamada limpa a tela e guarda a posição da bola em partida["tela"]. Com animação ligada, em
    terminal real e na velocidade normal, a bola anda de três em três colunas até o destino, e os quadros
    intermediários são desenhados sem pergunta, opções nem destaque. Cada quadro é redesenhado no mesmo lugar
    da tela e, ao final, a posição guardada é atualizada.

    Args:
        partida (dict): Estado da partida em andamento.
        clube_jogador (str): Identificador do clube controlado pelo jogador.
        pergunta (str | None): Pergunta feita ao jogador. Padrão None.
        opcoes (list | None): Textos das opções de resposta. Padrão None.
        animar (bool): Se a bola deve se mover aos poucos até o destino. Padrão False.
        destaque (str | None): Mensagem de destaque, como o aviso de gol. Padrão None.
        rodape (str | None): Texto extra no fim da linha de opções. Padrão None.
        aviso (str | None): Linha apagada no pé da tela. Padrão None.
    """
    alvo = posicao_alvo(partida, clube_jogador)
    if "tela" not in partida:
        limpar()
        partida["tela"] = {"coluna": alvo[0], "linha": alvo[1]}
    atual = partida["tela"]
    passos = []
    if animar and TERMINAL_REAL and partida["velocidade"] == "normal":
        coluna = atual["coluna"]
        while abs(alvo[0] - coluna) > 3:
            coluna += 3 if alvo[0] > coluna else -3
            passos.append((coluna, alvo[1]))
    passos.append(alvo)
    for coluna, linha in passos:
        intermediario = (coluna, linha) != alvo
        desenhar_no_lugar(
            lambda c=coluna, lin=linha, i=intermediario: desenhar_quadro(
                partida,
                clube_jogador,
                c,
                lin,
                None if i else pergunta,
                None if i else opcoes,
                None if i else destaque,
                None if i else rodape,
                aviso,
            )
        )
        if intermediario:
            time.sleep(0.03)
    atual["coluna"], atual["linha"] = alvo


def destaque_do_evento(partida, evento):
    """
    Gera a mensagem de destaque de um evento da partida.

    Args:
        partida (dict): Estado da partida em andamento.
        evento (dict): Evento que acabou de acontecer.

    Returns:
        str | None: Faixa de gol na cor do time que marcou, ou None se o evento não for gol.
    """
    if evento["tipo"] == "gol":
        cor = partida["times"][evento["time"]]["cor"]
        return f"[bold {cor} reverse]   G O O O O O L !   [/]"
    return None


def criar_exibidor(clube_jogador, ao_pausar=None):
    """
    Cria a função que mostra cada evento da partida na tela.

    A função criada guarda o clube do jogador e a ação de pausa, e é chamada pelo motor da partida a cada
    evento.

    Args:
        clube_jogador (str): Identificador do clube controlado pelo jogador.
        ao_pausar (callable | None): Função chamada com a partida e o clube do jogador quando o usuário pede
            pausa. Padrão None.

    Returns:
        callable: Função exibir(partida, evento).
    """

    def exibir(partida, evento):
        """
        Mostra um evento da partida e espera o ritmo escolhido.

        Não faz nada se a partida estiver em pausa. Em terminal real redesenha a tela com animação; fora dele
        apenas imprime a última linha da narração e o destaque. Na velocidade rápida espera um tempo curto,
        três vezes maior em eventos importantes como gol, expulsão e intervalo, e confere sem travar se o
        usuário apertou uma tecla: P abre a pausa e N volta para a velocidade normal. Na velocidade normal
        espera o Enter: P abre a pausa e R passa a simular o resto da partida em velocidade rápida.

        Args:
            partida (dict): Estado da partida em andamento.
            evento (dict): Evento que acabou de acontecer.
        """
        if partida.get("em_pausa"):
            return
        destaque = destaque_do_evento(partida, evento)
        rapida = partida["velocidade"] == "rapida"
        aviso = "Simulação rápida · P pausa · N volta a assistir" if rapida and TECLADO_REAL else None
        if TERMINAL_REAL:
            mostrar_partida(partida, clube_jogador, animar=True, destaque=destaque, aviso=aviso)
        else:
            console.print(f" {partida['narracao'][-1]}")
            if destaque:
                console.print(f" {destaque}")
        if rapida:
            time.sleep(PAUSA_RAPIDA * (3 if evento["tipo"] in PAUSAS_LONGAS else 1))
            tecla = tecla_pressionada()
            if tecla == "p" and ao_pausar:
                ao_pausar(partida, clube_jogador)
            elif tecla == "n":
                partida["velocidade"] = "normal"
            return
        resposta = console.input(" [dim]Enter avança · P pausa · R simula rápido[/] ").strip().lower()
        if resposta == "p" and ao_pausar:
            ao_pausar(partida, clube_jogador)
        elif resposta == "r":
            partida["modo"] = "simular"
            partida["velocidade"] = "rapida"

    return exibir
