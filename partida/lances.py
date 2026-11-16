import random

from config import ACRESCIMOS, MANDO_DE_CAMPO, MAX_SUBSTITUICOES, MINUTOS_POR_LANCE
from elenco.escalacao import atributo_efetivo, disponivel, forca_setores, limitar, rotulo
from elenco.substituicoes import aplicar_desgaste, marcar_desfalques, registrar_amarelo, substituir
from partida.narracao import narrar

DESCRICAO_ZONAS = {"meio": "no meio-campo", "ataque": "na entrada da área", "area": "dentro da área"}
PROXIMA_ZONA = {"meio": "ataque", "ataque": "area"}
ACOES = {
    "meio": ("tocar", "enfiar", "driblar", "lancar", "abrir"),
    "ataque": ("tocar", "tabelar", "driblar", "cruzar", "chutar"),
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
}
CHANCE_BASE = {
    "meio": {"tocar": 0.80, "enfiar": 0.32, "lancar": 0.45, "abrir": 0.74},
    "ataque": {"tocar": 0.76, "tabelar": 0.50, "cruzar": 0.55},
    "area": {"tocar": 0.66},
}
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
}
DEFESAS = ("bote", "pressao", "fechar", "recuar", "falta")
NOMES_DEFESAS = {
    "bote": "Dar o bote",
    "pressao": "Pressão alta",
    "fechar": "Fechar espaço",
    "recuar": "Recuar a linha",
    "falta": "Falta tática",
}
EFEITO_DEFESA = {
    "bote": {"meio": -0.07, "ataque": -0.07, "area": -0.07},
    "pressao": {"meio": -0.10, "ataque": 0.04, "area": 0.04},
    "fechar": {"meio": -0.03, "ataque": -0.03, "area": -0.03},
    "recuar": {"meio": 0.05, "ataque": -0.02, "area": -0.06},
    "falta": {"meio": 0.0, "ataque": 0.0, "area": -0.07},
}
CANTOS = ("esquerda", "meio", "direita")
FORCAS_PENALTI = ("colocado", "forte")

PESO_DIFERENCA = 0.005
PESO_MEIO = 0.006
PESO_FINALIZACAO = 0.004
FATOR_GOL = 1.55
PESOS_PORTADOR = {
    "meio": {"MEI": 5, "DEF": 1, "ATA": 2},
    "ataque": {"ATA": 4, "MEI": 4, "DEF": 0.5},
    "area": {"ATA": 6, "MEI": 2, "DEF": 0.5},
}
PESOS_MARCADOR = {"meio": {"MEI": 5, "DEF": 2, "ATA": 1}, "ataque": {"DEF": 5, "MEI": 2}, "area": {"DEF": 6, "MEI": 1}}
PESOS_CABECEIO = {"ATA": 5, "DEF": 2, "MEI": 1}
PESOS_REBOTE = {"ATA": 5, "MEI": 3, "DEF": 1}


