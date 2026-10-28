from errors import AppError
from models.constants import CATEGORIAS_VALIDAS


def parse_produto_payload(dados):
    if not dados:
        raise AppError("Dados inválidos")
    if "nome" not in dados:
        raise AppError("Nome é obrigatório")
    if "preco" not in dados:
        raise AppError("Preço é obrigatório")
    if "estoque" not in dados:
        raise AppError("Estoque é obrigatório")

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", "geral")

    if preco < 0:
        raise AppError("Preço não pode ser negativo")
    if estoque < 0:
        raise AppError("Estoque não pode ser negativo")
    if len(nome) < 2:
        raise AppError("Nome muito curto")
    if len(nome) > 200:
        raise AppError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise AppError("Categoria inválida. Válidas: " + str(list(CATEGORIAS_VALIDAS)))

    return nome, descricao, preco, estoque, categoria
