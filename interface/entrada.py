import os
import sys

from rich.console import Console

EM_IDE = "PYCHARM_HOSTED" in os.environ
TERMINAL_REAL = sys.stdout.isatty()
console = Console(highlight=False, force_terminal=True if EM_IDE else None, legacy_windows=False if EM_IDE else None)


def limpar():
    if TERMINAL_REAL:
        console.clear()
    else:
        console.rule(style="dim")


def desenhar_no_lugar(desenhar):
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


def ler_opcao(minimo, maximo, rotulo=" > "):
    while True:
        texto = console.input(rotulo).strip()
        if texto.isdigit() and minimo <= int(texto) <= maximo:
            return int(texto)
        console.print(f"[red]Digite um número de {minimo} a {maximo}.[/]")


def ler_valor(rotulo, minimo, maximo):
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
    while True:
        texto = " ".join(console.input(rotulo).split())
        if texto == "0":
            return None
        if minimo <= len(texto) <= maximo and any(letra.isalpha() for letra in texto):
            return texto.title()
        console.print(f"[red]Use de {minimo} a {maximo} caracteres, com pelo menos uma letra (0 para voltar).[/]")


def confirmar(pergunta):
    while True:
        resposta = console.input(f"{pergunta} (s/n) ").strip().lower()
        if resposta in ("s", "sim"):
            return True
        if resposta in ("n", "nao", "não"):
            return False
        console.print("[red]Responda s ou n.[/]")


def pausar(texto="Enter para voltar..."):
    console.input(f"\n[dim]{texto}[/]")
