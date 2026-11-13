"""Regressoes dos findings abertos da auditoria (project 3).

Cobrem FINDING-013 (N+1 em `/users`), FINDING-014 (full-table em stats),
FINDING-020 (bind padrao) e FINDING-021 (dependencias/notificacao orfas).
"""
import os

from services.task_service import TaskService


def _task_select_columns(statements):
    """Colunas `tasks.*` carregadas por SELECT (ignora agregacoes)."""
    loaded = []
    for statement in statements:
        flat = ' '.join(statement.split()).lower()
        if not flat.startswith('select') or 'count(' in flat:
            continue
        select_list = flat.split(' from ')[0]
        if 'tasks.' in select_list:
            loaded.append(select_list.count('tasks.'))
    return loaded


# ----- FINDING-013 ---------------------------------------------------------

def test_users_task_count_is_correct(client, auth, seeded, record_queries):
    response = client.get('/users', headers=auth)
    assert response.status_code == 200
    counts = {user['email']: user['task_count'] for user in response.get_json()}
    assert counts == {'admin@x.com': 0, 'u0@x.com': 1, 'u1@x.com': 2,
                      'u2@x.com': 3, 'u3@x.com': 4}


def test_users_does_not_lazy_load_tasks(client, auth, seeded, record_queries):
    """Antes: `len(user.tasks)` gerava 1 SELECT por usuario."""
    with record_queries() as statements:
        client.get('/users', headers=auth)
    assert _task_select_columns(statements) == []


# ----- FINDING-014 ---------------------------------------------------------

def test_summary_does_not_load_full_task_entities(client, auth, seeded, record_queries):
    with record_queries() as statements:
        response = client.get('/reports/summary', headers=auth)
    assert response.status_code == 200
    # No maximo a projecao de atrasadas (id, title, due_date) = 3 colunas.
    assert all(columns <= 3 for columns in _task_select_columns(statements))


def test_summary_keeps_the_original_contract(client, auth, seeded):
    payload = client.get('/reports/summary', headers=auth).get_json()
    assert set(payload) == {'generated_at', 'overview', 'tasks_by_status',
                            'tasks_by_priority', 'overdue', 'recent_activity',
                            'user_productivity'}
    assert payload['overview'] == {'total_tasks': 10, 'total_users': 5,
                                   'total_categories': 4}
    assert payload['tasks_by_status'] == {'pending': 10, 'in_progress': 0,
                                          'done': 0, 'cancelled': 0}
    assert set(payload['tasks_by_priority']) == {'critical', 'high', 'medium',
                                                 'low', 'minimal'}
    assert payload['overdue']['count'] == 10
    assert set(payload['overdue']['tasks'][0]) == {'id', 'title', 'due_date',
                                                   'days_overdue'}
    productivity = {item['user_id']: item for item in payload['user_productivity']}
    assert productivity[2]['total_tasks'] == 1
    assert productivity[5]['total_tasks'] == 4
    assert productivity[5]['completion_rate'] == 0


def test_stats_counts_overdue_in_the_database(client, auth, seeded, record_queries):
    with record_queries() as statements:
        response = client.get('/tasks/stats', headers=auth)
    assert response.status_code == 200
    assert response.get_json()['overdue'] == 10
    assert _task_select_columns(statements) == []


# ----- FINDING-015 (paginação opcional) -----------------------------------

def test_lists_keep_array_shape_without_pagination_params(client, auth, seeded):
    for path in ('/users', '/tasks', '/categories', '/tasks/search', '/users/2/tasks'):
        payload = client.get(path, headers=auth).get_json()
        assert isinstance(payload, list), path
        if payload:
            assert 'items' not in payload[0], path


def test_pagination_returns_envelope_with_metadata(client, auth, seeded):
    payload = client.get('/tasks?page=2&per_page=3', headers=auth).get_json()
    assert set(payload) == {'items', 'page', 'per_page', 'total', 'pages'}
    assert payload['page'] == 2
    assert payload['per_page'] == 3
    assert payload['total'] == 10
    assert payload['pages'] == 4
    assert len(payload['items']) == 3


def test_pagination_last_page_and_out_of_range(client, auth, seeded):
    first = client.get('/tasks?per_page=4&page=1', headers=auth).get_json()
    last = client.get('/tasks?per_page=4&page=3', headers=auth).get_json()
    beyond = client.get('/tasks?per_page=4&page=9', headers=auth).get_json()
    assert len(first['items']) == 4
    assert len(last['items']) == 2
    assert beyond['items'] == []
    assert beyond['total'] == 10


