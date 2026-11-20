import math
import time
from itertools import groupby

from rich.text import Text

from config import NOMES_ESTILOS, PAUSA_RAPIDA
from elenco.escalacao import limitar, rotulo
from interface.entrada import (
    TECLADO_REAL,
    TEM_EMOJI,
    TERMINAL_REAL,
    console,
    desenhar_no_lugar,
    limpar,
    tecla_pressionada,
)
from partida.lances import minuto_texto

COMPRIMENTO_REAL = 105
LARGURA_REAL = 68
RAIO_DO_CIRCULO = 9.15
FUNDO_GRANDE_AREA = 16.5
MEIA_LARGURA_GRANDE_AREA = 20.16
FUNDO_PEQUENA_AREA = 5.5
MEIA_LARGURA_PEQUENA_AREA = 9.16
DISTANCIA_PENALTI = 11
COLUNAS_GRAMADO = 57
MARGEM_GOL = 2
LARGURA_CAMPO = COLUNAS_GRAMADO + 2 * MARGEM_GOL
LINHAS_CAMPO = 11
ALTURA_PIXELS = LINHAS_CAMPO * 2
CENTRO_X = LARGURA_CAMPO // 2
CENTRO_Y = ALTURA_PIXELS // 2
LARGURA_FAIXA_GRAMA = 5
GRAMA_CLARA = "#3f8f45"
GRAMA_ESCURA = "#35803b"
COR_LINHA = "#eef3ea"
COR_REDE = "#b9c2bd"
COR_BOLA = "#ffffff"
BOLA_DESENHADA = "⚽"
LINHAS_FAIXA = {0: 2, 1: 5, 2: 8}
LINHAS_FAIXA_AREA = {0: 3, 1: 5, 2: 7}


def coluna_em_metros(metros):
    """
    Converte a distância até a linha de fundo esquerda na coluna correspondente do desenho.

    Args:
        metros (float): Distância real, de 0 a 105 metros.

    Returns:
        int: Coluna do desenho do campo.
    """
    return MARGEM_GOL + round(metros / COMPRIMENTO_REAL * (COLUNAS_GRAMADO - 1))


def recuo_em_pixels(metros):
    """
    Converte uma distância real no sentido da largura do campo em pixels do desenho.

    Args:
        metros (float): Distância real em metros.

    Returns:
        float: Distância em pixels, sem arredondar.
    """
    return metros / LARGURA_REAL * (CENTRO_Y - 1) * 2


COLUNAS_ZONA = {
    "saida": coluna_em_metros(6),
    "defesa": coluna_em_metros(25),
    "meio": CENTRO_X,
    "intermediaria": coluna_em_metros(66),
    "ataque": coluna_em_metros(80),
    "lateral": coluna_em_metros(80),
    "area": coluna_em_metros(95),
    "marca_penalti": LARGURA_CAMPO - 1 - coluna_em_metros(DISTANCIA_PENALTI),
    "pequena_area": coluna_em_metros(101),
    "linha_de_fundo": coluna_em_metros(103),
    "linha_do_gol": LARGURA_CAMPO - 1 - MARGEM_GOL,
    "escanteio": LARGURA_CAMPO - 1 - MARGEM_GOL,
    "gol": LARGURA_CAMPO - 2,
}
ZONAS_NO_CENTRO = ("gol", "marca_penalti", "pequena_area")
ZONAS_NA_BEIRA = ("linha_de_fundo", "escanteio", "lateral")
ZONAS_PERTO_DO_GOL = ("area", "linha_do_gol")
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

    A coluna vem da zona da bola, usando o meio-campo quando nenhum time tem a posse, e a linha vem da faixa
    do campo. Na marca do pênalti, na pequena área e no gol a bola fica no centro; na linha de fundo, no
    escanteio e no lateral, ela fica colada na beira de cima ou de baixo. Como o campo é desenhado com o clube
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
    if zona in ZONAS_NO_CENTRO:
        linha = LINHAS_CAMPO // 2
    elif zona in ZONAS_NA_BEIRA:
        linha = LINHAS_CAMPO - 1 if faixa == 2 else 0
    elif zona in ZONAS_PERTO_DO_GOL:
        linha = LINHAS_FAIXA_AREA[faixa]
    else:
        linha = LINHAS_FAIXA[faixa]
    coluna = COLUNAS_ZONA[zona]
    if bola["time"] is not None and bola["time"] != clube_jogador:
        coluna = LARGURA_CAMPO - 1 - coluna
    return coluna, linha


