# ==========================================
# AJUSTE DE SENSIBILIDADE DO RESULTADO
# ==========================================
#
# A média de muitas respostas tende a ficar no meio (perto de 50%),
# porque quase ninguém responde só 1 ou só 7.
#
# Para o resultado variar mais, o percentual é "esticado" a partir
# do centro (50%):
#   - 50% continua 50%
#   - 0% e 100% continuam 0% e 100%
#   - a ordem entre as pessoas nunca muda
#
# Quanto MENOR o número, MAIS o resultado se afasta do centro.
#   1.00 = sem ajuste (como era antes)
#   0.75 = ajuste médio (padrão do resultado geral)
#   0.60 = ajuste forte

EXPOENTE_GERAL = 0.75

# As categorias têm poucas perguntas (2 ou 3), então já variam
# bastante sozinhas. Por isso o ajuste delas é mais leve.

EXPOENTE_CATEGORIA = 0.90


def ampliar_resultado(percentual, expoente):
    """
    Afasta o percentual do centro (50%), mantendo 0%, 50% e 100%.

    Exemplo com expoente 0.75:
    60% vira 65%, 70% vira 75% e 80% vira 84%.
    """

    if expoente <= 0:

        raise ValueError(
            "O expoente de ajuste precisa ser maior que zero."
        )

    # Distância do centro, de -1 (0%) até +1 (100%)
    distancia = (percentual - 50) / 50

    sinal = 1 if distancia >= 0 else -1

    nova_distancia = sinal * (abs(distancia) ** expoente)

    novo_percentual = 50 + 50 * nova_distancia

    return round(
        max(0.0, min(100.0, novo_percentual)),
        2
    )


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

    Este é o percentual "bruto", sem o ajuste de sensibilidade.
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
    # os pesos e a inversão de cada pergunta
    # e aplica o ajuste de sensibilidade.

    percentual_geral = ampliar_resultado(
        calcular_percentual(respostas_com_perguntas),
        EXPOENTE_GERAL
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

    # Calcula o percentual individual de cada categoria,
    # com o ajuste mais leve.

    for categoria in sorted(grupos):

        percentual = ampliar_resultado(
            calcular_percentual(grupos[categoria]),
            EXPOENTE_CATEGORIA
        )

        resultado["categorias"].append({

            "categoria": categoria,

            "percentual": percentual,

            "classificacao": classificar(
                percentual
            )

        })

    return resultado