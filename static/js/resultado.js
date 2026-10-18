
document.addEventListener("DOMContentLoaded", function () {
    const botaoImprimir = document.getElementById("botaoImprimir");

    if (botaoImprimir) {
        botaoImprimir.addEventListener("click", function () {
            window.print();
        });
    }

    // Animação do medidor de resultado
    const medidor = document.querySelector(".medidor");
    const valor = document.querySelector(".medidor-valor");

    if (!medidor || !valor) return;

    // Obtém a porcentagem calculada pelo Flask
    const percentualOriginal = getComputedStyle(medidor)
        .getPropertyValue("--percentual")
        .trim();

    let percentualFinal = parseFloat(percentualOriginal);

    if (!Number.isFinite(percentualFinal)) return;

    // Garante que o valor fique entre 0% e 100%
    percentualFinal = Math.min(100, Math.max(0, percentualFinal));

    // Guarda o texto final e prepara o círculo para a animação
    const textoFinal = Math.round(percentualFinal);
    const duracao = 1400;
    let inicio = null;

    medidor.style.background = `conic-gradient(
        var(--azul) 0deg,
        #d8dfe4 0deg 360deg
    )`;

    valor.textContent = "0%";

    function animar(tempoAtual) {
        if (inicio === null) inicio = tempoAtual;

        const progresso = Math.min((tempoAtual - inicio) / duracao, 1);

        // Suaviza a animação no início e no final
        const suavizado = 1 - Math.pow(1 - progresso, 3);

        const percentualAtual = percentualFinal * suavizado;
        const graus = percentualAtual * 3.6;

        medidor.style.background = `conic-gradient(
            var(--azul) 0deg ${graus}deg,
            #d8dfe4 ${graus}deg 360deg
        )`;

        valor.textContent = `${Math.round(percentualAtual)}%`;

        if (progresso < 1) {
            requestAnimationFrame(animar);
        } else {
            valor.textContent = `${textoFinal}%`;
        }
    }

    // Respeita a preferência por movimento reduzido
    const movimentoReduzido = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    ).matches;

    if (movimentoReduzido) {
        medidor.style.background = `conic-gradient(
            var(--azul) 0deg ${percentualFinal * 3.6}deg,
            #d8dfe4 ${percentualFinal * 3.6}deg 360deg
        )`;
        valor.textContent = `${textoFinal}%`;
    } else {
        requestAnimationFrame(animar);
    }
});
