import math
import random
import time
from functools import partial
from itertools import groupby

from rich.text import Text

from interface.campo import celula_do_campo
from interface.entrada import TERMINAL_REAL, console, desenhar_no_lugar, tecla_pressionada

LARGURA_ARTE = 47
ALTURA_ARTE = 36
CENTRO_ARTE = LARGURA_ARTE // 2
RECUO_ARTE = "    "
QUADROS_SUBIDA = 40
QUADROS_FESTA = 60
TOTAL_QUADROS = QUADROS_SUBIDA + QUADROS_FESTA
PAUSA_QUADRO = 0.04
ALTURA_MINIMA_TELA = 29
LARGURA_MINIMA_TELA = LARGURA_ARTE + len(RECUO_ARTE)
ALTURA_TACA = 22
OMBRO_FINAL = 33
DISTANCIA_DOS_OMBROS = 11
RECUO_DA_ENTRADA = 30
TAMANHO_DO_BRACO = 7.5
QUANTIDADE_CONFETES = 70
PALETA_OURO = {
    "brilho": "#fff3b0",
    "claro": "#ffd94a",
    "medio": "#e6b422",
    "escuro": "#a87a12",
    "sombra": "#6f4e0b",
}
PALETA_PRATA = {
    "brilho": "#ffffff",
    "claro": "#e3e8ec",
    "medio": "#bcc4cb",
    "escuro": "#858e96",
    "sombra": "#565d64",
}
PALETA_COBRE = {
    "brilho": "#ffe3c4",
    "claro": "#f2b27a",
    "medio": "#d98a4e",
    "escuro": "#a35f2e",
    "sombra": "#6e3e1c",
}
BRANCO_DA_BOLA = "#f7f7f2"
PRETO_DA_BOLA = "#2a2a2a"
ESTRELA_SERIE_A = {
    (coluna, linha): PALETA_OURO["brilho"] for coluna, linha in ((0, 4), (-1, 5), (0, 5), (1, 5), (0, 6))
}
LETRA_SERIE_B = {
    (coluna, linha): PALETA_PRATA["sombra"]
    for coluna, linha in (
        (-1, 3),
        (0, 3),
        (-1, 4),
        (1, 4),
        (-1, 5),
        (0, 5),
        (-1, 6),
        (1, 6),
        (-1, 7),
        (0, 7),
    )
}
LETRA_DA_COPA = {
    (coluna, linha): PALETA_COBRE["sombra"]
    for coluna, linha in ((-1, 8), (0, 8), (-1, 9), (1, 9), (-1, 10), (0, 10), (-1, 11), (-1, 12))
}
BOLA_DA_COPA = {
    (coluna, linha): BRANCO_DA_BOLA
    for linha, meia_largura in enumerate((1, 2, 2, 2, 1))
    for coluna in range(-meia_largura, meia_largura + 1)
}
GOMOS_DA_BOLA = {posicao: PRETO_DA_BOLA for posicao in ((0, 2), (-2, 1), (2, 1), (-1, 4), (1, 4))}
TACAS = {
    "serie_a": {
        "perfil": (
            7.5,
            7.5,
            7.5,
            7.46,
            7.35,
            7.15,
            6.87,
            6.5,
            6,
            5.36,
            4.5,
            3.27,
            2,
            1.5,
            2.5,
            1.5,
            2,
            3,
            4.5,
            5.5,
            6.5,
            6.5,
        ),
        "boca": 0,
        "alca": (8, 4.5, 3.5, 3.8),
        "paleta": PALETA_OURO,
        "base": "#8a5a33",
        "detalhes": ESTRELA_SERIE_A,
    },
    "serie_b": {
        "perfil": (8, 8, 7.5, 7, 6.5, 6, 5.5, 5, 4.2, 3.4, 2.6, 2, 1.5, 1.5, 1.5, 1.5, 2, 3.5, 4.5, 5.5, 6.5, 6.5),
        "boca": 0,
        "alca": (8.5, 3.5, 2.8, 3),
        "paleta": PALETA_PRATA,
        "base": "#2f7d4f",
        "detalhes": LETRA_SERIE_B,
    },
    "copa": {
        "perfil": (1, 2, 2, 2, 1, 4, 6.5, 8, 8, 7.5, 7, 6, 4.5, 3, 1.5, 2.5, 1.5, 2.5, 4, 5.5, 6.5, 6.5),
        "boca": None,
        "alca": (9.5, 10, 3, 3.6),
        "paleta": PALETA_COBRE,
        "base": "#7a2e2e",
        "detalhes": {**BOLA_DA_COPA, **GOMOS_DA_BOLA, **LETRA_DA_COPA},
    },
}
TACA_DA_DIVISAO = {1: "serie_a", 2: "serie_b"}
PELE = "#c58a5c"
CABELO = "#5c3b22"
CONFETE_CLARO = "#f2f2f2"
BLOCOS_SEM_COR = {(True, True): "█", (True, False): "▀", (False, True): "▄", (False, False): " "}


