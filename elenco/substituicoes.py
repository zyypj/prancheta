import random

from config import LIMITE_AMARELOS, MAX_SUBSTITUICOES, RECUPERACAO_ENERGIA
from elenco.escalacao import valor_para_escalar


def pode_substituir(time):
    """
    Verifica se o time ainda pode fazer uma substituição.

    Args:
        time (dict): Time na partida.

    Returns:
        bool: True se o time não atingiu o limite de substituições e ainda tem jogadores no banco.
    """
    return time["subs"] < MAX_SUBSTITUICOES and len(time["banco"]) > 0


def substituir(time, sai_id, entra_id):
    """
    Troca um jogador em campo por um do banco.

    O jogador que entra ocupa a mesma posição na lista de quem está em campo, sai do banco, e o que sai vai para a lista dos que deixaram o jogo. O contador de substituições do time aumenta em um. Nada muda se o limite de substituições já foi atingido ou se algum dos jogadores não for encontrado.

    Args:
        time (dict): Time na partida.
        sai_id (str): Identificador do jogador que sai de campo.
        entra_id (str): Identificador do jogador do banco que entra.

    Returns:
        tuple | None: Par (jogador que sai, jogador que entra), ou None se a troca não foi feita.
    """
    if time["subs"] >= MAX_SUBSTITUICOES:
        return None
    sai = next((jogador for jogador in time["em_campo"] if jogador["id"] == sai_id), None)
    entra = next((jogador for jogador in time["banco"] if jogador["id"] == entra_id), None)
    if sai is None or entra is None:
        return None
    time["em_campo"][time["em_campo"].index(sai)] = entra
    time["banco"].remove(entra)
    time["saiu"].append(sai)
    time["subs"] += 1
    return sai, entra


def melhor_substituto(time, posicao):
    """
    Escolhe o melhor reserva do banco para uma posição.

    Dá preferência aos reservas da mesma posição. Se não houver nenhum, considera os reservas de linha, deixando os goleiros de fora. Entre os candidatos, vence o de maior valor para escalar, que leva em conta qualidade, grande fase e energia.

    Args:
        time (dict): Time na partida.
        posicao (str): Posição a ser reposta ("GOL", "DEF", "MEI" ou "ATA").

    Returns:
        dict | None: Jogador escolhido, ou None se não houver candidato no banco.
    """
    mesma = [jogador for jogador in time["banco"] if jogador["pos"] == posicao]
    candidatos = mesma or [jogador for jogador in time["banco"] if jogador["pos"] != "GOL"]
    if not candidatos:
        return None
    return max(candidatos, key=valor_para_escalar)


def aplicar_desgaste(time):
    """
    Reduz a energia dos jogadores em campo após um lance.

    Cada jogador perde 1,6 ponto de energia, mais 0,5 por nível de intensidade do plano acima de 3 (ou menos, abaixo de 3), mais um acréscimo aleatório de até 0,8. Goleiros perdem só 30% desse valor. A energia não fica abaixo de zero e é arredondada em uma casa decimal.

    Args:
        time (dict): Time na partida.
    """
    intensidade = time["plano"]["intensidade"]
    for jogador in time["em_campo"]:
        perda = 1.6 + (intensidade - 3) * 0.5 + random.random() * 0.8
        if jogador["pos"] == "GOL":
            perda *= 0.3
        jogador["energia"] = max(0, round(jogador["energia"] - perda, 1))


def registrar_amarelo(jogador):
    """
    Soma um cartão amarelo ao acumulado do jogador.

    Ao atingir o limite de amarelos, o acumulado volta a zero e o jogador fica suspenso por uma rodada.

    Args:
        jogador (dict): Jogador que recebeu o cartão.

    Returns:
        bool: True se o cartão gerou suspensão, False caso contrário.
    """
    jogador["amarelos"] += 1
    if jogador["amarelos"] >= LIMITE_AMARELOS:
        jogador["amarelos"] = 0
        jogador["suspenso"] = 1
        return True
    return False


def marcar_desfalques(elenco):
    """
    Marca como desfalque os jogadores lesionados ou suspensos.

    Args:
        elenco (list[dict]): Jogadores do clube.
    """
    for jogador in elenco:
        jogador["desfalque"] = jogador["lesao"] > 0 or jogador["suspenso"] > 0


def preparar_proxima_rodada(elenco):
    """
    Atualiza o elenco para a rodada seguinte.

    Jogadores marcados como desfalque cumprem uma rodada de suspensão e de lesão, e a marca de desfalque é retirada de todos. A grande fase diminui em uma rodada e a energia de cada jogador recupera um valor fixo, sem passar de 100.

    Args:
        elenco (list[dict]): Jogadores do clube.
    """
    for jogador in elenco:
        if jogador.get("desfalque"):
            if jogador["suspenso"] > 0:
                jogador["suspenso"] -= 1
            if jogador["lesao"] > 0:
                jogador["lesao"] -= 1
        jogador["desfalque"] = False
        if jogador["fase"] > 0:
            jogador["fase"] -= 1
        jogador["energia"] = min(100, round(jogador["energia"] + RECUPERACAO_ENERGIA, 1))
