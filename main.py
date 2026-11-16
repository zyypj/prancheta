import sys

from config import (
    ARQUIVO_BASTIDORES,
    ARQUIVO_ENTREVISTAS,
    ARQUIVO_EVENTOS,
    ARQUIVO_NARRACAO,
    ARQUIVO_NOMES,
    ARQUIVO_TIMES,
    PASTA_SUMULAS,
)
from elenco.escalacao import completar_titulares, ler_banco_de_nomes
from interface import telas
from interface.campo import criar_exibidor
from interface.controle import CONTROLE_HUMANO, menu_pausa
from interface.entrada import confirmar, console, ler_texto
from interface.mercado import tela_mercado, tela_proposta
from interface.treino import tela_treino
from liga.bastidores import aplicar_bastidor, cobrar_promessa, sortear_bastidor, sortear_entrevista
from liga.desafios import atualizar_objetivos, avaliar_desafio
from liga.eventos import aplicar_efeito, escolher_evento
from liga.temporada import (
    adversario_de,
    avancar_etapa,
    clube_do_jogador,
    criar_estado_novo,
    descricao_etapa,
    etapa_atual,
    fechar_fase_copa,
    fechar_rodada,
    jogo_do_jogador,
    jogo_neutro,
    mata_mata,
    resumo_final,
    simular_outros_jogos,
    temporada_acabou,
)
from liga.vestiario import resolver_discussao, sortear_discussao
from mercado.transferencias import movimentar_mercado
from partida.jogo import jogar_partida
from partida.lances import criar_partida
from partida.narracao import carregar_frases
from partida.simulacao import CONTROLE_IA, plano_ia
from persistencia.arquivos import anexar_txt, ler_json, ler_linhas_txt
from persistencia.ranking import ler_ranking, registrar_ranking
from persistencia.save import carregar_jogo, listar_saves, nome_do_arquivo, salvar_jogo


def carregar_recursos():
    """
    Carrega os arquivos de dados necessários para o funcionamento do jogo.

    Realiza a leitura das informações dos clubes, eventos, nomes de jogadores e frases utilizadas na narração
    das partidas.

    Verifica se os dados obrigatórios foram carregados corretamente, encerrando a execução caso algum recurso
    esteja ausente ou inválido.

    Returns:
        dict: Dicionário contendo clubes, eventos, nomes e frases de narração.
    """
    recursos = {
        "clubes": ler_json(ARQUIVO_TIMES, []),
        "eventos": ler_json(ARQUIVO_EVENTOS, []),
        "bastidores": ler_json(ARQUIVO_BASTIDORES, []),
        "entrevistas": ler_json(ARQUIVO_ENTREVISTAS, {}),
        "nomes": ler_banco_de_nomes(ler_linhas_txt(ARQUIVO_NOMES)),
        "frases": carregar_frases(ler_linhas_txt(ARQUIVO_NARRACAO)),
    }
    faltando = [nome for nome, valor in recursos.items() if not valor]
    if faltando or not all(recursos["nomes"].values()):
        console.print(
            f"[red]Arquivos de dados ausentes ou inválidos na pasta dados/: {', '.join(faltando) or 'nomes'}[/]"
        )
        sys.exit(1)
    return recursos


def novo_jogo(recursos):
    """
    Inicia a criação de uma nova temporada.

    Solicita o nome do técnico e permite selecionar um clube, utilizando os recursos previamente carregados.

    Args:
        recursos (dict): Dados necessários para criar o jogo.

    Returns:
        dict | None: Estado inicial da temporada ou None caso o usuário cancele a operação.
    """
    telas.titulo("NOVO JOGO")
    tecnico = ler_texto(" Nome do técnico (0 para voltar): ")
    if tecnico is None:
        return None
    clube_id = telas.escolher_clube(recursos["clubes"])
    if clube_id is None:
        return None
    return criar_estado_novo(tecnico, clube_id, recursos["clubes"], recursos["nomes"])


