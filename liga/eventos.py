import random

from elenco.escalacao import criar_jogador, limitar, sortear_nome, valor_para_escalar
from liga.temporada import ajustar_confianca, clube_do_jogador


def sortear_evento(eventos):
    return random.choices(eventos, weights=[evento["peso"] for evento in eventos])[0]


def escolher_alvo(clube, alvo):
    por_id = {jogador["id"]: jogador for jogador in clube["elenco"]}
    if alvo == "titular":
        candidatos = [por_id[identificador] for identificador in clube["titulares"] if identificador in por_id]
        return random.choice(candidatos) if candidatos else None
    if alvo == "melhor":
        linha = [jogador for jogador in clube["elenco"] if jogador["pos"] != "GOL"]
        return max(linha, key=lambda jogador: jogador["qualidade"]) if linha else None
    return None


def preparar_evento(evento, clube):
    jogador = escolher_alvo(clube, evento.get("alvo", "nenhum"))
    nome = jogador["nome"] if jogador else ""
    return {
        "id": evento["id"],
        "texto": evento["texto"].replace("{jogador}", nome),
        "jogador_id": jogador["id"] if jogador else None,
        "efeito": evento.get("efeito"),
        "opcoes": [
            {"texto": opcao["texto"].replace("{jogador}", nome), "efeito": opcao["efeito"]}
            for opcao in evento.get("opcoes", [])
        ],
    }


def nomes_em_uso(estado):
    return {jogador["nome"] for clube in estado["clubes"].values() for jogador in clube["elenco"]}


def novo_garoto(estado, clube, banco, qualidade, posicao):
    numero = max(int(jogador["id"].split("-")[1]) for jogador in clube["elenco"]) + 1
    nome = sortear_nome(banco, nomes_em_uso(estado))
    return criar_jogador(f"{clube['id']}-{numero:02d}", nome, posicao, qualidade)


def aplicar_efeito(estado, efeito, jogador_id, banco):
    clube = clube_do_jogador(estado)
    jogador = next((j for j in clube["elenco"] if j["id"] == jogador_id), None)
    if efeito == "grande_fase" and jogador:
        jogador["fase"] = 2
        return f"{jogador['nome']} ganha +5 de qualidade nas próximas 2 rodadas."
    if efeito == "lesao_treino" and jogador:
        jogador["lesao"] = random.randint(1, 3)
        return f"{jogador['nome']} fica fora por {jogador['lesao']} rodada(s)."
    if efeito == "reuniao":
        ajustar_confianca(estado, 2)
        return "O grupo se acertou. Confiança da diretoria +2."
    if efeito == "afastar" and jogador:
        jogador["suspenso"] = max(jogador["suspenso"], 1)
        ajustar_confianca(estado, 5)
        return f"{jogador['nome']} fica fora da próxima rodada. A diretoria aprovou a firmeza: confiança +5."
    if efeito == "vender" and jogador:
        clube["elenco"].remove(jogador)
        if jogador["id"] in clube["titulares"]:
            clube["titulares"].remove(jogador["id"])
        garoto = novo_garoto(estado, clube, banco, limitar(jogador["qualidade"] - 12, 40, 92), jogador["pos"])
        clube["elenco"].append(garoto)
        ajustar_confianca(estado, 6)
        return f"{jogador['nome']} foi vendido. {garoto['nome']} sobe da base no lugar. Confiança +6."
    if efeito == "segurar" and jogador:
        jogador["fase"] = max(jogador["fase"], 1)
        ajustar_confianca(estado, -3)
        return f"{jogador['nome']} fica e joga motivado na próxima rodada. A diretoria não gostou: confiança -3."
    if efeito == "base":
        linha = [j for j in clube["elenco"] if j["pos"] != "GOL"]
        pior = min(linha, key=valor_para_escalar)
        qualidade = limitar(clube["forca"] + random.randint(-6, 4), 40, 92)
        garoto = novo_garoto(estado, clube, banco, qualidade, pior["pos"])
        clube["elenco"].remove(pior)
        if pior["id"] in clube["titulares"]:
            clube["titulares"].remove(pior["id"])
        clube["elenco"].append(garoto)
        return f"{garoto['nome']} ({garoto['pos']}, qualidade {garoto['qualidade']}) entra no lugar de {pior['nome']}."
    if efeito == "protesto":
        ajustar_confianca(estado, -5)
        return "A pressão aumentou. Confiança da diretoria -5."
    if efeito == "descanso":
        for j in clube["elenco"]:
            j["energia"] = min(100, j["energia"] + 15)
        return "Todo o elenco recupera +15 de energia."
    return "Nada mudou."
