
function trocarTela(telaDestino) {
    const telas = [
        document.getElementById("login-area"),
        document.getElementById("cadastro-area"),
        document.getElementById("recuperacao-area")
    ];

    const telaAtual = telas.find(tela =>
        tela && !tela.classList.contains("escondido")
    );

    if (!telaDestino || telaAtual === telaDestino) return;

    // Evita cliques durante a animação
    if (window.transicaoLoginAtiva) return;
    window.transicaoLoginAtiva = true;

    if (telaAtual) {
        telaAtual.classList.add("animando-saida");

        setTimeout(() => {
            telaAtual.classList.add("escondido");
            telaAtual.classList.remove("animando-saida");

            telaDestino.classList.remove("escondido");
            telaDestino.classList.add("animando-entrada");

            setTimeout(() => {
                telaDestino.classList.remove("animando-entrada");
                window.transicaoLoginAtiva = false;
            }, 400);

        }, 220);

    } else {
        telaDestino.classList.remove("escondido");
        telaDestino.classList.add("animando-entrada");

        setTimeout(() => {
            telaDestino.classList.remove("animando-entrada");
            window.transicaoLoginAtiva = false;
        }, 400);
    }
}

function mostrarLogin() {
    trocarTela(document.getElementById("login-area"));

    document.getElementById("titulo-alternativo").textContent =
        "Não possui uma conta?";

    document.getElementById("texto-alternativo").textContent =
        "Faça já o cadastro";

    const botao = document.querySelector(".account-button");
    botao.textContent = "Criar uma conta";
    botao.onclick = mostrarCadastro;
}

function mostrarCadastro() {
    trocarTela(document.getElementById("cadastro-area"));

    document.getElementById("titulo-alternativo").textContent =
        "Já possui uma conta?";

    document.getElementById("texto-alternativo").textContent =
        "Entre para continuar utilizando a Mentis.";

    const botao = document.querySelector(".account-button");
    botao.textContent = "Entrar em uma conta";
    botao.onclick = mostrarLogin;
}

function mostrarRecuperacao(event) {
    if (event) {
        event.preventDefault();
    }

    // Sempre começa na etapa 1 (pedir o código).
    if (typeof resetarRecuperacao === "function") {
        resetarRecuperacao();
    }

    trocarTela(document.getElementById("recuperacao-area"));

    document.getElementById("titulo-alternativo").textContent =
        "Esqueceu sua senha?";

    document.getElementById("texto-alternativo").textContent =
        "Recupere seu acesso à Mentis.";

    const botao = document.querySelector(".account-button");
    botao.textContent = "Voltar ao login";
    botao.onclick = mostrarLogin;
}


// ==========================================
// RECUPERAÇÃO DE SENHA (CÓDIGO POR E-MAIL)
// ==========================================

let emailRecuperacao = "";
let temporizadorReenvio = null;

const INTERVALO_REENVIO = 60;

function elemento(id) {
    return document.getElementById(id);
}

function mostrarErroRecuperacao(mensagem) {
    const caixa = elemento("recuperacao-erro");

    caixa.textContent = mensagem;
    caixa.hidden = false;

    elemento("recuperacao-info").hidden = true;
}

function mostrarInfoRecuperacao(mensagem) {
    const caixa = elemento("recuperacao-info");

    caixa.textContent = mensagem;
    caixa.hidden = false;

    elemento("recuperacao-erro").hidden = true;
}

function limparMensagensRecuperacao() {
    elemento("recuperacao-erro").hidden = true;
    elemento("recuperacao-info").hidden = true;
}

function resetarRecuperacao() {
    emailRecuperacao = "";

    if (temporizadorReenvio) {
        clearInterval(temporizadorReenvio);
        temporizadorReenvio = null;
    }

    limparMensagensRecuperacao();

    elemento("form-recuperacao-email").hidden = false;
    elemento("form-recuperacao-codigo").hidden = true;
    elemento("recuperacao-sucesso").hidden = true;

    elemento("recuperacao-email").value = "";
    elemento("recuperacao-codigo").value = "";
    elemento("recuperacao-nova-senha").value = "";
    elemento("recuperacao-confirmar-senha").value = "";

    elemento("recuperacao-instrucao").textContent =
        "Digite seu e-mail para receber um código de verificação.";

    elemento("botao-enviar-codigo").disabled = false;
    elemento("botao-redefinir").disabled = false;

    const reenviar = elemento("botao-reenviar-codigo");
    reenviar.disabled = false;
    reenviar.textContent = "Reenviar código";
}

async function postarJSON(url, dados) {
    const resposta = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(dados)
    });

    let corpo = {};

    try {
        corpo = await resposta.json();
    } catch (erro) {
        corpo = {};
    }

    return {
        ok: resposta.ok,
        corpo: corpo
    };
}

function iniciarContagemReenvio() {
    const botao = elemento("botao-reenviar-codigo");

    let restante = INTERVALO_REENVIO;

    if (temporizadorReenvio) {
        clearInterval(temporizadorReenvio);
    }

    botao.disabled = true;
    botao.textContent = "Reenviar código (" + restante + "s)";

    temporizadorReenvio = setInterval(() => {
        restante -= 1;

        if (restante <= 0) {
            clearInterval(temporizadorReenvio);
            temporizadorReenvio = null;

            botao.disabled = false;
            botao.textContent = "Reenviar código";

            return;
        }

        botao.textContent = "Reenviar código (" + restante + "s)";
    }, 1000);
}

