import random

from elenco.escalacao import atributo_efetivo, limitar, rotulo
from partida.lances import (
    PESOS_MARCADOR,
    PESOS_PORTADOR,
    PESOS_REBOTE,
    amarelar,
    atacante_de_referencia,
    cara_a_cara,
    cartao_na_falta,
    chance_de_gol,
    cobrar_escanteio,
    cobrar_falta,
    cobrar_penalti,
    cometer_falta,
    cruzamento,
    entregar_bola,
    escolher_chute,
    escolher_jogador,
    finalizar,
    goleiro_de,
    jogar_posse,
    melhor_batedor,
    mover_bola,
    outro,
    perguntar,
    registrar,
    revisar_penalti,
)

CHANCE_JOGADA_ESPECIAL = 0.3
PESOS_JOGADAS = {
    "tiro_de_meta": 3,
    "lateral_no_ataque": 3,
    "superioridade": 3,
    "falta_lateral": 2,
    "falta_de_longe": 2,
    "sobra_na_entrada": 3,
    "erro_na_saida": 2,
    "arrancada": 3,
    "pressao_na_saida": 2,
    "escanteio_conquistado": 2,
    "bola_alta": 2,
    "um_contra_um": 3,
    "falta_na_meia_lua": 1,
    "goleiro_pressionado": 2,
    "virada_de_jogo": 2,
    "dois_contra_um": 2,
    "levantamento": 2,
    "pivo": 2,
    "contra_ataque_sofrido": 2,
}
CHANCES_ACONTECIMENTOS = {
    "reclamacao": 0.012,
    "confusao": 0.006,
    "paralisacao": 0.01,
    "chuva_comeca": 0.006,
    "beira_do_campo": 0.025,
}
PESOS_ATACANTE = {"ATA": 6, "MEI": 2}


def marcador_de(partida, time_id, zona):
    """
    Sorteia o jogador do adversário que marca a jogada numa zona.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time com a bola.
        zona (str): Zona do lance, uma das chaves de PESOS_MARCADOR.

    Returns:
        dict: Jogador do time adversário.
    """
    return escolher_jogador(partida["times"][outro(partida, time_id)], PESOS_MARCADOR[zona])


def contra_golpe(partida, time_id, zona, chance):
    """
    Decide se a perda da bola numa jogada especial vira contra-ataque do adversário.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time que perdeu a bola.
        zona (str): Zona onde a bola foi perdida.
        chance (float): Chance de o adversário puxar o contra-ataque.

    Returns:
        tuple | None: (adversário, jogador que puxa o contra-ataque) ou None.
    """
    if random.random() < chance:
        return outro(partida, time_id), marcador_de(partida, time_id, zona)
    return None


def tiro_de_meta(partida, time_id, portador):
    """
    O goleiro tem a bola e escolhe como repor.

    Sair jogando curto começa uma posse normal no meio. O lançamento no centroavante vira uma disputa no alto
    entre o físico do atacante e o desarme do zagueiro (45% de base): ganhando, a posse começa no ataque.
    Lançar na ponta dá certo em 55% das vezes. Perder a disputa entrega a bola ao adversário.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time que repõe a bola.
        portador (dict): Jogador que ganhou a bola no lance, usado se não houver goleiro.

    Returns:
        tuple | None: Contra-ataque do adversário, quando houver, como em jogar_posse.
    """
    time = partida["times"][time_id]
    goleiro = goleiro_de(time) or portador
    entregar_bola(partida, time_id, "saida", 1, goleiro)
    registrar(partida, "tiro_de_meta", {"goleiro": rotulo(goleiro), "time": time["nome"]}, time_id=time_id)
    alvo = escolher_jogador(time, PESOS_ATACANTE)
    zagueiro = marcador_de(partida, time_id, "ataque")
    chance_longo = limitar(
        0.45 + (atributo_efetivo(alvo, "fis") - atributo_efetivo(zagueiro, "des")) * 0.006, 0.15, 0.8
    )
    escolha = perguntar(
        partida,
        time_id,
        f"{rotulo(goleiro)} vai repor a bola. Como?",
        [
            ("curto", "Sair jogando curto", 4, 1.0),
            ("longo", "Lançar no centroavante", 3, chance_longo),
            ("ponta", "Lançar na ponta", 2, 0.55),
        ],
    )
    if escolha == "curto":
        mover_bola(partida, time_id, "defesa", 1)
        registrar(partida, "saida_curta", {"time": time["nome"]}, time_id=time_id)
        return jogar_posse(partida, time_id, zona_inicial="defesa")
    dados = {"jogador": rotulo(alvo), "marcador": rotulo(zagueiro), "goleiro": rotulo(goleiro)}
    chance = chance_longo if escolha == "longo" else 0.55
    if random.random() < chance:
        registrar(partida, f"lancamento_{escolha}_ok", dados, time_id=time_id)
        return jogar_posse(partida, time_id, portador=alvo, zona_inicial="ataque")
    registrar(partida, "lancamento_perdido", dados, tipo="perda", time_id=time_id)
    return contra_golpe(partida, time_id, "meio", 0.15)


def lateral_no_ataque(partida, time_id, portador):
    """
    Lateral a favor perto da área adversária.

    O lateral longo vira um cruzamento na área em 50% das vezes, com mais chance para quem tem físico alto; o
    curto começa uma posse já na entrada da área; recuar recomeça a jogada no meio.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time que cobra o lateral.
        portador (dict): Jogador que vai cobrar.

    Returns:
        tuple | None: Contra-ataque do adversário, quando houver.
    """
    time = partida["times"][time_id]
    faixa = random.choice((0, 2))
    entregar_bola(partida, time_id, "lateral", faixa, portador)
    registrar(partida, "lateral", {"time": time["nome"], "jogador": rotulo(portador)}, time_id=time_id)
    escolha = perguntar(
        partida,
        time_id,
        f"Lateral no ataque com {rotulo(portador)}. Como cobrar?",
        [
            (
                "longo",
                "Lateral longo na área",
                2,
                limitar(0.5 + (atributo_efetivo(portador, "fis") - 70) * 0.005, 0.05, 0.95),
            ),
            ("curto", "Curto, para tabelar", 4, 1.0),
            ("recuar", "Recuar e recomeçar", 2, 1.0),
        ],
    )
    if escolha == "longo":
        if random.random() < 0.5 + (atributo_efetivo(portador, "fis") - 70) * 0.005:
            registrar(partida, "lateral_longo", {"jogador": rotulo(portador)}, time_id=time_id)
            cruzamento(partida, time_id, portador, -0.04, "fechar")
            return None
        registrar(partida, "lateral_afastado", tipo="perda", time_id=time_id)
        return contra_golpe(partida, time_id, "ataque", 0.1)
    if escolha == "curto":
        return jogar_posse(partida, time_id, portador=portador, zona_inicial="ataque")
    registrar(partida, "lateral_recuado", {"time": time["nome"]}, time_id=time_id)
    return jogar_posse(partida, time_id, zona_inicial="intermediaria")


