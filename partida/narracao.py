import random


def carregar_frases(linhas):
    """
    Organiza as frases de narração por tipo de lance.

    Cada linha deve seguir o formato "chave|texto". A chave é normalizada em minúsculas e sem espaços nas
    pontas, e o texto é acrescentado à lista daquela chave. Linhas sem o separador "|" ou com texto vazio são
    ignoradas.

    Args:
        linhas (list[str]): Linhas lidas do arquivo de narração.

    Returns:
        dict: Dicionário que associa cada chave a uma lista de frases possíveis.
    """
    frases = {}
    for linha in linhas:
        chave, separador, texto = linha.partition("|")
        if separador and texto.strip():
            frases.setdefault(chave.strip().lower(), []).append(texto.strip())
    return frases


def narrar(frases, chave, dados=None):
    """
    Monta uma frase de narração para um lance.

    Sorteia uma das frases cadastradas para a chave e substitui cada marcador "{nome}" pelo valor
    correspondente em dados. Se a chave não tiver frases cadastradas, a própria chave é usada como texto.

    Args:
        frases (dict): Frases de narração agrupadas por chave.
        chave (str): Tipo de lance a ser narrado.
        dados (dict | None): Valores que preenchem os marcadores da frase. Padrão None.

    Returns:
        str: Frase de narração pronta para exibição.
    """
    texto = random.choice(frases.get(chave, [chave]))
    for nome, valor in (dados or {}).items():
        texto = texto.replace("{" + nome + "}", str(valor))
    return texto
