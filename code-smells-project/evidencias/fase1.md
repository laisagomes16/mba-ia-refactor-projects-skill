================================
PHASE 1: PROJECT ANALYSIS
================================

Language:      Python (versão unknown)
Framework:     Flask 3.1.1; flask-cors 5.0.1
Dependencies:  flask==3.1.1, flask-cors==5.0.1 (requirements.txt; sem lockfile). sqlite3 (stdlib). Sem ORM, Docker, CI ou suíte de testes detectados.
Domain:        API HTTP de loja/e-commerce: produtos, usuários, login, pedidos, relatório de vendas, health e rotas admin.
Architecture:  Híbrido — MVC parcial (app.py + controllers.py + models.py) com núcleo monolítico não estruturado. Pastas de camadas não existem; os nomes dos arquivos não correspondem às responsabilidades reais.
Source files:  4 arquivos Python analisados (app.py, controllers.py, models.py, database.py); também lidos requirements.txt e README.md. Sem testes, migrations, templates ou views.
DB:            SQLite via sqlite3, arquivo loja.db, conexão global em database.py (check_same_thread=False). Schema e seed no primeiro get_db().
DB tables:     produtos, usuarios, pedidos, itens_pedido

Entry points:
- app.py: Flask(__name__), CORS, registro de rotas, if __name__ == "__main__" → get_db() + app.run(host="0.0.0.0", port=5000, debug=True)
- README: pip install -r requirements.txt; python app.py (http://localhost:5000)
- Configuração: SECRET_KEY e DEBUG em app.config (hardcoded); db_path = "loja.db"; sem .env/Dockerfile detectados

Architecture flow:
Intenção aparente: Route → Controller → Model → Database

Fluxo real:
  HTTP (app.py add_url_rule / @app.route)
    → funções em controllers.py (validação, regras, JSON, prints de notificação, SQL no health_check)
    → funções em models.py (SQL concatenado + regras de pedido/estoque + relatório/desconto)
    → database.get_db() (singleton + DDL + seed)
  Exceções no fluxo:
    app.py /admin/reset-db e /admin/query → SQL direto (sem controllers/models)
    controllers.health_check → SQL direto
    models.py mistura persistência, regras de negócio e serialização dict
    Sem services, repositories, validators, middleware, jobs, events, testes

Potential risks:
- SQL montado por concatenação de strings em models.py (e query livre em /admin/query)
- Segredos e credenciais hardcoded (SECRET_KEY em app.py; senhas no seed de database.py; health_check devolve secret_key)
- Auth fraca: login compara senha em texto; GET /usuarios devolve senhas; sem auth nas rotas (incl. admin e relatórios)
- DEBUG=True, host 0.0.0.0; health_check marca ambiente "producao" com debug True
- Estado global mutável da conexão SQLite compartilhada entre threads
- N+1 em get_pedidos_usuario / get_todos_pedidos (cursors extras por pedido/item)
- Regras e side effects no controller (validação duplicada criar/atualizar produto; prints de e-mail/SMS/push)
- Endpoint de reset e execução arbitrária de SQL sem proteção
- Sem testes automatizados; import sqlite3 em models.py aparentemente não usado

================================