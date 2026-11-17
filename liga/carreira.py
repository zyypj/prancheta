import random

from config import (
    AGENTES_LIVRES,
    CHANCE_CONVITE,
    CHANCE_JOIA_DA_BASE,
    COMPOSICAO_ELENCO,
    CONFIANCA_INICIAL,
    DIVISOES,
    EVOLUCAO_POR_IDADE,
    FOLGA_DOS_TITULARES,
    IDADE_APOSENTADORIA,
    IDADE_LIMITE,
    MAX_ELENCO,
    METAS,
    NIVEIS,
    PESO_DO_NIVEL,
    PREMIO_ACESSO,
    PREMIO_CAMPEAO,
    PROPOSTAS_NA_JANELA,
    REPUTACAO_INICIAL,
    REPUTACAO_MAXIMA,
    VERSAO_SAVE,
    ZONA_ACESSO,
    ZONA_REBAIXAMENTO,
)
from elenco.escalacao import completar_titulares, escalar_automatico, gerar_elenco, limitar
from elenco.substituicoes import preparar_proxima_rodada
from liga.calendario import gerar_calendario, gerar_calendario_das_divisoes
from liga.copa import criar_copa
from liga.eventos import criar_proposta, nomes_em_uso, novo_garoto
from liga.financas import lancar
from liga.tabela import criar_tabela, posicao_do_clube, registrar_resultado
from liga.temporada import classificacao, clube_do_jogador, ultimos_resultados
from mercado.transferencias import criar_agente_livre, dinheiro, noticia, quantos_na_posicao
from partida.simulacao import simular_partida

ATRIBUTOS = ("fin", "pas", "des", "fis", "ref")


def fechar_divisoes(estado):
    """
    Fecha as duas divisões no fim da temporada: premia os campeões e troca quem sobe e quem cai.

    Guarda a classificação final de cada divisão em estado["classificacao_final"]. O campeão da Série A
    recebe PREMIO_CAMPEAO[1] (6 milhões) e o da Série B PREMIO_CAMPEAO[2] (3 milhões). Os ZONA_ACESSO (2)
    primeiros da Série B sobem, recebem PREMIO_ACESSO (2 milhões) e passam para a divisão 1; os
    ZONA_REBAIXAMENTO (2) últimos da Série A passam para a divisão 2. Deve ser chamada depois de montar o
    resumo da temporada, que usa a divisão antiga do clube do técnico.

    Args:
        estado (dict): Estado da temporada que acabou.

    Returns:
        dict: Campeão de cada divisão, clubes que subiram, clubes que caíram e as linhas de premiação.
    """
    final = {divisao: [linha["id"] for linha in classificacao(estado, divisao)] for divisao in DIVISOES}
    estado["classificacao_final"] = final
    premios = []
    campeoes = {}
    for divisao, ordem in final.items():
        if not ordem:
            continue
        campeao = estado["clubes"][ordem[0]]
        campeoes[divisao] = campeao["id"]
        lancar(estado, campeao["id"], "Premiação do campeonato", PREMIO_CAMPEAO[divisao])
        premios.append(f"{campeao['nome']}, campeão da {DIVISOES[divisao]}: +{dinheiro(PREMIO_CAMPEAO[divisao])}")
    subiram = final[2][:ZONA_ACESSO] if final[2] else []
    cairam = final[1][-ZONA_REBAIXAMENTO:] if final[2] else []
    for clube_id in subiram:
        estado["clubes"][clube_id]["divisao"] = 1
        lancar(estado, clube_id, "Premiação do acesso", PREMIO_ACESSO)
        premios.append(f"{estado['clubes'][clube_id]['nome']}, acesso à Série A: +{dinheiro(PREMIO_ACESSO)}")
    for clube_id in cairam:
        estado["clubes"][clube_id]["divisao"] = 2
    return {"campeoes": campeoes, "subiram": subiram, "cairam": cairam, "premios": premios}


