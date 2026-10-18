document.addEventListener("DOMContentLoaded", function () {
    const botaoImprimir = document.getElementById("botaoImprimir");

    if (botaoImprimir) {
        botaoImprimir.addEventListener("click", function () {
            window.print();
        });
    }
});