def superioridade(partida, time_id, portador):
    """
    Contra-ataque com três atacantes contra dois defensores.

    Tocar para o centroavante deixa ele cara a cara em 60% das vezes (mais com bom passe). Abrir para o ponta
    dá certo em 70% e vira cruzamento. Conduzir e chutar é uma finalização com bônus, de fora ou de dentro da
    área. Errar o passe pode devolver o contra-ataque.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time que contra-ataca.
        portador (dict): Jogador que conduz a bola.

    Returns:
        tuple | None: Contra-ataque do adversário, quando houver.
    """
    time = partida["times"][time_id]
    entregar_bola(partida, time_id, "ataque", 1, portador)
    registrar(partida, "superioridade", {"time": time["nome"], "jogador": rotulo(portador)}, time_id=time_id)
    escolha = perguntar(
        partida,
        time_id,
        f"Três contra dois! {rotulo(portador)} conduz. O que fazer?",
        [
            (
                "centro",
                "Tocar para o centroavante",
                4,
                limitar(0.6 + (atributo_efetivo(portador, "pas") - 70) * 0.004, 0.05, 0.95),
            ),
            ("ponta", "Abrir para o ponta", 3, 0.7),
            (
                "conduzir",
                "Conduzir e chutar",
                3,
                (
                    chance_de_gol(partida, time_id, portador, "longe", "colocado", 0.04, "recuar")
                    + chance_de_gol(partida, time_id, portador, "area", "colocado", 0.04, "recuar")
                )
                / 2,
            ),
        ],
    )
    if escolha == "centro":
        centroavante = escolher_jogador(time, PESOS_ATACANTE, excluir=portador)
        if random.random() < 0.6 + (atributo_efetivo(portador, "pas") - 70) * 0.004:
            cara_a_cara(partida, time_id, centroavante, 0.04, "recuar")
            return None
        registrar(partida, "passe_cortado", {"jogador": rotulo(portador)}, tipo="perda", time_id=time_id)
        return contra_golpe(partida, time_id, "ataque", 0.2)
    if escolha == "ponta":
        ponta = escolher_jogador(time, {"ATA": 4, "MEI": 4}, excluir=portador)
        if random.random() < 0.7:
            entregar_bola(partida, time_id, "ataque", random.choice((0, 2)), ponta)
            registrar(partida, "abriu_ponta", {"jogador": rotulo(ponta)}, time_id=time_id)
            cruzamento(partida, time_id, ponta, 0.03, "recuar")
            return None
        registrar(partida, "passe_cortado", {"jogador": rotulo(portador)}, tipo="perda", time_id=time_id)
        return contra_golpe(partida, time_id, "ataque", 0.2)
    local = random.choice(("longe", "area"))
    finalizar(partida, time_id, portador, local, escolher_chute(partida, time_id, portador, local), 0.04, "recuar")
    return None


def falta_lateral(partida, time_id, portador):
    """
    Falta a favor pelo lado do campo, perto da área.

    O adversário soma a falta e o autor pode levar amarelo (15%). O batedor escolhe cruzar fechado (o goleiro
    corta 15% das vezes e a bola pode entrar direto em 4%), aberto no segundo pau (35% de chance de a zaga
    afastar, mas com bônus), uma jogada ensaiada rasteira (metade das vezes alguém bate livre) ou bater
    direto, com pouca chance.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time que sofreu a falta.
        portador (dict): Jogador que sofreu a falta.

    Returns:
        tuple | None: Sempre None; a jogada termina na cobrança.
    """
    defensor_id = outro(partida, time_id)
    time = partida["times"][time_id]
    autor = marcador_de(partida, time_id, "ataque")
    partida["times"][defensor_id]["faltas"] += 1
    batedor = melhor_batedor(time)
    entregar_bola(partida, time_id, "ataque", random.choice((0, 2)), batedor)
    registrar(
        partida,
        "falta_lateral",
        {"marcador": rotulo(autor), "jogador": rotulo(portador), "time": time["nome"]},
        tipo="bola_parada",
        time_id=time_id,
    )
    cartao_na_falta(partida, defensor_id, autor, 0.15)
    escolha = perguntar(
        partida,
        time_id,
        f"Falta pelo lado! {rotulo(batedor)} na bola. Como cobrar?",
        [
            ("fechado", "Cruzar fechado, na direção do gol", 3, 0.81),
            ("aberto", "Cruzar aberto, no segundo pau", 3, 0.65),
            ("ensaiada", "Jogada ensaiada rasteira", 2, 0.5),
            ("direto", "Bater direto no gol", 1, chance_de_gol(partida, time_id, batedor, "falta", "forte", -0.1)),
        ],
    )
    dados = {"jogador": rotulo(batedor)}
    if escolha == "fechado":
        sorteio = random.random()
        if sorteio < 0.04:
            registrar(partida, "cruzamento_direto_gol", dados, tipo="oportunidade", time_id=time_id)
            finalizar(partida, time_id, batedor, "falta", "colocado", 0.3, "fechar", rebote=False)
        elif sorteio < 0.19:
            registrar(partida, "goleiro_corta", dados, tipo="defesa", time_id=time_id)
        else:
            cruzamento(partida, time_id, batedor, 0.0, "fechar")
    elif escolha == "aberto":
        if random.random() < 0.35:
            registrar(partida, "escanteio_afastado", tipo="perda", time_id=time_id)
        else:
            cruzamento(partida, time_id, batedor, 0.04, "fechar")
    elif escolha == "ensaiada":
        if random.random() < 0.5:
            companheiro = escolher_jogador(time, PESOS_REBOTE, excluir=batedor)
            entregar_bola(partida, time_id, "area", 1, companheiro)
            registrar(partida, "ensaiada_ok", {"jogador": rotulo(companheiro)}, time_id=time_id)
            finalizar(partida, time_id, companheiro, "area", "colocado", 0.05, "fechar")
        else:
            registrar(partida, "ensaiada_erro", dados, tipo="perda", time_id=time_id)
    else:
        finalizar(partida, time_id, batedor, "falta", "forte", -0.1, "fechar")
    return None


def falta_de_longe(partida, time_id, portador):
    """
    Falta a favor a uns 30 metros do gol.

    O batedor pode bater direto (chute forte de longe), levantar na área (55% de chance de o cruzamento
    chegar), rolar curto para manter a posse na entrada da área ou rolar para um companheiro bater de
    primeira.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time que sofreu a falta.
        portador (dict): Jogador que sofreu a falta.

    Returns:
        tuple | None: Contra-ataque do adversário, quando houver.
    """
    defensor_id = outro(partida, time_id)
    time = partida["times"][time_id]
    autor = marcador_de(partida, time_id, "meio")
    partida["times"][defensor_id]["faltas"] += 1
    batedor = melhor_batedor(time)
    entregar_bola(partida, time_id, "ataque", 1, batedor)
    registrar(
        partida,
        "falta_longe",
        {"marcador": rotulo(autor), "jogador": rotulo(portador), "time": time["nome"]},
        tipo="bola_parada",
        time_id=time_id,
    )
    cartao_na_falta(partida, defensor_id, autor, 0.12)
    escolha = perguntar(
        partida,
        time_id,
        f"Falta de longe! {rotulo(batedor)} ajeita a bola. O que fazer?",
        [
            ("direto", "Bater direto", 3, chance_de_gol(partida, time_id, batedor, "longe", "forte", -0.02)),
            ("levantar", "Levantar na área", 3, 0.55),
            ("curta", "Rolar curto e manter a posse", 3, 1.0),
            (
                "rolar",
                "Rolar para um companheiro bater",
                2,
                chance_de_gol(partida, time_id, atacante_de_referencia(time, batedor), "primeira", "forte", 0.03),
            ),
        ],
    )
    if escolha == "direto":
        finalizar(partida, time_id, batedor, "longe", "forte", -0.02, "fechar")
    elif escolha == "levantar":
        if random.random() < 0.55:
            cruzamento(partida, time_id, batedor, -0.03, "fechar")
        else:
            registrar(partida, "escanteio_afastado", tipo="perda", time_id=time_id)
    elif escolha == "curta":
        return jogar_posse(partida, time_id, portador=batedor, zona_inicial="ataque")
    else:
        companheiro = escolher_jogador(time, PESOS_REBOTE, excluir=batedor)
        registrar(
            partida,
            "falta_rolada",
            {"jogador": rotulo(batedor), "companheiro": rotulo(companheiro)},
            time_id=time_id,
        )
        finalizar(partida, time_id, companheiro, "primeira", "forte", 0.03, "fechar")
    return None


