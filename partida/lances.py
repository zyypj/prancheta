import random

from config import MANDO_DE_CAMPO, MAX_SUBSTITUICOES, REVELACOES_POR_PARTIDA
from elenco.escalacao import atributo_efetivo, disponivel, forca_setores, limitar, rotulo
from elenco.substituicoes import marcar_desfalques, registrar_amarelo, substituir
from partida.narracao import narrar

DESCRICAO_ZONAS = {
    "defesa": "no campo de defesa",
    "meio": "no meio-campo",
    "intermediaria": "na intermediária",
    "ataque": "na entrada da área",
    "linha_de_fundo": "na linha de fundo",
    "area": "dentro da área",
}
PROXIMA_ZONA = {
    "defesa": "meio",
    "meio": "intermediaria",
    "intermediaria": "ataque",
    "ataque": "area",
    "linha_de_fundo": "area",
}
ACOES = {
    "defesa": ("tocar", "conduzir", "lancar", "inverter"),
    "meio": ("tocar", "enfiar", "driblar", "lancar", "abrir"),
    "intermediaria": ("tocar", "enfiar", "driblar", "abrir", "chutar"),
    "ataque": ("tocar", "tabelar", "driblar", "cruzar", "chutar"),
    "linha_de_fundo": ("cruzar", "rasteiro", "driblar", "chutar"),
    "area": ("chutar", "driblar", "tocar"),
}
NOMES_ACOES = {
    "tocar": "Tocar",
    "enfiar": "Enfiada",
    "driblar": "Driblar",
    "lancar": "Lançar",
    "abrir": "Abrir na ponta",
    "tabelar": "Tabelar",
    "cruzar": "Cruzar",
    "chutar": "Chutar",
    "conduzir": "Conduzir",
    "inverter": "Inverter o jogo",
    "rasteiro": "Cruzar rasteiro para trás",
}
CHANCE_BASE = {
    "defesa": {"tocar": 0.86, "conduzir": 0.66, "lancar": 0.40, "inverter": 0.70},
    "meio": {"tocar": 0.80, "enfiar": 0.32, "lancar": 0.45, "abrir": 0.74},
    "intermediaria": {"tocar": 0.72, "enfiar": 0.30, "abrir": 0.70},
    "ataque": {"tocar": 0.76, "tabelar": 0.50, "cruzar": 0.55},
    "linha_de_fundo": {"cruzar": 0.60, "rasteiro": 0.52},
    "area": {"tocar": 0.66},
}
LOCAL_DO_CHUTE = {"intermediaria": "intermediaria", "ataque": "longe", "linha_de_fundo": "sem_angulo", "area": "area"}
ZONA_DO_LOCAL = {
    "longe": "ataque",
    "meio_campo": "meio",
    "falta": "ataque",
    "primeira": "ataque",
    "intermediaria": "intermediaria",
    "sem_angulo": "linha_de_fundo",
}
SETOR_DO_ATAQUE = {
    "defesa": "meio",
    "meio": "meio",
    "intermediaria": "meio",
    "ataque": "ataque",
    "linha_de_fundo": "ataque",
    "area": "ataque",
}
SETOR_DA_DEFESA = {
    "defesa": "ataque",
    "meio": "meio",
    "intermediaria": "meio",
    "ataque": "defesa",
    "linha_de_fundo": "defesa",
    "area": "defesa",
}
LUGARES_DE_INICIO = {"defesa": 3, "meio": 5, "intermediaria": 2}
PASSOS_DA_POSSE = 8
DRIBLES = {
    "corte": {"nome": "Corte seco", "base": 0.56, "bonus": 0.00, "peso": 4},
    "caneta": {"nome": "Caneta", "base": 0.42, "bonus": 0.06, "peso": 2},
    "chapeu": {"nome": "Chapéu", "base": 0.33, "bonus": 0.10, "peso": 1},
    "arrancada": {"nome": "Arrancada", "base": 0.50, "bonus": 0.02, "peso": 3},
}
CHUTES = {
    "colocado": {"nome": "Colocado", "texto": "colocado", "alvo": 0.72, "goleiro": 1.0, "peso": 4},
    "forte": {"nome": "Forte", "texto": "com força", "alvo": 0.56, "goleiro": 0.75, "peso": 3},
    "cavadinha": {"nome": "Cavadinha", "texto": "de cavadinha", "alvo": 0.52, "goleiro": 1.3, "peso": 1},
}
LOCAIS = {
    "meio_campo": {"gol": 0.25, "alvo": -0.30},
    "longe": {"gol": 0.14, "alvo": -0.14},
    "area": {"gol": 0.36, "alvo": 0.00},
    "cara": {"gol": 0.55, "alvo": 0.05},
    "cabeceio": {"gol": 0.32, "alvo": -0.12},
    "voleio": {"gol": 0.40, "alvo": -0.18},
    "rebote": {"gol": 0.50, "alvo": -0.05},
    "falta": {"gol": 0.22, "alvo": -0.10},
    "escanteio": {"gol": 0.30, "alvo": -0.12},
    "primeira": {"gol": 0.17, "alvo": -0.16},
    "bicicleta": {"gol": 0.48, "alvo": -0.32},
    "intermediaria": {"gol": 0.10, "alvo": -0.22},
    "sem_angulo": {"gol": 0.10, "alvo": -0.24},
}
LOCAIS_COM_BLOQUEIO = ("longe", "area", "primeira", "intermediaria")
GOLEIRO_NO_CARA_A_CARA = (
    ("sair", "Sair abafando", 3),
    ("esperar", "Esperar no gol", 3),
    ("angulo", "Fechar o ângulo", 2),
)
EFEITO_GOLEIRO = {
    "colocado": {"sair": 0.12, "esperar": -0.12, "angulo": 0.0},
    "forte": {"sair": -0.08, "esperar": 0.08, "angulo": -0.12},
    "cavadinha": {"sair": 0.30, "esperar": -0.30, "angulo": 0.04},
    "driblar": {"sair": 0.10, "esperar": -0.10, "angulo": -0.02},
}
BLOQUEIOS = (
    ("carrinho", "Carrinho para bloquear", 2),
    ("fechar", "Fechar o ângulo do chute", 3),
    ("goleiro", "Deixar para o goleiro", 3),
)
DEFESAS = ("bote", "pressao", "fechar", "recuar", "falta")
NOMES_DEFESAS = {
    "bote": "Dar o bote",
    "pressao": "Pressão alta",
    "fechar": "Fechar espaço",
    "recuar": "Recuar a linha",
    "falta": "Falta tática",
}
EFEITO_DEFESA = {
    "bote": {
        "defesa": -0.05,
        "meio": -0.07,
        "intermediaria": -0.07,
        "ataque": -0.07,
        "linha_de_fundo": -0.07,
        "area": -0.07,
    },
    "pressao": {
        "defesa": -0.12,
        "meio": -0.10,
        "intermediaria": -0.02,
        "ataque": 0.04,
        "linha_de_fundo": 0.04,
        "area": 0.04,
    },
    "fechar": {
        "defesa": -0.02,
        "meio": -0.03,
        "intermediaria": -0.03,
        "ataque": -0.03,
        "linha_de_fundo": -0.03,
        "area": -0.03,
    },
    "recuar": {
        "defesa": 0.08,
        "meio": 0.05,
        "intermediaria": 0.02,
        "ataque": -0.02,
        "linha_de_fundo": -0.04,
        "area": -0.06,
    },
    "falta": {"defesa": 0.0, "meio": 0.0, "intermediaria": 0.0, "ataque": 0.0, "linha_de_fundo": 0.0, "area": -0.07},
}
CANTOS = ("esquerda", "meio", "direita")
FORCAS_PENALTI = ("colocado", "forte", "paradinha")

PESO_DIFERENCA = 0.005
PESO_MEIO = 0.006
PESO_FINALIZACAO = 0.004
FATOR_GOL = 1.55
PESOS_PORTADOR = {
    "defesa": {"DEF": 5, "MEI": 3},
    "meio": {"MEI": 5, "DEF": 1, "ATA": 2},
    "intermediaria": {"MEI": 5, "ATA": 3, "DEF": 1},
    "ataque": {"ATA": 4, "MEI": 4, "DEF": 0.5},
    "linha_de_fundo": {"ATA": 4, "MEI": 3, "DEF": 2},
    "area": {"ATA": 6, "MEI": 2, "DEF": 0.5},
}
PESOS_MARCADOR = {
    "defesa": {"ATA": 5, "MEI": 3},
    "meio": {"MEI": 5, "DEF": 2, "ATA": 1},
    "intermediaria": {"MEI": 4, "DEF": 3},
    "ataque": {"DEF": 5, "MEI": 2},
    "linha_de_fundo": {"DEF": 6, "MEI": 1},
    "area": {"DEF": 6, "MEI": 1},
}
PESOS_CABECEIO = {"ATA": 5, "DEF": 2, "MEI": 1}
PESOS_REBOTE = {"ATA": 5, "MEI": 3, "DEF": 1}


def montar_time(clube, plano, em_casa):
    """
    Monta a estrutura de um time para a partida a partir do clube.

    Marca os desfalques do elenco, separa os titulares disponíveis dos reservas disponíveis e zera os
    contadores da partida (gols, cartões, chutes, posse, faltas e substituições).

    Args:
        clube (dict): Clube com elenco, titulares e dados de identificação.
        plano (dict): Plano tático usado na partida; é copiado para o time.
        em_casa (bool): Se o time joga com mando de campo.

    Returns:
        dict: Estrutura do time com jogadores em campo, banco e estatísticas zeradas.
    """
    marcar_desfalques(clube["elenco"])
    titulares = [jogador for jogador in clube["elenco"] if jogador["id"] in clube["titulares"] and disponivel(jogador)]
    banco = [jogador for jogador in clube["elenco"] if jogador["id"] not in clube["titulares"] and disponivel(jogador)]
    return {
        "id": clube["id"],
        "nome": clube["nome"],
        "sigla": clube["sigla"],
        "cor": clube["cor"],
        "forca": clube["forca"],
        "plano": dict(plano),
        "ofensividade_base": plano["ofensividade"],
        "em_casa": em_casa,
        "em_campo": titulares,
        "banco": banco,
        "saiu": [],
        "amarelados": [],
        "subs": 0,
        "gols": 0,
        "vermelhos": 0,
        "chutes": 0,
        "no_alvo": 0,
        "posse": 0,
        "faltas": 0,
    }


def criar_partida(clube_casa, clube_fora, frases, plano_casa=None, plano_fora=None, neutro=False):
    """
    Cria o estado inicial de uma partida entre dois clubes.

    Monta os dois times, define relógio, posição da bola e narração vazias, e sorteia chuva com 12% de chance.
    O mandante só recebe mando de campo se o jogo não for em campo neutro.

    Args:
        clube_casa (dict): Clube mandante.
        clube_fora (dict): Clube visitante.
        frases (dict): Frases usadas na narração.
        plano_casa (dict): Plano tático do mandante. Padrão None, que usa o plano do próprio clube.
        plano_fora (dict): Plano tático do visitante. Padrão None, que usa o plano do próprio clube.
        neutro (bool): Se a partida é em campo neutro. Padrão False.

    Returns:
        dict: Estado completo da partida, pronto para ser jogado.
    """
    return {
        "casa": clube_casa["id"],
        "fora": clube_fora["id"],
        "neutro": neutro,
        "penaltis": None,
        "times": {
            clube_casa["id"]: montar_time(clube_casa, plano_casa or clube_casa["plano"], not neutro),
            clube_fora["id"]: montar_time(clube_fora, plano_fora or clube_fora["plano"], False),
        },
        "minuto": 0,
        "tempo": 1,
        "limite": 45,
        "frases": frases,
        "narracao": [],
        "sumula": [],
        "ocorrencias": [],
        "chances": None,
        "revelacoes": {clube_casa["id"]: REVELACOES_POR_PARTIDA, clube_fora["id"]: REVELACOES_POR_PARTIDA},
        "chuva": random.random() < 0.12,
        "torcida": 0,
        "bola": {"time": None, "zona": "meio", "faixa": 1},
        "portador": None,
        "controles": {},
        "exibir": None,
        "modo": "simular",
        "velocidade": "normal",
        "encerrada": False,
        "cache_setores": {},
        "ultimo_local": None,
    }