def fase_alcancada_na_copa(copa, clube_id):
    """
    Descobre até onde um clube chegou na copa.

    Args:
        copa (dict): Estrutura da copa na temporada.
        clube_id (str): Identificador do clube.

    Returns:
        str | None: "campeão", "final" ou "semifinal", ou None se o clube não chegou à semifinal.
    """
    if copa["campeao"] == clube_id:
        return "campeão"
    for fase in ("final", "semifinal"):
        if any(clube_id in jogo for jogo in copa["confrontos"].get(fase, [])):
            return fase
    return None


def avaliar_diretoria(estado, resumo):
    """
    Decide se o técnico continua no clube depois da temporada.

    Quem cumpriu a meta é renovado. Quem não cumpriu ainda pode ganhar uma segunda chance se jogou bem: a
    nota parte da confiança da diretoria, perde 6 pontos por posição abaixo da meta e 15 se o clube caiu, e
    ganha 10 pela semifinal ou final da copa, 25 pelo título dela, 4 por objetivo da temporada e 5 por ter
    cumprido 6 desafios ou mais. A chance de continuar é (nota - 15) × 1,5 por cento, entre 5% e 90%.

    Args:
        estado (dict): Estado da temporada que acabou.
        resumo (dict): Resumo da temporada, montado por resumo_final.

    Returns:
        dict: Decisão ("renovado", "segunda_chance" ou "demitido"), o que pesou a favor, o que pesou contra
            e a chance de continuar, em porcentagem.
    """
    clube = clube_do_jogador(estado)
    a_favor = []
    contra = []
    confianca = estado["confianca"]
    if resumo["venceu"]:
        a_favor.append(f"meta cumprida ({resumo['meta']}, terminou em {resumo['posicao']}º)")
        return {"decisao": "renovado", "a_favor": a_favor, "contra": contra, "chance": 100}
    nota = confianca
    (a_favor if confianca >= 50 else contra).append(f"confiança da diretoria em {confianca}%")
    distancia = resumo["posicao"] - METAS[resumo["divisao"]][clube["nivel"]][1]
    nota -= 6 * distancia
    contra.append(f"terminou {distancia} posição(ões) abaixo da meta ({resumo['meta']})")
    if resumo["desfecho"].startswith("rebaixado"):
        nota -= 15
        contra.append("o clube foi rebaixado")
    fase = fase_alcancada_na_copa(estado["copa"], clube["id"])
    if fase == "campeão":
        nota += 25
        a_favor.append("título da copa")
    elif fase:
        nota += 10
        a_favor.append(f"chegou à {fase} da copa")
    if resumo["objetivos"]:
        nota += 4 * resumo["objetivos"]
        a_favor.append(f"{resumo['objetivos']} objetivo(s) da temporada")
    if resumo["desafios"] >= 6:
        nota += 5
        a_favor.append(f"{resumo['desafios']} desafios da diretoria cumpridos")
    chance = limitar(round((nota - 15) * 1.5), 5, 90)
    decisao = "segunda_chance" if random.randint(1, 100) <= chance else "demitido"
    return {"decisao": decisao, "a_favor": a_favor, "contra": contra, "chance": chance}


def atualizar_reputacao(estado, resumo, demitido):
    """
    Ajusta a reputação do técnico, que define os clubes que se interessam por ele.

    Cumprir a meta soma 1, ser campeão da liga ou da copa soma mais 1 e ser demitido tira 1. A reputação fica
    entre 0 e REPUTACAO_MAXIMA (5).

    Args:
        estado (dict): Estado da carreira.
        resumo (dict): Resumo da temporada ou do trecho dela no clube.
        demitido (bool): Se o técnico foi demitido.

    Returns:
        int: Variação aplicada.
    """
    variacao = (1 if resumo["venceu"] else 0) - (1 if demitido else 0)
    if resumo["desfecho"].startswith("campeão") or resumo.get("copa"):
        variacao += 1
    antes = estado.get("reputacao", 2)
    estado["reputacao"] = limitar(antes + variacao, 0, REPUTACAO_MAXIMA)
    return estado["reputacao"] - antes