def montar_time(clube, plano, em_casa):
    """
    Monta a estrutura de um time para a partida a partir do clube.

    Marca os desfalques do elenco, separa os titulares disponíveis dos reservas disponíveis e zera os contadores da partida (gols, cartões, chutes, posse, faltas e substituições).

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

    Monta os dois times, define relógio, posição da bola e narração vazias, e sorteia chuva com 12% de chance. O mandante só recebe mando de campo se o jogo não for em campo neutro.

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

    Usa 45 como base no primeiro tempo e 90 no segundo; passando da base, mostra o tempo extra no formato "45+2'".

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

    Gera o texto da narração a partir da chave, guarda apenas as cinco últimas linhas narradas com o minuto e, se houver uma função de exibição configurada, repassa o lance para ela.

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

    Considera apenas posições com peso positivo, sem o jogador excluído. Se ninguém se encaixar, usa qualquer jogador em campo exceto o excluído (ou o próprio excluído, se for o único), com peso mínimo de 0.5.

    Args:
        time (dict): Time da partida.
        pesos (dict): Peso de cada posição ("GOL", "DEF", "MEI", "ATA") no sorteio.
        excluir (dict | None): Jogador que não deve ser escolhido. Padrão None.

    Returns:
        dict: Jogador sorteado.
    """
    candidatos = [jogador for jogador in time["em_campo"] if
                  jogador is not excluir and pesos.get(jogador["pos"], 0) > 0]
    if not candidatos:
        candidatos = [jogador for jogador in time["em_campo"] if jogador is not excluir] or time["em_campo"]
    return random.choices(candidatos, weights=[pesos.get(jogador["pos"], 0.5) or 0.5 for jogador in candidatos])[0]


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

    Repassa a pergunta para a função "escolha" do controle do time (jogador humano ou IA). Se a resposta não for uma das chaves oferecidas, usa a primeira opção.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time que decide.
        pergunta (str): Texto da pergunta.
        opcoes (list): Lista de tuplas (chave, rótulo, peso).

    Returns:
        str: Chave da opção escolhida.
    """
    escolha = partida["controles"][time_id]["escolha"](partida, time_id, pergunta, opcoes)
    chaves = [chave for chave, _, _ in opcoes]
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

    Parte da força dos setores dos jogadores em campo e soma o bônus de mando de campo para o time da casa, com mais 3 pontos enquanto a torcida estiver empurrando. O resultado fica guardado até o cache ser invalidado.

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

    Sem jogador de saída (por exemplo, após uma lesão), apenas coloca o reserva em campo se ainda houver substituições disponíveis. Com jogador de saída, faz a troca normal. Em caso de sucesso, recalcula os setores, narra e anota a substituição na súmula.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time que faz a substituição.
        sai_id (str | None): Identificador do jogador que sai, ou None quando ninguém sai de campo.
        entra_id (str): Identificador do reserva que entra.
        nome_saida (str | None): Nome exibido para quem saiu quando sai_id é None. Padrão None, que mostra "-".

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
    registrar(partida, "substituicao", {"time": time["nome"], "sai": nome_sai, "entra": rotulo(entra)},
              tipo="substituicao", time_id=time_id)
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

    Tira o jogador de campo, soma um vermelho ao time, suspende o jogador por pelo menos uma rodada, recalcula os setores, narra e anota na súmula, e pausa a partida para os dois times.

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
    invalidar_setores(partida)
    registrar(partida, chave, {"jogador": rotulo(jogador)}, tipo="vermelho", time_id=time_id)
    anotar_sumula(partida, f"Vermelho — {rotulo(jogador)} ({time['sigla']})")
    pausar_todos(partida, "expulsao")


def amarelar(partida, time_id, jogador):
    """
    Aplica um cartão amarelo a um jogador.

    Se o jogador já tem amarelo nesta partida, é expulso pelo segundo amarelo. Caso contrário, o cartão é contado para a suspensão por acúmulo, narrado e anotado na súmula, com aviso quando for o terceiro amarelo.

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

    Define as rodadas de lesão, tira o jogador de campo, recalcula os setores, narra e anota na súmula como lesão (quando rodadas > 0) ou câimbra, e avisa o controle do time para que possa repor o jogador.

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

    Se a torcida já está empurrando, reduz a duração em um lance; senão, com 3% de chance ela passa a empurrar o mandante por 3 lances. Para cada time, há 1,2% de chance de um jogador de linha se lesionar (1 a 3 rodadas) e, se não houver lesão, 8% de chance de um jogador com energia abaixo de 15 sair com câimbra.

    Args:
        partida (dict): Estado da partida.
    """
    if partida["torcida"] > 0:
        partida["torcida"] -= 1
    elif random.random() < 0.03:
        partida["torcida"] = 3
        invalidar_setores(partida)
        registrar(partida, "torcida", {"time": partida["times"][partida["casa"]]["nome"]}, tipo="evento",
                  time_id=partida["casa"])
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

    A força do meio de cada time é ajustada pela intensidade do plano e recebe 4 pontos extras no estilo posse. A diferença entre os times desloca a chance base de 40% de cada lado, limitada entre 12% e 68%; o restante é a chance de ninguém ficar com a bola.

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

    Na arrancada vale o físico; nos demais dribles, a média de finalização, passe e físico; nas outras ações, o passe.

    Args:
        portador (dict): Jogador com a bola.
        acao (str): Ação tentada.
        drible (str | None): Tipo de drible, quando a ação é "driblar".

    Returns:
        float: Valor efetivo do atributo usado na ação.
    """
    if acao == "driblar":
        if drible == "arrancada":
            return atributo_efetivo(portador, "fis")
        return (atributo_efetivo(portador, "fin") + atributo_efetivo(portador, "pas") + atributo_efetivo(portador,
                                                                                                         "fis")) / 3
    return atributo_efetivo(portador, "pas")


