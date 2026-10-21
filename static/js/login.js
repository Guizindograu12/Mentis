
function mostrarLogin() {
    document.getElementById("cadastro-area").classList.add("escondido");
    document.getElementById("recuperacao-area").classList.add("escondido");
    document.getElementById("login-area").classList.remove("escondido");

    document.getElementById("titulo-alternativo").textContent =
        "Não possui uma conta?";

    document.getElementById("texto-alternativo").textContent =
        "Faça já o cadastro";

    const botao = document.querySelector(".account-button");
    botao.textContent = "Criar uma conta";
    botao.onclick = mostrarCadastro;
}

function mostrarCadastro() {
    document.getElementById("login-area").classList.add("escondido");
    document.getElementById("recuperacao-area").classList.add("escondido");
    document.getElementById("cadastro-area").classList.remove("escondido");

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

    document.getElementById("cadastro-area").classList.add("escondido");
    document.getElementById("login-area").classList.add("escondido");
    document.getElementById("recuperacao-area").classList.remove("escondido");

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

