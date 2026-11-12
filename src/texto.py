import re

TIME_RE = re.compile(r"\b\d{2}:\d{2}(?::\d{2})?\b")
RELEVANTE_RE = re.compile(r"sucesso|registrad|erro|matr[ií]cula|hoje|entrada|sa[ií]da", re.I)


def eh_placeholder(texto: str) -> bool:
    limpo = texto.strip()
    if not limpo:
        return True
    if re.fullmatch(r"[-–—. ]+", limpo):
        return True
    return bool(re.match(r"^(selecione|escolha|opção|opcao)\b", limpo, re.I) and not re.search(r"\d{3,}", limpo))


def opcoes_de_matricula(textos: list[str]) -> list[str]:
    reais: list[str] = []
    for texto in textos:
        limpo = " ".join(texto.split())
        if not limpo or eh_placeholder(limpo):
            continue
        reais.append(limpo)
    if not reais or all(re.fullmatch(r"20\d{2}", item) for item in reais):
        return []
    return reais


def linhas_relevantes(texto: str) -> list[str]:
    linhas: list[str] = []
    for bruta in texto.splitlines():
        linha = " ".join(bruta.split())
        if not linha:
            continue
        if TIME_RE.search(linha) or RELEVANTE_RE.search(linha):
            if linha not in linhas:
                linhas.append(linha)
    return linhas


def resumo_registro(texto: str) -> str:
    linhas = linhas_relevantes(texto)
    if linhas:
        return "Ponto enviado. O que apareceu na tela:\n" + "\n".join(linhas[:12])
    return "Cliquei em registrar e confirmei. Confere o horário na imagem."


def resumo_consulta(texto: str) -> str:
    linhas = linhas_relevantes(texto)
    if linhas:
        return "Registros que aparecem na tela:\n" + "\n".join(linhas[:20])
    return "Abri a tela de ponto, mas não achei horários listados. A imagem mostra o que o portal exibiu."
