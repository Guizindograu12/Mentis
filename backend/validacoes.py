import re
from datetime import date, datetime


# ==========================================
# REGRAS DO CADASTRO
# ==========================================

IDADE_MINIMA = 14
IDADE_MAXIMA = 120

TAMANHO_MINIMO_SENHA = 8
TAMANHO_MAXIMO_SENHA = 128

TIPOS_CONTA = ("funcionario", "empresa_rh")

# Domínio obrigatório por tipo de conta.
# Funcionário NÃO tem domínio obrigatório: aceita qualquer e-mail válido.
# Empresa/RH continua exigindo @mentisrh.com (domínio interno do Mentis,
# não precisa existir de verdade).
DOMINIOS_EMAIL = {
    "empresa_rh": "mentisrh.com"
}

# Formato geral de e-mail: nome@dominio.com
PADRAO_EMAIL_GERAL = r"[a-z0-9._%+\-]+@[a-z0-9\-]+(\.[a-z0-9\-]+)+"


# ==========================================
# FUNÇÕES AUXILIARES
# ==========================================

def email_valido(email, tipo_conta):
    """
    Confere se o e-mail tem um formato válido para o tipo de conta.

    - Empresa/RH: precisa ser nome@mentisrh.com
    - Funcionário: qualquer e-mail no formato nome@dominio.com

    O e-mail já deve vir em minúsculas.
    """

    dominio = DOMINIOS_EMAIL.get(tipo_conta)

    if dominio is not None:
        padrao = r"[a-z0-9._%+\-]+@" + re.escape(dominio)
    else:
        padrao = PADRAO_EMAIL_GERAL

    return re.fullmatch(padrao, email) is not None


def calcular_idade(nascimento, hoje=None):
    """
    Calcula a idade em anos completos.
    """

    if hoje is None:
        hoje = date.today()

    idade = hoje.year - nascimento.year

    ainda_nao_fez_aniversario = (
        (hoje.month, hoje.day) < (nascimento.month, nascimento.day)
    )

    if ainda_nao_fez_aniversario:
        idade -= 1

    return idade


def limpar_cnpj(valor):
    """
    Deixa só os números: 11.222.333/0001-81 -> 11222333000181
    """

    return re.sub(r"\D", "", valor or "")


def _digito_cnpj(base):

    if len(base) == 12:
        pesos = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    else:
        pesos = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    soma = sum(
        int(numero) * peso
        for numero, peso in zip(base, pesos)
    )

    resto = soma % 11

    return 0 if resto < 2 else 11 - resto


def cnpj_valido(cnpj):
    """
    Valida o CNPJ (14 números + dígitos verificadores).
    Recebe apenas números.
    """

    if len(cnpj) != 14 or not cnpj.isdigit():
        return False

    # Rejeita 00000000000000, 11111111111111, etc.
    if cnpj == cnpj[0] * 14:
        return False

    digito1 = _digito_cnpj(cnpj[:12])
    digito2 = _digito_cnpj(cnpj[:12] + str(digito1))

    return cnpj[12:] == f"{digito1}{digito2}"


# ==========================================
# VALIDAÇÃO COMPLETA DO CADASTRO
# ==========================================

def validar_cadastro(tipo_conta, form):
    """
    Valida os dados do formulário de cadastro.

    Retorna (dados, erro):
    - se estiver tudo certo: (dicionário com os dados limpos, None)
    - se houver problema:     (None, mensagem de erro)
    """

    email = form.get("email", "").strip().lower()
    senha = form.get("senha", "")
    confirmar_senha = form.get("confirmar_senha", "")

    empresa = form.get("empresa", "").strip()

    nome = None
    sobrenome = None
    data_nascimento = None
    cnpj = None

    # ------------------------------------------
    # CAMPOS ESPECÍFICOS DE CADA TIPO
    # ------------------------------------------

    if tipo_conta == "funcionario":

        nome = form.get("nome", "").strip()
        sobrenome = form.get("sobrenome", "").strip()
        data_texto = form.get("data_nascimento", "").strip()

        if not all([
            nome,
            sobrenome,
            empresa,
            data_texto,
            email,
            senha,
            confirmar_senha
        ]):
            return None, "Preencha todos os campos."

        if len(nome) > 100 or len(sobrenome) > 100:
            return None, "Nome e sobrenome podem ter no máximo 100 caracteres."

        if len(empresa) > 200:
            return None, "O nome da empresa pode ter no máximo 200 caracteres."

        try:
            data_nascimento = datetime.strptime(
                data_texto,
                "%Y-%m-%d"
            ).date()

        except ValueError:
            return None, "Informe uma data de nascimento válida."

        idade = calcular_idade(data_nascimento)

        if idade < 0 or idade > IDADE_MAXIMA:
            return None, "Informe uma data de nascimento válida."

        if idade < IDADE_MINIMA:
            return None, (
                f"Você precisa ter pelo menos {IDADE_MINIMA} anos "
                "para se cadastrar."
            )

    else:

        cnpj = limpar_cnpj(form.get("cnpj", ""))

        if not all([
            empresa,
            cnpj,
            email,
            senha,
            confirmar_senha
        ]):
            return None, "Preencha todos os campos."

        if len(empresa) > 200:
            return None, "O nome da empresa pode ter no máximo 200 caracteres."

        if not cnpj_valido(cnpj):
            return None, "Informe um CNPJ válido."

    # ------------------------------------------
    # E-MAIL E SENHA (iguais para os dois tipos)
    # ------------------------------------------

    if not email_valido(email, tipo_conta):

        if tipo_conta in DOMINIOS_EMAIL:

            return None, (
                f"O e-mail precisa terminar com @{DOMINIOS_EMAIL[tipo_conta]}."
            )

        return None, "Informe um e-mail válido."

    if len(email) > 320:
        return None, "O e-mail é muito longo."

    if len(senha) < TAMANHO_MINIMO_SENHA:

        return None, (
            f"A senha precisa ter pelo menos {TAMANHO_MINIMO_SENHA} caracteres."
        )

    if len(senha) > TAMANHO_MAXIMO_SENHA:

        return None, (
            f"A senha pode ter no máximo {TAMANHO_MAXIMO_SENHA} caracteres."
        )

    if senha != confirmar_senha:
        return None, "As senhas não são iguais."

    # ------------------------------------------
    # TUDO CERTO
    # ------------------------------------------

    return {
        "email": email,
        "senha": senha,
        "tipo_conta": tipo_conta,
        "nome": nome,
        "sobrenome": sobrenome,
        "empresa": empresa,
        "data_nascimento": data_nascimento,
        "cnpj": cnpj
    }, None