import random

from config import AGENTES_LIVRES, COMPOSICAO_ELENCO, ELENCO_MINIMO, MAX_ELENCO, MAXIMO_LIVRES, MINIMO_POR_POSICAO
from elenco.escalacao import (
    completar_titulares,
    criar_jogador,
    escalar_automatico,
    limitar,
    rotulo,
    sortear_nome,
    valor_de_mercado,
)
from liga.financas import lancar

POSICOES_LIVRES = ("GOL", "DEF", "DEF", "MEI", "MEI", "ATA", "ATA")


def dinheiro(valor):
    """
    Formata um valor em milhões de reais para exibição.

    Args:
        valor (float): Valor em milhões de reais.

    Returns:
        str: Texto no formato "R$ 12,5 mi", com uma casa decimal e vírgula como separador.
    """
    return f"R$ {valor:.1f} mi".replace(".", ",")


def gerar_agentes_livres(banco, usados, quantidade=AGENTES_LIVRES):
    """
    Gera a lista de jogadores sem clube disponíveis no mercado.

    Cada agente livre é criado por criar_agente_livre, e os identificadores seguem o padrão "liv-01", "liv-02"
    e assim por diante.

    Args:
        banco (dict): Banco de nomes usado para sortear o nome dos jogadores.
        usados (set): Nomes já utilizados, atualizado a cada nome sorteado para evitar repetição.
        quantidade (int): Número de agentes livres a gerar. Padrão: AGENTES_LIVRES (30).

    Returns:
        list: Lista de dicionários com os jogadores gerados.
    """
    return [criar_agente_livre(f"liv-{numero:02d}", banco, usados) for numero in range(1, quantidade + 1)]


def criar_agente_livre(identificador, banco, usados):
    """
    Cria um jogador sem clube.

    Recebe uma posição sorteada em POSICOES_LIVRES, uma qualidade sorteada por distribuição normal (média 61,
    desvio 6) limitada entre 45 e 77, e uma idade jovem (18 a 22 anos) ou veterana (29 a 35 anos).

    Args:
        identificador (str): Identificador do jogador, no padrão "liv-NN".
        banco (dict): Banco de nomes usado para sortear o nome.
        usados (set): Nomes já utilizados, atualizado com o nome sorteado.

    Returns:
        dict: Jogador criado.
    """
    posicao = random.choice(POSICOES_LIVRES)
    qualidade = limitar(round(random.gauss(61, 6)), 45, 77)
    idade = random.choice((random.randint(18, 22), random.randint(29, 35)))
    return criar_jogador(identificador, sortear_nome(banco, usados), posicao, qualidade, idade)


def chegar_dispensados(estado, banco):
    """
    Traz ao mercado 1 ou 2 jogadores dispensados por clubes do exterior, enquanto houver vaga na lista de
    livres.

    Os nomes não repetem os de nenhum jogador da temporada, e os identificadores continuam a numeração "liv-"
    a partir do maior já usado. Cada chegada vira notícia.

    Args:
        estado (dict): Estado atual da temporada.
        banco (dict): Banco de nomes usado para sortear o nome.

    Returns:
        list[str]: Notícias das chegadas.
    """
    todos = [jogador for clube in estado["clubes"].values() for jogador in clube["elenco"]] + estado["livres"]
    usados = {jogador["nome"] for jogador in todos}
    numeros = [int(jogador["id"][4:]) for jogador in todos if jogador["id"].startswith("liv-")]
    numero = max(numeros + [estado.get("ultimo_livre", 0)])
    noticias = []
    for _ in range(random.randint(1, 2)):
        if len(estado["livres"]) >= MAXIMO_LIVRES:
            break
        numero += 1
        jogador = criar_agente_livre(f"liv-{numero:02d}", banco, usados)
        estado["livres"].append(jogador)
        texto = (
            f"{rotulo(jogador)}, qualidade {jogador['qualidade']} e {jogador['idade']} anos, foi dispensado por um "
            "clube do exterior e está sem clube."
        )
        noticias.append(noticia(estado, texto))
    estado["ultimo_livre"] = numero
    return noticias


