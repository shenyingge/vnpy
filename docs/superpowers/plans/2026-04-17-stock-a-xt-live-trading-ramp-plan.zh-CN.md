# XT Stock-A Live Trading Ramp Implementation Plan

**Status:** 这份计划最初把自定义 `stock_a.live` 运行时写成了正式交易主边界。该方向现已判定与 `vnpy_qmt` 的 gateway 设计、以及后续继续使用 vn.py 自带界面的目标不一致。

**Correction:** 正式交易边界应保留为 `vnpy_qmt.QmtGateway`。如果实现有问题，应优先直接修改 `vendor/vnpy_qmt` 源码并重新打包安装。`probe`、`dry_run`、白名单、资金上限、确认闸门等能力应放在 gateway 外层，作为包装和辅助入口，而不是替代 gateway 本身。

**Execution Note:** 本文件下方的任务清单保留为历史草案，不能按原样直接执行。后续若继续实现，需要先基于新的架构约束重写 implementation plan。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在当前已打通的 `xtquant -> vnpy_xt -> stock_a -> AlphaLab -> BacktestingEngine` 历史数据链路之上，建立一个按风险递增推进的实盘接入阶梯，同时保持 `vnpy_qmt` 作为正式 QMT gateway，并保留未来继续使用 vn.py 自带界面的能力。

**Architecture:** 历史数据继续使用现有 `vnpy_xt` 和研究链路；正式交易入口保留为 `vnpy_qmt.QmtGateway`，并继续兼容 vn.py 原生 `MainEngine/gateway/UI` 关系。安全控制、探活、dry_run、运行脚本、配置模板等能力放在 gateway 外层，作为包装层而不是替代层。

**Tech Stack:** Python 3.13, uv, pytest, vnpy_qmt, xtquant.xttrader, xtquant.xtdata, vnpy.trader.engine, vnpy.trader.gateway, dataclasses, argparse, JSON config

---

## 文件结构

## 更正后的执行原则

- `vnpy_qmt` 保持为正式 gateway，不绕开、不降级为纯参考实现。
- 如果 QMT 接入存在实现问题，优先直接修改 [`vendor/vnpy_qmt`](/C:/Users/sai/project/vnpy/.worktrees/xt-first/vendor/vnpy_qmt) 源码并重新打包。
- 外层只做安全包装、自动化脚本、配置模板和探活流程。
- 回测尽量贴近 vn.py 原生方案，不额外再发展一条平行交易主线。
- 下方旧任务清单仅供历史参考，不应直接进入执行。

### 需要新建的文件

- Create: `vnpy/research/stock_a/live/__init__.py`
- Create: `vnpy/research/stock_a/live/config.py`
- Create: `vnpy/research/stock_a/live/models.py`
- Create: `vnpy/research/stock_a/live/xt_trader.py`
- Create: `vnpy/research/stock_a/live/service.py`
- Create: `tests/test_stock_a_xt_live_config.py`
- Create: `tests/test_stock_a_xt_live_service.py`
- Create: `examples/no_ui/xt_stock_a_live.py`
- Create: `examples/no_ui/xt_stock_a_live.example.json`
- Create: `examples/no_ui/README_xt_stock_a_live.zh-CN.md`

### 需要修改的文件

- Modify: `vnpy/research/stock_a/__init__.py`

### 职责划分

- `config.py`：定义 live 模式配置模型、加载逻辑和安全校验。
- `models.py`：定义账户快照、持仓快照、委托草稿、dry_run 结果、探活结果等纯数据结构。
- `xt_trader.py`：包住 `xtquant.xttrader` 与 `xtquant.xttype.StockAccount`，提供可替换的薄适配器。
- `service.py`：编排只读联调、dry_run、仿真、最小真钱四种模式，集中处理安全闸门。
- `test_stock_a_xt_live_config.py`：覆盖配置解析、模式校验、最小真钱保护规则。
- `test_stock_a_xt_live_service.py`：用 fake trader 覆盖 probe、dry_run、simulate/live 分支。
- `xt_stock_a_live.py`：单文件 CLI，提供 `probe`、`order`、`cancel` 子命令。
- `README_xt_stock_a_live.zh-CN.md`：给出从 0 成本联调到最小真钱的运行手册。

