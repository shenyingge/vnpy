from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "examples" / "no_ui" / "qmt_gateway_probe.py"
SPEC = spec_from_file_location("qmt_gateway_probe", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

ProbeConfig = MODULE.ProbeConfig
load_probe_config = MODULE.load_probe_config
build_gateway_setting = MODULE.build_gateway_setting


def test_load_probe_config_parses_defaults(tmp_path) -> None:
    path = tmp_path / "probe.json"
    path.write_text(
        json.dumps(
            {
                "account": "12345678",
                "mini_path": "C:/QMT/userdata_mini",
            }
        ),
        encoding="utf-8",
    )

    config = load_probe_config(path)

    assert config.gateway_name == "QMT"
    assert config.account == "12345678"
    assert config.mini_path == "C:/QMT/userdata_mini"
    assert config.session_id is None
    assert config.enable_md is False
    assert config.preload_contracts is False
    assert config.wait_seconds == 3.0


def test_build_gateway_setting_maps_wrapper_fields() -> None:
    config = ProbeConfig(
        gateway_name="QMT",
        account="12345678",
        mini_path="C:/QMT/userdata_mini",
        session_id=9001,
        enable_md=True,
        preload_contracts=True,
        wait_seconds=1.5,
    )

    assert build_gateway_setting(config) == {
        "交易账号": "12345678",
        "mini路径": "C:/QMT/userdata_mini",
        "会话编号": 9001,
        "启用行情": True,
        "预加载合约": True,
    }