def noticia(estado, texto):
    """
    Registra uma notícia do mercado no estado da temporada.

    Mantém apenas as 20 notícias mais recentes, descartando as mais antigas.

    Args:
        estado (dict): Estado atual da temporada.
        texto (str): Texto da notícia.

    Returns:
        str: O próprio texto da notícia registrada.
    """
    estado["noticias"] = (estado.get("noticias", []) + [texto])[-20:]
    return texto


def quantos_na_posicao(elenco, posicao):
    """
    Conta quantos jogadores do elenco atuam em uma posição.

    Args:
        elenco (list): Lista de jogadores do clube.
        posicao (str): Sigla da posição (GOL, DEF, MEI ou ATA).

    Returns:
        int: Quantidade de jogadores na posição.
    """
    return sum(1 for jogador in elenco if jogador["pos"] == posicao)


def pode_sair(clube, jogador):
    """
    Verifica se o clube pode liberar um jogador sem desfalcar o elenco.

    O jogador só pode sair se o elenco tiver mais de ELENCO_MINIMO (18) jogadores e se a posição dele
    continuar acima do mínimo definido em MINIMO_POR_POSICAO (2 goleiros, 5 defensores, 5 meias e 3
    atacantes).

    Args:
        clube (dict): Clube dono do jogador.
        jogador (dict): Jogador que se pretende negociar.

    Returns:
        bool: True se a saída é permitida, False caso contrário.
    """
    return (
        len(clube["elenco"]) > ELENCO_MINIMO
        and quantos_na_posicao(clube["elenco"], jogador["pos"]) > MINIMO_POR_POSICAO[jogador["pos"]]
    )


def preco_pedido(clube, jogador):
    """
    Calcula o preço que um clube pede para vender um jogador.

    Parte do valor de mercado do jogador, acrescenta 30% se ele for titular e mais 15% se o clube for de nível
    grande. O resultado é arredondado para uma casa decimal.

    Args:
        clube (dict): Clube vendedor.
        jogador (dict): Jogador à venda.

    Returns:
        float: Preço pedido, em milhões de reais.
    """
    preco = valor_de_mercado(jogador)
    if jogador["id"] in clube["titulares"]:
        preco *= 1.3
    if clube["nivel"] == "grande":
        preco *= 1.15
    return round(preco, 1)


def luvas(jogador):
    """
    Calcula o valor das luvas para contratar um jogador sem clube.

    As luvas correspondem a 15% do valor de mercado do jogador, com mínimo de 0,2 milhão, arredondadas para
    uma casa decimal.

    Args:
        jogador (dict): Jogador sem clube.

    Returns:
        float: Valor das luvas, em milhões de reais.
    """
    return round(max(0.2, valor_de_mercado(jogador) * 0.15), 1)


def jogadores_a_venda(estado, posicao=None):
    """
    Lista os jogadores dos outros clubes que podem receber proposta.

    Inclui todos os jogadores de todos os clubes, exceto o do técnico, opcionalmente filtrados por posição,
    ordenados da maior para a menor qualidade.

    Args:
        estado (dict): Estado atual da temporada.
        posicao (str | None): Sigla da posição para filtrar. Padrão: None, que lista todas as posições.

    Returns:
        list: Lista de tuplas (jogador, clube) ordenada por qualidade decrescente.
    """
    disponiveis = [
        (jogador, clube)
        for clube in estado["clubes"].values()
        if clube["id"] != estado["clube_id"]
        for jogador in clube["elenco"]
        if posicao is None or jogador["pos"] == posicao
    ]
    return sorted(disponiveis, key=lambda par: par[0]["qualidade"], reverse=True)


def reorganizar(estado, clube):
    """
    Ajusta a escalação de um clube depois de uma mudança no elenco.

    No clube do técnico, apenas completa os titulares que faltam, preservando as escolhas do jogador. Nos
    clubes controlados pela IA, refaz a escalação inteira de forma automática conforme a formação do plano
    tático.

    Args:
        estado (dict): Estado atual da temporada.
        clube (dict): Clube cujo elenco foi alterado.
    """
    if clube["id"] == estado["clube_id"]:
        completar_titulares(clube)
    else:
        clube["titulares"] = escalar_automatico(clube["elenco"], clube["plano"]["formacao"])