## 约束和前提

- 历史数据和回测链路不重写，继续复用现有 `stock_a` 模块。
- 真实交易链路不和 `AlphaLab` 耦合，避免把回测目录逻辑硬塞进实盘。
- 默认模式必须是安全的：
  - 默认只读；
  - `dry_run` 下永不真实发单；
  - `live` 模式下没有显式确认标记就拒绝发单。
- “仿真模式”在代码里支持，但是否能真正跑通取决于国金证券/QMT 是否提供仿真账号或测试端。

## 配置模型

统一使用一个 live JSON 配置，包含三层：

1. XT 运行时
- `qmt_path`
- `stock_account`
- `session_id`
- `account_type`

2. 模式控制
- `mode`: `probe` / `dry_run` / `simulate` / `live`
- `enable_quote_subscribe`
- `confirm_live`
- `cash_limit`
- `symbol_allowlist`

3. 单笔指令模板
- `symbol`
- `direction`
- `volume`
- `price_type`
- `limit_price`

## 执行顺序

按用户要求固定成四段：

1. 只读联调：连接、查账户、查持仓、可选订阅行情，不发单。
2. dry_run：完整走一遍“准备下单”的代码路径，但在最后一层明确拦截。
3. 仿真：只有在券商/QMT 提供仿真或测试环境时才启用；代码结构和 `live` 共用。
4. 最小真钱：在 `live` 模式下增加确认闸门、标的白名单、资金上限和日志留痕。

### Task 1: 建立 Live 配置模型和模式校验

**Files:**
- Create: `vnpy/research/stock_a/live/config.py`
- Create: `vnpy/research/stock_a/live/__init__.py`
- Modify: `vnpy/research/stock_a/__init__.py`
- Test: `tests/test_stock_a_xt_live_config.py`

- [ ] **Step 1: 写失败测试，覆盖配置默认值与模式校验**

```python
import json

import pytest

from vnpy.research.stock_a.live.config import LiveMode, load_xt_live_config


def test_load_xt_live_config_parses_probe_defaults(tmp_path) -> None:
    path = tmp_path / "live.json"
    path.write_text(
        json.dumps(
            {
                "qmt_path": "C:/QMT/userdata_mini",
                "stock_account": "12345678",
                "session_id": 1001
            }
        ),
        encoding="utf-8",
    )

    config = load_xt_live_config(path)

    assert config.mode is LiveMode.PROBE
    assert config.account_type == "STOCK"
    assert config.enable_quote_subscribe is False
    assert config.confirm_live is False
    assert config.cash_limit is None
    assert config.symbol_allowlist == []


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (
            {
                "qmt_path": "C:/QMT/userdata_mini",
                "stock_account": "12345678",
                "session_id": 1001,
                "mode": "live",
                "confirm_live": False,
            },
            "confirm_live",
        ),
        (
            {
                "qmt_path": "C:/QMT/userdata_mini",
                "stock_account": "12345678",
                "session_id": 0,
            },
            "session_id",
        ),
        (
            {
                "qmt_path": "C:/QMT/userdata_mini",
                "stock_account": "",
                "session_id": 1001,
            },
            "stock_account",
        ),
    ],
)
def test_load_xt_live_config_validates_safety_fields(tmp_path, payload, message) -> None:
    path = tmp_path / "live.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        load_xt_live_config(path)
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `uv run pytest tests/test_stock_a_xt_live_config.py -v`

Expected: FAIL，提示 `ModuleNotFoundError` 或 `cannot import name 'load_xt_live_config'`

- [ ] **Step 3: 实现最小配置模型**

```python
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json


class LiveMode(str, Enum):
    PROBE = "probe"
    DRY_RUN = "dry_run"
    SIMULATE = "simulate"
    LIVE = "live"


