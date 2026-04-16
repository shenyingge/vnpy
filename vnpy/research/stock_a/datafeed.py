from collections.abc import Callable

from vnpy.trader.datafeed import BaseDatafeed
from vnpy.trader.object import BarData, HistoryRequest

from .sources import StockAHistorySource, create_xt_history_source


class StockAResearchDatafeed(BaseDatafeed):
    def __init__(self, source: StockAHistorySource, backend: str = "xt") -> None:
        self.source: StockAHistorySource = source
        self.backend: str = backend

    def init(self, output: Callable = print) -> bool:
        return self.source.init(output=output)

    @classmethod
    def from_backend(cls, backend: str = "xt") -> "StockAResearchDatafeed":
        if backend == "xt":
            return cls(source=create_xt_history_source(), backend=backend)

        raise ValueError(f"unsupported history backend: {backend}")

    def query_bar_history(
        self,
        req: HistoryRequest,
        output: Callable = print,
    ) -> list[BarData]:
        return self.source.query_bar_history(req, output=output)