def patamar(clube):
    """
    Mede o tamanho do cargo de técnico de um clube, de 1 a 4.

    Soma o peso do nível (PESO_DO_NIVEL: grande 3, médio 2, pequeno 1) e 1 se o clube está na Série A.

    Args:
        clube (dict): Clube avaliado.

    Returns:
        int: Patamar do clube.
    """
    return PESO_DO_NIVEL[clube["nivel"]] + (1 if clube.get("divisao", 1) == 1 else 0)


def propostas_de_emprego(estado, motivo):
    """
    Monta as propostas de outros clubes para o técnico.

    Depois de uma demissão, de 2 a 3 clubes com patamar até a reputação mais 1 oferecem o cargo; no meio da
    temporada, os que estão na metade de baixo da sua divisão têm o dobro de chance de aparecer, porque
    acabaram de mandar o técnico embora. Se nenhum clube servir, os de menor patamar fazem a proposta. Depois
    de uma temporada com a meta cumprida, há CHANCE_CONVITE (45%) de 1 ou 2 clubes maiores que o atual, até a
    reputação mais 1, fazerem um convite.

    Args:
        estado (dict): Estado da carreira.
        motivo (str): "demitido" ou "convite".

    Returns:
        list[dict]: Propostas com o identificador do clube e o motivo do interesse.
    """
    atual = clube_do_jogador(estado)
    outros = [clube for clube in estado["clubes"].values() if clube["id"] != atual["id"]]
    reputacao = estado.get("reputacao", 2)
    if motivo == "convite":
        candidatos = [clube for clube in outros if patamar(atual) < patamar(clube) <= reputacao + 1]
        if not candidatos or random.random() >= CHANCE_CONVITE:
            return []
        escolhidos = random.sample(candidatos, min(len(candidatos), random.randint(1, 2)))
        return [{"clube_id": clube["id"], "motivo": "quer contratar você"} for clube in escolhidos]
    candidatos = [clube for clube in outros if patamar(clube) <= reputacao + 1]
    if not candidatos:
        menor = min(patamar(clube) for clube in outros)
        candidatos = [clube for clube in outros if patamar(clube) == menor]
    meio_da_temporada = not estado["encerrado"]
    pesos = []
    for clube in candidatos:
        divisao = classificacao(estado, clube.get("divisao", 1))
        mal = posicao_do_clube(divisao, clube["id"]) > len(divisao) / 2
        pesos.append(2 if meio_da_temporada and mal else 1)
    escolhidos = []
    for _ in range(min(len(candidatos), random.randint(2, 3))):
        indice = random.choices(range(len(candidatos)), pesos)[0]
        escolhidos.append(candidatos.pop(indice))
        pesos.pop(indice)
    texto = "demitiu o técnico" if meio_da_temporada else "procura técnico"
    return [{"clube_id": clube["id"], "motivo": texto} for clube in escolhidos]


def assumir_clube(estado, clube_id):
    """
    Troca o clube comandado pelo técnico.

    O clube antigo passa para a IA, que refaz a escalação. No novo clube, a confiança da diretoria começa em
    CONFIANCA_INICIAL e os desafios, objetivos, extrato e treino da temporada recomeçam do zero; os últimos
    resultados passam a ser os do novo clube. A troca vira notícia.

    Args:
        estado (dict): Estado da carreira.
        clube_id (str): Clube que o técnico assume.
    """
    antigo = clube_do_jogador(estado)
    antigo["titulares"] = escalar_automatico(antigo["elenco"], antigo["plano"]["formacao"])
    estado["clube_id"] = clube_id
    estado["confianca"] = CONFIANCA_INICIAL
    estado["demitido"] = False
    estado["ultimos"] = ultimos_resultados(estado, clube_id)
    estado["objetivos"] = []
    estado["desafios_cumpridos"] = 0
    estado["financas"] = {}
    for chave in ("desafio", "treino_etapa", "torcida_extra", "promessa", "extrato_etapa"):
        estado.pop(chave, None)
    completar_titulares(clube_do_jogador(estado))
    noticia(estado, f"{estado['tecnico']} é o novo técnico do {clube_do_jogador(estado)['nome']}.")