def sobra_na_entrada(partida, time_id, portador):
    """
    A defesa afasta mal e a bola sobra na entrada da área.

    Bater de primeira é um chute forte com pouco controle; matar no peito perde a bola 30% das vezes, mas
    deixa escolher o chute; o lençol passa pelo marcador conforme o físico contra o desarme e deixa o jogador
    na área com bônus; tocar recomeça a jogada da entrada da área.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time que fica com a sobra.
        portador (dict): Jogador que ganhou a bola no lance, não usado aqui.

    Returns:
        tuple | None: Contra-ataque do adversário, quando houver.
    """
    time = partida["times"][time_id]
    jogador = escolher_jogador(time, PESOS_REBOTE)
    entregar_bola(partida, time_id, "ataque", random.randint(0, 2), jogador)
    registrar(
        partida, "sobra", {"jogador": rotulo(jogador), "time": time["nome"]}, tipo="oportunidade", time_id=time_id
    )
    marcador = marcador_de(partida, time_id, "ataque")
    chance_lencol = limitar(
        0.35 + (atributo_efetivo(jogador, "fis") - atributo_efetivo(marcador, "des")) * 0.005, 0.15, 0.6
    )
    escolha = perguntar(
        partida,
        time_id,
        f"A bola sobra para {rotulo(jogador)} na entrada da área!",
        [
            ("primeira", "Bater de primeira", 4, chance_de_gol(partida, time_id, jogador, "primeira", "forte", 0.02)),
            ("peito", "Matar no peito e bater", 3, 0.7 * chance_de_gol(partida, time_id, jogador, "longe", "colocado")),
            ("lencol", "Dar um lençol no marcador", 1, chance_lencol),
            ("tocar", "Tocar e reorganizar", 2, 1.0),
        ],
    )
    if escolha == "primeira":
        finalizar(partida, time_id, jogador, "primeira", "forte", 0.02, "fechar")
        return None
    if escolha == "peito":
        if random.random() < 0.3:
            registrar(partida, "dominar_erro", {"jogador": rotulo(jogador)}, tipo="perda", time_id=time_id)
            return contra_golpe(partida, time_id, "ataque", 0.15)
        finalizar(partida, time_id, jogador, "longe", escolher_chute(partida, time_id, jogador, "longe"), 0.0, "fechar")
        return None
    if escolha == "lencol":
        dados = {"jogador": rotulo(jogador), "marcador": rotulo(marcador)}
        if random.random() < chance_lencol:
            entregar_bola(partida, time_id, "area", partida["bola"]["faixa"], jogador)
            registrar(partida, "lencol_ok", dados, time_id=time_id)
            finalizar(partida, time_id, jogador, "area", "colocado", 0.08, "fechar")
            return None
        registrar(partida, "lencol_erro", dados, tipo="perda", time_id=time_id)
        return contra_golpe(partida, time_id, "ataque", 0.2)
    return jogar_posse(partida, time_id, portador=jogador, zona_inicial="ataque")


def erro_na_saida(partida, time_id, portador):
    """
    O adversário erra o passe na saída de bola e o atacante rouba perto da área.

    Chutar logo é uma finalização da área com bônus pequeno; avançar deixa o atacante cara a cara em 55% das
    vezes (mais com bom físico), senão o zagueiro chega no carrinho e pode fazer pênalti; tocar para o
    companheiro livre dá certo em 65% das vezes e vira uma finalização com bônus.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time que roubou a bola.
        portador (dict): Jogador que ganhou a bola no lance, não usado aqui.

    Returns:
        tuple | None: Sempre None; a jogada termina no ataque.
    """
    time = partida["times"][time_id]
    errou = marcador_de(partida, time_id, "area")
    ladrao = escolher_jogador(time, PESOS_ATACANTE)
    entregar_bola(partida, time_id, "area", 1, ladrao)
    registrar(
        partida,
        "erro_saida",
        {"marcador": rotulo(errou), "jogador": rotulo(ladrao)},
        tipo="oportunidade",
        time_id=time_id,
    )
    escolha = perguntar(
        partida,
        time_id,
        f"{rotulo(ladrao)} rouba a bola na saída! O que fazer?",
        [
            ("chutar", "Chutar logo", 3, chance_de_gol(partida, time_id, ladrao, "area", "colocado", 0.02, "recuar")),
            (
                "avancar",
                "Avançar para o cara a cara",
                3,
                limitar(0.55 + (atributo_efetivo(ladrao, "fis") - 70) * 0.004, 0.05, 0.95),
            ),
            ("tocar", "Tocar para o companheiro livre", 3, 0.65),
        ],
    )
    if escolha == "chutar":
        finalizar(partida, time_id, ladrao, "area", escolher_chute(partida, time_id, ladrao, "area"), 0.02, "recuar")
    elif escolha == "avancar":
        if random.random() < 0.55 + (atributo_efetivo(ladrao, "fis") - 70) * 0.004:
            cara_a_cara(partida, time_id, ladrao, 0.03, "recuar")
            return None
        zagueiro = marcador_de(partida, time_id, "area")
        if random.random() < 0.2:
            cometer_falta(partida, time_id, "area", ladrao, zagueiro, "bote")
            if revisar_penalti(partida, time_id):
                cobrar_penalti(partida, time_id)
        else:
            registrar(partida, "carrinho_salvador", {"marcador": rotulo(zagueiro)}, tipo="defesa", time_id=time_id)
    elif random.random() < 0.65:
        companheiro = escolher_jogador(time, PESOS_REBOTE, excluir=ladrao)
        registrar(
            partida, "tocou_livre", {"jogador": rotulo(ladrao), "companheiro": rotulo(companheiro)}, time_id=time_id
        )
        finalizar(partida, time_id, companheiro, "area", "colocado", 0.06, "recuar")
    else:
        registrar(partida, "passe_cortado", {"jogador": rotulo(ladrao)}, tipo="perda", time_id=time_id)
    return None


