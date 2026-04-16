from collections.abc import Callable
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

    def query_bar_history(self, req: HistoryRequest) -> list[BarData]:
        bars: list[BarData] = self.xt_datafeed.query_bar_history(req)
        normalized: list[BarData] = []

        for bar in bars:
            bar.datetime = normalize_cn_datetime(bar.datetime)
            normalized.append(bar)

        return normalized


def create_xt_history_source(
    xt_datafeed_factory: Callable[[], object] | None = None,
) -> XtHistorySource:
    if xt_datafeed_factory is None:
        from vnpy_xt.xt_datafeed import XtDatafeed

        xt_datafeed_factory = XtDatafeed

    xt_datafeed = xt_datafeed_factory()

    if hasattr(xt_datafeed, "init"):
        xt_datafeed.init()

    return XtHistorySource(xt_datafeed=xt_datafeed)