def outro(partida, time_id):
    """
    Retorna o identificador do adversário de um time na partida.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Identificador de um dos times.

    Returns:
        str: Identificador do outro time.
    """
    return partida["fora"] if time_id == partida["casa"] else partida["casa"]


def placar(partida):
    """
    Monta o texto do placar atual com as siglas dos times.

    Args:
        partida (dict): Estado da partida.

    Returns:
        str: Placar no formato "SIG 1 x 0 SIG".
    """
    casa = partida["times"][partida["casa"]]
    fora = partida["times"][partida["fora"]]
    return f"{casa['sigla']} {casa['gols']} x {fora['gols']} {fora['sigla']}"


def minuto_texto(partida):
    """
    Formata o minuto atual da partida, indicando os acréscimos.

    Usa 45 como base no primeiro tempo e 90 no segundo; passando da base, mostra o tempo extra no formato
    "45+2'".

    Args:
        partida (dict): Estado da partida.

    Returns:
        str: Minuto formatado, como "30'" ou "90+3'".
    """
    base = 45 if partida["tempo"] == 1 else 90
    if partida["minuto"] > base:
        return f"{base}+{partida['minuto'] - base}'"
    return f"{partida['minuto']}'"


def mover_bola(partida, time_id, zona, faixa=None):
    """
    Atualiza a posição da bola na partida.

    Args:
        partida (dict): Estado da partida.
        time_id (str | None): Time com a posse, ou None quando a bola está disputada.
        zona (str): Zona do campo ("meio", "ataque", "area" ou "gol").
        faixa (int | None): Faixa lateral (0, 1 ou 2). Padrão None, que sorteia uma faixa.
    """
    partida["bola"] = {"time": time_id, "zona": zona, "faixa": random.randint(0, 2) if faixa is None else faixa}


def entregar_bola(partida, time_id, zona, faixa, portador):
    """
    Define o jogador com a bola e move a bola para a zona indicada.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time com a posse.
        zona (str): Zona do campo onde a bola fica.
        faixa (int | None): Faixa lateral; None sorteia uma faixa.
        portador (dict): Jogador que passa a conduzir a bola.
    """
    partida["portador"] = portador
    mover_bola(partida, time_id, zona, faixa)


def registrar(partida, chave, dados=None, tipo="lance", time_id=None):
    """
    Narra um lance e o envia para a exibição da partida.

    Gera o texto da narração a partir da chave, guarda apenas as cinco últimas linhas narradas com o minuto e,
    se houver uma função de exibição configurada, repassa o lance para ela.

    Args:
        partida (dict): Estado da partida.
        chave (str): Chave da frase de narração.
        dados (dict | None): Valores usados para preencher a frase. Padrão None.
        tipo (str): Tipo do lance, usado pela exibição. Padrão "lance".
        time_id (str | None): Time relacionado ao lance. Padrão None.

    Returns:
        str: Texto narrado.
    """
    texto = narrar(partida["frases"], chave, dados)
    partida["narracao"] = (partida["narracao"] + [f"{minuto_texto(partida)} {texto}"])[-5:]
    if partida["exibir"]:
        partida["exibir"](partida, {"texto": texto, "tipo": tipo, "time": time_id})
    return texto


def anotar_sumula(partida, texto):
    """
    Adiciona uma linha à súmula da partida, precedida do minuto atual.

    Args:
        partida (dict): Estado da partida.
        texto (str): Texto do acontecimento.
    """
    partida["sumula"].append(f"{minuto_texto(partida)} {texto}")


def goleiro_de(time):
    """
    Busca o goleiro que está em campo pelo time.

    Args:
        time (dict): Time da partida.

    Returns:
        dict | None: Jogador da posição GOL em campo, ou None se não houver.
    """
    return next((jogador for jogador in time["em_campo"] if jogador["pos"] == "GOL"), None)


def escolher_jogador(time, pesos, excluir=None):
    """
    Sorteia um jogador em campo, com probabilidade proporcional ao peso da sua posição.

    Considera apenas posições com peso positivo, sem o jogador excluído. Se ninguém se encaixar, usa qualquer
    jogador em campo exceto o excluído (ou o próprio excluído, se for o único), com peso mínimo de 0.5.

    Args:
        time (dict): Time da partida.
        pesos (dict): Peso de cada posição ("GOL", "DEF", "MEI", "ATA") no sorteio.
        excluir (dict | None): Jogador que não deve ser escolhido. Padrão None.

    Returns:
        dict: Jogador sorteado.
    """
    candidatos = [
        jogador for jogador in time["em_campo"] if jogador is not excluir and pesos.get(jogador["pos"], 0) > 0
    ]
    if not candidatos:
        candidatos = [jogador for jogador in time["em_campo"] if jogador is not excluir] or time["em_campo"]
    return random.choices(candidatos, weights=[pesos.get(jogador["pos"], 0.5) or 0.5 for jogador in candidatos])[0]


def atacante_de_referencia(time, excluir=None):
    """
    Escolhe o jogador de frente com melhor finalização, usado para estimar chances de jogadas que ainda não
    têm finalizador definido.

    Args:
        time (dict): Time da partida.
        excluir (dict | None): Jogador que não pode ser escolhido. Padrão None.

    Returns:
        dict: Atacante ou meia em campo com maior finalização efetiva, ou qualquer jogador se não houver.
    """
    candidatos = [j for j in time["em_campo"] if j is not excluir and j["pos"] in ("ATA", "MEI")]
    return max(candidatos or time["em_campo"], key=lambda j: atributo_efetivo(j, "fin"))


def melhor_batedor(time):
    """
    Escolhe o jogador de linha em campo com a maior finalização efetiva.

    Se só restar o goleiro em campo, ele é considerado.

    Args:
        time (dict): Time da partida.

    Returns:
        dict: Jogador escolhido para a cobrança.
    """
    linha = [jogador for jogador in time["em_campo"] if jogador["pos"] != "GOL"] or time["em_campo"]
    return max(linha, key=lambda jogador: atributo_efetivo(jogador, "fin"))


def perguntar(partida, time_id, pergunta, opcoes):
    """
    Pede ao controle do time que escolha uma das opções de um lance.

    Repassa a pergunta para a função "escolha" do controle do time (jogador humano ou IA). Se a resposta não
    for uma das chaves oferecidas, usa a primeira opção.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time que decide.
        pergunta (str): Texto da pergunta.
        opcoes (list): Lista de tuplas (chave, rótulo, peso) ou (chave, rótulo, peso, chance), em que a chance
            de a opção dar certo, entre 0 e 1, pode ser revelada pelo jogador humano.

    Returns:
        str: Chave da opção escolhida.
    """
    escolha = partida["controles"][time_id]["escolha"](partida, time_id, pergunta, opcoes)
    chaves = [opcao[0] for opcao in opcoes]
    return escolha if escolha in chaves else chaves[0]


def invalidar_setores(partida):
    """
    Limpa o cache de força dos setores dos times.

    Args:
        partida (dict): Estado da partida.
    """
    partida["cache_setores"] = {}


def setores(partida, time_id):
    """
    Calcula a força de cada setor do time em campo, usando cache.

    Parte da força dos setores dos jogadores em campo e soma o bônus de mando de campo para o time da casa,
    com mais 3 pontos enquanto a torcida estiver empurrando. O resultado fica guardado até o cache ser
    invalidado.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time a ser avaliado.

    Returns:
        dict: Força de cada setor ("defesa", "meio", "ataque" e "goleiro") já com os bônus.
    """
    if time_id in partida["cache_setores"]:
        return partida["cache_setores"][time_id]
    time = partida["times"][time_id]
    bonus = 0
    if time["em_casa"]:
        bonus += MANDO_DE_CAMPO
        if partida["torcida"] > 0:
            bonus += 3
    valores = {setor: valor + bonus for setor, valor in forca_setores(time["em_campo"]).items()}
    partida["cache_setores"][time_id] = valores
    return valores


def fazer_substituicao(partida, time_id, sai_id, entra_id, nome_saida=None):
    """
    Realiza uma substituição durante a partida.

    Sem jogador de saída (por exemplo, após uma lesão), apenas coloca o reserva em campo se ainda houver
    substituições disponíveis. Com jogador de saída, faz a troca normal. Em caso de sucesso, recalcula os
    setores, narra e anota a substituição na súmula.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time que faz a substituição.
        sai_id (str | None): Identificador do jogador que sai, ou None quando ninguém sai de campo.
        entra_id (str): Identificador do reserva que entra.
        nome_saida (str | None): Nome exibido para quem saiu quando sai_id é None. Padrão None, que mostra
            "-".

    Returns:
        bool: True se a substituição foi feita, False caso contrário.
    """
    time = partida["times"][time_id]
    if sai_id is None:
        entra = next((jogador for jogador in time["banco"] if jogador["id"] == entra_id), None)
        if entra is None or time["subs"] >= MAX_SUBSTITUICOES:
            return False
        time["banco"].remove(entra)
        time["em_campo"].append(entra)
        time["subs"] += 1
        nome_sai = nome_saida or "-"
    else:
        troca = substituir(time, sai_id, entra_id)
        if troca is None:
            return False
        nome_sai, entra = rotulo(troca[0]), troca[1]
    invalidar_setores(partida)
    registrar(
        partida,
        "substituicao",
        {"time": time["nome"], "sai": nome_sai, "entra": rotulo(entra)},
        tipo="substituicao",
        time_id=time_id,
    )
    anotar_sumula(partida, f"Substituição ({time['sigla']}): sai {nome_sai}, entra {rotulo(entra)}")
    return True


def pausar_todos(partida, motivo):
    """
    Avisa os controles dos dois times de uma pausa na partida.

    Args:
        partida (dict): Estado da partida.
        motivo (str): Motivo da pausa, como "intervalo" ou "expulsao".
    """
    for time_id in (partida["casa"], partida["fora"]):
        partida["controles"][time_id]["pausa"](partida, time_id, motivo)


def expulsar(partida, time_id, jogador, chave):
    """
    Expulsa um jogador da partida.

    Tira o jogador de campo, soma um vermelho ao time, suspende o jogador por pelo menos uma rodada, recalcula
    os setores, narra e anota na súmula, e pausa a partida para os dois times.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time do jogador expulso.
        jogador (dict): Jogador expulso.
        chave (str): Chave da narração ("vermelho" ou "segundo_amarelo").
    """
    time = partida["times"][time_id]
    if jogador in time["em_campo"]:
        time["em_campo"].remove(jogador)
        time["saiu"].append(jogador)
    time["vermelhos"] += 1
    jogador["suspenso"] = max(jogador["suspenso"], 1)
    partida["ocorrencias"].append({"tipo": "vermelho", "time": time_id, "jogador": jogador["id"]})
    invalidar_setores(partida)
    registrar(partida, chave, {"jogador": rotulo(jogador)}, tipo="vermelho", time_id=time_id)
    anotar_sumula(partida, f"Vermelho — {rotulo(jogador)} ({time['sigla']})")
    pausar_todos(partida, "expulsao")