def chance_da_acao(partida, atacante_id, zona, faixa, acao, portador, marcador, defesa, bonus, drible=None):
    """
    Calcula a chance de sucesso de uma ação ofensiva.

    Parte da chance base da ação na zona (ou do drible), com penalidade de 0,12 para cruzamento pelo meio. Soma a diferença entre o atributo do portador e o desarme do marcador (peso 0,4) e entre o setor de ataque e o de defesa (peso 0,6), o bônus acumulado, os efeitos da ofensividade dos dois times, da intensidade do defensor e da defesa escolhida. Com chuva, passes, lançamentos e cruzamentos perdem 0,06. O resultado fica entre 5% e 95%.

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
    setor_atq = forca_atq["meio"] if zona == "meio" else forca_atq["ataque"]
    setor_def = forca_def["meio"] if zona == "meio" else forca_def["defesa"]
    diferenca = (valor_da_acao(portador, acao, drible) - atributo_efetivo(marcador, "des")) * 0.4 + (
                setor_atq - setor_def) * 0.6
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

    Parte de 5%, ajustada pela intensidade do plano defensivo; dar o bote soma 5%, pressão alta soma 3% e enfrentar um drible soma 3%. Dentro da área a chance cai pela metade.

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

    Soma o gol, leva a bola para o gol e narra o lance. Gols normais têm 4% de chance de serem anulados pelo VAR, desfazendo o placar. Se o gol vale, é anotado na súmula e, quando não é contra, conta para o artilheiro.

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
    registrar(partida, chave, {"jogador": rotulo(autor), "time": time["nome"], "placar": placar(partida)}, tipo="gol",
              time_id=atacante_id)
    if not contra and random.random() < 0.04:
        time["gols"] -= 1
        registrar(partida, "var", tipo="var", time_id=atacante_id)
        anotar_sumula(partida, f"Gol anulado pelo VAR — {rotulo(autor)} ({time['sigla']})")
        return False
    if contra:
        anotar_sumula(partida, f"GOL CONTRA — {rotulo(autor)} (a favor do {time['sigla']})")
    else:
        autor["gols"] += 1
        anotar_sumula(partida, f"GOL — {rotulo(autor)} ({time['sigla']})")
    return True


def escolher_chute(partida, atacante_id, finalizador, local):
    """
    Pergunta ao time como o finalizador vai bater na bola.

    Oferece os tipos de chute com seus pesos; o chute forte ganha peso extra de longe ou do meio-campo e a cavadinha ganha peso extra cara a cara.

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
        opcoes.append((chave, chute["nome"], peso))
    return perguntar(partida, atacante_id, f"Como {rotulo(finalizador)} vai bater?", opcoes)


def finalizar(partida, atacante_id, finalizador, local, tipo="colocado", bonus=0.0, defesa="fechar", rebote=True,
              escanteio=True):
    """
    Resolve uma finalização ao gol.

    Primeiro sorteia se o chute vai no alvo, com base no tipo de chute, no local, na finalização do jogador (no cabeceio, média com o físico), no bônus e na linha recuada do adversário. Fora do alvo, há 12% de chance de bater na trave, com 40% de chance de rebote. No alvo, a chance de gol compara finalização e reflexo do goleiro, ajustada pelo tipo de chute, e cai 0,03 no estilo jogo direto. Se o goleiro defende, pode haver rebote (22%) ou escanteio (35%). Atualiza chutes, chutes no alvo e o último local de finalização.

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
    mover_bola(partida, atacante_id, "area" if local not in ("longe", "meio_campo", "falta") else "ataque")
    registrar(partida, f"chute_{local}", {"jogador": rotulo(finalizador), "tipo": chute["texto"]}, tipo="chute",
              time_id=atacante_id)
    finalizacao = atributo_efetivo(finalizador, "fin")
    if local == "cabeceio":
        finalizacao = (finalizacao + atributo_efetivo(finalizador, "fis")) / 2
    alvo = chute["alvo"] + LOCAIS[local]["alvo"] + (finalizacao - 65) * 0.004 + bonus * 0.5
    if defesa == "recuar" and local in ("longe", "area", "cara"):
        alvo -= 0.06
    atacante["chutes"] += 1
    if random.random() >= limitar(alvo, 0.1, 0.95):
        if random.random() < 0.12:
            registrar(partida, "trave", {"jogador": rotulo(finalizador)}, tipo="trave", time_id=atacante_id)
            if rebote and random.random() < 0.4:
                pegar_rebote(partida, atacante_id, defesa)
            return
        registrar(partida, "fora", {"jogador": rotulo(finalizador)}, tipo="fora", time_id=atacante_id)
        return
    atacante["no_alvo"] += 1
    fator_goleiro = 0.45 if tipo == "cavadinha" and local == "cara" else chute["goleiro"]
    reflexo = atributo_efetivo(goleiro, "ref") if goleiro else 30
    chance = (LOCAIS[local]["gol"] + (
                finalizacao - reflexo) * PESO_FINALIZACAO) / fator_goleiro * FATOR_GOL + bonus * 0.5
    if atacante["plano"]["estilo"] == "jogo direto":
        chance -= 0.03
    if random.random() < limitar(chance, 0.03, 0.9):
        marcar_gol(partida, atacante_id, finalizador)
        return
    nome_goleiro = rotulo(goleiro) if goleiro else "o zagueiro improvisado"
    registrar(partida, "defesa", {"goleiro": nome_goleiro}, tipo="defesa", time_id=atacante_id)
    if rebote and random.random() < 0.22:
        pegar_rebote(partida, atacante_id, defesa)
    elif escanteio and random.random() < 0.35:
        cobrar_escanteio(partida, atacante_id, defesa)


def pegar_rebote(partida, atacante_id, defesa):
    """
    Resolve a sobra de bola após uma finalização.

    Sorteia quem pega o rebote e pergunta se ele chuta de primeira (chute forte do local de rebote) ou ajeita antes; ao ajeitar, há 45% de chance de a bola ser bloqueada, senão sai um chute colocado da área. Nenhum dos chutes pode gerar novo rebote.

    Args:
        partida (dict): Estado da partida.
        atacante_id (str): Time que pega o rebote.
        defesa (str): Postura defensiva do adversário.
    """
    time = partida["times"][atacante_id]
    jogador = escolher_jogador(time, PESOS_REBOTE)
    entregar_bola(partida, atacante_id, "area", 1, jogador)
    registrar(partida, "rebote", {"jogador": rotulo(jogador)}, tipo="oportunidade", time_id=atacante_id)
    escolha = perguntar(partida, atacante_id, f"Rebote! {rotulo(jogador)} pega a sobra. E agora?", [
        ("primeira", "Chutar de primeira", 5),
        ("ajeitar", "Ajeitar e bater", 3),
    ])
    if escolha == "primeira":
        finalizar(partida, atacante_id, jogador, "rebote", "forte", defesa=defesa, rebote=False)
    elif random.random() < 0.45:
        registrar(partida, "rebote_bloqueado", {"jogador": rotulo(jogador)}, tipo="perda", time_id=atacante_id)
    else:
        finalizar(partida, atacante_id, jogador, "area", "colocado", defesa=defesa, rebote=False)


def cobrar_escanteio(partida, atacante_id, defesa):
    """
    Resolve a cobrança de um escanteio.

    O melhor batedor cobra; há 0,4% de chance de gol olímpico. Na cobrança curta, há 60% de chance de um companheiro chutar de longe. Na primeira trave (45%) ou na segunda (38%, com bônus de 0,05), um jogador cabeceia. Nos demais casos a defesa afasta. Nenhuma finalização daqui gera novo escanteio.

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
    escolha = perguntar(partida, atacante_id, "Escanteio! Como cobrar?", [
        ("primeira", "Na primeira trave", 3),
        ("segunda", "Na segunda trave", 3),
        ("curto", "Cobrança curta", 2),
    ])
    if escolha == "curto":
        if random.random() < 0.6:
            jogador = escolher_jogador(time, PESOS_PORTADOR["ataque"], excluir=batedor)
            registrar(partida, "escanteio_curto", {"jogador": rotulo(jogador)}, time_id=atacante_id)
            finalizar(partida, atacante_id, jogador, "longe", escolher_chute(partida, atacante_id, jogador, "longe"),
                      defesa=defesa, escanteio=False)
            return
    elif random.random() < (0.45 if escolha == "primeira" else 0.38):
        bonus = 0.05 if escolha == "segunda" else 0.0
        finalizar(partida, atacante_id, escolher_jogador(time, PESOS_CABECEIO, excluir=batedor), "escanteio",
                  bonus=bonus, defesa=defesa, escanteio=False)
        return
    registrar(partida, "escanteio_afastado", tipo="perda", time_id=atacante_id)