def arrancada(partida, time_id, portador):
    """
    O jogador mais forte e técnico do meio para frente arranca com a bola dominada.

    Arrancar em velocidade compara o físico dele com o desarme do marcador (45% de base): passando, finaliza
    da área; parado, pode sofrer falta perigosa (30%). Driblar dois marcadores é mais difícil (25% de base),
    mas termina cara a cara. Soltar a bola no ponto futuro começa uma posse na entrada da área.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time com a bola.
        portador (dict): Jogador usado se o time não tiver meias nem atacantes em campo.

    Returns:
        tuple | None: Contra-ataque do adversário, quando houver.
    """
    time = partida["times"][time_id]
    candidatos = [j for j in time["em_campo"] if j["pos"] in ("MEI", "ATA")]
    craque = max(candidatos, key=lambda j: atributo_efetivo(j, "fis") + atributo_efetivo(j, "fin"), default=portador)
    entregar_bola(partida, time_id, "meio", 1, craque)
    registrar(partida, "arrancada", {"jogador": rotulo(craque), "time": time["nome"]}, time_id=time_id)
    marcador = marcador_de(partida, time_id, "ataque")
    chance_velocidade = limitar(
        0.45 + (atributo_efetivo(craque, "fis") - atributo_efetivo(marcador, "des")) * 0.005, 0.2, 0.75
    )
    tecnica = (atributo_efetivo(craque, "fin") + atributo_efetivo(craque, "fis")) / 2
    chance_dois = limitar(0.25 + (tecnica - atributo_efetivo(marcador, "des")) * 0.005, 0.1, 0.5)
    escolha = perguntar(
        partida,
        time_id,
        f"{rotulo(craque)} arranca com a bola dominada! E agora?",
        [
            ("velocidade", "Arrancar em velocidade", 4, chance_velocidade),
            ("driblar_dois", "Driblar dois marcadores", 2, chance_dois),
            ("soltar", "Soltar a bola no ponto futuro", 3, 1.0),
        ],
    )
    dados = {"jogador": rotulo(craque), "marcador": rotulo(marcador)}
    if escolha == "velocidade":
        if random.random() < chance_velocidade:
            entregar_bola(partida, time_id, "area", 1, craque)
            registrar(partida, "arrancada_ok", dados, time_id=time_id)
            finalizar(
                partida, time_id, craque, "area", escolher_chute(partida, time_id, craque, "area"), 0.03, "fechar"
            )
            return None
        if random.random() < 0.3:
            cometer_falta(partida, time_id, "ataque", craque, marcador, "bote")
            cobrar_falta(partida, time_id, "fechar")
            return None
        registrar(partida, "arrancada_parada", dados, tipo="perda", time_id=time_id)
        return contra_golpe(partida, time_id, "meio", 0.15)
    if escolha == "driblar_dois":
        if random.random() < chance_dois:
            entregar_bola(partida, time_id, "area", 1, craque)
            registrar(partida, "driblou_dois", dados, tipo="oportunidade", time_id=time_id)
            cara_a_cara(partida, time_id, craque, 0.08, "fechar")
            return None
        registrar(partida, "driblar_erro", dados, tipo="perda", time_id=time_id)
        return contra_golpe(partida, time_id, "meio", 0.25)
    companheiro = escolher_jogador(time, PESOS_PORTADOR["ataque"], excluir=craque)
    registrar(partida, "ponto_futuro", {"jogador": rotulo(craque), "companheiro": rotulo(companheiro)}, time_id=time_id)
    return jogar_posse(partida, time_id, portador=companheiro, zona_inicial="ataque")


def pressao_na_saida(partida, time_id, portador):
    """
    O adversário tenta sair jogando de trás e o time escolhe como pressionar.

    Pressionar o goleiro rouba a bola na área em 30% das vezes, força um chutão em 15% e, no resto, a pressão
    é furada e o adversário pode sair em contra-ataque (55%). Fechar as linhas de passe recupera a bola no
    ataque em 45% das vezes. Esperar no meio deixa o adversário com a posse.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time que pressiona.
        portador (dict): Jogador que ganhou a bola no lance, não usado aqui.

    Returns:
        tuple | None: Contra-ataque de algum dos times, quando houver.
    """
    time = partida["times"][time_id]
    adversario_id = outro(partida, time_id)
    adversario = partida["times"][adversario_id]
    goleiro = goleiro_de(adversario)
    nome_goleiro = rotulo(goleiro) if goleiro else "o zagueiro"
    mover_bola(partida, adversario_id, "saida", 1)
    registrar(partida, "pressao_saida", {"time": adversario["nome"], "goleiro": nome_goleiro}, time_id=adversario_id)
    escolha = perguntar(
        partida,
        time_id,
        f"O {adversario['nome']} quer sair jogando de trás. Como o {time['nome']} pressiona?",
        [
            ("pressionar", "Pressionar o goleiro", 3, 0.3),
            ("linhas", "Fechar as linhas de passe", 3, 0.45),
            ("esperar", "Esperar no meio", 2, 0.0),
        ],
    )
    if escolha == "pressionar":
        sorteio = random.random()
        if sorteio < 0.3:
            ladrao = escolher_jogador(time, PESOS_ATACANTE)
            entregar_bola(partida, time_id, "area", 1, ladrao)
            registrar(
                partida,
                "roubou_na_saida",
                {"jogador": rotulo(ladrao), "goleiro": nome_goleiro},
                tipo="oportunidade",
                time_id=time_id,
            )
            finalizar(partida, time_id, ladrao, "area", "colocado", 0.06, "recuar")
            return None
        if sorteio < 0.45:
            registrar(partida, "chutao", {"goleiro": nome_goleiro}, time_id=adversario_id)
            return None
        registrar(partida, "pressao_furada", {"time": adversario["nome"]}, tipo="perda", time_id=adversario_id)
        return contra_golpe(partida, time_id, "meio", 0.55)
    if escolha == "linhas":
        if random.random() < 0.45:
            jogador = escolher_jogador(time, PESOS_PORTADOR["ataque"])
            registrar(partida, "recuperou_alto", {"jogador": rotulo(jogador), "time": time["nome"]}, time_id=time_id)
            return jogar_posse(partida, time_id, portador=jogador, zona_inicial="ataque")
        registrar(partida, "adversario_escapa", {"time": adversario["nome"]}, time_id=adversario_id)
        return None
    registrar(partida, "time_espera", {"time": time["nome"]}, time_id=time_id)
    return jogar_posse(partida, adversario_id)


def escanteio_conquistado(partida, time_id, portador):
    """
    O ataque força um escanteio logo de cara.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time que ganhou o escanteio.
        portador (dict): Jogador que forçou o escanteio.

    Returns:
        tuple | None: Sempre None; a jogada termina na cobrança.
    """
    registrar(
        partida,
        "escanteio_conquistado",
        {"jogador": rotulo(portador), "time": partida["times"][time_id]["nome"]},
        time_id=time_id,
    )
    cobrar_escanteio(partida, time_id, "fechar")
    return None