def registrar_na_carreira(estado, resumo):
    """
    Guarda o resumo de uma temporada (ou do trecho dela num clube) no histórico da carreira.

    Args:
        estado (dict): Estado da carreira.
        resumo (dict): Resumo montado por resumo_final.
    """
    estado.setdefault("carreira", []).append(
        {
            "temporada": resumo["temporada"],
            "clube": resumo["clube"],
            "divisao": resumo["divisao"],
            "posicao": resumo["posicao"],
            "desfecho": resumo["desfecho"],
            "pontuacao": resumo["pontuacao"],
        }
    )


def evolucao_da_idade(idade):
    """
    Sorteia quanto a qualidade de um jogador muda na virada da temporada, conforme a idade dele.

    Usa EVOLUCAO_POR_IDADE: até 21 anos sobe de 2 a 5, até 24 de 1 a 3, até 28 varia de -1 a 2, até 31 de -2
    a 1, até 33 de -3 a 0 e depois cai de 1 a 5.

    Args:
        idade (int): Idade do jogador no fim da temporada, já contando o aniversário dela.

    Returns:
        int: Variação da qualidade.
    """
    for limite, minimo, maximo in EVOLUCAO_POR_IDADE:
        if idade <= limite:
            return random.randint(minimo, maximo)
    return 0


def vai_se_aposentar(jogador):
    """
    Sorteia se um jogador encerra a carreira na virada da temporada.

    A partir de IDADE_APOSENTADORIA (35 anos) a chance é de 35%, mais 20 pontos por ano acima disso; com
    IDADE_LIMITE (38 anos) ele sempre para.

    Args:
        jogador (dict): Jogador avaliado, com a idade do fim da temporada.

    Returns:
        bool: True se o jogador se aposenta.
    """
    idade = jogador.get("idade", 26)
    if idade >= IDADE_LIMITE:
        return True
    if idade < IDADE_APOSENTADORIA:
        return False
    return random.random() < 0.35 + 0.2 * (idade - IDADE_APOSENTADORIA)


def virar_o_ano(jogador):
    """
    Aplica a evolução da idade a um jogador e zera os números da temporada.

    A idade não muda aqui: cada jogador fica mais velho no próprio aniversário, ao longo da temporada. A
    qualidade muda conforme evolucao_da_idade (entre 40 e 92) e cada atributo acompanha a mudança, com
    variação de -1 a 1 (entre 5 e 99). Gols, cartões, suspensões, lesões, grande fase, insatisfação e foco
    de treino são zerados, e a energia volta a 100.

    Args:
        jogador (dict): Jogador a atualizar.

    Returns:
        int: Variação da qualidade.
    """
    jogador.setdefault("idade", 26)
    antes = jogador["qualidade"]
    jogador["qualidade"] = limitar(antes + evolucao_da_idade(jogador["idade"]), 40, 92)
    variacao = jogador["qualidade"] - antes
    for atributo in ATRIBUTOS:
        jogador[atributo] = limitar(jogador[atributo] + variacao + random.randint(-1, 1), 5, 99)
    jogador.update({"gols": 0, "amarelos": 0, "suspenso": 0, "lesao": 0, "fase": 0, "energia": 100})
    jogador["desfalque"] = False
    jogador.pop("insatisfeito", None)
    jogador.pop("treino_foco", None)
    return variacao


def garoto_da_base(estado, clube, banco, posicao, joia=False):
    """
    Sobe um garoto das categorias de base para o elenco do clube.

    O garoto tem de 17 a 19 anos e qualidade sorteada em torno da força do clube menos 12 (desvio 4); a joia
    da base fica em torno da força menos 2 (desvio 3). A qualidade fica entre 40 e 92.

    Args:
        estado (dict): Estado da carreira.
        clube (dict): Clube que recebe o garoto.
        banco (dict): Banco de nomes.
        posicao (str): Posição do garoto.
        joia (bool): Se é uma joia da base. Padrão False.

    Returns:
        dict: Garoto criado, já no elenco do clube.
    """
    media, desvio = (clube["forca"] - 2, 3) if joia else (clube["forca"] - 12, 4)
    qualidade = limitar(round(random.gauss(media, desvio)), 40, 92)
    garoto = novo_garoto(estado, clube, banco, qualidade, posicao, random.randint(17, 19))
    clube["elenco"].append(garoto)
    return garoto