@dataclass(slots=True)
class XtLiveConfig:
    qmt_path: Path
    stock_account: str
    session_id: int
    account_type: str = "STOCK"
    mode: LiveMode = LiveMode.PROBE
    enable_quote_subscribe: bool = False
    confirm_live: bool = False
    cash_limit: float | None = None
    symbol_allowlist: list[str] = field(default_factory=list)
    symbol: str | None = None
    direction: str | None = None
    volume: int | None = None
    price_type: str = "latest"
    limit_price: float | None = None

    def __post_init__(self) -> None:
        self.qmt_path = Path(self.qmt_path)
        if self.session_id <= 0:
            raise ValueError("session_id must be > 0")
        if not self.stock_account.strip():
            raise ValueError("stock_account must not be blank")
        if self.mode is LiveMode.LIVE and not self.confirm_live:
            raise ValueError("confirm_live must be true when mode='live'")


def load_xt_live_config(config_path: Path) -> XtLiveConfig:
    raw = json.loads(Path(config_path).read_text(encoding="utf-8"))
    return XtLiveConfig(
        qmt_path=raw["qmt_path"],
        stock_account=raw["stock_account"],
        session_id=int(raw["session_id"]),
        account_type=raw.get("account_type", "STOCK"),
        mode=LiveMode(raw.get("mode", "probe")),
        enable_quote_subscribe=bool(raw.get("enable_quote_subscribe", False)),
        confirm_live=bool(raw.get("confirm_live", False)),
        cash_limit=raw.get("cash_limit"),
        symbol_allowlist=list(raw.get("symbol_allowlist", [])),
        symbol=raw.get("symbol"),
        direction=raw.get("direction"),
        volume=raw.get("volume"),
        price_type=raw.get("price_type", "latest"),
        limit_price=raw.get("limit_price"),
    )
```

- [ ] **Step 4: 暴露公共导出**

```python
from .config import LiveMode, XtLiveConfig, load_xt_live_config


__all__ = [
    "LiveMode",
    "XtLiveConfig",
    "load_xt_live_config",
]
```

```python
from .live import LiveMode, XtLiveConfig, load_xt_live_config
```

- [ ] **Step 5: 运行测试，确认通过**

Run: `uv run pytest tests/test_stock_a_xt_live_config.py -v`

Expected: PASS，2 个测试通过

- [ ] **Step 6: 提交**

```bash
git add vnpy/research/stock_a/live/__init__.py vnpy/research/stock_a/live/config.py vnpy/research/stock_a/__init__.py tests/test_stock_a_xt_live_config.py
git commit -m "feat: add xt live trading config model"
```

### Task 2: 实现只读联调链路

**Files:**
- Create: `vnpy/research/stock_a/live/models.py`
- Create: `vnpy/research/stock_a/live/xt_trader.py`
- Create: `vnpy/research/stock_a/live/service.py`
- Test: `tests/test_stock_a_xt_live_service.py`

- [ ] **Step 1: 写失败测试，覆盖 probe 模式不发单**

```python
from dataclasses import dataclass

from vnpy.research.stock_a.live.config import XtLiveConfig
from vnpy.research.stock_a.live.service import XtLiveService


@dataclass
class FakeTrader:
    connected: bool = False
    sent_orders: list = None

    def __post_init__(self) -> None:
        self.sent_orders = []

    def connect(self) -> None:
        self.connected = True

    def query_asset(self) -> dict:
        return {"cash": 100000.0}

    def query_positions(self) -> list[dict]:
        return [{"symbol": "601138.SH", "volume": 0}]

    def send_order(self, order) -> str:
        self.sent_orders.append(order)
        return "ORDER-1"


def test_probe_returns_snapshot_without_sending_orders(tmp_path) -> None:
    config = XtLiveConfig(
        qmt_path=tmp_path / "userdata_mini",
        stock_account="12345678",
        session_id=1001,
    )
    trader = FakeTrader()
    service = XtLiveService(config=config, trader=trader)

    result = service.probe()

    assert trader.connected is True
    assert result.asset["cash"] == 100000.0
    assert len(result.positions) == 1
    assert trader.sent_orders == []
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `uv run pytest tests/test_stock_a_xt_live_service.py::test_probe_returns_snapshot_without_sending_orders -v`

Expected: FAIL，提示 `ModuleNotFoundError` 或 `cannot import name 'XtLiveService'`

