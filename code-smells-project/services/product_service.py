from repositories.product_repository import ProductRepository
from validators.product_validator import parse_produto_payload
from errors import AppError


class ProductService:
    def __init__(self, repository=None):
        self.repository = repository or ProductRepository()

    def listar(self, limit=None, offset=0):
        return self.repository.list_all(limit=limit, offset=offset)

    def obter(self, product_id):
        produto = self.repository.get_by_id(product_id)
        if not produto:
            raise AppError("Produto não encontrado", 404)
        return produto

    def criar(self, dados):
        nome, descricao, preco, estoque, categoria = parse_produto_payload(dados)
        return self.repository.create(nome, descricao, preco, estoque, categoria)

    def atualizar(self, product_id, dados):
        if not self.repository.get_by_id(product_id):
            raise AppError("Produto não encontrado", 404)
        nome, descricao, preco, estoque, categoria = parse_produto_payload(dados)
        self.repository.update(product_id, nome, descricao, preco, estoque, categoria)

    def deletar(self, product_id):
        if not self.repository.get_by_id(product_id):
            raise AppError("Produto não encontrado", 404)
        self.repository.delete(product_id)

    def buscar(self, termo, categoria, preco_min, preco_max):
        return self.repository.search(termo, categoria, preco_min, preco_max)