def renovar_elenco(estado, clube, banco):
    """
    Passa o elenco de um clube para a nova temporada.

    Cada jogador evolui conforme a idade (virar_o_ano) ou se aposenta (vai_se_aposentar). Depois a base
    completa as posições que ficaram abaixo de COMPOSICAO_ELENCO, sem passar de MAX_ELENCO, e com
    CHANCE_JOIA_DA_BASE (30%) sobe também uma joia da base, de linha.

    Args:
        estado (dict): Estado da carreira.
        clube (dict): Clube a renovar.
        banco (dict): Banco de nomes.

    Returns:
        dict: Jogadores aposentados, garotos que subiram e as variações de qualidade (jogador, variação).
    """
    aposentados = []
    variacoes = []
    for jogador in list(clube["elenco"]):
        jogador.setdefault("idade", 26)
        if vai_se_aposentar(jogador):
            clube["elenco"].remove(jogador)
            aposentados.append(jogador)
            continue
        variacoes.append((jogador, virar_o_ano(jogador)))
    clube["titulares"] = [clube_id for clube_id in clube["titulares"] if clube_id in {j["id"] for j in clube["elenco"]}]
    revelados = []
    for posicao, quantidade in COMPOSICAO_ELENCO.items():
        while quantos_na_posicao(clube["elenco"], posicao) < quantidade and len(clube["elenco"]) < MAX_ELENCO:
            revelados.append(garoto_da_base(estado, clube, banco, posicao))
    if random.random() < CHANCE_JOIA_DA_BASE and len(clube["elenco"]) < MAX_ELENCO:
        revelados.append(garoto_da_base(estado, clube, banco, random.choice(("DEF", "MEI", "ATA")), joia=True))
    return {"aposentados": aposentados, "revelados": revelados, "variacoes": variacoes}


def renovar_livres(estado, banco):
    """
    Passa os jogadores sem clube para a nova temporada e traz gente nova ao mercado.

    Os livres evoluem como os outros jogadores, e quem passa de 33 anos tem 40% de chance de parar (além da
    aposentadoria normal). Depois a lista é completada com novos jogadores até AGENTES_LIVRES (30).

    Args:
        estado (dict): Estado da carreira.
        banco (dict): Banco de nomes.

    Returns:
        int: Quantidade de jogadores novos no mercado.
    """
    livres = []
    for jogador in estado["livres"]:
        idade = jogador.get("idade", 26)
        if vai_se_aposentar(jogador) or (idade > 33 and random.random() < 0.4):
            continue
        virar_o_ano(jogador)
        livres.append(jogador)
    estado["livres"] = livres
    todos = [jogador for clube in estado["clubes"].values() for jogador in clube["elenco"]] + livres
    usados = {jogador["nome"] for jogador in todos}
    numeros = [int(jogador["id"][4:]) for jogador in todos if jogador["id"].startswith("liv-")]
    numero = max(numeros + [estado.get("ultimo_livre", 0)])
    novos = 0
    while len(estado["livres"]) < AGENTES_LIVRES:
        numero += 1
        estado["livres"].append(criar_agente_livre(f"liv-{numero:02d}", banco, usados))
        novos += 1
    estado["ultimo_livre"] = numero
    return novos


def recalcular_forca(clube):
    """
    Recalcula a força do clube a partir do elenco atual.

    A força é a qualidade média dos titulares que a escalação automática escolheria, menos FOLGA_DOS_TITULARES
    (2,5), que é a diferença média entre os titulares e a força no começo do jogo. Fica entre 40 e 92.

    Args:
        clube (dict): Clube avaliado.

    Returns:
        int: Nova força do clube.
    """
    ids = set(escalar_automatico(clube["elenco"], clube["plano"]["formacao"]))
    qualidades = [jogador["qualidade"] for jogador in clube["elenco"] if jogador["id"] in ids]
    if qualidades:
        clube["forca"] = limitar(round(sum(qualidades) / len(qualidades) - FOLGA_DOS_TITULARES), 40, 92)
    return clube["forca"]