async function pedirCodigo(email) {
    const resultado = await postarJSON(
        "/recuperar-senha/enviar-codigo",
        { email: email }
    );

    return resultado;
}

function configurarRecuperacao() {
    const formEmail = elemento("form-recuperacao-email");
    const formCodigo = elemento("form-recuperacao-codigo");

    if (!formEmail || !formCodigo) return;

    // ETAPA 1: pedir o código
    formEmail.addEventListener("submit", async function (evento) {
        evento.preventDefault();

        const email = elemento("recuperacao-email").value.trim().toLowerCase();

        if (!email || email.indexOf("@") === -1) {
            mostrarErroRecuperacao("Digite um e-mail válido.");
            return;
        }

        const botao = elemento("botao-enviar-codigo");
        botao.disabled = true;

        try {
            const resultado = await pedirCodigo(email);

            if (!resultado.ok) {
                mostrarErroRecuperacao(
                    resultado.corpo.mensagem ||
                    "Não foi possível enviar o código."
                );
                botao.disabled = false;
                return;
            }

            emailRecuperacao = email;

            formEmail.hidden = true;
            formCodigo.hidden = false;

            elemento("recuperacao-instrucao").textContent =
                "Digite o código enviado para " + email +
                " e escolha a nova senha.";

            mostrarInfoRecuperacao(resultado.corpo.mensagem);

            iniciarContagemReenvio();

            elemento("recuperacao-codigo").focus();

        } catch (erro) {
            mostrarErroRecuperacao(
                "Sem conexão com o servidor. Tente novamente."
            );
        }

        botao.disabled = false;
    });

    // ETAPA 2: conferir o código e trocar a senha
    formCodigo.addEventListener("submit", async function (evento) {
        evento.preventDefault();

        const codigo = elemento("recuperacao-codigo").value.trim();
        const novaSenha = elemento("recuperacao-nova-senha").value;
        const confirmarSenha = elemento("recuperacao-confirmar-senha").value;

        if (!/^[0-9]{6}$/.test(codigo)) {
            mostrarErroRecuperacao("O código tem 6 números.");
            return;
        }

        if (novaSenha.length < 8) {
            mostrarErroRecuperacao(
                "A senha precisa ter pelo menos 8 caracteres."
            );
            return;
        }

        if (novaSenha !== confirmarSenha) {
            mostrarErroRecuperacao("As senhas não são iguais.");
            return;
        }

        const botao = elemento("botao-redefinir");
        botao.disabled = true;

        try {
            const resultado = await postarJSON(
                "/recuperar-senha/redefinir",
                {
                    email: emailRecuperacao,
                    codigo: codigo,
                    nova_senha: novaSenha,
                    confirmar_senha: confirmarSenha
                }
            );

            if (!resultado.ok) {
                mostrarErroRecuperacao(
                    resultado.corpo.mensagem ||
                    "Não foi possível alterar a senha."
                );
                botao.disabled = false;
                return;
            }

            limparMensagensRecuperacao();

            formCodigo.hidden = true;

            elemento("recuperacao-instrucao").textContent = "";

            elemento("recuperacao-sucesso-texto").textContent =
                resultado.corpo.mensagem ||
                "Senha alterada! Agora você pode voltar ao login.";

            elemento("recuperacao-sucesso").hidden = false;

            if (temporizadorReenvio) {
                clearInterval(temporizadorReenvio);
                temporizadorReenvio = null;
            }

        } catch (erro) {
            mostrarErroRecuperacao(
                "Sem conexão com o servidor. Tente novamente."
            );
            botao.disabled = false;
        }
    });

    // Reenviar o código
    elemento("botao-reenviar-codigo").addEventListener(
        "click",
        async function () {
            if (!emailRecuperacao) return;

            elemento("botao-reenviar-codigo").disabled = true;

            try {
                const resultado = await pedirCodigo(emailRecuperacao);

                if (!resultado.ok) {
                    mostrarErroRecuperacao(
                        resultado.corpo.mensagem ||
                        "Não foi possível reenviar o código."
                    );
                    elemento("botao-reenviar-codigo").disabled = false;
                    return;
                }

                mostrarInfoRecuperacao(
                    "Pedimos um novo código. " + resultado.corpo.mensagem
                );

                iniciarContagemReenvio();

            } catch (erro) {
                mostrarErroRecuperacao(
                    "Sem conexão com o servidor. Tente novamente."
                );
                elemento("botao-reenviar-codigo").disabled = false;
            }
        }
    );

    // O campo do código só aceita números
    elemento("recuperacao-codigo").addEventListener("input", function () {
        this.value = this.value.replace(/[^0-9]/g, "").slice(0, 6);
    });
}

document.addEventListener("DOMContentLoaded", function () {
    configurarRecuperacao();

    const modoRecuperacao =
        document.body.dataset.recoveryMode === "true";

    if (modoRecuperacao) {
        mostrarRecuperacao();
    }
});