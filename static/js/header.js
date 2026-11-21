
(function () {

    "use strict";

    // =========================================
    // CONFIGURAÇÕES
    // =========================================


    const CONFIG = {
        fonte: {
            padrao: "normal",
            valores: ["normal", "grande", "muito-grande"]
        },

        tema: {
            padrao: "claro",
            valores: ["claro", "escuro", "alto-contraste"]
        },

        animacoes: {
            padrao: "normal",
            valores: ["normal", "reduzidas"]
        },

        dislexia: {
            padrao: "normal",
            valores: ["normal", "ligada"]
        }
    };


    window.MENTIS_CONFIG = CONFIG;

    const html = document.documentElement;

    // Carrega as configurações salvas.
    Object.keys(CONFIG).forEach(function (chave) {

        let valor = CONFIG[chave].padrao;

        try {

            const salvo = localStorage.getItem("mentis-" + chave);

            if (
                salvo &&
                CONFIG[chave].valores.includes(salvo)
            ) {
                valor = salvo;
            }

        } catch (erro) {}

        html.setAttribute("data-" + chave, valor);

    });
    
    // O alto contraste é um tema próprio,
    // não uma configuração independente.
    html.setAttribute(
        "data-contraste",
        html.getAttribute("data-tema") === "alto-contraste"
            ? "alto"
            : "normal"
    );

    // =========================================
    // INICIALIZAÇÃO
    // =========================================

    document.addEventListener("DOMContentLoaded", function () {

        inicializarMenu();
        inicializarPainelConta();
        inicializarPaineisSecundarios();
        inicializarConfiguracoes();
        inicializarPrivacidade();

    });


    // =========================================
    // MENU MOBILE
    // =========================================

    function inicializarMenu() {

        const botaoAbrir = document.getElementById("menu-toggle");
        const botaoFechar = document.getElementById("menu-close");
        const menu = document.getElementById("menu-principal");
        const overlay = document.getElementById("menu-overlay");

        if (!botaoAbrir || !botaoFechar || !menu || !overlay) {
            return;
        }

        function abrirMenu() {

            menu.classList.add("menu-aberto");
            overlay.classList.add("overlay-visivel");

            botaoAbrir.setAttribute("aria-expanded", "true");
            botaoAbrir.setAttribute("aria-label", "Fechar menu");

            document.body.classList.add("menu-bloqueado");

        }

        function fecharMenu() {

            menu.classList.remove("menu-aberto");
            overlay.classList.remove("overlay-visivel");

            botaoAbrir.setAttribute("aria-expanded", "false");
            botaoAbrir.setAttribute("aria-label", "Abrir menu");

            document.body.classList.remove("menu-bloqueado");

        }

        botaoAbrir.addEventListener("click", abrirMenu);

        botaoFechar.addEventListener("click", fecharMenu);

        overlay.addEventListener("click", fecharMenu);

        menu.querySelectorAll("a").forEach(function (link) {

            link.addEventListener("click", fecharMenu);

        });

        document.addEventListener("keydown", function (event) {

            if (event.key === "Escape") {
                fecharMenu();
            }

        });

        window.addEventListener("resize", function () {

            if (window.innerWidth > 800) {
                fecharMenu();
            }

        });

    }


    // =========================================
    // PAINEL DA CONTA
    // =========================================

    function inicializarPainelConta() {

        const botao = document.getElementById("btn-conta");
        const painel = document.getElementById("painel-conta");
        const overlay = document.getElementById("conta-overlay");
        const botaoFechar = document.getElementById("conta-fechar");

        if (!botao || !painel || !overlay || !botaoFechar) {
            return;
        }

        function abrirPainel() {

            painel.classList.add("conta-aberta");
            overlay.classList.add("conta-overlay-visivel");

            painel.setAttribute("aria-hidden", "false");
            botao.setAttribute("aria-expanded", "true");

            document.body.classList.add("conta-bloqueado");

            botaoFechar.focus();

        }

        function fecharPainel() {

            if (!painel.classList.contains("conta-aberta")) {
                return;
            }

            painel.classList.remove("conta-aberta");
            overlay.classList.remove("conta-overlay-visivel");

            painel.setAttribute("aria-hidden", "true");
            botao.setAttribute("aria-expanded", "false");

            document.body.classList.remove("conta-bloqueado");

            botao.focus();

        }

        botao.addEventListener("click", abrirPainel);

        botaoFechar.addEventListener("click", fecharPainel);

        overlay.addEventListener("click", fecharPainel);

        document.addEventListener("keydown", function (event) {

            if (event.key === "Escape") {
                fecharPainel();
            }

        });

    }


    // =========================================
    // PAINÉIS SECUNDÁRIOS
    // =========================================

    function inicializarPaineisSecundarios() {

        const overlay = document.getElementById("conta-overlay");
        const fecharConta = document.getElementById("conta-fechar");

        if (!overlay || !fecharConta) {
            return;
        }

        const paineis = [

            {
                abrir: "abrir-config",
                painel: "painel-config",
                voltar: "config-voltar",
                fechar: "config-fechar"
            },

            {
                abrir: "abrir-privacidade",
                painel: "painel-privacidade",
                voltar: "privacidade-voltar",
                fechar: "privacidade-fechar"
            }

        ].map(function (ids) {

            return {
                botaoAbrir: document.getElementById(ids.abrir),
                painel: document.getElementById(ids.painel),
                botaoVoltar: document.getElementById(ids.voltar),
                botaoFechar: document.getElementById(ids.fechar)
            };

        }).filter(function (item) {

            return (
                item.botaoAbrir &&
                item.painel &&
                item.botaoVoltar &&
                item.botaoFechar
            );

        });


        function abrir(item) {

            item.painel.classList.add("conta-aberta");

            item.painel.setAttribute("aria-hidden", "false");

            item.botaoAbrir.setAttribute("aria-expanded", "true");

            item.botaoVoltar.focus();

        }


        function fechar(item) {

            if (!item.painel.classList.contains("conta-aberta")) {
                return;
            }

            item.painel.classList.remove("conta-aberta");

            item.painel.setAttribute("aria-hidden", "true");

            item.botaoAbrir.setAttribute("aria-expanded", "false");

            item.painel.dispatchEvent(
                new CustomEvent("painel-fechado")
            );

        }


        paineis.forEach(function (item) {

            item.botaoAbrir.addEventListener("click", function () {

                abrir(item);

            });


            // Voltar para Minha conta.
            item.botaoVoltar.addEventListener("click", function () {

                fechar(item);

                item.botaoAbrir.focus();

            });


            // Fechar o painel secundário e o principal.
            item.botaoFechar.addEventListener("click", function () {

                fechar(item);

                fecharConta.click();

            });

        });


        // Fechar pelo fundo escuro.
        overlay.addEventListener("click", function () {

            paineis.forEach(fechar);

        });


        // Fechar com Escape.
        document.addEventListener("keydown", function (event) {

            if (event.key === "Escape") {

                paineis.forEach(fechar);

            }

        });

    }


    // =========================================
    // CONFIGURAÇÕES DE ACESSIBILIDADE
    // =========================================

    function inicializarConfiguracoes() {

        function valorAtual(chave) {

            return (
                html.getAttribute("data-" + chave) ||
                CONFIG[chave].padrao
            );

        }


        // Atualiza o estado visual dos controles.
        function atualizarPainel() {

            document.querySelectorAll("[data-config][data-valor]")
                .forEach(function (botao) {

                    botao.setAttribute(
                        "aria-pressed",

                        valorAtual(botao.dataset.config) === botao.dataset.valor
                            ? "true"
                            : "false"
                    );

                });


            document.querySelectorAll(".config-switch")
                .forEach(function (botao) {

                    botao.setAttribute(
                        "aria-checked",

                        valorAtual(botao.dataset.config) === botao.dataset.ligado
                            ? "true"
                            : "false"
                    );

                });

        }


        // Altera e salva uma configuração.
        function definir(chave, valor) {

            if (!CONFIG[chave]) {
                return;
            }

            if (!CONFIG[chave].valores.includes(valor)) {
                return;
            }

            html.setAttribute("data-" + chave, valor);

            // Sincroniza o contraste com o tema escolhido.
            if (chave === "tema") {

            html.setAttribute(
            "data-contraste",
            valor === "alto-contraste" ? "alto" : "normal"
            );

            }

            try {

                localStorage.setItem(
                    "mentis-" + chave,
                    valor
                );

            } catch (erro) {}

            atualizarPainel();

        }


        // Botões de escolha: fonte e tema.
        document.querySelectorAll("[data-config][data-valor]")
            .forEach(function (botao) {

                botao.addEventListener("click", function () {

                    definir(
                        botao.dataset.config,
                        botao.dataset.valor
                    );

                });

            });


        // Interruptores: contraste, animações e dislexia.
        document.querySelectorAll(".config-switch")
            .forEach(function (botao) {

                botao.addEventListener("click", function () {

                    const ligado =
                        valorAtual(botao.dataset.config) === botao.dataset.ligado;

                    definir(
                        botao.dataset.config,

                        ligado
                            ? botao.dataset.desligado
                            : botao.dataset.ligado
                    );

                });

            });


        // Restaurar configurações padrão.
        const restaurar = document.getElementById("config-restaurar");

        if (restaurar) {

            restaurar.addEventListener("click", function () {

                Object.keys(CONFIG).forEach(function (chave) {

                    definir(
                        chave,
                        CONFIG[chave].padrao
                    );

                });

            });

        }

        atualizarPainel();

    }


    // =========================================
    // PRIVACIDADE E SEGURANÇA
    // =========================================

    function inicializarPrivacidade() {

        const painel = document.getElementById("painel-privacidade");

        const formSenha = document.getElementById("form-senha");

        const formExclusao = document.getElementById("form-exclusao");

        const botaoAbrirExclusao =
            document.getElementById("abrir-exclusao");

        const botaoCancelarExclusao =
            document.getElementById("cancelar-exclusao");


        if (
            !painel ||
            !formSenha ||
            !formExclusao ||
            !botaoAbrirExclusao ||
            !botaoCancelarExclusao
        ) {
            return;
        }


        const msgSenha = document.getElementById("msg-senha");

        const msgExclusao = document.getElementById("msg-exclusao");


        // Mostra mensagens.
        function mostrarMensagem(elemento, texto, tipo) {

            elemento.textContent = texto;

            elemento.className = "priv-mensagem priv-" + tipo;

        }


        // Limpa mensagens.
        function limparMensagem(elemento) {

            elemento.textContent = "";

            elemento.className = "priv-mensagem";

        }


        // Envia informações para o Flask.
        async function enviar(url, dados) {

            try {

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

                } catch (erro) {}


                return {

                    ok: resposta.ok && corpo.status === "sucesso",

                    dados: corpo

                };

            } catch (erro) {

                return {

                    ok: false,

                    dados: {
                        mensagem: "Não foi possível conectar ao servidor. Tente novamente."
                    }

                };

            }

        }


        // =====================================
        // ALTERAR SENHA
        // =====================================

        formSenha.addEventListener("submit", async function (evento) {

            evento.preventDefault();


            const senhaAtual =
                document.getElementById("senha-atual").value;

            const senhaNova =
                document.getElementById("senha-nova").value;

            const senhaConfirmar =
                document.getElementById("senha-confirmar").value;


            if (!senhaAtual || !senhaNova || !senhaConfirmar) {

                mostrarMensagem(
                    msgSenha,
                    "Preencha todos os campos.",
                    "erro"
                );

                return;

            }


            if (senhaNova.length < 8) {

                mostrarMensagem(
                    msgSenha,
                    "A nova senha precisa ter pelo menos 8 caracteres.",
                    "erro"
                );

                return;

            }


            if (senhaNova !== senhaConfirmar) {

                mostrarMensagem(
                    msgSenha,
                    "As senhas novas não são iguais.",
                    "erro"
                );

                return;

            }


            const botao = formSenha.querySelector(
                "button[type='submit']"
            );

            botao.disabled = true;


            const resultado = await enviar(
                formSenha.dataset.url,

                {
                    senha_atual: senhaAtual,
                    nova_senha: senhaNova,
                    confirmar_senha: senhaConfirmar
                }
            );


            botao.disabled = false;


            if (resultado.ok) {

                formSenha.reset();

                mostrarMensagem(
                    msgSenha,
                    resultado.dados.mensagem || "Senha alterada com sucesso.",
                    "sucesso"
                );

            } else {

                mostrarMensagem(
                    msgSenha,
                    resultado.dados.mensagem || "Não foi possível alterar a senha.",
                    "erro"
                );

            }

        });


        // =====================================
        // EXCLUIR CONTA
        // =====================================

        botaoAbrirExclusao.addEventListener("click", function () {

            formExclusao.hidden = false;

            botaoAbrirExclusao.setAttribute(
                "aria-expanded",
                "true"
            );

            document.getElementById("senha-exclusao").focus();

        });


        // Cancelar exclusão.
        function cancelarExclusao() {

            formExclusao.reset();

            formExclusao.hidden = true;

            botaoAbrirExclusao.setAttribute(
                "aria-expanded",
                "false"
            );

            limparMensagem(msgExclusao);

        }


        botaoCancelarExclusao.addEventListener(
            "click",
            cancelarExclusao
        );


        // Confirmar exclusão.
        formExclusao.addEventListener("submit", async function (evento) {

            evento.preventDefault();


            const senha =
                document.getElementById("senha-exclusao").value;


            if (!senha) {

                mostrarMensagem(
                    msgExclusao,
                    "Digite sua senha para confirmar.",
                    "erro"
                );

                return;

            }


            const botao = formExclusao.querySelector(
                "button[type='submit']"
            );

            botao.disabled = true;


            const resultado = await enviar(
                painel.dataset.urlExclusao,

                {
                    senha: senha
                }
            );


            botao.disabled = false;


            if (resultado.ok) {

                window.location.href =
                    resultado.dados.redirecionar || "/";

            } else {

                mostrarMensagem(
                    msgExclusao,
                    resultado.dados.mensagem || "Não foi possível excluir a conta.",
                    "erro"
                );

            }

        });


        // Limpar os campos ao fechar o painel.
        painel.addEventListener("painel-fechado", function () {

            formSenha.reset();

            limparMensagem(msgSenha);

            cancelarExclusao();

        });

    }

})();
