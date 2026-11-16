import sys

from config import ARQUIVO_EVENTOS, ARQUIVO_NARRACAO, ARQUIVO_NOMES, ARQUIVO_TIMES, PASTA_SUMULAS
from elenco.escalacao import completar_titulares, ler_banco_de_nomes
from interface.campo import criar_exibidor
from interface.controle import CONTROLE_HUMANO
from interface.entrada import confirmar, console, ler_texto
from interface import telas
from liga.eventos import aplicar_efeito, preparar_evento, sortear_evento
from liga.temporada import (
    adversario_de,
    clube_do_jogador,
    criar_estado_novo,
    fechar_rodada,
    jogo_do_jogador,
    resumo_final,
    simular_outros_jogos,
    temporada_acabou,
)
from partida.lances import criar_partida, jogar_partida
from partida.narracao import carregar_frases
from partida.simulacao import CONTROLE_IA, plano_ia
from persistencia.arquivos import anexar_txt, ler_json, ler_linhas_txt
from persistencia.ranking import ler_ranking, registrar_ranking
from persistencia.save import carregar_jogo, listar_saves, nome_do_arquivo, salvar_jogo


def carregar_recursos():
    recursos = {
        "clubes": ler_json(ARQUIVO_TIMES, []),
        "eventos": ler_json(ARQUIVO_EVENTOS, []),
        "nomes": ler_banco_de_nomes(ler_linhas_txt(ARQUIVO_NOMES)),
        "frases": carregar_frases(ler_linhas_txt(ARQUIVO_NARRACAO)),
    }
    faltando = [nome for nome, valor in recursos.items() if not valor]
    if faltando or not all(recursos["nomes"].values()):
        console.print(f"[red]Arquivos de dados ausentes ou inválidos na pasta dados/: {', '.join(faltando) or 'nomes'}[/]")
        sys.exit(1)
    return recursos


def novo_jogo(recursos):
    telas.titulo("NOVO JOGO")
    tecnico = ler_texto(" Nome do técnico (0 para voltar): ")
    if tecnico is None:
        return None
    clube_id = telas.escolher_clube(recursos["clubes"])
    if clube_id is None:
        return None
    return criar_estado_novo(tecnico, clube_id, recursos["clubes"], recursos["nomes"])


def montar_partida(estado, recursos, modo, velocidade):
    casa_id, fora_id = jogo_do_jogador(estado)
    casa = estado["clubes"][casa_id]
    fora = estado["clubes"][fora_id]
    planos = {
        casa_id: casa["plano"] if casa_id == estado["clube_id"] else plano_ia(casa, fora, True),
        fora_id: fora["plano"] if fora_id == estado["clube_id"] else plano_ia(fora, casa, False),
    }
    partida = criar_partida(casa, fora, recursos["frases"], planos[casa_id], planos[fora_id])
    partida["modo"] = modo
    partida["velocidade"] = velocidade
    return partida


def registrar_sumula(estado, resultado, numero):
    estado["sumulas"][str(numero)] = resultado["sumula"]
    casa = estado["clubes"][resultado["mandante"]]["nome"]
    fora = estado["clubes"][resultado["visitante"]]["nome"]
    texto = [f"Rodada {numero}: {casa} {resultado['gm']} x {resultado['gv']} {fora}"] + [f"  {linha}" for linha in resultado["sumula"]]
    anexar_txt(PASTA_SUMULAS / f"{nome_do_arquivo(estado['tecnico'])}.txt", "\n".join(texto) + "\n")


def evento_da_semana(estado, recursos):
    clube = clube_do_jogador(estado)
    evento = preparar_evento(sortear_evento(recursos["eventos"]), clube)
    efeito = telas.mostrar_evento(evento)
    mensagem = aplicar_efeito(estado, efeito, evento["jogador_id"], recursos["nomes"])
    completar_titulares(clube)
    telas.mostrar_mensagem(mensagem)


def jogar_rodada(estado, recursos):
    while True:
        escolha = telas.pre_jogo(estado)
        if escolha == 0:
            return
        if escolha == 4:
            telas.editar_plano(clube_do_jogador(estado))
            continue
        break
    completar_titulares(clube_do_jogador(estado))
    modo = "jogar" if escolha == 1 else "simular"
    velocidade = "rapida" if escolha == 3 else "normal"
    partida = montar_partida(estado, recursos, modo, velocidade)
    adversario = adversario_de(jogo_do_jogador(estado), estado["clube_id"])
    controles = {estado["clube_id"]: CONTROLE_HUMANO, adversario: CONTROLE_IA}
    resultado = jogar_partida(partida, controles, criar_exibidor(estado["clube_id"]))
    telas.mostrar_fim_de_jogo(estado, resultado)
    with console.status("Simulando os outros jogos da rodada..."):
        resultados = [resultado] + simular_outros_jogos(estado, recursos["frases"])
    numero = estado["rodada"]
    registrar_sumula(estado, resultado, numero)
    informacao = fechar_rodada(estado, resultados)
    telas.mostrar_resultados_rodada(estado, resultados, informacao, numero)
    if not temporada_acabou(estado):
        evento_da_semana(estado, recursos)
    if salvar_jogo(estado):
        console.print(" [dim]Jogo salvo automaticamente.[/]")


def encerrar_temporada(estado):
    resumo = resumo_final(estado)
    if not estado.get("ranking_registrado"):
        estado["ranking_registrado"] = registrar_ranking(resumo)
        salvar_jogo(estado)
    telas.mostrar_final(resumo)


def central(estado, recursos):
    while True:
        if temporada_acabou(estado):
            encerrar_temporada(estado)
            return
        escolha = telas.mostrar_central(estado)
        clube = clube_do_jogador(estado)
        if escolha == 1:
            jogar_rodada(estado, recursos)
        elif escolha == 2:
            telas.mostrar_elenco(clube)
        elif escolha == 3:
            telas.editar_plano(clube)
        elif escolha == 4:
            telas.mostrar_classificacao(estado)
        elif escolha == 5:
            telas.mostrar_rodadas(estado)
        elif escolha == 6:
            mensagem = "Jogo salvo!" if salvar_jogo(estado) else "Não foi possível salvar o jogo."
            telas.mostrar_mensagem(mensagem)
        elif confirmar(" Salvar antes de voltar ao menu?"):
            salvar_jogo(estado)
            return
        else:
            return


def abrir_save(recursos):
    caminho = telas.escolher_save(listar_saves())
    if not caminho:
        return
    estado = carregar_jogo(caminho)
    if estado:
        central(estado, recursos)
    else:
        telas.mostrar_mensagem("Save corrompido ou inválido.", "red")


def executar_opcao(escolha, recursos):
    if escolha == 1:
        estado = novo_jogo(recursos)
        if estado:
            central(estado, recursos)
    elif escolha == 2:
        abrir_save(recursos)
    else:
        telas.mostrar_ranking(ler_ranking())


def main():
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
