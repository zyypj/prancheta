import random
from datetime import datetime

from config import (
    AGENDA,
    BONUS_COPA,
    BONUS_DESAFIO,
    BONUS_META,
    BONUS_OBJETIVO,
    BONUS_TITULO,
    CONFIANCA_AVANCO_COPA,
    CONFIANCA_DERROTA,
    CONFIANCA_EMPATE,
    CONFIANCA_INICIAL,
    CONFIANCA_QUEDA_COPA,
    CONFIANCA_TITULO_COPA,
    CONFIANCA_VITORIA,
    CONFIANCA_ZEBRA,
    DIFERENCA_FAVORITISMO,
    FASES_COPA,
    METAS,
    NIVEIS,
    NOMES_FASES,
    PONTOS_VITORIA,
    PREMIO_EMPATE,
    PREMIO_VITORIA,
    REPUTACAO_INICIAL,
    TOTAL_RODADAS,
    VERSAO_SAVE,
    ZONA_ACESSO,
    ZONA_REBAIXAMENTO,
)
from elenco.escalacao import completar_titulares, escalar_automatico, gerar_elenco
from elenco.substituicoes import preparar_proxima_rodada
from liga.calendario import gerar_calendario_das_divisoes, jogo_do_clube
from liga.copa import criar_copa, fase_neutra, preparar_fase, registrar_fase
from liga.financas import lancar, receber_bilheteria, receber_cota_tv
from liga.tabela import criar_tabela, ordenar_tabela, posicao_do_clube, registrar_resultado, saldo
from mercado.transferencias import gerar_agentes_livres
from partida.simulacao import simular_partida


def criar_estado_novo(tecnico, clube_id, clubes_base, banco_nomes):
    """
    Cria o estado inicial de uma nova temporada.

    Copia cada clube base, com a sua divisão, define o caixa inicial conforme o nível do clube, gera o elenco
    com nomes que não se repetem (guardando o último número de identificador usado) e escala os titulares
    automaticamente. Em seguida monta o calendário das duas
    divisões, a copa, os agentes livres e a tabela zerada, começando com a confiança da diretoria em
    CONFIANCA_INICIAL. A reputação do técnico começa conforme o nível do clube escolhido (REPUTACAO_INICIAL),
    com um ponto a menos na Série B, e a carreira começa na temporada 1.

    Args:
        tecnico (str): Nome do técnico.
        clube_id (str): Identificador do clube escolhido pelo jogador.
        clubes_base (list[dict]): Clubes lidos de times.json.
        banco_nomes (dict): Banco de nomes usado para gerar os jogadores.

    Returns:
        dict: Estado completo da nova temporada.
    """
    usados = set()
    clubes = {}
    for base in clubes_base:
        clube = dict(base)
        clube["plano"] = dict(base["plano"])
        clube["divisao"] = base.get("divisao", 1)
        clube["caixa"] = NIVEIS[clube["nivel"]]["caixa"]
        clube["elenco"] = gerar_elenco(clube, banco_nomes, usados)
        clube["ultimo_id"] = len(clube["elenco"])
        clube["titulares"] = escalar_automatico(clube["elenco"], clube["plano"]["formacao"])
        clubes[clube["id"]] = clube
    ids = list(clubes)
    return {
        "versao": VERSAO_SAVE,
        "tecnico": tecnico,
        "clube_id": clube_id,
        "clubes": clubes,
        "calendario": gerar_calendario_das_divisoes(clubes),
        "copa": criar_copa(clubes),
        "livres": gerar_agentes_livres(banco_nomes, usados),
        "etapa": 0,
        "rodada": 1,
        "tabela": criar_tabela(ids),
        "historico": [],
        "sumulas": {},
        "noticias": [],
        "confianca": CONFIANCA_INICIAL,
        "ultimos": [],
        "demitido": False,
        "encerrado": False,
        "temporada": 1,
        "carreira": [],
        "reputacao": max(0, REPUTACAO_INICIAL[clubes[clube_id]["nivel"]] - (clubes[clube_id]["divisao"] - 1)),
        "inicio": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }


def clube_do_jogador(estado):
    """
    Obtém o clube comandado pelo jogador.

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        dict: Clube do jogador.
    """
    return estado["clubes"][estado["clube_id"]]


def divisao_do_jogador(estado):
    """
    Obtém a divisão em que joga o clube do técnico.

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        int: 1 para a Série A ou 2 para a Série B.
    """
    return clube_do_jogador(estado).get("divisao", 1)


