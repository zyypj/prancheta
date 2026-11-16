import random

from config import BONUS_GRANDE_FASE, COMPOSICAO_ELENCO, ENERGIA_SEM_PERDA, FORMACOES

ATRIBUTOS = ("fin", "pas", "des", "fis", "ref")
AJUSTES = {
    "GOL": {"fin": -40, "pas": -15, "des": -25, "fis": -5, "ref": 0},
    "DEF": {"fin": -18, "pas": -6, "des": 4, "fis": 2, "ref": -60},
    "MEI": {"fin": -6, "pas": 4, "des": -6, "fis": 0, "ref": -60},
    "ATA": {"fin": 4, "pas": -6, "des": -24, "fis": 0, "ref": -60},
}
TITULARES_POR_POSICAO = {"GOL": 1, "DEF": 4, "MEI": 4, "ATA": 2}


def limitar(valor, minimo, maximo):
    """
    Restringe um valor a um intervalo.

    Args:
        valor (int | float): Valor a ser limitado.
        minimo (int | float): Menor valor aceito.
        maximo (int | float): Maior valor aceito.

    Returns:
        int | float: O próprio valor, ou o limite mais próximo se ele estiver fora do intervalo.
    """
    return max(minimo, min(maximo, valor))


def ler_banco_de_nomes(linhas):
    """
    Organiza as linhas do arquivo de nomes por tipo.

    Cada linha deve seguir o formato "tipo:texto", em que o tipo é N (prenome), S (sobrenome) ou A (apelido),
    sem diferenciar maiúsculas de minúsculas. Linhas sem o separador ":", com tipo desconhecido ou com texto
    vazio são ignoradas.

    Args:
        linhas (list[str]): Linhas lidas do arquivo de nomes.

    Returns:
        dict: Dicionário com as chaves "N", "S" e "A", cada uma com a lista de textos daquele tipo.
    """
    banco = {"N": [], "S": [], "A": []}
    for linha in linhas:
        tipo, separador, texto = linha.partition(":")
        tipo = tipo.strip().upper()
        if separador and tipo in banco and texto.strip():
            banco[tipo].append(texto.strip())
    return banco


def sortear_nome(banco, usados):
    """
    Sorteia um nome de jogador que ainda não foi usado.

    Faz até 80 tentativas. Em cada uma, há 25% de chance de usar um apelido (quando existe algum) e, no
    restante, combina um prenome com um sobrenome. Se todas as tentativas repetirem nomes, usa um prenome
    seguido de um número. O nome escolhido é adicionado ao conjunto de usados.

    Args:
        banco (dict): Banco de nomes com as listas "N", "S" e "A".
        usados (set): Nomes já atribuídos a outros jogadores.

    Returns:
        str: Nome sorteado.
    """
    for _ in range(80):
        if banco["A"] and random.random() < 0.25:
            nome = random.choice(banco["A"])
        else:
            nome = f"{random.choice(banco['N'])} {random.choice(banco['S'])}"
        if nome not in usados:
            usados.add(nome)
            return nome
    nome = f"{random.choice(banco['N'])} {len(usados) + 1}"
    usados.add(nome)
    return nome


def rotulo(jogador):
    """
    Monta o texto de identificação do jogador com posição e nome.

    Args:
        jogador (dict): Jogador a ser identificado.

    Returns:
        str: Texto no formato "POS Nome", por exemplo "ATA Fulano".
    """
    return f"{jogador['pos']} {jogador['nome']}"


def valor_de_mercado(jogador):
    """
    Calcula o valor de mercado do jogador, em milhões de reais.

    O valor cresce com o cubo da qualidade acima de 40: (qualidade - 40) / 10, elevado ao cubo e multiplicado
    por 0,5. Jogadores com 23 anos ou menos valem 30% a mais, e os com 31 anos ou mais valem 40% a menos; sem
    idade registrada, considera 26 anos. O resultado tem no mínimo 0,1 e é arredondado em uma casa decimal.

    Args:
        jogador (dict): Jogador avaliado.

    Returns:
        float: Valor de mercado em milhões.
    """
    base = (max(jogador["qualidade"], 41) - 40) / 10
    valor = base**3 * 0.5
    idade = jogador.get("idade", 26)
    if idade <= 23:
        valor *= 1.3
    elif idade >= 31:
        valor *= 0.6
    return round(max(valor, 0.1), 1)


