import random
import time

from interface.entrada import TECLADO_REAL, TERMINAL_REAL, console, tecla_pressionada

SETAS = {"w": "↑", "a": "←", "s": "↓", "d": "→"}
DIFICULDADE_DRIBLE = {
    "corte": (4, 5.0),
    "arrancada": (4, 4.0),
    "caneta": (5, 5.0),
    "chapeu": (6, 5.5),
}
MINIJOGOS = {
    "drible": {"titulo": "DRIBLE", "tipo": "sequencia"},
    "desarme": {"titulo": "DESARME", "tipo": "sequencia", "tamanho": 3, "limite": 3.0},
    "falta": {"titulo": "EFEITO NA FALTA", "tipo": "sequencia", "tamanho": 5, "limite": 5.0},
    "penalti": {"titulo": "CONCENTRAÇÃO NO PÊNALTI", "tipo": "sequencia", "tamanho": 4, "limite": 4.0},
    "chute": {"titulo": "PONTARIA", "tipo": "memoria", "tamanho": 4, "exibicao": 1.6},
    "goleiro": {"titulo": "REFLEXO DO GOLEIRO", "tipo": "reflexo", "janela": 0.9},
    "goleiro_cara": {"titulo": "SAÍDA DO GOLEIRO", "tipo": "reflexo", "janela": 0.9},
    "cara_a_cara": {"titulo": "TEMPO DA BATIDA", "tipo": "reflexo", "janela": 0.8},
    "cabeceio": {"titulo": "TEMPO DE BOLA", "tipo": "reflexo", "janela": 1.0},
}


def sortear_setas(tamanho):
    """
    Sorteia uma sequência de teclas de seta (W, A, S, D).

    Args:
        tamanho (int): Quantidade de setas.

    Returns:
        list[str]: Teclas sorteadas.
    """
    return [random.choice(tuple(SETAS)) for _ in range(tamanho)]


def desenhar_setas(teclas):
    """
    Monta a linha com as setas de uma sequência.

    Args:
        teclas (list[str]): Teclas da sequência.

    Returns:
        str: Setas separadas por espaço, com marcação do rich.
    """
    return "  " + "  ".join(f"[bold]{SETAS[tecla]}[/]" for tecla in teclas)


def sequencia_de_setas(titulo, tamanho, limite):
    """
    Minijogo de sequência: mostra setas que o jogador precisa digitar com W, A, S e D antes do tempo acabar.

    O tempo conta a partir do momento em que a sequência aparece até o Enter.

    Args:
        titulo (str): Nome do minijogo.
        tamanho (int): Quantidade de setas.
        limite (float): Tempo máximo, em segundos.

    Returns:
        tuple: (acertou, segundos gastos).
    """
    teclas = sortear_setas(tamanho)
    segundos = f"{limite:g}".replace(".", ",")
    console.print(f"\n [bold yellow]{titulo}: digite a sequência em até {segundos} segundos e aperte Enter[/]")
    console.print(" [dim]W = ↑   A = ←   S = ↓   D = →[/]")
    console.print(desenhar_setas(teclas))
    inicio = time.monotonic()
    digitado = console.input(" > ").strip().lower().replace(" ", "")
    gasto = time.monotonic() - inicio
    return digitado == "".join(teclas) and gasto <= limite, gasto


def memoria_de_setas(titulo, tamanho, exibicao):
    """
    Minijogo de memória: as setas aparecem por um instante, somem, e o jogador digita a sequência de cabeça.

    Num terminal de verdade a linha das setas é apagada com códigos ANSI; fora dele, linhas em branco empurram
    as setas para cima.

    Args:
        titulo (str): Nome do minijogo.
        tamanho (int): Quantidade de setas.
        exibicao (float): Tempo em que as setas ficam visíveis, em segundos.

    Returns:
        tuple: (acertou, segundos em que as setas ficaram na tela).
    """
    teclas = sortear_setas(tamanho)
    console.print(f"\n [bold yellow]{titulo}: memorize as setas, elas vão sumir![/]")
    console.print(" [dim]W = ↑   A = ←   S = ↓   D = →[/]")
    console.print(desenhar_setas(teclas))
    time.sleep(exibicao)
    if TERMINAL_REAL:
        console.file.write("\x1b[1A\x1b[2K")
        console.file.flush()
    else:
        console.print("\n" * 25)
    digitado = console.input(" Agora digite a sequência > ").strip().lower().replace(" ", "")
    return digitado == "".join(teclas), exibicao


def teste_de_reflexo(titulo, janela):
    """
    Minijogo de reflexo: o jogador aperta Enter assim que aparecer AGORA.

    Espera um tempo sorteado entre 1 e 2,5 segundos antes do sinal. Se a resposta vier rápida demais, o
    jogador apertou antes do sinal e queimou.

    Args:
        titulo (str): Nome do minijogo.
        janela (float): Tempo máximo de reação aceito, em segundos.

    Returns:
        tuple: (acertou, segundos de reação).
    """
    console.print(f"\n [bold yellow]{titulo}: aperte Enter assim que aparecer AGORA![/]")
    console.print(" [dim]Prepare-se...[/]")
    time.sleep(random.uniform(1.0, 2.5))
    while TECLADO_REAL and tecla_pressionada():
        pass
    console.print(" [bold red]AGORA![/]")
    inicio = time.monotonic()
    console.input("")
    reacao = time.monotonic() - inicio
    return 0.08 <= reacao <= janela, reacao


def jogar_minijogo(tipo, detalhe):
    """
    Roda o minijogo da jogada e mostra o resultado.

    Cada jogada usa um dos três formatos de MINIJOGOS: sequência de setas (drible, desarme, falta e pênalti a
    favor), memória (pontaria do chute) ou reflexo (goleiro, cara a cara e cabeçada). No drible, o tamanho e o
    tempo da sequência dependem do tipo de drible, e o chapéu é o mais difícil.

    Args:
        tipo (str): Chave da jogada em MINIJOGOS.
        detalhe (str | None): Tipo de drible, quando o minijogo é de drible.

    Returns:
        bool: True se o jogador acertou o minijogo.
    """
    dados = MINIJOGOS[tipo]
    if dados["tipo"] == "sequencia":
        tamanho, limite = (
            DIFICULDADE_DRIBLE.get(detalhe, (4, 5.0)) if tipo == "drible" else (dados["tamanho"], dados["limite"])
        )
        acertou, gasto = sequencia_de_setas(dados["titulo"], tamanho, limite)
        tempo = f"{gasto:.1f} s"
    elif dados["tipo"] == "memoria":
        acertou, _ = memoria_de_setas(dados["titulo"], dados["tamanho"], dados["exibicao"])
        tempo = "de memória"
    else:
        acertou, gasto = teste_de_reflexo(dados["titulo"], dados["janela"])
        tempo = f"reação de {gasto:.2f} s" if gasto >= 0.08 else "apertou antes do sinal"
    if acertou:
        console.print(f" [bold green]Perfeito! ({tempo}) A jogada fica mais fácil.[/]")
    else:
        console.print(f" [bold red]Não deu! ({tempo}) A jogada fica mais difícil.[/]")
    time.sleep(1.2)
    return acertou
