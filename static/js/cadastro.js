/* ==========================================
   CADASTRO E LOGIN: abas, máscara do CNPJ e validações
   As regras do cadastro aqui são só para avisar rápido o usuário.
   O servidor (backend/validacoes.py) valida tudo de novo.
   ========================================== */

(function () {
    "use strict";

    var IDADE_MINIMA = 14;
    var TAMANHO_MINIMO_SENHA = 8;

    // Só Empresa/RH tem domínio obrigatório.
    // Funcionário aceita qualquer e-mail válido.
    var DOMINIOS = {
        empresa_rh: "mentisrh.com"
    };


    // ==========================================
    // CADASTRO
    // ==========================================

    function iniciarCadastro() {

        var area = document.getElementById("cadastro-area");

        if (!area) {
            return;
        }

        var abas = area.querySelectorAll(".aba-cadastro");

        var paineis = {
            funcionario: document.getElementById("painel-funcionario"),
            empresa_rh: document.getElementById("painel-empresa")
        };


        // ------------------------------------------
        // ABAS
        // ------------------------------------------

        function mostrarTipo(tipo) {

            Object.keys(paineis).forEach(function (chave) {
                paineis[chave].hidden = (chave !== tipo);
            });

            abas.forEach(function (aba) {

                var ativa = aba.getAttribute("data-tipo") === tipo;

                aba.classList.toggle("ativa", ativa);
                aba.setAttribute("aria-selected", ativa ? "true" : "false");
            });
        }

        abas.forEach(function (aba) {

            aba.addEventListener("click", function () {
                mostrarTipo(aba.getAttribute("data-tipo"));
            });
        });

        // Se o servidor devolveu um erro, abre a aba que a pessoa estava usando
        var tipoInicial = area.getAttribute("data-tipo-inicial");

        mostrarTipo(tipoInicial === "empresa_rh" ? "empresa_rh" : "funcionario");


        // ------------------------------------------
        // DATA DE NASCIMENTO
        // ------------------------------------------

        function formatarDataISO(data) {

            var mes = String(data.getMonth() + 1).padStart(2, "0");
            var dia = String(data.getDate()).padStart(2, "0");

            return data.getFullYear() + "-" + mes + "-" + dia;
        }

        function calcularIdade(valorISO) {

            // valorISO no formato AAAA-MM-DD
            var partes = valorISO.split("-");

            if (partes.length !== 3) {
                return null;
            }

            var ano = Number(partes[0]);
            var mes = Number(partes[1]);
            var dia = Number(partes[2]);

            if (!ano || !mes || !dia) {
                return null;
            }

            var hoje = new Date();
            var idade = hoje.getFullYear() - ano;

            var jaFezAniversario = (
                hoje.getMonth() + 1 > mes ||
                (hoje.getMonth() + 1 === mes && hoje.getDate() >= dia)
            );

            if (!jaFezAniversario) {
                idade -= 1;
            }

            return idade;
        }

        var campoData = area.querySelector('input[name="data_nascimento"]');

        if (campoData) {
            // Não deixa escolher uma data no futuro
            campoData.max = formatarDataISO(new Date());
        }


        // ------------------------------------------
        // CNPJ (máscara e validação)
        // ------------------------------------------

        function aplicarMascaraCnpj(valor) {

            var d = valor.replace(/\D/g, "").slice(0, 14);

            var resultado = d;

            if (d.length > 2) {
                resultado = d.slice(0, 2) + "." + d.slice(2);
            }

            if (d.length > 5) {
                resultado = d.slice(0, 2) + "." + d.slice(2, 5) + "." + d.slice(5);
            }

            if (d.length > 8) {
                resultado = d.slice(0, 2) + "." + d.slice(2, 5) + "." +
                            d.slice(5, 8) + "/" + d.slice(8);
            }

            if (d.length > 12) {
                resultado = d.slice(0, 2) + "." + d.slice(2, 5) + "." +
                            d.slice(5, 8) + "/" + d.slice(8, 12) + "-" +
                            d.slice(12);
            }

            return resultado;
        }

        function calcularDigitoCnpj(base) {

            var pesos = (base.length === 12)
                ? [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
                : [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];

            var soma = 0;

            for (var i = 0; i < base.length; i++) {
                soma += Number(base.charAt(i)) * pesos[i];
            }

            var resto = soma % 11;

            return resto < 2 ? 0 : 11 - resto;
        }

        function cnpjValido(valor) {

            var d = valor.replace(/\D/g, "");

            if (d.length !== 14) {
                return false;
            }

            // Rejeita 00000000000000, 11111111111111, etc.
            if (/^(\d)\1+$/.test(d)) {
                return false;
            }

            var base = d.slice(0, 12);
            var digito1 = calcularDigitoCnpj(base);
            var digito2 = calcularDigitoCnpj(base + digito1);

            return (
                digito1 === Number(d.charAt(12)) &&
                digito2 === Number(d.charAt(13))
            );
        }

        var campoCnpj = area.querySelector('input[name="cnpj"]');

        if (campoCnpj) {

            campoCnpj.addEventListener("input", function () {
                campoCnpj.value = aplicarMascaraCnpj(campoCnpj.value);
            });
        }


        // ------------------------------------------
        // VALIDAÇÃO AO ENVIAR
        // ------------------------------------------

        function emailValido(email, tipo) {

            var padrao;

            if (DOMINIOS[tipo]) {

                // Empresa/RH: domínio obrigatório
                var dominio = DOMINIOS[tipo].replace(".", "\\.");
                padrao = new RegExp("^[a-z0-9._%+\\-]+@" + dominio + "$");

            } else {

                // Funcionário: qualquer e-mail no formato nome@dominio.com
                padrao = /^[a-z0-9._%+\-]+@[a-z0-9\-]+(\.[a-z0-9\-]+)+$/;
            }

            return padrao.test(email);
        }

        function validarFormulario(form) {

            var tipo = form.getAttribute("data-tipo");

            var email = form.elements["email"].value.trim().toLowerCase();
            var senha = form.elements["senha"].value;
            var confirmar = form.elements["confirmar_senha"].value;

            if (tipo === "funcionario") {

                var data = form.elements["data_nascimento"].value;
                var idade = calcularIdade(data);

                if (idade === null || idade < 0 || idade > 120) {
                    return "Informe uma data de nascimento válida.";
                }

                if (idade < IDADE_MINIMA) {
                    return "Você precisa ter pelo menos " + IDADE_MINIMA +
                           " anos para se cadastrar.";
                }
            }

            if (tipo === "empresa_rh") {

                if (!cnpjValido(form.elements["cnpj"].value)) {
                    return "Informe um CNPJ válido.";
                }
            }

            if (!emailValido(email, tipo)) {

                if (DOMINIOS[tipo]) {
                    return "O e-mail precisa terminar com @" + DOMINIOS[tipo] + ".";
                }

                return "Informe um e-mail válido.";
            }

            if (senha.length < TAMANHO_MINIMO_SENHA) {
                return "A senha precisa ter pelo menos " +
                       TAMANHO_MINIMO_SENHA + " caracteres.";
            }

            if (senha !== confirmar) {
                return "As senhas não são iguais.";
            }

            return null;
        }

        var formularios = area.querySelectorAll(".form-cadastro");

        formularios.forEach(function (form) {

            var caixaErro = form.querySelector(".erro-cliente");

            form.addEventListener("submit", function (evento) {

                var mensagem = validarFormulario(form);

                if (mensagem) {

                    evento.preventDefault();

                    caixaErro.textContent = mensagem;
                    caixaErro.hidden = false;

                    return;
                }

                caixaErro.hidden = true;
            });
        });
    }


    // ==========================================
    // LOGIN (abas Funcionário / Empresa-RH)
    // Por enquanto as abas só mudam os textos e a dica do e-mail.
    // ==========================================

    function iniciarAbasLogin() {

        var areaLogin = document.getElementById("login-area");

        if (!areaLogin) {
            return;
        }

        var abas = areaLogin.querySelectorAll(".aba-cadastro");

        var icone = document.getElementById("login-cartao-icone");
        var titulo = document.getElementById("login-cartao-titulo");
        var subtitulo = document.getElementById("login-cartao-subtitulo");
        var campoEmail = document.getElementById("login-email");

        var ICONE_FUNCIONARIO = (
            '<circle cx="12" cy="8" r="4"></circle>' +
            '<path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7z"></path>'
        );

        var ICONE_EMPRESA = (
            '<path d="M4 21V4a1 1 0 0 1 1-1h9a1 1 0 0 1 1 1v6h4a1 1 0 0 1 1 1v10z"></path>'
        );

        var TEXTOS = {

            funcionario: {
                titulo: "Entrar como Funcionário",
                subtitulo: "Use o e-mail e a senha da sua conta.",
                placeholder: "E-mail",
                icone: ICONE_FUNCIONARIO
            },

            empresa_rh: {
                titulo: "Entrar como Empresa / RH",
                subtitulo: "Use o e-mail e a senha da conta da empresa.",
                placeholder: "E-mail (@mentisrh.com)",
                icone: ICONE_EMPRESA
            }
        };

        function mostrarTipoLogin(tipo) {

            var textos = TEXTOS[tipo];

            titulo.textContent = textos.titulo;
            subtitulo.textContent = textos.subtitulo;
            campoEmail.placeholder = textos.placeholder;
            icone.innerHTML = textos.icone;

            abas.forEach(function (aba) {

                var ativa = aba.getAttribute("data-tipo") === tipo;

                aba.classList.toggle("ativa", ativa);
                aba.setAttribute("aria-selected", ativa ? "true" : "false");
            });
        }

        abas.forEach(function (aba) {

            aba.addEventListener("click", function () {
                mostrarTipoLogin(aba.getAttribute("data-tipo"));
            });
        });
    }


    iniciarCadastro();
    iniciarAbasLogin();

})();