from models.constants import DESCONTO_FAIXAS
from repositories.order_repository import OrderRepository


class ReportService:
    def __init__(self, order_repo=None):
        self.order_repo = order_repo or OrderRepository()

    def vendas(self):
        total_pedidos, faturamento, pendentes, aprovados, cancelados = (
            self.order_repo.sales_aggregates()
        )
        if faturamento is None:
            faturamento = 0

        desconto = 0
        for limite, taxa in DESCONTO_FAIXAS:
            if faturamento > limite:
                desconto = faturamento * taxa
                break

        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
            "pedidos_pendentes": pendentes,
            "pedidos_aprovados": aprovados,
            "pedidos_cancelados": cancelados,
            "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0
        }
