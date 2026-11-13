"""Fixtures compartilhadas — app em memória, sem SMTP e sem banco em disco."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, init_database  # noqa: E402
from config import TestConfig  # noqa: E402
from database import db  # noqa: E402
from models.category import Category  # noqa: E402
from models.task import Task  # noqa: E402
from models.user import User  # noqa: E402
from utils.helpers import utcnow  # noqa: E402

from datetime import timedelta  # noqa: E402


@pytest.fixture()
def app():
    application = create_app(TestConfig)
    init_database(application)
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def seeded(app):
    """admin + `count` usuários com `i+1` tasks cada, todas atrasadas e pendentes."""
    with app.app_context():
        admin = User(name='Admin', email='admin@x.com', role='admin')
        admin.set_password('1234')
        db.session.add(admin)
        db.session.commit()

        for i in range(4):
            user = User(name='User %d' % i, email='u%d@x.com' % i)
            user.set_password('1234')
            db.session.add(user)
            category = Category(name='Cat %d' % i, description='', color='#000000')
            db.session.add(category)
            db.session.commit()
            for j in range(i + 1):
                db.session.add(Task(title='T %d-%d' % (i, j), status='pending', priority=3,
                                    user_id=user.id, category_id=category.id,
                                    due_date=utcnow() - timedelta(days=j + 1)))
        db.session.commit()
    return app


@pytest.fixture()
def token(client, seeded):
    response = client.post('/login', json={'email': 'admin@x.com', 'password': '1234'})
    return response.get_json()['token']


@pytest.fixture()
def auth(token):
    return {'Authorization': 'Bearer %s' % token}


@pytest.fixture()
def record_queries(app):
    """Context manager que devolve a lista de SQL emitido dentro do bloco."""
    from contextlib import contextmanager

    from sqlalchemy import event

    @contextmanager
    def _record():
        statements = []

        def _capture(conn, cursor, statement, params, context, executemany):
            statements.append(statement)

        with app.app_context():
            engine = db.engine
        event.listen(engine, 'before_cursor_execute', _capture)
        try:
            yield statements
        finally:
            event.remove(engine, 'before_cursor_execute', _capture)

    return _record