def transferir(estado, jogador, vendedor, comprador, valor):
    """
    Efetiva a transferência de um jogador entre dois clubes.

    Remove o jogador do elenco e dos titulares do vendedor, inclui no elenco do comprador, credita o valor no
    caixa do vendedor e debita do comprador. Em seguida reorganiza a escalação do vendedor e, se o comprador
    não for o clube do técnico, também a dele. Por fim registra a notícia da negociação.

    Args:
        estado (dict): Estado atual da temporada.
        jogador (dict): Jogador transferido.
        vendedor (dict): Clube que vende o jogador.
        comprador (dict): Clube que compra o jogador.
        valor (float): Valor da transferência, em milhões de reais.

    Returns:
        str: Texto da notícia da transferência.
    """
    vendedor["elenco"].remove(jogador)
    if jogador["id"] in vendedor["titulares"]:
        vendedor["titulares"].remove(jogador["id"])
    comprador["elenco"].append(jogador)
    lancar(estado, vendedor["id"], "Vendas de jogadores", valor)
    lancar(estado, comprador["id"], "Compras de jogadores", -valor)
    reorganizar(estado, vendedor)
    if comprador["id"] != estado["clube_id"]:
        reorganizar(estado, comprador)
    return noticia(
        estado, f"{comprador['nome']} contrata {rotulo(jogador)} do {vendedor['nome']} por {dinheiro(valor)}."
    )


def tentar_comprar(estado, jogador, vendedor, oferta):
    """
    Tenta comprar um jogador de outro clube com a oferta do técnico.

    A proposta é recusada de imediato se o elenco do técnico já tiver MAX_ELENCO (28) jogadores, se a oferta
    for maior que o caixa ou se o vendedor não puder liberar o jogador. Caso contrário, a chance de aceitar
    cresce de forma linear com a razão entre oferta e preço pedido: é nula com 80% do pedido ou menos e chega
    perto de dois terços logo abaixo do pedido. Oferecer o preço pedido ou mais sempre fecha o negócio.

    Args:
        estado (dict): Estado atual da temporada.
        jogador (dict): Jogador desejado.
        vendedor (dict): Clube dono do jogador.
        oferta (float): Valor oferecido, em milhões de reais.

    Returns:
        tuple: Par (bool, str) indicando se a compra foi concluída e a mensagem para o técnico.
    """
    comprador = estado["clubes"][estado["clube_id"]]
    if len(comprador["elenco"]) >= MAX_ELENCO:
        return False, f"Seu elenco está cheio (máximo de {MAX_ELENCO} jogadores)."
    if oferta > comprador.get("caixa", 0):
        return False, f"Dinheiro insuficiente. Você tem {dinheiro(comprador.get('caixa', 0))}."
    if not pode_sair(vendedor, jogador):
        return False, f"O {vendedor['nome']} não vende: ficaria sem reposição para a posição."
    pedido = preco_pedido(vendedor, jogador)
    chance = 1 if oferta >= pedido else limitar((oferta / pedido - 0.8) / 0.3, 0, 1)
    if random.random() >= chance:
        return False, f"Proposta recusada. O {vendedor['nome']} quer {dinheiro(pedido)} por {rotulo(jogador)}."
    transferir(estado, jogador, vendedor, comprador, oferta)
    return True, f"{rotulo(jogador)} é o novo reforço do {comprador['nome']} por {dinheiro(oferta)}!"


