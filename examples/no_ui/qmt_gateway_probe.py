from __future__ import annotations

from dataclasses import dataclass
import argparse
import json
from pathlib import Path
import sys
import time


PROJECT_ROOT = Path(__file__).resolve().parents[2]
VENDOR_QMT_ROOT = PROJECT_ROOT / "vendor" / "vnpy_qmt"
if str(VENDOR_QMT_ROOT) not in sys.path:
    sys.path.insert(0, str(VENDOR_QMT_ROOT))


@dataclass(slots=True)
class ProbeConfig:
    gateway_name: str
    account: str
    mini_path: str
    session_id: int | None = None
    enable_md: bool = False
    preload_contracts: bool = False
    wait_seconds: float = 3.0


def load_probe_config(path: Path) -> ProbeConfig:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return ProbeConfig(
        gateway_name=raw.get("gateway_name", "QMT"),
        account=raw["account"],
        mini_path=raw["mini_path"],
        session_id=raw.get("session_id"),
        enable_md=bool(raw.get("enable_md", False)),
        preload_contracts=bool(raw.get("preload_contracts", False)),
        wait_seconds=float(raw.get("wait_seconds", 3.0)),
    )


def build_gateway_setting(config: ProbeConfig) -> dict[str, object]:
    return {
        "交易账号": config.account,
        "mini路径": config.mini_path,
        "会话编号": config.session_id or 0,
        "启用行情": config.enable_md,
        "预加载合约": config.preload_contracts,
    }


def run_probe(config: ProbeConfig) -> int:
    from vnpy.event import EventEngine
    from vnpy.trader.engine import MainEngine
    from vnpy_qmt.qmt_gateway import QmtGateway

    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)

    try:
        main_engine.add_gateway(QmtGateway, gateway_name=config.gateway_name)
        main_engine.connect(build_gateway_setting(config), config.gateway_name)
        time.sleep(config.wait_seconds)

        gateway = main_engine.get_gateway(config.gateway_name)
        if gateway is None:
            raise RuntimeError(f"gateway not found: {config.gateway_name}")

        gateway.query_account()
        gateway.query_position()
        gateway.query_order()
        gateway.query_trade()
        time.sleep(config.wait_seconds)
    finally:
        main_engine.close()

    print("QMT probe completed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only probe for local vnpy_qmt gateway.")
    parser.add_argument("--config", required=True, help="Path to probe json config.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    config = load_probe_config(Path(args.config))
    return run_probe(config)


if __name__ == "__main__":
    raise SystemExit(main())