def ordem_da_copa(estado):
    """
    Monta a ordem dos clubes de cada divisão para a copa da nova temporada.

    Na Série A vêm os que continuaram nela, na ordem da classificação final, e depois os que subiram. Na Série
    B vêm os que continuaram nela, na ordem final, e depois os que caíram.

    Args:
        estado (dict): Estado da carreira, já com as divisões trocadas por fechar_divisoes.

    Returns:
        dict: Para cada divisão, os identificadores do melhor para o pior.
    """
    final = estado.get("classificacao_final", {1: [], 2: []})
    divisao = {clube_id: clube.get("divisao", 1) for clube_id, clube in estado["clubes"].items()}
    serie_a = [c for c in final[1] if divisao[c] == 1] + [c for c in final[2] if divisao[c] == 1]
    serie_b = [c for c in final[2] if divisao[c] == 2] + [c for c in final[1] if divisao[c] == 2]
    return {1: serie_a, 2: serie_b}


def nova_temporada(estado, banco, confianca):
    """
    Começa a próxima temporada da carreira.

    Renova os elencos de todos os clubes (evolução pela idade, aposentadorias e garotos da base) e a lista de
    jogadores sem clube, recalcula a força de cada clube, refaz as escalações, gera o calendário das duas
    divisões e a copa pela classificação anterior, zera a tabela, o histórico, as súmulas, os desafios, os
    objetivos e o extrato, e define a confiança inicial da diretoria.

    Args:
        estado (dict): Estado da carreira, com as divisões já trocadas por fechar_divisoes.
        banco (dict): Banco de nomes.
        confianca (int): Confiança da diretoria no começo da temporada.

    Returns:
        dict: O que mudou no clube do técnico: aposentados, garotos da base, maiores evoluções e quedas,
            força antiga e nova, e quantos jogadores novos chegaram ao mercado.
    """
    estado["temporada"] = estado.get("temporada", 1) + 1
    meu = clube_do_jogador(estado)
    forca_antiga = meu["forca"]
    relatorio = {}
    for clube in estado["clubes"].values():
        mudancas = renovar_elenco(estado, clube, banco)
        recalcular_forca(clube)
        if clube["id"] == meu["id"]:
            relatorio = mudancas
            completar_titulares(clube)
        else:
            clube["titulares"] = escalar_automatico(clube["elenco"], clube["plano"]["formacao"])
    novos_no_mercado = renovar_livres(estado, banco)
    variacoes = sorted(relatorio["variacoes"], key=lambda par: par[1], reverse=True)
    estado.update(
        {
            "calendario": gerar_calendario_das_divisoes(estado["clubes"]),
            "copa": criar_copa(estado["clubes"], ordem_da_copa(estado)),
            "tabela": criar_tabela(list(estado["clubes"])),
            "historico": [],
            "sumulas": {},
            "etapa": 0,
            "rodada": 1,
            "encerrado": False,
            "demitido": False,
            "confianca": confianca,
            "ultimos": [],
            "objetivos": [],
            "desafios_cumpridos": 0,
            "financas": {},
        }
    )
    for chave in ("desafio", "treino_etapa", "torcida_extra", "promessa", "extrato_etapa", "classificacao_final"):
        estado.pop(chave, None)
    return {
        "aposentados": relatorio["aposentados"],
        "revelados": relatorio["revelados"],
        "evoluiram": [par for par in variacoes if par[1] > 0][:3],
        "cairam": [par for par in reversed(variacoes) if par[1] < 0][:3],
        "forca": (forca_antiga, meu["forca"]),
        "novos_no_mercado": novos_no_mercado,
    }


