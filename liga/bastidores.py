import random

from config import CHANCE_ENTREVISTA, CHANCE_EVENTO_POS, CHANCE_EVENTO_PRE, PESO_TORCIDA, TORCIDA_NA_FESTA
from elenco.escalacao import rotulo
from liga.eventos import escolher_alvo, mudar_energia, pagar
from liga.financas import lancar
from liga.temporada import adversario_de, ajustar_confianca, clube_do_jogador, jogo_do_jogador, resultado_para
from mercado.transferencias import dinheiro

CONTEXTOS = {"V": "vitoria", "E": "empate", "D": "derrota"}


def contexto_do_jogo(estado, resultado):
    """
    Descobre o contexto do momento: antes do jogo, ou o resultado do jogo que acabou.

    Args:
        estado (dict): Estado atual da temporada.
        resultado (dict | None): Resultado do jogo do técnico, ou None antes do jogo.

    Returns:
        str: "pre", "vitoria", "empate" ou "derrota".
    """
    if not resultado:
        return "pre"
    return CONTEXTOS[resultado_para(estado["clube_id"], resultado)]


def nome_do_adversario(estado, resultado):
    """
    Busca o nome do adversário do jogo atual ou do jogo que acabou.

    Args:
        estado (dict): Estado atual da temporada.
        resultado (dict | None): Resultado do jogo do técnico, ou None antes do jogo.

    Returns:
        str: Nome do adversário, ou "adversário" se não houver jogo.
    """
    jogo = (resultado["mandante"], resultado["visitante"]) if resultado else jogo_do_jogador(estado)
    if not jogo:
        return "adversário"
    return estado["clubes"][adversario_de(jogo, estado["clube_id"])]["nome"]


def joga_em_casa(estado, resultado):
    """
    Indica se o clube do técnico é (ou foi) o mandante do jogo.

    Args:
        estado (dict): Estado atual da temporada.
        resultado (dict | None): Resultado do jogo do técnico, ou None antes do jogo.

    Returns:
        bool: True se o técnico joga em casa.
    """
    jogo = (resultado["mandante"], resultado["visitante"]) if resultado else jogo_do_jogador(estado)
    return bool(jogo) and jogo[0] == estado["clube_id"]


def escolher_jogador_alvo(clube, alvo):
    """
    Escolhe o jogador citado num bastidor ou entrevista.

    Além dos alvos dos eventos da semana ("titular" e "melhor"), aceita "artilheiro", o jogador com mais gols
    na temporada (ou o melhor, se ninguém marcou).

    Args:
        clube (dict): Clube do técnico.
        alvo (str): Tipo de alvo.

    Returns:
        dict | None: Jogador escolhido, ou None se o alvo não envolve jogador.
    """
    if alvo == "artilheiro":
        artilheiro = max(clube["elenco"], key=lambda jogador: jogador["gols"], default=None)
        if artilheiro and artilheiro["gols"]:
            return artilheiro
        return escolher_alvo(clube, "melhor")
    return escolher_alvo(clube, alvo)


def montar_tela(texto, opcoes, efeito, jogador, adversario):
    """
    Monta o bastidor ou a entrevista no formato usado pela tela de eventos.

    Troca {jogador} e {adversario} no texto e nas opções.

    Args:
        texto (str): Texto do acontecimento.
        opcoes (list[dict]): Opções com texto e efeito.
        efeito (str | None): Efeito direto, quando não há opções.
        jogador (dict | None): Jogador citado.
        adversario (str): Nome do adversário.

    Returns:
        dict: Evento com texto, opções, efeito e jogador alvo.
    """
    nome = rotulo(jogador) if jogador else ""

    def preencher(frase):
        """
        Troca as marcações de uma frase.

        Args:
            frase (str): Frase com {jogador} e {adversario}.

        Returns:
            str: Frase preenchida.
        """
        return frase.replace("{jogador}", nome).replace("{adversario}", adversario)

    return {
        "texto": preencher(texto),
        "jogador_id": jogador["id"] if jogador else None,
        "efeito": efeito,
        "negociacao": None,
        "opcoes": [{"texto": preencher(opcao["texto"]), "efeito": opcao["efeito"]} for opcao in opcoes],
    }


