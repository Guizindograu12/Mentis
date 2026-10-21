document.addEventListener("DOMContentLoaded", function () {
    const botaoImprimir = document.getElementById("botaoImprimir");

    if (botaoImprimir) {
        botaoImprimir.addEventListener("click", function () {
            window.print();
        });
    }

    // Verifica a preferência por movimento reduzido
    const movimentoReduzido = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    ).matches;

    // ANIMAÇÃO DO CÍRCULO PRINCIPAL
    const medidor = document.querySelector(".medidor");
    const valor = document.querySelector(".medidor-valor");

    if (medidor && valor) {
        const percentualOriginal = getComputedStyle(medidor)
            .getPropertyValue("--percentual")
            .trim();

        let percentualFinal = parseFloat(percentualOriginal);

        if (Number.isFinite(percentualFinal)) {
            percentualFinal = Math.min(100, Math.max(0, percentualFinal));

            const textoFinal = Math.round(percentualFinal) + "%";
            const duracao = 1400;

            function aplicarPercentual(percentual) {
                const graus = percentual * 3.6;

                medidor.style.background = `conic-gradient(
                    var(--azul) 0deg ${graus}deg,
                    #d8dfe4 ${graus}deg 360deg
                )`;

                valor.textContent = Math.round(percentual) + "%";
            }

            if (movimentoReduzido) {
                aplicarPercentual(percentualFinal);
                valor.textContent = textoFinal;
            } else {
                let inicio = null;

                aplicarPercentual(0);

                function animar(tempoAtual) {
                    if (inicio === null) inicio = tempoAtual;

                    const progresso = Math.min(
                        (tempoAtual - inicio) / duracao,
                        1
                    );

                    const suavizado = 1 - Math.pow(1 - progresso, 3);
                    const atual = percentualFinal * suavizado;

                    aplicarPercentual(atual);

                    if (progresso < 1) {
                        requestAnimationFrame(animar);
                    } else {
                        valor.textContent = textoFinal;
                    }
                }

                requestAnimationFrame(animar);
            }
        }
    }

    // ANIMAÇÃO DOS PERCENTUAIS DAS CATEGORIAS
    const percentuaisCategorias = document.querySelectorAll(
        ".percentual-categoria"
    );

    percentuaisCategorias.forEach(function (elemento) {
        const percentualFinal = Number(elemento.dataset.percentual);

        if (!Number.isFinite(percentualFinal)) return;

        const textoFinal =
            percentualFinal.toFixed(2).replace(".", ",") + "%";

        if (movimentoReduzido) {
            elemento.textContent = textoFinal;
            return;
        }

        const duracao = 1400;
        const inicioAnimacao = performance.now();

        elemento.textContent = "0,00%";

        function contar(tempoAtual) {
            const progresso = Math.min(
                (tempoAtual - inicioAnimacao) / duracao,
                1
            );

            const suavizado = 1 - Math.pow(1 - progresso, 3);
            const atual = percentualFinal * suavizado;

            elemento.textContent =
                atual.toFixed(2).replace(".", ",") + "%";

            if (progresso < 1) {
                requestAnimationFrame(contar);
            } else {
                elemento.textContent = textoFinal;
            }
        }

        requestAnimationFrame(contar);
    });
});
