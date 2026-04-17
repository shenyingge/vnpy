from pathlib import Path
import sys
import types

from vnpy.trader.constant import Exchange


def install_xtquant_stubs() -> None:
    xtconstant = types.SimpleNamespace(
        STOCK_BUY=23,
        STOCK_SELL=24,
        FIX_PRICE=11,
        LATEST_PRICE=5,
        ORDER_UNREPORTED=0,
        ORDER_WAIT_REPORTING=1,
        ORDER_REPORTED=2,
        ORDER_REPORTED_CANCEL=3,
        ORDER_PARTSUCC_CANCEL=4,
        ORDER_PART_CANCEL=5,
        ORDER_CANCELED=6,
        ORDER_PART_SUCC=7,
        ORDER_SUCCEEDED=8,
        ORDER_JUNK=9,
        ORDER_UNKNOWN=10,
    )

    xtquant = types.ModuleType("xtquant")
    xtdata = types.ModuleType("xtquant.xtdata")
    xtdata.subscribe_quote = lambda **kwargs: 1
    xtdata.unsubscribe_quote = lambda seq: None
    xtdata.get_stock_list_in_sector = lambda sector_name: []

    xttrader = types.ModuleType("xtquant.xttrader")

    class XtQuantTraderCallback:
        pass

    class XtQuantTrader:
        def __init__(self, path: str, session: int) -> None:
            self.path = path
            self.session = session
            self.started = False
            self.stopped = False
            self.connected = False
            self.callback = None

        def register_callback(self, callback) -> None:
            self.callback = callback

        def start(self) -> None:
            self.started = True

        def connect(self) -> int:
            self.connected = True
            return 0

        def subscribe(self, account) -> int:
            return 0

        def stop(self) -> None:
            self.stopped = True

    xttrader.XtQuantTraderCallback = XtQuantTraderCallback
    xttrader.XtQuantTrader = XtQuantTrader

    xttype = types.ModuleType("xtquant.xttype")

    class StockAccount:
        def __init__(self, account_id: str) -> None:
            self.account_id = account_id

    for name in [
        "XtTrade",
        "XtAsset",
        "XtOrder",
        "XtOrderError",
        "XtCreditOrder",
        "XtOrderResponse",
        "XtPosition",
        "XtCreditDeal",
        "XtCancelError",
        "XtCancelOrderResponse",
    ]:
        setattr(xttype, name, type(name, (), {}))

    xttype.StockAccount = StockAccount

    xtquant.xtdata = xtdata
    xtquant.xttrader = xttrader
    xtquant.xttype = xttype
    xtquant.xtconstant = xtconstant

    sys.modules["xtquant"] = xtquant
    sys.modules["xtquant.xtdata"] = xtdata
    sys.modules["xtquant.xttrader"] = xttrader
    sys.modules["xtquant.xttype"] = xttype


install_xtquant_stubs()

VENDOR_ROOT = Path(__file__).resolve().parents[1] / "vendor" / "vnpy_qmt"
if str(VENDOR_ROOT) not in sys.path:
    sys.path.insert(0, str(VENDOR_ROOT))

from vnpy_qmt.qmt_gateway import QmtGateway
from vnpy_qmt.td import TD
from vnpy_qmt.md import MD


class DummyEventEngine:
    def register(self, event_type, handler) -> None:
        self.last_registration = (event_type, handler)

    def put(self, event) -> None:
        self.last_event = event


class DummyGateway:
    def __init__(self) -> None:
        self.gateway_name = "QMT"
        self.logs: list[str] = []

    def write_log(self, message: str) -> None:
        self.logs.append(message)


def test_qmt_gateway_default_setting_exposes_runtime_controls() -> None:
    assert QmtGateway.default_setting["交易账号"] == ""
    assert QmtGateway.default_setting["mini路径"] == ""
    assert QmtGateway.default_setting["会话编号"] == 0
    assert QmtGateway.default_setting["启用行情"] is True
    assert QmtGateway.default_setting["预加载合约"] is False


def test_qmt_gateway_connect_can_skip_market_data(monkeypatch) -> None:
    gateway = QmtGateway(DummyEventEngine())
    calls: list[str] = []

    monkeypatch.setattr(gateway.td, "connect", lambda setting: calls.append("td"))
    monkeypatch.setattr(gateway.md, "connect", lambda setting: calls.append("md"))

    gateway.connect(
        {
            "交易账号": "12345678",
            "mini路径": "C:/QMT/userdata_mini",
            "会话编号": 9001,
            "启用行情": False,
            "预加载合约": False,
        }
    )

    assert calls == ["td"]