def contratar_livre(estado, jogador):
    """
    Contrata um jogador sem clube para o time do técnico.

    A contratação é negada se o elenco já tiver MAX_ELENCO (28) jogadores ou se o caixa não cobrir as luvas.
    Quando aprovada, o jogador sai da lista de agentes livres, entra no elenco, as luvas são debitadas do
    caixa e a notícia é registrada.

    Args:
        estado (dict): Estado atual da temporada.
        jogador (dict): Agente livre a contratar.

    Returns:
        tuple: Par (bool, str) indicando se a contratação foi concluída e a mensagem para o técnico.
    """
    clube = estado["clubes"][estado["clube_id"]]
    custo = luvas(jogador)
    if len(clube["elenco"]) >= MAX_ELENCO:
        return False, f"Seu elenco está cheio (máximo de {MAX_ELENCO} jogadores)."
    if custo > clube.get("caixa", 0):
        return False, f"Dinheiro insuficiente para as luvas de {dinheiro(custo)}."
    estado["livres"].remove(jogador)
    clube["elenco"].append(jogador)
    lancar(estado, clube["id"], "Luvas de contratação", -custo)
    noticia(estado, f"{clube['nome']} contrata {rotulo(jogador)}, que estava sem clube.")
    return True, f"{rotulo(jogador)} assinou com o {clube['nome']} por {dinheiro(custo)} de luvas."


def ofertas_por(estado, jogador):
    """
    Gera as propostas de outros clubes por um jogador do técnico.

    São interessados os clubes da IA com vaga no elenco e caixa de pelo menos 70% do valor de mercado do
    jogador. Até três deles, sorteados, fazem uma oferta entre 75% e 120% do valor de mercado, limitada ao
    caixa de cada clube.

    Args:
        estado (dict): Estado atual da temporada.
        jogador (dict): Jogador colocado à venda.

    Returns:
        list: Lista de tuplas (clube, oferta) ordenada da maior para a menor oferta.
    """
    valor = valor_de_mercado(jogador)
    interessados = [
        clube
        for clube in estado["clubes"].values()
        if clube["id"] != estado["clube_id"]
        and len(clube["elenco"]) < MAX_ELENCO
        and clube.get("caixa", 0) >= valor * 0.7
    ]
    random.shuffle(interessados)
    ofertas = []
    for clube in interessados[:3]:
        oferta = round(min(clube["caixa"], valor * random.uniform(0.75, 1.2)), 1)
        ofertas.append((clube, oferta))
    return sorted(ofertas, key=lambda par: par[1], reverse=True)


def vender(estado, jogador, comprador, valor):
    """
    Vende um jogador do técnico para outro clube.

    Args:
        estado (dict): Estado atual da temporada.
        jogador (dict): Jogador vendido.
        comprador (dict): Clube que compra o jogador.
        valor (float): Valor da venda, em milhões de reais.

    Returns:
        str: Mensagem confirmando a venda.
    """
    vendedor = estado["clubes"][estado["clube_id"]]
    transferir(estado, jogador, vendedor, comprador, valor)
    return f"{rotulo(jogador)} vendido ao {comprador['nome']} por {dinheiro(valor)}."


def pior_da_posicao(clube, posicao):
    """
    Encontra o jogador de menor qualidade do clube em uma posição.

    Args:
        clube (dict): Clube analisado.
        posicao (str): Sigla da posição (GOL, DEF, MEI ou ATA).

    Returns:
        dict | None: Jogador de menor qualidade na posição ou None se não houver ninguém nela.
    """
    da_posicao = [jogador for jogador in clube["elenco"] if jogador["pos"] == posicao]
    return min(da_posicao, key=lambda jogador: jogador["qualidade"]) if da_posicao else None


def contratacao_de_livre_ia(estado):
    """
    Faz um clube da IA contratar um jogador sem clube, se valer a pena.

    Sorteia um clube da IA com vaga no elenco e percorre os agentes livres do melhor para o pior. Contrata o
    primeiro que supere em mais de 2 pontos de qualidade o pior jogador do clube na mesma posição e cujas
    luvas caibam no caixa, reorganizando a escalação em seguida.

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        str | None: Texto da notícia da contratação ou None se nenhuma ocorreu.
    """
    clubes = [c for c in estado["clubes"].values() if c["id"] != estado["clube_id"] and len(c["elenco"]) < MAX_ELENCO]
    if not clubes or not estado["livres"]:
        return None
    clube = random.choice(clubes)
    for livre in sorted(estado["livres"], key=lambda jogador: jogador["qualidade"], reverse=True):
        pior = pior_da_posicao(clube, livre["pos"])
        custo = luvas(livre)
        if pior and livre["qualidade"] > pior["qualidade"] + 2 and clube.get("caixa", 0) >= custo:
            estado["livres"].remove(livre)
            clube["elenco"].append(livre)
            lancar(estado, clube["id"], "Luvas de contratação", -custo)
            reorganizar(estado, clube)
            return noticia(estado, f"{clube['nome']} contrata {rotulo(livre)}, que estava sem clube.")
    return None


