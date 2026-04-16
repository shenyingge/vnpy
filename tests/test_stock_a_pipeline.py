from datetime import datetime

import vnpy.research.stock_a as stock_a
from vnpy.alpha import AlphaLab, BacktestingEngine
from vnpy.research.stock_a import StockAResearchDatafeed, import_bar_history
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData, HistoryRequest


class FakeSource:
    def __init__(self, bars: list[BarData]) -> None:
        self.bars = bars

    def query_bar_history(self, req: HistoryRequest, output=print) -> list[BarData]:
        return list(self.bars)


def test_stock_a_public_api_exports_history_backend_config() -> None:
    assert hasattr(stock_a, "StockAHistoryBackendConfig")


def test_xt_first_research_pipeline_loads_imported_history_into_backtesting_engine(tmp_path) -> None:
    lab = AlphaLab(str(tmp_path))
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
    datafeed = StockAResearchDatafeed(source=FakeSource([bar]))
    req = HistoryRequest(
        symbol="600000",
        exchange=Exchange.SSE,
        interval=Interval.MINUTE,
        start=datetime(2024, 1, 2, 9, 31),
        end=datetime(2024, 1, 2, 9, 31),
    )

    imported = import_bar_history(lab, datafeed, req)
    assert imported == 1

    lab.add_contract_setting(
        "600000.SSE",
        long_rate=0.0003,
        short_rate=0.0013,
        size=1,
        pricetick=0.01,
    )

    engine = BacktestingEngine(lab)
    engine.set_parameters(
        vt_symbols=["600000.SSE"],
        interval=Interval.MINUTE,
        start=datetime(2024, 1, 2, 9, 30),
        end=datetime(2024, 1, 2, 9, 32),
    )
    engine.load_data()

    key = (bar.datetime, "600000.SSE")
    assert key in engine.history_data
    assert engine.history_data[key].close_price == bar.close_price
