import csv
import os

from config import ARQUIVO_RANKING, CAMPOS_RANKING


def registrar_ranking(linha, caminho=ARQUIVO_RANKING):
    try:
        existe = os.path.exists(caminho) and os.path.getsize(caminho) > 0
        with open(caminho, "a", encoding="utf-8", newline="") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_RANKING)
            if not existe:
                escritor.writeheader()
            escritor.writerow({campo: linha.get(campo, "") for campo in CAMPOS_RANKING})
        return True
    except OSError:
        return False


def converter_pontuacao(linha):
    try:
        return int(linha.get("pontuacao", 0))
    except (TypeError, ValueError):
        return 0


def ler_ranking(limite=10, caminho=ARQUIVO_RANKING):
    try:
        with open(caminho, encoding="utf-8", newline="") as arquivo:
            linhas = list(csv.DictReader(arquivo))
    except OSError:
        return []
    linhas.sort(key=converter_pontuacao, reverse=True)
    return linhas[:limite]
