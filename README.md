# Mentis

## Banco de dados

A Mentis utiliza:

- PostgreSQL
- Flask-SQLAlchemy
- SQLAlchemy
- Psycopg 3

## Nova estrutura

- `usuarios`: contas cadastradas
- `perguntas`: perguntas do questionário
- `testes`: cada execução feita por um usuário
- `respostas`: cada resposta ligada ao teste e à pergunta
- `resultados`: resultado geral de cada teste
- `resultado_categorias`: resultado calculado para cada categoria

Relacionamentos:

```text
usuarios
   |
   +--- testes
          |
          +--- respostas --- perguntas
          |
          +--- resultados
                  |
                  +--- resultado_categorias
```

## Primeira configuração desta versão

Como a estrutura do PostgreSQL mudou, e o banco atual contém apenas dados de teste, é recomendado recriá-lo uma vez.

1. Feche o Flask.
2. Ative o ambiente virtual.
3. Execute:

```bash
python resetar_banco.py
```

4. Quando aparecer a confirmação, digite:

```text
APAGAR
```

Isso remove as tabelas atuais e cria a nova estrutura, incluindo as 25 perguntas.

Depois:

```bash
python app.py
```

O sistema continuará sincronizando as perguntas com o banco.

## Resultado

Depois de enviar um questionário, o fluxo é:

```text
respostas
    ↓
análise geral
    ↓
análise por categoria
    ↓
resultado salvo
    ↓
relatório
```

A página de resultado fica disponível em `/resultado/<teste_id>` e só pode ser aberta pelo usuário que realizou aquele teste.

## Configuração

Crie `.env` a partir de `.env.example`:

```text
DATABASE_URL=postgresql+psycopg://postgres:SUA_SENHA@localhost:5432/mentis
SECRET_KEY=sua-chave
```

Nunca compartilhe seu `.env` real.
