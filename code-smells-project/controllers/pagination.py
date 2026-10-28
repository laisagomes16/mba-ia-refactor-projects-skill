from flask import request

from errors import AppError


def parse_pagination():
    limit_raw = request.args.get("limit")
    offset_raw = request.args.get("offset", "0")
    try:
        offset = int(offset_raw)
        limit = int(limit_raw) if limit_raw is not None else None
    except ValueError:
        raise AppError("Paginação inválida")
    if offset < 0 or (limit is not None and limit < 1):
        raise AppError("Paginação inválida")
    return limit, offset