def cobrar_falta(partida, atacante_id, defesa):
    """
    Resolve a cobrança de uma falta perigosa na entrada da área.

    O melhor batedor pode bater por cima da barreira (chute colocado), rasteiro (20% de chance de parar na barreira, senão chute colocado com bônus de 0,03), forte no canto ou cruzar na área.

    Args:
        partida (dict): Estado da partida.
        atacante_id (str): Time que cobra a falta.
        defesa (str): Postura defensiva do adversário.
    """
    time = partida["times"][atacante_id]
    batedor = melhor_batedor(time)
    mover_bola(partida, atacante_id, "ataque", 1)
    registrar(partida, "falta_perigosa", {"time": time["nome"]}, tipo="bola_parada", time_id=atacante_id)
    escolha = perguntar(partida, atacante_id, f"Falta perigosa! {rotulo(batedor)} na bola. Como cobrar?", [
        ("barreira", "Por cima da barreira", 4),
        ("rasteiro", "Rasteiro, por baixo", 2),
        ("forte", "Bomba no canto", 2),
        ("cruzar", "Cruzar na área", 3),
    ])
    if escolha == "cruzar":
        cruzamento(partida, atacante_id, batedor, 0.0, defesa)
        return
    if escolha == "rasteiro" and random.random() < 0.2:
        registrar(partida, "barreira", tipo="defesa", time_id=atacante_id)
        return
    tipo = "forte" if escolha == "forte" else "colocado"
    bonus = 0.03 if escolha == "rasteiro" else 0.0
    finalizar(partida, atacante_id, batedor, "falta", tipo, bonus, defesa)