def meta_do_clube(clube):
    """
    Obtém a meta da diretoria de um clube, que depende do nível e da divisão (METAS).

    Na Série A, o grande quer o título, o médio o G4 e o pequeno não cair; na Série B, o grande quer o acesso,
    o médio brigar por ele e o pequeno ficar no meio da tabela.

    Args:
        clube (dict): Clube avaliado.

    Returns:
        tuple[str, int]: Texto da meta e a pior posição que ainda a cumpre.
    """
    return METAS[clube.get("divisao", 1)][clube["nivel"]]


def ids_da_divisao(estado, divisao):
    """
    Lista os clubes de uma divisão.

    Args:
        estado (dict): Estado atual da temporada.
        divisao (int): 1 para a Série A ou 2 para a Série B.

    Returns:
        list[str]: Identificadores dos clubes da divisão.
    """
    return [clube_id for clube_id, clube in estado["clubes"].items() if clube.get("divisao", 1) == divisao]


def etapa_atual(estado):
    """
    Obtém a etapa da agenda que está sendo disputada.

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        tuple | None: Competição ("liga" ou "copa") e rodada ou fase, ou None se a agenda já terminou.
    """
    if estado["etapa"] >= len(AGENDA):
        return None
    return AGENDA[estado["etapa"]]


def descricao_etapa(etapa):
    """
    Monta o texto que identifica uma etapa da agenda.

    Args:
        etapa (tuple): Competição ("liga" ou "copa") e rodada ou fase.

    Returns:
        str: Texto como "Liga — rodada 3/9" ou "Copa — Semifinal".
    """
    competicao, valor = etapa
    if competicao == "liga":
        return f"Liga — rodada {valor}/{TOTAL_RODADAS}"
    return f"Copa — {NOMES_FASES[valor]}"


def fazer_aniversario(jogador, etapa):
    """
    Deixa o jogador um ano mais velho se o aniversário dele cai na etapa informada.

    Jogadores de saves antigos, que ainda não têm aniversário, ganham um sorteado entre as etapas da agenda.

    Args:
        jogador (dict): Jogador avaliado.
        etapa (int): Índice da etapa que está terminando.

    Returns:
        bool: True se o jogador fez aniversário.
    """
    if "aniversario" not in jogador:
        jogador["aniversario"] = random.randrange(len(AGENDA))
    if jogador["aniversario"] != etapa:
        return False
    jogador["idade"] = jogador.get("idade", 26) + 1
    return True


def comemorar_aniversarios(estado):
    """
    Faz os aniversários da etapa atual, em todos os elencos e entre os jogadores sem clube.

    Cada jogador faz aniversário uma vez por temporada, ao fim da etapa sorteada para ele, então as idades vão
    mudando ao longo do ano e não todas de uma vez na virada.

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        list[dict]: Jogadores do clube do técnico que fizeram aniversário.
    """
    etapa = estado["etapa"]
    do_tecnico = []
    for clube in estado["clubes"].values():
        for jogador in clube["elenco"]:
            if fazer_aniversario(jogador, etapa) and clube["id"] == estado["clube_id"]:
                do_tecnico.append(jogador)
    for jogador in estado.get("livres", []):
        fazer_aniversario(jogador, etapa)
    return do_tecnico


def jogos_da_rodada(estado, rodada=None):
    """
    Obtém os jogos de uma rodada da liga.

    Args:
        estado (dict): Estado atual da temporada.
        rodada (int | None): Número da rodada, começando em 1. Padrão: None, que usa a rodada atual da liga.

    Returns:
        list[tuple[str, str]]: Jogos da rodada no formato (mandante, visitante).
    """
    numero = rodada or estado["rodada"]
    return estado["calendario"][numero - 1]


def jogos_da_etapa(estado):
    """
    Obtém os jogos da etapa atual, seja uma rodada da liga ou uma fase da copa.

    Na copa, os confrontos da fase são montados se ainda não existirem.

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        list[tuple[str, str]]: Jogos da etapa no formato (mandante, visitante).
    """
    competicao, valor = etapa_atual(estado)
    if competicao == "liga":
        return jogos_da_rodada(estado, valor)
    return preparar_fase(estado["copa"], valor)


def jogo_neutro(estado):
    """
    Indica se os jogos da etapa atual são em campo neutro, o que só acontece na final da copa.

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        bool: True se a etapa for uma fase neutra da copa.
    """
    competicao, valor = etapa_atual(estado)
    return competicao == "copa" and fase_neutra(valor)