def bola_alta(partida, time_id, portador):
    """
    Uma bola longa chega pelo alto e o jogador escolhe como dominar.

    Ganhar de cabeça depende do físico contra o do marcador (50% de base) e leva a posse para a entrada da
    área; dominar no peito depende do passe (60% de base) e mantém a posse no meio; deixar quicar é cara ou
    coroa.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time que disputa a bola.
        portador (dict): Jogador que ganhou a bola no lance, não usado aqui.

    Returns:
        tuple | None: Contra-ataque de algum dos times, quando houver.
    """
    time = partida["times"][time_id]
    jogador = escolher_jogador(time, {"ATA": 4, "MEI": 3, "DEF": 2})
    marcador = marcador_de(partida, time_id, "meio")
    dados = {"jogador": rotulo(jogador), "marcador": rotulo(marcador)}
    entregar_bola(partida, time_id, "meio", random.randint(0, 2), jogador)
    registrar(partida, "bola_alta", dados, time_id=time_id)
    chance_cabeca = limitar(
        0.5 + (atributo_efetivo(jogador, "fis") - atributo_efetivo(marcador, "fis")) * 0.006, 0.2, 0.8
    )
    chance_peito = limitar(0.6 + (atributo_efetivo(jogador, "pas") - 70) * 0.004, 0.05, 0.95)
    escolha = perguntar(
        partida,
        time_id,
        f"A bola vem pelo alto para {rotulo(jogador)}. Como dominar?",
        [
            ("cabeca", "Ganhar de cabeça e escorar", 3, chance_cabeca),
            ("peito", "Dominar no peito", 3, chance_peito),
            ("deixar", "Deixar quicar", 1, 0.5),
        ],
    )
    if escolha == "cabeca":
        if random.random() < chance_cabeca:
            registrar(partida, "escorou_alto", dados, time_id=time_id)
            return jogar_posse(partida, time_id, zona_inicial="ataque")
        registrar(partida, "perdeu_alto", dados, tipo="perda", time_id=time_id)
        return None
    if escolha == "peito":
        if random.random() < chance_peito:
            registrar(partida, "dominou_alto", dados, time_id=time_id)
            return jogar_posse(partida, time_id, portador=jogador, zona_inicial="meio")
        registrar(partida, "dominar_erro", dados, tipo="perda", time_id=time_id)
        return contra_golpe(partida, time_id, "meio", 0.1)
    if random.random() < 0.5:
        registrar(partida, "quicou_bem", dados, time_id=time_id)
        return jogar_posse(partida, time_id, portador=jogador, zona_inicial="meio")
    registrar(partida, "quicou_mal", dados, tipo="perda", time_id=time_id)
    return None


def um_contra_um(partida, time_id, portador):
    """
    O ponta recebe na linha de fundo e encara o lateral no mano a mano.

    Ir para cima compara a técnica do ponta (média de finalização e físico) com o desarme do lateral (45% de
    base) e, passando, deixa o ponta cara a cara; cruzar de primeira chega em 60% das vezes; esperar a
    ultrapassagem do lateral dá certo em 65% e o cruzamento sai com bônus; cortar para dentro termina num
    chute colocado da entrada da área.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time com a bola.
        portador (dict): Jogador que ganhou a bola no lance, não usado aqui.

    Returns:
        tuple | None: Contra-ataque do adversário, quando houver.
    """
    time = partida["times"][time_id]
    ponta = escolher_jogador(time, {"ATA": 5, "MEI": 3})
    lateral = marcador_de(partida, time_id, "linha_de_fundo")
    apoio = escolher_jogador(time, {"DEF": 4, "MEI": 2}, excluir=ponta)
    entregar_bola(partida, time_id, "linha_de_fundo", random.choice((0, 2)), ponta)
    dados = {"jogador": rotulo(ponta), "marcador": rotulo(lateral)}
    registrar(partida, "um_contra_um", dados, tipo="oportunidade", time_id=time_id)
    tecnica = (atributo_efetivo(ponta, "fin") + atributo_efetivo(ponta, "fis")) / 2
    chance_drible = limitar(0.45 + (tecnica - atributo_efetivo(lateral, "des")) * 0.005, 0.15, 0.75)
    escolha = perguntar(
        partida,
        time_id,
        f"{rotulo(ponta)} encara {rotulo(lateral)} na linha de fundo!",
        [
            ("encarar", "Ir para cima e driblar", 3, chance_drible),
            ("cruzar", "Cruzar de primeira", 3, 0.6),
            ("ultrapassagem", f"Esperar a ultrapassagem de {rotulo(apoio)}", 2, 0.65),
            (
                "cortar",
                "Cortar para dentro e chutar",
                2,
                chance_de_gol(partida, time_id, ponta, "longe", "colocado", 0.02),
            ),
        ],
    )
    if escolha == "encarar":
        if random.random() < chance_drible:
            registrar(partida, "um_contra_um_ok", dados, time_id=time_id)
            cara_a_cara(partida, time_id, ponta, 0.02, "fechar")
            return None
        registrar(partida, "driblar_erro", dados, tipo="perda", time_id=time_id)
        return contra_golpe(partida, time_id, "ataque", 0.15)
    if escolha == "cruzar":
        if random.random() < 0.6:
            cruzamento(partida, time_id, ponta, 0.02, "fechar")
            return None
        registrar(partida, "cruzar_erro", dados, tipo="perda", time_id=time_id)
        if random.random() < 0.3:
            cobrar_escanteio(partida, time_id, "fechar")
        return None
    if escolha == "ultrapassagem":
        if random.random() < 0.65:
            registrar(
                partida, "ultrapassagem", {"jogador": rotulo(apoio), "companheiro": rotulo(ponta)}, time_id=time_id
            )
            cruzamento(partida, time_id, apoio, 0.06, "fechar")
            return None
        registrar(partida, "passe_cortado", {"jogador": rotulo(ponta)}, tipo="perda", time_id=time_id)
        return contra_golpe(partida, time_id, "ataque", 0.15)
    entregar_bola(partida, time_id, "ataque", 1, ponta)
    finalizar(partida, time_id, ponta, "longe", "colocado", 0.02, "fechar")
    return None


def falta_na_meia_lua(partida, time_id, portador):
    """
    Falta a favor bem na meia-lua, a melhor posição para bater direto.

    O autor da falta leva amarelo em 27,5% das vezes. Bater no ângulo é um chute colocado com bônus alto; por
    baixo da barreira para nela em 15% das vezes, mas surpreende o goleiro; um rola e o outro bate é uma
    finalização de primeira do melhor atacante.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time que sofreu a falta.
        portador (dict): Jogador que sofreu a falta.

    Returns:
        tuple | None: Sempre None; a jogada termina na cobrança.
    """
    defensor_id = outro(partida, time_id)
    time = partida["times"][time_id]
    autor = marcador_de(partida, time_id, "ataque")
    partida["times"][defensor_id]["faltas"] += 1
    batedor = melhor_batedor(time)
    companheiro = atacante_de_referencia(time, batedor)
    entregar_bola(partida, time_id, "ataque", 1, batedor)
    registrar(
        partida,
        "falta_meia_lua",
        {"marcador": rotulo(autor), "jogador": rotulo(portador), "time": time["nome"]},
        tipo="bola_parada",
        time_id=time_id,
    )
    cartao_na_falta(partida, defensor_id, autor, 0.3)
    escolha = perguntar(
        partida,
        time_id,
        f"Falta na meia-lua! {rotulo(batedor)} ajeita a bola. Como bater?",
        [
            ("angulo", "Bater no ângulo", 3, chance_de_gol(partida, time_id, batedor, "falta", "colocado", 0.06)),
            (
                "baixo",
                "Por baixo da barreira",
                2,
                0.85 * chance_de_gol(partida, time_id, batedor, "falta", "colocado", 0.03),
            ),
            (
                "dois",
                f"Rolar para {rotulo(companheiro)} bater",
                2,
                chance_de_gol(partida, time_id, companheiro, "primeira", "forte", 0.05),
            ),
        ],
    )
    if escolha == "angulo":
        finalizar(partida, time_id, batedor, "falta", "colocado", 0.06, "fechar")
    elif escolha == "baixo":
        if random.random() < 0.15:
            registrar(partida, "barreira", tipo="defesa", time_id=time_id)
        else:
            finalizar(partida, time_id, batedor, "falta", "colocado", 0.03, "fechar")
    else:
        registrar(
            partida, "falta_rolada", {"jogador": rotulo(batedor), "companheiro": rotulo(companheiro)}, time_id=time_id
        )
        finalizar(partida, time_id, companheiro, "primeira", "forte", 0.05, "fechar")
    return None


