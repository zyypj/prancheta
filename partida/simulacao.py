import random

from elenco.escalacao import limitar, rotulo
from elenco.substituicoes import melhor_substituto, pode_substituir
from partida.lances import CANTOS, FORCAS_PENALTI, criar_partida, fazer_substituicao, goleiro_de, jogar_partida

SUBSTITUICOES_IA = 3


def escolher_ponderado(pesos):
    opcoes = list(pesos)
    return random.choices(opcoes, weights=[max(0.1, pesos[opcao]) for opcao in opcoes])[0]


def ia_ataque(partida, time_id, zona, portador):
    plano = partida["times"][time_id]["plano"]
    ofensividade = plano["ofensividade"]
    if zona == "meio":
        direto = 2.5 if plano["estilo"] == "jogo direto" else 0
        return escolher_ponderado({
            "tocar": 7 - ofensividade,
            "enfiar": 0.4 + 0.3 * ofensividade,
            "driblar": 0.6 * ofensividade,
            "lancar": 0.5 + 0.4 * ofensividade + direto,
            "abrir": 2,
        })
    if zona == "ataque":
        na_ponta = partida["bola"]["faixa"] != 1
        return escolher_ponderado({
            "tocar": 4.5 - ofensividade,
            "tabelar": 1.5,
            "driblar": 0.5 * ofensividade,
            "cruzar": 3.5 if na_ponta else 1,
            "chutar": 0.6 * ofensividade,
        })
    return escolher_ponderado({"chutar": 2.5 + 0.6 * ofensividade, "driblar": 0.6 * ofensividade, "tocar": 1.2})


def ia_defesa(partida, time_id):
    plano = partida["times"][time_id]["plano"]
    return escolher_ponderado({
        "bote": plano["intensidade"],
        "pressao": 0.5 * plano["intensidade"] + (1 if plano["ofensividade"] >= 4 else 0),
        "fechar": 3,
        "recuar": 5 - plano["ofensividade"],
        "falta": 0.3,
    })


def ia_escolha(partida, time_id, pergunta, opcoes):
    return random.choices([chave for chave, _, _ in opcoes], weights=[peso for _, _, peso in opcoes])[0]


def ia_bater_penalti(partida, time_id, batedor, goleiro):
    return random.choices(CANTOS, weights=(0.42, 0.16, 0.42))[0], random.choice(FORCAS_PENALTI)


def ia_defender_penalti(partida, time_id, batedor, goleiro):
    return random.choices(CANTOS, weights=(0.45, 0.10, 0.45))[0]


def ia_lesao(partida, time_id, lesionado):
    time = partida["times"][time_id]
    if pode_substituir(time):
        entra = melhor_substituto(time, lesionado["pos"])
        if entra:
            fazer_substituicao(partida, time_id, None, entra["id"], rotulo(lesionado))


def ajustar_ofensividade(partida, time_id):
    time = partida["times"][time_id]
    adversario = partida["times"][partida["fora"] if time_id == partida["casa"] else partida["casa"]]
    diferenca = time["gols"] - adversario["gols"]
    base = time["ofensividade_base"]
    if diferenca < 0:
        time["plano"]["ofensividade"] = min(5, base + 1)
    elif diferenca > 0 and partida["minuto"] >= 75:
        time["plano"]["ofensividade"] = max(1, base - 1)
    else:
        time["plano"]["ofensividade"] = base


def trocar_cansados(partida, time_id, limite_energia, quantidade):
    time = partida["times"][time_id]
    cansados = sorted([j for j in time["em_campo"] if j["pos"] != "GOL" and j["energia"] < limite_energia],
                      key=lambda j: j["energia"])
    for jogador in cansados[:quantidade]:
        if time["subs"] >= SUBSTITUICOES_IA or not pode_substituir(time):
            return
        entra = melhor_substituto(time, jogador["pos"])
        if entra:
            fazer_substituicao(partida, time_id, jogador["id"], entra["id"])


def ia_pausa(partida, time_id, motivo):
    time = partida["times"][time_id]
    if motivo == "expulsao" and goleiro_de(time) is None and pode_substituir(time):
        reserva = next((j for j in time["banco"] if j["pos"] == "GOL"), None)
        linha = [j for j in time["em_campo"] if j["pos"] != "GOL"]
        if reserva and linha:
            fazer_substituicao(partida, time_id, min(linha, key=lambda j: j["qualidade"])["id"], reserva["id"])
    if motivo == "intervalo":
        trocar_cansados(partida, time_id, 60, 2)
        ajustar_ofensividade(partida, time_id)


def ia_ajuste(partida, time_id):
    if partida["minuto"] >= 60:
        trocar_cansados(partida, time_id, 45, 1)
    if partida["minuto"] >= 70:
        ajustar_ofensividade(partida, time_id)


CONTROLE_IA = {
    "ataque": ia_ataque,
    "defesa": ia_defesa,
    "escolha": ia_escolha,
    "bater_penalti": ia_bater_penalti,
    "defender_penalti": ia_defender_penalti,
    "lesao": ia_lesao,
    "pausa": ia_pausa,
    "ajuste": ia_ajuste,
}


def plano_ia(clube, adversario, em_casa):
    plano = dict(clube["plano"])
    diferenca = clube["forca"] - adversario["forca"]
    ofensividade = plano["ofensividade"] + (1 if em_casa else 0) + (1 if diferenca > 8 else 0) - (
        1 if diferenca < -8 else 0)
    plano["ofensividade"] = int(limitar(ofensividade, 1, 5))
    return plano


def simular_partida(clube_casa, clube_fora, frases, neutro=False, mata_mata=False):
    partida = criar_partida(
        clube_casa,
        clube_fora,
        frases,
        plano_ia(clube_casa, clube_fora, not neutro),
        plano_ia(clube_fora, clube_casa, False),
        neutro,
    )
    return jogar_partida(partida, {clube_casa["id"]: CONTROLE_IA, clube_fora["id"]: CONTROLE_IA}, mata_mata=mata_mata)