def propostas_da_janela(estado):
    """
    Monta as propostas da janela de transferências entre uma temporada e outra.

    Sorteia de 1 a 3 propostas (PROPOSTAS_NA_JANELA), cada uma por um jogador diferente.

    Args:
        estado (dict): Estado da carreira.

    Returns:
        list[dict]: Propostas no formato de evento, prontas para a tela de negociação.
    """
    propostas = []
    for _ in range(random.randint(*PROPOSTAS_NA_JANELA)):
        proposta = criar_proposta(estado)
        if proposta and proposta["jogador_id"] not in {p["jogador_id"] for p in propostas}:
            propostas.append(proposta)
    return propostas


def migrar_save(estado, clubes_base, banco, frases):
    """
    Atualiza um save da versão 2 (uma divisão só, uma temporada) para a versão atual.

    Os clubes do save ficam na Série A. Os clubes de times.json que faltam entram na Série B, com caixa,
    elenco e escalação novos; o turno deles entra no calendário, e as rodadas que já foram jogadas são
    simuladas para a tabela da Série B ficar em dia. A copa ganha a lista de participantes, a carreira começa
    na temporada 1, com a reputação do nível do clube, e uma temporada que já foi para o ranking não é gravada
    de novo.

    Args:
        estado (dict): Estado carregado do save antigo.
        clubes_base (list[dict]): Clubes lidos de times.json.
        banco (dict): Banco de nomes.
        frases (dict): Frases de narração, usadas na simulação das rodadas atrasadas.

    Returns:
        dict: O mesmo estado, já na versão atual.
    """
    if estado.get("versao") == VERSAO_SAVE:
        return estado
    for clube in estado["clubes"].values():
        clube.setdefault("divisao", 1)
    usados = nomes_em_uso(estado) | {jogador["nome"] for jogador in estado.get("livres", [])}
    novos = {}
    for base in clubes_base:
        if base["id"] in estado["clubes"]:
            continue
        clube = dict(base)
        clube["plano"] = dict(base["plano"])
        clube["divisao"] = base.get("divisao", 2)
        clube["caixa"] = NIVEIS[clube["nivel"]]["caixa"]
        clube["elenco"] = gerar_elenco(clube, banco, usados)
        clube["titulares"] = escalar_automatico(clube["elenco"], clube["plano"]["formacao"])
        estado["clubes"][clube["id"]] = clube
        novos[clube["id"]] = clube
    if novos:
        turno = gerar_calendario(list(novos))
        for numero, jogos in enumerate(turno):
            if numero < len(estado["calendario"]):
                estado["calendario"][numero] = list(estado["calendario"][numero]) + jogos
        estado["tabela"].update(criar_tabela(list(novos)))
        for numero, rodada in enumerate(estado["historico"]):
            for casa, fora in turno[numero] if numero < len(turno) else []:
                resultado = simular_partida(estado["clubes"][casa], estado["clubes"][fora], frases)
                registrar_resultado(estado["tabela"], resultado)
                rodada.append({chave: resultado[chave] for chave in ("mandante", "visitante", "gm", "gv")})
            for clube in novos.values():
                preparar_proxima_rodada(clube["elenco"])
    copa = estado["copa"]
    no_sorteio = [clube_id for jogos in copa["confrontos"].values() for jogo in jogos for clube_id in jogo]
    copa.setdefault("participantes", list(dict.fromkeys(copa["classificados"] + no_sorteio)))
    clube = clube_do_jogador(estado)
    if estado.pop("ranking_registrado", False):
        estado["registros"] = [f"1-{clube['id']}"]
    estado.setdefault("temporada", 1)
    estado.setdefault("carreira", [])
    estado.setdefault("reputacao", REPUTACAO_INICIAL[clube["nivel"]])
    estado["versao"] = VERSAO_SAVE
    return estado


def situacao_na_nova_copa(estado):
    """
    Descreve como o clube do técnico entra na copa da temporada.

    Args:
        estado (dict): Estado da carreira.

    Returns:
        str: "direto nas quartas de final", "na fase preliminar" ou "fora da copa".
    """
    copa = estado["copa"]
    if estado["clube_id"] in copa["classificados"]:
        return "direto nas quartas de final"
    if estado["clube_id"] in copa.get("participantes", []):
        return "na fase preliminar"
    return "fora da copa"