def sortear_bastidor(estado, eventos, resultado=None):
    """
    Decide se acontece um bastidor antes ou depois do jogo e sorteia qual.

    Antes do jogo, acontece com CHANCE_EVENTO_PRE (30%); depois, com CHANCE_EVENTO_POS (35%). Só entram os
    eventos do momento cuja condição combina (vitória, empate, derrota, em casa ou fora). Os eventos da
    torcida organizada têm o peso multiplicado por PESO_TORCIDA conforme o nível do clube: o dobro nos grandes
    e a metade nos pequenos. Eventos que citam um jogador inexistente são descartados.

    Args:
        estado (dict): Estado atual da temporada.
        eventos (list[dict]): Bastidores lidos de bastidores.json.
        resultado (dict | None): Resultado do jogo do técnico, ou None antes do jogo. Padrão None.

    Returns:
        dict | None: Bastidor pronto para a tela, ou None.
    """
    momento = "pos" if resultado else "pre"
    if random.random() >= (CHANCE_EVENTO_POS if resultado else CHANCE_EVENTO_PRE):
        return None
    clube = clube_do_jogador(estado)
    contexto = contexto_do_jogo(estado, resultado)
    local = "casa" if joga_em_casa(estado, resultado) else "fora"
    possiveis = [
        evento
        for evento in eventos
        if evento["momento"] == momento and evento.get("condicao") in (None, contexto, local)
    ]
    if not possiveis:
        return None
    pesos = [evento["peso"] * (PESO_TORCIDA[clube["nivel"]] if evento.get("torcida") else 1) for evento in possiveis]
    evento = random.choices(possiveis, weights=pesos)[0]
    jogador = escolher_jogador_alvo(clube, evento.get("alvo", "nenhum"))
    if evento.get("alvo", "nenhum") != "nenhum" and not jogador:
        return None
    tela = montar_tela(
        evento["texto"], evento.get("opcoes", []), evento.get("efeito"), jogador, nome_do_adversario(estado, resultado)
    )
    tela["titulo"] = ("TORCIDA ORGANIZADA" if evento.get("torcida") else "BASTIDORES") + (
        " — PÓS-JOGO" if resultado else " — PRÉ-JOGO"
    )
    return tela


def sortear_entrevista(estado, entrevistas, resultado=None):
    """
    Decide se o técnico dá entrevista e sorteia a pergunta.

    A chance depende do nível do clube (CHANCE_ENTREVISTA: grandes são mais procurados pela imprensa), e antes
    do jogo cai para um terço. A pergunta vem do contexto (antes do jogo, vitória, empate ou derrota), de um
    veículo sorteado, e pode citar o adversário e o melhor jogador do time.

    Args:
        estado (dict): Estado atual da temporada.
        entrevistas (dict): Veículos e perguntas lidos de entrevistas.json.
        resultado (dict | None): Resultado do jogo do técnico, ou None antes do jogo. Padrão None.

    Returns:
        dict | None: Entrevista pronta para a tela, ou None.
    """
    clube = clube_do_jogador(estado)
    chance = CHANCE_ENTREVISTA[clube["nivel"]] * (1 if resultado else 1 / 3)
    if random.random() >= chance:
        return None
    pergunta = random.choice(entrevistas[contexto_do_jogo(estado, resultado)])
    jogador = escolher_jogador_alvo(clube, "artilheiro" if resultado else "titular")
    veiculo = random.choice(entrevistas["veiculos"])
    tela = montar_tela(
        f'{veiculo}: "{pergunta["pergunta"]}"',
        pergunta["respostas"],
        None,
        jogador,
        nome_do_adversario(estado, resultado),
    )
    tela["titulo"] = "ENTREVISTA" + (" — PÓS-JOGO" if resultado else " — PRÉ-JOGO")
    return tela


def cobrar_promessa(estado, resultado):
    """
    Cobra a promessa de vitória feita numa entrevista depois do jogo seguinte.

    Se o time perdeu, a diretoria tira 3 de confiança; se venceu, dá 1. Empate não muda nada. A promessa é
    apagada em qualquer caso.

    Args:
        estado (dict): Estado atual da temporada.
        resultado (dict | None): Resultado do jogo do técnico.

    Returns:
        str | None: Mensagem sobre a promessa, ou None se não havia promessa ou jogo.
    """
    if not resultado or not estado.pop("promessa", False):
        return None
    contexto = contexto_do_jogo(estado, resultado)
    if contexto == "derrota":
        ajustar_confianca(estado, -3)
        return "Você prometeu vitória na entrevista e o time perdeu. A diretoria cobrou: confiança -3."
    if contexto == "vitoria":
        ajustar_confianca(estado, 1)
        return "Promessa cumprida: você disse que o time venceria, e venceu. Confiança +1."
    return None


