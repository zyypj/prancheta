import json
import os


def ler_json(caminho, padrao=None):
    """
    Lê e interpreta um arquivo JSON.

    O arquivo é aberto em UTF-8 dentro de um try/except: se ele não existir, não puder ser lido ou tiver JSON inválido, a função não interrompe o jogo e devolve o valor padrão.

    Args:
        caminho (str | Path): Caminho do arquivo JSON.
        padrao (Any): Valor devolvido em caso de erro. Padrão: None.

    Returns:
        Any: Conteúdo do JSON convertido para objetos Python ou o valor padrão em caso de erro.
    """
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (OSError, json.JSONDecodeError):
        return padrao


def gravar_json(caminho, dados):
    """
    Grava dados em um arquivo JSON.

    Cria a pasta de destino se ela não existir e escreve o arquivo em UTF-8, com acentos preservados e indentação de 2 espaços. Erros de sistema de arquivos ou dados que não podem ser convertidos para JSON são capturados por try/except e indicados no retorno.

    Args:
        caminho (str | Path): Caminho do arquivo JSON.
        dados (Any): Dados a serem gravados.

    Returns:
        bool: True se a gravação foi concluída, False em caso de erro.
    """
    try:
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
        return True
    except (OSError, TypeError, ValueError):
        return False


def ler_linhas_txt(caminho):
    """
    Lê as linhas de um arquivo de texto.

    Remove os espaços das pontas de cada linha e descarta as linhas vazias. Se o arquivo não puder ser aberto, o erro é capturado por try/except e a função devolve uma lista vazia.

    Args:
        caminho (str | Path): Caminho do arquivo de texto.

    Returns:
        list: Linhas não vazias do arquivo ou lista vazia em caso de erro.
    """
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            return [linha.strip() for linha in arquivo if linha.strip()]
    except OSError:
        return []


def anexar_txt(caminho, texto):
    """
    Acrescenta um texto ao final de um arquivo de texto.

    Cria a pasta de destino se ela não existir, remove os espaços e quebras de linha do fim do texto e grava em UTF-8 seguido de uma única quebra de linha. Erros de sistema de arquivos são capturados por try/except e indicados no retorno.

    Args:
        caminho (str | Path): Caminho do arquivo de texto.
        texto (str): Texto a ser acrescentado.

    Returns:
        bool: True se o texto foi gravado, False em caso de erro.
    """
    try:
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "a", encoding="utf-8") as arquivo:
            arquivo.write(texto.rstrip() + "\n")
        return True
    except OSError:
        return False
