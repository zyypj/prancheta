import random

from config import EVOLUCOES_PARA_QUALIDADE, FOCOS_DE_TREINO, INTENSIDADES_DE_TREINO
from elenco.escalacao import disponivel, limitar


def pode_treinar(estado):
    """
    Indica se o técnico ainda pode treinar o elenco nesta etapa (um treino por semana).

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        bool: True se ainda não houve treino nesta etapa.
    """
    return estado.get("treino_etapa") != estado["etapa"]


def grupo_de_treino(clube, grupo, foco):
    """
    Lista os jogadores que participam do treino.

    Só treinam jogadores disponíveis (sem lesão nem suspensão). O treino de goleiros reúne apenas os goleiros
    do grupo escolhido; os outros focos deixam os goleiros de fora, exceto o de recuperação.

    Args:
        clube (dict): Clube do técnico.
        grupo (str): "titulares", "reservas" ou "todos".
        foco (str): Chave do foco em FOCOS_DE_TREINO.

    Returns:
        list[dict]: Jogadores que vão treinar.
    """
    if grupo == "titulares":
        jogadores = [j for j in clube["elenco"] if j["id"] in clube["titulares"]]
    elif grupo == "reservas":
        jogadores = [j for j in clube["elenco"] if j["id"] not in clube["titulares"]]
    else:
        jogadores = list(clube["elenco"])
    jogadores = [j for j in jogadores if disponivel(j)]
    if foco == "goleiros":
        return [j for j in jogadores if j["pos"] == "GOL"]
    if foco == "recuperacao":
        return jogadores
    return [j for j in jogadores if j["pos"] != "GOL"]


def chance_de_evolucao(jogador, intensidade):
    """
    Calcula a chance de um jogador melhorar 1 ponto no atributo treinado.

    Parte da chance da intensidade e multiplica por 1,5 para jovens de até 23 anos e por 0,6 para veteranos
    a partir de 31.

    Args:
        jogador (dict): Jogador que treina.
        intensidade (str): Chave da intensidade em INTENSIDADES_DE_TREINO.

    Returns:
        float: Chance de evolução, entre 0 e 1.
    """
    chance = INTENSIDADES_DE_TREINO[intensidade]["evolucao"]
    idade = jogador.get("idade", 26)
    if idade <= 23:
        chance *= 1.5
    elif idade >= 31:
        chance *= 0.6
    return chance


def treinar(estado, foco, intensidade, grupo):
    """
    Faz o treino da semana com o grupo, o foco e a intensidade escolhidos.

    Cada participante perde a energia da intensidade e fica com o foco do treino, que soma BONUS_TREINO (3) ao
    atributo treinado na próxima partida. Cada um tem chance_de_evolucao de ganhar +1 de vez no atributo (até
    99, com metade da chance a partir de 85); a cada EVOLUCOES_PARA_QUALIDADE (2) evoluções, a qualidade sobe
    1 (até 92), o que também valoriza o jogador. No treino pesado, cada um tem uma pequena chance de se
    lesionar por 1 rodada. O treino de recuperação devolve energia e não dá evolução. Só é possível treinar
    uma vez por etapa.

    Args:
        estado (dict): Estado atual da temporada.
        foco (str): Chave do foco em FOCOS_DE_TREINO.
        intensidade (str): Chave da intensidade em INTENSIDADES_DE_TREINO.
        grupo (str): "titulares", "reservas" ou "todos".

    Returns:
        dict: Resumo do treino, com participantes, quem evoluiu (jogador, atributo, novo valor e se a
            qualidade subiu), quem se lesionou e a energia gasta ou recuperada.
    """
    clube = estado["clubes"][estado["clube_id"]]
    participantes = grupo_de_treino(clube, grupo, foco)
    estado["treino_etapa"] = estado["etapa"]
    atributo = FOCOS_DE_TREINO[foco]["atributo"]
    resumo = {"participantes": participantes, "evoluiram": [], "lesionados": [], "energia": 0}
    if foco == "recuperacao":
        for jogador in participantes:
            jogador["energia"] = min(100, jogador["energia"] + 15)
        resumo["energia"] = 15
        return resumo
    dados = INTENSIDADES_DE_TREINO[intensidade]
    resumo["energia"] = -dados["energia"]
    for jogador in participantes:
        jogador["energia"] = max(0, jogador["energia"] - dados["energia"])
        jogador["treino_foco"] = atributo
        chance = chance_de_evolucao(jogador, intensidade)
        if jogador[atributo] >= 85:
            chance /= 2
        if jogador[atributo] < 99 and random.random() < chance:
            jogador[atributo] += 1
            jogador["evolucoes"] = jogador.get("evolucoes", 0) + 1
            subiu = jogador["evolucoes"] % EVOLUCOES_PARA_QUALIDADE == 0 and jogador["qualidade"] < 92
            if subiu:
                jogador["qualidade"] = limitar(jogador["qualidade"] + 1, 40, 92)
            resumo["evoluiram"].append((jogador, atributo, jogador[atributo], subiu))
        if random.random() < dados["lesao"]:
            jogador["lesao"] = max(jogador["lesao"], 1)
            resumo["lesionados"].append(jogador)
    return resumo
