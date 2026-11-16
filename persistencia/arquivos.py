import json
import os


def ler_json(caminho, padrao=None):
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (OSError, json.JSONDecodeError):
        return padrao


def gravar_json(caminho, dados):
    try:
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
        return True
    except (OSError, TypeError, ValueError):
        return False


def ler_linhas_txt(caminho):
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            return [linha.strip() for linha in arquivo if linha.strip()]
    except OSError:
        return []


def anexar_txt(caminho, texto):
    try:
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "a", encoding="utf-8") as arquivo:
            arquivo.write(texto.rstrip() + "\n")
        return True
    except OSError:
        return False