def suavizar(valor):
    """
    Suaviza um avanço de 0 a 1, começando e terminando devagar.

    Args:
        valor (float): Avanço entre 0 e 1.

    Returns:
        float: Avanço suavizado, entre 0 e 1.
    """
    return valor * valor * (3 - 2 * valor)


def pintar(pixels, coluna, linha, cor):
    """
    Pinta um pixel da arte, ignorando o que estiver fora dela.

    Args:
        pixels (list[list]): Grade de cores da arte.
        coluna (float): Coluna do pixel.
        linha (float): Linha do pixel.
        cor (str): Cor do pixel.
    """
    x, y = round(coluna), round(linha)
    if 0 <= x < LARGURA_ARTE and 0 <= y < ALTURA_ARTE:
        pixels[y][x] = cor


def pintar_disco(pixels, centro_x, centro_y, raio, cor):
    """
    Pinta um disco na arte.

    Args:
        pixels (list[list]): Grade de cores da arte.
        centro_x (float): Coluna do centro.
        centro_y (float): Linha do centro.
        raio (float): Raio do disco, em pixels.
        cor (str): Cor do disco.
    """
    for y in range(math.floor(centro_y - raio), math.ceil(centro_y + raio) + 1):
        for x in range(math.floor(centro_x - raio), math.ceil(centro_x + raio) + 1):
            if (x - centro_x) ** 2 + (y - centro_y) ** 2 <= raio**2:
                pintar(pixels, x, y, cor)


def pintar_segmento(pixels, inicio, fim, raio, cor):
    """
    Pinta um segmento grosso entre dois pontos.

    Args:
        pixels (list[list]): Grade de cores da arte.
        inicio (tuple): Coluna e linha do começo do segmento.
        fim (tuple): Coluna e linha do fim do segmento.
        raio (float): Metade da grossura, em pixels.
        cor (str): Cor do segmento.
    """
    passos = int(max(abs(fim[0] - inicio[0]), abs(fim[1] - inicio[1])) * 2) + 1
    for passo in range(passos + 1):
        avanco = passo / passos
        x = inicio[0] + (fim[0] - inicio[0]) * avanco
        y = inicio[1] + (fim[1] - inicio[1]) * avanco
        pintar_disco(pixels, x, y, raio, cor)


def taca_do_titulo(titulo, divisao):
    """
    Escolhe a taça de um título.

    Args:
        titulo (str): Título conquistado, "liga" ou "copa".
        divisao (int): Divisão do clube, usada no título da liga.

    Returns:
        str: Chave da taça em TACAS.
    """
    return "copa" if titulo == "copa" else TACA_DA_DIVISAO[divisao]