def amarelar(partida, time_id, jogador):
    """
    Aplica um cartão amarelo a um jogador.

    Se o jogador já tem amarelo nesta partida, é expulso pelo segundo amarelo. Caso contrário, o cartão é
    contado para a suspensão por acúmulo, narrado e anotado na súmula, com aviso quando for o terceiro
    amarelo.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time do jogador.
        jogador (dict): Jogador advertido.
    """
    time = partida["times"][time_id]
    if jogador["id"] in time["amarelados"]:
        expulsar(partida, time_id, jogador, "segundo_amarelo")
        return
    time["amarelados"].append(jogador["id"])
    suspenso = registrar_amarelo(jogador)
    registrar(partida, "amarelo", {"jogador": rotulo(jogador)}, tipo="amarelo", time_id=time_id)
    aviso = " (3º amarelo, suspenso na próxima rodada)" if suspenso else ""
    anotar_sumula(partida, f"Amarelo — {rotulo(jogador)} ({time['sigla']}){aviso}")


def tirar_de_campo(partida, time_id, jogador, chave, rodadas):
    """
    Retira de campo um jogador lesionado ou com câimbra.

    Define as rodadas de lesão, tira o jogador de campo, recalcula os setores, narra e anota na súmula como
    lesão (quando rodadas > 0) ou câimbra, e avisa o controle do time para que possa repor o jogador.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time do jogador.
        jogador (dict): Jogador que deixa o campo.
        chave (str): Chave da narração ("lesao" ou "caimbra").
        rodadas (int): Rodadas de afastamento; 0 indica câimbra.
    """
    time = partida["times"][time_id]
    jogador["lesao"] = rodadas
    time["em_campo"].remove(jogador)
    time["saiu"].append(jogador)
    invalidar_setores(partida)
    registrar(partida, chave, {"jogador": rotulo(jogador)}, tipo="lesao", time_id=time_id)
    if rodadas:
        anotar_sumula(partida, f"Lesão — {rotulo(jogador)} ({time['sigla']}), fora por {rodadas} rodada(s)")
    else:
        anotar_sumula(partida, f"Câimbra — {rotulo(jogador)} ({time['sigla']}) deixa o campo")
    partida["controles"][time_id]["lesao"](partida, time_id, jogador)


def sortear_eventos_do_lance(partida):
    """
    Sorteia os eventos aleatórios que podem acontecer antes de um lance.

    Se a torcida já está empurrando, reduz a duração em um lance; senão, com 3% de chance ela passa a empurrar
    o mandante por 3 lances. Para cada time, há 1,2% de chance de um jogador de linha se lesionar (1 a 3
    rodadas) e, se não houver lesão, 8% de chance de um jogador com energia abaixo de 15 sair com câimbra.

    Args:
        partida (dict): Estado da partida.
    """
    if partida["torcida"] > 0:
        partida["torcida"] -= 1
    elif random.random() < 0.03:
        partida["torcida"] = 3
        invalidar_setores(partida)
        registrar(
            partida,
            "torcida",
            {"time": partida["times"][partida["casa"]]["nome"]},
            tipo="evento",
            time_id=partida["casa"],
        )
    for time_id in (partida["casa"], partida["fora"]):
        linha = [jogador for jogador in partida["times"][time_id]["em_campo"] if jogador["pos"] != "GOL"]
        if not linha:
            continue
        if random.random() < 0.012:
            tirar_de_campo(partida, time_id, random.choice(linha), "lesao", random.randint(1, 3))
            continue
        exaustos = [jogador for jogador in linha if jogador["energia"] < 15]
        if exaustos and random.random() < 0.08:
            tirar_de_campo(partida, time_id, random.choice(exaustos), "caimbra", 0)


def disputar_meio(partida):
    """
    Sorteia qual time ganha a disputa de bola no meio-campo.

    A força do meio de cada time é ajustada pela intensidade do plano e recebe 4 pontos extras no estilo
    posse. A diferença entre os times desloca a chance base de 40% de cada lado, limitada entre 12% e 68%; o
    restante é a chance de ninguém ficar com a bola.

    Args:
        partida (dict): Estado da partida.

    Returns:
        str | None: Identificador do time que venceu a disputa, ou None se a bola saiu sem dono.
    """
    valores = {}
    for time_id in (partida["casa"], partida["fora"]):
        plano = partida["times"][time_id]["plano"]
        valor = setores(partida, time_id)["meio"] + (plano["intensidade"] - 3) * 2
        if plano["estilo"] == "posse":
            valor += 4
        valores[time_id] = valor
    diferenca = valores[partida["casa"]] - valores[partida["fora"]]
    chance_casa = limitar(0.40 + diferenca * PESO_MEIO, 0.12, 0.68)
    chance_fora = limitar(0.40 - diferenca * PESO_MEIO, 0.12, 0.68)
    sorteio = random.random()
    if sorteio < chance_casa:
        return partida["casa"]
    if sorteio < chance_casa + chance_fora:
        return partida["fora"]
    return None


def valor_da_acao(portador, acao, drible):
    """
    Calcula o atributo do portador que pesa na ação escolhida.

    Na arrancada e na condução vale o físico; nos demais dribles, a média de finalização, passe e físico; nas
    outras ações, o passe.

    Args:
        portador (dict): Jogador com a bola.
        acao (str): Ação tentada.
        drible (str | None): Tipo de drible, quando a ação é "driblar".

    Returns:
        float: Valor efetivo do atributo usado na ação.
    """
    if acao == "conduzir":
        return atributo_efetivo(portador, "fis")
    if acao == "driblar":
        if drible == "arrancada":
            return atributo_efetivo(portador, "fis")
        return (
            atributo_efetivo(portador, "fin") + atributo_efetivo(portador, "pas") + atributo_efetivo(portador, "fis")
        ) / 3
    return atributo_efetivo(portador, "pas")


def chance_da_acao(partida, atacante_id, zona, faixa, acao, portador, marcador, defesa, bonus, drible=None):
    """
    Calcula a chance de sucesso de uma ação ofensiva.

    Parte da chance base da ação na zona (ou do drible), com penalidade de 0,12 para cruzamento pelo meio.
    Soma a diferença entre o atributo do portador e o desarme do marcador (peso 0,4) e entre o setor de ataque
    e o de defesa (peso 0,6, com os setores de SETOR_DO_ATAQUE e SETOR_DA_DEFESA para cada zona), o bônus
    acumulado, os efeitos da ofensividade dos dois times, da intensidade do
    defensor e da defesa escolhida. Com chuva, passes, lançamentos e cruzamentos perdem 0,06. O resultado fica
    entre 5% e 95%.

    Args:
        partida (dict): Estado da partida.
        atacante_id (str): Time com a posse.
        zona (str): Zona do campo onde está a bola.
        faixa (int): Faixa lateral da bola; 1 é o centro.
        acao (str): Ação tentada pelo portador.
        portador (dict): Jogador com a bola.
        marcador (dict): Jogador que marca o portador.
        defesa (str): Postura defensiva escolhida pelo adversário.
        bonus (float): Bônus acumulado na jogada.
        drible (str | None): Tipo de drible, quando a ação é "driblar". Padrão None.

    Returns:
        float: Probabilidade de sucesso da ação, entre 0.05 e 0.95.
    """
    defensor_id = outro(partida, atacante_id)
    atacante = partida["times"][atacante_id]
    defensor = partida["times"][defensor_id]
    forca_atq = setores(partida, atacante_id)
    forca_def = setores(partida, defensor_id)
    base = DRIBLES[drible]["base"] if acao == "driblar" else CHANCE_BASE[zona][acao]
    if acao == "cruzar" and faixa == 1:
        base -= 0.12
    setor_atq = forca_atq[SETOR_DO_ATAQUE[zona]]
    setor_def = forca_def[SETOR_DA_DEFESA[zona]]
    diferenca = (valor_da_acao(portador, acao, drible) - atributo_efetivo(marcador, "des")) * 0.4 + (
        setor_atq - setor_def
    ) * 0.6
    chance = base + diferenca * PESO_DIFERENCA + bonus
    chance += (atacante["plano"]["ofensividade"] - 3) * 0.02
    chance += (defensor["plano"]["ofensividade"] - 3) * 0.02
    chance -= (defensor["plano"]["intensidade"] - 3) * 0.015
    chance += EFEITO_DEFESA[defesa][zona]
    if partida["chuva"] and acao in ("tocar", "lancar", "cruzar", "enfiar", "abrir", "tabelar"):
        chance -= 0.06
    return limitar(chance, 0.05, 0.95)


def chance_de_falta(plano_defensor, defesa, acao, zona):
    """
    Calcula a chance de o defensor cometer falta no lance.

    Parte de 5%, ajustada pela intensidade do plano defensivo; dar o bote soma 5%, pressão alta soma 3% e
    enfrentar um drible soma 3%. Dentro da área a chance cai pela metade.

    Args:
        plano_defensor (dict): Plano tático do time que defende.
        defesa (str): Postura defensiva escolhida.
        acao (str): Ação tentada pelo atacante.
        zona (str): Zona do campo onde está a bola.

    Returns:
        float: Probabilidade de falta.
    """
    chance = 0.05 + (plano_defensor["intensidade"] - 3) * 0.015
    if defesa == "bote":
        chance += 0.05
    elif defesa == "pressao":
        chance += 0.03
    if acao == "driblar":
        chance += 0.03
    if zona == "area":
        chance *= 0.5
    return chance


def marcar_gol(partida, atacante_id, autor, contra=False):
    """
    Registra um gol para o time atacante.

    Soma o gol, leva a bola para o gol e narra o lance. Gols normais têm 4% de chance de serem anulados pelo
    VAR, desfazendo o placar. Se o gol vale, é anotado na súmula e, quando não é contra, conta para o
    artilheiro.

    Args:
        partida (dict): Estado da partida.
        atacante_id (str): Time que recebe o gol.
        autor (dict): Jogador que fez o gol (do adversário, se for gol contra).
        contra (bool): Se é gol contra. Padrão False.

    Returns:
        bool: True se o gol foi validado, False se foi anulado pelo VAR.
    """
    time = partida["times"][atacante_id]
    time["gols"] += 1
    mover_bola(partida, atacante_id, "gol", 1)
    chave = "gol_contra" if contra else "gol"
    registrar(
        partida,
        chave,
        {"jogador": rotulo(autor), "time": time["nome"], "placar": placar(partida)},
        tipo="gol",
        time_id=atacante_id,
    )
    if not contra and random.random() < 0.04:
        time["gols"] -= 1
        registrar(partida, "var", tipo="var", time_id=atacante_id)
        anotar_sumula(partida, f"Gol anulado pelo VAR — {rotulo(autor)} ({time['sigla']})")
        return False
    if contra:
        anotar_sumula(partida, f"GOL CONTRA — {rotulo(autor)} (a favor do {time['sigla']})")
    else:
        autor["gols"] += 1
        partida["ocorrencias"].append({"tipo": "gol", "time": atacante_id, "jogador": autor["id"]})
        anotar_sumula(partida, f"GOL — {rotulo(autor)} ({time['sigla']})")
    return True


def escolher_chute(partida, atacante_id, finalizador, local):
    """
    Pergunta ao time como o finalizador vai bater na bola.

    Oferece os tipos de chute com seus pesos e a chance de gol de cada um, para as revelações; o chute forte
    ganha peso extra de longe ou do meio-campo e a cavadinha ganha peso extra cara a cara.

    Args:
        partida (dict): Estado da partida.
        atacante_id (str): Time que finaliza.
        finalizador (dict): Jogador que vai chutar.
        local (str): Local da finalização.

    Returns:
        str: Tipo de chute escolhido: "colocado", "forte" ou "cavadinha".
    """
    opcoes = []
    for chave, chute in CHUTES.items():
        peso = chute["peso"]
        if chave == "forte" and local in ("longe", "meio_campo"):
            peso += 2
        if chave == "cavadinha" and local == "cara":
            peso += 2
        opcoes.append((chave, chute["nome"], peso, chance_de_gol(partida, atacante_id, finalizador, local, chave)))
    return perguntar(partida, atacante_id, f"Como {rotulo(finalizador)} vai bater?", opcoes)