- [ ] **Step 3: 实现只读模型与 trader 适配器骨架**

```python
from dataclasses import dataclass


@dataclass(slots=True)
class ProbeResult:
    asset: dict
    positions: list[dict]
```

```python
from xtquant.xttrader import XtQuantTrader
from xtquant.xttype import StockAccount


class XtTraderAdapter:
    def __init__(self, qmt_path: str, session_id: int, stock_account: str) -> None:
        self.qmt_path = qmt_path
        self.session_id = session_id
        self.stock_account = stock_account
        self.trader = XtQuantTrader(qmt_path, session_id)
        self.account = StockAccount(stock_account)

    def connect(self) -> None:
        self.trader.start()
        self.trader.connect()

    def query_asset(self) -> dict:
        return self.trader.query_stock_asset(self.account)

    def query_positions(self) -> list[dict]:
        return self.trader.query_stock_positions(self.account)
```

```python
from .models import ProbeResult
from .xt_trader import XtTraderAdapter


class XtLiveService:
    def __init__(self, config, trader) -> None:
        self.config = config
        self.trader = trader

    def probe(self) -> ProbeResult:
        self.trader.connect()
        asset = self.trader.query_asset()
        positions = self.trader.query_positions()
        return ProbeResult(asset=asset, positions=positions)
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `uv run pytest tests/test_stock_a_xt_live_service.py::test_probe_returns_snapshot_without_sending_orders -v`

Expected: PASS

- [ ] **Step 5: 增加只读联调 CLI**

```python
import argparse
from pathlib import Path

from vnpy.research.stock_a.live import load_xt_live_config
from vnpy.research.stock_a.live.service import XtLiveService
from vnpy.research.stock_a.live.xt_trader import XtTraderAdapter


def run_probe(config_path: str) -> None:
    config = load_xt_live_config(Path(config_path))
    trader = XtTraderAdapter(str(config.qmt_path), config.session_id, config.stock_account)
    service = XtLiveService(config=config, trader=trader)
    result = service.probe()
    print(result)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--mode", choices=["probe"], default="probe")
    args = parser.parse_args()
    run_probe(args.config)
```

- [ ] **Step 6: 提交**

```bash
git add vnpy/research/stock_a/live/models.py vnpy/research/stock_a/live/xt_trader.py vnpy/research/stock_a/live/service.py tests/test_stock_a_xt_live_service.py examples/no_ui/xt_stock_a_live.py
git commit -m "feat: add xt live probe flow"
```

### Task 3: 实现 dry_run 下单路径

**Files:**
- Modify: `vnpy/research/stock_a/live/models.py`
- Modify: `vnpy/research/stock_a/live/service.py`
- Test: `tests/test_stock_a_xt_live_service.py`

- [ ] **Step 1: 写失败测试，覆盖 dry_run 拦截**

```python
from vnpy.research.stock_a.live.config import LiveMode, XtLiveConfig
from vnpy.research.stock_a.live.service import XtLiveService


def test_dry_run_builds_order_but_never_calls_send_order(tmp_path) -> None:
    config = XtLiveConfig(
        qmt_path=tmp_path / "userdata_mini",
        stock_account="12345678",
        session_id=1001,
        mode=LiveMode.DRY_RUN,
        symbol="601138.SH",
        direction="buy",
        volume=100,
    )
    trader = FakeTrader()
    service = XtLiveService(config=config, trader=trader)

    result = service.place_order()

    assert result.mode == "dry_run"
    assert result.order_sent is False
    assert result.symbol == "601138.SH"
    assert trader.sent_orders == []
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `uv run pytest tests/test_stock_a_xt_live_service.py::test_dry_run_builds_order_but_never_calls_send_order -v`

Expected: FAIL，提示 `AttributeError: 'XtLiveService' object has no attribute 'place_order'`

- [ ] **Step 3: 实现 dry_run 结果模型与下单分支**

```python
from dataclasses import dataclass


@dataclass(slots=True)
class OrderAttempt:
    mode: str
    symbol: str
    direction: str
    volume: int
    order_sent: bool
    broker_order_id: str | None
```