def mata_mata(estado):
    """
    Indica se a etapa atual é eliminatória, ou seja, uma fase da copa.

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        bool: True se a etapa for da copa.
    """
    return etapa_atual(estado)[0] == "copa"


def jogo_do_jogador(estado):
    """
    Obtém o jogo do clube do jogador na etapa atual.

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        tuple[str, str] | None: Jogo no formato (mandante, visitante) ou None se o clube não joga nessa etapa.
    """
    return jogo_do_clube(jogos_da_etapa(estado), estado["clube_id"])


def adversario_de(jogo, clube_id):
    """
    Identifica o adversário de um clube em um jogo.

    Args:
        jogo (tuple[str, str]): Jogo no formato (mandante, visitante).
        clube_id (str): Identificador do clube.

    Returns:
        str: Identificador do outro clube do jogo.
    """
    return jogo[1] if jogo[0] == clube_id else jogo[0]


def simular_outros_jogos(estado, frases):
    """
    Simula todos os jogos da etapa atual, menos o do clube do jogador.

    Cada partida respeita o campo neutro e o caráter eliminatório da etapa.

    Args:
        estado (dict): Estado atual da temporada.
        frases (dict): Frases de narração usadas na simulação.

    Returns:
        list[dict]: Resultados das partidas simuladas.
    """
    jogo = jogo_do_jogador(estado)
    return [
        simular_partida(estado["clubes"][casa], estado["clubes"][fora], frases, jogo_neutro(estado), mata_mata(estado))
        for casa, fora in jogos_da_etapa(estado)
        if (casa, fora) != jogo
    ]


def classificacao(estado, divisao=None):
    """
    Obtém a classificação atual de uma divisão, já com os critérios de desempate aplicados.

    Args:
        estado (dict): Estado atual da temporada.
        divisao (int | None): Divisão a classificar. Padrão None, que usa a divisão do clube do técnico.

    Returns:
        list[dict]: Linhas da tabela do primeiro ao último colocado da divisão.
    """
    ids = set(ids_da_divisao(estado, divisao or divisao_do_jogador(estado)))
    tabela = {clube_id: linha for clube_id, linha in estado["tabela"].items() if clube_id in ids}
    return ordenar_tabela(tabela, estado["historico"])


def posicao_atual(estado):
    """
    Obtém a posição atual do clube do jogador na sua divisão.

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        int: Posição do clube na classificação, começando em 1.
    """
    return posicao_do_clube(classificacao(estado), estado["clube_id"])


def titulo_garantido(estado):
    """
    Verifica se o clube do jogador já não pode mais perder o título da sua divisão.

    Com a liga encerrada, basta estar em primeiro. Antes disso, a vantagem de pontos sobre o segundo colocado
    precisa ser maior do que os pontos que ainda estão em disputa. Técnico demitido não conquista o título.

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        bool: True se o título da liga está garantido.
    """
    linhas = classificacao(estado)
    if estado["demitido"] or posicao_do_clube(linhas, estado["clube_id"]) != 1:
        return False
    restantes = TOTAL_RODADAS - len(estado["historico"])
    return restantes == 0 or linhas[0]["pontos"] > linhas[1]["pontos"] + restantes * PONTOS_VITORIA


def gols_do_clube(clube_id, resultado):
    """
    Obtém os gols marcados e sofridos por um clube em um jogo.

    Args:
        clube_id (str): Identificador do clube.
        resultado (dict): Resultado da partida.

    Returns:
        tuple[int, int]: Gols marcados e gols sofridos pelo clube.
    """
    if resultado["mandante"] == clube_id:
        return resultado["gm"], resultado["gv"]
    return resultado["gv"], resultado["gm"]


def resultado_para(clube_id, resultado):
    """
    Classifica o resultado de um jogo do ponto de vista de um clube, considerando apenas os gols.

    Args:
        clube_id (str): Identificador do clube.
        resultado (dict): Resultado da partida.

    Returns:
        str: "V" para vitória, "E" para empate ou "D" para derrota.
    """
    feitos, sofridos = gols_do_clube(clube_id, resultado)
    if feitos > sofridos:
        return "V"
    if feitos == sofridos:
        return "E"
    return "D"


