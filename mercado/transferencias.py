import random

from config import AGENTES_LIVRES, MAX_ELENCO, MINIMO_POR_POSICAO
from elenco.escalacao import (
    completar_titulares,
    criar_jogador,
    escalar_automatico,
    limitar,
    rotulo,
    sortear_nome,
    valor_de_mercado,
)

POSICOES_LIVRES = ("GOL", "DEF", "DEF", "MEI", "MEI", "ATA", "ATA")
ELENCO_MINIMO = 16


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

    Cada agente livre recebe uma posição sorteada em POSICOES_LIVRES, uma qualidade sorteada por distribuição
    normal (média 64, desvio 7) limitada entre 45 e 82, e uma idade jovem (18 a 22 anos) ou veterana (29 a 35
    anos). Os identificadores seguem o padrão "liv-01", "liv-02" e assim por diante.

    Args:
        banco (dict): Banco de nomes usado para sortear o nome dos jogadores.
        usados (set): Nomes já utilizados, atualizado a cada nome sorteado para evitar repetição.
        quantidade (int): Número de agentes livres a gerar. Padrão: AGENTES_LIVRES (14).

    Returns:
        list: Lista de dicionários com os jogadores gerados.
    """
    livres = []
    for numero in range(1, quantidade + 1):
        posicao = random.choice(POSICOES_LIVRES)
        qualidade = limitar(round(random.gauss(64, 7)), 45, 82)
        idade = random.choice((random.randint(18, 22), random.randint(29, 35)))
        livres.append(criar_jogador(f"liv-{numero:02d}", sortear_nome(banco, usados), posicao, qualidade, idade))
    return livres


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

    O jogador só pode sair se o elenco tiver mais de ELENCO_MINIMO (16) jogadores e se a posição dele
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
    vendedor["caixa"] = round(vendedor.get("caixa", 0) + valor, 1)
    comprador["caixa"] = round(comprador.get("caixa", 0) - valor, 1)
    reorganizar(estado, vendedor)
    if comprador["id"] != estado["clube_id"]:
        reorganizar(estado, comprador)
    return noticia(
        estado, f"{comprador['nome']} contrata {rotulo(jogador)} do {vendedor['nome']} por {dinheiro(valor)}."
    )


def tentar_comprar(estado, jogador, vendedor, oferta):
    """
    Tenta comprar um jogador de outro clube com a oferta do técnico.

    A proposta é recusada de imediato se o elenco do técnico já tiver MAX_ELENCO (25) jogadores, se a oferta
    for maior que o caixa ou se o vendedor não puder liberar o jogador. Caso contrário, a chance de aceitar
    cresce de forma linear com a razão entre oferta e preço pedido: é nula com 80% do pedido ou menos e certa
    a partir de 110%.

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
    chance = limitar((oferta / pedido - 0.8) / 0.3, 0, 1)
    if random.random() >= chance:
        return False, f"Proposta recusada. O {vendedor['nome']} quer {dinheiro(pedido)} por {rotulo(jogador)}."
    transferir(estado, jogador, vendedor, comprador, oferta)
    return True, f"{rotulo(jogador)} é o novo reforço do {comprador['nome']} por {dinheiro(oferta)}!"


def contratar_livre(estado, jogador):
    """
    Contrata um jogador sem clube para o time do técnico.

    A contratação é negada se o elenco já tiver MAX_ELENCO (25) jogadores ou se o caixa não cobrir as luvas.
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
    clube["caixa"] = round(clube["caixa"] - custo, 1)
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
            clube["caixa"] = round(clube["caixa"] - custo, 1)
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


def movimentar_mercado(estado):
    """
    Movimenta o mercado entre os clubes da IA.

    Há 45% de chance de tentar uma contratação de agente livre e 30% de chance de tentar uma negociação entre
    clubes da IA, de forma independente.

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        list: Textos das notícias geradas, sem as tentativas que não resultaram em negócio.
    """
    noticias = []
    if random.random() < 0.45:
        noticias.append(contratacao_de_livre_ia(estado))
    if random.random() < 0.3:
        noticias.append(negociacao_entre_ia(estado))
    return [texto for texto in noticias if texto]
