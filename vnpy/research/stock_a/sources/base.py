from dataclasses import dataclass
from typing import Protocol

from vnpy.trader.object import BarData, HistoryRequest


class StockAHistorySource(Protocol):
    def query_bar_history(self, req: HistoryRequest) -> list[BarData]:
        ...


@dataclass(slots=True)
class StockAHistoryBackendConfig:
    backend: str = "xt"
