from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData, HistoryRequest
from vnpy.research.stock_a.datafeed import StockAResearchDatafeed
from vnpy.research.stock_a.sources.xt import XtHistorySource, normalize_cn_datetime


class FakeXtDatafeed:
    def __init__(self, bars: list[BarData]) -> None:
        self.bars = bars
        self.requests: list[HistoryRequest] = []
        self.inited: bool = False

    def init(self) -> bool:
        self.inited = True
        return True

    def query_bar_history(self, req: HistoryRequest) -> list[BarData]:
        self.requests.append(req)
        return list(self.bars)


class FakeSource:
    def __init__(self, bars: list[BarData]) -> None:
        self.bars = bars
        self.requests: list[HistoryRequest] = []

    def query_bar_history(self, req: HistoryRequest) -> list[BarData]:
        self.requests.append(req)
        return list(self.bars)


def test_normalize_cn_datetime_returns_local_naive_time() -> None:
    dt = datetime(2024, 1, 2, 9, 31, tzinfo=ZoneInfo("Asia/Shanghai"))

    assert normalize_cn_datetime(dt) == datetime(2024, 1, 2, 9, 31)


def test_xt_history_source_converts_xt_bar_datetimes_to_local_naive() -> None:
    bar = BarData(
        symbol="600000",
        exchange=Exchange.SSE,
        datetime=datetime(2024, 1, 2, 9, 31, tzinfo=ZoneInfo("Asia/Shanghai")),
        interval=Interval.MINUTE,
        open_price=10.0,
        high_price=10.2,
        low_price=9.9,
        close_price=10.1,
        volume=1000,
        turnover=10100,
        gateway_name="XT",
    )
    xt_datafeed = FakeXtDatafeed([bar])

    source = XtHistorySource(xt_datafeed=xt_datafeed)

    req = HistoryRequest(
        symbol="600000",
        exchange=Exchange.SSE,
        interval=Interval.MINUTE,
        start=datetime(2024, 1, 2, 9, 31),
        end=datetime(2024, 1, 2, 9, 31),
    )
    bars = source.query_bar_history(req)

    assert len(bars) == 1
    assert bars[0].datetime == datetime(2024, 1, 2, 9, 31)
    assert bars[0].datetime.tzinfo is None


def test_stock_a_research_datafeed_delegates_history_requests() -> None:
    bar = BarData(
        symbol="600000",
        exchange=Exchange.SSE,
        datetime=datetime(2024, 1, 2, 9, 31),
        interval=Interval.MINUTE,
        open_price=10.0,
        high_price=10.2,
        low_price=9.9,
        close_price=10.1,
        volume=1000,
        turnover=10100,
        gateway_name="XT",
    )
    source = FakeSource([bar])
    datafeed = StockAResearchDatafeed(source=source, backend="xt")

    req = HistoryRequest(
        symbol="600000",
        exchange=Exchange.SSE,
        interval=Interval.MINUTE,
        start=datetime(2024, 1, 2, 9, 31),
        end=datetime(2024, 1, 2, 9, 31),
    )
    bars = datafeed.query_bar_history(req)

    assert len(bars) == 1
    assert source.requests == [req]
    assert bars[0].vt_symbol == "600000.SSE"


def test_from_backend_rejects_unimplemented_db_backend() -> None:
    with pytest.raises(ValueError, match="unsupported history backend: db"):
        StockAResearchDatafeed.from_backend("db")
