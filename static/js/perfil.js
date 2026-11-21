
document.addEventListener("DOMContentLoaded", function () {
    const dados = window.MENTIS_DASHBOARD || {
        testes: [],
        moods: [],
        mediaTestes: null,
        ultimoTeste: null
    };

    const testes = dados.testes || [];

    // ========================================
    // CHECK-IN EMOCIONAL
    // ========================================

    const botoesHumor = document.querySelectorAll(".mood-option");
    const feedback = document.getElementById("mood-feedback");

    botoesHumor.forEach(function (botao) {
        botao.addEventListener("click", async function () {
            const humor = Number(botao.dataset.mood);

            if (!Number.isFinite(humor)) {
                return;
            }

            botoesHumor.forEach(function (item) {
                item.classList.remove("selecionado");
            });

            botao.classList.add("selecionado");

            if (feedback) {
                feedback.textContent = "Registrando seu check-in...";
                feedback.classList.remove("error");
            }

            try {
                const resposta = await fetch("/checkin-humor", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        humor: humor
                    })
                });

                const textoResposta = await resposta.text();

                let resultado;

                try {
                    resultado = JSON.parse(textoResposta);
                } catch {
                    console.error(
                        "O servidor retornou uma resposta inválida:",
                        textoResposta
                    );

                    throw new Error(
                        "O servidor não retornou uma resposta válida. " +
                        "Verifique o terminal do Flask."
                    );
                }

                if (!resposta.ok) {
                    throw new Error(
                        resultado.mensagem ||
                        "Não foi possível salvar seu check-in."
                    );
                }

                if (feedback) {
                    feedback.textContent =
                        `Check-in registrado! Seu humor de hoje: ${humor}/10.`;
                }

                if (resultado.media_humor !== undefined) {
                    atualizarMediaHumor(resultado.media_humor);
                }

            } catch (erro) {
                if (feedback) {
                    feedback.textContent =
                        erro.message ||
                        "Não foi possível registrar o check-in.";

                    feedback.classList.add("error");
                }

                console.error("Erro no check-in:", erro);
            }
        });
    });

    function atualizarMediaHumor(media) {
        const cartoes = document.querySelectorAll(".stat-card");

        cartoes.forEach(function (cartao) {
            const titulo = cartao.querySelector("span");
            const valor = cartao.querySelector("strong");

            if (
                titulo &&
                valor &&
                titulo.textContent.trim() === "Avg. Mood"
            ) {
                valor.textContent = `${Number(media).toFixed(1)}/10`;
            }
        });
    }

    // ========================================
    // CONFIGURAÇÕES DOS GRÁFICOS
    // ========================================

    if (typeof Chart === "undefined") {
        console.error("A biblioteca Chart.js não foi carregada.");
        return;
    }

    Chart.defaults.font.family = "Arial, Helvetica, sans-serif";

    // Guarda os gráficos criados para atualizar suas cores.
    const graficos = [];

    // ========================================
    // IDENTIFICA O TEMA ATUAL
    // ========================================

    function obterCoresTema() {
    const tema = document.documentElement.dataset.tema;

    const escuro = tema === "escuro";
    const contraste = tema === "alto-contraste";

    return {
        texto: contraste
            ? "#ffffff"
            : escuro
                ? "#e5eaf2"
                : "#77788a",

        grade: contraste
            ? "#ffffff"
            : escuro
                ? "#52647c"
                : "#eeeeF5",

        tooltip: contraste
            ? "#000000"
            : escuro
                ? "#263449"
                : "#191970",

            barraAnterior: contraste
                ? "#67E8F9"
                : escuro
                    ? "#C4B5FD"
                    : "#B7A8ED",

            barraAtual: contraste
                ? "#FFFF00"
                : escuro
                    ? "#8B5CF6"
                    : "#5144A8",

            linha: contraste
                ? "#FFFF00"
                : escuro
                    ? "#C4B5FD"
                    : "#5144A8"
    };
}

    const coresIniciais = obterCoresTema();

    Chart.defaults.color = coresIniciais.texto;

    const opcoesComuns = {
        responsive: true,
        maintainAspectRatio: false,

        interaction: {
            intersect: false,
            mode: "index"
        },

        plugins: {
            legend: {
                display: false
            },

            tooltip: {
                backgroundColor: coresIniciais.tooltip,
                titleColor: "#ffffff",
                bodyColor: "#ffffff",
                padding: 12,
                cornerRadius: 8
            }
        },

        scales: {
            y: {
                min: 0,
                max: 100,

                ticks: {
                    stepSize: 20,
                    callback: function (valor) {
                        return valor + "%";
                    }
                },

                grid: {
                    color: coresIniciais.grade
                }
            },

            x: {
                grid: {
                    display: false
                }
            }
        }
    };

    // ========================================
    // GRÁFICO DE LINHA: EVOLUÇÃO
    // ========================================

    const graficoLinha = document.getElementById("trendChart");

    if (graficoLinha && testes.length > 0) {
        const grafico = new Chart(graficoLinha, {
            type: "line",

            data: {
                labels: testes.map(function (teste, indice) {
                    return teste.data_label || `Teste ${indice + 1}`;
                }),

                datasets: [{
                    label: "Resultado geral",

                    data: testes.map(function (teste) {
                        return Number(teste.percentual);
                    }),

                    borderColor: coresIniciais.linha,
                    backgroundColor: "transparent",
                    pointBackgroundColor: coresIniciais.linha,
                    pointBorderColor: "#ffffff",
                    pointBorderWidth: 3,

                    fill: false,
                    tension: 0.3,

                    pointRadius: 8,
                    pointHoverRadius: 11,
                    borderWidth: 5
                }]
            },

            options: opcoesComuns
        });

        graficos.push(grafico);
    }

    // ========================================
    // GRÁFICO DE COLUNAS: MÉDIA X ÚLTIMO TESTE
    // ========================================

    const graficoResumo = document.getElementById("summaryChart");

    if (graficoResumo && testes.length > 0) {
        const resultados = testes.map(function (teste) {
            return Number(teste.percentual);
        });

        const media =
            resultados.reduce(function (soma, valor) {
                return soma + valor;
            }, 0) / resultados.length;

        const ultimo = resultados[resultados.length - 1];

        const grafico = new Chart(graficoResumo, {
            type: "bar",

            data: {
                labels: [
                    "Média dos testes",
                    "Último teste"
                ],

                datasets: [{
                    data: [media, ultimo],

                    backgroundColor: [
                    coresIniciais.barraAnterior,
                    coresIniciais.barraAtual
                ],

                    borderRadius: 8,
                    maxBarThickness: 75
                }]
            },

            options: {
                ...opcoesComuns,

                scales: {
                    ...opcoesComuns.scales,

                    y: {
                        ...opcoesComuns.scales.y,
                        beginAtZero: true
                    }
                }
            }
        });

        graficos.push(grafico);
    }

    // ========================================
    // GRÁFICO POR CATEGORIA
    // ========================================

    const seletor = document.getElementById("category-select");
    const graficoCategoria = document.getElementById("categoryChart");
    const descricao = document.getElementById("category-description");

    if (graficoCategoria && testes.length > 0) {
        const testesAnteriores = testes.slice(0, -1);
        const testeMaisRecente = testes[testes.length - 1];

        // Reúne todas as categorias do histórico.
        const nomesCategorias = [
            ...new Set(
                testes.flatMap(function (teste) {
                    return (teste.categorias || []).map(
                        function (categoria) {
                            return categoria.nome;
                        }
                    );
                })
            )
        ];

        // O seletor não é mais necessário.
        if (seletor) {
            seletor.hidden = true;

            const label = document.querySelector(
                'label[for="category-select"]'
            );

            if (label) {
                label.hidden = true;
            }
        }

        if (nomesCategorias.length === 0) {
            graficoCategoria.hidden = true;

            if (descricao) {
                descricao.textContent =
                    "As categorias aparecerão aqui quando houver resultados disponíveis.";
            }

        } else {
            graficoCategoria.hidden = false;

            // Calcula a média dos testes anteriores.
            const mediasAnteriores = nomesCategorias.map(
                function (nome) {
                    const valoresAnteriores = testesAnteriores
                        .flatMap(function (teste) {
                            return (teste.categorias || [])
                                .filter(function (categoria) {
                                    return categoria.nome === nome;
                                })
                                .map(function (categoria) {
                                    return Number(categoria.percentual);
                                });
                        })
                        .filter(Number.isFinite);

                    if (valoresAnteriores.length === 0) {
                        return null;
                    }

                    const soma = valoresAnteriores.reduce(
                        function (total, valor) {
                            return total + valor;
                        },
                        0
                    );

                    return soma / valoresAnteriores.length;
                }
            );

            // Obtém os resultados do teste mais recente.
            const resultadosRecentes = nomesCategorias.map(
                function (nome) {
                    const categoria = (
                        testeMaisRecente.categorias || []
                    ).find(function (item) {
                        return item.nome === nome;
                    });

                    if (!categoria) {
                        return null;
                    }

                    const valor = Number(categoria.percentual);

                    return Number.isFinite(valor) ? valor : null;
                }
            );

            // Cria o gráfico de barras agrupadas.
            const grafico = new Chart(graficoCategoria, {
                type: "bar",

                data: {
                    labels: nomesCategorias,

                    datasets: [
                        {
                            label: "Média dos testes anteriores",
                            data: mediasAnteriores,
                            backgroundColor: coresIniciais.barraAnterior,
                            borderRadius: 7,
                            maxBarThickness: 32
                        },
                        {
                            label: "Último teste",
                            data: resultadosRecentes,
                            backgroundColor: coresIniciais.barraAtual,
                            borderRadius: 7,
                            maxBarThickness: 32
                        }
                    ]
                },

                options: {
                    ...opcoesComuns,

                    interaction: {
                        intersect: false,
                        mode: "index"
                    },

                    plugins: {
                        ...opcoesComuns.plugins,

                        legend: {
                            display: true,
                            position: "bottom",

                            labels: {
                                usePointStyle: true,
                                pointStyle: "rectRounded",
                                padding: 18,
                                boxWidth: 10,

                                font: {
                                    size: 11
                                }
                            }
                        },

                        tooltip: {
                            ...opcoesComuns.plugins.tooltip,

                            callbacks: {
                                label: function (context) {
                                    if (context.raw === null) {
                                        return context.dataset.label +
                                            ": sem resultado";
                                    }

                                    return context.dataset.label + ": " +
                                        Number(context.raw).toLocaleString(
                                            "pt-BR",
                                            {
                                                minimumFractionDigits: 2,
                                                maximumFractionDigits: 2
                                            }
                                        ) + "%";
                                }
                            }
                        }
                    },

                    scales: {
                        ...opcoesComuns.scales,

                        x: {
                            ...opcoesComuns.scales.x,
                            offset: true,

                            ticks: {
                                autoSkip: false,
                                maxRotation: 0,
                                minRotation: 0,
                                align: "center",

                                font: {
                                    size: 10
                                },

                                padding: 8
                            }
                        },

                        y: {
                            ...opcoesComuns.scales.y,
                            min: 0,
                            max: 100,
                            beginAtZero: true
                        }
                    }
                }
            });

            graficos.push(grafico);

            // Texto explicativo abaixo do gráfico.
            if (descricao) {
                if (testesAnteriores.length === 0) {
                    descricao.textContent =
                        "Este é seu primeiro questionário. " +
                        "A média por categoria estará disponível após novos testes.";
                } else {
                    descricao.textContent =
                        "Compare a média de cada categoria nos testes anteriores " +
                        "com o resultado do questionário mais recente. " +
                        "Categorias sem resultado anterior ou atual não terão " +
                        "as duas barras preenchidas.";
                }
            }
        }
    }

    // ========================================
    // ATUALIZA AS CORES DOS GRÁFICOS
    // ========================================

    function atualizarTemaGraficos() {
        const cores = obterCoresTema();

        Chart.defaults.color = cores.texto;

        graficos.forEach(function (grafico) {
            const escalas = grafico.options.scales || {};

            Object.values(escalas).forEach(function (eixo) {
                if (eixo.ticks) {
                    eixo.ticks.color = cores.texto;
                }

                if (eixo.grid && eixo.grid.display !== false) {
                    eixo.grid.color = cores.grade;
                }
            });

            const plugins = grafico.options.plugins || {};

            if (plugins.legend && plugins.legend.labels) {
                plugins.legend.labels.color = cores.texto;
            }

            if (plugins.tooltip) {
                plugins.tooltip.backgroundColor = cores.tooltip;
                plugins.tooltip.titleColor = "#ffffff";
                plugins.tooltip.bodyColor = "#ffffff";
            }
            
            grafico.data.datasets.forEach(function (dataset) {
                if (dataset.label === "Resultado geral") {
                    dataset.borderColor = cores.linha;
                    dataset.backgroundColor = "transparent";
                    dataset.pointBackgroundColor = cores.linha;
                    dataset.pointBorderColor = "#ffffff";
                    dataset.pointBorderWidth = 3;
                    dataset.borderWidth = 5;
                    dataset.pointRadius = 8;
                    dataset.pointHoverRadius = 11;
                }

                if (dataset.label === "Média dos testes anteriores") {
                    dataset.backgroundColor = cores.barraAnterior;
                }

                if (dataset.label === "Último teste") {
                    dataset.backgroundColor = cores.barraAtual;
                }
            });
            grafico.update();
        });
    }

    // Observa mudanças nos três temas.
    const observadorTema = new MutationObserver(function () {
        atualizarTemaGraficos();
    });

    observadorTema.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ["data-tema"]
    });

    // Aplica as cores do tema escolhido ao carregar.
    atualizarTemaGraficos();
});