def cor_da_taca(taca, coluna, linha):
    """
    Escolhe a cor de um ponto da taça, com a luz vindo da esquerda.

    Args:
        taca (dict): Dados da taça, um dos valores de TACAS.
        coluna (int): Coluna relativa ao centro da taça.
        linha (int): Linha dentro da taça.

    Returns:
        str: Cor do ponto.
    """
    paleta = taca["paleta"]
    meia_largura = taca["perfil"][linha]
    if linha >= ALTURA_TACA - 2:
        return taca["base"]
    if (coluna, linha) in taca["detalhes"]:
        return taca["detalhes"][(coluna, linha)]
    if linha == taca["boca"]:
        return paleta["claro"]
    if taca["boca"] is not None and linha == taca["boca"] + 1 and abs(coluna) < meia_largura - 1.5:
        return paleta["sombra"]
    posicao = coluna / meia_largura
    if posicao < -0.7:
        return paleta["medio"]
    if posicao < -0.15:
        return paleta["claro"]
    if posicao < 0.5:
        return paleta["medio"]
    return paleta["escuro"] if posicao < 0.85 else paleta["sombra"]


def pintar_alcas(pixels, taca, topo):
    """
    Pinta as duas alças da taça, nas laterais do bojo.

    Args:
        pixels (list[list]): Grade de cores da arte.
        taca (dict): Dados da taça, um dos valores de TACAS.
        topo (int): Linha do alto da taça.
    """
    centro_x, centro_y, raio_x, raio_y = taca["alca"]
    for lado, tom in ((-1, "medio"), (1, "escuro")):
        for y in range(ALTURA_TACA):
            for x in range(4, 14):
                distancia = math.hypot((x - centro_x) / raio_x, (y - centro_y) / raio_y)
                if 0.72 <= distancia <= 1.12 and x > taca["perfil"][y]:
                    pintar(pixels, CENTRO_ARTE + lado * x, topo + y, taca["paleta"][tom])


def pintar_taca(pixels, taca, topo, faixa_de_brilho):
    """
    Pinta a taça, com as alças, o pé, a base e a faixa de brilho.

    Args:
        pixels (list[list]): Grade de cores da arte.
        taca (dict): Dados da taça, um dos valores de TACAS.
        topo (int): Linha do alto da taça.
        faixa_de_brilho (float | None): Posição diagonal do brilho, ou None se não houver brilho.
    """
    pintar_alcas(pixels, taca, topo)
    for y, meia_largura in enumerate(taca["perfil"]):
        alcance = math.ceil(meia_largura)
        for x in range(-alcance, alcance + 1):
            if abs(x) > meia_largura:
                continue
            cor = cor_da_taca(taca, x, y)
            if faixa_de_brilho is not None and cor != taca["base"] and abs(x + y - faixa_de_brilho) < 1.6:
                cor = taca["paleta"]["brilho"]
            pintar(pixels, CENTRO_ARTE + x, topo + y, cor)


def posicao_do_cotovelo(ombro, mao, lado):
    """
    Calcula onde fica o cotovelo de um braço de tamanho fixo, dobrado para fora do corpo.

    Args:
        ombro (tuple): Coluna e linha do ombro.
        mao (tuple): Coluna e linha da mão.
        lado (int): -1 para o braço esquerdo e 1 para o direito.

    Returns:
        tuple: Coluna e linha do cotovelo.
    """
    delta_x = mao[0] - ombro[0]
    delta_y = mao[1] - ombro[1]
    distancia = max(math.hypot(delta_x, delta_y), 0.01)
    metade = min(distancia / 2, TAMANHO_DO_BRACO)
    dobra = math.sqrt(TAMANHO_DO_BRACO**2 - metade**2)
    normal_x = -delta_y / distancia
    normal_y = delta_x / distancia
    if normal_x * lado < 0:
        normal_x, normal_y = -normal_x, -normal_y
    return (ombro[0] + delta_x / 2 + normal_x * dobra, ombro[1] + delta_y / 2 + normal_y * dobra)


