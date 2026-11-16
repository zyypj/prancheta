import random

from config import ACRESCIMOS, MANDO_DE_CAMPO, MAX_SUBSTITUICOES, MINUTOS_POR_LANCE
from elenco.escalacao import atributo_efetivo, disponivel, forca_setores, limitar
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
        "ultimo_local": None,
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


def mover_bola(partida, time_id, zona, faixa=None):
    partida["bola"] = {"time": time_id, "zona": zona, "faixa": random.randint(0, 2) if faixa is None else faixa}


def entregar_bola(partida, time_id, zona, faixa, portador):
    partida["portador"] = portador
    mover_bola(partida, time_id, zona, faixa)


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


def perguntar(partida, time_id, pergunta, opcoes):
    escolha = partida["controles"][time_id]["escolha"](partida, time_id, pergunta, opcoes)
    chaves = [chave for chave, _, _ in opcoes]
    return escolha if escolha in chaves else chaves[0]


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


def tirar_de_campo(partida, time_id, jogador, chave, rodadas):
    time = partida["times"][time_id]
    jogador["lesao"] = rodadas
    time["em_campo"].remove(jogador)
    time["saiu"].append(jogador)
    invalidar_setores(partida)
    registrar(partida, chave, {"jogador": jogador["nome"]}, tipo="lesao", time_id=time_id)
    if rodadas:
        anotar_sumula(partida, f"Lesão — {jogador['nome']} ({time['sigla']}), fora por {rodadas} rodada(s)")
    else:
        anotar_sumula(partida, f"Câimbra — {jogador['nome']} ({time['sigla']}) deixa o campo")
    partida["controles"][time_id]["lesao"](partida, time_id, jogador)


def sortear_eventos_do_lance(partida):
    if partida["torcida"] > 0:
        partida["torcida"] -= 1
    elif random.random() < 0.03:
        partida["torcida"] = 3
        invalidar_setores(partida)
        registrar(partida, "torcida", {"time": partida["times"][partida["casa"]]["nome"]}, tipo="evento", time_id=partida["casa"])
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
    if acao == "driblar":
        if drible == "arrancada":
            return atributo_efetivo(portador, "fis")
        return (atributo_efetivo(portador, "fin") + atributo_efetivo(portador, "pas") + atributo_efetivo(portador, "fis")) / 3
    return atributo_efetivo(portador, "pas")


def chance_da_acao(partida, atacante_id, zona, faixa, acao, portador, marcador, defesa, bonus, drible=None):
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
    diferenca = (valor_da_acao(portador, acao, drible) - atributo_efetivo(marcador, "des")) * 0.4 + (setor_atq - setor_def) * 0.6
    chance = base + diferenca * PESO_DIFERENCA + bonus
    chance += (atacante["plano"]["ofensividade"] - 3) * 0.02
    chance += (defensor["plano"]["ofensividade"] - 3) * 0.02
    chance -= (defensor["plano"]["intensidade"] - 3) * 0.015
    chance += EFEITO_DEFESA[defesa][zona]
    if partida["chuva"] and acao in ("tocar", "lancar", "cruzar", "enfiar", "abrir", "tabelar"):
        chance -= 0.06
    return limitar(chance, 0.05, 0.95)


def chance_de_falta(plano_defensor, defesa, acao, zona):
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
    time = partida["times"][atacante_id]
    time["gols"] += 1
    mover_bola(partida, atacante_id, "gol", 1)
    chave = "gol_contra" if contra else "gol"
    registrar(partida, chave, {"jogador": autor["nome"], "time": time["nome"], "placar": placar(partida)}, tipo="gol", time_id=atacante_id)
    if not contra and random.random() < 0.04:
        time["gols"] -= 1
        registrar(partida, "var", tipo="var", time_id=atacante_id)
        anotar_sumula(partida, f"Gol anulado pelo VAR — {autor['nome']} ({time['sigla']})")
        return False
    if contra:
        anotar_sumula(partida, f"GOL CONTRA — {autor['nome']} (a favor do {time['sigla']})")
    else:
        autor["gols"] += 1
        anotar_sumula(partida, f"GOL — {autor['nome']} ({time['sigla']})")
    return True


def escolher_chute(partida, atacante_id, finalizador, local):
    opcoes = []
    for chave, chute in CHUTES.items():
        peso = chute["peso"]
        if chave == "forte" and local in ("longe", "meio_campo"):
            peso += 2
        if chave == "cavadinha" and local == "cara":
            peso += 2
        opcoes.append((chave, chute["nome"], peso))
    return perguntar(partida, atacante_id, f"Como {finalizador['nome']} vai bater?", opcoes)