def negociacao_entre_ia(estado):
    """
    Simula uma transferência entre dois clubes controlados pela IA.

    Sorteia um comprador com vaga no elenco e um vendedor diferente. São candidatos os jogadores que o
    vendedor pode liberar, cujo preço pedido cabe no caixa do comprador e que superam em mais de 3 pontos de
    qualidade o pior jogador do comprador na mesma posição. Um candidato é sorteado e transferido pelo preço
    pedido.

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        str | None: Texto da notícia da transferência ou None se não houve negócio.
    """
    clubes = [c for c in estado["clubes"].values() if c["id"] != estado["clube_id"]]
    comprador = random.choice(clubes)
    if len(comprador["elenco"]) >= MAX_ELENCO:
        return None
    vendedores = [c for c in clubes if c is not comprador]
    vendedor = random.choice(vendedores)
    candidatos = [
        jogador
        for jogador in vendedor["elenco"]
        if pode_sair(vendedor, jogador)
        and preco_pedido(vendedor, jogador) <= comprador.get("caixa", 0)
        and pior_da_posicao(comprador, jogador["pos"])
        and jogador["qualidade"] > pior_da_posicao(comprador, jogador["pos"])["qualidade"] + 3
    ]
    if not candidatos:
        return None
    jogador = random.choice(candidatos)
    return transferir(estado, jogador, vendedor, comprador, preco_pedido(vendedor, jogador))


def movimentar_mercado(estado, banco=None):
    """
    Movimenta o mercado entre os clubes da IA.

    Há 45% de chance de tentar uma contratação de agente livre e 30% de chance de tentar uma negociação entre
    clubes da IA, de forma independente. Com o banco de nomes, também chegam jogadores dispensados do exterior
    à lista de livres.

    Args:
        estado (dict): Estado atual da temporada.
        banco (dict | None): Banco de nomes para os dispensados; sem ele, ninguém chega. Padrão None.

    Returns:
        list: Textos das notícias geradas, sem as tentativas que não resultaram em negócio.
    """
    noticias = []
    if random.random() < 0.45:
        noticias.append(contratacao_de_livre_ia(estado))
    if random.random() < 0.3:
        noticias.append(negociacao_entre_ia(estado))
    if banco:
        noticias.extend(chegar_dispensados(estado, banco))
    return [texto for texto in noticias if texto]


def motivo_da_contratacao(jogador, titulares_da_posicao, reservas_da_posicao, quantidade_na_posicao, forca):
    """
    Avalia um jogador para o elenco do técnico e explica por que valeria contratá-lo.

    Soma o ganho de qualidade sobre o titular mais fraco da posição (quando o jogador seria titular), 4 pontos
    se a posição tem menos jogadores que a composição padrão do elenco (COMPOSICAO_ELENCO) e o jogador não é
    muito mais fraco que o time, 2 pontos para jovens de até 21 anos com qualidade perto da força do clube e
    1,5 ponto quando o jogador é pelo menos 6 pontos melhor que o reserva mais fraco da posição, reforçando o
    banco. O motivo mostrado é o mais forte desses.

    Args:
        jogador (dict): Jogador avaliado.
        titulares_da_posicao (list[dict]): Titulares do técnico na mesma posição.
        reservas_da_posicao (list[dict]): Reservas do técnico na mesma posição.
        quantidade_na_posicao (int): Quantos jogadores o técnico tem nessa posição.
        forca (int): Força do clube do técnico.

    Returns:
        tuple: (pontuação, motivo), com motivo None quando o jogador não acrescenta nada.
    """
    pontos = 0.0
    motivos = []
    pior = min(titulares_da_posicao, key=lambda j: j["qualidade"], default=None)
    if pior and jogador["qualidade"] >= pior["qualidade"] + 3:
        ganho = jogador["qualidade"] - pior["qualidade"]
        pontos += ganho
        motivos.append(f"vira titular no lugar de {rotulo(pior)}, com +{ganho} de qualidade")
    if quantidade_na_posicao < COMPOSICAO_ELENCO[jogador["pos"]] and jogador["qualidade"] >= forca - 8:
        pontos += 4
        motivos.append(f"a posição só tem {quantidade_na_posicao} jogadores")
    if jogador.get("idade", 30) <= 21 and jogador["qualidade"] >= forca - 6:
        pontos += 2
        motivos.append(f"jovem promissor ({jogador['idade']} anos), vai valorizar")
    reserva = min(reservas_da_posicao, key=lambda j: j["qualidade"], default=None)
    if reserva and jogador["qualidade"] >= reserva["qualidade"] + 6 and jogador["qualidade"] >= forca - 6:
        pontos += 1.5
        motivos.append(f"reforça o banco: bem melhor que {rotulo(reserva)}, que tem {reserva['qualidade']}")
    return pontos, (motivos[0] if motivos else None)


