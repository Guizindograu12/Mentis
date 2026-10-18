
document
    .getElementById("formulario")
    .addEventListener("submit", async function (e) {
        e.preventDefault();

        const formulario = this;
        const botao = document.getElementById("botaoEnviar");
        const mensagem = document.getElementById("mensagem");

        botao.disabled = true;
        mensagem.style.display = "block";
        mensagem.textContent = "Enviando suas respostas...";

        const respostas = {};
        const formData = new FormData(formulario);

        formData.forEach((valor, chave) => {
            respostas[chave] = valor;
        });

        try {
            const resposta = await fetch(URL_ANALISAR, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                body: JSON.stringify(respostas)
            });

            if (resposta.status === 401) {
                window.location.href = URL_LOGIN;
                return;
            }

            const tipo = resposta.headers.get("content-type") || "";

            if (!tipo.includes("application/json")) {
                console.error(
                    "Resposta inesperada do servidor:",
                    resposta.status,
                    resposta.url,
                    await resposta.text()
                );

                mensagem.textContent =
                    "O servidor não retornou o resultado esperado. Confira o terminal do Flask.";

                botao.disabled = false;
                return;
            }

            const resultado = await resposta.json();

            if (
                resposta.ok &&
                resultado.status === "sucesso" &&
                resultado.resultado_url
            ) {
                window.location.href = resultado.resultado_url;
                return;
            }

            mensagem.textContent =
                resultado.mensagem ||
                "Não foi possível processar as respostas.";

            botao.disabled = false;

        } catch (erro) {
            console.error("Erro ao enviar respostas:", erro);

            mensagem.textContent =
                "Erro na comunicação com o servidor. Confira o terminal do Flask.";

            botao.disabled = false;
        }
    });