def pintar_corpo(pixels, ombro_y, cor):
    """
    Pinta, de costas, a cabeça e o tronco de quem levanta a taça.

    Args:
        pixels (list[list]): Grade de cores da arte.
        ombro_y (float): Linha dos ombros.
        cor (str): Cor da camisa, a mesma do clube.
    """
    pintar_segmento(pixels, (CENTRO_ARTE, ombro_y - 3), (CENTRO_ARTE, ombro_y), 1.5, PELE)
    pintar_disco(pixels, CENTRO_ARTE, ombro_y - 5, 4, CABELO)
    esquerda = (CENTRO_ARTE - DISTANCIA_DOS_OMBROS, ombro_y)
    direita = (CENTRO_ARTE + DISTANCIA_DOS_OMBROS, ombro_y)
    pintar_segmento(pixels, esquerda, direita, 2.5, cor)
    for y in range(max(0, round(ombro_y)), ALTURA_ARTE):
        for x in range(-DISTANCIA_DOS_OMBROS - 2, DISTANCIA_DOS_OMBROS + 3):
            pintar(pixels, CENTRO_ARTE + x, y, cor)


def pintar_braco(pixels, ombro, mao, lado, cor):
    """
    Pinta um braço, com a manga na cor do clube.

    Args:
        pixels (list[list]): Grade de cores da arte.
        ombro (tuple): Coluna e linha do ombro.
        mao (tuple): Coluna e linha da mão.
        lado (int): -1 para o braço esquerdo e 1 para o direito.
        cor (str): Cor da camisa.
    """
    cotovelo = posicao_do_cotovelo(ombro, mao, lado)
    manga = (ombro[0] + (cotovelo[0] - ombro[0]) * 0.6, ombro[1] + (cotovelo[1] - ombro[1]) * 0.6)
    pintar_segmento(pixels, ombro, cotovelo, 1.5, PELE)
    pintar_segmento(pixels, cotovelo, mao, 1.3, PELE)
    pintar_segmento(pixels, ombro, manga, 2, cor)


def criar_confetes(cor, taca):
    """
    Sorteia os confetes da comemoração, sem mexer no sorteio do jogo.

    Args:
        cor (str): Cor do clube, usada em parte dos confetes.
        taca (dict): Dados da taça, cujo tom claro colore outra parte deles.

    Returns:
        list[tuple]: Coluna, linha inicial, velocidade, fase do balanço e cor de cada confete.
    """
    sorteio = random.Random(LARGURA_ARTE)
    cores = (cor, cor, taca["paleta"]["claro"], CONFETE_CLARO)
    return [
        (
            sorteio.uniform(0, LARGURA_ARTE - 1),
            sorteio.uniform(-ALTURA_ARTE, 0),
            sorteio.uniform(0.4, 0.8),
            sorteio.uniform(0, math.tau),
            sorteio.choice(cores),
        )
        for _ in range(QUANTIDADE_CONFETES)
    ]


def pintar_confetes(pixels, confetes, tempo):
    """
    Pinta os confetes que já entraram na arte, caindo com um leve balanço.

    Args:
        pixels (list[list]): Grade de cores da arte.
        confetes (list[tuple]): Confetes criados por criar_confetes.
        tempo (int): Quadros passados desde o início da comemoração.
    """
    for coluna, inicio, velocidade, fase, cor in confetes:
        linha = inicio + velocidade * tempo
        if linha >= 0:
            pintar(pixels, coluna + math.sin(tempo * 0.12 + fase) * 1.5, linha % ALTURA_ARTE, cor)