def revisar_penalti(partida, atacante_id, chance_revisao=0.2, chance_anular=0.35):
    """
    Decide se o VAR revisa um pênalti marcado e se ele é mantido.

    Com chance_revisao o VAR chama o árbitro; revisado, o pênalti é anulado com chance_anular e confirmado no
    restante dos casos. Cada passo é narrado, e a anulação vai para a súmula.

    Args:
        partida (dict): Estado da partida.
        atacante_id (str): Time a favor de quem o pênalti foi marcado.
        chance_revisao (float): Chance de o VAR revisar o lance. Padrão 0.2.
        chance_anular (float): Chance de o pênalti ser anulado depois da revisão. Padrão 0.35.

    Returns:
        bool: True se o pênalti deve ser cobrado, False se foi anulado.
    """
    if random.random() >= chance_revisao:
        return True
    registrar(partida, "var_penalti", tipo="var", time_id=atacante_id)
    if random.random() < chance_anular:
        registrar(partida, "var_penalti_anulado", tipo="var", time_id=atacante_id)
        anotar_sumula(partida, f"Pênalti anulado pelo VAR ({partida['times'][atacante_id]['sigla']})")
        return False
    registrar(partida, "var_penalti_confirmado", tipo="var", time_id=atacante_id)
    return True


def tentar_bloqueio(partida, atacante_id, finalizador, local):
    """
    Deixa o time que defende escolher como reagir a um chute que vai sair.

    Pergunta ao defensor entre carrinho, fechar o ângulo ou deixar para o goleiro. O carrinho bloqueia com
    32% de chance, ajustada pelo desarme do zagueiro, mas dentro da área pode virar pênalti (8%) e, quando
    falha, deixa o atacante mais livre. Fechar o ângulo bloqueia 15% das vezes e, se não bloquear, atrapalha a
    pontaria. Deixar para o goleiro não muda nada.

    Args:
        partida (dict): Estado da partida.
        atacante_id (str): Time que vai chutar.
        finalizador (dict): Jogador que vai chutar.
        local (str): Local da finalização.

    Returns:
        str: "bloqueado", "penalti", "carrinho_falhou", "fechado" ou "nenhum".
    """
    defensor_id = outro(partida, atacante_id)
    defensor = partida["times"][defensor_id]
    zagueiro = escolher_jogador(defensor, PESOS_MARCADOR["area" if local == "area" else "ataque"])
    chance_carrinho = limitar(0.32 + (atributo_efetivo(zagueiro, "des") - 70) * 0.004, 0.05, 0.9)
    escolha = perguntar(
        partida,
        defensor_id,
        f"{rotulo(finalizador)} prepara o chute! Como o {defensor['nome']} defende?",
        [opcao + (chance,) for opcao, chance in zip(BLOQUEIOS, (chance_carrinho, 0.15, 0.0))],
    )
    dados = {"marcador": rotulo(zagueiro), "jogador": rotulo(finalizador)}
    if escolha == "carrinho":
        if local == "area" and random.random() < 0.08:
            defensor["faltas"] += 1
            registrar(partida, "carrinho_penalti", dados, tipo="falta", time_id=defensor_id)
            cartao_na_falta(partida, defensor_id, zagueiro, 0.4)
            if revisar_penalti(partida, atacante_id):
                cobrar_penalti(partida, atacante_id)
            return "penalti"
        if random.random() < chance_carrinho:
            registrar(partida, "bloqueio_carrinho", dados, tipo="defesa", time_id=atacante_id)
            return "bloqueado"
        registrar(partida, "carrinho_falhou", dados, tipo="lance", time_id=atacante_id)
        return "carrinho_falhou"
    if escolha == "fechar":
        if random.random() < 0.15:
            registrar(partida, "bloqueio", dados, tipo="defesa", time_id=atacante_id)
            return "bloqueado"
        return "fechado"
    return "nenhum"


def probabilidades_do_chute(partida, atacante_id, finalizador, local, tipo, bonus, defesa, fator_desvio=1.0):
    """
    Calcula a chance de um chute ir no alvo e, indo, de virar gol.

    No alvo: base do tipo de chute e do local, mais a finalização (no cabeceio, média com o físico) e metade
    do bônus, com 0,06 a menos contra linha recuada. Gol: compara finalização e reflexo do goleiro, dividindo
    pelo fator do goleiro no tipo de chute (a cavadinha cara a cara engana mais) e pelo desvio, multiplica por
    FATOR_GOL e soma metade do bônus; o estilo jogo direto tira 0,03.

    Args:
        partida (dict): Estado da partida.
        atacante_id (str): Time que finaliza.
        finalizador (dict): Jogador que chuta.
        local (str): Local da finalização, uma das chaves de LOCAIS.
        tipo (str): Tipo de chute.
        bonus (float): Bônus acumulado na jogada.
        defesa (str): Postura defensiva do adversário.
        fator_desvio (float): Multiplicador do fator do goleiro quando a bola desvia. Padrão 1.0.

    Returns:
        tuple: (chance de ir no alvo, chance de gol se for no alvo), ainda sem os limites.
    """
    atacante = partida["times"][atacante_id]
    goleiro = goleiro_de(partida["times"][outro(partida, atacante_id)])
    chute = CHUTES[tipo]
    finalizacao = atributo_efetivo(finalizador, "fin")
    if local == "cabeceio":
        finalizacao = (finalizacao + atributo_efetivo(finalizador, "fis")) / 2
    alvo = chute["alvo"] + LOCAIS[local]["alvo"] + (finalizacao - 65) * 0.004 + bonus * 0.5
    if defesa == "recuar" and local in ("longe", "area", "cara"):
        alvo -= 0.06
    fator_goleiro = (0.45 if tipo == "cavadinha" and local == "cara" else chute["goleiro"]) * fator_desvio
    reflexo = atributo_efetivo(goleiro, "ref") if goleiro else 30
    gol = (LOCAIS[local]["gol"] + (finalizacao - reflexo) * PESO_FINALIZACAO) / fator_goleiro * FATOR_GOL + bonus * 0.5
    if atacante["plano"]["estilo"] == "jogo direto":
        gol -= 0.03
    return alvo, gol


def chance_de_gol(partida, atacante_id, finalizador, local, tipo="colocado", bonus=0.0, defesa="fechar"):
    """
    Calcula a chance de um chute virar gol, já com os limites usados no sorteio.

    Não conta bloqueio, desvio, frango nem bola salva em cima da linha, que são raros. É o número mostrado nas
    revelações.

    Args:
        partida (dict): Estado da partida.
        atacante_id (str): Time que finaliza.
        finalizador (dict): Jogador que chuta.
        local (str): Local da finalização.
        tipo (str): Tipo de chute. Padrão "colocado".
        bonus (float): Bônus acumulado na jogada. Padrão 0.0.
        defesa (str): Postura defensiva do adversário. Padrão "fechar".

    Returns:
        float: Chance de gol, entre 0 e 1.
    """
    alvo, gol = probabilidades_do_chute(partida, atacante_id, finalizador, local, tipo, bonus, defesa)
    return limitar(alvo, 0.1, 0.95) * limitar(gol, 0.03, 0.9)


def chance_media_do_drible(partida, atacante_id, zona, faixa, portador, marcador, defesa, bonus):
    """
    Calcula a chance média de um drible dar certo, ponderando os tipos de drible pelo peso de cada um.

    Args:
        partida (dict): Estado da partida.
        atacante_id (str): Time com a bola.
        zona (str): Zona da jogada.
        faixa (int): Faixa do campo.
        portador (dict): Jogador com a bola.
        marcador (dict): Defensor que marca o lance.
        defesa (str): Postura defensiva do adversário.
        bonus (float): Bônus acumulado na jogada.

    Returns:
        float: Chance média, entre 0 e 1.
    """
    total = sum(dados["peso"] for dados in DRIBLES.values())
    return (
        sum(
            chance_da_acao(partida, atacante_id, zona, faixa, "driblar", portador, marcador, defesa, bonus, chave)
            * dados["peso"]
            for chave, dados in DRIBLES.items()
        )
        / total
    )


def chances_das_acoes(partida, atacante_id, zona, faixa, portador, marcador, defesa, bonus):
    """
    Calcula a chance de cada ação da zona dar certo, para as revelações.

    Para chutar, é a chance de gol de um chute colocado do local da zona; para driblar, a média dos dribles;
    nas demais ações, a chance de a jogada prosseguir.

    Args:
        partida (dict): Estado da partida.
        atacante_id (str): Time com a bola.
        zona (str): Zona da jogada.
        faixa (int): Faixa do campo.
        portador (dict): Jogador com a bola.
        marcador (dict): Defensor que marca o lance.
        defesa (str): Postura defensiva do adversário.
        bonus (float): Bônus acumulado na jogada.

    Returns:
        dict: Chance de cada ação de ACOES[zona], entre 0 e 1.
    """
    chances = {}
    for acao in ACOES[zona]:
        if acao == "chutar":
            chances[acao] = chance_de_gol(
                partida, atacante_id, portador, LOCAL_DO_CHUTE[zona], "colocado", bonus, defesa
            )
        elif acao == "driblar":
            chances[acao] = chance_media_do_drible(partida, atacante_id, zona, faixa, portador, marcador, defesa, bonus)
        else:
            chances[acao] = chance_da_acao(
                partida, atacante_id, zona, faixa, acao, portador, marcador, defesa, bonus, None
            )
    return chances


