document.addEventListener("DOMContentLoaded", function () {

    const perguntas = document.querySelectorAll(".faq-pergunta");

    perguntas.forEach(function (pergunta) {

        pergunta.addEventListener("click", function () {

            const respostaId = pergunta.getAttribute("aria-controls");
            const resposta = document.getElementById(respostaId);

            if (!resposta) {
                return;
            }

            const estavaAberta =
                pergunta.getAttribute("aria-expanded") === "true";

            // Fecha todas as outras perguntas.
            perguntas.forEach(function (outraPergunta) {

                const outroId = outraPergunta.getAttribute("aria-controls");
                const outraResposta = document.getElementById(outroId);

                outraPergunta.setAttribute("aria-expanded", "false");

                if (outraResposta) {
                    outraResposta.hidden = true;
                }

            });

            // Abre ou fecha a pergunta selecionada.
            if (!estavaAberta) {
                pergunta.setAttribute("aria-expanded", "true");
                resposta.hidden = false;
            }

        });

    });

});