```python
from .models import OrderAttempt


class XtLiveService:
    ...

    def place_order(self) -> OrderAttempt:
        if not self.config.symbol or not self.config.direction or not self.config.volume:
            raise ValueError("symbol/direction/volume are required for order path")

        if self.config.mode.value == "dry_run":
            return OrderAttempt(
                mode="dry_run",
                symbol=self.config.symbol,
                direction=self.config.direction,
                volume=self.config.volume,
                order_sent=False,
                broker_order_id=None,
            )

        raise RuntimeError("place_order not implemented for this mode yet")
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `uv run pytest tests/test_stock_a_xt_live_service.py::test_dry_run_builds_order_but_never_calls_send_order -v`

Expected: PASS

- [ ] **Step 5: 扩展 CLI 支持 dry_run**

```python
parser.add_argument("--action", choices=["probe", "order"], default="probe")
...
if args.action == "order":
    result = service.place_order()
    print(result)
```

- [ ] **Step 6: 提交**

```bash
git add vnpy/research/stock_a/live/models.py vnpy/research/stock_a/live/service.py tests/test_stock_a_xt_live_service.py examples/no_ui/xt_stock_a_live.py
git commit -m "feat: add xt live dry-run order flow"
```

### Task 4: 实现仿真和最小真钱的统一下单闸门

**Files:**
- Modify: `vnpy/research/stock_a/live/service.py`
- Modify: `vnpy/research/stock_a/live/xt_trader.py`
- Test: `tests/test_stock_a_xt_live_service.py`

- [ ] **Step 1: 写失败测试，覆盖 live 模式必须过安全门**

```python
import pytest

from vnpy.research.stock_a.live.config import LiveMode, XtLiveConfig
from vnpy.research.stock_a.live.service import XtLiveService


def test_live_mode_rejects_order_when_symbol_not_in_allowlist(tmp_path) -> None:
    config = XtLiveConfig(
        qmt_path=tmp_path / "userdata_mini",
        stock_account="12345678",
        session_id=1001,
        mode=LiveMode.LIVE,
        confirm_live=True,
        symbol_allowlist=["600000.SH"],
        symbol="601138.SH",
        direction="buy",
        volume=100,
    )
    service = XtLiveService(config=config, trader=FakeTrader())

    with pytest.raises(ValueError, match="symbol_allowlist"):
        service.place_order()


def test_simulate_mode_calls_send_order_when_explicitly_enabled(tmp_path) -> None:
    config = XtLiveConfig(
        qmt_path=tmp_path / "userdata_mini",
        stock_account="12345678",
        session_id=1001,
        mode=LiveMode.SIMULATE,
        symbol="601138.SH",
        direction="buy",
        volume=100,
    )
    trader = FakeTrader()
    service = XtLiveService(config=config, trader=trader)

    result = service.place_order()

    assert result.order_sent is True
    assert result.broker_order_id == "ORDER-1"
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `uv run pytest tests/test_stock_a_xt_live_service.py -k "allowlist or simulate" -v`

Expected: FAIL，提示安全校验缺失或 `RuntimeError("place_order not implemented")`

- [ ] **Step 3: 实现统一下单闸门**

```python
class XtLiveService:
    ...

    def _validate_order_guard(self) -> None:
        if self.config.mode.value == "live":
            if self.config.symbol_allowlist and self.config.symbol not in self.config.symbol_allowlist:
                raise ValueError("symbol_allowlist rejected current symbol")
            if self.config.cash_limit is not None and self.config.limit_price is not None:
                order_value = self.config.limit_price * self.config.volume
                if order_value > self.config.cash_limit:
                    raise ValueError("cash_limit exceeded")

    def place_order(self) -> OrderAttempt:
        ...
        if self.config.mode.value in {"simulate", "live"}:
            self._validate_order_guard()
            order_id = self.trader.send_order(
                {
                    "symbol": self.config.symbol,
                    "direction": self.config.direction,
                    "volume": self.config.volume,
                    "price_type": self.config.price_type,
                    "limit_price": self.config.limit_price,
                }
            )
            return OrderAttempt(
                mode=self.config.mode.value,
                symbol=self.config.symbol,
                direction=self.config.direction,
                volume=self.config.volume,
                order_sent=True,
                broker_order_id=order_id,
            )
```

