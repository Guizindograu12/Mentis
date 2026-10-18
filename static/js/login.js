function mostrarLogin() {
    document.getElementById("cadastro-area").classList.add("escondido");
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
    document.getElementById("cadastro-area").classList.remove("escondido");

    document.getElementById("titulo-alternativo").textContent =
        "Já possui uma conta?";

    document.getElementById("texto-alternativo").textContent =
        "Entre para continuar utilizando a Mentis.";

    const botao = document.querySelector(".account-button");
    botao.textContent = "Entrar em uma conta";
    botao.onclick = mostrarLogin;
}
