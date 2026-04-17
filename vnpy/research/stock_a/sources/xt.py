from collections.abc import Callable
from dataclasses import replace
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from vnpy.trader.object import BarData, HistoryRequest

from .base import StockAHistorySource


CN_TZ = ZoneInfo("Asia/Shanghai")


def normalize_cn_datetime(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(CN_TZ).replace(tzinfo=None)


@dataclass(slots=True)
class XtHistorySource(StockAHistorySource):
    xt_datafeed: object

    def init(self, output: Callable = print) -> bool:
        if hasattr(self.xt_datafeed, "init"):
            return self.xt_datafeed.init(output=output)
        return True

    def query_bar_history(
        self,
        req: HistoryRequest,
        output: Callable = print,
    ) -> list[BarData]:
        bars: list[BarData] = self.xt_datafeed.query_bar_history(req, output=output)
        normalized: list[BarData] = []

        for bar in bars:
            normalized_bar: BarData = replace(bar, datetime=normalize_cn_datetime(bar.datetime))
            normalized_bar.extra = bar.extra
            normalized.append(normalized_bar)

        return normalized


def create_xt_history_source(
    xt_datafeed_factory: Callable[[], object] | None = None,
) -> XtHistorySource:
    if xt_datafeed_factory is None:
        from vnpy_xt.xt_datafeed import XtDatafeed

        xt_datafeed_factory = XtDatafeed

    xt_datafeed = xt_datafeed_factory()

    return XtHistorySource(xt_datafeed=xt_datafeed)
