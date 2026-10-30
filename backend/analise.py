def calcular_percentual(respostas):
    """
    Calcula o percentual de dificuldade considerando:

    - Respostas de 1 a 7.
    - Peso de relevância de cada pergunta.
    - Inversão das perguntas positivas.

    Cada item deve conter:
    resposta, peso e invertida.

    O resultado varia de 0 a 100.
    Quanto maior o percentual, maior a dificuldade indicada.
    """

    if not respostas:
        return 0.0

    soma_ponderada = 0.0
    soma_pesos = 0.0

    for item in respostas:

        if isinstance(item, dict):

            resposta = int(item["resposta"])

            peso = float(
                item.get("peso", 1.0)
            )

            invertida = bool(
                item.get("invertida", False)
            )

        else:

            resposta = int(item)

            peso = 1.0

            invertida = False

        if resposta < 1 or resposta > 7:

            raise ValueError(
                "As respostas precisam estar entre 1 e 7."
            )

        if peso <= 0:

            raise ValueError(
                "O peso de uma pergunta precisa ser maior que zero."
            )

        if peso > 1:

            raise ValueError(
                "O peso de uma pergunta não pode ser maior que 1."
            )

        # Perguntas positivas:
        # quanto maior a concordância, menor a dificuldade.
        #
        # Por isso, a pontuação é invertida.

        if invertida:

            resposta = 8 - resposta

        soma_ponderada += resposta * peso

        soma_pesos += peso

    if soma_pesos == 0:

        return 0.0

    media_ponderada = (
        soma_ponderada / soma_pesos
    )

    percentual = (
        (media_ponderada - 1) / 6
    ) * 100

    return round(
        max(0.0, min(100.0, percentual)),
        2
    )


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


def analisar_respostas(respostas_com_perguntas):

    if not respostas_com_perguntas:

        raise ValueError(
            "Não existem respostas para realizar a análise."
        )

    # Calcula o resultado geral considerando
    # os pesos e a inversão de cada pergunta.

    percentual_geral = calcular_percentual(
        respostas_com_perguntas
    )

    resultado = {

        "percentual_geral": percentual_geral,

        "classificacao_geral": classificar(
            percentual_geral
        ),

        "categorias": []

    }

    # Separa as respostas por categoria.

    grupos = {}

    for item in respostas_com_perguntas:

        categoria = item["categoria"]

        grupos.setdefault(
            categoria,
            []
        )

        grupos[categoria].append(item)

    # Calcula o percentual individual de cada categoria.

    for categoria in sorted(grupos):

        percentual = calcular_percentual(
            grupos[categoria]
        )

        resultado["categorias"].append({

            "categoria": categoria,

            "percentual": percentual,

            "classificacao": classificar(
                percentual
            )

        })

    return resultado