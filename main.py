from rich.console import Console
from rich.panel import Panel

from config import NOME_JOGO

console = Console()

OPCOES_MENU = ("Novo jogo", "Carregar", "Ranking", "Sair")


def mostrar_menu():
    console.clear()
    titulo = " ".join(NOME_JOGO)
    console.print(Panel.fit(f"[bold green]{titulo}[/]", border_style="green"))
    for numero, opcao in enumerate(OPCOES_MENU, start=1):
        console.print(f" {numero} - {opcao}")


def ler_opcao(minimo, maximo):
    while True:
        texto = console.input(" > ").strip()
        if texto.isdigit() and minimo <= int(texto) <= maximo:
            return int(texto)
        console.print(f"[red]Digite um número de {minimo} a {maximo}.[/]")


def main():
    while True:
        mostrar_menu()
        opcao = ler_opcao(1, len(OPCOES_MENU))
        if opcao == len(OPCOES_MENU):
            console.print("[green]Até a próxima, professor![/]")
            break
        console.print(f"[yellow]{OPCOES_MENU[opcao - 1]}: em construção.[/]")
        console.input("[dim]Enter para voltar...[/]")


if __name__ == "__main__":
    main()
