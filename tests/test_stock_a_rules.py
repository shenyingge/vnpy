from datetime import datetime

import pytest

from vnpy.research.stock_a.rules import (
    StockARuleConfig,
    calculate_sellable_volume,
    can_sell,
    estimate_trade_cost,
    is_trading_minute,
    round_lot,
)
from vnpy.trader.constant import Direction, Exchange
from vnpy.trader.object import PositionData


def test_round_lot_rounds_down_to_lot_size() -> None:
    assert round_lot(253) == 200
    assert round_lot(99) == 0


def test_calculate_sellable_volume_uses_position_and_freeze_constraints() -> None:
    position = PositionData(
        symbol="600000",
        exchange=Exchange.SSE,
        direction=Direction.LONG,
        volume=1300,
        yd_volume=900,
        frozen=150,
        gateway_name="XT",
    )

    assert calculate_sellable_volume(position) == 700


def test_can_sell_validates_requested_volume_after_rounding() -> None:
    position = PositionData(
        symbol="600000",
        exchange=Exchange.SSE,
        direction=Direction.LONG,
        volume=1000,
        yd_volume=1000,
        frozen=100,
        gateway_name="XT",
    )

    assert can_sell(position, 900) is True
    assert can_sell(position, 1000) is False


def test_is_trading_minute_matches_a_share_sessions() -> None:
    assert is_trading_minute(datetime(2024, 1, 2, 9, 30)) is True
    assert is_trading_minute(datetime(2024, 1, 2, 11, 29)) is True
    assert is_trading_minute(datetime(2024, 1, 2, 11, 30)) is False
    assert is_trading_minute(datetime(2024, 1, 2, 13, 0)) is True
    assert is_trading_minute(datetime(2024, 1, 2, 15, 0)) is False


def test_estimate_trade_cost_buy_and_sell_breakdown() -> None:
    config = StockARuleConfig(
        commission_rate=0.0003,
        transfer_rate=0.00001,
        stamp_tax_rate=0.001,
        min_commission=5.0,
    )

    buy_cost = estimate_trade_cost(10.0, 1000, Direction.LONG, config)
    sell_cost = estimate_trade_cost(10.0, 1000, Direction.SHORT, config)

    assert buy_cost.commission == pytest.approx(5.0)
    assert buy_cost.transfer_fee == pytest.approx(0.10)
    assert buy_cost.stamp_tax == pytest.approx(0.0)
    assert buy_cost.total == pytest.approx(5.10)

    assert sell_cost.commission == pytest.approx(5.0)
    assert sell_cost.transfer_fee == pytest.approx(0.10)
    assert sell_cost.stamp_tax == pytest.approx(10.0)
    assert sell_cost.total == pytest.approx(15.10)