def sugerir_contratacoes(estado, maximo=6):
    """
    Monta as sugestões do olheiro para reforçar o elenco do técnico.

    Considera os jogadores de outros clubes que podem ser liberados (pelo preço pedido) e os jogadores sem
    clube (pelas luvas), desde que caibam no caixa. Cada um é avaliado por motivo_da_contratacao; jogadores
    sem clube ganham 1,5 ponto por custarem só as luvas, e o custo tira pontos em proporção ao caixa (gastar o
    caixa inteiro tira 4 pontos). Entram só os
    que têm motivo e pontuação positiva, no máximo dois por posição, e nenhum se o elenco já estiver cheio.

    Args:
        estado (dict): Estado atual da temporada.
        maximo (int): Quantidade máxima de sugestões. Padrão 6.

    Returns:
        list[dict]: Sugestões com o jogador, o clube vendedor (None se estiver sem clube), o custo e o motivo,
            da melhor para a pior.
    """
    clube = estado["clubes"][estado["clube_id"]]
    if len(clube["elenco"]) >= MAX_ELENCO:
        return []
    caixa = clube.get("caixa", 0)
    por_id = {jogador["id"]: jogador for jogador in clube["elenco"]}
    titulares = [por_id[i] for i in clube["titulares"] if i in por_id]
    reservas = [jogador for jogador in clube["elenco"] if jogador["id"] not in clube["titulares"]]
    candidatos = [
        (jogador, vendedor, preco_pedido(vendedor, jogador))
        for jogador, vendedor in jogadores_a_venda(estado)
        if pode_sair(vendedor, jogador)
    ]
    candidatos += [(jogador, None, luvas(jogador)) for jogador in estado["livres"]]
    avaliados = []
    for jogador, vendedor, custo in candidatos:
        if custo > caixa:
            continue
        mesma_posicao = [titular for titular in titulares if titular["pos"] == jogador["pos"]]
        banco = [reserva for reserva in reservas if reserva["pos"] == jogador["pos"]]
        pontos, motivo = motivo_da_contratacao(
            jogador, mesma_posicao, banco, quantos_na_posicao(clube["elenco"], jogador["pos"]), clube["forca"]
        )
        if not motivo:
            continue
        pontos += (1.5 if vendedor is None else 0) - custo / max(caixa, 1) * 4
        if pontos <= 0:
            continue
        avaliados.append({"jogador": jogador, "vendedor": vendedor, "custo": custo, "motivo": motivo, "pontos": pontos})
    sugestoes = []
    por_posicao = {}
    for item in sorted(avaliados, key=lambda item: item["pontos"], reverse=True):
        posicao = item["jogador"]["pos"]
        if por_posicao.get(posicao, 0) >= 2:
            continue
        por_posicao[posicao] = por_posicao.get(posicao, 0) + 1
        sugestoes.append(item)
        if len(sugestoes) == maximo:
            break
    return sugestoes