def titulares_sorteados(clube, quantidade):
    """
    Sorteia alguns titulares do clube.

    Args:
        clube (dict): Clube do técnico.
        quantidade (int): Quantos titulares sortear.

    Returns:
        list[dict]: Titulares sorteados.
    """
    por_id = {jogador["id"]: jogador for jogador in clube["elenco"]}
    titulares = [por_id[i] for i in clube["titulares"] if i in por_id]
    return random.sample(titulares, min(quantidade, len(titulares)))


def motivar(clube, quantidade):
    """
    Deixa titulares sorteados motivados (em grande fase) por uma rodada.

    Args:
        clube (dict): Clube do técnico.
        quantidade (int): Quantos titulares motivar.

    Returns:
        str: Nomes dos motivados, separados por vírgula.
    """
    escolhidos = titulares_sorteados(clube, quantidade)
    for jogador in escolhidos:
        jogador["fase"] = max(jogador["fase"], 1)
    return ", ".join(rotulo(jogador) for jogador in escolhidos)


def chatear(clube, quantidade):
    """
    Deixa titulares sorteados insatisfeitos por uma rodada.

    Args:
        clube (dict): Clube do técnico.
        quantidade (int): Quantos titulares chatear.

    Returns:
        str: Nomes dos insatisfeitos, separados por vírgula.
    """
    escolhidos = titulares_sorteados(clube, quantidade)
    for jogador in escolhidos:
        jogador["insatisfeito"] = max(jogador.get("insatisfeito", 0), 1)
    return ", ".join(rotulo(jogador) for jogador in escolhidos)


