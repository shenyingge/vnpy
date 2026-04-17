# 本地 vnpy_qmt Gateway Probe 使用说明

## 目标与边界

本目录下的 probe 是本地 fork 的只读探活入口，用于连接与查询：

- 连接 QMT gateway
- 查询账户、持仓、委托、成交

它不会发送委托。**probe 是辅助入口，不替代 vn.py UI/gateway 正式边界**。

## 1. 安装本地 fork

在项目根目录执行：

```bash
uv pip install -U ./vendor/vnpy_qmt
```

如果你修改了 `vendor/vnpy_qmt`，请重新执行一次上述安装命令。

## 2. 准备 local 配置

复制示例配置为本地文件：

```bash
cp examples/no_ui/qmt_gateway_probe.example.json examples/no_ui/qmt_gateway_probe.local.json
```

至少确认以下字段：

- `gateway_name`
- `account`
- `mini_path`
- `session_id`
- `enable_md`
- `preload_contracts`
- `wait_seconds`

补充建议：

- `session_id` 不要机械照抄示例值（如 `9001`），应使用本机未占用的独立 `session_id`，避免会话冲突。
- `mini_path`：这是传给底层 `XtQuantTrader(path=...)` 的本地 QMT 运行目录，通常就是实际 `userdata_mini` 目录；配错会导致连接初始化落到错误环境。
- `enable_md`：这是是否启用行情侧能力；为 `false` 时会跳过 `md.connect()`，后续订阅请求也会被忽略。
- `preload_contracts`：仅在 `enable_md=true` 时有意义，会触发一次较重的全量合约预加载；只读 probe 默认建议保持 `false`。

## 3. 运行只读 probe

```bash
uv run python examples/no_ui/qmt_gateway_probe.py --config examples/no_ui/qmt_gateway_probe.local.json
```

连接和查询完成后会输出：

```text
QMT probe completed
```

## 4. 回到 vn.py 自带界面

probe 仅用于辅助排查连接与查询链路。正式使用仍建议回到 vn.py 自带界面，通过 `MainEngine.add_gateway(QmtGateway)` 和 UI 连接 `QMT`。

## 5. 修改优先级建议

若发现 gateway 行为有问题，优先直接修改 `vendor/vnpy_qmt`。外层 probe 只做辅助包装和验证，不承载正式 gateway 的实现职责。