def montar_partida(estado, recursos, modo, velocidade):
    """
    Prepara uma partida a partir do estado atual da temporada.

    Identifica os clubes participantes, define os planos táticos, aplica a festa da torcida preparada num
    bastidor (só quando o técnico joga em casa), configura a inteligência artificial e
    estabelece o modo e a velocidade de execução da partida.

    Args:
        estado (dict): Estado atual da temporada.
        recursos (dict): Recursos utilizados pela partida.
        modo (str): Modo de jogo escolhido.
        velocidade (str): Velocidade de execução.

    Returns:
        dict: Estrutura com os dados da partida preparada.
    """
    casa_id, fora_id = jogo_do_jogador(estado)
    casa = estado["clubes"][casa_id]
    fora = estado["clubes"][fora_id]
    neutro = jogo_neutro(estado)
    planos = {
        casa_id: casa["plano"] if casa_id == estado["clube_id"] else plano_ia(casa, fora, not neutro),
        fora_id: fora["plano"] if fora_id == estado["clube_id"] else plano_ia(fora, casa, False),
    }
    partida = criar_partida(casa, fora, recursos["frases"], planos[casa_id], planos[fora_id], neutro)
    torcida_extra = estado.pop("torcida_extra", 0)
    if casa_id == estado["clube_id"] and not neutro:
        partida["torcida"] = torcida_extra
    partida["modo"] = modo
    partida["velocidade"] = velocidade
    return partida


def registrar_sumula(estado, resultado, chave, titulo_jogo):
    """
    Registra a súmula de uma partida disputada.

    Armazena os acontecimentos no histórico da temporada e adiciona o resultado e os lances ao arquivo de
    texto correspondente ao técnico.

    Args:
        estado (dict): Estado atual da temporada.
        resultado (dict): Resultado e súmula da partida.
        chave (str): Chave da súmula no histórico (número da rodada ou fase da copa).
        titulo_jogo (str): Competição e rodada ou fase, usado no arquivo de texto.
    """
    estado["sumulas"][chave] = resultado["sumula"]
    casa = estado["clubes"][resultado["mandante"]]["nome"]
    fora = estado["clubes"][resultado["visitante"]]["nome"]
    cabecalho = f"{titulo_jogo}: {casa} {resultado['gm']} x {resultado['gv']} {fora}"
    texto = [cabecalho] + [f"  {linha}" for linha in resultado["sumula"]]
    anexar_txt(PASTA_SUMULAS / f"{nome_do_arquivo(estado['tecnico'])}.txt", "\n".join(texto) + "\n")


def bastidores_do_jogo(estado, recursos, resultado=None):
    """
    Mostra, de vez em quando, uma entrevista ou um bastidor antes ou depois do jogo do técnico.

    Depois do jogo, primeiro cobra a promessa de vitória feita numa entrevista, se houver. Em seguida tenta
    uma entrevista (mais comum em clubes grandes) e, se não houver, um bastidor (eventos do dia do jogo e da
    torcida organizada). No máximo um dos dois aparece em cada momento, para não interromper demais.

    Args:
        estado (dict): Estado atual da temporada.
        recursos (dict): Recursos carregados, com bastidores e entrevistas.
        resultado (dict | None): Resultado do jogo do técnico, ou None antes do jogo. Padrão None.
    """
    aviso = cobrar_promessa(estado, resultado)
    if aviso:
        telas.mostrar_mensagem(aviso, "bold")
    tela = sortear_entrevista(estado, recursos["entrevistas"], resultado) or sortear_bastidor(
        estado, recursos["bastidores"], resultado
    )
    if not tela:
        return
    efeito = telas.mostrar_evento(tela, tela["titulo"])
    telas.mostrar_mensagem(aplicar_bastidor(estado, efeito, tela["jogador_id"]))


def evento_da_semana(estado, recursos, resultado=None):
    """
    Executa um evento aleatório após uma rodada.

    Primeiro vê se algo do último jogo ou do elenco causou uma discussão entre jogadores; se sim, a semana é
    dela, mostrada na tela do vestiário. Senão, sorteia um acontecimento, apresenta suas opções ao usuário e
    aplica o efeito escolhido. Quando o evento é uma proposta por um jogador, abre a tela de negociação, e o
    valor acertado nela é o que entra no caixa. No fim, atualiza a escalação do clube.

    Args:
        estado (dict): Estado atual da temporada.
        recursos (dict): Dados dos eventos e jogadores.
        resultado (dict | None): Resultado do último jogo do técnico, usado nas discussões. Padrão None.
    """
    clube = clube_do_jogador(estado)
    discussao = sortear_discussao(estado, resultado)
    if discussao:
        efeito = telas.mostrar_evento(discussao, "VESTIÁRIO")
        mensagem = resolver_discussao(estado, discussao, efeito)
    else:
        evento = escolher_evento(recursos["eventos"], clube, estado.get("eventos_recentes", []))
        estado["eventos_recentes"] = (estado.get("eventos_recentes", []) + [evento["id"]])[-4:]
        negociacao = evento["negociacao"]
        efeito = tela_proposta(estado, evento) if negociacao else telas.mostrar_evento(evento)
        valor_venda = negociacao["acordo"] if negociacao else None
        mensagem = aplicar_efeito(estado, efeito, evento["jogador_id"], recursos["nomes"], valor_venda)
    completar_titulares(clube)
    telas.mostrar_mensagem(mensagem)