def finalizar(partida, atacante_id, finalizador, local, tipo="colocado", bonus=0.0, defesa="fechar", rebote=True, escanteio=True):
    atacante = partida["times"][atacante_id]
    defensor = partida["times"][outro(partida, atacante_id)]
    goleiro = goleiro_de(defensor)
    chute = CHUTES[tipo]
    partida["ultimo_local"] = local
    mover_bola(partida, atacante_id, "area" if local not in ("longe", "meio_campo", "falta") else "ataque")
    registrar(partida, f"chute_{local}", {"jogador": finalizador["nome"], "tipo": chute["texto"]}, tipo="chute", time_id=atacante_id)
    finalizacao = atributo_efetivo(finalizador, "fin")
    if local == "cabeceio":
        finalizacao = (finalizacao + atributo_efetivo(finalizador, "fis")) / 2
    alvo = chute["alvo"] + LOCAIS[local]["alvo"] + (finalizacao - 65) * 0.004 + bonus * 0.5
    if defesa == "recuar" and local in ("longe", "area", "cara"):
        alvo -= 0.06
    atacante["chutes"] += 1
    if random.random() >= limitar(alvo, 0.1, 0.95):
        if random.random() < 0.12:
            registrar(partida, "trave", {"jogador": finalizador["nome"]}, tipo="trave", time_id=atacante_id)
            if rebote and random.random() < 0.4:
                pegar_rebote(partida, atacante_id, defesa)
            return
        registrar(partida, "fora", {"jogador": finalizador["nome"]}, tipo="fora", time_id=atacante_id)
        return
    atacante["no_alvo"] += 1
    fator_goleiro = 0.45 if tipo == "cavadinha" and local == "cara" else chute["goleiro"]
    reflexo = atributo_efetivo(goleiro, "ref") if goleiro else 30
    chance = (LOCAIS[local]["gol"] + (finalizacao - reflexo) * PESO_FINALIZACAO) / fator_goleiro * FATOR_GOL + bonus * 0.5
    if atacante["plano"]["estilo"] == "jogo direto":
        chance -= 0.03
    if random.random() < limitar(chance, 0.03, 0.9):
        marcar_gol(partida, atacante_id, finalizador)
        return
    nome_goleiro = goleiro["nome"] if goleiro else "o zagueiro improvisado"
    registrar(partida, "defesa", {"goleiro": nome_goleiro}, tipo="defesa", time_id=atacante_id)
    if rebote and random.random() < 0.22:
        pegar_rebote(partida, atacante_id, defesa)
    elif escanteio and random.random() < 0.35:
        cobrar_escanteio(partida, atacante_id, defesa)


def pegar_rebote(partida, atacante_id, defesa):
    time = partida["times"][atacante_id]
    jogador = escolher_jogador(time, PESOS_REBOTE)
    entregar_bola(partida, atacante_id, "area", 1, jogador)
    registrar(partida, "rebote", {"jogador": jogador["nome"]}, tipo="oportunidade", time_id=atacante_id)
    escolha = perguntar(partida, atacante_id, f"Rebote! {jogador['nome']} pega a sobra. E agora?", [
        ("primeira", "Chutar de primeira", 5),
        ("ajeitar", "Ajeitar e bater", 3),
    ])
    if escolha == "primeira":
        finalizar(partida, atacante_id, jogador, "rebote", "forte", defesa=defesa, rebote=False)
    elif random.random() < 0.45:
        registrar(partida, "rebote_bloqueado", {"jogador": jogador["nome"]}, tipo="perda", time_id=atacante_id)
    else:
        finalizar(partida, atacante_id, jogador, "area", "colocado", defesa=defesa, rebote=False)