def sortear_idade():
    """
    Sorteia a idade de um jogador.

    Returns:
        int: Idade entre 18 e 34 anos, inclusive.
    """
    return random.randint(18, 34)


def criar_jogador(identificador, nome, posicao, qualidade, idade=None):
    """
    Cria um jogador novo com energia cheia e sem cartões, lesões ou gols.

    Os atributos de finalização, passe, desarme, físico e reflexo partem da qualidade, recebem o ajuste típico
    da posição e uma variação aleatória de -5 a 5, e ficam entre 5 e 99. Sem idade informada, a idade é
    sorteada.

    Args:
        identificador (str): Identificador único do jogador.
        nome (str): Nome do jogador.
        posicao (str): Posição ("GOL", "DEF", "MEI" ou "ATA").
        qualidade (int): Qualidade geral do jogador.
        idade (int | None): Idade do jogador. Padrão None.

    Returns:
        dict: Jogador criado.
    """
    jogador = {
        "id": identificador,
        "nome": nome,
        "pos": posicao,
        "qualidade": qualidade,
        "idade": idade or sortear_idade(),
        "energia": 100,
        "amarelos": 0,
        "suspenso": 0,
        "lesao": 0,
        "fase": 0,
        "gols": 0,
        "desfalque": False,
    }
    for atributo in ATRIBUTOS:
        jogador[atributo] = limitar(qualidade + AJUSTES[posicao][atributo] + random.randint(-5, 5), 5, 99)
    return jogador


def sortear_qualidade(forca, titular):
    """
    Sorteia a qualidade de um jogador a partir da força do clube.

    Usa uma distribuição normal com desvio padrão 4, centrada em força + 2 para titulares e em força - 6 para
    reservas. O resultado é arredondado e fica entre 40 e 92.

    Args:
        forca (int): Força do clube.
        titular (bool): Se o jogador é titular.

    Returns:
        int: Qualidade sorteada.
    """
    media = forca + 2 if titular else forca - 6
    return limitar(round(random.gauss(media, 4)), 40, 92)


def gerar_elenco(clube, banco, usados):
    """
    Gera o elenco completo de um clube.

    Cria a quantidade de jogadores definida para cada posição, numerando os identificadores a partir do id do
    clube. Os primeiros de cada posição, até o número de titulares dela, recebem qualidade de titular e os
    demais, de reserva. Um jogador de linha é sorteado como craque e ganha 7 pontos de qualidade e de
    finalização, passe, desarme e físico.

    Args:
        clube (dict): Clube dono do elenco.
        banco (dict): Banco de nomes usado no sorteio.
        usados (set): Nomes já atribuídos, atualizado a cada jogador criado.

    Returns:
        list[dict]: Jogadores do elenco.
    """
    elenco = []
    numero = 1
    for posicao, quantidade in COMPOSICAO_ELENCO.items():
        for indice in range(quantidade):
            titular = indice < TITULARES_POR_POSICAO[posicao]
            qualidade = sortear_qualidade(clube["forca"], titular)
            elenco.append(criar_jogador(f"{clube['id']}-{numero:02d}", sortear_nome(banco, usados), posicao, qualidade))
            numero += 1
    craque = random.choice([jogador for jogador in elenco if jogador["pos"] != "GOL"])
    craque["qualidade"] = limitar(craque["qualidade"] + 7, 40, 92)
    for atributo in ("fin", "pas", "des", "fis"):
        craque[atributo] = limitar(craque[atributo] + 7, 5, 99)
    return elenco