def resolver_cobranca(partida, atacante_id, batedor, goleiro):
    """
    Decide o desfecho de uma cobrança de pênalti.

    O controle do atacante escolhe canto e força, e o do defensor escolhe o canto do pulo; a escolha fica salva em "ultimo_penalti". O chute vai para fora com 4% (colocado) ou 14% (forte) de chance, mais um acréscimo se a finalização for menor que 70. Se o goleiro acerta o canto, defende com 80% no meio, 55% no colocado ou 30% no forte, ajustado pela diferença entre reflexo e finalização e limitado entre 10% e 90%.

    Args:
        partida (dict): Estado da partida.
        atacante_id (str): Time que cobra.
        batedor (dict): Jogador que bate o pênalti.
        goleiro (dict | None): Goleiro adversário, ou None se não houver goleiro em campo.

    Returns:
        str: Desfecho da cobrança: "fora", "defesa" ou "gol".
    """
    defensor_id = outro(partida, atacante_id)
    canto, forca = partida["controles"][atacante_id]["bater_penalti"](partida, atacante_id, batedor, goleiro)
    pulo = partida["controles"][defensor_id]["defender_penalti"](partida, defensor_id, batedor, goleiro)
    partida["ultimo_penalti"] = {"time": atacante_id, "canto": canto, "forca": forca, "pulo": pulo}
    finalizacao = atributo_efetivo(batedor, "fin")
    chance_fora = (0.04 if forca == "colocado" else 0.14) + max(0, 70 - finalizacao) * 0.002
    if random.random() < chance_fora:
        return "fora"
    if canto == pulo:
        defende = 0.80 if canto == "meio" else (0.55 if forca == "colocado" else 0.30)
        reflexo = atributo_efetivo(goleiro, "ref") if goleiro else 30
        defende += (reflexo - finalizacao) * 0.004
        if random.random() < limitar(defende, 0.1, 0.9):
            return "defesa"
    return "gol"


def cobrar_penalti(partida, atacante_id):
    """
    Executa um pênalti marcado durante o jogo.

    O melhor batedor cobra contra o goleiro adversário. Conta o chute e, conforme o desfecho, registra o pênalti perdido, defendido ou convertido, atualizando gols do time e do batedor, narração e súmula.

    Args:
        partida (dict): Estado da partida.
        atacante_id (str): Time que cobra o pênalti.
    """
    defensor_id = outro(partida, atacante_id)
    atacante = partida["times"][atacante_id]
    goleiro = goleiro_de(partida["times"][defensor_id])
    batedor = melhor_batedor(atacante)
    entregar_bola(partida, atacante_id, "area", 1, batedor)
    registrar(partida, "penalti", {"time": atacante["nome"], "jogador": rotulo(batedor)}, tipo="penalti",
              time_id=atacante_id)
    partida["ultimo_local"] = "penalti"
    desfecho = resolver_cobranca(partida, atacante_id, batedor, goleiro)
    atacante["chutes"] += 1
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
    mover_bola(partida, atacante_id, "gol", 1)
    registrar(partida, "penalti_gol", {"jogador": rotulo(batedor), "placar": placar(partida)}, tipo="gol",
              time_id=atacante_id)
    anotar_sumula(partida, f"GOL (pênalti) — {rotulo(batedor)} ({atacante['sigla']})")


def cartao_na_falta(partida, defensor_id, marcador, chance_amarelo):
    """
    Sorteia o cartão aplicado ao autor de uma falta.

    Com 2,5% de chance o jogador recebe vermelho direto; se o sorteio ficar abaixo de chance_amarelo, recebe amarelo. Como o mesmo sorteio é usado, a chance real de amarelo é chance_amarelo menos 2,5%.

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

    Soma a falta ao time defensor, narra o lance e sorteia o cartão, com chance de amarelo de 22% (30% se a defesa deu o bote). O tipo de falta depende da zona onde ocorreu.

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
    registrar(partida, "falta", {"marcador": rotulo(marcador), "jogador": rotulo(portador)}, tipo="falta",
              time_id=defensor_id)
    cartao_na_falta(partida, defensor_id, marcador, 0.22 + (0.08 if defesa == "bote" else 0))
    if zona == "area":
        return "penalti"
    if zona == "ataque":
        return "perigosa"
    return "meio"


def falta_tatica(partida, atacante_id, zona, portador, defesa):
    """
    Executa a falta tática escolhida pela defesa para parar a jogada.

    Sorteia o marcador que faz a falta, soma a falta ao time defensor, narra o lance e sorteia o cartão com chance de amarelo de 45%. Se a falta foi na entrada da área, o atacante cobra uma falta perigosa.

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
    registrar(partida, "falta_tatica", {"marcador": rotulo(marcador), "jogador": rotulo(portador)}, tipo="falta",
              time_id=defensor_id)
    cartao_na_falta(partida, defensor_id, marcador, 0.45)
    if zona == "ataque":
        cobrar_falta(partida, atacante_id, defesa)


