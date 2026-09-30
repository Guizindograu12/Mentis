def calcular_percentual(respostas):

    if not respostas:
        return 0.0

    media = sum(respostas) / len(respostas)

    percentual = ((media - 1) / 6) * 100

    return round(percentual, 2)


def classificar(valor):

    if valor <= 20:
        return "Muito Baixo"

    elif valor <= 40:
        return "Baixo"

    elif valor <= 60:
        return "Moderado"

    elif valor <= 80:
        return "Elevado"

    return "Muito Elevado"


def analisar_respostas(
    respostas_com_perguntas
):

    valores_gerais = [
        item["resposta"]
        for item in respostas_com_perguntas
    ]

    percentual_geral = calcular_percentual(
        valores_gerais
    )

    resultado = {
        "percentual_geral": percentual_geral,
        "classificacao_geral": classificar(
            percentual_geral
        ),
        "categorias": []
    }


    grupos = {}

    for item in respostas_com_perguntas:

        categoria = item["categoria"]

        grupos.setdefault(
            categoria,
            []
        )

        grupos[categoria].append(
            item["resposta"]
        )


    for categoria in sorted(grupos):

        percentual = calcular_percentual(
            grupos[categoria]
        )

        resultado["categorias"].append({

            "categoria": categoria,

            "percentual": percentual,

            "classificacao":
                classificar(percentual)

        })


    return resultado
