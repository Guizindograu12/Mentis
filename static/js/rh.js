(function () {
    "use strict";

    // Tira acentos e maiúsculas para a busca não depender disso.
    function normalizar(texto) {

        return String(texto || "")
            .toLowerCase()
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "");
    }


    // ==========================================
    // BUSCA E FILTROS DAS TABELAS
    // ==========================================

    function iniciarLista(area) {

        var campoBusca = area.querySelector("[data-busca]");
        var filtros = area.querySelectorAll("[data-filtro]");
        var linhas = area.querySelectorAll("[data-linha]");
        var aviso = area.querySelector("[data-vazio]");
        var contador = area.querySelector("[data-contador]");

        function aplicar() {

            var termo = normalizar(campoBusca ? campoBusca.value : "").trim();
            var filtroAtual = "todos";

            filtros.forEach(function (filtro) {

                if (filtro.checked) {
                    filtroAtual = filtro.value;
                }
            });

            var visiveis = 0;

            linhas.forEach(function (linha) {

                var combinaBusca = (
                    !termo ||
                    normalizar(linha.getAttribute("data-nome")).indexOf(termo) !== -1
                );

                var combinaFiltro = (
                    filtroAtual === "todos" ||
                    linha.getAttribute("data-status") === filtroAtual
                );

                var mostrar = combinaBusca && combinaFiltro;

                linha.hidden = !mostrar;

                if (mostrar) {
                    visiveis += 1;
                }
            });

            if (aviso) {
                aviso.hidden = visiveis !== 0;
            }

            if (contador) {
                contador.textContent = visiveis + " de " + linhas.length;
            }
        }

        if (campoBusca) {
            campoBusca.addEventListener("input", aplicar);
        }

        filtros.forEach(function (filtro) {
            filtro.addEventListener("change", aplicar);
        });

        aplicar();
    }

    document.querySelectorAll("[data-lista]").forEach(iniciarLista);


    // ==========================================
    // CONFIGURAÇÕES: abre o painel da conta
    // e, em seguida, o painel de configurações
    // ==========================================

    document.querySelectorAll("[data-abrir-config]").forEach(function (link) {

        link.addEventListener("click", function (evento) {

            evento.preventDefault();

            var botaoConta = document.getElementById("btn-conta");

            if (!botaoConta) {
                return;
            }

            botaoConta.click();

            window.setTimeout(function () {

                var botaoConfig = document.getElementById("abrir-config");

                if (botaoConfig) {
                    botaoConfig.click();
                }

            }, 150);
        });
    });

})();