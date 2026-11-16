import random

from config import ACRESCIMOS, MANDO_DE_CAMPO, MAX_SUBSTITUICOES, MINUTOS_POR_LANCE
from elenco.escalacao import atributo_efetivo, disponivel, forca_setores, limitar
from elenco.substituicoes import aplicar_desgaste, marcar_desfalques, registrar_amarelo, substituir
from partida.narracao import narrar

ACOES = {"meio": ("tocar", "driblar", "lancar"), "ataque": ("chutar", "driblar", "cruzar", "tocar")}
NOMES_ACOES = {"tocar": "Tocar", "driblar": "Driblar", "lancar": "Lançar", "chutar": "Chutar", "cruzar": "Cruzar"}
DEFESAS = ("bote", "fechar", "recuar")
NOMES_DEFESAS = {"bote": "Dar o bote", "fechar": "Fechar espaço", "recuar": "Recuar a linha"}
CANTOS = ("esquerda", "meio", "direita")
FORCAS_PENALTI = ("colocado", "forte")

CHANCE_BASE = {
    "meio": {"tocar": 0.80, "driblar": 0.55, "lancar": 0.45},
    "ataque": {"driblar": 0.45, "cruzar": 0.55, "tocar": 0.75},
}
BASE_FINALIZACAO = {"chute": 0.26, "cara": 0.48, "cabeceio": 0.24, "falta": 0.12, "escanteio": 0.16, "contra": 0.34}
PESO_DIFERENCA = 0.004
PESO_MEIO = 0.006
PESO_FINALIZACAO = 0.003
PESOS_PORTADOR = {"meio": {"MEI": 5, "DEF": 1, "ATA": 2}, "ataque": {"ATA": 5, "MEI": 3, "DEF": 0.5}}
PESOS_MARCADOR = {"meio": {"MEI": 5, "DEF": 2, "ATA": 1}, "ataque": {"DEF": 5, "MEI": 2}}
PESOS_CABECEIO = {"ATA": 5, "DEF": 2, "MEI": 1}


def montar_time(clube, plano, em_casa):
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


