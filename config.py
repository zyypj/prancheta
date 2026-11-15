from pathlib import Path

NOME_JOGO = "PRANCHETA"
SLOGAN = "o futebol é decidido aqui"

PASTA_RAIZ = Path(__file__).resolve().parent
PASTA_DADOS = PASTA_RAIZ / "dados"
PASTA_SAVES = PASTA_DADOS / "saves"
ARQUIVO_TIMES = PASTA_DADOS / "times.json"
ARQUIVO_RANKING = PASTA_DADOS / "ranking.csv"
ARQUIVO_NARRACAO = PASTA_DADOS / "narracao.txt"

FORMACOES = {
    "4-4-2": (4, 4, 2),
    "4-3-3": (4, 3, 3),
    "5-3-2": (5, 3, 2),
}

POSTURAS = ("defensiva", "equilibrada", "ofensiva")
