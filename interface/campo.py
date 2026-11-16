import time

from rich.text import Text

from config import NOMES_ESTILOS, PAUSA_RAPIDA
from elenco.escalacao import limitar
from interface.entrada import TERMINAL_REAL, console, desenhar_no_lugar, limpar
from partida.lances import minuto_texto

LARGURA_ZONA = 17
LARGURA_CAMPO = LARGURA_ZONA * 3 + 4
SEPARADORES = (0, LARGURA_ZONA + 1, 2 * LARGURA_ZONA + 2, LARGURA_CAMPO - 1)
ALTURA_CAMPO = 7
LARGURA_AREA = 7
LINHAS_FAIXA = {0: 1, 1: 3, 2: 5}
LINHAS_FAIXA_AREA = {0: 2, 1: 3, 2: 4}
COLUNAS_ZONA = {
    "meio": LARGURA_CAMPO // 2,
    "ataque": (SEPARADORES[2] + LARGURA_CAMPO - 2 - LARGURA_AREA) // 2,
    "area": LARGURA_CAMPO - 2 - LARGURA_AREA // 2,
    "gol": LARGURA_CAMPO - 2,
}
GRAMADO = "on dark_green"
PAUSAS_LONGAS = ("gol", "penalti_fim", "vermelho", "intervalo", "fim", "var", "lesao", "trave", "oportunidade")


def barra(valor, tamanho=10):
    cheio = round(limitar(valor, 0, 100) / 100 * tamanho)
    cor = "green" if valor >= 60 else ("yellow" if valor >= 35 else "red")
    return f"[{cor}]{'█' * cheio}[/][dim]{'░' * (tamanho - cheio)}[/] {round(valor)}%"


def posicao_alvo(partida, clube_jogador):
    bola = partida["bola"]
    faixa = bola.get("faixa", 1)
    zona = bola["zona"] if bola["time"] is not None else "meio"
    if zona == "gol":
        linha = 3
    elif zona == "area":
        linha = LINHAS_FAIXA_AREA[faixa]
    else:
        linha = LINHAS_FAIXA[faixa]
    coluna = COLUNAS_ZONA[zona]
    if bola["time"] is not None and bola["time"] != clube_jogador:
        coluna = LARGURA_CAMPO - 1 - coluna
    return coluna, linha


def gramado_vazio():
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
    ritmo = "rápido" if partida["velocidade"] == "rapida" else "assistindo"
    modo = "jogando lance a lance" if partida["modo"] == "jogar" else f"simulando ({ritmo})"
    console.print(
        f" [dim]{plano['formacao']} · {NOMES_ESTILOS[plano['estilo']]} · Ofensividade {plano['ofensividade']}"
        f" · Intensidade {plano['intensidade']} · Substituições {meu['subs']}/5 · {modo}[/]"
    )


def desenhar_quadro(partida, clube_jogador, coluna, linha, pergunta, opcoes, destaque):
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
            f"\n Bola com: [bold {dono['cor']}]{portador['nome']}[/] ({portador['pos']} {portador['qualidade']})"
            f"   Energia {barra(portador['energia'])}"
        )
    if destaque:
        console.print(f"\n {destaque}")
    if pergunta:
        console.print(f"\n [bold yellow]{pergunta}[/]")
    if opcoes:
        console.print(" " + "   ".join(f"[bold]{numero}[/] {texto}" for numero, texto in enumerate(opcoes, start=1)) + "   [bold]0[/] Pausar")


def mostrar_partida(partida, clube_jogador, pergunta=None, opcoes=None, animar=False, destaque=None):
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
        desenhar_no_lugar(lambda c=coluna, l=linha, i=intermediario: desenhar_quadro(
            partida, clube_jogador, c, l, None if i else pergunta, None if i else opcoes, None if i else destaque
        ))
        if intermediario:
            time.sleep(0.03)
    atual["coluna"], atual["linha"] = alvo


def destaque_do_evento(partida, evento):
    if evento["tipo"] == "gol":
        cor = partida["times"][evento["time"]]["cor"]
        return f"[bold {cor} reverse]   G O O O O O L !   [/]"
    return None


def criar_exibidor(clube_jogador, ao_pausar=None):
    def exibir(partida, evento):
        if partida.get("em_pausa"):
            return
        destaque = destaque_do_evento(partida, evento)
        if TERMINAL_REAL:
            mostrar_partida(partida, clube_jogador, animar=True, destaque=destaque)
        else:
            console.print(f" {partida['narracao'][-1]}")
            if destaque:
                console.print(f" {destaque}")
        if partida["velocidade"] == "rapida":
            time.sleep(PAUSA_RAPIDA * (3 if evento["tipo"] in PAUSAS_LONGAS else 1))
            return
        resposta = console.input(" [dim]Enter avança · P pausa · R simula rápido[/] ").strip().lower()
        if resposta == "p" and ao_pausar:
            ao_pausar(partida, clube_jogador)
        elif resposta == "r":
            partida["modo"] = "simular"
            partida["velocidade"] = "rapida"

    return exibir