def goleiro_pressionado(partida, time_id, portador):
    """
    O goleiro do time está com a bola na própria área e um atacante adversário vem pressionar.

    Driblar o atacante depende do passe do goleiro contra o desarme do atacante e, se der errado, o adversário
    fica com a bola quase sem goleiro. O chutão devolve a posse em metade das vezes. Tocar para o zagueiro dá
    certo em 80%; se for interceptado, o atacante chuta de dentro da área.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time do goleiro.
        portador (dict): Jogador usado se o time estiver sem goleiro.

    Returns:
        tuple | None: Contra-ataque de algum dos times, quando houver.
    """
    time = partida["times"][time_id]
    adversario_id = outro(partida, time_id)
    goleiro = goleiro_de(time) or portador
    atacante = escolher_jogador(partida["times"][adversario_id], PESOS_ATACANTE)
    zagueiro = escolher_jogador(time, {"DEF": 5, "MEI": 1})
    entregar_bola(partida, time_id, "saida", 1, goleiro)
    dados = {"goleiro": rotulo(goleiro), "jogador": rotulo(atacante)}
    registrar(partida, "goleiro_pressionado", dados, time_id=time_id)
    chance_drible = limitar(
        0.45 + (atributo_efetivo(goleiro, "pas") - atributo_efetivo(atacante, "des")) * 0.005, 0.15, 0.8
    )
    escolha = perguntar(
        partida,
        time_id,
        f"{rotulo(atacante)} vem pressionar {rotulo(goleiro)}! O que o goleiro faz?",
        [
            ("driblar", "Driblar o atacante", 1, chance_drible),
            ("chutao", "Dar um chutão para frente", 3, 0.5),
            ("zagueiro", f"Tocar para {rotulo(zagueiro)}", 3, 0.8),
        ],
    )
    if escolha == "driblar":
        if random.random() < chance_drible:
            registrar(partida, "goleiro_driblou", dados, tipo="oportunidade", time_id=time_id)
            return jogar_posse(partida, time_id, zona_inicial="defesa")
        entregar_bola(partida, adversario_id, "area", 1, atacante)
        registrar(partida, "goleiro_perdeu", dados, tipo="oportunidade", time_id=adversario_id)
        finalizar(partida, adversario_id, atacante, "area", "colocado", 0.25, "fechar")
        return None
    if escolha == "chutao":
        registrar(partida, "chutao", {"goleiro": rotulo(goleiro)}, time_id=time_id)
        if random.random() < 0.5:
            return jogar_posse(partida, time_id, zona_inicial="meio")
        return None
    if random.random() < 0.8:
        registrar(partida, "goleiro_tocou", {"goleiro": rotulo(goleiro), "jogador": rotulo(zagueiro)}, time_id=time_id)
        return jogar_posse(partida, time_id, portador=zagueiro, zona_inicial="defesa")
    entregar_bola(partida, adversario_id, "area", 1, atacante)
    registrar(partida, "interceptou_saida", dados, tipo="oportunidade", time_id=adversario_id)
    finalizar(partida, adversario_id, atacante, "area", "colocado", 0.05, "fechar")
    return None


def virada_de_jogo(partida, time_id, portador):
    """
    Um zagueiro tem a bola no campo de defesa e procura a melhor saída.

    Inverter para o lado livre depende do passe (70% de base) e começa a posse na intermediária; a ligação
    direta nas costas da zaga dá certo em 35% (mais com bom passe) e deixa o centroavante cara a cara; o toque
    curto começa uma posse com calma no campo de defesa. Errar a inversão pode dar contra-ataque.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time com a bola.
        portador (dict): Jogador que ganhou a bola no lance, não usado aqui.

    Returns:
        tuple | None: Contra-ataque de algum dos times, quando houver.
    """
    time = partida["times"][time_id]
    zagueiro = escolher_jogador(time, {"DEF": 5, "MEI": 2})
    lateral = escolher_jogador(time, {"DEF": 3, "MEI": 3}, excluir=zagueiro)
    centroavante = escolher_jogador(time, PESOS_ATACANTE)
    entregar_bola(partida, time_id, "defesa", random.choice((0, 2)), zagueiro)
    registrar(partida, "virada", {"jogador": rotulo(zagueiro), "time": time["nome"]}, time_id=time_id)
    passe = atributo_efetivo(zagueiro, "pas") - 70
    chance_inverter = limitar(0.7 + passe * 0.004, 0.3, 0.9)
    chance_ligacao = limitar(0.35 + passe * 0.004, 0.1, 0.6)
    escolha = perguntar(
        partida,
        time_id,
        f"{rotulo(zagueiro)} tem a bola no campo de defesa. Para onde?",
        [
            ("inverter", f"Inverter para {rotulo(lateral)}, livre do outro lado", 3, chance_inverter),
            ("ligacao", f"Ligação direta para {rotulo(centroavante)}", 2, chance_ligacao),
            ("paciencia", "Toque curto e paciência", 3, 1.0),
        ],
    )
    if escolha == "inverter":
        if random.random() < chance_inverter:
            registrar(
                partida, "virada_ok", {"jogador": rotulo(zagueiro), "companheiro": rotulo(lateral)}, time_id=time_id
            )
            return jogar_posse(partida, time_id, portador=lateral, zona_inicial="intermediaria")
        registrar(partida, "virada_erro", {"jogador": rotulo(zagueiro)}, tipo="perda", time_id=time_id)
        return contra_golpe(partida, time_id, "defesa", 0.3)
    if escolha == "ligacao":
        if random.random() < chance_ligacao:
            registrar(
                partida,
                "ligacao_ok",
                {"jogador": rotulo(zagueiro), "companheiro": rotulo(centroavante)},
                time_id=time_id,
            )
            cara_a_cara(partida, time_id, centroavante, 0.0, "fechar")
            return None
        registrar(partida, "ligacao_erro", {"jogador": rotulo(zagueiro)}, tipo="perda", time_id=time_id)
        return None
    return jogar_posse(partida, time_id, portador=zagueiro, zona_inicial="defesa")


