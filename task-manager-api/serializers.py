"""Serializers — única fonte do formato JSON público.

O contrato anterior é preservado campo a campo (incluindo as chaves extras que
cada endpoint já devolvia); a única diferença intencional é a remoção do campo
`password` (FINDING-003).
"""


def _fmt(moment):
    return str(moment) if moment else None


def serialize_task(task, include_tags=True):
    """Formato base de `/tasks` — todos os campos originais preservados."""
    data = {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'user_id': task.user_id,
        'category_id': task.category_id,
        'created_at': _fmt(task.created_at),
        'updated_at': _fmt(task.updated_at),
        'due_date': _fmt(task.due_date),
    }
    if include_tags:
        data['tags'] = task.tag_list
    return data


def serialize_task_summary(task):
    """Formato enxuto usado por `/users/<id>/tasks`."""
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'due_date': _fmt(task.due_date),
        'created_at': _fmt(task.created_at),
        'overdue': task.is_overdue(),
    }


def serialize_task_with_relations(task):
    """Formato de `/tasks` (lista): base + nomes do usuário e categoria."""
    data = serialize_task(task)
    data['user_name'] = task.user.name if task.user else None
    data['category_name'] = task.category.name if task.category else None
    data['overdue'] = task.is_overdue()
    return data


def serialize_user(user, include_tasks=False):
    data = {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'active': user.active,
        'created_at': _fmt(user.created_at),
    }
    if include_tasks:
        data['tasks'] = [serialize_task(task, include_tags=False) for task in user.tasks]
    return data


def serialize_user_summary(user):
    """Formato de `/users` (lista) — `task_count` é adicionado pelo controller."""
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'active': user.active,
        'created_at': _fmt(user.created_at),
    }


def serialize_category(category):
    return {
        'id': category.id,
        'name': category.name,
        'description': category.description,
        'color': category.color,
        'created_at': _fmt(category.created_at),
    }
