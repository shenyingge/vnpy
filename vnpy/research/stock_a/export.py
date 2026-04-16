from vnpy.alpha import AlphaLab
from vnpy.trader.datafeed import BaseDatafeed
from vnpy.trader.object import HistoryRequest


def import_bar_history(
    lab: AlphaLab,
    datafeed: BaseDatafeed,
    req: HistoryRequest,
) -> int:
    bars = datafeed.query_bar_history(req)
    lab.save_bar_data(bars)
    return len(bars)


def import_bar_histories(
    lab: AlphaLab,
    datafeed: BaseDatafeed,
    requests: list[HistoryRequest],
) -> dict[str, int]:
    result: dict[str, int] = {}

    for req in requests:
        count = import_bar_history(lab, datafeed, req)
        result[req.vt_symbol] = count

    return result