def pixels_do_quadro(cor, confetes, numero, taca):
    """
    Monta a grade de cores de um quadro da animação.

    Na subida, a pessoa entra por baixo e estica os braços até o alto. Na comemoração, a taça balança, uma faixa
    de brilho passa por ela e os confetes caem. O último quadro é a imagem final, com a taça parada no alto.

    Args:
        cor (str): Cor do clube.
        confetes (list[tuple]): Confetes criados por criar_confetes.
        numero (int): Número do quadro, de 0 a TOTAL_QUADROS.
        taca (dict): Dados da taça, um dos valores de TACAS.

    Returns:
        list[list]: Grade de cores, com None nos pixels vazios.
    """
    pixels = [[None] * LARGURA_ARTE for _ in range(ALTURA_ARTE)]
    subida = min(1, numero / QUADROS_SUBIDA)
    festa = max(0, (numero - QUADROS_SUBIDA) / QUADROS_FESTA)
    entrada = suavizar(min(1, subida / 0.4))
    erguer = suavizar(max(0, (subida - 0.35) / 0.65))
    balanco = math.sin(festa * math.pi * 6) * 1.2 * (1 - festa)
    ombro_y = OMBRO_FINAL + (1 - entrada) * RECUO_DA_ENTRADA
    mao_y = ombro_y - 5 - 7 * erguer + balanco
    faixa = (festa * 3) % 1 * 44 - 10 if 0 < festa < 1 else None
    if numero >= QUADROS_SUBIDA:
        pintar_confetes(pixels, confetes, numero - QUADROS_SUBIDA)
    pintar_corpo(pixels, ombro_y, cor)
    maos = {lado: (CENTRO_ARTE + lado * 7, mao_y) for lado in (-1, 1)}
    for lado, mao in maos.items():
        pintar_braco(pixels, (CENTRO_ARTE + lado * DISTANCIA_DOS_OMBROS, ombro_y), mao, lado, cor)
    pintar_taca(pixels, taca, round(mao_y) - 20, faixa)
    for mao in maos.values():
        pintar_disco(pixels, mao[0], mao[1], 1.8, PELE)
    return pixels


def celula_sem_cor(superior, inferior):
    """
    Escolhe o bloco que mostra dois pixels em um terminal sem cores.

    Args:
        superior (str | None): Cor do pixel de cima, ou None se ele estiver vazio.
        inferior (str | None): Cor do pixel de baixo, ou None se ele estiver vazio.

    Returns:
        tuple: Caractere e estilo vazio.
    """
    return BLOCOS_SEM_COR[(superior is not None, inferior is not None)], ""


def texto_da_arte(pixels):
    """
    Converte a grade de cores em texto, juntando dois pixels em cada célula do terminal.

    Em um terminal sem cores, a arte vira uma silhueta feita de blocos.

    Args:
        pixels (list[list]): Grade de cores da arte.

    Returns:
        Text: Texto do rich pronto para imprimir.
    """
    celula = celula_sem_cor if console.no_color or console.color_system is None else celula_do_campo
    arte = Text(no_wrap=True, overflow="crop")
    for linha in range(0, ALTURA_ARTE, 2):
        celulas = [celula(cima, baixo) for cima, baixo in zip(pixels[linha], pixels[linha + 1])]
        arte.append(RECUO_ARTE)
        for estilo, grupo in groupby(celulas, key=lambda par: par[1]):
            arte.append("".join(caractere for caractere, _ in grupo), style=estilo)
        if linha < ALTURA_ARTE - 2:
            arte.append("\n")
    return arte


def animar_taca(cor, desenhar_tela, chave_da_taca):
    """
    Mostra a taça sendo levantada e termina na imagem final.

    A animação dura cerca de 4 segundos e qualquer tecla pula para o fim. Fora de um terminal real, ou em uma
    janela pequena demais para redesenhar a tela, aparece só a imagem final.

    Args:
        cor (str): Cor do clube.
        desenhar_tela (callable): Função que recebe a arte e imprime a tela inteira.
        chave_da_taca (str): Chave da taça em TACAS.
    """
    taca = TACAS[chave_da_taca]
    confetes = criar_confetes(cor, taca)
    if TERMINAL_REAL and console.height >= ALTURA_MINIMA_TELA and console.width >= LARGURA_MINIMA_TELA:
        tecla_pressionada()
        console.show_cursor(False)
        try:
            for numero in range(TOTAL_QUADROS):
                arte = texto_da_arte(pixels_do_quadro(cor, confetes, numero, taca))
                desenhar_no_lugar(partial(desenhar_tela, arte))
                time.sleep(PAUSA_QUADRO)
                if tecla_pressionada():
                    break
        finally:
            console.show_cursor(True)
    final = texto_da_arte(pixels_do_quadro(cor, confetes, TOTAL_QUADROS, taca))
    desenhar_no_lugar(partial(desenhar_tela, final))
