from datetime import datetime

from vnpy.alpha import AlphaLab
from vnpy.research.stock_a.datafeed import StockAResearchDatafeed
from vnpy.research.stock_a.export import import_bar_histories, import_bar_history
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData, HistoryRequest


class FakeSource:
    def __init__(self, bars: list[BarData]) -> None:
        self.bars = bars

    def query_bar_history(self, req: HistoryRequest, output=print) -> list[BarData]:
        return list(self.bars)


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
    datafeed = StockAResearchDatafeed(source=FakeSource(bars))
    req = HistoryRequest(
        symbol="600000",
        exchange=Exchange.SSE,
        interval=Interval.MINUTE,
        start=datetime(2024, 1, 2, 9, 30),
        end=datetime(2024, 1, 2, 9, 31),
    )

    saved = import_bar_history(lab, datafeed, req)
    loaded = lab.load_bar_data(
        "600000.SSE",
        Interval.MINUTE,
        datetime(2024, 1, 2, 9, 30),
        datetime(2024, 1, 2, 9, 31),
    )

    assert saved == 2
    assert [bar.close_price for bar in loaded] == [10.1, 10.2]


def test_import_bar_histories_returns_counts_by_vt_symbol(tmp_path) -> None:
    lab = AlphaLab(str(tmp_path))
    bars = [make_bar(datetime(2024, 1, 2, 9, 30), 10.1)]
    datafeed = StockAResearchDatafeed(source=FakeSource(bars))
    requests = [
        HistoryRequest(
            symbol="600000",
            exchange=Exchange.SSE,
            interval=Interval.MINUTE,
            start=datetime(2024, 1, 2, 9, 30),
            end=datetime(2024, 1, 2, 9, 30),
        )
    ]

    result = import_bar_histories(lab, datafeed, requests)

    assert result == {"600000.SSE": 1}
