import csv
import os

from config import ARQUIVO_RANKING, CAMPOS_RANKING


def registrar_ranking(linha, caminho=ARQUIVO_RANKING):
    """
    Registra o resultado de uma temporada no ranking em CSV.

    O arquivo usa as colunas de CAMPOS_RANKING (tecnico, clube, posicao, pontos, pontuacao, desfecho e data). O cabeçalho é escrito apenas quando o arquivo ainda não existe ou está vazio, e campos ausentes na linha ficam em branco. Erros de sistema de arquivos são capturados por try/except e indicados no retorno.

    Args:
        linha (dict): Dados da temporada, com chaves iguais às colunas do ranking.
        caminho (str | Path): Caminho do arquivo CSV. Padrão: ARQUIVO_RANKING (dados/ranking.csv).

    Returns:
        bool: True se a linha foi gravada, False em caso de erro.
    """
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
    """
    Converte a pontuação de uma linha do ranking para número inteiro.

    Valores ausentes ou que não representam um inteiro são tratados por try/except e viram 0.

    Args:
        linha (dict): Linha lida do CSV do ranking.

    Returns:
        int: Pontuação da linha ou 0 se ela for inválida.
    """
    try:
        return int(linha.get("pontuacao", 0))
    except (TypeError, ValueError):
        return 0


def ler_ranking(limite=10, caminho=ARQUIVO_RANKING):
    """
    Lê as melhores campanhas registradas no ranking em CSV.

    As linhas são ordenadas pela pontuação, da maior para a menor. Se o arquivo não puder ser aberto, o erro é capturado por try/except e a função devolve uma lista vazia.

    Args:
        limite (int): Quantidade máxima de linhas devolvidas. Padrão: 10.
        caminho (str | Path): Caminho do arquivo CSV. Padrão: ARQUIVO_RANKING (dados/ranking.csv).

    Returns:
        list: Dicionários com as linhas do ranking, com os valores em texto, ou lista vazia em caso de erro.
    """
    try:
        with open(caminho, encoding="utf-8", newline="") as arquivo:
            linhas = list(csv.DictReader(arquivo))
    except OSError:
        return []
    linhas.sort(key=converter_pontuacao, reverse=True)
    return linhas[:limite]
