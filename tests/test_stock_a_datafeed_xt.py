from datetime import datetime
from types import ModuleType
from zoneinfo import ZoneInfo
import sys

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
        self.init_output = None
        self.query_outputs: list[object] = []

    def init(self, output=print) -> bool:
        self.inited = True
        self.init_output = output
        return True

    def query_bar_history(self, req: HistoryRequest, output=print) -> list[BarData]:
        self.requests.append(req)
        self.query_outputs.append(output)
        return list(self.bars)


class FakeSource:
    def __init__(self, bars: list[BarData]) -> None:
        self.bars = bars
        self.requests: list[HistoryRequest] = []
        self.query_outputs: list[object] = []
        self.init_output = None

    def init(self, output=print) -> bool:
        self.init_output = output
        return True

    def query_bar_history(self, req: HistoryRequest, output=print) -> list[BarData]:
        self.requests.append(req)
        self.query_outputs.append(output)
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
    bar.extra = {"source": "xt"}
    xt_datafeed = FakeXtDatafeed([bar])
    output = object()

    source = XtHistorySource(xt_datafeed=xt_datafeed)

    req = HistoryRequest(
        symbol="600000",
        exchange=Exchange.SSE,
        interval=Interval.MINUTE,
        start=datetime(2024, 1, 2, 9, 31),
        end=datetime(2024, 1, 2, 9, 31),
    )
    bars = source.query_bar_history(req, output=output)

    assert len(bars) == 1
    assert bars[0].datetime == datetime(2024, 1, 2, 9, 31)
    assert bars[0].datetime.tzinfo is None
    assert bars[0] is not bar
    assert bar.datetime.tzinfo == ZoneInfo("Asia/Shanghai")
    assert bars[0].extra == {"source": "xt"}
    assert xt_datafeed.query_outputs == [output]


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
    output = object()

    req = HistoryRequest(
        symbol="600000",
        exchange=Exchange.SSE,
        interval=Interval.MINUTE,
        start=datetime(2024, 1, 2, 9, 31),
        end=datetime(2024, 1, 2, 9, 31),
    )
    bars = datafeed.query_bar_history(req, output=output)

    assert len(bars) == 1
    assert source.requests == [req]
    assert source.query_outputs == [output]
    assert bars[0].vt_symbol == "600000.SSE"


def test_stock_a_research_datafeed_init_delegates_to_source() -> None:
    source = FakeSource([])
    datafeed = StockAResearchDatafeed(source=source, backend="xt")
    output = object()

    assert datafeed.init(output=output) is True
    assert source.init_output is output


def test_from_backend_xt_uses_real_construction_path_and_init() -> None:
    fake_module = ModuleType("vnpy_xt.xt_datafeed")
    fake_package = ModuleType("vnpy_xt")
    fake_bar = BarData(
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

    class StubXtDatafeed(FakeXtDatafeed):
        def __init__(self) -> None:
            super().__init__([fake_bar])

    fake_module.XtDatafeed = StubXtDatafeed
    fake_package.xt_datafeed = fake_module

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setitem(sys.modules, "vnpy_xt", fake_package)
    monkeypatch.setitem(sys.modules, "vnpy_xt.xt_datafeed", fake_module)

    try:
        datafeed = StockAResearchDatafeed.from_backend("xt")
        output = object()

        assert datafeed.init(output=output) is True
        assert isinstance(datafeed.source, XtHistorySource)
        assert datafeed.source.xt_datafeed.inited is True
        assert datafeed.source.xt_datafeed.init_output is output

        req = HistoryRequest(
            symbol="600000",
            exchange=Exchange.SSE,
            interval=Interval.MINUTE,
            start=datetime(2024, 1, 2, 9, 31),
            end=datetime(2024, 1, 2, 9, 31),
        )
        bars = datafeed.query_bar_history(req, output=output)

        assert len(bars) == 1
        assert bars[0].datetime == datetime(2024, 1, 2, 9, 31)
        assert datafeed.source.xt_datafeed.query_outputs == [output]
    finally:
        monkeypatch.undo()


def test_from_backend_rejects_unimplemented_db_backend() -> None:
    with pytest.raises(ValueError, match="unsupported history backend: db"):
        StockAResearchDatafeed.from_backend("db")
