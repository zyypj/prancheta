import os
import sys

from rich.console import Console

EM_IDE = "PYCHARM_HOSTED" in os.environ
console = Console(highlight=False, force_terminal=True if EM_IDE else None, legacy_windows=False if EM_IDE else None)


def limpar():
    if sys.stdout.isatty():
        console.clear()
    else:
        console.print("\n" * max(console.height, 40))


def ler_opcao(minimo, maximo, rotulo=" > "):
    while True:
        texto = console.input(rotulo).strip()
        if texto.isdigit() and minimo <= int(texto) <= maximo:
            return int(texto)
        console.print(f"[red]Digite um número de {minimo} a {maximo}.[/]")


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