def ultimos_resultados(estado, clube_id, quantidade=5):
    """
    Lista os resultados mais recentes de um clube na liga.

    Percorre o histórico da liga em ordem e guarda a letra de cada jogo do clube; jogos da copa não entram.

    Args:
        estado (dict): Estado atual da temporada.
        clube_id (str): Identificador do clube.
        quantidade (int): Quantidade máxima de resultados. Padrão: 5.

    Returns:
        list[str]: Letras "V", "E" ou "D", do jogo mais antigo para o mais recente.
    """
    letras = []
    for rodada in estado["historico"]:
        for jogo in rodada:
            if clube_id in (jogo["mandante"], jogo["visitante"]):
                letras.append(resultado_para(clube_id, jogo))
    return letras[-quantidade:]


def diferenca_de_forca(estado, adversario_id):
    """
    Calcula a diferença de força entre o clube do jogador e um adversário.

    Args:
        estado (dict): Estado atual da temporada.
        adversario_id (str): Identificador do adversário.

    Returns:
        int: Força do clube do jogador menos a força do adversário; valor positivo indica que o jogador é o
            favorito.
    """
    return clube_do_jogador(estado)["forca"] - estado["clubes"][adversario_id]["forca"]


def variacao_de_confianca(estado, resultado):
    """
    Calcula quanto a confiança da diretoria muda após um jogo da liga.

    A vitória vale CONFIANCA_VITORIA (+6), o empate CONFIANCA_EMPATE (0) e a derrota CONFIANCA_DERROTA (-8).
    Quando a diferença de força passa de DIFERENCA_FAVORITISMO (5), há zebra: vencer um adversário mais forte
    rende CONFIANCA_ZEBRA (4) a mais, e perder para um mais fraco custa CONFIANCA_ZEBRA a mais.

    Args:
        estado (dict): Estado atual da temporada.
        resultado (dict): Resultado do jogo do clube do jogador.

    Returns:
        tuple[str, int]: Letra do resultado ("V", "E" ou "D") e variação da confiança.
    """
    clube_id = estado["clube_id"]
    adversario = adversario_de((resultado["mandante"], resultado["visitante"]), clube_id)
    diferenca = diferenca_de_forca(estado, adversario)
    letra = resultado_para(clube_id, resultado)
    variacao = {"V": CONFIANCA_VITORIA, "E": CONFIANCA_EMPATE, "D": CONFIANCA_DERROTA}[letra]
    if letra == "V" and diferenca < -DIFERENCA_FAVORITISMO:
        variacao += CONFIANCA_ZEBRA
    elif letra == "D" and diferenca > DIFERENCA_FAVORITISMO:
        variacao -= CONFIANCA_ZEBRA
    return letra, variacao


def ajustar_confianca(estado, variacao):
    """
    Aplica uma variação à confiança da diretoria.

    A confiança fica limitada entre 0 e 100; se chegar a 0, o técnico é demitido.

    Args:
        estado (dict): Estado atual da temporada.
        variacao (int): Valor a somar à confiança, positivo ou negativo.
    """
    estado["confianca"] = max(0, min(100, estado["confianca"] + variacao))
    if estado["confianca"] <= 0:
        estado["demitido"] = True


def pagar_premios(estado, resultado):
    """
    Paga a premiação de um jogo da liga aos dois clubes.

    Cada clube recebe no caixa, como "Premiação por resultado", PREMIO_VITORIA (0,8) pela vitória,
    PREMIO_EMPATE (0,3) pelo empate e nada pela derrota.

    Args:
        estado (dict): Estado atual da temporada.
        resultado (dict): Resultado da partida.
    """
    for clube_id in (resultado["mandante"], resultado["visitante"]):
        letra = resultado_para(clube_id, resultado)
        premio = PREMIO_VITORIA if letra == "V" else (PREMIO_EMPATE if letra == "E" else 0)
        lancar(estado, clube_id, "Premiação por resultado", premio)


def preparar_elencos(estado):
    """
    Prepara os elencos de todos os clubes para o próximo jogo.

    Atualiza suspensões, lesões, grande fase e energia de cada jogador. No clube do jogador, completa os
    titulares que ficaram indisponíveis; nos demais clubes, refaz a escalação automaticamente.

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        list[str]: Titulares do clube do jogador que precisaram ser trocados.
    """
    trocados = []
    for clube in estado["clubes"].values():
        preparar_proxima_rodada(clube["elenco"])
        if clube["id"] == estado["clube_id"]:
            trocados = completar_titulares(clube)
        else:
            clube["titulares"] = escalar_automatico(clube["elenco"], clube["plano"]["formacao"])
    return trocados


