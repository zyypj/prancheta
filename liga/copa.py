import random

from config import CLASSIFICADOS_DIRETO_COPA, FASES_COPA, NOMES_FASES, PREMIO_FASE_COPA, PREMIO_TITULO_COPA


def montar_confrontos(ids):
    sorteados = list(ids)
    random.shuffle(sorteados)
    return [(sorteados[indice], sorteados[indice + 1]) for indice in range(0, len(sorteados) - 1, 2)]


def criar_copa(clubes):
    ordem = sorted(clubes.values(), key=lambda clube: clube["forca"], reverse=True)
    diretos = [clube["id"] for clube in ordem[:CLASSIFICADOS_DIRETO_COPA]]
    preliminar = [clube["id"] for clube in ordem[CLASSIFICADOS_DIRETO_COPA:]]
    return {
        "classificados": diretos,
        "confrontos": {"preliminar": montar_confrontos(preliminar)},
        "resultados": {},
        "campeao": None,
        "eliminado_em": None,
    }


def preparar_fase(copa, fase):
    if fase in copa["confrontos"]:
        return copa["confrontos"][fase]
    if fase == "quartas":
        confrontos = montar_confrontos(copa["classificados"])
    else:
        vivos = copa["classificados"]
        confrontos = [(vivos[indice], vivos[indice + 1]) for indice in range(0, len(vivos) - 1, 2)]
    copa["confrontos"][fase] = confrontos
    return confrontos


def jogo_na_fase(copa, fase, clube_id):
    return next((jogo for jogo in copa["confrontos"].get(fase, []) if clube_id in jogo), None)


def fase_neutra(fase):
    return fase == "final"


def registrar_fase(estado, fase, resultados):
    copa = estado["copa"]
    copa["resultados"][fase] = [
        {chave: resultado.get(chave) for chave in ("mandante", "visitante", "gm", "gv", "penaltis", "vencedor")}
        for resultado in resultados
    ]
    vencedores = [resultado["vencedor"] for resultado in resultados]
    for clube_id in vencedores:
        estado["clubes"][clube_id]["caixa"] = round(estado["clubes"][clube_id].get("caixa", 0) + PREMIO_FASE_COPA, 1)
    if fase == "preliminar":
        copa["classificados"] = copa["classificados"] + vencedores
    else:
        ordem = [jogo for jogo in copa["confrontos"][fase]]
        por_jogo = {(r["mandante"], r["visitante"]): r["vencedor"] for r in resultados}
        copa["classificados"] = [por_jogo[jogo] for jogo in ordem]
    if fase == FASES_COPA[-1]:
        copa["campeao"] = vencedores[0]
        campeao = estado["clubes"][copa["campeao"]]
        campeao["caixa"] = round(campeao.get("caixa", 0) + PREMIO_TITULO_COPA, 1)
    jogo = next((r for r in resultados if estado["clube_id"] in (r["mandante"], r["visitante"])), None)
    if jogo and jogo["vencedor"] != estado["clube_id"]:
        copa["eliminado_em"] = fase
    return jogo


def situacao_do_clube(copa, clube_id):
    if copa["campeao"] == clube_id:
        return "campeão"
    for fase, resultados in copa["resultados"].items():
        for resultado in resultados:
            if clube_id in (resultado["mandante"], resultado["visitante"]) and resultado["vencedor"] != clube_id:
                return f"eliminado na {NOMES_FASES[fase].lower()}"
    return "na disputa"