def cara_a_cara(partida, atacante_id, jogador, bonus, defesa):
    """
    Resolve um lance em que o atacante fica cara a cara com o goleiro.

    O time escolhe tocar no canto, encher o pé, cavadinha ou driblar o goleiro. Os três primeiros viram uma finalização do local "cara". No drible, a chance parte de 50%, ajustada pela diferença entre a técnica do jogador (média de finalização e físico) e o reflexo do goleiro, mais o bônus, entre 15% e 85%; se der certo, o gol é marcado com o gol vazio, senão o goleiro salva.

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
    escolha = perguntar(partida, atacante_id, f"{rotulo(jogador)} está cara a cara com o goleiro!", [
        ("colocado", "Tocar no canto", 4),
        ("forte", "Encher o pé", 3),
        ("cavadinha", "Cavadinha", 2),
        ("driblar", "Driblar o goleiro", 2),
    ])
    if escolha != "driblar":
        finalizar(partida, atacante_id, jogador, "cara", escolha, bonus, defesa)
        return
    reflexo = atributo_efetivo(goleiro, "ref") if goleiro else 30
    tecnica = (atributo_efetivo(jogador, "fin") + atributo_efetivo(jogador, "fis")) / 2
    nome_goleiro = rotulo(goleiro) if goleiro else "o zagueiro"
    if random.random() < limitar(0.5 + (tecnica - reflexo) * 0.005 + bonus, 0.15, 0.85):
        registrar(partida, "driblou_goleiro", {"jogador": rotulo(jogador)}, time_id=atacante_id)
        partida["times"][atacante_id]["chutes"] += 1
        partida["times"][atacante_id]["no_alvo"] += 1
        partida["ultimo_local"] = "gol_vazio"
        marcar_gol(partida, atacante_id, jogador)
        return
    registrar(partida, "goleiro_salva", {"goleiro": nome_goleiro, "jogador": rotulo(jogador)}, tipo="defesa",
              time_id=atacante_id)


def cruzamento(partida, atacante_id, cruzador, bonus, defesa):
    """
    Resolve a chegada de um cruzamento na área.

    Sorteia o receptor, dando preferência aos atacantes, e pergunta se ele cabeceia, bate de voleio (chute forte) ou domina e chuta. Ao dominar, há 40% de chance de perder a bola; senão o time escolhe o tipo de chute da área.

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
    escolha = perguntar(partida, atacante_id, f"A bola vem na área para {rotulo(receptor)}!", [
        ("cabecear", "Cabecear", 5),
        ("voleio", "Bater de voleio", 2),
        ("dominar", "Dominar e chutar", 3),
    ])
    if escolha == "cabecear":
        finalizar(partida, atacante_id, receptor, "cabeceio", bonus=bonus, defesa=defesa)
    elif escolha == "voleio":
        finalizar(partida, atacante_id, receptor, "voleio", "forte", bonus, defesa)
    elif random.random() < 0.4:
        registrar(partida, "dominar_erro", {"jogador": rotulo(receptor)}, tipo="perda", time_id=atacante_id)
    else:
        finalizar(partida, atacante_id, receptor, "area", escolher_chute(partida, atacante_id, receptor, "area"), bonus,
                  defesa)