def escolher_como_jogar(estado):
    """
    Mostra a tela de pré-jogo até o usuário decidir como disputar a partida.

    As opções de ver o adversário, ajustar o plano de jogo e treinar o elenco abrem suas telas e voltam para o
    pré-jogo, sem iniciar a partida.

    Args:
        estado (dict): Estado atual da temporada.

    Returns:
        int: 1 para jogar, 2 para simular assistindo, 3 para simular rápido, 4 para ir direto ao resultado ou
            0 para voltar.
    """
    while True:
        escolha = telas.pre_jogo(estado)
        if escolha == 5:
            telas.mostrar_clube(estado, adversario_de(jogo_do_jogador(estado), estado["clube_id"]))
        elif escolha == 6:
            telas.editar_plano(clube_do_jogador(estado))
        elif escolha == 7:
            tela_treino(estado)
        else:
            return escolha


def jogar_partida_do_jogador(estado, recursos, escolha):
    """
    Disputa a partida do clube do jogador no modo escolhido.

    Completa os titulares desfalcados, monta a partida e define quem controla cada time. No modo "só o
    resultado" os dois times ficam com a IA e nada é exibido; nos outros modos o jogador controla o próprio
    time e a partida é desenhada no campo. Em jogos de mata-mata o empate vai para os pênaltis.

    Args:
        estado (dict): Estado atual da temporada.
        recursos (dict): Recursos carregados, incluindo as frases de narração.
        escolha (int): Modo escolhido no pré-jogo, de 1 a 4.

    Returns:
        dict: Resultado da partida, com placar, súmula e vencedor.
    """
    completar_titulares(clube_do_jogador(estado))
    modo = "jogar" if escolha == 1 else "simular"
    velocidade = "rapida" if escolha in (3, 4) else "normal"
    partida = montar_partida(estado, recursos, modo, velocidade)
    adversario = adversario_de(jogo_do_jogador(estado), estado["clube_id"])
    if escolha == 4:
        controles = {estado["clube_id"]: CONTROLE_IA, adversario: CONTROLE_IA}
        with console.status("Simulando a partida..."):
            resultado = jogar_partida(partida, controles, mata_mata=mata_mata(estado))
    else:
        controles = {estado["clube_id"]: CONTROLE_HUMANO, adversario: CONTROLE_IA}
        exibidor = criar_exibidor(estado["clube_id"], menu_pausa)
        resultado = jogar_partida(partida, controles, exibidor, mata_mata(estado))
    telas.mostrar_fim_de_jogo(estado, resultado)
    return resultado


def jogar_etapa(estado, recursos):
    """
    Disputa a etapa atual da temporada, seja uma rodada da liga ou uma fase da copa.

    Joga a partida do clube do jogador (se ele estiver na etapa), com os bastidores de antes e depois do
    jogo, avalia o desafio da diretoria, simula os
    outros jogos, registra a súmula, fecha a rodada ou a fase e confere os objetivos da temporada. Depois
    movimenta o mercado dos outros clubes, mostra os resultados, avança para a próxima etapa, sorteia o evento
    da semana e salva o jogo automaticamente.

    Args:
        estado (dict): Estado atual da temporada.
        recursos (dict): Recursos carregados (frases, eventos e nomes).
    """
    etapa = etapa_atual(estado)
    competicao, valor = etapa
    resultado = None
    if jogo_do_jogador(estado):
        escolha = escolher_como_jogar(estado)
        if escolha == 0:
            return
        estado["extrato_etapa"] = []
        bastidores_do_jogo(estado, recursos)
        resultado = jogar_partida_do_jogador(estado, recursos, escolha)
        bastidores_do_jogo(estado, recursos, resultado)
    else:
        estado["extrato_etapa"] = []
    desafio = avaliar_desafio(estado, resultado)
    with console.status("Simulando os outros jogos..."):
        resultados = ([resultado] if resultado else []) + simular_outros_jogos(estado, recursos["frases"])
    if competicao == "liga":
        registrar_sumula(estado, resultado, str(valor), f"Liga, rodada {valor}")
        informacao = fechar_rodada(estado, resultados)
        titulo_tela = f"RESULTADOS DA RODADA {valor}"
    else:
        if resultado:
            registrar_sumula(estado, resultado, f"copa-{valor}", descricao_etapa(etapa))
        informacao = fechar_fase_copa(estado, resultados)
        titulo_tela = f"RESULTADOS — {descricao_etapa(etapa).upper()}"
    informacao["desafio"] = desafio
    informacao["objetivos"] = atualizar_objetivos(estado)
    noticias = movimentar_mercado(estado, recursos["nomes"])
    telas.mostrar_resultados(estado, titulo_tela, resultados, informacao, noticias)
    avancar_etapa(estado)
    if not temporada_acabou(estado):
        evento_da_semana(estado, recursos, resultado)
    if salvar_jogo(estado):
        console.print(" [dim]Jogo salvo automaticamente.[/]")


