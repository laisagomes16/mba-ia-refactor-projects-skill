# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Diferente dos outros projetos, este já possui alguma separação de camadas (`models/`, `routes/`, `services/`, `utils/`), mas ainda contém problemas arquiteturais e de qualidade.

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env          # preencha FLASK_SECRET_KEY
python seed.py                # popula o banco SQLite
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`tasks.db`)
com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso
contrário os endpoints vão retornar listas vazias.

## Configuração

Toda configuração sensível vem de variáveis de ambiente (veja `.env.example`). Nenhum
segredo fica no código-fonte.

| Variável | Padrão | Descrição |
|---|---|---|
| `FLASK_SECRET_KEY` | aleatório por processo | Assina os tokens de autenticação |
| `TASK_MANAGER_DATABASE_URI` | `sqlite:///tasks.db` | Conexão do banco |
| `TASK_MANAGER_HOST` / `TASK_MANAGER_PORT` | `0.0.0.0` / `5000` | Bind do servidor |
| `FLASK_DEBUG` | `false` | Modo debug (nunca em produção) |
| `SMTP_*` | — | Opcionais; sem eles o envio de e-mail é apenas registrado em log |

## Arquitetura

```text
app.py                  app factory (create_app) + rotas / e /health
config.py               configuração por ambiente (sem segredos)
errors.py               exceções de domínio
error_handlers.py       mapeamento central de erro → HTTP JSON
serializers.py          formato JSON público (única fonte)
routes/                  controllers finos (só HTTP)
services/                regras de negócio (sem HTTP, sem SQL)
repositories/            acesso a dados (único lugar com queries)
models/                  entidades e invariantes do domínio
utils/helpers.py         constantes e utilitários compartilhados
```

Fluxo de uma requisição: `route → service → repository → model`, com erros de domínio
traduzidos para HTTP pelo handler central.

## Compatibilidade

- O contrato JSON das 22 rotas originais é preservado campo a campo. A única diferença
  intencional é que o campo `password` **não** é mais exposto em nenhuma resposta.
- Contas com hash MD5 legado continuam autenticando e são migradas para PBKDF2 no
  primeiro login bem-sucedido.
- `POST /login` continua devolvendo `token`; o valor agora é um token HMAC assinado e
  validável (`services/auth_service.py`) em vez de `fake-jwt-token-<id>`.

