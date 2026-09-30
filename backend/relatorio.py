from datetime import datetime


def montar_relatorio(
    resultado
):

    categorias = [
        {
            "categoria": categoria.categoria,
            "percentual": float(
                categoria.percentual
            ),
            "classificacao":
                categoria.classificacao
        }

        for categoria in resultado.categorias
    ]


    return {

        "teste_id":
            resultado.teste_id,

        "data_geracao":
            resultado.data_geracao,

        "percentual_geral":
            float(resultado.percentual_geral),

        "classificacao_geral":
            resultado.classificacao_geral,

        "categorias":
            categorias

    }