def cor_da_grama(coluna):
    """
    Devolve a cor da faixa de grama cortada em uma coluna do campo.

    Args:
        coluna (int): Coluna do desenho.

    Returns:
        str | None: Cor da grama, ou None se a coluna fica fora do gramado, atrás dos gols.
    """
    if not MARGEM_GOL <= coluna < LARGURA_CAMPO - MARGEM_GOL:
        return None
    faixa = (abs(coluna - CENTRO_X) + LARGURA_FAIXA_GRAMA // 2) // LARGURA_FAIXA_GRAMA
    return GRAMA_CLARA if faixa % 2 == 0 else GRAMA_ESCURA


def marcar(pixels, coluna, linha, cor=COR_LINHA):
    """
    Pinta um ponto do campo e os seus reflexos nos outros três quadrantes.

    Args:
        pixels (list): Grade de cores do campo.
        coluna (int): Coluna do ponto no quadrante superior esquerdo.
        linha (int): Linha do ponto no quadrante superior esquerdo.
        cor (str): Cor do ponto. Padrão COR_LINHA.
    """
    for y in (linha, ALTURA_PIXELS - linha):
        for x in (coluna, LARGURA_CAMPO - 1 - coluna):
            pixels[y][x] = cor


def marcar_arco(pixels, centro_x, inicio, fim, coluna_minima=0):
    """
    Pinta um arco de raio igual ao do círculo central, centrado na linha do meio da largura do campo.

    Args:
        pixels (list): Grade de cores do campo.
        centro_x (int): Coluna do centro do arco.
        inicio (int): Ângulo inicial em graus.
        fim (int): Ângulo final em graus.
        coluna_minima (int): Só pinta da coluna seguinte a esta em diante. Padrão 0.
    """
    raio_x = RAIO_DO_CIRCULO / COMPRIMENTO_REAL * (COLUNAS_GRAMADO - 1)
    raio_y = recuo_em_pixels(RAIO_DO_CIRCULO)
    for angulo in range(inicio, fim + 1, 5):
        radianos = math.radians(angulo)
        coluna = round(centro_x + raio_x * math.cos(radianos))
        linha = round(CENTRO_Y - raio_y * math.sin(radianos))
        if coluna > coluna_minima:
            marcar(pixels, coluna, linha)


def marcar_area(pixels, fundo, meia_largura):
    """
    Pinta o contorno de uma área a partir da linha de fundo.

    Args:
        pixels (list): Grade de cores do campo.
        fundo (float): Profundidade da área em metros.
        meia_largura (float): Metade da largura da área em metros.

    Returns:
        int: Coluna da linha frontal da área.
    """
    frente = coluna_em_metros(fundo)
    topo = CENTRO_Y - round(recuo_em_pixels(meia_largura))
    for coluna in range(MARGEM_GOL, frente + 1):
        marcar(pixels, coluna, topo)
    for linha in range(topo, CENTRO_Y + 1):
        marcar(pixels, frente, linha)
    return frente


def gramado_vazio():
    """
    Cria a grade de cores do campo, sem a bola, com as medidas de um campo oficial.

    Cada linha de texto do terminal vale dois pixels na vertical. A grade traz a grama cortada em faixas, as
    linhas laterais e de fundo, a linha do meio com o círculo central, as grandes e pequenas áreas, as marcas
    de pênalti com a meia-lua, os arcos de escanteio e os dois gols com a rede.

    Returns:
        list: Lista de linhas de pixels, cada uma com a cor de cada coluna, ou None onde não há campo.
    """
    pixels = [[None] * LARGURA_CAMPO for _ in range(ALTURA_PIXELS)]
    for linha in range(1, ALTURA_PIXELS):
        pixels[linha] = [cor_da_grama(coluna) for coluna in range(LARGURA_CAMPO)]
    for coluna in range(MARGEM_GOL, CENTRO_X + 1):
        marcar(pixels, coluna, 1)
    for linha in range(1, CENTRO_Y + 1):
        marcar(pixels, MARGEM_GOL, linha)
        marcar(pixels, CENTRO_X, linha)
    marcar_arco(pixels, CENTRO_X, 90, 180)
    frente_da_area = marcar_area(pixels, FUNDO_GRANDE_AREA, MEIA_LARGURA_GRANDE_AREA)
    marcar_area(pixels, FUNDO_PEQUENA_AREA, MEIA_LARGURA_PEQUENA_AREA)
    marca_do_penalti = coluna_em_metros(DISTANCIA_PENALTI)
    marcar(pixels, marca_do_penalti, CENTRO_Y)
    marcar_arco(pixels, marca_do_penalti, 0, 90, frente_da_area)
    marcar(pixels, MARGEM_GOL + 1, 2)
    for coluna in range(MARGEM_GOL):
        marcar(pixels, coluna, CENTRO_Y - 1, COR_REDE)
    marcar(pixels, 0, CENTRO_Y, COR_REDE)
    return pixels


def celula_do_campo(superior, inferior):
    """
    Escolhe o caractere e o estilo que mostram dois pixels em uma única célula do terminal.

    Args:
        superior (str | None): Cor do pixel de cima, ou None se ele estiver vazio.
        inferior (str | None): Cor do pixel de baixo, ou None se ele estiver vazio.

    Returns:
        tuple: Caractere e estilo do rich.
    """
    if superior == inferior:
        return " ", f"on {superior}" if superior else ""
    if superior is None:
        return "▄", inferior
    if inferior is None:
        return "▀", superior
    return "▀", f"{superior} on {inferior}"


def desenhar_campo(coluna, linha):
    """
    Monta o desenho completo do campo com a bola na posição indicada.

    Junta os pixels do gramado de dois em dois em cada célula do terminal, troca a célula da posição informada
    pela bola e acrescenta embaixo os rótulos dos terços de defesa, meio e ataque. Nos terminais que mostram
    emoji (TEM_EMOJI: Windows Terminal, Windows 11 e terminais conhecidos), a bola é a de futebol, branca com
    gomos pretos, e ocupa duas células; nos outros, é um círculo branco.

    Args:
        coluna (int): Coluna da bola na grade do campo.
        linha (int): Linha da bola na grade do campo.

    Returns:
        Text: Texto do rich com o campo pronto para imprimir.
    """
    pixels = gramado_vazio()
    campo = Text()
    for indice_linha in range(LINHAS_CAMPO):
        superior = pixels[indice_linha * 2]
        inferior = pixels[indice_linha * 2 + 1]
        celulas = [celula_do_campo(cima, baixo) for cima, baixo in zip(superior, inferior)]
        if indice_linha == linha:
            grama = cor_da_grama(coluna)
            if TEM_EMOJI:
                inicio = min(coluna, LARGURA_CAMPO - 2)
                celulas[inicio : inicio + 2] = [(BOLA_DESENHADA, f"on {grama}" if grama else "")]
            else:
                celulas[coluna] = ("●", f"bold {COR_BOLA} on {grama}" if grama else f"bold {COR_BOLA}")
        for estilo, grupo in groupby(celulas, key=lambda celula: celula[1]):
            campo.append("".join(caractere for caractere, _ in grupo), style=estilo)
        campo.append("\n")
    terco = COLUNAS_GRAMADO // 3
    rotulos = "DEFESA".center(terco) + "MEIO".center(terco) + "ATAQUE".center(terco)
    campo.append(" " * MARGEM_GOL + rotulos, style="dim")
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