def finalizar(
    partida, atacante_id, finalizador, local, tipo="colocado", bonus=0.0, defesa="fechar", rebote=True, escanteio=True
):
    """
    Resolve uma finalização ao gol.

    Em chutes de fora, da área ou de primeira, há 35% de chance de a defesa tentar o bloqueio (veja
    tentar_bloqueio). Depois, 6% dos chutes desviam no meio do caminho: quase metade vira escanteio e o resto
    engana o goleiro. Em seguida sorteia se o chute vai no alvo, com base no tipo de chute, no local, na
    finalização do jogador (no cabeceio, média com o físico), no bônus e na linha recuada do adversário. Fora
    do alvo, há 12% de chance de bater na trave, com 40% de chance de rebote. No alvo, a chance de gol compara
    finalização e reflexo do goleiro, ajustada pelo tipo de chute, e cai 0,03 no estilo jogo direto. Um gol
    pode ser salvo em cima da linha (3%) e uma defesa pode virar frango (3%). Se o goleiro defende, pode haver
    rebote (22%) ou escanteio (35%). Atualiza chutes, chutes no alvo e o último local de finalização.

    Args:
        partida (dict): Estado da partida.
        atacante_id (str): Time que finaliza.
        finalizador (dict): Jogador que chuta.
        local (str): Local da finalização, uma das chaves de LOCAIS.
        tipo (str): Tipo de chute. Padrão "colocado".
        bonus (float): Bônus acumulado na jogada. Padrão 0.0.
        defesa (str): Postura defensiva do adversário. Padrão "fechar".
        rebote (bool): Se o lance pode gerar rebote. Padrão True.
        escanteio (bool): Se a defesa do goleiro pode gerar escanteio. Padrão True.
    """
    atacante = partida["times"][atacante_id]
    defensor = partida["times"][outro(partida, atacante_id)]
    goleiro = goleiro_de(defensor)
    chute = CHUTES[tipo]
    partida["ultimo_local"] = local
    mover_bola(partida, atacante_id, ZONA_DO_LOCAL.get(local, "area"))
    atacante["chutes"] += 1
    bloqueio = "nenhum"
    if local in LOCAIS_COM_BLOQUEIO and random.random() < 0.35:
        bloqueio = tentar_bloqueio(partida, atacante_id, finalizador, local)
        if bloqueio == "bloqueado":
            if escanteio and random.random() < 0.4:
                cobrar_escanteio(partida, atacante_id, defesa)
            return
        if bloqueio == "penalti":
            return
    registrar(
        partida,
        f"chute_{local}",
        {"jogador": rotulo(finalizador), "tipo": chute["texto"]},
        tipo="chute",
        time_id=atacante_id,
    )
    ajuste_alvo = {"carrinho_falhou": 0.03, "fechado": -0.05}.get(bloqueio, 0)
    fator_desvio = 1.0
    if random.random() < 0.06:
        if random.random() < 0.45:
            registrar(partida, "desvio_escanteio", {"jogador": rotulo(finalizador)}, tipo="lance", time_id=atacante_id)
            if escanteio:
                cobrar_escanteio(partida, atacante_id, defesa)
            return
        registrar(partida, "desvio", {"jogador": rotulo(finalizador)}, tipo="oportunidade", time_id=atacante_id)
        ajuste_alvo += 0.15
        fator_desvio = 0.6
    alvo, chance = probabilidades_do_chute(partida, atacante_id, finalizador, local, tipo, bonus, defesa, fator_desvio)
    alvo += ajuste_alvo
    if random.random() >= limitar(alvo, 0.1, 0.95):
        if random.random() < 0.12:
            registrar(partida, "trave", {"jogador": rotulo(finalizador)}, tipo="trave", time_id=atacante_id)
            if rebote and random.random() < 0.4:
                pegar_rebote(partida, atacante_id, defesa)
            return
        registrar(partida, "fora", {"jogador": rotulo(finalizador)}, tipo="fora", time_id=atacante_id)
        return
    atacante["no_alvo"] += 1
    nome_goleiro = rotulo(goleiro) if goleiro else "o zagueiro improvisado"
    if random.random() < limitar(chance, 0.03, 0.9):
        if random.random() < 0.03:
            salvador = escolher_jogador(defensor, {"DEF": 6, "MEI": 1})
            registrar(partida, "salva_na_linha", {"marcador": rotulo(salvador)}, tipo="defesa", time_id=atacante_id)
            if escanteio and random.random() < 0.5:
                cobrar_escanteio(partida, atacante_id, defesa)
            return
        marcar_gol(partida, atacante_id, finalizador)
        return
    if goleiro and random.random() < 0.03:
        registrar(partida, "frango", {"goleiro": nome_goleiro}, tipo="oportunidade", time_id=atacante_id)
        marcar_gol(partida, atacante_id, finalizador)
        return
    registrar(partida, "defesa", {"goleiro": nome_goleiro}, tipo="defesa", time_id=atacante_id)
    if rebote and random.random() < 0.22:
        pegar_rebote(partida, atacante_id, defesa)
    elif escanteio and random.random() < 0.35:
        cobrar_escanteio(partida, atacante_id, defesa)


def pegar_rebote(partida, atacante_id, defesa):
    """
    Resolve a sobra de bola após uma finalização.

    Sorteia quem pega o rebote e pergunta se ele chuta de primeira (chute forte do local de rebote) ou ajeita
    antes; ao ajeitar, há 45% de chance de a bola ser bloqueada, senão sai um chute colocado da área. Nenhum
    dos chutes pode gerar novo rebote.

    Args:
        partida (dict): Estado da partida.
        atacante_id (str): Time que pega o rebote.
        defesa (str): Postura defensiva do adversário.
    """
    time = partida["times"][atacante_id]
    jogador = escolher_jogador(time, PESOS_REBOTE)
    entregar_bola(partida, atacante_id, "area", 1, jogador)
    registrar(partida, "rebote", {"jogador": rotulo(jogador)}, tipo="oportunidade", time_id=atacante_id)
    escolha = perguntar(
        partida,
        atacante_id,
        f"Rebote! {rotulo(jogador)} pega a sobra. E agora?",
        [
            (
                "primeira",
                "Chutar de primeira",
                5,
                chance_de_gol(partida, atacante_id, jogador, "rebote", "forte", 0, defesa),
            ),
            (
                "ajeitar",
                "Ajeitar e bater",
                3,
                0.55 * chance_de_gol(partida, atacante_id, jogador, "area", "colocado", 0, defesa),
            ),
        ],
    )
    if escolha == "primeira":
        finalizar(partida, atacante_id, jogador, "rebote", "forte", defesa=defesa, rebote=False)
    elif random.random() < 0.45:
        registrar(partida, "rebote_bloqueado", {"jogador": rotulo(jogador)}, tipo="perda", time_id=atacante_id)
    else:
        finalizar(partida, atacante_id, jogador, "area", "colocado", defesa=defesa, rebote=False)


def cobrar_escanteio(partida, atacante_id, defesa):
    """
    Resolve a cobrança de um escanteio.

    O melhor batedor cobra; há 0,4% de chance de gol olímpico. Na cobrança curta, há 60% de chance de um
    companheiro chutar de longe. Na primeira trave (45%) ou na segunda (38%, com bônus de 0,05), um jogador
    cabeceia. Fechado no goleiro, a bola pode entrar direto (2,5%), o goleiro pode socar para um rebote
    (42,5%) ou segurar. Na jogada ensaiada, metade das vezes um meia chega livre para bater da área. Nos
    demais casos a defesa afasta. Nenhuma finalização daqui gera novo escanteio.

    Args:
        partida (dict): Estado da partida.
        atacante_id (str): Time que cobra o escanteio.
        defesa (str): Postura defensiva do adversário.
    """
    time = partida["times"][atacante_id]
    batedor = melhor_batedor(time)
    mover_bola(partida, atacante_id, "area", random.choice((0, 2)))
    registrar(partida, "escanteio", {"time": time["nome"]}, tipo="bola_parada", time_id=atacante_id)
    if random.random() < 0.004:
        partida["ultimo_local"] = "olimpico"
        registrar(partida, "gol_olimpico", {"jogador": rotulo(batedor)}, tipo="oportunidade", time_id=atacante_id)
        marcar_gol(partida, atacante_id, batedor)
        return
    escolha = perguntar(
        partida,
        atacante_id,
        "Escanteio! Como cobrar?",
        [
            ("primeira", "Na primeira trave", 3, 0.45),
            ("segunda", "Na segunda trave", 3, 0.38),
            ("curto", "Cobrança curta", 2, 0.6),
            ("fechado", "Fechado, no goleiro", 1, 0.45),
            ("ensaiada", "Jogada ensaiada", 2, 0.5),
        ],
    )
    if escolha == "fechado":
        sorteio = random.random()
        if sorteio < 0.025:
            registrar(
                partida, "escanteio_direto", {"jogador": rotulo(batedor)}, tipo="oportunidade", time_id=atacante_id
            )
            partida["ultimo_local"] = "olimpico"
            marcar_gol(partida, atacante_id, batedor)
        elif sorteio < 0.45:
            registrar(partida, "goleiro_soca", tipo="defesa", time_id=atacante_id)
            pegar_rebote(partida, atacante_id, defesa)
        else:
            registrar(partida, "goleiro_segura_escanteio", tipo="defesa", time_id=atacante_id)
        return
    if escolha == "ensaiada":
        if random.random() < 0.5:
            jogador = escolher_jogador(time, {"MEI": 5, "ATA": 3}, excluir=batedor)
            registrar(partida, "escanteio_ensaiado", {"jogador": rotulo(jogador)}, time_id=atacante_id)
            finalizar(partida, atacante_id, jogador, "area", "colocado", 0.04, defesa, escanteio=False)
        else:
            registrar(partida, "escanteio_ensaiado_erro", tipo="perda", time_id=atacante_id)
        return
    if escolha == "curto":
        if random.random() < 0.6:
            jogador = escolher_jogador(time, PESOS_PORTADOR["ataque"], excluir=batedor)
            registrar(partida, "escanteio_curto", {"jogador": rotulo(jogador)}, time_id=atacante_id)
            finalizar(
                partida,
                atacante_id,
                jogador,
                "longe",
                escolher_chute(partida, atacante_id, jogador, "longe"),
                defesa=defesa,
                escanteio=False,
            )
            return
    elif random.random() < (0.45 if escolha == "primeira" else 0.38):
        bonus = 0.05 if escolha == "segunda" else 0.0
        finalizar(
            partida,
            atacante_id,
            escolher_jogador(time, PESOS_CABECEIO, excluir=batedor),
            "escanteio",
            bonus=bonus,
            defesa=defesa,
            escanteio=False,
        )
        return
    registrar(partida, "escanteio_afastado", tipo="perda", time_id=atacante_id)


def cobrar_falta(partida, atacante_id, defesa):
    """
    Resolve a cobrança de uma falta perigosa na entrada da área.

    O melhor batedor pode bater por cima da barreira (chute colocado), rasteiro (20% de chance de parar na
    barreira, senão chute colocado com bônus de 0,03), forte no canto, cruzar na área ou rolar para um
    companheiro bater de primeira.

    Args:
        partida (dict): Estado da partida.
        atacante_id (str): Time que cobra a falta.
        defesa (str): Postura defensiva do adversário.
    """
    time = partida["times"][atacante_id]
    batedor = melhor_batedor(time)
    referencia = atacante_de_referencia(time, batedor)
    mover_bola(partida, atacante_id, "ataque", 1)
    registrar(partida, "falta_perigosa", {"time": time["nome"]}, tipo="bola_parada", time_id=atacante_id)
    escolha = perguntar(
        partida,
        atacante_id,
        f"Falta perigosa! {rotulo(batedor)} na bola. Como cobrar?",
        [
            (
                "barreira",
                "Por cima da barreira",
                4,
                chance_de_gol(partida, atacante_id, batedor, "falta", "colocado", 0, defesa),
            ),
            (
                "rasteiro",
                "Rasteiro, por baixo",
                2,
                0.8 * chance_de_gol(partida, atacante_id, batedor, "falta", "colocado", 0.03, defesa),
            ),
            ("forte", "Bomba no canto", 2, chance_de_gol(partida, atacante_id, batedor, "falta", "forte", 0, defesa)),
            (
                "cruzar",
                "Cruzar na área",
                3,
                chance_de_gol(partida, atacante_id, referencia, "cabeceio", "colocado", 0, defesa),
            ),
            (
                "rolar",
                "Rolar para um companheiro bater",
                2,
                chance_de_gol(partida, atacante_id, referencia, "primeira", "forte", 0.03, defesa),
            ),
        ],
    )
    if escolha == "cruzar":
        cruzamento(partida, atacante_id, batedor, 0.0, defesa)
        return
    if escolha == "rolar":
        companheiro = escolher_jogador(time, PESOS_REBOTE, excluir=batedor)
        registrar(
            partida,
            "falta_rolada",
            {"jogador": rotulo(batedor), "companheiro": rotulo(companheiro)},
            time_id=atacante_id,
        )
        finalizar(partida, atacante_id, companheiro, "primeira", "forte", 0.03, defesa)
        return
    if escolha == "rasteiro" and random.random() < 0.2:
        registrar(partida, "barreira", tipo="defesa", time_id=atacante_id)
        return
    tipo = "forte" if escolha == "forte" else "colocado"
    bonus = 0.03 if escolha == "rasteiro" else 0.0
    finalizar(partida, atacante_id, batedor, "falta", tipo, bonus, defesa)


