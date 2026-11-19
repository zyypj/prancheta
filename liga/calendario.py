import random


def gerar_calendario(ids):
    """
    Gera o calendário da liga em turno único, no sistema de todos contra todos.

    Embaralha os clubes e aplica o método do círculo: o primeiro clube fica fixo e os demais giram a cada
    rodada. Com número ímpar de clubes, um espaço vazio é incluído e quem cair contra ele folga na rodada. Em
    cada confronto, manda o jogo quem jogou menos vezes em casa até ali; no empate, quem jogou fora na rodada
    anterior, e depois sorteio. Assim cada clube joga de 4 a 6 vezes em casa e nunca passa de 4 jogos seguidos
    com o mesmo mando.

    Args:
        ids (Iterable[str]): Identificadores dos clubes participantes.

    Returns:
        list[list[tuple[str, str]]]: Lista de rodadas, cada uma com os jogos no formato (mandante, visitante).
    """
    times = list(ids)
    random.shuffle(times)
    if len(times) % 2:
        times.append(None)
    quantidade = len(times)
    jogos_em_casa = {time: 0 for time in times if time}
    ultimo_mando = {}
    turno = []
    for _ in range(quantidade - 1):
        jogos = []
        for indice in range(quantidade // 2):
            um, outro = times[indice], times[quantidade - 1 - indice]
            if um is None or outro is None:
                continue
            casa, fora = sorted(
                (um, outro), key=lambda time: (jogos_em_casa[time], ultimo_mando.get(time) == "casa", random.random())
            )
            jogos_em_casa[casa] += 1
            ultimo_mando[casa], ultimo_mando[fora] = "casa", "fora"
            jogos.append((casa, fora))
        turno.append(jogos)
        times = [times[0], times[-1]] + times[1:-1]
    return turno


def gerar_calendario_das_divisoes(clubes, quantidade_de_turnos=1):
    """
    Gera o calendário das duas divisões, que jogam as rodadas ao mesmo tempo.

    Cada divisão tem o seu turno gerado por gerar_calendario, e a rodada N do calendário junta os jogos da
    rodada N das duas divisões. Com dois turnos, o returno repete a ordem do turno com os mandos invertidos.

    Args:
        clubes (dict): Clubes da temporada, indexados pelo identificador, cada um com a sua divisão.
        quantidade_de_turnos (int): 1 para turno único ou 2 para ida e volta. Padrão 1.

    Returns:
        list[list[tuple[str, str]]]: Lista de rodadas, cada uma com os jogos das duas divisões no formato
            (mandante, visitante).
    """
    divisoes = sorted({clube.get("divisao", 1) for clube in clubes.values()})
    turnos = [
        gerar_calendario([clube_id for clube_id, clube in clubes.items() if clube.get("divisao", 1) == divisao])
        for divisao in divisoes
    ]
    rodadas = max(len(turno) for turno in turnos)
    ida = [[jogo for turno in turnos if numero < len(turno) for jogo in turno[numero]] for numero in range(rodadas)]
    if quantidade_de_turnos == 1:
        return ida
    return ida + [[(fora, casa) for casa, fora in rodada] for rodada in ida]


def jogo_do_clube(rodada, clube_id):
    """
    Procura, dentro de uma rodada, o jogo em que o clube informado atua.

    Args:
        rodada (list[tuple[str, str]]): Jogos da rodada no formato (mandante, visitante).
        clube_id (str): Identificador do clube procurado.

    Returns:
        tuple[str, str] | None: Jogo do clube ou None se ele não joga nessa rodada.
    """
    for jogo in rodada:
        if clube_id in jogo:
            return jogo
    return None