def test_qmt_gateway_subscribe_skips_md_when_market_data_disabled(monkeypatch) -> None:
    gateway = QmtGateway(DummyEventEngine())
    calls: list[str] = []

    monkeypatch.setattr(gateway.td, "connect", lambda setting: None)
    monkeypatch.setattr(gateway.md, "connect", lambda setting: None)
    monkeypatch.setattr(gateway.md, "subscribe", lambda req: calls.append("md_sub") or 1)

    gateway.connect(
        {
            "交易账号": "12345678",
            "mini路径": "C:/QMT/userdata_mini",
            "会话编号": 9001,
            "启用行情": False,
            "预加载合约": False,
        }
    )

    req = types.SimpleNamespace(symbol="000001", exchange="SZ")
    result = gateway.subscribe(req)

    assert result is None
    assert calls == []


def test_qmt_gateway_close_calls_md_and_td_close(monkeypatch) -> None:
    gateway = QmtGateway(DummyEventEngine())
    calls: list[str] = []

    monkeypatch.setattr(gateway.md, "close", lambda: calls.append("md"))
    monkeypatch.setattr(gateway.td, "close", lambda: calls.append("td"))

    gateway.close()

    assert calls == ["md", "td"]


def test_td_uses_explicit_session_id_when_provided() -> None:
    gateway = DummyGateway()
    td = TD(gateway)

    td.connect(
        {
            "交易账号": "12345678",
            "mini路径": "C:/QMT/userdata_mini",
            "会话编号": 9001,
        }
    )

    assert td.session_id == 9001
    assert td.inited is True
    assert td.trader.session == 9001


def test_md_connect_respects_preload_contract_flag(monkeypatch) -> None:
    md = MD(DummyGateway())
    calls: list[str] = []

    monkeypatch.setattr(md, "get_contract", lambda: calls.append("contracts"))

    md.connect({"预加载合约": False})
    assert calls == []

    md.connect({"预加载合约": True})
    assert calls == ["contracts"]


def test_md_subscribe_ignored_when_market_data_disabled(monkeypatch) -> None:
    md = MD(DummyGateway())
    md.enabled = False
    called = False

    def should_not_run(**kwargs):
        nonlocal called
        called = True
        return 1

    xtdata = sys.modules["xtquant.xtdata"]
    monkeypatch.setattr(xtdata, "subscribe_quote", should_not_run)

    req = types.SimpleNamespace(symbol="000001", exchange=Exchange.SZSE)
    result = md.subscribe(req)

    assert result is None
    assert called is False


def test_md_close_unsubscribes_recorded_sequences(monkeypatch) -> None:
    md = MD(DummyGateway())
    md.subscriptions.update({1001, 1002})
    calls: list[int] = []

    xtdata = sys.modules["xtquant.xtdata"]
    monkeypatch.setattr(xtdata, "unsubscribe_quote", lambda seq: calls.append(seq))

    md.close()

    assert sorted(calls) == [1001, 1002]
    assert md.subscriptions == set()


def test_td_close_handles_trader_with_stop_only() -> None:
    class TraderWithStop:
        def __init__(self) -> None:
            self.stop_called = False

        def stop(self) -> None:
            self.stop_called = True

    td = TD(DummyGateway())
    td.inited = True
    trader = TraderWithStop()
    td.trader = trader

    td.close()

    assert td.inited is False
    assert trader.stop_called is True


def test_td_close_handles_trader_with_disconnect_and_stop() -> None:
    class TraderWithDisconnectAndStop:
        def __init__(self) -> None:
            self.disconnect_called = False
            self.stop_called = False

        def disconnect(self) -> None:
            self.disconnect_called = True

        def stop(self) -> None:
            self.stop_called = True

    td = TD(DummyGateway())
    td.inited = True
    trader = TraderWithDisconnectAndStop()
    td.trader = trader

    td.close()

    assert td.inited is False
    assert trader.disconnect_called is True
    assert trader.stop_called is True


def test_td_on_stock_position_reports_without_preloaded_contract() -> None:
    class GatewayWithoutContract:
        gateway_name = "QMT"

        def __init__(self) -> None:
            self.positions = []

        def get_contract(self, vt_symbol):
            return None

        def on_position(self, position) -> None:
            self.positions.append(position)

        def write_log(self, message: str) -> None:
            pass

    gateway = GatewayWithoutContract()
    td = TD(gateway)

    position = types.SimpleNamespace(
        stock_code="000001.SZ",
        volume=100,
        yesterday_volume=80,
        open_price=10.0,
        market_value=1200.0,
    )

    td.on_stock_position(position)

    assert len(gateway.positions) == 1
    emitted = gateway.positions[0]
    assert emitted.symbol == "000001"
    assert emitted.exchange == Exchange.SZSE
    assert emitted.volume == 100
