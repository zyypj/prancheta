import random


def carregar_frases(linhas):
    frases = {}
    for linha in linhas:
        chave, separador, texto = linha.partition("|")
        if separador and texto.strip():
            frases.setdefault(chave.strip().lower(), []).append(texto.strip())
    return frases


def narrar(frases, chave, dados=None):
    texto = random.choice(frases.get(chave, [chave]))
    for nome, valor in (dados or {}).items():
        texto = texto.replace("{" + nome + "}", str(valor))
    return texto