def oportunidade_do_meio(partida, atacante_id, portador, defesa):
    """
    Oferece ao portador a chance de chutar do meio-campo com o goleiro adiantado.

    Narra o goleiro adiantado e pergunta se o portador arrisca o chute forte do meio-campo, sem possibilidade de rebote, ou segue a jogada.

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
    escolha = perguntar(partida, atacante_id,
                        f"{nome_goleiro} está adiantado! {rotulo(portador)} arrisca do meio-campo?", [
                            ("arriscar", "Chutar do meio-campo", 1),
                            ("seguir", "Seguir a jogada", 4),
                        ])
    if escolha == "arriscar":
        finalizar(partida, atacante_id, portador, "meio_campo", "forte", defesa=defesa, rebote=False)
        return True
    return False


def jogar_posse(partida, atacante_id, contra_ataque=False, portador=None):
    """
    Simula uma posse de bola completa do time atacante.

    A posse começa no meio-campo, ou já no ataque em contra-ataque (bônus de 0,08) e, no estilo jogo direto, com 40% de chance (bônus de -0,03). O adversário escolhe a postura defensiva; a falta tática fora da área encerra a posse na hora. Em até seis passos, o time escolhe uma ação por zona (no último passo, toca no meio ou chuta nas outras zonas), que pode virar falta, finalização, avanço de zona, troca de portador ou perda da bola. Na perda, pode haver escanteio, gol contra no cruzamento ou recuperação do adversário, que puxa um contra-ataque se jogar nesse estilo contra um time ofensivo (50%), com 10% de chance geral ou com 25% de chance quando a pressão alta rouba no meio-campo.

    Args:
        partida (dict): Estado da partida.
        atacante_id (str): Time com a posse.
        contra_ataque (bool): Se a posse nasce de um contra-ataque. Padrão False.
        portador (dict | None): Jogador que começa com a bola; se não estiver em campo, outro é sorteado. Padrão None.

    Returns:
        tuple | None: (defensor_id, marcador) quando a posse termina em contra-ataque do adversário, senão None.
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
    for passo in range(6):
        if trocar_portador:
            portador = escolher_jogador(atacante, PESOS_PORTADOR[zona], excluir=portador)
        entregar_bola(partida, atacante_id, zona, faixa, portador)
        trocar_portador = False
        if contra_ataque and passo == 0:
            registrar(partida, "contra_ataque", {"time": atacante["nome"], "jogador": rotulo(portador)},
                      time_id=atacante_id)
        if zona == "meio" and random.random() < 0.025 and oportunidade_do_meio(partida, atacante_id, portador, defesa):
            return None
        if passo == 5:
            acao = "tocar" if zona == "meio" else "chutar"
        else:
            acao = controles[atacante_id]["ataque"](partida, atacante_id, zona, portador)
        if acao not in ACOES[zona]:
            acao = ACOES[zona][0]
        marcador = escolher_jogador(defensor, PESOS_MARCADOR[zona])
        if acao == "chutar":
            local = "longe" if zona == "ataque" else "area"
            finalizar(partida, atacante_id, portador, local, escolher_chute(partida, atacante_id, portador, local),
                      bonus, defesa)
            return None
        if random.random() < chance_de_falta(defensor["plano"], defesa, acao, zona):
            desfecho = cometer_falta(partida, atacante_id, zona, portador, marcador, defesa)
            if desfecho == "penalti":
                cobrar_penalti(partida, atacante_id)
                return None
            if desfecho == "perigosa":
                cobrar_falta(partida, atacante_id, defesa)
                return None
            continue
        drible = None
        if acao == "driblar":
            drible = perguntar(partida, atacante_id, f"Que drible {rotulo(portador)} vai tentar?", [
                (chave, dados_drible["nome"], dados_drible["peso"]) for chave, dados_drible in DRIBLES.items()
            ])
        dados = {"jogador": rotulo(portador), "marcador": rotulo(marcador), "time": atacante["nome"]}
        if random.random() < chance_da_acao(partida, atacante_id, zona, faixa, acao, portador, marcador, defesa, bonus,
                                            drible):
            if defesa == "pressao" and zona == "meio":
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
                cruzamento(partida, atacante_id, portador, bonus + (0.04 if faixa != 1 else 0.0), defesa)
                return None
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
                zona = "ataque"
            elif acao == "lancar":
                zona = "ataque"
                bonus += 0.04
            elif zona == "meio" and random.random() < 0.5:
                zona = "ataque"
            else:
                bonus += 0.03
            continue
        if acao == "enfiar" and random.random() < 0.35:
            registrar(partida, "impedimento", tipo="perda", time_id=atacante_id)
            return None
        registrar(partida, f"{acao}_erro", dados, tipo="perda", time_id=atacante_id)
        if acao == "cruzar":
            if random.random() < 0.015:
                marcar_gol(partida, atacante_id, marcador, contra=True)
                return None
            if random.random() < 0.3:
                cobrar_escanteio(partida, atacante_id, defesa)
                return None
        if defesa == "recuar" and zona != "meio" and random.random() < 0.25:
            cobrar_escanteio(partida, atacante_id, defesa)
            return None
        if random.random() < 0.5:
            registrar(partida, f"{'bote' if defesa == 'falta' else defesa}_ok",
                      {"marcador": rotulo(marcador), "time": defensor["nome"]}, tipo="recuperacao", time_id=defensor_id)
        contra = defensor["plano"]["estilo"] == "contra-ataque" and atacante["plano"][
            "ofensividade"] >= 4 and random.random() < 0.5
        if contra or random.random() < 0.10 or (defesa == "pressao" and zona == "meio" and random.random() < 0.25):
            return defensor_id, marcador
        return None
    registrar(partida, "tocar_erro", {"jogador": rotulo(partida["portador"]), "marcador": "a defesa"}, tipo="perda",
              time_id=atacante_id)
    return None


def jogar_lance(partida):
    """
    Simula um lance da partida, da disputa no meio-campo até o fim da jogada.

    Aplica o desgaste e os ajustes dos controles nos dois times, sorteia os eventos do lance e disputa a bola no meio. Se ninguém ganha, narra a bola saindo; senão o vencedor joga a posse e, se ela terminar em contra-ataque, o adversário joga uma posse de contra-ataque.

    Args:
        partida (dict): Estado da partida.
    """
    for time_id in (partida["casa"], partida["fora"]):
        aplicar_desgaste(partida["times"][time_id])
        partida["controles"][time_id]["ajuste"](partida, time_id)
    invalidar_setores(partida)
    sortear_eventos_do_lance(partida)
    mover_bola(partida, None, "meio", 1)
    vencedor = disputar_meio(partida)
    if vencedor is None:
        lateral = random.choice((partida["casa"], partida["fora"]))
        registrar(partida, "meio_nada", {"time": partida["times"][lateral]["nome"]}, tipo="meio")
        return
    portador = escolher_jogador(partida["times"][vencedor], PESOS_PORTADOR["meio"])
    entregar_bola(partida, vencedor, "meio", None, portador)
    registrar(partida, "meio_ganhou", {"time": partida["times"][vencedor]["nome"], "jogador": rotulo(portador)},
              tipo="meio", time_id=vencedor)
    proximo = jogar_posse(partida, vencedor, portador=portador)
    if proximo:
        jogar_posse(partida, proximo[0], contra_ataque=True, portador=proximo[1])


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

    Nas cinco primeiras cobranças de cada lado, a disputa acaba quando um time não consegue mais alcançar o outro mesmo convertendo as cobranças restantes. Nas alternadas, acaba quando os dois bateram o mesmo número de vezes e o placar está diferente.

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
        return (placar_penaltis[primeiro] + restam_primeiro < placar_penaltis[segundo]
                or placar_penaltis[segundo] + restam_segundo < placar_penaltis[primeiro])
    return cobrancas[primeiro] == cobrancas[segundo] and placar_penaltis[primeiro] != placar_penaltis[segundo]


