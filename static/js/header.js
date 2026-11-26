(function () {
    "use strict";

    // =========================================
    // CONFIGURAÇÕES PADRÃO
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
    const LARGURA_MOBILE = 800;

    // =========================================
    // CARREGAR CONFIGURAÇÕES SALVAS
    // =========================================

    Object.keys(CONFIG).forEach(function (chave) {
        let valor = CONFIG[chave].padrao;

        try {
            const salvo = localStorage.getItem("mentis-" + chave);

            if (salvo && CONFIG[chave].valores.includes(salvo)) {
                valor = salvo;
            }
        } catch (erro) {
            // Continua com a configuração padrão.
        }

        html.setAttribute("data-" + chave, valor);
    });

    atualizarContraste();

    function atualizarContraste() {
        html.setAttribute(
            "data-contraste",
            html.getAttribute("data-tema") === "alto-contraste"
                ? "alto"
                : "normal"
        );
    }

    // =========================================
    // INICIALIZAÇÃO
    // =========================================

    document.addEventListener("DOMContentLoaded", function () {
        prepararPaineisMobile();
        inicializarMenu();
        inicializarPainelConta();
        inicializarPaineisSecundarios();
        inicializarConfiguracoes();
        inicializarPrivacidade();
    });

    // =========================================
    // ELEMENTOS DO MENU
    // =========================================

    function obterElementosMenu() {
        return {
            botao: document.getElementById("menu-toggle"),
            fechar: document.getElementById("menu-close"),
            menu: document.getElementById("menu-principal"),
            overlay: document.getElementById("menu-overlay")
        };
    }

    // =========================================
    // ABRIR E FECHAR MENU
    // =========================================

    function abrirMenu() {
        const elementos = obterElementosMenu();

        if (!elementos.menu || !elementos.overlay) return;

        fecharPainelConta();

        elementos.menu.classList.add("menu-aberto");
        elementos.overlay.classList.add("overlay-visivel");

        if (elementos.botao) {
            elementos.botao.setAttribute("aria-expanded", "true");
            elementos.botao.setAttribute("aria-label", "Fechar menu");
        }

        document.body.classList.add("menu-bloqueado");
    }

    function fecharMenu() {
        const elementos = obterElementosMenu();

        if (elementos.menu) {
            elementos.menu.classList.remove("menu-aberto");
        }

        if (elementos.overlay) {
            elementos.overlay.classList.remove("overlay-visivel");
        }

        if (elementos.botao) {
            elementos.botao.setAttribute("aria-expanded", "false");
            elementos.botao.setAttribute("aria-label", "Abrir menu");
        }

        document.body.classList.remove("menu-bloqueado");
    }

    function inicializarMenu() {
        const elementos = obterElementosMenu();

        if (!elementos.menu) return;

        if (elementos.botao) {
            elementos.botao.addEventListener("click", function () {
                if (elementos.menu.classList.contains("menu-aberto")) {
                    fecharMenu();
                } else {
                    abrirMenu();
                }
            });
        }

        if (elementos.fechar) {
            elementos.fechar.addEventListener("click", fecharMenu);
        }

        if (elementos.overlay) {
            elementos.overlay.addEventListener("click", fecharMenu);
        }

        elementos.menu.addEventListener("click", function (evento) {
            const link = evento.target.closest("a");

            if (link) {
                fecharMenu();
            }
        });

        document.addEventListener("keydown", function (evento) {
            if (evento.key === "Escape") {
                fecharMenu();
                fecharPainelConta();
                fecharPaineisSecundarios();
            }
        });

        window.addEventListener("resize", function () {
            prepararPaineisMobile();

            if (window.innerWidth > LARGURA_MOBILE) {
                fecharMenu();
            }
        });
    }

    // =========================================
    // MOVER PAINÉIS PARA A SIDEBAR NO MOBILE
    // =========================================

    const locaisOriginais = new Map();

    function prepararPaineisMobile() {
        const menu = document.getElementById("menu-principal");

        if (!menu) return;

        const paineis = [
            document.getElementById("painel-config"),
            document.getElementById("painel-privacidade")
        ].filter(Boolean);

        // Guarda a posição original de cada painel.
        paineis.forEach(function (painel) {
            if (!locaisOriginais.has(painel)) {
                locaisOriginais.set(painel, {
                    pai: painel.parentNode,
                    proximo: painel.nextSibling
                });
            }
        });

        if (window.innerWidth <= LARGURA_MOBILE) {
            paineis.forEach(function (painel) {
                if (painel.parentNode !== menu) {
                    menu.appendChild(painel);
                }
            });

            return;
        }

        // No desktop, restaura de trás para frente
        // para preservar a ordem original dos elementos.
        paineis.slice().reverse().forEach(function (painel) {
            const local = locaisOriginais.get(painel);

            if (!local || !local.pai) return;

            if (painel.parentNode !== local.pai) {
                if (
                    local.proximo &&
                    local.proximo.parentNode === local.pai
                ) {
                    local.pai.insertBefore(painel, local.proximo);
                } else {
                    local.pai.appendChild(painel);
                }
            }

            painel.classList.remove("conta-aberta");
            painel.setAttribute("aria-hidden", "true");
        });

        menu.classList.remove("menu-painel-secundario");
    }

    // =========================================
    // PAINEL DA CONTA — DESKTOP
    // =========================================

    function inicializarPainelConta() {
        const botao = document.getElementById("btn-conta");
        const painel = document.getElementById("painel-conta");
        const overlay = document.getElementById("conta-overlay");
        const botaoFechar = document.getElementById("conta-fechar");

        if (!painel || !overlay) return;

        if (botao) {
            botao.addEventListener("click", function () {
                if (painel.classList.contains("conta-aberta")) {
                    fecharPainelConta();
                } else {
                    abrirPainelConta();
                }
            });
        }

        if (botaoFechar) {
            botaoFechar.addEventListener("click", fecharPainelConta);
        }

        overlay.addEventListener("click", fecharPainelConta);
    }

    function abrirPainelConta() {
        const painel = document.getElementById("painel-conta");
        const overlay = document.getElementById("conta-overlay");
        const botao = document.getElementById("btn-conta");

        if (!painel || !overlay) return;

        fecharMenu();
        fecharPaineisSecundarios();

        painel.classList.add("conta-aberta");
        painel.setAttribute("aria-hidden", "false");

        overlay.classList.add("conta-overlay-visivel");

        if (botao) {
            botao.setAttribute("aria-expanded", "true");
        }

        document.body.classList.add("conta-bloqueado");
    }

    function fecharPainelConta() {
        const painel = document.getElementById("painel-conta");
        const overlay = document.getElementById("conta-overlay");
        const botao = document.getElementById("btn-conta");

        if (painel) {
            painel.classList.remove("conta-aberta");
            painel.setAttribute("aria-hidden", "true");
        }

        if (overlay) {
            overlay.classList.remove("conta-overlay-visivel");
        }

        if (botao) {
            botao.setAttribute("aria-expanded", "false");
        }

        document.body.classList.remove("conta-bloqueado");
    }

    // =========================================
    // PAINÉIS DE CONFIGURAÇÕES E PRIVACIDADE
    // =========================================

    function obterPaineisSecundarios() {
        return [
            {
                seletores: ".abrir-config",
                painel: document.getElementById("painel-config"),
                voltar: document.getElementById("config-voltar"),
                fechar: document.getElementById("config-fechar")
            },
            {
                seletores: ".abrir-privacidade",
                painel: document.getElementById("painel-privacidade"),
                voltar: document.getElementById("privacidade-voltar"),
                fechar: document.getElementById("privacidade-fechar")
            }
        ].map(function (item) {
            item.aberturas = Array.from(
                document.querySelectorAll(item.seletores)
            );

            return item;
        }).filter(function (item) {
            return item.aberturas.length > 0 && item.painel;
        });
    }

    function inicializarPaineisSecundarios() {
        obterPaineisSecundarios().forEach(function (item) {

            item.aberturas.forEach(function (botao) {
                botao.addEventListener("click", function () {
                    const mobile = window.innerWidth <= LARGURA_MOBILE;
                    const menu = document.getElementById("menu-principal");

                    fecharPaineisSecundarios();

                    if (!mobile) {
                        fecharMenu();
                    }

                    item.painel.classList.add("conta-aberta");
                    item.painel.setAttribute("aria-hidden", "false");

                    if (mobile && menu) {
                        menu.classList.add("menu-painel-secundario");
                        menu.classList.add("menu-aberto");

                        const overlay = document.getElementById("menu-overlay");

                        if (overlay) {
                            overlay.classList.add("overlay-visivel");
                        }

                        document.body.classList.add("menu-bloqueado");
                    }

                    item.aberturas.forEach(function (abertura) {
                        abertura.setAttribute("aria-expanded", "true");
                    });

                    if (item.voltar) {
                        item.voltar.focus();
                    }
                });
            });

            if (item.voltar) {
                item.voltar.addEventListener("click", function () {
                    fecharPainelSecundario(item);

                    if (window.innerWidth <= LARGURA_MOBILE) {
                        const menu = document.getElementById("menu-principal");

                        if (menu) {
                            menu.classList.remove("menu-painel-secundario");
                        }

                        // Retorna à navegação da mesma sidebar.
                        abrirMenu();
                    } else {
                        abrirPainelConta();
                    }
                });
            }

            if (item.fechar) {
                item.fechar.addEventListener("click", function () {
                    fecharPainelSecundario(item);

                    if (window.innerWidth <= LARGURA_MOBILE) {
                        fecharMenu();
                    } else {
                        fecharPainelConta();
                    }
                });
            }
        });
    }

    function fecharPainelSecundario(item) {
        if (!item || !item.painel) return;

        item.painel.classList.remove("conta-aberta");
        item.painel.setAttribute("aria-hidden", "true");

        item.aberturas.forEach(function (botao) {
            botao.setAttribute("aria-expanded", "false");
        });

        item.painel.dispatchEvent(new CustomEvent("painel-fechado"));
    }

    function fecharPaineisSecundarios() {
        obterPaineisSecundarios().forEach(function (item) {
            if (item.painel.classList.contains("conta-aberta")) {
                fecharPainelSecundario(item);
            }
        });

        const menu = document.getElementById("menu-principal");

        if (menu) {
            menu.classList.remove("menu-painel-secundario");
        }
    }

    // =========================================
    // ACESSIBILIDADE
    // =========================================

    function inicializarConfiguracoes() {

        function valorAtual(chave) {
            return html.getAttribute("data-" + chave) ||
                CONFIG[chave].padrao;
        }

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

        function definir(chave, valor) {
            if (
                !CONFIG[chave] ||
                !CONFIG[chave].valores.includes(valor)
            ) {
                return;
            }

            html.setAttribute("data-" + chave, valor);

            if (chave === "tema") {
                atualizarContraste();
            }

            try {
                localStorage.setItem("mentis-" + chave, valor);
            } catch (erro) {
                // A configuração continua aplicada nesta sessão.
            }

            atualizarPainel();
        }

        document.querySelectorAll("[data-config][data-valor]")
            .forEach(function (botao) {

                botao.addEventListener("click", function () {
                    definir(
                        botao.dataset.config,
                        botao.dataset.valor
                    );
                });
            });

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

        const restaurar = document.getElementById("config-restaurar");

        if (restaurar) {
            restaurar.addEventListener("click", function () {
                Object.keys(CONFIG).forEach(function (chave) {
                    definir(chave, CONFIG[chave].padrao);
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

        function mostrarMensagem(elemento, texto, tipo) {
            if (!elemento) return;

            elemento.textContent = texto;
            elemento.className = "priv-mensagem priv-" + tipo;
        }

        function limparMensagem(elemento) {
            if (!elemento) return;

            elemento.textContent = "";
            elemento.className = "priv-mensagem";
        }

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
                } catch (erro) {
                    // Resposta sem JSON.
                }

                return {
                    ok: resposta.ok && corpo.status === "sucesso",
                    dados: corpo
                };

            } catch (erro) {
                return {
                    ok: false,
                    dados: {
                        mensagem:
                            "Não foi possível conectar ao servidor. Tente novamente."
                    }
                };
            }
        }

        // ALTERAR SENHA

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

            const botao = formSenha.querySelector("button[type='submit']");

            if (botao) {
                botao.disabled = true;
            }

            const resultado = await enviar(formSenha.dataset.url, {
                senha_atual: senhaAtual,
                nova_senha: senhaNova,
                confirmar_senha: senhaConfirmar
            });

            if (botao) {
                botao.disabled = false;
            }

            if (resultado.ok) {
                formSenha.reset();

                mostrarMensagem(
                    msgSenha,
                    resultado.dados.mensagem ||
                        "Senha alterada com sucesso.",
                    "sucesso"
                );
            } else {
                mostrarMensagem(
                    msgSenha,
                    resultado.dados.mensagem ||
                        "Não foi possível alterar a senha.",
                    "erro"
                );
            }
        });

        // ABRIR FORMULÁRIO DE EXCLUSÃO

        botaoAbrirExclusao.addEventListener("click", function () {
            formExclusao.hidden = false;

            botaoAbrirExclusao.setAttribute(
                "aria-expanded",
                "true"
            );

            document.getElementById("senha-exclusao").focus();
        });

        // CANCELAR EXCLUSÃO

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

        // CONFIRMAR EXCLUSÃO

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

            const botao =
                formExclusao.querySelector("button[type='submit']");

            if (botao) {
                botao.disabled = true;
            }

            const resultado = await enviar(
                painel.dataset.urlExclusao,
                { senha: senha }
            );

            if (botao) {
                botao.disabled = false;
            }

            if (resultado.ok) {
                window.location.href =
                    resultado.dados.redirecionar || "/";
            } else {
                mostrarMensagem(
                    msgExclusao,
                    resultado.dados.mensagem ||
                        "Não foi possível excluir a conta.",
                    "erro"
                );
            }
        });

        // LIMPAR OS CAMPOS QUANDO O PAINEL FECHAR

        painel.addEventListener("painel-fechado", function () {
            formSenha.reset();
            limparMensagem(msgSenha);
            cancelarExclusao();
        });
    }

})();