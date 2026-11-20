import os
import sys

from rich.console import Console

if os.name == "nt":
    import msvcrt
else:
    import select

EM_IDE = "PYCHARM_HOSTED" in os.environ
TERMINAL_REAL = sys.stdout.isatty()
TERMINAIS_COM_EMOJI = ("vscode", "iTerm.app", "WezTerm", "Apple_Terminal")
PRIMEIRA_VERSAO_DO_WINDOWS_11 = 22000
TECLADO_REAL = sys.stdin.isatty()
console = Console(highlight=False, force_terminal=True if EM_IDE else None, legacy_windows=False if EM_IDE else None)
WINDOWS_11 = os.name == "nt" and sys.getwindowsversion().build >= PRIMEIRA_VERSAO_DO_WINDOWS_11
TEM_EMOJI = (
    TERMINAL_REAL
    and not EM_IDE
    and not console.legacy_windows
    and ("WT_SESSION" in os.environ or os.environ.get("TERM_PROGRAM") in TERMINAIS_COM_EMOJI or WINDOWS_11)
)


def limpar():
    """
    Limpa a tela do terminal.

    Em terminal real apaga a tela; quando a saída não é um terminal, como no console de uma IDE, imprime uma
    linha divisória no lugar.
    """
    if TERMINAL_REAL:
        console.clear()
    else:
        console.rule(style="dim")


def desenhar_no_lugar(desenhar):
    """
    Redesenha a tela por cima do quadro anterior, sem limpar e sem piscar.

    Fora de um terminal real apenas chama a função de desenho. Em terminal real, captura o que seria impresso,
    volta o cursor ao topo da tela, escreve cada linha apagando o resto dela e apaga o que sobrou abaixo do
    novo quadro.

    Args:
        desenhar (callable): Função sem parâmetros que imprime o quadro.
    """
    if not TERMINAL_REAL:
        desenhar()
        return
    with console.capture() as captura:
        desenhar()
    linhas = captura.get().split("\n")
    if linhas and not linhas[-1]:
        linhas.pop()
    console.file.write("\x1b[H" + "".join(f"{linha}\x1b[K\n" for linha in linhas) + "\x1b[J")
    console.file.flush()


def tecla_pressionada():
    """
    Verifica, sem esperar, se o usuário apertou alguma tecla.

    No Windows usa msvcrt para ler a tecla na hora e descarta o que sobrou no buffer; nos outros sistemas usa
    select, e a tecla só chega depois do Enter. Fora de um terminal de verdade (como no console comum de uma
    IDE) não dá para ler o teclado sem travar o jogo, e a função sempre devolve None.

    Returns:
        str | None: Tecla apertada, em minúsculas, ou None se nada foi apertado.
    """
    if not TECLADO_REAL:
        return None
    if os.name == "nt":
        if not msvcrt.kbhit():
            return None
        tecla = msvcrt.getwch()
        while msvcrt.kbhit():
            msvcrt.getwch()
        return tecla.lower()
    pronto, _, _ = select.select([sys.stdin], [], [], 0)
    if not pronto:
        return None
    return sys.stdin.readline().strip().lower()[:1] or "\n"


def ler_opcao(minimo, maximo, rotulo=" > "):
    """
    Lê do usuário um número inteiro dentro de um intervalo.

    Repete a pergunta, com uma mensagem de erro, até ser digitado um número inteiro entre o mínimo e o máximo.

    Args:
        minimo (int): Menor valor aceito.
        maximo (int): Maior valor aceito.
        rotulo (str): Texto mostrado antes da digitação. Padrão " > ".

    Returns:
        int: Número digitado.
    """
    while True:
        texto = console.input(rotulo).strip()
        if texto.isdigit() and minimo <= int(texto) <= maximo:
            return int(texto)
        console.print(f"[red]Digite um número de {minimo} a {maximo}.[/]")


