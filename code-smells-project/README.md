# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo.

## Configuração

Copie `.env.example` (ou exporte variáveis no shell). Principais:

- `FLASK_SECRET_KEY` — chave da sessão/token (gerada automaticamente se ausente)
- `FLASK_DEBUG` — default `false`
- `FLASK_HOST` / `FLASK_PORT` — default `127.0.0.1:5000`
- `DATABASE_PATH` — default `loja.db`
- `CORS_ORIGINS` — lista separada por vírgula

## Autenticação

Após `POST /login` com `email` e `senha`, a resposta inclui `dados.token`.
Rotas autenticadas usam o header:

```text
Authorization: Bearer <token>
```

Usuários seed: `admin@loja.com` / `admin123` (admin) e `joao@email.com` / `123456` (cliente).

`POST /admin/query` não executa SQL (desativado). `POST /admin/reset-db` exige admin.