def dois_contra_um(partida, time_id, portador):
    """
    Dois atacantes chegam contra um único zagueiro na entrada da área.

    Tocar para o companheiro depende do passe contra o desarme (65% de base) e o deixa cara a cara; chutar é
    uma finalização colocada de fora com bônus; driblar o último zagueiro é mais arriscado, mas também termina
    cara a cara, com bônus maior.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time com a bola.
        portador (dict): Jogador que ganhou a bola no lance, não usado aqui.

    Returns:
        tuple | None: Contra-ataque do adversário, quando houver.
    """
    time = partida["times"][time_id]
    condutor = escolher_jogador(time, PESOS_ATACANTE)
    companheiro = escolher_jogador(time, PESOS_ATACANTE, excluir=condutor)
    zagueiro = marcador_de(partida, time_id, "ataque")
    entregar_bola(partida, time_id, "ataque", 1, condutor)
    dados = {"jogador": rotulo(condutor), "companheiro": rotulo(companheiro), "marcador": rotulo(zagueiro)}
    registrar(partida, "dois_contra_um", dados, tipo="oportunidade", time_id=time_id)
    chance_passe = limitar(
        0.65 + (atributo_efetivo(condutor, "pas") - atributo_efetivo(zagueiro, "des")) * 0.004, 0.2, 0.9
    )
    tecnica = (atributo_efetivo(condutor, "fin") + atributo_efetivo(condutor, "fis")) / 2
    chance_drible = limitar(0.45 + (tecnica - atributo_efetivo(zagueiro, "des")) * 0.005, 0.15, 0.75)
    escolha = perguntar(
        partida,
        time_id,
        f"Dois contra um! {rotulo(condutor)} tem {rotulo(companheiro)} ao lado. O que fazer?",
        [
            ("tocar", f"Tocar para {rotulo(companheiro)}", 3, chance_passe),
            ("chutar", "Chutar", 2, chance_de_gol(partida, time_id, condutor, "longe", "colocado", 0.04)),
            ("driblar", "Driblar o último zagueiro", 2, chance_drible),
        ],
    )
    if escolha == "tocar":
        if random.random() < chance_passe:
            cara_a_cara(partida, time_id, companheiro, 0.05, "fechar")
            return None
        registrar(partida, "passe_cortado", {"jogador": rotulo(condutor)}, tipo="perda", time_id=time_id)
        return contra_golpe(partida, time_id, "ataque", 0.2)
    if escolha == "chutar":
        finalizar(partida, time_id, condutor, "longe", "colocado", 0.04, "fechar")
        return None
    if random.random() < chance_drible:
        registrar(partida, "drible_corte_ok", dados, time_id=time_id)
        cara_a_cara(partida, time_id, condutor, 0.08, "fechar")
        return None
    registrar(partida, "driblar_erro", dados, tipo="perda", time_id=time_id)
    return contra_golpe(partida, time_id, "ataque", 0.2)


def levantamento(partida, time_id, portador):
    """
    Um meia recebe na intermediária, a uns 35 metros do gol.

    Levantar na área chega em 60% das vezes e vira cruzamento; chutar da intermediária é um chute forte de
    longe, com pouca chance; tocar para o meia começa uma posse na intermediária.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time com a bola.
        portador (dict): Jogador que ganhou a bola no lance, não usado aqui.

    Returns:
        tuple | None: Contra-ataque do adversário, quando houver.
    """
    time = partida["times"][time_id]
    jogador = escolher_jogador(time, {"MEI": 5, "DEF": 2, "ATA": 1})
    entregar_bola(partida, time_id, "intermediaria", random.randint(0, 2), jogador)
    registrar(partida, "levantamento", {"jogador": rotulo(jogador), "time": time["nome"]}, time_id=time_id)
    escolha = perguntar(
        partida,
        time_id,
        f"{rotulo(jogador)} tem a bola na intermediária. E agora?",
        [
            ("levantar", "Levantar na área", 3, 0.6),
            (
                "chutar",
                "Chutar da intermediária",
                2,
                chance_de_gol(partida, time_id, jogador, "intermediaria", "forte"),
            ),
            ("tocar", "Tocar para o meia e construir", 3, 1.0),
        ],
    )
    if escolha == "levantar":
        if random.random() < 0.6:
            cruzamento(partida, time_id, jogador, -0.02, "fechar")
        else:
            registrar(partida, "escanteio_afastado", tipo="perda", time_id=time_id)
        return None
    if escolha == "chutar":
        finalizar(partida, time_id, jogador, "intermediaria", "forte", 0.0, "fechar")
        return None
    return jogar_posse(partida, time_id, zona_inicial="intermediaria")


def pivo(partida, time_id, portador):
    """
    O centroavante recebe de costas para o gol na entrada da área, com o zagueiro colado.

    Girar e chutar depende do físico contra o desarme (45% de base) e termina num chute da área; segurar e
    esperar o apoio começa uma posse na entrada da área com o meia; ajeitar de primeira chega ao meia em 70%
    das vezes, que bate de primeira.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time com a bola.
        portador (dict): Jogador que ganhou a bola no lance, não usado aqui.

    Returns:
        tuple | None: Contra-ataque do adversário, quando houver.
    """
    time = partida["times"][time_id]
    centroavante = escolher_jogador(time, {"ATA": 6, "MEI": 1})
    zagueiro = marcador_de(partida, time_id, "ataque")
    apoio = escolher_jogador(time, {"MEI": 5, "ATA": 2}, excluir=centroavante)
    entregar_bola(partida, time_id, "ataque", 1, centroavante)
    dados = {"jogador": rotulo(centroavante), "marcador": rotulo(zagueiro)}
    registrar(partida, "pivo", dados, time_id=time_id)
    chance_giro = limitar(
        0.45 + (atributo_efetivo(centroavante, "fis") - atributo_efetivo(zagueiro, "des")) * 0.005, 0.15, 0.75
    )
    escolha = perguntar(
        partida,
        time_id,
        f"{rotulo(centroavante)} recebe de costas, com {rotulo(zagueiro)} colado. O que fazer?",
        [
            (
                "girar",
                "Girar e chutar",
                3,
                chance_giro * chance_de_gol(partida, time_id, centroavante, "area", "colocado", 0.03),
            ),
            ("segurar", f"Segurar e esperar {rotulo(apoio)}", 3, 1.0),
            (
                "ajeitar",
                f"Ajeitar de primeira para {rotulo(apoio)}",
                3,
                0.7 * chance_de_gol(partida, time_id, apoio, "primeira", "forte", 0.04),
            ),
        ],
    )
    if escolha == "girar":
        if random.random() < chance_giro:
            registrar(partida, "pivo_girou", dados, time_id=time_id)
            finalizar(partida, time_id, centroavante, "area", "colocado", 0.03, "fechar")
            return None
        registrar(partida, "pivo_perdeu", dados, tipo="perda", time_id=time_id)
        return contra_golpe(partida, time_id, "ataque", 0.15)
    if escolha == "segurar":
        registrar(
            partida, "pivo_segurou", {"jogador": rotulo(centroavante), "companheiro": rotulo(apoio)}, time_id=time_id
        )
        return jogar_posse(partida, time_id, portador=apoio, zona_inicial="ataque")
    if random.random() < 0.7:
        registrar(partida, "escora", {"jogador": rotulo(centroavante), "companheiro": rotulo(apoio)}, time_id=time_id)
        finalizar(partida, time_id, apoio, "primeira", "forte", 0.04, "fechar")
        return None
    registrar(partida, "escora_erro", {"jogador": rotulo(centroavante)}, tipo="perda", time_id=time_id)
    return None