def ler_opcao_ou_letra(minimo, maximo, letras, rotulo=" > "):
    """
    Lê um número inteiro dentro de um intervalo ou uma das letras aceitas.

    Repete a pergunta, com uma mensagem de erro, até ser digitado um número entre o mínimo e o máximo ou uma
    das letras, sem diferenciar maiúsculas.

    Args:
        minimo (int): Menor número aceito.
        maximo (int): Maior número aceito.
        letras (Iterable[str]): Letras aceitas, em minúsculas.
        rotulo (str): Texto mostrado antes da digitação. Padrão " > ".

    Returns:
        int | str: Número digitado ou a letra, em minúsculas.
    """
    while True:
        texto = console.input(rotulo).strip().lower()
        if texto in letras:
            return texto
        if texto.isdigit() and minimo <= int(texto) <= maximo:
            return int(texto)
        extra = "".join(f" ou {letra.upper()}" for letra in letras)
        console.print(f"[red]Digite um número de {minimo} a {maximo}{extra}.[/]")


def ler_valor(rotulo, minimo, maximo):
    """
    Lê do usuário um valor decimal dentro de um intervalo, aceitando 0 para cancelar.

    Aceita vírgula ou ponto como separador decimal e arredonda o valor para uma casa. Repete a pergunta, com
    uma mensagem de erro, até o valor ser 0 ou estar entre o mínimo e o máximo.

    Args:
        rotulo (str): Texto mostrado antes da digitação.
        minimo (float): Menor valor aceito, além do 0.
        maximo (float): Maior valor aceito.

    Returns:
        float: Valor digitado, ou 0 se o usuário cancelou.
    """
    while True:
        texto = console.input(rotulo).strip().replace(",", ".")
        try:
            valor = round(float(texto), 1)
        except ValueError:
            valor = None
        if valor is not None and (valor == 0 or minimo <= valor <= maximo):
            return valor
        console.print(f"[red]Digite um valor entre {minimo} e {maximo} (0 cancela).[/]")


def ler_texto(rotulo, minimo=2, maximo=20):
    """
    Lê do usuário um texto curto, como um nome, aceitando 0 para voltar.

    Junta os espaços repetidos e exige um tamanho dentro do limite e pelo menos uma letra, repetindo a
    pergunta até receber um texto válido. O texto aceito volta com a inicial de cada palavra em maiúscula.

    Args:
        rotulo (str): Texto mostrado antes da digitação.
        minimo (int): Menor quantidade de caracteres aceita. Padrão 2.
        maximo (int): Maior quantidade de caracteres aceita. Padrão 20.

    Returns:
        str | None: Texto digitado, ou None se o usuário digitou 0.
    """
    while True:
        texto = " ".join(console.input(rotulo).split())
        if texto == "0":
            return None
        if minimo <= len(texto) <= maximo and any(letra.isalpha() for letra in texto):
            return texto.title()
        console.print(f"[red]Use de {minimo} a {maximo} caracteres, com pelo menos uma letra (0 para voltar).[/]")


def confirmar(pergunta):
    """
    Faz uma pergunta de sim ou não ao usuário.

    Aceita s, sim, n, nao ou não, sem diferenciar maiúsculas, e repete a pergunta para qualquer outra
    resposta.

    Args:
        pergunta (str): Texto da pergunta.

    Returns:
        bool: True se o usuário respondeu sim, False se respondeu não.
    """
    while True:
        resposta = console.input(f"{pergunta} (s/n) ").strip().lower()
        if resposta in ("s", "sim"):
            return True
        if resposta in ("n", "nao", "não"):
            return False
        console.print("[red]Responda s ou n.[/]")


def pausar(texto="Enter para voltar..."):
    """
    Mostra um aviso e espera o usuário apertar Enter.

    Args:
        texto (str): Aviso mostrado. Padrão "Enter para voltar...".
    """
    console.input(f"\n[dim]{texto}[/]")