def criar_partida(clube_casa, clube_fora, frases, plano_casa=None, plano_fora=None):
    return {
        "casa": clube_casa["id"],
        "fora": clube_fora["id"],
        "times": {
            clube_casa["id"]: montar_time(clube_casa, plano_casa or clube_casa["plano"], True),
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
    }


def outro(partida, time_id):
    return partida["fora"] if time_id == partida["casa"] else partida["casa"]


def placar(partida):
    casa = partida["times"][partida["casa"]]
    fora = partida["times"][partida["fora"]]
    return f"{casa['sigla']} {casa['gols']} x {fora['gols']} {fora['sigla']}"


def minuto_texto(partida):
    base = 45 if partida["tempo"] == 1 else 90
    if partida["minuto"] > base:
        return f"{base}+{partida['minuto'] - base}'"
    return f"{partida['minuto']}'"


def mover_bola(partida, time_id, zona):
    partida["bola"] = {"time": time_id, "zona": zona, "faixa": random.randint(0, 2)}


def registrar(partida, chave, dados=None, tipo="lance", time_id=None):
    texto = narrar(partida["frases"], chave, dados)
    partida["narracao"] = (partida["narracao"] + [f"{minuto_texto(partida)} {texto}"])[-5:]
    if partida["exibir"]:
        partida["exibir"](partida, {"texto": texto, "tipo": tipo, "time": time_id})
    return texto


def anotar_sumula(partida, texto):
    partida["sumula"].append(f"{minuto_texto(partida)} {texto}")


def goleiro_de(time):
    return next((jogador for jogador in time["em_campo"] if jogador["pos"] == "GOL"), None)


def escolher_jogador(time, pesos, excluir=None):
    candidatos = [jogador for jogador in time["em_campo"] if jogador is not excluir and pesos.get(jogador["pos"], 0) > 0]
    if not candidatos:
        candidatos = [jogador for jogador in time["em_campo"] if jogador is not excluir] or time["em_campo"]
    return random.choices(candidatos, weights=[pesos.get(jogador["pos"], 0.5) or 0.5 for jogador in candidatos])[0]


def melhor_batedor(time):
    linha = [jogador for jogador in time["em_campo"] if jogador["pos"] != "GOL"] or time["em_campo"]
    return max(linha, key=lambda jogador: atributo_efetivo(jogador, "fin"))


def invalidar_setores(partida):
    partida["cache_setores"] = {}


def setores(partida, time_id):
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
        nome_sai, entra = troca[0]["nome"], troca[1]
    invalidar_setores(partida)
    registrar(partida, "substituicao", {"time": time["nome"], "sai": nome_sai, "entra": entra["nome"]}, tipo="substituicao", time_id=time_id)
    anotar_sumula(partida, f"Substituição ({time['sigla']}): sai {nome_sai}, entra {entra['nome']}")
    return True


def pausar_todos(partida, motivo):
    for time_id in (partida["casa"], partida["fora"]):
        partida["controles"][time_id]["pausa"](partida, time_id, motivo)


def expulsar(partida, time_id, jogador, chave):
    time = partida["times"][time_id]
    if jogador in time["em_campo"]:
        time["em_campo"].remove(jogador)
        time["saiu"].append(jogador)
    time["vermelhos"] += 1
    jogador["suspenso"] = max(jogador["suspenso"], 1)
    invalidar_setores(partida)
    registrar(partida, chave, {"jogador": jogador["nome"]}, tipo="vermelho", time_id=time_id)
    anotar_sumula(partida, f"Vermelho — {jogador['nome']} ({time['sigla']})")
    pausar_todos(partida, "expulsao")


def amarelar(partida, time_id, jogador):
    time = partida["times"][time_id]
    if jogador["id"] in time["amarelados"]:
        expulsar(partida, time_id, jogador, "segundo_amarelo")
        return
    time["amarelados"].append(jogador["id"])
    suspenso = registrar_amarelo(jogador)
    registrar(partida, "amarelo", {"jogador": jogador["nome"]}, tipo="amarelo", time_id=time_id)
    aviso = " (3º amarelo, suspenso na próxima rodada)" if suspenso else ""
    anotar_sumula(partida, f"Amarelo — {jogador['nome']} ({time['sigla']}){aviso}")


def lesionar(partida, time_id, jogador):
    time = partida["times"][time_id]
    jogador["lesao"] = random.randint(1, 3)
    time["em_campo"].remove(jogador)
    time["saiu"].append(jogador)
    invalidar_setores(partida)
    registrar(partida, "lesao", {"jogador": jogador["nome"]}, tipo="lesao", time_id=time_id)
    anotar_sumula(partida, f"Lesão — {jogador['nome']} ({time['sigla']}), fora por {jogador['lesao']} rodada(s)")
    partida["controles"][time_id]["lesao"](partida, time_id, jogador)


def sortear_eventos_do_lance(partida):
    if partida["torcida"] > 0:
        partida["torcida"] -= 1
    elif random.random() < 0.03:
        partida["torcida"] = 3
        invalidar_setores(partida)
        registrar(partida, "torcida", {"time": partida["times"][partida["casa"]]["nome"]}, tipo="evento", time_id=partida["casa"])
    for time_id in (partida["casa"], partida["fora"]):
        if random.random() < 0.012:
            linha = [jogador for jogador in partida["times"][time_id]["em_campo"] if jogador["pos"] != "GOL"]
            if linha:
                lesionar(partida, time_id, random.choice(linha))


def disputar_meio(partida):
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


def chance_da_acao(partida, atacante_id, zona, acao, portador, marcador, defesa, bonus):
    defensor_id = outro(partida, atacante_id)
    atacante = partida["times"][atacante_id]
    defensor = partida["times"][defensor_id]
    forca_atq = setores(partida, atacante_id)
    forca_def = setores(partida, defensor_id)
    if acao in ("tocar", "lancar", "cruzar"):
        valor = atributo_efetivo(portador, "pas")
    else:
        valor = (atributo_efetivo(portador, "fin") + atributo_efetivo(portador, "fis") + atributo_efetivo(portador, "pas")) / 3
    oposicao = atributo_efetivo(marcador, "des")
    setor_atq = forca_atq["ataque"] if zona == "ataque" else forca_atq["meio"]
    setor_def = forca_def["defesa"] if zona == "ataque" else forca_def["meio"]
    diferenca = (valor - oposicao) * 0.4 + (setor_atq - setor_def) * 0.6
    chance = CHANCE_BASE[zona][acao] + diferenca * PESO_DIFERENCA + bonus
    chance += (atacante["plano"]["ofensividade"] - 3) * 0.02
    chance += (defensor["plano"]["ofensividade"] - 3) * 0.02
    chance -= (defensor["plano"]["intensidade"] - 3) * 0.015
    chance += {"bote": -0.07, "fechar": -0.03, "recuar": 0.04}[defesa]
    if partida["chuva"] and acao in ("tocar", "lancar", "cruzar"):
        chance -= 0.06
    return limitar(chance, 0.05, 0.95)


def chance_de_falta(plano_defensor, defesa, acao):
    chance = 0.05 + (plano_defensor["intensidade"] - 3) * 0.015
    if defesa == "bote":
        chance += 0.05
    if acao == "driblar":
        chance += 0.03
    return chance


def marcar_gol(partida, atacante_id, autor):
    time = partida["times"][atacante_id]
    time["gols"] += 1
    mover_bola(partida, atacante_id, "gol")
    registrar(partida, "gol", {"jogador": autor["nome"], "time": time["nome"], "placar": placar(partida)}, tipo="gol", time_id=atacante_id)
    if random.random() < 0.04:
        time["gols"] -= 1
        registrar(partida, "var", tipo="var", time_id=atacante_id)
        anotar_sumula(partida, f"Gol anulado pelo VAR — {autor['nome']} ({time['sigla']})")
        return False
    autor["gols"] += 1
    anotar_sumula(partida, f"GOL — {autor['nome']} ({time['sigla']})")
    return True


def finalizar(partida, atacante_id, finalizador, tipo, bonus=0.0, defesa="fechar", pode_escanteio=True):
    atacante = partida["times"][atacante_id]
    defensor = partida["times"][outro(partida, atacante_id)]
    goleiro = goleiro_de(defensor)
    reflexo = atributo_efetivo(goleiro, "ref") if goleiro else 30
    chave = {"chute": "chute", "cara": "cara", "cabeceio": "cabeceio", "falta": "chute", "escanteio": "cabeceio", "contra": "cara"}[tipo]
    mover_bola(partida, atacante_id, "ataque")
    registrar(partida, chave, {"jogador": finalizador["nome"]}, tipo="chute", time_id=atacante_id)
    chance = BASE_FINALIZACAO[tipo] + (atributo_efetivo(finalizador, "fin") - reflexo) * PESO_FINALIZACAO + bonus * 0.5
    if defesa == "recuar" and tipo in ("chute", "cara", "contra"):
        chance -= 0.06
    if atacante["plano"]["estilo"] == "jogo direto":
        chance -= 0.03
    chance = limitar(chance, 0.03, 0.75)
    atacante["chutes"] += 1
    sorteio = random.random()
    if sorteio < chance:
        atacante["no_alvo"] += 1
        marcar_gol(partida, atacante_id, finalizador)
        return
    if sorteio < chance + (1 - chance) * 0.45:
        atacante["no_alvo"] += 1
        nome_goleiro = goleiro["nome"] if goleiro else "o zagueiro improvisado"
        registrar(partida, "defesa", {"goleiro": nome_goleiro}, tipo="defesa", time_id=atacante_id)
        if pode_escanteio and random.random() < 0.35:
            cobrar_escanteio(partida, atacante_id, defesa)
        return
    registrar(partida, "fora", {"jogador": finalizador["nome"]}, tipo="fora", time_id=atacante_id)


def cobrar_escanteio(partida, atacante_id, defesa):
    time = partida["times"][atacante_id]
    registrar(partida, "escanteio", {"time": time["nome"]}, tipo="bola_parada", time_id=atacante_id)
    if random.random() < 0.45:
        finalizar(partida, atacante_id, escolher_jogador(time, PESOS_CABECEIO), "escanteio", defesa=defesa, pode_escanteio=False)


def cobrar_falta(partida, atacante_id, defesa):
    time = partida["times"][atacante_id]
    registrar(partida, "falta_perigosa", {"time": time["nome"]}, tipo="bola_parada", time_id=atacante_id)
    batedor = melhor_batedor(time)
    escolha = partida["controles"][atacante_id]["falta"](partida, atacante_id, batedor)
    if escolha == "direto":
        finalizar(partida, atacante_id, batedor, "falta", defesa=defesa)
        return
    registrar(partida, "cruzar_ok", {"jogador": batedor["nome"]}, time_id=atacante_id)
    if random.random() < 0.55:
        finalizar(partida, atacante_id, escolher_jogador(time, PESOS_CABECEIO, excluir=batedor), "cabeceio", defesa=defesa, pode_escanteio=False)
    else:
        registrar(partida, "cruzar_erro", {"jogador": batedor["nome"], "marcador": "a defesa"}, time_id=atacante_id)


def cobrar_penalti(partida, atacante_id):
    defensor_id = outro(partida, atacante_id)
    atacante = partida["times"][atacante_id]
    goleiro = goleiro_de(partida["times"][defensor_id])
    batedor = melhor_batedor(atacante)
    mover_bola(partida, atacante_id, "ataque")
    registrar(partida, "penalti", {"time": atacante["nome"], "jogador": batedor["nome"]}, tipo="penalti", time_id=atacante_id)
    canto, forca = partida["controles"][atacante_id]["bater_penalti"](partida, atacante_id, batedor, goleiro)
    pulo = partida["controles"][defensor_id]["defender_penalti"](partida, defensor_id, batedor, goleiro)
    partida["ultimo_penalti"] = {"time": atacante_id, "canto": canto, "forca": forca, "pulo": pulo}
    finalizacao = atributo_efetivo(batedor, "fin")
    chance_fora = (0.04 if forca == "colocado" else 0.14) + max(0, 70 - finalizacao) * 0.002
    atacante["chutes"] += 1
    if random.random() < chance_fora:
        registrar(partida, "penalti_fora", {"jogador": batedor["nome"]}, tipo="penalti_fim", time_id=atacante_id)
        anotar_sumula(partida, f"Pênalti perdido — {batedor['nome']} ({atacante['sigla']})")
        return
    atacante["no_alvo"] += 1
    if canto == pulo:
        defende = 0.80 if canto == "meio" else (0.55 if forca == "colocado" else 0.30)
        reflexo = atributo_efetivo(goleiro, "ref") if goleiro else 30
        defende += (reflexo - finalizacao) * 0.004
        if random.random() < limitar(defende, 0.1, 0.9):
            nome_goleiro = goleiro["nome"] if goleiro else "o goleiro improvisado"
            registrar(partida, "penalti_defesa", {"goleiro": nome_goleiro}, tipo="penalti_fim", time_id=atacante_id)
            anotar_sumula(partida, f"Pênalti defendido — {nome_goleiro}")
            return
    atacante["gols"] += 1
    batedor["gols"] += 1
    mover_bola(partida, atacante_id, "gol")
    registrar(partida, "penalti_gol", {"jogador": batedor["nome"], "placar": placar(partida)}, tipo="gol", time_id=atacante_id)
    anotar_sumula(partida, f"GOL (pênalti) — {batedor['nome']} ({atacante['sigla']})")


def cometer_falta(partida, atacante_id, zona, acao, portador, marcador, defesa):
    defensor_id = outro(partida, atacante_id)
    partida["times"][defensor_id]["faltas"] += 1
    registrar(partida, "falta", {"marcador": marcador["nome"], "jogador": portador["nome"]}, tipo="falta", time_id=defensor_id)
    sorteio = random.random()
    if sorteio < 0.025:
        expulsar(partida, defensor_id, marcador, "vermelho")
    elif sorteio < 0.22 + (0.08 if defesa == "bote" else 0):
        amarelar(partida, defensor_id, marcador)
    if zona == "ataque":
        if acao == "driblar" and random.random() < 0.40:
            return "penalti"
        return "perigosa"
    return "meio"


def jogar_posse(partida, atacante_id, contra_ataque=False):
    defensor_id = outro(partida, atacante_id)
    atacante = partida["times"][atacante_id]
    defensor = partida["times"][defensor_id]
    controles = partida["controles"]
    atacante["posse"] += 1
    zona = "meio"
    bonus = 0.0
    if contra_ataque:
        zona = "ataque"
        bonus = 0.08
    elif atacante["plano"]["estilo"] == "jogo direto" and random.random() < 0.40:
        zona = "ataque"
        bonus = -0.03
    defesa = controles[defensor_id]["defesa"](partida, defensor_id)
    if defesa not in DEFESAS:
        defesa = "fechar"
    for passo in range(5):
        portador = escolher_jogador(atacante, PESOS_PORTADOR[zona])
        partida["portador"] = portador
        mover_bola(partida, atacante_id, zona)
        if contra_ataque and passo == 0:
            registrar(partida, "contra_ataque", {"time": atacante["nome"], "jogador": portador["nome"]}, time_id=atacante_id)
        if zona == "ataque" and passo == 4:
            acao = "chutar"
        else:
            acao = controles[atacante_id]["ataque"](partida, atacante_id, zona, portador)
        if acao not in ACOES[zona]:
            acao = ACOES[zona][0]
        marcador = escolher_jogador(defensor, PESOS_MARCADOR[zona])
        if acao == "chutar":
            finalizar(partida, atacante_id, portador, "contra" if contra_ataque else "chute", bonus, defesa)
            return None
        if random.random() < chance_de_falta(defensor["plano"], defesa, acao):
            desfecho = cometer_falta(partida, atacante_id, zona, acao, portador, marcador, defesa)
            if desfecho == "penalti":
                cobrar_penalti(partida, atacante_id)
                return None
            if desfecho == "perigosa":
                cobrar_falta(partida, atacante_id, defesa)
                return None
            continue
        dados = {"jogador": portador["nome"], "marcador": marcador["nome"], "time": atacante["nome"]}
        if random.random() < chance_da_acao(partida, atacante_id, zona, acao, portador, marcador, defesa, bonus):
            if acao == "cruzar":
                registrar(partida, "cruzar_ok", dados, time_id=atacante_id)
                finalizar(partida, atacante_id, escolher_jogador(atacante, PESOS_CABECEIO, excluir=portador), "cabeceio", bonus, defesa)
                return None
            if acao == "driblar" and zona == "ataque":
                registrar(partida, "driblar_ok", dados, time_id=atacante_id)
                finalizar(partida, atacante_id, portador, "cara", bonus, defesa)
                return None
            registrar(partida, f"{acao}_ok", dados, time_id=atacante_id)
            if zona == "meio":
                if acao == "tocar" and random.random() < 0.45:
                    bonus += 0.02
                    continue
                if acao == "lancar":
                    bonus += 0.05
                zona = "ataque"
            else:
                bonus += 0.04
            continue
        registrar(partida, f"{acao}_erro", dados, tipo="perda", time_id=atacante_id)
        if acao == "cruzar" and random.random() < 0.3:
            cobrar_escanteio(partida, atacante_id, defesa)
            return None
        if defesa == "recuar" and zona == "ataque" and random.random() < 0.25:
            cobrar_escanteio(partida, atacante_id, defesa)
            return None
        if random.random() < 0.5:
            registrar(partida, f"{defesa}_ok", {"marcador": marcador["nome"], "time": defensor["nome"]}, tipo="recuperacao", time_id=defensor_id)
        if defensor["plano"]["estilo"] == "contra-ataque" and atacante["plano"]["ofensividade"] >= 4 and random.random() < 0.5:
            return defensor_id
        if random.random() < 0.10:
            return defensor_id
        return None
    registrar(partida, "tocar_erro", {"jogador": partida["portador"]["nome"], "marcador": "a defesa"}, tipo="perda", time_id=atacante_id)
    return None


def jogar_lance(partida):
    for time_id in (partida["casa"], partida["fora"]):
        aplicar_desgaste(partida["times"][time_id])
        partida["controles"][time_id]["ajuste"](partida, time_id)
    invalidar_setores(partida)
    sortear_eventos_do_lance(partida)
    mover_bola(partida, None, "meio")
    vencedor = disputar_meio(partida)
    if vencedor is None:
        lateral = random.choice((partida["casa"], partida["fora"]))
        registrar(partida, "meio_nada", {"time": partida["times"][lateral]["nome"]}, tipo="meio")
        return
    portador = escolher_jogador(partida["times"][vencedor], PESOS_PORTADOR["meio"])
    partida["portador"] = portador
    mover_bola(partida, vencedor, "meio")
    registrar(partida, "meio_ganhou", {"time": partida["times"][vencedor]["nome"], "jogador": portador["nome"]}, tipo="meio", time_id=vencedor)
    proximo = jogar_posse(partida, vencedor)
    if proximo:
        jogar_posse(partida, proximo, contra_ataque=True)


def resultado_da_partida(partida):
    casa = partida["times"][partida["casa"]]
    fora = partida["times"][partida["fora"]]
    total_posse = max(1, casa["posse"] + fora["posse"])
    return {
        "mandante": partida["casa"],
        "visitante": partida["fora"],
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


def jogar_partida(partida, controles, exibir=None):
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
    partida["encerrada"] = True
    registrar(partida, "fim", {"placar": placar(partida)}, tipo="fim")
    return resultado_da_partida(partida)