def resolver_cobranca(partida, atacante_id, batedor, goleiro, minijogo=True):
    """
    Decide o desfecho de uma cobrança de pênalti.

    O controle do atacante escolhe canto e força, e o do defensor escolhe o canto do pulo; a escolha fica
    salva em "ultimo_penalti". O chute vai para fora com 4% (colocado), 14% (forte) ou 6% (paradinha) de
    chance, mais um acréscimo se a finalização for menor que 70. Na paradinha, o goleiro espera sem pular em
    25% das vezes e vai no canto certo. Se o goleiro acerta o canto, defende com 80% no meio, 55% no colocado,
    30% no forte ou 50% na paradinha, ajustado pela diferença entre reflexo e finalização e limitado entre 10%
    e 90%.

    Args:
        partida (dict): Estado da partida.
        atacante_id (str): Time que cobra.
        batedor (dict): Jogador que bate o pênalti.
        goleiro (dict | None): Goleiro adversário, ou None se não houver goleiro em campo.
        minijogo (bool): Se o goleiro humano faz o minijogo de reflexo, que soma 0,15 à chance de defesa
            quando ele acerta o canto. Padrão True; a disputa de pênaltis passa False.

    Returns:
        str: Desfecho da cobrança: "fora", "defesa" ou "gol".
    """
    defensor_id = outro(partida, atacante_id)
    canto, forca = partida["controles"][atacante_id]["bater_penalti"](partida, atacante_id, batedor, goleiro)
    pulo = partida["controles"][defensor_id]["defender_penalti"](partida, defensor_id, batedor, goleiro)
    esperou = forca == "paradinha" and random.random() < 0.25
    if esperou:
        pulo = canto
    partida["ultimo_penalti"] = {"time": atacante_id, "canto": canto, "forca": forca, "pulo": pulo, "esperou": esperou}
    finalizacao = atributo_efetivo(batedor, "fin")
    chance_fora = {"colocado": 0.04, "forte": 0.14, "paradinha": 0.06}.get(forca, 0.04)
    chance_fora += max(0, 70 - finalizacao) * 0.002
    if random.random() < chance_fora:
        return "fora"
    if canto == pulo:
        defende = 0.80 if canto == "meio" else {"colocado": 0.55, "forte": 0.30, "paradinha": 0.50}.get(forca, 0.55)
        reflexo = atributo_efetivo(goleiro, "ref") if goleiro else 30
        defende += (reflexo - finalizacao) * 0.004
        if minijogo:
            defende += partida["controles"][defensor_id]["minijogo"](partida, defensor_id, "goleiro", None)
        if random.random() < limitar(defende, 0.1, 0.9):
            return "defesa"
    return "gol"


def cobrar_penalti(partida, atacante_id):
    """
    Executa um pênalti marcado durante o jogo.

    O melhor batedor cobra contra o goleiro adversário. Conta o chute e, conforme o desfecho, registra o
    pênalti perdido, defendido ou convertido, atualizando gols do time e do batedor, narração e súmula.

    Args:
        partida (dict): Estado da partida.
        atacante_id (str): Time que cobra o pênalti.
    """
    defensor_id = outro(partida, atacante_id)
    atacante = partida["times"][atacante_id]
    goleiro = goleiro_de(partida["times"][defensor_id])
    batedor = melhor_batedor(atacante)
    entregar_bola(partida, atacante_id, "area", 1, batedor)
    registrar(
        partida, "penalti", {"time": atacante["nome"], "jogador": rotulo(batedor)}, tipo="penalti", time_id=atacante_id
    )
    partida["ultimo_local"] = "penalti"
    desfecho = resolver_cobranca(partida, atacante_id, batedor, goleiro)
    atacante["chutes"] += 1
    cobranca = partida["ultimo_penalti"]
    if cobranca["forca"] == "paradinha":
        chave = "paradinha_esperou" if cobranca["esperou"] else "paradinha"
        nome = rotulo(goleiro) if goleiro else "o goleiro"
        registrar(partida, chave, {"jogador": rotulo(batedor), "goleiro": nome}, tipo="lance", time_id=atacante_id)
    if desfecho != "gol":
        partida["ocorrencias"].append({"tipo": "penalti_perdido", "time": atacante_id, "jogador": batedor["id"]})
    if desfecho == "fora":
        registrar(partida, "penalti_fora", {"jogador": rotulo(batedor)}, tipo="penalti_fim", time_id=atacante_id)
        anotar_sumula(partida, f"Pênalti perdido — {rotulo(batedor)} ({atacante['sigla']})")
        return
    atacante["no_alvo"] += 1
    if desfecho == "defesa":
        nome_goleiro = rotulo(goleiro) if goleiro else "o goleiro improvisado"
        registrar(partida, "penalti_defesa", {"goleiro": nome_goleiro}, tipo="penalti_fim", time_id=atacante_id)
        anotar_sumula(partida, f"Pênalti defendido — {nome_goleiro}")
        return
    atacante["gols"] += 1
    batedor["gols"] += 1
    partida["ocorrencias"].append({"tipo": "gol", "time": atacante_id, "jogador": batedor["id"]})
    mover_bola(partida, atacante_id, "gol", 1)
    registrar(
        partida, "penalti_gol", {"jogador": rotulo(batedor), "placar": placar(partida)}, tipo="gol", time_id=atacante_id
    )
    anotar_sumula(partida, f"GOL (pênalti) — {rotulo(batedor)} ({atacante['sigla']})")


def cartao_na_falta(partida, defensor_id, marcador, chance_amarelo):
    """
    Sorteia o cartão aplicado ao autor de uma falta.

    Com 2,5% de chance o jogador recebe vermelho direto; se o sorteio ficar abaixo de chance_amarelo, recebe
    amarelo. Como o mesmo sorteio é usado, a chance real de amarelo é chance_amarelo menos 2,5%.

    Args:
        partida (dict): Estado da partida.
        defensor_id (str): Time que cometeu a falta.
        marcador (dict): Jogador que cometeu a falta.
        chance_amarelo (float): Limite do sorteio para o amarelo.
    """
    sorteio = random.random()
    if sorteio < 0.025:
        expulsar(partida, defensor_id, marcador, "vermelho")
    elif sorteio < chance_amarelo:
        amarelar(partida, defensor_id, marcador)


def cometer_falta(partida, atacante_id, zona, portador, marcador, defesa):
    """
    Registra uma falta do marcador sobre o portador da bola.

    Soma a falta ao time defensor, narra o lance e sorteia o cartão, com chance de amarelo de 22% (30% se a
    defesa deu o bote). O tipo de falta depende da zona onde ocorreu.

    Args:
        partida (dict): Estado da partida.
        atacante_id (str): Time que sofreu a falta.
        zona (str): Zona do campo onde ocorreu a falta.
        portador (dict): Jogador que sofreu a falta.
        marcador (dict): Jogador que cometeu a falta.
        defesa (str): Postura defensiva do adversário.

    Returns:
        str: "penalti" se foi na área, "perigosa" se foi na entrada da área ou "meio" se foi no meio-campo.
    """
    defensor_id = outro(partida, atacante_id)
    partida["times"][defensor_id]["faltas"] += 1
    registrar(
        partida, "falta", {"marcador": rotulo(marcador), "jogador": rotulo(portador)}, tipo="falta", time_id=defensor_id
    )
    cartao_na_falta(partida, defensor_id, marcador, 0.22 + (0.08 if defesa == "bote" else 0))
    if zona == "area":
        return "penalti"
    if zona == "ataque":
        return "perigosa"
    return "meio"


def falta_tatica(partida, atacante_id, zona, portador, defesa):
    """
    Executa a falta tática escolhida pela defesa para parar a jogada.

    Sorteia o marcador que faz a falta, soma a falta ao time defensor, narra o lance e sorteia o cartão com
    chance de amarelo de 45%. Se a falta foi na entrada da área, o atacante cobra uma falta perigosa.

    Args:
        partida (dict): Estado da partida.
        atacante_id (str): Time que sofreu a falta.
        zona (str): Zona do campo onde ocorreu a falta.
        portador (dict): Jogador que sofreu a falta.
        defesa (str): Postura defensiva do adversário.
    """
    defensor_id = outro(partida, atacante_id)
    marcador = escolher_jogador(partida["times"][defensor_id], PESOS_MARCADOR[zona])
    partida["times"][defensor_id]["faltas"] += 1
    registrar(
        partida,
        "falta_tatica",
        {"marcador": rotulo(marcador), "jogador": rotulo(portador)},
        tipo="falta",
        time_id=defensor_id,
    )
    cartao_na_falta(partida, defensor_id, marcador, 0.45)
    if zona in ("ataque", "linha_de_fundo"):
        cobrar_falta(partida, atacante_id, defesa)


def chance_drible_goleiro(jogador, goleiro, bonus):
    """
    Calcula a chance de o atacante driblar o goleiro no cara a cara.

    Parte de 50% e soma a diferença entre a técnica do atacante (média de finalização e físico) e o reflexo do
    goleiro (peso 0,005), mais o bônus, ficando entre 15% e 85%.

    Args:
        jogador (dict): Atacante cara a cara.
        goleiro (dict | None): Goleiro adversário, ou None se não houver.
        bonus (float): Bônus acumulado na jogada, já com o efeito da escolha do goleiro.

    Returns:
        float: Chance de o drible dar certo.
    """
    reflexo = atributo_efetivo(goleiro, "ref") if goleiro else 30
    tecnica = (atributo_efetivo(jogador, "fin") + atributo_efetivo(jogador, "fis")) / 2
    return limitar(0.5 + (tecnica - reflexo) * 0.005 + bonus, 0.15, 0.85)


def cara_a_cara(partida, atacante_id, jogador, bonus, defesa):
    """
    Resolve um lance em que o atacante fica cara a cara com o goleiro.

    O time escolhe tocar no canto, encher o pé, cavadinha ou driblar o goleiro, e o time que defende escolhe
    o que o goleiro faz: sair abafando, esperar no gol ou fechar o ângulo. Cada combinação muda a chance como
    em EFEITO_GOLEIRO (a cavadinha, por exemplo, é ótima contra o goleiro que sai e péssima contra o que
    espera). Os três primeiros viram uma finalização do local "cara". No drible, a chance parte de 50%,
    ajustada pela diferença entre a técnica do jogador (média de finalização e físico) e o reflexo do goleiro,
    mais o bônus e o efeito da escolha do goleiro, entre 15% e 85%; se der certo, o gol é marcado com o gol
    vazio, senão o goleiro salva.

    Args:
        partida (dict): Estado da partida.
        atacante_id (str): Time que ataca.
        jogador (dict): Jogador cara a cara com o goleiro.
        bonus (float): Bônus acumulado na jogada.
        defesa (str): Postura defensiva do adversário.
    """
    defensor = partida["times"][outro(partida, atacante_id)]
    goleiro = goleiro_de(defensor)
    entregar_bola(partida, atacante_id, "area", 1, jogador)
    registrar(partida, "cara", {"jogador": rotulo(jogador)}, tipo="oportunidade", time_id=atacante_id)
    escolha = perguntar(
        partida,
        atacante_id,
        f"{rotulo(jogador)} está cara a cara com o goleiro!",
        [
            (
                "colocado",
                "Tocar no canto",
                4,
                chance_de_gol(partida, atacante_id, jogador, "cara", "colocado", bonus, defesa),
            ),
            ("forte", "Encher o pé", 3, chance_de_gol(partida, atacante_id, jogador, "cara", "forte", bonus, defesa)),
            (
                "cavadinha",
                "Cavadinha",
                2,
                chance_de_gol(partida, atacante_id, jogador, "cara", "cavadinha", bonus, defesa),
            ),
            ("driblar", "Driblar o goleiro", 2, chance_drible_goleiro(jogador, goleiro, bonus)),
        ],
    )
    nome_goleiro = rotulo(goleiro) if goleiro else "o zagueiro"
    postura = "esperar"
    if goleiro:
        defensor_id = outro(partida, atacante_id)
        postura = perguntar(
            partida,
            defensor_id,
            f"{rotulo(jogador)} vem cara a cara! O que {nome_goleiro} faz?",
            list(GOLEIRO_NO_CARA_A_CARA),
        )
        registrar(partida, f"goleiro_{postura}", {"goleiro": nome_goleiro}, tipo="lance", time_id=defensor_id)
    efeito = EFEITO_GOLEIRO[escolha][postura]
    if escolha != "driblar":
        finalizar(partida, atacante_id, jogador, "cara", escolha, bonus + efeito, defesa)
        return
    if random.random() < chance_drible_goleiro(jogador, goleiro, bonus + efeito):
        registrar(partida, "driblou_goleiro", {"jogador": rotulo(jogador)}, time_id=atacante_id)
        partida["times"][atacante_id]["chutes"] += 1
        partida["times"][atacante_id]["no_alvo"] += 1
        partida["ultimo_local"] = "gol_vazio"
        marcar_gol(partida, atacante_id, jogador)
        return
    registrar(
        partida,
        "goleiro_salva",
        {"goleiro": nome_goleiro, "jogador": rotulo(jogador)},
        tipo="defesa",
        time_id=atacante_id,
    )


