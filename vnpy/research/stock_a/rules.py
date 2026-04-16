"""A-share trading rule helpers based on PositionData semantics."""

from dataclasses import dataclass
from datetime import datetime, time

from vnpy.trader.constant import Direction
from vnpy.trader.object import PositionData


@dataclass
class StockARuleConfig:
    lot_size: int = 100
    commission_rate: float = 0.0
    transfer_rate: float = 0.0
    stamp_tax_rate: float = 0.0
    min_commission: float = 0.0


@dataclass
class TradeCostBreakdown:
    commission: float
    transfer_fee: float
    stamp_tax: float
    total: float


def round_lot(volume: float, lot_size: int = 100) -> int:
    if volume <= 0 or lot_size <= 0:
        return 0

    return int(volume // lot_size) * lot_size


def calculate_sellable_volume(position: PositionData, lot_size: int = 100) -> int:
    base_sellable = max(min(position.volume, position.yd_volume) - position.frozen, 0)
    return round_lot(base_sellable, lot_size=lot_size)


def can_sell(position: PositionData, requested_volume: float, lot_size: int = 100) -> bool:
    rounded_requested = round_lot(requested_volume, lot_size=lot_size)
    if rounded_requested <= 0:
        return False

    return rounded_requested <= calculate_sellable_volume(position, lot_size=lot_size)


def is_trading_minute(dt: datetime) -> bool:
    minute = dt.time()
    return (time(9, 30) <= minute < time(11, 30)) or (time(13, 0) <= minute < time(15, 0))


def estimate_trade_cost(
    price: float, volume: float, direction: Direction, config: StockARuleConfig
) -> TradeCostBreakdown:
    turnover = price * volume

    commission = 0.0
    if turnover > 0:
        commission = max(turnover * config.commission_rate, config.min_commission)

    transfer_fee = turnover * config.transfer_rate
    stamp_tax = turnover * config.stamp_tax_rate if direction == Direction.SHORT else 0.0
    total = commission + transfer_fee + stamp_tax

    return TradeCostBreakdown(
        commission=commission,
        transfer_fee=transfer_fee,
        stamp_tax=stamp_tax,
        total=total,
    )
