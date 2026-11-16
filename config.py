from pathlib import Path

NOME_JOGO = "PRANCHETA"
VERSAO = "2.0"
VERSAO_SAVE = 2

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
    "grande": {"nome": "Grande", "meta": "título", "multiplicador": 1.0, "posicao_meta": 1, "caixa": 60.0},
    "medio": {"nome": "Médio", "meta": "G4", "multiplicador": 1.3, "posicao_meta": 4, "caixa": 30.0},
    "pequeno": {"nome": "Pequeno", "meta": "não cair", "multiplicador": 1.6, "posicao_meta": 8, "caixa": 15.0},
}

TOTAL_RODADAS = 9
FASES_COPA = ("preliminar", "quartas", "semifinal", "final")
NOMES_FASES = {
    "preliminar": "Fase preliminar",
    "quartas": "Quartas de final",
    "semifinal": "Semifinal",
    "final": "Final",
}
CLASSIFICADOS_DIRETO_COPA = 6
AGENDA = (
    ("liga", 1),
    ("liga", 2),
    ("copa", "preliminar"),
    ("liga", 3),
    ("liga", 4),
    ("copa", "quartas"),
    ("liga", 5),
    ("liga", 6),
    ("copa", "semifinal"),
    ("liga", 7),
    ("liga", 8),
    ("copa", "final"),
    ("liga", 9),
)
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
BONUS_COPA = 250

CONFIANCA_AVANCO_COPA = 3
CONFIANCA_QUEDA_COPA = -4
CONFIANCA_TITULO_COPA = 10

PREMIO_VITORIA = 0.8
PREMIO_EMPATE = 0.3
PREMIO_FASE_COPA = 2.0
PREMIO_TITULO_COPA = 5.0
MAX_ELENCO = 25
MINIMO_POR_POSICAO = {"GOL": 2, "DEF": 5, "MEI": 5, "ATA": 3}
AGENTES_LIVRES = 14

CLUBES_DO_EXTERIOR = (
    "Calcio Ventura (Itália)",
    "Deportivo Mirasol (Espanha)",
    "Olympique Garonne (França)",
    "Lusitânia FC (Portugal)",
    "FK Danúbio (Sérvia)",
    "Al-Nakhla (Arábia Saudita)",
    "Sakura Minato (Japão)",
    "Atlético Pampero (Argentina)",
)
FAIXA_OFERTA_EXTERIOR = (1.1, 1.4)
FAIXA_TETO_EXTERIOR = (1.0, 1.3)
QUEDA_QUALIDADE_GAROTO = 12
CONFIANCA_VENDA = 6
CONFIANCA_SEGURAR = -3
CONFIANCA_NEGOCIACAO_FRACASSADA = -2

MAX_SUBSTITUICOES = 5
RECUPERACAO_ENERGIA = 30
ENERGIA_SEM_PERDA = 50
LIMITE_AMARELOS = 3
BONUS_GRANDE_FASE = 5

MANDO_DE_CAMPO = 10
MINUTOS_POR_LANCE = (3, 6)
ACRESCIMOS = (1, 5)

PAUSA_RAPIDA = 0.15