def cruzamento(partida, atacante_id, cruzador, bonus, defesa):
    """
    Resolve a chegada de um cruzamento na área.

    Sorteia o receptor, dando preferência aos atacantes, e pergunta se ele cabeceia, bate de voleio (chute
    forte), domina e chuta, escora para um companheiro ou tenta de bicicleta. Ao dominar, há 40% de chance de
    perder a bola; senão o time escolhe o tipo de chute da área. A escorada chega ao companheiro em 55% das
    vezes, que bate livre da área. A bicicleta raramente vai no gol, mas quando vai é difícil de defender.

    Args:
        partida (dict): Estado da partida.
        atacante_id (str): Time que cruzou.
        cruzador (dict): Jogador que fez o cruzamento; não pode ser o receptor.
        bonus (float): Bônus acumulado na jogada.
        defesa (str): Postura defensiva do adversário.
    """
    time = partida["times"][atacante_id]
    receptor = escolher_jogador(time, PESOS_CABECEIO, excluir=cruzador)
    entregar_bola(partida, atacante_id, "area", 1, receptor)
    escolha = perguntar(
        partida,
        atacante_id,
        f"A bola vem na área para {rotulo(receptor)}!",
        [
            (
                "cabecear",
                "Cabecear",
                5,
                chance_de_gol(partida, atacante_id, receptor, "cabeceio", "colocado", bonus, defesa),
            ),
            (
                "voleio",
                "Bater de voleio",
                2,
                chance_de_gol(partida, atacante_id, receptor, "voleio", "forte", bonus, defesa),
            ),
            (
                "dominar",
                "Dominar e chutar",
                3,
                0.6 * chance_de_gol(partida, atacante_id, receptor, "area", "colocado", bonus, defesa),
            ),
            (
                "escorar",
                "Escorar para um companheiro",
                2,
                0.55 * chance_de_gol(partida, atacante_id, receptor, "area", "colocado", bonus + 0.06, defesa),
            ),
            (
                "bicicleta",
                "Tentar de bicicleta",
                1,
                chance_de_gol(partida, atacante_id, receptor, "bicicleta", "forte", bonus, defesa),
            ),
        ],
    )
    if escolha == "cabecear":
        ajuste = partida["controles"][atacante_id]["minijogo"](partida, atacante_id, "cabeceio", None)
        finalizar(partida, atacante_id, receptor, "cabeceio", bonus=bonus + ajuste, defesa=defesa)
    elif escolha == "voleio":
        finalizar(partida, atacante_id, receptor, "voleio", "forte", bonus, defesa)
    elif escolha == "bicicleta":
        finalizar(partida, atacante_id, receptor, "bicicleta", "forte", bonus, defesa)
    elif escolha == "escorar":
        if random.random() < 0.55:
            companheiro = escolher_jogador(time, PESOS_REBOTE, excluir=receptor)
            registrar(
                partida,
                "escora",
                {"jogador": rotulo(receptor), "companheiro": rotulo(companheiro)},
                time_id=atacante_id,
            )
            finalizar(partida, atacante_id, companheiro, "area", "colocado", bonus + 0.06, defesa)
        else:
            registrar(partida, "escora_erro", {"jogador": rotulo(receptor)}, tipo="perda", time_id=atacante_id)
    elif random.random() < 0.4:
        registrar(partida, "dominar_erro", {"jogador": rotulo(receptor)}, tipo="perda", time_id=atacante_id)
    else:
        finalizar(
            partida,
            atacante_id,
            receptor,
            "area",
            escolher_chute(partida, atacante_id, receptor, "area"),
            bonus,
            defesa,
        )


def oportunidade_do_meio(partida, atacante_id, portador, defesa):
    """
    Oferece ao portador a chance de chutar do meio-campo com o goleiro adiantado.

    Narra o goleiro adiantado e pergunta se o portador arrisca o chute forte do meio-campo, sem possibilidade
    de rebote, ou segue a jogada.

    Args:
        partida (dict): Estado da partida.
        atacante_id (str): Time com a posse.
        portador (dict): Jogador com a bola.
        defesa (str): Postura defensiva do adversário.

    Returns:
        bool: True se o portador chutou do meio-campo, False se seguiu a jogada.
    """
    goleiro = goleiro_de(partida["times"][outro(partida, atacante_id)])
    nome_goleiro = rotulo(goleiro) if goleiro else "O goleiro"
    registrar(partida, "goleiro_adiantado", {"goleiro": nome_goleiro}, tipo="oportunidade", time_id=atacante_id)
    escolha = perguntar(
        partida,
        atacante_id,
        f"{nome_goleiro} está adiantado! {rotulo(portador)} arrisca do meio-campo?",
        [
            (
                "arriscar",
                "Chutar do meio-campo",
                1,
                chance_de_gol(partida, atacante_id, portador, "meio_campo", "forte", 0, defesa),
            ),
            ("seguir", "Seguir a jogada", 4, 1.0),
        ],
    )
    if escolha == "arriscar":
        finalizar(partida, atacante_id, portador, "meio_campo", "forte", defesa=defesa, rebote=False)
        return True
    return False


def lance_de_simulacao(partida, atacante_id, portador, marcador):
    """
    Resolve o lance em que o atacante cai na área depois de perder o drible.

    Em 70% das vezes o árbitro vê a simulação e dá amarelo ao atacante. Nas outras, marca pênalti, que tem
    60% de chance de ir para o VAR e, revisado, 60% de chance de ser anulado.

    Args:
        partida (dict): Estado da partida.
        atacante_id (str): Time do jogador que caiu.
        portador (dict): Jogador que caiu na área.
        marcador (dict): Defensor envolvido no lance.
    """
    dados = {"jogador": rotulo(portador), "marcador": rotulo(marcador)}
    registrar(partida, "simulacao", dados, tipo="falta", time_id=atacante_id)
    if random.random() < 0.7:
        registrar(partida, "simulacao_amarelo", dados, tipo="falta", time_id=atacante_id)
        amarelar(partida, atacante_id, portador)
        return
    registrar(partida, "simulacao_penalti", dados, tipo="falta", time_id=atacante_id)
    if revisar_penalti(partida, atacante_id, chance_revisao=0.6, chance_anular=0.6):
        cobrar_penalti(partida, atacante_id)


