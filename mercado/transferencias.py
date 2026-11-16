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
    return f"R$ {valor:.1f} mi".replace(".", ",")


def gerar_agentes_livres(banco, usados, quantidade=AGENTES_LIVRES):
    livres = []
    for numero in range(1, quantidade + 1):
        posicao = random.choice(POSICOES_LIVRES)
        qualidade = limitar(round(random.gauss(64, 7)), 45, 82)
        idade = random.choice((random.randint(18, 22), random.randint(29, 35)))
        livres.append(criar_jogador(f"liv-{numero:02d}", sortear_nome(banco, usados), posicao, qualidade, idade))
    return livres


def noticia(estado, texto):
    estado["noticias"] = (estado.get("noticias", []) + [texto])[-20:]
    return texto


def quantos_na_posicao(elenco, posicao):
    return sum(1 for jogador in elenco if jogador["pos"] == posicao)


def pode_sair(clube, jogador):
    return len(clube["elenco"]) > ELENCO_MINIMO and quantos_na_posicao(clube["elenco"], jogador["pos"]) > MINIMO_POR_POSICAO[jogador["pos"]]


def preco_pedido(clube, jogador):
    preco = valor_de_mercado(jogador)
    if jogador["id"] in clube["titulares"]:
        preco *= 1.3
    if clube["nivel"] == "grande":
        preco *= 1.15
    return round(preco, 1)


def luvas(jogador):
    return round(max(0.2, valor_de_mercado(jogador) * 0.15), 1)


def jogadores_a_venda(estado, posicao=None):
    disponiveis = [
        (jogador, clube)
        for clube in estado["clubes"].values()
        if clube["id"] != estado["clube_id"]
        for jogador in clube["elenco"]
        if posicao is None or jogador["pos"] == posicao
    ]
    return sorted(disponiveis, key=lambda par: par[0]["qualidade"], reverse=True)


def reorganizar(estado, clube):
    if clube["id"] == estado["clube_id"]:
        completar_titulares(clube)
    else:
        clube["titulares"] = escalar_automatico(clube["elenco"], clube["plano"]["formacao"])


def transferir(estado, jogador, vendedor, comprador, valor):
    vendedor["elenco"].remove(jogador)
    if jogador["id"] in vendedor["titulares"]:
        vendedor["titulares"].remove(jogador["id"])
    comprador["elenco"].append(jogador)
    vendedor["caixa"] = round(vendedor.get("caixa", 0) + valor, 1)
    comprador["caixa"] = round(comprador.get("caixa", 0) - valor, 1)
    reorganizar(estado, vendedor)
    if comprador["id"] != estado["clube_id"]:
        reorganizar(estado, comprador)
    return noticia(estado, f"{comprador['nome']} contrata {rotulo(jogador)} do {vendedor['nome']} por {dinheiro(valor)}.")


def tentar_comprar(estado, jogador, vendedor, oferta):
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
    valor = valor_de_mercado(jogador)
    interessados = [
        clube for clube in estado["clubes"].values()
        if clube["id"] != estado["clube_id"] and len(clube["elenco"]) < MAX_ELENCO and clube.get("caixa", 0) >= valor * 0.7
    ]
    random.shuffle(interessados)
    ofertas = []
    for clube in interessados[:3]:
        oferta = round(min(clube["caixa"], valor * random.uniform(0.75, 1.2)), 1)
        ofertas.append((clube, oferta))
    return sorted(ofertas, key=lambda par: par[1], reverse=True)


def vender(estado, jogador, comprador, valor):
    vendedor = estado["clubes"][estado["clube_id"]]
    transferir(estado, jogador, vendedor, comprador, valor)
    return f"{rotulo(jogador)} vendido ao {comprador['nome']} por {dinheiro(valor)}."


def pior_da_posicao(clube, posicao):
    da_posicao = [jogador for jogador in clube["elenco"] if jogador["pos"] == posicao]
    return min(da_posicao, key=lambda jogador: jogador["qualidade"]) if da_posicao else None


def contratacao_de_livre_ia(estado):
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
    clubes = [c for c in estado["clubes"].values() if c["id"] != estado["clube_id"]]
    comprador = random.choice(clubes)
    if len(comprador["elenco"]) >= MAX_ELENCO:
        return None
    vendedores = [c for c in clubes if c is not comprador]
    vendedor = random.choice(vendedores)
    candidatos = [
        jogador for jogador in vendedor["elenco"]
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
    noticias = []
    if random.random() < 0.45:
        noticias.append(contratacao_de_livre_ia(estado))
    if random.random() < 0.3:
        noticias.append(negociacao_entre_ia(estado))
    return [texto for texto in noticias if texto]