def encerrar_temporada(estado):
    """
    Encerra a temporada e mostra o resumo final.

    Confere os objetivos que só valem no fim (como o saldo de gols), calcula a pontuação do técnico e grava no
    ranking uma única vez, mesmo que o save seja aberto de novo depois do fim.

    Args:
        estado (dict): Estado da temporada encerrada.
    """
    atualizar_objetivos(estado)
    resumo = resumo_final(estado)
    if not estado.get("ranking_registrado"):
        estado["ranking_registrado"] = registrar_ranking(resumo)
        salvar_jogo(estado)
    telas.mostrar_final(resumo)


def central(estado, recursos):
    """
    Mantém o usuário na central do clube durante a temporada.

    Mostra a central e executa a opção escolhida: próximo jogo, elenco, plano de jogo, treino, classificação,
    copa, rodadas, mercado, clubes, finanças e objetivos ou salvar. Ao voltar, pergunta se deve salvar. Quando a
    temporada acaba, encerra e sai.

    Args:
        estado (dict): Estado atual da temporada.
        recursos (dict): Recursos carregados do jogo.
    """
    while True:
        if temporada_acabou(estado):
            encerrar_temporada(estado)
            return
        escolha = telas.mostrar_central(estado)
        clube = clube_do_jogador(estado)
        if escolha == 1:
            jogar_etapa(estado, recursos)
        elif escolha == 2:
            telas.mostrar_elenco(clube)
        elif escolha == 3:
            telas.editar_plano(clube)
        elif escolha == 4:
            tela_treino(estado)
        elif escolha == 5:
            telas.mostrar_classificacao(estado)
        elif escolha == 6:
            telas.mostrar_copa(estado)
        elif escolha == 7:
            telas.mostrar_rodadas(estado)
        elif escolha == 8:
            tela_mercado(estado)
        elif escolha == 9:
            telas.escolher_clube_para_ver(estado)
        elif escolha == 10:
            telas.mostrar_financas(estado)
        elif escolha == 11:
            mensagem = "Jogo salvo!" if salvar_jogo(estado) else "Não foi possível salvar o jogo."
            telas.mostrar_mensagem(mensagem)
        elif confirmar(" Salvar antes de voltar ao menu?"):
            salvar_jogo(estado)
            return
        else:
            return


def abrir_save(recursos):
    """
    Lista os saves, carrega o escolhido e abre a central do clube.

    Mostra um aviso se o arquivo estiver corrompido ou for de uma versão antiga.

    Args:
        recursos (dict): Recursos carregados do jogo.
    """
    caminho = telas.escolher_save(listar_saves())
    if not caminho:
        return
    estado = carregar_jogo(caminho)
    if estado:
        central(estado, recursos)
    else:
        telas.mostrar_mensagem("Save corrompido ou inválido.", "red")


def executar_opcao(escolha, recursos):
    """
    Executa a opção escolhida no menu inicial.

    Args:
        escolha (int): 1 para novo jogo, 2 para carregar e 3 para ver o ranking.
        recursos (dict): Recursos carregados do jogo.
    """
    if escolha == 1:
        estado = novo_jogo(recursos)
        if estado:
            central(estado, recursos)
    elif escolha == 2:
        abrir_save(recursos)
    else:
        telas.mostrar_ranking(ler_ranking())


def main():
    """
    Ponto de entrada do jogo.

    Carrega os recursos e repete o menu inicial até o usuário escolher sair. Qualquer erro inesperado numa
    opção é mostrado na tela e o jogo volta ao menu em vez de fechar.
    """
    recursos = carregar_recursos()
    while True:
        escolha = telas.mostrar_menu_inicial()
        if escolha == 4:
            console.print("[green]Até a próxima![/]")
            break
        try:
            executar_opcao(escolha, recursos)
        except (KeyboardInterrupt, EOFError):
            raise
        except Exception as erro:
            telas.mostrar_mensagem(f"Algo deu errado ({type(erro).__name__}: {erro}). Voltando ao menu.", "red")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[yellow]Jogo encerrado.[/]")
