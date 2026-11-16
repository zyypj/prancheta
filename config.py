from pathlib import Path

NOME_JOGO = "PRANCHETA"
VERSAO = "1.0"

PASTA_RAIZ = Path(__file__).resolve().parent
PASTA_DADOS = PASTA_RAIZ / "dados"
PASTA_SAVES = PASTA_DADOS / "saves"
PASTA_SUMULAS = PASTA_DADOS / "sumulas"
ARQUIVO_TIMES = PASTA_DADOS / "times.json"
ARQUIVO_NOMES = PASTA_DADOS / "nomes.txt"
ARQUIVO_NARRACAO = PASTA_DADOS / "narracao.txt"
ARQUIVO_EVENTOS = PASTA_DADOS / "eventos.json"
ARQUIVO_RANKING = PASTA_DADOS / "ranking.csv"

CAMPOS_RANKING = ("tecnico", "clube", "posicao", "pontos", "pontuacao", "desfecho", "data")

FORMACOES = {
    "4-4-2": (4, 4, 2),
    "4-3-3": (4, 3, 3),
    "3-5-2": (3, 5, 2),
    "5-3-2": (5, 3, 2),
    "4-5-1": (4, 5, 1),
}
ESTILOS = ("posse", "contra-ataque", "jogo direto")
NOMES_ESTILOS = {"posse": "Posse de bola", "contra-ataque": "Contra-ataque", "jogo direto": "Jogo direto"}

POSICOES = ("GOL", "DEF", "MEI", "ATA")
COMPOSICAO_ELENCO = {"GOL": 2, "DEF": 6, "MEI": 6, "ATA": 4}

NIVEIS = {
    "grande": {"nome": "Grande", "meta": "título", "multiplicador": 1.0, "posicao_meta": 1},
    "medio": {"nome": "Médio", "meta": "G4", "multiplicador": 1.3, "posicao_meta": 4},
    "pequeno": {"nome": "Pequeno", "meta": "não cair", "multiplicador": 1.6, "posicao_meta": 8},
}

TOTAL_RODADAS = 18
PONTOS_VITORIA = 3
PONTOS_EMPATE = 1
ZONA_G4 = 4
ZONA_REBAIXAMENTO = 2

CONFIANCA_INICIAL = 60
CONFIANCA_VITORIA = 6
CONFIANCA_EMPATE = 0
CONFIANCA_DERROTA = -8
CONFIANCA_ZEBRA = 4
DIFERENCA_FAVORITISMO = 5

BONUS_META = 300
BONUS_TITULO = 200

MAX_SUBSTITUICOES = 5
RECUPERACAO_ENERGIA = 30
ENERGIA_SEM_PERDA = 50
LIMITE_AMARELOS = 3
BONUS_GRANDE_FASE = 5

MANDO_DE_CAMPO = 10
MINUTOS_POR_LANCE = (3, 6)
ACRESCIMOS = (1, 5)

PAUSA_RAPIDA = 0.15
