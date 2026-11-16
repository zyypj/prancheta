from rich.console import Console

console = Console(highlight=False)


def limpar():
    console.clear()


def ler_opcao(minimo, maximo, rotulo=" > "):
    while True:
        texto = console.input(rotulo).strip()
        if texto.isdigit() and minimo <= int(texto) <= maximo:
            return int(texto)
        console.print(f"[red]Digite um número de {minimo} a {maximo}.[/]")


def ler_texto(rotulo, minimo=2, maximo=20):
    while True:
        texto = " ".join(console.input(rotulo).split())
        if minimo <= len(texto) <= maximo and any(letra.isalpha() for letra in texto):
            return texto.title()
        console.print(f"[red]Use de {minimo} a {maximo} caracteres, com pelo menos uma letra.[/]")


def confirmar(pergunta):
    while True:
        resposta = console.input(f"{pergunta} (s/n) ").strip().lower()
        if resposta in ("s", "sim"):
            return True
        if resposta in ("n", "nao", "não"):
            return False
        console.print("[red]Responda s ou n.[/]")


def pausar(texto="Enter para continuar..."):
    console.input(f"[dim]{texto}[/]")
