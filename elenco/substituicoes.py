import random

from config import LIMITE_AMARELOS, MAX_SUBSTITUICOES, RECUPERACAO_ENERGIA
from elenco.escalacao import valor_para_escalar


def pode_substituir(time):
    return time["subs"] < MAX_SUBSTITUICOES and len(time["banco"]) > 0


def substituir(time, sai_id, entra_id):
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
    mesma = [jogador for jogador in time["banco"] if jogador["pos"] == posicao]
    candidatos = mesma or [jogador for jogador in time["banco"] if jogador["pos"] != "GOL"]
    if not candidatos:
        return None
    return max(candidatos, key=valor_para_escalar)


def aplicar_desgaste(time):
    intensidade = time["plano"]["intensidade"]
    for jogador in time["em_campo"]:
        perda = 1.6 + (intensidade - 3) * 0.5 + random.random() * 0.8
        if jogador["pos"] == "GOL":
            perda *= 0.3
        jogador["energia"] = max(0, round(jogador["energia"] - perda, 1))


def registrar_amarelo(jogador):
    jogador["amarelos"] += 1
    if jogador["amarelos"] >= LIMITE_AMARELOS:
        jogador["amarelos"] = 0
        jogador["suspenso"] = 1
        return True
    return False


def marcar_desfalques(elenco):
    for jogador in elenco:
        jogador["desfalque"] = jogador["lesao"] > 0 or jogador["suspenso"] > 0


def preparar_proxima_rodada(elenco):
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