def contra_ataque_sofrido(partida, time_id, portador):
    """
    O time que ganhou a bola sai em contra-ataque e quem decide é o time que defende.

    A falta tática para a jogada na hora, com 42,5% de chance de amarelo. Recuar e fechar a área deixa o
    adversário atacar com calma, a partir da intermediária. O bote depende do desarme do zagueiro contra o
    físico do condutor (40% de base): dando certo, quem defendia puxa o contra-ataque; dando errado, o
    condutor fica cara a cara em metade das vezes ou segue em velocidade.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time que contra-ataca.
        portador (dict): Jogador que ganhou a bola no lance, não usado aqui.

    Returns:
        tuple | None: Contra-ataque de algum dos times, quando houver.
    """
    atacantes = partida["times"][time_id]
    defensor_id = outro(partida, time_id)
    defensor = partida["times"][defensor_id]
    condutor = escolher_jogador(atacantes, PESOS_ATACANTE)
    zagueiro = escolher_jogador(defensor, {"DEF": 5, "MEI": 2})
    entregar_bola(partida, time_id, "meio", 1, condutor)
    dados = {"jogador": rotulo(condutor), "marcador": rotulo(zagueiro), "time": atacantes["nome"]}
    registrar(partida, "contra_ataque_sofrido", dados, time_id=time_id)
    chance_bote = limitar(
        0.4 + (atributo_efetivo(zagueiro, "des") - atributo_efetivo(condutor, "fis")) * 0.005, 0.15, 0.7
    )
    escolha = perguntar(
        partida,
        defensor_id,
        f"Contra-ataque do {atacantes['nome']} com {rotulo(condutor)}! Como o {defensor['nome']} reage?",
        [
            ("falta", "Falta tática para parar", 2, 1.0),
            ("recuar", "Recuar e fechar a área", 3, 0.6),
            ("bote", f"{rotulo(zagueiro)} dá o bote", 3, chance_bote),
        ],
    )
    if escolha == "falta":
        defensor["faltas"] += 1
        registrar(partida, "falta_tatica", dados, tipo="falta", time_id=defensor_id)
        cartao_na_falta(partida, defensor_id, zagueiro, 0.45)
        return None
    if escolha == "recuar":
        registrar(partida, "recuou_contra", {"time": defensor["nome"]}, time_id=defensor_id)
        return jogar_posse(partida, time_id, portador=condutor, zona_inicial="intermediaria")
    if random.random() < chance_bote:
        registrar(partida, "bote_ok", {"marcador": rotulo(zagueiro), "time": defensor["nome"]}, time_id=defensor_id)
        return defensor_id, zagueiro
    registrar(partida, "bote_furado", dados, tipo="oportunidade", time_id=time_id)
    if random.random() < 0.5:
        cara_a_cara(partida, time_id, condutor, 0.05, "recuar")
        return None
    return jogar_posse(partida, time_id, contra_ataque=True, portador=condutor)


def reclamacao(partida):
    """
    Um jogador reclama demais com o árbitro e leva amarelo.

    Args:
        partida (dict): Estado da partida.
    """
    time_id = random.choice((partida["casa"], partida["fora"]))
    jogador = escolher_jogador(partida["times"][time_id], {"DEF": 2, "MEI": 2, "ATA": 2})
    registrar(partida, "reclamacao", {"jogador": rotulo(jogador)}, tipo="falta", time_id=time_id)
    amarelar(partida, time_id, jogador)


def confusao(partida):
    """
    Começa um empurra-empurra entre os jogadores; cada time tem 40% de chance de levar um amarelo.

    Args:
        partida (dict): Estado da partida.
    """
    casa = partida["times"][partida["casa"]]
    fora = partida["times"][partida["fora"]]
    registrar(partida, "confusao", {"time_casa": casa["nome"], "time_fora": fora["nome"]}, tipo="falta")
    for time_id in (partida["casa"], partida["fora"]):
        if random.random() < 0.4:
            jogador = escolher_jogador(partida["times"][time_id], {"DEF": 3, "MEI": 2, "ATA": 2})
            amarelar(partida, time_id, jogador)


def paralisacao(partida):
    """
    O jogo para por alguns minutos, e o árbitro aumenta os acréscimos em 1 ou 2 minutos.

    Args:
        partida (dict): Estado da partida.
    """
    registrar(partida, "paralisacao", tipo="evento")
    partida["limite"] = partida.get("limite", 45) + random.randint(1, 2)


def chuva_comeca(partida):
    """
    Começa a chover durante o jogo, o que deixa passes e cruzamentos mais difíceis dali em diante.

    Args:
        partida (dict): Estado da partida.
    """
    if partida["chuva"]:
        return
    partida["chuva"] = True
    registrar(partida, "chuva_comeca", tipo="evento")


def beira_do_campo(partida):
    """
    Narra algo que acontece fora das quatro linhas, sem efeito no jogo.

    Args:
        partida (dict): Estado da partida.
    """
    time_id = random.choice((partida["casa"], partida["fora"]))
    registrar(partida, "beira_do_campo", {"time": partida["times"][time_id]["nome"]}, tipo="evento", time_id=time_id)


FUNCOES_JOGADAS = {
    "tiro_de_meta": tiro_de_meta,
    "lateral_no_ataque": lateral_no_ataque,
    "superioridade": superioridade,
    "falta_lateral": falta_lateral,
    "falta_de_longe": falta_de_longe,
    "sobra_na_entrada": sobra_na_entrada,
    "erro_na_saida": erro_na_saida,
    "arrancada": arrancada,
    "pressao_na_saida": pressao_na_saida,
    "escanteio_conquistado": escanteio_conquistado,
    "bola_alta": bola_alta,
    "um_contra_um": um_contra_um,
    "falta_na_meia_lua": falta_na_meia_lua,
    "goleiro_pressionado": goleiro_pressionado,
    "virada_de_jogo": virada_de_jogo,
    "dois_contra_um": dois_contra_um,
    "levantamento": levantamento,
    "pivo": pivo,
    "contra_ataque_sofrido": contra_ataque_sofrido,
}
FUNCOES_ACONTECIMENTOS = {
    "reclamacao": reclamacao,
    "confusao": confusao,
    "paralisacao": paralisacao,
    "chuva_comeca": chuva_comeca,
    "beira_do_campo": beira_do_campo,
}


def jogada_especial(partida, time_id, portador):
    """
    Sorteia e joga uma das jogadas especiais para o time que ganhou a bola.

    A jogada é sorteada com os pesos de PESOS_JOGADAS e executada pela função correspondente em
    FUNCOES_JOGADAS.

    Args:
        partida (dict): Estado da partida.
        time_id (str): Time que ganhou a bola.
        portador (dict): Jogador que ganhou a bola.

    Returns:
        tuple | None: Contra-ataque de algum dos times, quando houver, como em jogar_posse.
    """
    tipo = random.choices(list(PESOS_JOGADAS), weights=list(PESOS_JOGADAS.values()))[0]
    return FUNCOES_JOGADAS[tipo](partida, time_id, portador)


def sortear_acontecimento(partida):
    """
    Sorteia no máximo um acontecimento extra antes do lance, como reclamação, confusão ou paralisação.

    Cada acontecimento tem a sua chance em CHANCES_ACONTECIMENTOS; o primeiro sorteado é executado.

    Args:
        partida (dict): Estado da partida.
    """
    for tipo, chance in CHANCES_ACONTECIMENTOS.items():
        if random.random() < chance:
            FUNCOES_ACONTECIMENTOS[tipo](partida)
            return
