import time

from rich.text import Text

from config import NOMES_ESTILOS, VELOCIDADES
from elenco.escalacao import limitar
from interface.entrada import console, limpar
from partida.lances import minuto_texto

LARGURA_ZONA = 15
LARGURA_CAMPO = LARGURA_ZONA * 3 + 4
SEPARADORES = (0, LARGURA_ZONA + 1, 2 * LARGURA_ZONA + 2, LARGURA_CAMPO - 1)
GRAMADO = "on dark_green"
PAUSAS_LONGAS = ("gol", "penalti_fim", "vermelho", "intervalo", "fim", "var", "lesao")


def barra(valor, tamanho=10):
    cheio = round(limitar(valor, 0, 100) / 100 * tamanho)
    cor = "green" if valor >= 60 else ("yellow" if valor >= 35 else "red")
    return f"[{cor}]{'█' * cheio}[/][dim]{'░' * (tamanho - cheio)}[/] {round(valor)}%"


def posicao_alvo(partida, clube_jogador):
    bola = partida["bola"]
    faixa = bola.get("faixa", 1)
    if bola["zona"] == "gol":
        coluna = LARGURA_CAMPO - 2 if bola["time"] == clube_jogador else 1
        return coluna, 1
    if bola["time"] is None or bola["zona"] == "meio":
        indice = 1
    else:
        indice = 2 if bola["time"] == clube_jogador else 0
    coluna = SEPARADORES[indice] + 1 + LARGURA_ZONA // 2 + (faixa - 1) * 4
    return coluna, faixa


def desenhar_campo(coluna, linha):
    topo = "┌" + "┬".join("─" * LARGURA_ZONA for _ in range(3)) + "┐"
    base = "└" + "┴".join("─" * LARGURA_ZONA for _ in range(3)) + "┘"
    campo = Text()
    campo.append(topo + "\n", style=f"white {GRAMADO}")
    for faixa in range(3):
        caracteres = [" "] * LARGURA_CAMPO
        for separador in SEPARADORES:
            caracteres[separador] = "│"
        if faixa == 1:
            caracteres[0] = "▌"
            caracteres[-1] = "▐"
        for indice, caractere in enumerate(caracteres):
            if faixa == linha and indice == coluna:
                campo.append("●", style=f"bold bright_white {GRAMADO}")
            else:
                campo.append(caractere, style=f"white {GRAMADO}")
        campo.append("\n")
    campo.append(base + "\n", style=f"white {GRAMADO}")
    rotulos = "DEFESA".center(LARGURA_ZONA + 1) + "MEIO".center(LARGURA_ZONA + 1) + "ATAQUE".center(LARGURA_ZONA + 1)
    campo.append(" " + rotulos, style="dim")
    return campo


def cabecalho(partida, clube_jogador):
    casa = partida["times"][partida["casa"]]
    fora = partida["times"][partida["fora"]]
    tempo = "1º TEMPO" if partida["tempo"] == 1 else "2º TEMPO"
    clima = "  [cyan]chuva forte[/]" if partida["chuva"] else ""
    console.print(
        f" [bold {casa['cor']}]{casa['nome']}[/] [bold]{casa['gols']} x {fora['gols']}[/] [bold {fora['cor']}]{fora['nome']}[/]"
        f"   [dim]{tempo}[/] [bold]{minuto_texto(partida)}[/]{clima}"
    )
    meu = partida["times"][clube_jogador]
    plano = meu["plano"]
    modo = "jogando lance a lance" if partida["modo"] == "jogar" else f"simulando ({partida['velocidade']})"
    console.print(
        f" [dim]{plano['formacao']} · {NOMES_ESTILOS[plano['estilo']]} · Ofensividade {plano['ofensividade']}"
        f" · Intensidade {plano['intensidade']} · Substituições {meu['subs']}/5 · {modo}[/]"
    )


def mostrar_partida(partida, clube_jogador, pergunta=None, opcoes=None, animar=False):
    alvo = posicao_alvo(partida, clube_jogador)
    atual = partida.setdefault("tela", {"coluna": alvo[0], "linha": alvo[1]})
    passos = []
    if animar and partida["velocidade"] == "normal":
        coluna = atual["coluna"]
        while abs(alvo[0] - coluna) > 3:
            coluna += 3 if alvo[0] > coluna else -3
            passos.append((coluna, alvo[1]))
    passos.append(alvo)
    for coluna, linha in passos:
        limpar()
        cabecalho(partida, clube_jogador)
        console.print(desenhar_campo(coluna, linha))
        if len(passos) > 1 and (coluna, linha) != alvo:
            time.sleep(0.03)
    atual["coluna"], atual["linha"] = alvo
    linhas = partida["narracao"]
    for indice, texto in enumerate(linhas):
        estilo = "bold" if indice == len(linhas) - 1 else "dim"
        console.print(f" [{estilo}]{texto}[/]")
    portador = partida.get("portador")
    if portador and partida["bola"]["time"]:
        dono = partida["times"][partida["bola"]["time"]]
        console.print(
            f"\n Bola com: [bold {dono['cor']}]{portador['nome']}[/] ({portador['pos']} {portador['qualidade']})"
            f"   Energia {barra(portador['energia'])}"
        )
    if pergunta:
        console.print(f"\n [bold yellow]{pergunta}[/]")
    if opcoes:
        console.print(" " + "   ".join(f"[bold]{numero}[/] {texto}" for numero, texto in enumerate(opcoes, start=1)) + "   [bold]0[/] Pausar")


def criar_exibidor(clube_jogador):
    def exibir(partida, evento):
        mostrar_partida(partida, clube_jogador, animar=True)
        if evento["tipo"] == "gol":
            cor = partida["times"][evento["time"]]["cor"]
            console.print(f"\n [bold {cor} reverse]   G O O O O O L !   [/]")
        espera = VELOCIDADES[partida["velocidade"]]
        if partida["modo"] == "jogar":
            espera = min(espera, 0.7)
        if evento["tipo"] in PAUSAS_LONGAS:
            espera *= 2
        time.sleep(espera)

    return exibir