- [ ] **Step 4: 为 trader 适配器补 send_order/cancel_order 骨架**

```python
class XtTraderAdapter:
    ...

    def send_order(self, order: dict) -> str:
        raise NotImplementedError("map order dict into xtquant order request here")

    def cancel_order(self, broker_order_id: str) -> None:
        raise NotImplementedError("map broker order id into xtquant cancel request here")
```

- [ ] **Step 5: 运行测试，确认通过**

Run: `uv run pytest tests/test_stock_a_xt_live_service.py -v`

Expected: PASS，probe/dry_run/simulate/live 安全测试全部通过

- [ ] **Step 6: 提交**

```bash
git add vnpy/research/stock_a/live/service.py vnpy/research/stock_a/live/xt_trader.py tests/test_stock_a_xt_live_service.py
git commit -m "feat: add xt simulate and live order guards"
```

### Task 5: 增加运行模板和风险递增手册

**Files:**
- Create: `examples/no_ui/xt_stock_a_live.example.json`
- Create: `examples/no_ui/README_xt_stock_a_live.zh-CN.md`
- Modify: `examples/no_ui/xt_stock_a_live.py`

- [ ] **Step 1: 写模板配置**

```json
{
  "qmt_path": "C:\\QMT\\userdata_mini",
  "stock_account": "12345678",
  "session_id": 1001,
  "account_type": "STOCK",
  "mode": "probe",
  "enable_quote_subscribe": false,
  "confirm_live": false,
  "cash_limit": 3000,
  "symbol_allowlist": ["601138.SH"],
  "symbol": "601138.SH",
  "direction": "buy",
  "volume": 100,
  "price_type": "latest",
  "limit_price": null
}
```

- [ ] **Step 2: 写手册，按四段推进**

```markdown
# XT A股实盘接入阶梯说明

## 第 1 步：只读联调

```powershell
uv run python examples/no_ui/xt_stock_a_live.py --config examples/no_ui/xt_stock_a_live.local.json --action probe
```

预期：
- 能连接 QMT
- 能看到账户资产
- 能看到持仓
- 不发单

## 第 2 步：dry_run

把 `mode` 改成 `dry_run`，执行：

```powershell
uv run python examples/no_ui/xt_stock_a_live.py --config examples/no_ui/xt_stock_a_live.local.json --action order
```

预期：
- 能走完整下单前校验
- 打印订单草稿
- 不真实发单

## 第 3 步：仿真

只有拿到券商仿真环境时才执行。把 `mode` 改成 `simulate`。

## 第 4 步：最小真钱

只有在前 3 步全部稳定后再执行：
- `mode = live`
- `confirm_live = true`
- 白名单只保留 1 个标的
- `cash_limit` 设成你愿意承担的最小金额
```
```

- [ ] **Step 3: 运行 CLI 帮助命令**

Run: `uv run python examples/no_ui/xt_stock_a_live.py --help`

Expected: PASS，展示 `--config` 和 `--action`

- [ ] **Step 4: 运行配置相关测试**

Run: `uv run pytest tests/test_stock_a_xt_live_config.py tests/test_stock_a_xt_live_service.py -v`

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add examples/no_ui/xt_stock_a_live.py examples/no_ui/xt_stock_a_live.example.json examples/no_ui/README_xt_stock_a_live.zh-CN.md
git commit -m "docs: add xt live trading ramp guide"
```

## 自检

### 规格覆盖

- 只读联调：Task 2
- dry_run：Task 3
- 仿真：Task 4
- 最小真钱：Task 4、Task 5
- 风险递增手册：Task 5
- 与现有 research 链路解耦：文件结构与 Task 1-4

### 占位符检查

- 没有 `TODO`
- 没有 `TBD`
- 没有“后续补上”式空步骤
- 每个任务都有明确命令
- 每个代码步骤都给出最小骨架

### 类型一致性

- 配置统一使用 `XtLiveConfig`
- 模式统一使用 `LiveMode`
- 只读结果统一使用 `ProbeResult`
- 下单结果统一使用 `OrderAttempt`
