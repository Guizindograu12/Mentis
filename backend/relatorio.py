import bleach
import markdown

from markupsafe import Markup

from backend.database import buscar_analise_ia


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
            "hr"
        ],
        attributes={},
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