def cobrar_escanteio(partida, atacante_id, defesa):
    time = partida["times"][atacante_id]
    batedor = melhor_batedor(time)
    mover_bola(partida, atacante_id, "area", random.choice((0, 2)))
    registrar(partida, "escanteio", {"time": time["nome"]}, tipo="bola_parada", time_id=atacante_id)
    if random.random() < 0.004:
        partida["ultimo_local"] = "olimpico"
        registrar(partida, "gol_olimpico", {"jogador": batedor["nome"]}, tipo="oportunidade", time_id=atacante_id)
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
            registrar(partida, "escanteio_curto", {"jogador": jogador["nome"]}, time_id=atacante_id)
            finalizar(partida, atacante_id, jogador, "longe", escolher_chute(partida, atacante_id, jogador, "longe"), defesa=defesa, escanteio=False)
            return
    elif random.random() < (0.45 if escolha == "primeira" else 0.38):
        bonus = 0.05 if escolha == "segunda" else 0.0
        finalizar(partida, atacante_id, escolher_jogador(time, PESOS_CABECEIO, excluir=batedor), "escanteio", bonus=bonus, defesa=defesa, escanteio=False)
        return
    registrar(partida, "escanteio_afastado", tipo="perda", time_id=atacante_id)


def cobrar_falta(partida, atacante_id, defesa):
    time = partida["times"][atacante_id]
    batedor = melhor_batedor(time)
    mover_bola(partida, atacante_id, "ataque", 1)
    registrar(partida, "falta_perigosa", {"time": time["nome"]}, tipo="bola_parada", time_id=atacante_id)
    escolha = perguntar(partida, atacante_id, f"Falta perigosa! {batedor['nome']} na bola. Como cobrar?", [
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


def cobrar_penalti(partida, atacante_id):
    defensor_id = outro(partida, atacante_id)
    atacante = partida["times"][atacante_id]
    goleiro = goleiro_de(partida["times"][defensor_id])
    batedor = melhor_batedor(atacante)
    entregar_bola(partida, atacante_id, "area", 1, batedor)
    registrar(partida, "penalti", {"time": atacante["nome"], "jogador": batedor["nome"]}, tipo="penalti", time_id=atacante_id)
    canto, forca = partida["controles"][atacante_id]["bater_penalti"](partida, atacante_id, batedor, goleiro)
    pulo = partida["controles"][defensor_id]["defender_penalti"](partida, defensor_id, batedor, goleiro)
    partida["ultimo_penalti"] = {"time": atacante_id, "canto": canto, "forca": forca, "pulo": pulo}
    partida["ultimo_local"] = "penalti"
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
    mover_bola(partida, atacante_id, "gol", 1)
    registrar(partida, "penalti_gol", {"jogador": batedor["nome"], "placar": placar(partida)}, tipo="gol", time_id=atacante_id)
    anotar_sumula(partida, f"GOL (pênalti) — {batedor['nome']} ({atacante['sigla']})")


def cartao_na_falta(partida, defensor_id, marcador, chance_amarelo):
    sorteio = random.random()
    if sorteio < 0.025:
        expulsar(partida, defensor_id, marcador, "vermelho")
    elif sorteio < chance_amarelo:
        amarelar(partida, defensor_id, marcador)


def cometer_falta(partida, atacante_id, zona, portador, marcador, defesa):
    defensor_id = outro(partida, atacante_id)
    partida["times"][defensor_id]["faltas"] += 1
    registrar(partida, "falta", {"marcador": marcador["nome"], "jogador": portador["nome"]}, tipo="falta", time_id=defensor_id)
    cartao_na_falta(partida, defensor_id, marcador, 0.22 + (0.08 if defesa == "bote" else 0))
    if zona == "area":
        return "penalti"
    if zona == "ataque":
        return "perigosa"
    return "meio"


def falta_tatica(partida, atacante_id, zona, portador, defesa):
    defensor_id = outro(partida, atacante_id)
    marcador = escolher_jogador(partida["times"][defensor_id], PESOS_MARCADOR[zona])
    partida["times"][defensor_id]["faltas"] += 1
    registrar(partida, "falta_tatica", {"marcador": marcador["nome"], "jogador": portador["nome"]}, tipo="falta", time_id=defensor_id)
    cartao_na_falta(partida, defensor_id, marcador, 0.45)
    if zona == "ataque":
        cobrar_falta(partida, atacante_id, defesa)


def cara_a_cara(partida, atacante_id, jogador, bonus, defesa):
    defensor = partida["times"][outro(partida, atacante_id)]
    goleiro = goleiro_de(defensor)
    entregar_bola(partida, atacante_id, "area", 1, jogador)
    registrar(partida, "cara", {"jogador": jogador["nome"]}, tipo="oportunidade", time_id=atacante_id)
    escolha = perguntar(partida, atacante_id, f"{jogador['nome']} está cara a cara com o goleiro!", [
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
    nome_goleiro = goleiro["nome"] if goleiro else "o zagueiro"
    if random.random() < limitar(0.5 + (tecnica - reflexo) * 0.005 + bonus, 0.15, 0.85):
        registrar(partida, "driblou_goleiro", {"jogador": jogador["nome"]}, time_id=atacante_id)
        partida["times"][atacante_id]["chutes"] += 1
        partida["times"][atacante_id]["no_alvo"] += 1
        partida["ultimo_local"] = "gol_vazio"
        marcar_gol(partida, atacante_id, jogador)
        return
    registrar(partida, "goleiro_salva", {"goleiro": nome_goleiro, "jogador": jogador["nome"]}, tipo="defesa", time_id=atacante_id)


def cruzamento(partida, atacante_id, cruzador, bonus, defesa):
    time = partida["times"][atacante_id]
    receptor = escolher_jogador(time, PESOS_CABECEIO, excluir=cruzador)
    entregar_bola(partida, atacante_id, "area", 1, receptor)
    escolha = perguntar(partida, atacante_id, f"A bola vem na área para {receptor['nome']}!", [
        ("cabecear", "Cabecear", 5),
        ("voleio", "Bater de voleio", 2),
        ("dominar", "Dominar e chutar", 3),
    ])
    if escolha == "cabecear":
        finalizar(partida, atacante_id, receptor, "cabeceio", bonus=bonus, defesa=defesa)
    elif escolha == "voleio":
        finalizar(partida, atacante_id, receptor, "voleio", "forte", bonus, defesa)
    elif random.random() < 0.4:
        registrar(partida, "dominar_erro", {"jogador": receptor["nome"]}, tipo="perda", time_id=atacante_id)
    else:
        finalizar(partida, atacante_id, receptor, "area", escolher_chute(partida, atacante_id, receptor, "area"), bonus, defesa)


def oportunidade_do_meio(partida, atacante_id, portador, defesa):
    goleiro = goleiro_de(partida["times"][outro(partida, atacante_id)])
    nome_goleiro = goleiro["nome"] if goleiro else "O goleiro"
    registrar(partida, "goleiro_adiantado", {"goleiro": nome_goleiro}, tipo="oportunidade", time_id=atacante_id)
    escolha = perguntar(partida, atacante_id, f"{nome_goleiro} está adiantado! {portador['nome']} arrisca do meio-campo?", [
        ("arriscar", "Chutar do meio-campo", 1),
        ("seguir", "Seguir a jogada", 4),
    ])
    if escolha == "arriscar":
        finalizar(partida, atacante_id, portador, "meio_campo", "forte", defesa=defesa, rebote=False)
        return True
    return False


def jogar_posse(partida, atacante_id, contra_ataque=False, portador=None):
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
            registrar(partida, "contra_ataque", {"time": atacante["nome"], "jogador": portador["nome"]}, time_id=atacante_id)
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
            finalizar(partida, atacante_id, portador, local, escolher_chute(partida, atacante_id, portador, local), bonus, defesa)
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
            drible = perguntar(partida, atacante_id, f"Que drible {portador['nome']} vai tentar?", [
                (chave, dados_drible["nome"], dados_drible["peso"]) for chave, dados_drible in DRIBLES.items()
            ])
        dados = {"jogador": portador["nome"], "marcador": marcador["nome"], "time": atacante["nome"]}
        if random.random() < chance_da_acao(partida, atacante_id, zona, faixa, acao, portador, marcador, defesa, bonus, drible):
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
            registrar(partida, f"{'bote' if defesa == 'falta' else defesa}_ok", {"marcador": marcador["nome"], "time": defensor["nome"]}, tipo="recuperacao", time_id=defensor_id)
        contra = defensor["plano"]["estilo"] == "contra-ataque" and atacante["plano"]["ofensividade"] >= 4 and random.random() < 0.5
        if contra or random.random() < 0.10 or (defesa == "pressao" and zona == "meio" and random.random() < 0.25):
            return defensor_id, marcador
        return None
    registrar(partida, "tocar_erro", {"jogador": partida["portador"]["nome"], "marcador": "a defesa"}, tipo="perda", time_id=atacante_id)
    return None


def jogar_lance(partida):
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
    registrar(partida, "meio_ganhou", {"time": partida["times"][vencedor]["nome"], "jogador": portador["nome"]}, tipo="meio", time_id=vencedor)
    proximo = jogar_posse(partida, vencedor, portador=portador)
    if proximo:
        jogar_posse(partida, proximo[0], contra_ataque=True, portador=proximo[1])


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