def disponivel(jogador):
    """
    Verifica se o jogador pode ser escalado.

    Args:
        jogador (dict): Jogador avaliado.

    Returns:
        bool: True se o jogador não está lesionado nem suspenso.
    """
    return jogador["lesao"] == 0 and jogador["suspenso"] == 0


def fator_energia(energia):
    """
    Calcula quanto o cansaço reduz o rendimento do jogador.

    A partir do nível de energia sem perda o rendimento é integral. Abaixo dele, o fator cai de forma linear
    até 0,7 com energia zero.

    Args:
        energia (float): Energia atual do jogador, de 0 a 100.

    Returns:
        float: Fator multiplicador entre 0,7 e 1,0.
    """
    if energia >= ENERGIA_SEM_PERDA:
        return 1.0
    return 0.7 + 0.3 * energia / ENERGIA_SEM_PERDA


def atributo_efetivo(jogador, atributo):
    """
    Calcula o valor de um atributo considerando grande fase e cansaço.

    Args:
        jogador (dict): Jogador avaliado.
        atributo (str): Atributo desejado ("fin", "pas", "des", "fis" ou "ref").

    Returns:
        float: Atributo somado ao bônus de grande fase, quando houver, e multiplicado pelo fator de energia.
    """
    bonus = BONUS_GRANDE_FASE if jogador["fase"] > 0 else 0
    return (jogador[atributo] + bonus) * fator_energia(jogador["energia"])


def valor_para_escalar(jogador):
    """
    Calcula a nota usada para comparar jogadores na hora de escalar.

    Args:
        jogador (dict): Jogador avaliado.

    Returns:
        float: Qualidade somada ao bônus de grande fase, quando houver, e multiplicada pelo fator de energia.
    """
    bonus = BONUS_GRANDE_FASE if jogador["fase"] > 0 else 0
    return (jogador["qualidade"] + bonus) * fator_energia(jogador["energia"])


def escalar_automatico(elenco, formacao):
    """
    Monta automaticamente os 11 titulares para uma formação.

    Considera só os jogadores disponíveis, ordenados pelo valor para escalar. Preenche primeiro um goleiro e
    as vagas de defensores, meias e atacantes da formação com os melhores de cada posição. Se ainda faltarem
    jogadores, completa com os melhores de linha restantes, de qualquer posição.

    Args:
        elenco (list[dict]): Jogadores do clube.
        formacao (str): Formação tática, por exemplo "4-4-2".

    Returns:
        list[str]: Identificadores dos jogadores escolhidos, podendo ter menos de 11 se faltarem disponíveis.
    """
    defensores, meias, atacantes = FORMACOES[formacao]
    vagas = {"GOL": 1, "DEF": defensores, "MEI": meias, "ATA": atacantes}
    livres = sorted([jogador for jogador in elenco if disponivel(jogador)], key=valor_para_escalar, reverse=True)
    escolhidos = []
    for posicao, quantidade in vagas.items():
        da_posicao = [jogador for jogador in livres if jogador["pos"] == posicao and jogador not in escolhidos]
        escolhidos.extend(da_posicao[:quantidade])
    restantes = [jogador for jogador in livres if jogador not in escolhidos and jogador["pos"] != "GOL"]
    while len(escolhidos) < 11 and restantes:
        escolhidos.append(restantes.pop(0))
    return [jogador["id"] for jogador in escolhidos]


def completar_titulares(clube):
    """
    Garante que o clube tenha 11 titulares disponíveis.

    Mantém os titulares atuais que ainda estão no elenco e disponíveis. Se sobrarem 11, nada mais muda. Caso
    contrário, completa as vagas com os jogadores da escalação automática para a formação do clube, na ordem
    sugerida, e atualiza a lista de titulares.

    Args:
        clube (dict): Clube cujos titulares serão conferidos.

    Returns:
        list[str]: Rótulos dos titulares que saíram por estarem indisponíveis, ou lista vazia se não houve
            troca.
    """
    por_id = {jogador["id"]: jogador for jogador in clube["elenco"]}
    validos = [
        identificador
        for identificador in clube["titulares"]
        if identificador in por_id and disponivel(por_id[identificador])
    ]
    if len(validos) == 11:
        clube["titulares"] = validos
        return []
    sugestao = escalar_automatico(clube["elenco"], clube["plano"]["formacao"])
    trocados = [
        rotulo(por_id[identificador])
        for identificador in clube["titulares"]
        if identificador not in validos and identificador in por_id
    ]
    for identificador in sugestao:
        if len(validos) >= 11:
            break
        if identificador not in validos:
            validos.append(identificador)
    clube["titulares"] = validos
    return trocados