def fechar_rodada(estado, resultados):
    """
    Encerra uma rodada da liga.

    Registra cada resultado na tabela, paga os prêmios e a bilheteria do mandante, guarda a rodada no
    histórico e paga a cota de TV a todos os clubes. Depois calcula a variação de confiança pelo jogo do clube
    do jogador, atualiza a sequência dos últimos 5 resultados, aplica a confiança, prepara os elencos e avança
    o número da rodada. Também indica se o título da liga foi garantido nesta rodada.

    Args:
        estado (dict): Estado atual da temporada.
        resultados (list[dict]): Resultados de todos os jogos da rodada, incluindo o do jogador.

    Returns:
        dict: Letra do resultado do jogador, variação da confiança, titulares trocados e o título conquistado
            na rodada ("liga" ou None).
    """
    ja_garantido = titulo_garantido(estado)
    rodada = []
    for resultado in resultados:
        registrar_resultado(estado["tabela"], resultado)
        pagar_premios(estado, resultado)
        receber_bilheteria(estado, resultado)
        rodada.append({chave: resultado[chave] for chave in ("mandante", "visitante", "gm", "gv")})
    estado["historico"].append(rodada)
    receber_cota_tv(estado)
    do_jogador = next(
        resultado for resultado in resultados if estado["clube_id"] in (resultado["mandante"], resultado["visitante"])
    )
    letra, variacao = variacao_de_confianca(estado, do_jogador)
    estado["ultimos"] = (estado["ultimos"] + [letra])[-5:]
    ajustar_confianca(estado, variacao)
    trocados = preparar_elencos(estado)
    estado["rodada"] += 1
    conquistou = titulo_garantido(estado) and not ja_garantido
    return {"letra": letra, "variacao": variacao, "trocados": trocados, "titulo": "liga" if conquistou else None}


def fechar_fase_copa(estado, resultados):
    """
    Encerra uma fase da copa.

    Registra os resultados da fase e paga a bilheteria de cada jogo (dividida na final, em campo neutro). Se o
    clube do jogador jogou, avançar conta como "V" e soma
    CONFIANCA_AVANCO_COPA (3), ou CONFIANCA_TITULO_COPA (10) na final; ser eliminado conta como "D" e aplica
    CONFIANCA_QUEDA_COPA (-4), com CONFIANCA_ZEBRA (4) a menos se o adversário era mais fraco por mais de
    DIFERENCA_FAVORITISMO (5). Por fim, prepara os elencos e indica se o clube do jogador ganhou a final.

    Args:
        estado (dict): Estado atual da temporada.
        resultados (list[dict]): Resultados de todos os jogos da fase.

    Returns:
        dict: Letra do resultado do jogador (ou None se ele não jogou), variação da confiança, titulares
            trocados, o jogo do jogador e o título conquistado na fase ("copa" ou None).
    """
    fase = etapa_atual(estado)[1]
    jogo = registrar_fase(estado, fase, resultados)
    for resultado in resultados:
        receber_bilheteria(estado, resultado, fase_neutra(fase))
    variacao = 0
    letra = None
    if jogo:
        passou = jogo["vencedor"] == estado["clube_id"]
        letra = "V" if passou else "D"
        if passou:
            variacao = CONFIANCA_TITULO_COPA if fase == FASES_COPA[-1] else CONFIANCA_AVANCO_COPA
        else:
            adversario = adversario_de((jogo["mandante"], jogo["visitante"]), estado["clube_id"])
            variacao = CONFIANCA_QUEDA_COPA
            if diferenca_de_forca(estado, adversario) > DIFERENCA_FAVORITISMO:
                variacao -= CONFIANCA_ZEBRA
        estado["ultimos"] = (estado["ultimos"] + [letra])[-5:]
        ajustar_confianca(estado, variacao)
    trocados = preparar_elencos(estado)
    conquistou = fase == FASES_COPA[-1] and estado["copa"]["campeao"] == estado["clube_id"]
    return {
        "letra": letra,
        "variacao": variacao,
        "trocados": trocados,
        "jogo": jogo,
        "titulo": "copa" if conquistou else None,
    }


def avancar_etapa(estado):
    """
    Avança para a próxima etapa da agenda.

    Se a agenda acabou, marca a temporada como encerrada; se a próxima etapa for da copa, já monta os
    confrontos da fase.

    Args:
        estado (dict): Estado atual da temporada.
    """
    estado["etapa"] += 1
    proxima = etapa_atual(estado)
    if proxima is None:
        estado["encerrado"] = True
    elif proxima[0] == "copa":
        preparar_fase(estado["copa"], proxima[1])


