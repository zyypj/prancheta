import random

from config import PONTOS_EMPATE, PONTOS_VITORIA


def criar_tabela(ids):
    return {
        identificador: {
            "id": identificador,
            "pontos": 0,
            "jogos": 0,
            "vitorias": 0,
            "empates": 0,
            "derrotas": 0,
            "gp": 0,
            "gc": 0,
            "vermelhos": 0,
            "sorteio": random.random(),
        }
        for identificador in ids
    }


def saldo(linha):
    return linha["gp"] - linha["gc"]


def aplicar_placar(linha, feitos, sofridos, vermelhos):
    linha["jogos"] += 1
    linha["gp"] += feitos
    linha["gc"] += sofridos
    linha["vermelhos"] += vermelhos
    if feitos > sofridos:
        linha["vitorias"] += 1
        linha["pontos"] += PONTOS_VITORIA
    elif feitos == sofridos:
        linha["empates"] += 1
        linha["pontos"] += PONTOS_EMPATE
    else:
        linha["derrotas"] += 1


def registrar_resultado(tabela, resultado):
    aplicar_placar(tabela[resultado["mandante"]], resultado["gm"], resultado["gv"], resultado.get("vm", 0))
    aplicar_placar(tabela[resultado["visitante"]], resultado["gv"], resultado["gm"], resultado.get("vv", 0))


def criterio_principal(linha):
    return linha["pontos"], linha["vitorias"], saldo(linha), linha["gp"]


def pontos_no_confronto(historico, grupo):
    pontos = {identificador: 0 for identificador in grupo}
    for rodada in historico:
        for jogo in rodada:
            casa, fora = jogo["mandante"], jogo["visitante"]
            if casa not in grupo or fora not in grupo:
                continue
            if jogo["gm"] > jogo["gv"]:
                pontos[casa] += PONTOS_VITORIA
            elif jogo["gm"] < jogo["gv"]:
                pontos[fora] += PONTOS_VITORIA
            else:
                pontos[casa] += PONTOS_EMPATE
                pontos[fora] += PONTOS_EMPATE
    return pontos


def ordenar_tabela(tabela, historico):
    linhas = sorted(tabela.values(), key=criterio_principal, reverse=True)
    ordenada = []
    inicio = 0
    while inicio < len(linhas):
        fim = inicio
        while fim < len(linhas) and criterio_principal(linhas[fim]) == criterio_principal(linhas[inicio]):
            fim += 1
        grupo = linhas[inicio:fim]
        if len(grupo) > 1:
            confronto = pontos_no_confronto(historico, {linha["id"] for linha in grupo})
            grupo.sort(key=lambda linha: (confronto[linha["id"]], -linha["vermelhos"], linha["sorteio"]), reverse=True)
        ordenada.extend(grupo)
        inicio = fim
    return ordenada


def posicao_do_clube(ordenada, clube_id):
    for posicao, linha in enumerate(ordenada, start=1):
        if linha["id"] == clube_id:
            return posicao
    return len(ordenada)