def test_pagination_is_consistent_across_list_endpoints(client, auth, seeded):
    users = client.get('/users?page=1&per_page=2', headers=auth).get_json()
    categories = client.get('/categories?page=1&per_page=2', headers=auth).get_json()
    user_tasks = client.get('/users/5/tasks?page=1&per_page=2', headers=auth).get_json()
    search = client.get('/tasks/search?q=T&page=1&per_page=2', headers=auth).get_json()
    ranked = client.get('/tasks/search?status=pending&page=1&per_page=2',
                        headers=auth).get_json()
    assert (users['total'], users['pages'], len(users['items'])) == (5, 3, 2)
    assert (categories['total'], categories['pages']) == (4, 2)
    assert (user_tasks['total'], user_tasks['pages'], len(user_tasks['items'])) == (4, 2, 2)
    assert (search['total'], len(search['items'])) == (10, 2)
    assert (ranked['total'], len(ranked['items'])) == (10, 2)


def test_pagination_uses_limit_offset_and_one_count_query(client, auth, seeded, record_queries):
    with record_queries() as statements:
        client.get('/tasks?page=2&per_page=3', headers=auth)
    flat = [' '.join(statement.split()).upper() for statement in statements]
    assert sum('LIMIT' in statement for statement in flat) == 1
    assert sum('COUNT(' in statement for statement in flat) == 1
    assert not any('count(*) from (select' in statement.lower() for statement in flat)


def test_pagination_rejects_invalid_parameters(client, auth, seeded):
    for query in ('?page=0', '?page=abc', '?per_page=0', '?per_page=101', '?page=-1'):
        response = client.get('/tasks%s' % query, headers=auth)
        assert response.status_code == 400, query
        assert 'error' in response.get_json()


def test_default_host_is_loopback(monkeypatch):
    monkeypatch.delenv('TASK_MANAGER_HOST', raising=False)
    import importlib

    import config as config_module

    reloaded = importlib.reload(config_module)
    assert reloaded.Config.HOST == '127.0.0.1'


# ----- FINDING-021 ---------------------------------------------------------

def test_requirements_has_only_used_dependencies():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'requirements.txt')
    with open(path, encoding='utf-8') as handle:
        declared = [line.strip().split('==')[0].lower()
                    for line in handle if line.strip() and not line.startswith('#')]
    assert 'flask' in declared
    assert 'marshmallow' not in declared
    assert 'requests' not in declared
    assert 'python-dotenv' not in declared


def test_notification_is_sent_on_task_assignment(client, auth, seeded, monkeypatch):
    sent = []

    class SpyNotification:
        @staticmethod
        def notify_task_assigned(user, task):
            sent.append((user.email if user else None, task.title))
            return True

    monkeypatch.setattr(TaskService, 'notifications', SpyNotification)
    created = client.post('/tasks', json={'title': 'Nova task', 'user_id': 2},
                          headers=auth).get_json()

    # Reatribuir para outro usuario notifica; renomear nao.
    client.put('/tasks/%d' % created['id'], json={'user_id': 3}, headers=auth)
    client.put('/tasks/%d' % created['id'], json={'title': 'Renomeada'}, headers=auth)

    assert sent == [('u0@x.com', 'Nova task'), ('u1@x.com', 'Nova task')]


def test_notification_skipped_when_task_has_no_assignee(client, auth, seeded, monkeypatch):
    sent = []

    class SpyNotification:
        @staticmethod
        def notify_task_assigned(user, task):
            sent.append(task.title)
            return True

    monkeypatch.setattr(TaskService, 'notifications', SpyNotification)
    response = client.post('/tasks', json={'title': 'Sem responsavel'}, headers=auth)
    assert response.status_code == 201
    assert sent == []


def test_notification_service_degrades_without_smtp(app, seeded):
    """Sem SMTP configurado, enviar e-mail apenas loga e retorna False."""
    from services.notification_service import NotificationService

    with app.app_context():
        assert NotificationService.is_configured() is False
        assert NotificationService.send_email('alvo@x.com', 'assunto', 'corpo') is False


def test_task_creation_survives_unconfigured_smtp(client, auth, seeded):
    """Sem SMTP, a criacao de task continua funcionando (notificacao e best-effort)."""
    response = client.post('/tasks', json={'title': 'Persistida', 'user_id': 2},
                           headers=auth)
    assert response.status_code == 201
    assert response.get_json()['title'] == 'Persistida'
    tasks = client.get('/users/2/tasks', headers=auth).get_json()
    assert 'Persistida' in [task['title'] for task in tasks]
