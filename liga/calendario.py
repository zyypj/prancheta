import random


def gerar_calendario(ids):
    times = list(ids)
    random.shuffle(times)
    if len(times) % 2:
        times.append(None)
    quantidade = len(times)
    turno = []
    for numero in range(quantidade - 1):
        jogos = []
        for indice in range(quantidade // 2):
            casa, fora = times[indice], times[quantidade - 1 - indice]
            if casa is None or fora is None:
                continue
            jogos.append((casa, fora) if (numero + indice) % 2 == 0 else (fora, casa))
        turno.append(jogos)
        times = [times[0], times[-1]] + times[1:-1]
    returno = [[(fora, casa) for casa, fora in rodada] for rodada in turno]
    return turno + returno


def jogo_do_clube(rodada, clube_id):
    for jogo in rodada:
        if clube_id in jogo:
            return jogo
    return None
