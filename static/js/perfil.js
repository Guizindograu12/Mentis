document.addEventListener("DOMContentLoaded", function () {
    const dados = window.MENTIS_DASHBOARD || {
        testes: [],
        moods: [],
        mediaTestes: null,
        ultimoTeste: null
    };

    const testes = dados.testes || [];
    const moods = dados.moods || [];

    // ========================================
    // CHECK-IN EMOCIONAL
    // ========================================

    const botoesHumor = document.querySelectorAll(".mood-option");
    const feedback = document.getElementById("mood-feedback");

    botoesHumor.forEach(function (botao) {
        botao.addEventListener("click", async function () {
            const humor = Number(botao.dataset.mood);

            botoesHumor.forEach(function (item) {
                item.classList.remove("selecionado");
            });

            botao.classList.add("selecionado");

            if (!feedback) return;

            feedback.textContent = "Registrando seu check-in...";
            feedback.classList.remove("error");

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
        "O servidor retornou HTML em vez de JSON:",
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

                feedback.textContent =
                    `Check-in registrado! Seu humor de hoje: ${humor}/10.`;

                // Atualiza a média na tela.
                if (resultado.media_humor !== undefined) {
                    atualizarMediaHumor(resultado.media_humor);
                }

            } catch (erro) {
                feedback.textContent =
                    erro.message ||
                    "Não foi possível registrar o check-in.";

                feedback.classList.add("error");
            }
        });
    });

    function atualizarMediaHumor(media) {
        const cartoes = document.querySelectorAll(".stat-card");

        cartoes.forEach(function (cartao) {
            const titulo = cartao.querySelector("span");
            const valor = cartao.querySelector("strong");

            if (titulo && valor && titulo.textContent.trim() === "Avg. Mood") {
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
    Chart.defaults.color = "#77788a";

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
                backgroundColor: "#191970",
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
                    color: "#eeeeF5"
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
        new Chart(graficoLinha, {
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

                    borderColor: "#6255bd",
                    backgroundColor: "rgba(98, 85, 189, 0.12)",

                    fill: true,
                    tension: 0.3,

                    pointRadius: 5,
                    pointHoverRadius: 7,
                    pointBackgroundColor: "#6255bd",
                    borderWidth: 3
                }]
            },

            options: opcoesComuns
        });
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

        new Chart(graficoResumo, {
            type: "bar",

            data: {
                labels: [
                    "Média dos testes",
                    "Último teste"
                ],

                datasets: [{
                    data: [media, ultimo],

                    backgroundColor: [
                        "#b7a8ed",
                        "#5144a8"
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
    }

    // ========================================
    // GRÁFICO: MÉDIA ANTERIOR X ÚLTIMO TESTE
    // POR CATEGORIA
    // ========================================

    const seletor = document.getElementById("category-select");
    const graficoCategoria = document.getElementById("categoryChart");
    const descricao = document.getElementById("category-description");

    if (graficoCategoria && testes.length > 0) {

        // O histórico está ordenado do teste mais antigo
        // para o mais recente.
        const testesAnteriores = testes.slice(0, -1);
        const testeMaisRecente = testes[testes.length - 1];

        // Reúne todas as categorias encontradas no histórico.
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

        // O gráfico agora apresenta todas as categorias.
        // O seletor deixa de ser necessário.
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

            return;
        }

        graficoCategoria.hidden = false;

        // Calcula a média anterior e o último resultado
        // separadamente para cada categoria.
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
        new Chart(graficoCategoria, {
            type: "bar",

            data: {
                labels: nomesCategorias,

                datasets: [
                    {
                        label: "Média dos testes anteriores",
                        data: mediasAnteriores,
                        backgroundColor: "#b7a8ed",
                        borderRadius: 7,
                        maxBarThickness: 32
                    },
                    {
                        label: "Último teste",
                        data: resultadosRecentes,
                        backgroundColor: "#5144a8",
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

        // Explicação abaixo do gráfico.
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
})