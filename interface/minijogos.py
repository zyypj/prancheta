import random
import time

from interface.entrada import TECLADO_REAL, console, tecla_pressionada

SETAS = {"w": "↑", "a": "←", "s": "↓", "d": "→"}
DIFICULDADE_DRIBLE = {
    "corte": (4, 5.0),
    "arrancada": (4, 4.0),
    "caneta": (5, 5.0),
    "chapeu": (6, 5.5),
}
JANELA_REFLEXO = {"goleiro": 0.9, "cabeceio": 1.0}


def sequencia_de_setas(tamanho, limite):
    """
    Minijogo de sequência: mostra setas que o jogador precisa digitar com W, A, S e D antes do tempo acabar.

    O tempo conta a partir do momento em que a sequência aparece até o Enter.

    Args:
        tamanho (int): Quantidade de setas.
        limite (float): Tempo máximo, em segundos.

    Returns:
        tuple: (acertou, segundos gastos).
    """
    teclas = [random.choice(tuple(SETAS)) for _ in range(tamanho)]
    segundos = f"{limite:g}".replace(".", ",")
    console.print(f"\n [bold yellow]MINIJOGO: digite a sequência em até {segundos} segundos e aperte Enter[/]")
    console.print(" [dim]W = ↑   A = ←   S = ↓   D = →[/]")
    console.print("  " + "  ".join(f"[bold]{SETAS[tecla]}[/]" for tecla in teclas))
    inicio = time.monotonic()
    digitado = console.input(" > ").strip().lower().replace(" ", "")
    gasto = time.monotonic() - inicio
    return digitado == "".join(teclas) and gasto <= limite, gasto


def teste_de_reflexo(janela):
    """
    Minijogo de reflexo: o jogador aperta Enter assim que aparecer AGORA.

    Espera um tempo sorteado entre 1 e 2,5 segundos antes do sinal. Se a resposta vier rápida demais, o
    jogador apertou antes do sinal e queimou.

    Args:
        janela (float): Tempo máximo de reação aceito, em segundos.

    Returns:
        tuple: (acertou, segundos de reação).
    """
    console.print("\n [bold yellow]MINIJOGO: aperte Enter assim que aparecer AGORA![/]")
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

    No drible, o tamanho e o tempo da sequência dependem do tipo de drible (o chapéu é o mais difícil). No
    pênalti contra e na cabeçada, é um teste de reflexo.

    Args:
        tipo (str): "drible", "goleiro" ou "cabeceio".
        detalhe (str | None): Tipo de drible, quando o minijogo é de drible.

    Returns:
        bool: True se o jogador acertou o minijogo.
    """
    if tipo == "drible":
        tamanho, limite = DIFICULDADE_DRIBLE.get(detalhe, (4, 5.0))
        acertou, gasto = sequencia_de_setas(tamanho, limite)
        tempo = f"{gasto:.1f} s"
    else:
        acertou, gasto = teste_de_reflexo(JANELA_REFLEXO[tipo])
        tempo = f"reação de {gasto:.2f} s" if gasto >= 0.08 else "apertou antes do sinal"
    if acertou:
        console.print(f" [bold green]Perfeito! ({tempo}) A jogada fica mais fácil.[/]")
    else:
        console.print(f" [bold red]Não deu! ({tempo}) A jogada fica mais difícil.[/]")
    time.sleep(1.2)
    return acertou
