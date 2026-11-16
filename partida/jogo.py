import random

from config import ACRESCIMOS, MINUTOS_POR_LANCE
from elenco.escalacao import rotulo
from elenco.substituicoes import aplicar_desgaste
from partida.jogadas import CHANCE_JOGADA_ESPECIAL, jogada_especial, sortear_acontecimento
from partida.lances import (
    PESOS_PORTADOR,
    disputa_de_penaltis,
    disputar_meio,
    entregar_bola,
    escolher_jogador,
    invalidar_setores,
    jogar_posse,
    mover_bola,
    pausar_todos,
    placar,
    registrar,
    resultado_da_partida,
    sortear_eventos_do_lance,
)


def jogar_lance(partida):
    """
    Simula um lance da partida, da disputa no meio-campo até o fim da jogada.

    Aplica o desgaste e os ajustes dos controles nos dois times, sorteia os eventos do lance e os
    acontecimentos extras, e disputa a bola no meio. Se ninguém ganha, narra a bola saindo. Se alguém ganha,
    em CHANCE_JOGADA_ESPECIAL (24%) dos lances o time ganha uma jogada especial (tiro de meta, lateral, falta,
    arrancada, pressão na saída e outras); no resto, joga uma posse normal. Se a jogada terminar em
    contra-ataque, o outro time joga uma posse de contra-ataque.

    Args:
        partida (dict): Estado da partida.
    """
    for time_id in (partida["casa"], partida["fora"]):
        aplicar_desgaste(partida["times"][time_id])
        partida["controles"][time_id]["ajuste"](partida, time_id)
    invalidar_setores(partida)
    sortear_eventos_do_lance(partida)
    sortear_acontecimento(partida)
    mover_bola(partida, None, "meio", 1)
    vencedor = disputar_meio(partida)
    if vencedor is None:
        lateral = random.choice((partida["casa"], partida["fora"]))
        registrar(partida, "meio_nada", {"time": partida["times"][lateral]["nome"]}, tipo="meio")
        return
    portador = escolher_jogador(partida["times"][vencedor], PESOS_PORTADOR["meio"])
    entregar_bola(partida, vencedor, "meio", None, portador)
    if random.random() < CHANCE_JOGADA_ESPECIAL:
        proximo = jogada_especial(partida, vencedor, portador)
    else:
        registrar(
            partida,
            "meio_ganhou",
            {"time": partida["times"][vencedor]["nome"], "jogador": rotulo(portador)},
            tipo="meio",
            time_id=vencedor,
        )
        proximo = jogar_posse(partida, vencedor, portador=portador)
    if proximo:
        jogar_posse(partida, proximo[0], contra_ataque=True, portador=proximo[1])


def jogar_partida(partida, controles, exibir=None, mata_mata=False):
    """
    Joga a partida inteira, do apito inicial ao resultado.

    Configura os controles e a exibição, narra o início e a chuva, e joga os dois tempos lance a lance,
    avançando o relógio a cada lance até o limite de 45 minutos mais os acréscimos sorteados. No intervalo,
    pausa os dois times. Em jogos de mata-mata que terminam empatados, decide nos pênaltis.

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
