from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from vnpy.trader.object import BarData, HistoryRequest


class StockAHistorySource(Protocol):
    def init(self, output: Callable = print) -> bool:
        ...

    def query_bar_history(
        self,
        req: HistoryRequest,
        output: Callable = print,
    ) -> list[BarData]:
        ...


@dataclass(slots=True)
class StockAHistoryBackendConfig:
    backend: str = "xt"
