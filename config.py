from pathlib import Path

NOME_JOGO = "PRANCHETA"
VERSAO = "3.0"
VERSAO_SAVE = 3
VERSOES_DE_SAVE_ACEITAS = (2, 3)

PASTA_RAIZ = Path(__file__).resolve().parent
PASTA_DADOS = PASTA_RAIZ / "dados"
PASTA_SAVES = PASTA_DADOS / "saves"
PASTA_SUMULAS = PASTA_DADOS / "sumulas"
ARQUIVO_TIMES = PASTA_DADOS / "times.json"
ARQUIVO_NOMES = PASTA_DADOS / "nomes.txt"
ARQUIVO_NARRACAO = PASTA_DADOS / "narracao.txt"
ARQUIVO_EVENTOS = PASTA_DADOS / "eventos.json"
ARQUIVO_BASTIDORES = PASTA_DADOS / "bastidores.json"
ARQUIVO_ENTREVISTAS = PASTA_DADOS / "entrevistas.json"
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
COMPOSICAO_ELENCO = {"GOL": 3, "DEF": 7, "MEI": 7, "ATA": 5}

NIVEIS = {
    "grande": {"nome": "Grande", "multiplicador": 1.0, "caixa": 60.0},
    "medio": {"nome": "Médio", "multiplicador": 1.3, "caixa": 30.0},
    "pequeno": {"nome": "Pequeno", "multiplicador": 1.6, "caixa": 15.0},
}
DIVISOES = {1: "Série A", 2: "Série B"}
METAS = {
    1: {"grande": ("título", 1), "medio": ("G4", 4), "pequeno": ("não cair", 8)},
    2: {"grande": ("acesso", 2), "medio": ("brigar pelo acesso", 4), "pequeno": ("meio da tabela", 6)},
}
FATOR_RECEITA_SERIE_B = 0.6
PREMIO_CAMPEAO = {1: 6.0, 2: 3.0}
PREMIO_ACESSO = 2.0

TOTAL_RODADAS = 9
FASES_COPA = ("preliminar", "quartas", "semifinal", "final")
NOMES_FASES = {
    "preliminar": "Fase preliminar",
    "quartas": "Quartas de final",
    "semifinal": "Semifinal",
    "final": "Final",
}
CLASSIFICADOS_DIRETO_COPA = 4
VAGAS_SERIE_B_COPA = 2
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
ZONA_ACESSO = 2

CONFIANCA_INICIAL = 60
CONFIANCA_RENOVADO = 70
CONFIANCA_SEGUNDA_CHANCE = 45
REPUTACAO_INICIAL = {"grande": 3, "medio": 2, "pequeno": 1}
REPUTACAO_MAXIMA = 5
PESO_DO_NIVEL = {"grande": 3, "medio": 2, "pequeno": 1}
CHANCE_CONVITE = 0.45
CHANCE_PROPOSTA_SEMANA = 0.3
PROPOSTAS_NA_JANELA = (1, 3)
IDADE_APOSENTADORIA = 35
IDADE_LIMITE = 38
EVOLUCAO_POR_IDADE = ((21, 1, 4), (24, 0, 3), (28, -1, 1), (31, -2, 0), (33, -3, -1), (99, -5, -2))
CHANCE_JOIA_DA_BASE = 0.3
FOLGA_DOS_TITULARES = 2.5
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
MAX_ELENCO = 28
ELENCO_MINIMO = 18
MINIMO_POR_POSICAO = {"GOL": 2, "DEF": 5, "MEI": 5, "ATA": 3}
AGENTES_LIVRES = 30
MAXIMO_LIVRES = 40

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

BILHETERIA = {"grande": 1.5, "medio": 1.0, "pequeno": 0.6}
COTA_TV = {"grande": 1.2, "medio": 0.8, "pequeno": 0.5}
BONUS_DESAFIO = 25
BONUS_OBJETIVO = 60
PREMIO_OBJETIVO = 2.0
DESAFIOS_PARA_OBJETIVO = 6
CHANCE_DISCUSSAO = 0.55
CHANCE_DISCUSSAO_ELENCO = 0.2
PENALIDADE_INSATISFEITO = 4
MULTA_DISCUSSAO = 0.5
CHANCE_EVENTO_PRE = 0.3
CHANCE_EVENTO_POS = 0.35
CHANCE_ENTREVISTA = {"grande": 0.4, "medio": 0.25, "pequeno": 0.12}
PESO_TORCIDA = {"grande": 2.0, "medio": 1.0, "pequeno": 0.5}
TORCIDA_NA_FESTA = 6

MAX_SUBSTITUICOES = 5
RECUPERACAO_ENERGIA = 30
ENERGIA_SEM_PERDA = 50
LIMITE_AMARELOS = 3
BONUS_GRANDE_FASE = 5

MANDO_DE_CAMPO = 10
MINUTOS_POR_LANCE = (3, 6)
ACRESCIMOS = (1, 5)

PAUSA_RAPIDA = 0.15
REVELACOES_POR_PARTIDA = 3
FOCOS_DE_TREINO = {
    "finalizacao": {"nome": "Finalização", "atributo": "fin"},
    "passe": {"nome": "Passe", "atributo": "pas"},
    "desarme": {"nome": "Desarme", "atributo": "des"},
    "fisico": {"nome": "Físico", "atributo": "fis"},
    "goleiros": {"nome": "Goleiros (reflexo)", "atributo": "ref"},
    "recuperacao": {"nome": "Recuperação", "atributo": None},
}
INTENSIDADES_DE_TREINO = {
    "leve": {"nome": "Leve", "energia": 6, "evolucao": 0.12, "lesao": 0.0},
    "normal": {"nome": "Normal", "energia": 12, "evolucao": 0.25, "lesao": 0.0},
    "pesado": {"nome": "Pesado", "energia": 22, "evolucao": 0.4, "lesao": 0.04},
}
BONUS_TREINO = 3
EVOLUCOES_PARA_QUALIDADE = 2
CHANCE_MINIJOGO = {
    "drible": 0.4,
    "goleiro": 1.0,
    "cabeceio": 0.3,
    "chute": 0.25,
    "cara_a_cara": 0.5,
    "goleiro_cara": 0.5,
    "desarme": 0.15,
    "falta": 0.6,
    "penalti": 1.0,
}
