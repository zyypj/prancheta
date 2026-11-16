from rich.table import Table

from config import BONUS_TREINO, FOCOS_DE_TREINO, INTENSIDADES_DE_TREINO
from elenco.escalacao import rotulo, valor_de_mercado
from elenco.treino import grupo_de_treino, pode_treinar, treinar
from interface.campo import barra
from interface.entrada import console, ler_opcao, pausar
from interface.telas import mostrar_mensagem, titulo
from liga.temporada import clube_do_jogador
from mercado.transferencias import dinheiro

GRUPOS = (("titulares", "Titulares"), ("reservas", "Reservas"), ("todos", "Elenco todo"))
NOMES_ATRIBUTOS = {"fin": "finalização", "pas": "passe", "des": "desarme", "fis": "físico", "ref": "reflexo"}


def escolher_da_lista(rotulo_pergunta, opcoes):
    """
    Mostra uma lista numerada de opções e lê a escolhida.

    Args:
        rotulo_pergunta (str): Texto da pergunta.
        opcoes (list[str]): Textos das opções.

    Returns:
        int: Índice da opção escolhida, começando em 0, ou -1 se o usuário voltou com 0.
    """
    console.print(f"\n [bold]{rotulo_pergunta}[/]")
    for numero, texto in enumerate(opcoes, start=1):
        console.print(f" {numero} - {texto}")
    console.print(" 0 - Voltar")
    return ler_opcao(0, len(opcoes)) - 1


def mostrar_resultado_do_treino(foco, resumo):
    """
    Mostra o que o treino mudou: energia do grupo, quem evoluiu, quem valorizou e quem se lesionou.

    Args:
        foco (str): Foco escolhido.
        resumo (dict): Resumo devolvido por treinar.
    """
    titulo("RESULTADO DO TREINO")
    participantes = resumo["participantes"]
    energia = resumo["energia"]
    sinal = "+" if energia >= 0 else ""
    console.print(f" {len(participantes)} jogadores treinaram. Energia de cada um: [bold]{sinal}{energia}[/].")
    if FOCOS_DE_TREINO[foco]["atributo"]:
        nome = NOMES_ATRIBUTOS[FOCOS_DE_TREINO[foco]["atributo"]]
        console.print(f" No próximo jogo, todos eles têm [bold]+{BONUS_TREINO}[/] de {nome}.")
    if resumo["evoluiram"]:
        tabela = Table(title="Evoluíram de vez", title_justify="left", header_style="bold")
        for coluna in ("Jogador", "Atributo", "Novo valor", "Qualidade", "Valor de mercado"):
            tabela.add_column(coluna)
        for jogador, atributo, valor, subiu in resumo["evoluiram"]:
            qualidade = f"[green]{jogador['qualidade']} (+1)[/]" if subiu else str(jogador["qualidade"])
            tabela.add_row(
                rotulo(jogador), NOMES_ATRIBUTOS[atributo], str(valor), qualidade, dinheiro(valor_de_mercado(jogador))
            )
        console.print(tabela)
    elif FOCOS_DE_TREINO[foco]["atributo"]:
        console.print(" [dim]Ninguém evoluiu de vez desta vez.[/]")
    for jogador in resumo["lesionados"]:
        console.print(f" [red]{rotulo(jogador)} sentiu o treino pesado e está lesionado por 1 rodada.[/]")
    pausar()


def tela_treino(estado):
    """
    Conduz o treino da semana antes do jogo.

    Mostra a energia média dos titulares e dos reservas, e o usuário escolhe o foco (um atributo ou
    recuperação), a intensidade (leve, normal ou pesado, com o gasto de energia e a chance de evolução de cada
    uma) e quem treina. Treinar os titulares melhora o atributo deles no jogo, mas cansa quem vai jogar;
    treinar os reservas faz o elenco evoluir sem cansar o time. Só é possível treinar uma vez por etapa.

    Args:
        estado (dict): Estado atual da temporada.
    """
    if not pode_treinar(estado):
        mostrar_mensagem("O elenco já treinou esta semana. Volte depois do jogo.", "yellow")
        return
    clube = clube_do_jogador(estado)
    titulo("TREINO DA SEMANA")
    for chave, nome in GRUPOS[:2]:
        jogadores = grupo_de_treino(clube, chave, "recuperacao")
        media = sum(j["energia"] for j in jogadores) / max(1, len(jogadores))
        console.print(f" Energia média dos {nome.lower()}: {barra(media)}")
    console.print(
        " [dim]Treinar melhora o jogador no próximo jogo e pode fazê-lo evoluir de vez (mais nos jovens), mas cansa.[/]"
    )
    focos = list(FOCOS_DE_TREINO)
    indice = escolher_da_lista("Foco do treino:", [FOCOS_DE_TREINO[foco]["nome"] for foco in focos])
    if indice < 0:
        return
    foco = focos[indice]
    intensidade = "normal"
    if foco != "recuperacao":
        intensidades = list(INTENSIDADES_DE_TREINO)
        textos = [
            f"{dados['nome']} (energia -{dados['energia']}, chance de evoluir {round(dados['evolucao'] * 100)}%"
            + (f", risco de lesão {round(dados['lesao'] * 100)}%)" if dados["lesao"] else ")")
            for dados in INTENSIDADES_DE_TREINO.values()
        ]
        indice = escolher_da_lista("Intensidade:", textos)
        if indice < 0:
            return
        intensidade = intensidades[indice]
    indice = escolher_da_lista("Quem treina?", [nome for _, nome in GRUPOS])
    if indice < 0:
        return
    grupo = GRUPOS[indice][0]
    if not grupo_de_treino(clube, grupo, foco):
        mostrar_mensagem("Ninguém desse grupo pode fazer esse treino agora.", "yellow")
        return
    mostrar_resultado_do_treino(foco, treinar(estado, foco, intensidade, grupo))
