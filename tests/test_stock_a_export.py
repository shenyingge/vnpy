from datetime import datetime
from typing import Callable

from vnpy.alpha import AlphaLab
from vnpy.research.stock_a.datafeed import StockAResearchDatafeed
from vnpy.research.stock_a.export import import_bar_histories, import_bar_history
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData, HistoryRequest


class FakeSource:
    def __init__(
        self,
        bars: list[BarData] | None = None,
        bars_by_request: dict[tuple[str, datetime, datetime], list[BarData]] | None = None,
    ) -> None:
        self.bars = bars or []
        self.bars_by_request = bars_by_request or {}
        self.requests: list[HistoryRequest] = []
        self.outputs: list[Callable] = []

    def query_bar_history(self, req: HistoryRequest, output=print) -> list[BarData]:
        self.requests.append(req)
        self.outputs.append(output)

        key = (req.vt_symbol, req.start, req.end)
        bars = self.bars_by_request.get(key, self.bars)
        return list(bars)


def make_bar(dt: datetime, close_price: float) -> BarData:
    return BarData(
        symbol="600000",
        exchange=Exchange.SSE,
        datetime=dt,
        interval=Interval.MINUTE,
        open_price=10.0,
        high_price=10.2,
        low_price=9.9,
        close_price=close_price,
        volume=1000,
        turnover=close_price * 1000,
        gateway_name="XT",
    )


def test_import_bar_history_saves_xt_bars_into_alphalab(tmp_path) -> None:
    lab = AlphaLab(str(tmp_path))
    bars = [
        make_bar(datetime(2024, 1, 2, 9, 30), 10.1),
        make_bar(datetime(2024, 1, 2, 9, 31), 10.2),
    ]
    source = FakeSource(bars)
    datafeed = StockAResearchDatafeed(source=source)
    req = HistoryRequest(
        symbol="600000",
        exchange=Exchange.SSE,
        interval=Interval.MINUTE,
        start=datetime(2024, 1, 2, 9, 30),
        end=datetime(2024, 1, 2, 9, 31),
    )
    output = lambda message: None

    saved = import_bar_history(lab, datafeed, req, output=output)
    loaded = lab.load_bar_data(
        "600000.SSE",
        Interval.MINUTE,
        datetime(2024, 1, 2, 9, 30),
        datetime(2024, 1, 2, 9, 31),
    )

    assert saved == 2
    assert [bar.close_price for bar in loaded] == [10.1, 10.2]
    assert source.requests == [req]
    assert source.outputs == [output]


def test_import_bar_histories_accumulates_counts_by_vt_symbol(tmp_path) -> None:
    lab = AlphaLab(str(tmp_path))
    first_req = HistoryRequest(
        symbol="600000",
        exchange=Exchange.SSE,
        interval=Interval.MINUTE,
        start=datetime(2024, 1, 2, 9, 30),
        end=datetime(2024, 1, 2, 9, 30),
    )
    second_req = HistoryRequest(
        symbol="600000",
        exchange=Exchange.SSE,
        interval=Interval.MINUTE,
        start=datetime(2024, 1, 2, 9, 31),
        end=datetime(2024, 1, 2, 9, 32),
    )
    source = FakeSource(
        bars_by_request={
            (first_req.vt_symbol, first_req.start, first_req.end): [
                make_bar(datetime(2024, 1, 2, 9, 30), 10.1)
            ],
            (second_req.vt_symbol, second_req.start, second_req.end): [
                make_bar(datetime(2024, 1, 2, 9, 31), 10.2),
                make_bar(datetime(2024, 1, 2, 9, 32), 10.3),
            ],
        }
    )
    datafeed = StockAResearchDatafeed(source=source)
    requests = [
        first_req,
        second_req,
    ]

    result = import_bar_histories(lab, datafeed, requests)

    assert result == {"600000.SSE": 3}
    assert source.requests == [first_req, second_req]