def contar_posicoes(jogadores):
    """
    Conta quantos jogadores há em cada posição.

    Args:
        jogadores (list[dict]): Jogadores a serem contados.

    Returns:
        dict: Quantidade por posição, com as chaves "GOL", "DEF", "MEI" e "ATA".
    """
    contagem = {posicao: 0 for posicao in ("GOL", "DEF", "MEI", "ATA")}
    for jogador in jogadores:
        contagem[jogador["pos"]] += 1
    return contagem


def media(valores, padrao):
    """
    Calcula a média aritmética de uma lista de valores.

    Args:
        valores (list[float]): Valores a serem considerados.
        padrao (float): Valor devolvido quando a lista está vazia.

    Returns:
        float: Média dos valores, ou o valor padrão se a lista estiver vazia.
    """
    return sum(valores) / len(valores) if valores else padrao


def forca_setores(em_campo):
    """
    Calcula a força de defesa, meio, ataque e goleiro dos jogadores em campo.

    Cada setor é a média de uma combinação ponderada dos atributos efetivos dos jogadores da posição: defesa
    usa desarme (80%) e físico (20%); meio usa passe (60%), desarme (20%) e físico (20%); ataque usa
    finalização (70%) e físico (30%) e depois recebe 25% de peso do passe dos meias. Setor sem jogadores vale
    35, e o goleiro vale o maior reflexo entre os goleiros, ou 30 se não houver goleiro. Cada defensor ou meia
    acima de 4 soma 2,5 ao respectivo setor e cada atacante acima de 2 soma 3 ao ataque; abaixo dessas
    quantidades, os mesmos valores são subtraídos. Para cada jogador a menos que 11, defesa e meio perdem 3 e
    ataque perde 2.

    Args:
        em_campo (list[dict]): Jogadores atualmente em campo.

    Returns:
        dict: Força de cada setor, com as chaves "defesa", "meio", "ataque" e "goleiro".
    """
    por_posicao = {
        posicao: [jogador for jogador in em_campo if jogador["pos"] == posicao]
        for posicao in ("GOL", "DEF", "MEI", "ATA")
    }
    contagem = contar_posicoes(em_campo)
    defesa = media(
        [atributo_efetivo(j, "des") * 0.8 + atributo_efetivo(j, "fis") * 0.2 for j in por_posicao["DEF"]], 35
    )
    meio = media(
        [
            atributo_efetivo(j, "pas") * 0.6 + atributo_efetivo(j, "des") * 0.2 + atributo_efetivo(j, "fis") * 0.2
            for j in por_posicao["MEI"]
        ],
        35,
    )
    ataque = media(
        [atributo_efetivo(j, "fin") * 0.7 + atributo_efetivo(j, "fis") * 0.3 for j in por_posicao["ATA"]], 35
    )
    ataque = ataque * 0.75 + media([atributo_efetivo(j, "pas") for j in por_posicao["MEI"]], 35) * 0.25
    goleiro = max([atributo_efetivo(j, "ref") for j in por_posicao["GOL"]], default=30)
    defesa += (contagem["DEF"] - 4) * 2.5
    meio += (contagem["MEI"] - 4) * 2.5
    ataque += (contagem["ATA"] - 2) * 3
    falta = 11 - len(em_campo)
    return {
        "defesa": defesa - falta * 3,
        "meio": meio - falta * 3,
        "ataque": ataque - falta * 2,
        "goleiro": goleiro,
    }