def aplicar_bastidor(estado, efeito, jogador_id):
    """
    Aplica o efeito de um bastidor ou de uma resposta de entrevista.

    Os efeitos mexem na confiança da diretoria, na energia do elenco, na motivação ou insatisfação de
    jogadores, em multas e prêmios no caixa, na festa da torcida no próximo jogo em casa e em promessas de
    vitória, que são cobradas por cobrar_promessa.

    Args:
        estado (dict): Estado atual da temporada.
        efeito (str | None): Nome do efeito.
        jogador_id (str | None): Jogador citado, quando houver.

    Returns:
        str: Mensagem descrevendo o que mudou.
    """
    clube = clube_do_jogador(estado)
    jogador = next((j for j in clube["elenco"] if j["id"] == jogador_id), None)
    if efeito == "arriscar_doente" and jogador:
        jogador["energia"] = max(0, jogador["energia"] - 25)
        return f"{rotulo(jogador)} joga, mas começa a partida sem fôlego (-25 de energia)."
    if efeito == "poupar_jogador" and jogador:
        if jogador["id"] in clube["titulares"]:
            clube["titulares"].remove(jogador["id"])
        jogador["energia"] = min(100, jogador["energia"] + 20)
        return f"{rotulo(jogador)} fica fora deste jogo para se recuperar. Outro entra no lugar."
    if efeito == "responder_provocacao":
        nomes = motivar(clube, 3)
        ajustar_confianca(estado, -1)
        return f"A resposta inflamou o elenco: {nomes} entram motivados. A diretoria não gostou: confiança -1."
    if efeito == "cansar_pouco":
        mudar_energia(clube, -5)
        return "O elenco entra em campo um pouco mais cansado (-5 de energia)."
    if efeito == "cansar_medio":
        mudar_energia(clube, -10)
        return "Ninguém dormiu direito: o elenco perde 10 de energia."
    if efeito == "motivar_titulares":
        return f"O elenco comprou a ideia: {motivar(clube, 3)} entram motivados."
    if efeito == "motivar_jogador" and jogador:
        jogador["fase"] = max(jogador["fase"], 2)
        return f"{rotulo(jogador)} ficou empolgado e está em grande fase nas próximas 2 rodadas."
    if efeito == "elogiar_jogadores":
        return f"Os jogadores gostaram dos elogios: {motivar(clube, 2)} chegam motivados."
    if efeito == "cobrar_jogador" and jogador:
        jogador["insatisfeito"] = max(jogador.get("insatisfeito", 0), 1)
        ajustar_confianca(estado, 1)
        return (
            f"{rotulo(jogador)} não gostou da cobrança pública (insatisfeito), mas a diretoria aprovou: confiança +1."
        )
    if efeito == "cobrar_jogadores":
        nomes = chatear(clube, 2)
        ajustar_confianca(estado, 1)
        return f"A diretoria gostou da cobrança (confiança +1), mas {nomes} ficaram insatisfeitos."
    if efeito == "confianca_mais_1":
        ajustar_confianca(estado, 1)
        return "A diretoria gostou da postura. Confiança +1."
    if efeito == "confianca_mais_2":
        ajustar_confianca(estado, 2)
        return "A diretoria respeitou a sua postura. Confiança +2."
    if efeito == "confianca_menos_1":
        ajustar_confianca(estado, -1)
        return "A decisão pegou mal com a diretoria. Confiança -1."
    if efeito == "confianca_menos_2":
        ajustar_confianca(estado, -2)
        return "A torcida e a diretoria não gostaram. Confiança -2."
    if efeito == "festa_no_estadio":
        estado["torcida_extra"] = TORCIDA_NA_FESTA
        ajustar_confianca(estado, 1)
        return "O estádio vai ferver: a torcida empurra o time por mais tempo no próximo jogo. Confiança +1."
    if efeito == "multar_balada" and jogador:
        lancar(estado, clube["id"], "Multas aplicadas", 0.5)
        jogador["insatisfeito"] = max(jogador.get("insatisfeito", 0), 1)
        return f"Os envolvidos pagam multa ({dinheiro(0.5)} para o clube) e {rotulo(jogador)} fica insatisfeito."
    if efeito == "deixar_passar":
        mudar_energia(clube, -10)
        ajustar_confianca(estado, -1)
        return "Ninguém foi punido: o elenco chega cansado (-10 de energia) e a diretoria reclamou (confiança -1)."
    if efeito == "pagar_bicho":
        if not pagar(estado, clube, "Bicho extra", 1.0):
            return "O clube não tem caixa para o bicho. Nada mudou."
        return f"Bicho pago: {motivar(clube, 3)} chegam motivados."
    if efeito == "reclamar_arbitragem":
        lancar(estado, clube["id"], "Multas", -0.5)
        ajustar_confianca(estado, 1)
        return f"O clube foi multado em {dinheiro(0.5)}, mas a diretoria apoiou a reclamação. Confiança +1."
    if efeito == "dialogar_organizada":
        if random.random() < 0.7:
            ajustar_confianca(estado, 1)
            return "A conversa acalmou a organizada. Confiança +1."
        ajustar_confianca(estado, -2)
        return "A conversa não adiantou e o protesto cresceu. Confiança -2."
    if efeito == "festa_desembarque":
        ajustar_confianca(estado, 2)
        return f"Clima de festa: confiança +2 e {motivar(clube, 2)} chegam embalados."
    if efeito == "punicao_briga":
        lancar(estado, clube["id"], "Multas", -1.0)
        ajustar_confianca(estado, -1)
        return f"O clube pagou {dinheiro(1.0)} de multa pela briga. Confiança -1."
    if efeito == "prometer_vitoria":
        estado["promessa"] = True
        ajustar_confianca(estado, 2)
        return "A torcida adorou a confiança (confiança +2). Mas se perder o próximo jogo, a diretoria vai cobrar."
    if efeito == "treinar_dobrado":
        mudar_energia(clube, -10)
        ajustar_confianca(estado, 1)
        return "Semana de treino dobrado: o elenco perde 10 de energia, mas a diretoria aprovou (confiança +1)."
    if efeito == "pedir_reforco":
        lancar(estado, clube["id"], "Verba da diretoria", 2.0)
        ajustar_confianca(estado, -2)
        return f"A diretoria liberou {dinheiro(2.0)} para reforços, mas não gostou da cobrança pública: confiança -2."
    return "Nada mudou."