def jogar_posse(partida, atacante_id, contra_ataque=False, portador=None, zona_inicial=None):
    """
    Simula uma posse de bola completa do time atacante.

    A posse começa no meio-campo, na zona_inicial pedida (campo de defesa, meio ou intermediária, por
    exemplo), ou já no ataque em contra-ataque (bônus de 0,08) e, no estilo jogo direto, com 40% de chance
    (bônus de -0,03). O adversário escolhe a postura defensiva; a falta tática fora da área encerra a posse na
    hora. Em até PASSOS_DA_POSSE (8) passos, o time escolhe uma ação da zona onde está a bola (campo de
    defesa, meio, intermediária, entrada da área, linha de fundo ou área); antes de cada escolha, a chance de
    cada ação fica em partida["chances"] para as revelações. No último passo, toca nas zonas de trás ou chuta
    nas da frente. A ação pode virar falta, finalização, avanço de zona, troca de portador ou perda da bola;
    perder a bola no campo de defesa dá contra-ataque ao adversário em 35% das vezes. Na perda, pode haver
    escanteio, gol contra no cruzamento ou recuperação do adversário, que puxa um contra-ataque se jogar nesse
    estilo contra um time ofensivo (50%), com 10% de chance geral ou com 25% de chance quando a pressão alta
    rouba no meio-campo ou no campo de defesa. Pênaltis podem ser revisados pelo VAR; um drible errado na área
    pode virar simulação; e uma enfiada em impedimento às vezes passa batida pelo bandeira. Se os passos
    acabarem sem finalização nem perda, a narração diz que o time rodou a bola sem achar espaço e a posse
    termina.

    Args:
        partida (dict): Estado da partida.
        atacante_id (str): Time com a posse.
        contra_ataque (bool): Se a posse nasce de um contra-ataque. Padrão False.
        portador (dict | None): Jogador que começa com a bola; se não estiver em campo, outro é sorteado.
            Padrão None.
        zona_inicial (str | None): Zona onde a posse começa, usada pelas jogadas especiais. Padrão None.

    Returns:
        tuple | None: (defensor_id, marcador) quando a posse termina em contra-ataque do adversário, senão
            None.
    """
    defensor_id = outro(partida, atacante_id)
    atacante = partida["times"][atacante_id]
    defensor = partida["times"][defensor_id]
    controles = partida["controles"]
    atacante["posse"] += 1
    zona = "meio"
    faixa = random.randint(0, 2)
    bonus = 0.0
    if contra_ataque:
        zona = "ataque"
        bonus = 0.08
    elif zona_inicial:
        zona = zona_inicial
    elif atacante["plano"]["estilo"] == "jogo direto" and random.random() < 0.40:
        zona = "ataque"
        bonus = -0.03
    if portador not in atacante["em_campo"]:
        portador = escolher_jogador(atacante, PESOS_PORTADOR[zona])
    entregar_bola(partida, atacante_id, zona, faixa, portador)
    defesa = controles[defensor_id]["defesa"](partida, defensor_id)
    if defesa not in DEFESAS:
        defesa = "fechar"
    if defesa == "falta" and zona != "area":
        falta_tatica(partida, atacante_id, zona, portador, defesa)
        return None
    trocar_portador = False
    for passo in range(PASSOS_DA_POSSE):
        if trocar_portador:
            portador = escolher_jogador(atacante, PESOS_PORTADOR[zona], excluir=portador)
        entregar_bola(partida, atacante_id, zona, faixa, portador)
        trocar_portador = False
        if contra_ataque and passo == 0:
            registrar(
                partida, "contra_ataque", {"time": atacante["nome"], "jogador": rotulo(portador)}, time_id=atacante_id
            )
        if zona == "meio" and random.random() < 0.025 and oportunidade_do_meio(partida, atacante_id, portador, defesa):
            return None
        marcador = escolher_jogador(defensor, PESOS_MARCADOR[zona])
        if passo == PASSOS_DA_POSSE - 1:
            acao = "chutar" if zona in LOCAL_DO_CHUTE else "tocar"
        else:
            partida["chances"] = chances_das_acoes(partida, atacante_id, zona, faixa, portador, marcador, defesa, bonus)
            acao = controles[atacante_id]["ataque"](partida, atacante_id, zona, portador)
            partida["chances"] = None
        if acao not in ACOES[zona]:
            acao = ACOES[zona][0]
        if acao == "chutar":
            local = LOCAL_DO_CHUTE[zona]
            finalizar(
                partida,
                atacante_id,
                portador,
                local,
                escolher_chute(partida, atacante_id, portador, local),
                bonus,
                defesa,
            )
            return None
        if random.random() < chance_de_falta(defensor["plano"], defesa, acao, zona):
            desfecho = cometer_falta(partida, atacante_id, zona, portador, marcador, defesa)
            if desfecho == "penalti":
                if revisar_penalti(partida, atacante_id):
                    cobrar_penalti(partida, atacante_id)
                return None
            if desfecho == "perigosa":
                cobrar_falta(partida, atacante_id, defesa)
                return None
            continue
        drible = None
        if acao == "driblar":
            drible = perguntar(
                partida,
                atacante_id,
                f"Que drible {rotulo(portador)} vai tentar?",
                [
                    (
                        chave,
                        dados_drible["nome"],
                        dados_drible["peso"],
                        chance_da_acao(
                            partida, atacante_id, zona, faixa, "driblar", portador, marcador, defesa, bonus, chave
                        ),
                    )
                    for chave, dados_drible in DRIBLES.items()
                ],
            )
        dados = {"jogador": rotulo(portador), "marcador": rotulo(marcador), "time": atacante["nome"]}
        ajuste = controles[atacante_id]["minijogo"](partida, atacante_id, "drible", drible) if drible else 0.0
        if random.random() < chance_da_acao(
            partida, atacante_id, zona, faixa, acao, portador, marcador, defesa, bonus + ajuste, drible
        ):
            if defesa == "pressao" and zona in ("defesa", "meio"):
                bonus += 0.06
            if acao == "driblar":
                registrar(partida, f"drible_{drible}_ok", dados, time_id=atacante_id)
                bonus += DRIBLES[drible]["bonus"]
                if zona == "area":
                    cara_a_cara(partida, atacante_id, portador, bonus, defesa)
                    return None
                zona = PROXIMA_ZONA[zona]
                continue
            registrar(partida, f"{acao}_ok", dados, time_id=atacante_id)
            if acao == "cruzar":
                extra = (0.04 if faixa != 1 else 0.0) + (0.04 if zona == "linha_de_fundo" else 0.0)
                cruzamento(partida, atacante_id, portador, bonus + extra, defesa)
                return None
            if acao == "rasteiro":
                companheiro = escolher_jogador(atacante, PESOS_REBOTE, excluir=portador)
                entregar_bola(partida, atacante_id, "area", 1, companheiro)
                finalizar(partida, atacante_id, companheiro, "area", "colocado", bonus + 0.08, defesa)
                return None
            if acao == "conduzir":
                zona = PROXIMA_ZONA[zona]
                bonus += 0.02
                continue
            if acao == "enfiar":
                recebedor = escolher_jogador(atacante, {"ATA": 6, "MEI": 2}, excluir=portador)
                if random.random() < 0.4:
                    cara_a_cara(partida, atacante_id, recebedor, bonus + 0.05, defesa)
                    return None
                portador = recebedor
                zona = "area"
                bonus += 0.08
                continue
            if acao == "tabelar":
                zona = "area"
                bonus += 0.05
                continue
            trocar_portador = True
            if acao == "abrir":
                faixa = random.choice((0, 2))
                zona = "linha_de_fundo" if zona == "intermediaria" else "ataque"
            elif acao == "lancar":
                zona = "intermediaria" if zona == "defesa" else "ataque"
                bonus += 0.02 if zona == "intermediaria" else 0.04
            elif acao == "inverter":
                faixa = 2 if faixa == 0 else 0
                zona = PROXIMA_ZONA[zona]
                bonus += 0.02
            elif zona in ("defesa", "meio", "intermediaria") and random.random() < 0.5:
                zona = PROXIMA_ZONA[zona]
            else:
                bonus += 0.03
            continue
        if acao == "enfiar" and random.random() < 0.35:
            if random.random() < 0.1:
                recebedor = escolher_jogador(atacante, {"ATA": 6, "MEI": 2}, excluir=portador)
                registrar(partida, "impedimento_duvidoso", {"jogador": rotulo(recebedor)}, time_id=atacante_id)
                cara_a_cara(partida, atacante_id, recebedor, bonus, defesa)
                return None
            registrar(partida, "impedimento", tipo="perda", time_id=atacante_id)
            return None
        if acao == "driblar" and zona == "area" and random.random() < 0.08:
            lance_de_simulacao(partida, atacante_id, portador, marcador)
            return None
        registrar(partida, f"{acao}_erro", dados, tipo="perda", time_id=atacante_id)
        if acao == "cruzar":
            if random.random() < 0.015:
                marcar_gol(partida, atacante_id, marcador, contra=True)
                return None
            if random.random() < 0.3:
                cobrar_escanteio(partida, atacante_id, defesa)
                return None
        if defesa == "recuar" and zona in ("ataque", "linha_de_fundo", "area") and random.random() < 0.25:
            cobrar_escanteio(partida, atacante_id, defesa)
            return None
        if random.random() < 0.5:
            registrar(
                partida,
                f"{'bote' if defesa == 'falta' else defesa}_ok",
                {"marcador": rotulo(marcador), "time": defensor["nome"]},
                tipo="recuperacao",
                time_id=defensor_id,
            )
        contra = (
            defensor["plano"]["estilo"] == "contra-ataque"
            and atacante["plano"]["ofensividade"] >= 4
            and random.random() < 0.5
        )
        pressao_alta = defesa == "pressao" and zona in ("defesa", "meio") and random.random() < 0.25
        perdeu_atras = zona == "defesa" and random.random() < 0.35
        if contra or random.random() < 0.10 or pressao_alta or perdeu_atras:
            return defensor_id, marcador
        return None
    registrar(
        partida,
        "posse_sem_espaco",
        {"time": atacante["nome"], "defesa": defensor["nome"]},
        tipo="perda",
        time_id=atacante_id,
    )
    return None


def texto_penaltis(partida):
    """
    Monta o texto do placar da disputa de pênaltis.

    Args:
        partida (dict): Estado da partida, com o placar de pênaltis preenchido.

    Returns:
        str: Placar no formato "Pênaltis: SIG 4 x 3 SIG".
    """
    casa = partida["times"][partida["casa"]]
    fora = partida["times"][partida["fora"]]
    placar_penaltis = partida["penaltis"]
    return f"Pênaltis: {casa['sigla']} {placar_penaltis[casa['id']]} x {placar_penaltis[fora['id']]} {fora['sigla']}"


def disputa_decidida(placar_penaltis, cobrancas, primeiro, segundo):
    """
    Verifica se a disputa de pênaltis já tem vencedor.

    Nas cinco primeiras cobranças de cada lado, a disputa acaba quando um time não consegue mais alcançar o
    outro mesmo convertendo as cobranças restantes. Nas alternadas, acaba quando os dois bateram o mesmo
    número de vezes e o placar está diferente.

    Args:
        placar_penaltis (dict): Gols de pênalti de cada time.
        cobrancas (dict): Número de cobranças já feitas por cada time.
        primeiro (str): Time que bate primeiro.
        segundo (str): Time que bate em segundo.

    Returns:
        bool: True se a disputa está decidida, False caso contrário.
    """
    if cobrancas[primeiro] <= 5 and cobrancas[segundo] <= 5:
        restam_primeiro = 5 - cobrancas[primeiro]
        restam_segundo = 5 - cobrancas[segundo]
        return (
            placar_penaltis[primeiro] + restam_primeiro < placar_penaltis[segundo]
            or placar_penaltis[segundo] + restam_segundo < placar_penaltis[primeiro]
        )
    return cobrancas[primeiro] == cobrancas[segundo] and placar_penaltis[primeiro] != placar_penaltis[segundo]


def disputa_de_penaltis(partida):
    """
    Executa a disputa de pênaltis ao fim de um jogo empatado.

    Ordena os jogadores de linha em campo pela finalização, do melhor para o pior, e os times se alternam nas
    cobranças, com o mandante batendo primeiro e a fila de batedores recomeçando quando acaba. Cada cobrança é
    narrada e, quando a disputa é decidida (ou após 40 rodadas), o placar final é anotado na súmula.

    Args:
        partida (dict): Estado da partida.
    """
    ordem = (partida["casa"], partida["fora"])
    partida["penaltis"] = {time_id: 0 for time_id in ordem}
    cobrancas = {time_id: 0 for time_id in ordem}
    batedores = {}
    for time_id in ordem:
        linha = [j for j in partida["times"][time_id]["em_campo"] if j["pos"] != "GOL"] or partida["times"][time_id][
            "em_campo"
        ]
        batedores[time_id] = sorted(linha, key=lambda jogador: atributo_efetivo(jogador, "fin"), reverse=True)
    registrar(partida, "disputa_inicio", tipo="intervalo")
    for _ in range(40):
        for time_id in ordem:
            fila = batedores[time_id]
            batedor = fila[cobrancas[time_id] % len(fila)]
            cobrancas[time_id] += 1
            goleiro = goleiro_de(partida["times"][outro(partida, time_id)])
            entregar_bola(partida, time_id, "area", 1, batedor)
            desfecho = resolver_cobranca(partida, time_id, batedor, goleiro, minijogo=False)
            if desfecho == "gol":
                partida["penaltis"][time_id] += 1
            dados = {
                "jogador": rotulo(batedor),
                "goleiro": rotulo(goleiro) if goleiro else "o goleiro",
                "placar": texto_penaltis(partida),
            }
            registrar(partida, f"disputa_{desfecho}", dados, tipo="penalti_fim", time_id=time_id)
            if disputa_decidida(partida["penaltis"], cobrancas, *ordem):
                anotar_sumula(partida, texto_penaltis(partida))
                return
    anotar_sumula(partida, texto_penaltis(partida))


def vencedor_da_partida(partida):
    """
    Define o vencedor da partida pelo placar ou, em caso de empate, pelos pênaltis.

    Args:
        partida (dict): Estado da partida.

    Returns:
        str | None: Identificador do time vencedor, ou None em caso de empate sem disputa de pênaltis.
    """
    casa = partida["times"][partida["casa"]]
    fora = partida["times"][partida["fora"]]
    if casa["gols"] != fora["gols"]:
        return casa["id"] if casa["gols"] > fora["gols"] else fora["id"]
    if partida["penaltis"]:
        return casa["id"] if partida["penaltis"][casa["id"]] > partida["penaltis"][fora["id"]] else fora["id"]
    return None


def resultado_da_partida(partida):
    """
    Monta o resumo final da partida.

    Reúne mandante, visitante, placar, pênaltis, vencedor, expulsões, súmula, ocorrências (gols, expulsões e
    pênaltis perdidos, com o jogador de cada uma) e as estatísticas de cada time, com a posse convertida em
    porcentagem dos lances de posse.

    Args:
        partida (dict): Estado da partida.

    Returns:
        dict: Resultado com placar ("gm", "gv"), vermelhos ("vm", "vv"), pênaltis, vencedor, súmula e
            estatísticas por time.
    """
    casa = partida["times"][partida["casa"]]
    fora = partida["times"][partida["fora"]]
    total_posse = max(1, casa["posse"] + fora["posse"])
    return {
        "mandante": partida["casa"],
        "visitante": partida["fora"],
        "penaltis": dict(partida["penaltis"]) if partida["penaltis"] else None,
        "vencedor": vencedor_da_partida(partida),
        "gm": casa["gols"],
        "gv": fora["gols"],
        "vm": casa["vermelhos"],
        "vv": fora["vermelhos"],
        "sumula": list(partida["sumula"]),
        "ocorrencias": list(partida["ocorrencias"]),
        "estatisticas": {
            time["id"]: {
                "posse": round(100 * time["posse"] / total_posse),
                "chutes": time["chutes"],
                "no_alvo": time["no_alvo"],
                "faltas": time["faltas"],
            }
            for time in (casa, fora)
        },
    }
