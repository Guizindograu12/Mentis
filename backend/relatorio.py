
import re

import bleach
import markdown

from markupsafe import Markup

from backend.database import buscar_analise_ia


def colorir_tendencias(html):

    tendencias = {
        "aumento leve": "tendencia-aumento-leve",
        "aumento": "tendencia-aumento",
        "redução leve": "tendencia-reducao-leve",
        "redução": "tendencia-reducao",
        "estável": "tendencia-estavel"
    }

    padrao = re.compile(
        r"<strong>\s*(Aumento leve|Aumento|Redução leve|Redução|Estável)\s*</strong>",
        re.IGNORECASE
    )

    def substituir(match):

        texto = match.group(1)
        classe = tendencias[texto.casefold()]

        return (
            f'<span class="tendencia {classe}">'
            f'{texto}'
            f'</span>'
        )

    return padrao.sub(substituir, html)


def colorir_classificacoes(html):

    classificacoes = {
        "muito elevado": "indicador-muito-elevado",
        "elevado": "indicador-elevado",
        "moderado": "indicador-moderado",
        "baixo": "indicador-baixo"
    }

    padrao = re.compile(
        r"\((Muito Elevado|Elevado|Moderado|Baixo)\)",
        re.IGNORECASE
    )

    def substituir(match):

        texto = match.group(1)
        classe = classificacoes[texto.casefold()]

        return (
            f'(<span class="indicador-classificacao {classe}">'
            f'{texto}'
            f'</span>)'
        )

    return padrao.sub(substituir, html)


def converter_analise_html(texto):

    if not texto:
        return Markup("")

    html = markdown.markdown(
        texto,
        extensions=[
            "extra",
            "sane_lists"
        ]
    )

    html = colorir_tendencias(html)
    html = colorir_classificacoes(html)

    html_seguro = bleach.clean(
        html,
        tags=[
            "p",
            "strong",
            "em",
            "ul",
            "ol",
            "li",
            "h3",
            "h4",
            "blockquote",
            "br",
            "hr",
            "span"
        ],
        attributes={
            "span": ["class"]
        },
        strip=True
    )

    return Markup(html_seguro)


def montar_relatorio(resultado):

    categorias = [
        {
            "categoria": categoria.categoria,
            "percentual": float(categoria.percentual),
            "classificacao": categoria.classificacao
        }
        for categoria in resultado.categorias
    ]

    analise_ia = buscar_analise_ia(resultado.id)

    texto_analise = (
        analise_ia.texto
        if analise_ia
        else "A análise personalizada ainda não está disponível."
    )

    return {
        "teste_id": resultado.teste_id,
        "data_geracao": resultado.data_geracao,
        "percentual_geral": float(resultado.percentual_geral),
        "classificacao_geral": resultado.classificacao_geral,
        "categorias": categorias,

        "analise_personalizada": texto_analise,

        "analise_personalizada_html": converter_analise_html(
            texto_analise
        ),

        "status_analise": (
            analise_ia.status if analise_ia else "pendente"
        )
    }