def temporada_acabou(estado):
    """
    Indica se a temporada terminou, por demissão do técnico ou pelo fim da agenda.

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        bool: True se a temporada terminou.
    """
    return estado["demitido"] or estado["encerrado"]


def meta_cumprida(estado, posicao):
    """
    Verifica se a posição alcança a meta do clube do jogador.

    A meta é terminar na posição definida por meta_do_clube ou acima dela: na Série A, 1º para clube grande,
    4º para médio e 8º para pequeno; na Série B, 2º, 4º e 6º.

    Args:
        estado (dict): Estado atual da temporada.
        posicao (int): Posição do clube na liga.

    Returns:
        bool: True se a meta foi cumprida.
    """
    return posicao <= meta_do_clube(clube_do_jogador(estado))[1]


def resumo_final(estado):
    """
    Monta o resumo da temporada do técnico, usado na tela final e no ranking.

    A pontuação é (pontos × 10 + saldo × 2 + bônus) multiplicada pelo multiplicador do nível do clube, nunca
    abaixo de zero. Os bônus são BONUS_META (300) por cumprir a meta, BONUS_TITULO (200) pelo título da Série
    A (metade pelo da Série B) e BONUS_COPA (250) pelo título da copa, mais BONUS_DESAFIO (25) por desafio da
    diretoria cumprido e BONUS_OBJETIVO (60) por objetivo da temporada alcançado; técnico demitido não recebe
    os bônus de meta e de título da liga. O desfecho informa a demissão (com a etapa em que aconteceu), o
    título (feito histórico se o clube não for grande), o acesso, o rebaixamento, a meta cumprida ou não, e
    acrescenta o título da copa quando houver e, a partir da segunda temporada, o número dela.

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        dict: Técnico, clube, divisão, temporada, posição, pontos, saldo, pontuação, desfecho, se a meta foi
            cumprida, a meta, se ganhou a copa e a data.
    """
    clube = clube_do_jogador(estado)
    nivel = NIVEIS[clube["nivel"]]
    divisao = clube.get("divisao", 1)
    linha = estado["tabela"][clube["id"]]
    posicao = posicao_atual(estado)
    titulo = posicao == 1 and not estado["demitido"]
    copa = estado["copa"]["campeao"] == clube["id"]
    cumpriu = meta_cumprida(estado, posicao) and not estado["demitido"]
    bonus_titulo = BONUS_TITULO if divisao == 1 else BONUS_TITULO // 2
    bonus = (BONUS_META if cumpriu else 0) + (bonus_titulo if titulo else 0) + (BONUS_COPA if copa else 0)
    desafios = estado.get("desafios_cumpridos", 0)
    objetivos = len(estado.get("objetivos", []))
    bonus += desafios * BONUS_DESAFIO + objetivos * BONUS_OBJETIVO
    pontuacao = round((linha["pontos"] * 10 + saldo(linha) * 2 + bonus) * nivel["multiplicador"])
    if estado["demitido"]:
        desfecho = f"demitido ({descricao_etapa(AGENDA[max(0, estado['etapa'] - 1)])})"
    elif titulo and divisao == 2:
        desfecho = "campeão da Série B"
    elif titulo and clube["nivel"] != "grande":
        desfecho = "campeão (feito histórico)"
    elif titulo:
        desfecho = "campeão"
    elif divisao == 2 and posicao <= ZONA_ACESSO:
        desfecho = "acesso à Série A"
    elif divisao == 1 and posicao > len(ids_da_divisao(estado, 1)) - ZONA_REBAIXAMENTO:
        desfecho = "rebaixado"
    elif cumpriu:
        desfecho = "meta cumprida"
    else:
        desfecho = "meta não cumprida"
    if copa:
        desfecho += " + campeão da copa"
    temporada = estado.get("temporada", 1)
    if temporada > 1:
        desfecho += f" ({temporada}ª temporada)"
    return {
        "tecnico": estado["tecnico"],
        "clube": clube["nome"],
        "divisao": divisao,
        "temporada": temporada,
        "posicao": posicao,
        "pontos": linha["pontos"],
        "saldo": saldo(linha),
        "pontuacao": max(0, pontuacao),
        "desfecho": desfecho,
        "venceu": cumpriu,
        "meta": meta_do_clube(clube)[0],
        "copa": copa,
        "desafios": desafios,
        "objetivos": objetivos,
        "data": datetime.now().strftime("%d/%m/%Y"),
    }
