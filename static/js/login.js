
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

    trocarTela(document.getElementById("recuperacao-area"));

    document.getElementById("titulo-alternativo").textContent =
        "Esqueceu sua senha?";

    document.getElementById("texto-alternativo").textContent =
        "Recupere seu acesso à Mentis.";

    const botao = document.querySelector(".account-button");
    botao.textContent = "Voltar ao login";
    botao.onclick = mostrarLogin;
}

document.addEventListener("DOMContentLoaded", function () {
    const modoRecuperacao =
        document.body.dataset.recoveryMode === "true";

    if (modoRecuperacao) {
        mostrarRecuperacao();
    }
});