def disputa_de_penaltis(partida):
    """
    Executa a disputa de pênaltis ao fim de um jogo empatado.

    Ordena os jogadores de linha em campo pela finalização, do melhor para o pior, e os times se alternam nas cobranças, com o mandante batendo primeiro e a fila de batedores recomeçando quando acaba. Cada cobrança é narrada e, quando a disputa é decidida (ou após 40 rodadas), o placar final é anotado na súmula.

    Args:
        partida (dict): Estado da partida.
    """
    ordem = (partida["casa"], partida["fora"])
    partida["penaltis"] = {time_id: 0 for time_id in ordem}
    cobrancas = {time_id: 0 for time_id in ordem}
    batedores = {}
    for time_id in ordem:
        linha = [j for j in partida["times"][time_id]["em_campo"] if j["pos"] != "GOL"] or partida["times"][time_id]["em_campo"]
        batedores[time_id] = sorted(linha, key=lambda jogador: atributo_efetivo(jogador, "fin"), reverse=True)
    registrar(partida, "disputa_inicio", tipo="intervalo")
    for _ in range(40):
        for time_id in ordem:
            fila = batedores[time_id]
            batedor = fila[cobrancas[time_id] % len(fila)]
            cobrancas[time_id] += 1
            goleiro = goleiro_de(partida["times"][outro(partida, time_id)])
            entregar_bola(partida, time_id, "area", 1, batedor)
            desfecho = resolver_cobranca(partida, time_id, batedor, goleiro)
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

    Reúne mandante, visitante, placar, pênaltis, vencedor, expulsões, súmula e as estatísticas de cada time, com a posse convertida em porcentagem dos lances de posse.

    Args:
        partida (dict): Estado da partida.

    Returns:
        dict: Resultado com placar ("gm", "gv"), vermelhos ("vm", "vv"), pênaltis, vencedor, súmula e estatísticas por time.
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


def jogar_partida(partida, controles, exibir=None, mata_mata=False):
    """
    Joga a partida inteira, do apito inicial ao resultado.

    Configura os controles e a exibição, narra o início e a chuva, e joga os dois tempos lance a lance, avançando o relógio a cada lance até o limite de 45 minutos mais os acréscimos sorteados. No intervalo, pausa os dois times. Em jogos de mata-mata que terminam empatados, decide nos pênaltis.

    Args:
        partida (dict): Estado da partida criado por criar_partida.
        controles (dict): Funções de decisão de cada time, indexadas pelo identificador do time.
        exibir (callable | None): Função chamada a cada lance narrado. Padrão None.
        mata_mata (bool): Se o empate deve ser decidido nos pênaltis. Padrão False.

    Returns:
        dict: Resultado final da partida, como em resultado_da_partida.
    """
    partida["controles"] = controles
    partida["exibir"] = exibir
    casa = partida["times"][partida["casa"]]
    fora = partida["times"][partida["fora"]]
    registrar(partida, "inicio", {"time_casa": casa["nome"], "time_fora": fora["nome"]}, tipo="inicio")
    if partida["chuva"]:
        registrar(partida, "chuva", tipo="evento")
    for tempo in (1, 2):
        partida["tempo"] = tempo
        inicio = 0 if tempo == 1 else 45
        partida["minuto"] = inicio
        partida["limite"] = inicio + 45 + random.randint(*ACRESCIMOS)
        if tempo == 2:
            registrar(partida, "segundo_tempo", {"placar": placar(partida)}, tipo="inicio")
        while True:
            partida["minuto"] += random.randint(*MINUTOS_POR_LANCE)
            if partida["minuto"] > partida["limite"]:
                partida["minuto"] = partida["limite"]
                break
            jogar_lance(partida)
        if tempo == 1:
            registrar(partida, "intervalo", {"placar": placar(partida)}, tipo="intervalo")
            pausar_todos(partida, "intervalo")
    registrar(partida, "fim", {"placar": placar(partida)}, tipo="fim")
    if mata_mata and partida["times"][partida["casa"]]["gols"] == partida["times"][partida["fora"]]["gols"]:
        disputa_de_penaltis(partida)
    partida["encerrada"] = True
    return resultado_da_partida(partida)
