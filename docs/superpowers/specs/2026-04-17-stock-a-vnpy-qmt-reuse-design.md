# stock_a 实盘链路复用 vnpy_qmt 设计

日期：2026-04-17

## 背景

当前项目已经完成了以下事实确认：

- 历史数据链路已经以 `xtquant -> vnpy_xt -> stock_a -> AlphaLab -> BacktestingEngine` 跑通；
- `vnpy_qmt` 已被一次性 vendor 到当前工作树，可作为本地源码长期维护；
- 用户当前目标不是把整个 `vnpy_qmt` 原样挂到现有工程里，而是尽量复用其中成熟部分，补齐 `stock_a` 的实盘接入能力。

基于对 `vendor/vnpy_qmt` 的源码检查，可以确认：

- [`QmtGateway`](/C:/Users/sai/project/vnpy/.worktrees/xt-first/vendor/vnpy_qmt/vnpy_qmt/qmt_gateway.py) 是标准的 vn.py `BaseGateway` 实现入口；
- [`TD`](/C:/Users/sai/project/vnpy/.worktrees/xt-first/vendor/vnpy_qmt/vnpy_qmt/td.py) 封装了 `xtquant.xttrader` 的账户连接、下单、撤单、查单、查成交、查持仓、查资金；
- [`MD`](/C:/Users/sai/project/vnpy/.worktrees/xt-first/vendor/vnpy_qmt/vnpy_qmt/md.py) 封装了 `xtquant.xtdata` 的 tick 订阅和合约拉取；
- [`utils.py`](/C:/Users/sai/project/vnpy/.worktrees/xt-first/vendor/vnpy_qmt/vnpy_qmt/utils.py) 已经提供了一组可直接借鉴的代码、交易方向、订单状态、交易所映射。

问题不在于“它能不能用”，而在于“它应该在当前项目里承担哪一层职责”。

## 目标

本次设计目标是明确：

1. `vnpy_qmt` 中哪些内容可以直接复用；
2. 哪些内容只适合作为参考，不能作为当前项目的正式边界；
3. 它如何与当前 `stock_a.live` 规划对接；
4. 后续实现时应优先复用哪一层、重写哪一层。

## 方案选择

### 方案 A：直接把 vnpy_qmt 当正式网关接入

做法：

- 直接安装或导入 `vnpy_qmt`
- 在运行时注册 `QmtGateway`
- 让当前项目通过 gateway 机制走 QMT 实盘

优点：

- 接入速度最快；
- 能尽快验证“是否能连通、能否下单”。

缺点：

- 当前项目的 `stock_a` 运行边界会直接暴露给 vn.py gateway 交互模型；
- 很难自然表达 `probe`、`dry_run`、`simulate`、`live` 这些安全模式；
- 配置模型和用户当前需要的风险闸门不匹配。

### 方案 B：完全不复用 vnpy_qmt，自建 xttrader 接入

做法：

- 只保留 `xtquant` 官方 API 依赖
- 按当前 `stock_a.live` 设计从零封装 trader/runtime/service

优点：

- 边界最干净；
- 完全按当前项目目标设计。

缺点：

- 会重复实现大量已经验证过的字段映射和回报处理逻辑；
- 风险不在于“设计错”，而在于实现细节容易重复踩坑。

### 方案 C：复用 vnpy_qmt 的交易内核和映射层，自建 stock_a.live 外层

做法：

- 历史数据继续使用 `vnpy_xt`
- 实盘交易侧复用 `vnpy_qmt` 的 `TD` 接法和 `utils.py` 映射
- 行情侧按需少量借鉴 `MD.subscribe()`
- 最外层仍由当前项目自建 `stock_a.live` 配置、安全模式、运行编排

优点：

- 最符合当前项目“研究与交易分层”的设计；
- 最大限度复用已经存在的 xttrader 接法；
- 仍然可以保留 `probe -> dry_run -> simulate -> live` 这套安全闸门。

缺点：

- 需要做一层适配与拆解，不能直接整包拿来。

本次选择方案 C。

## 总体结论

`vnpy_qmt` 应当在当前项目里承担“**交易适配器参考实现**”的角色，而不是“**最终运行边界**”。

更具体地说：

- `vnpy_xt` 继续负责历史数据；
- `vnpy_qmt` 主要为实盘交易提供 xttrader 接法、订单回报映射、代码映射；
- `stock_a.live` 负责模式控制、安全闸门、配置模型、CLI 或服务编排；
- 不建议把 `vnpy_qmt` 的 `QmtGateway` 直接作为当前项目正式实盘入口。

## 复用拆解表

### 1. QmtGateway

源码：

- [`vendor/vnpy_qmt/vnpy_qmt/qmt_gateway.py`](/C:/Users/sai/project/vnpy/.worktrees/xt-first/vendor/vnpy_qmt/vnpy_qmt/qmt_gateway.py)

当前职责：

- 作为 vn.py `BaseGateway` 入口；
- 把 `MD` 和 `TD` 挂到 vn.py 标准网关接口上；
- 通过定时器轮询账户、持仓、委托、成交。

是否直接复用：

- 不建议直接复用为当前项目的最终入口。

建议处理方式：

- 保留为参考实现；
- 借鉴它的接口覆盖范围和轮询节奏；
- 不直接把 `QmtGateway` 暴露为 `stock_a.live` 的运行边界。

原因：

- 当前 `stock_a` 计划是“安全模式优先”的服务层，而不是先做一个 GUI gateway；
- `QmtGateway` 默认配置项只有“交易账号”“mini路径”，缺少 `session_id`、`mode`、`confirm_live`、`cash_limit`、`symbol_allowlist` 等运行控制；
- `close()` 生命周期较薄，不足以支撑后续严谨实盘运行。

### 2. TD

源码：

- [`vendor/vnpy_qmt/vnpy_qmt/td.py`](/C:/Users/sai/project/vnpy/.worktrees/xt-first/vendor/vnpy_qmt/vnpy_qmt/td.py)

当前职责：

- 创建 `StockAccount`；
- 创建 `XtQuantTrader`；
- 连接 QMT；
- 发起下单、撤单、查资金、查持仓、查委托、查成交；
- 把 XT 回报转换成 vn.py 风格对象。

是否直接复用：

- 可以作为最重要的复用来源。

建议处理方式：

- 优先复用连接逻辑；
- 优先复用异步查询和回调转换逻辑；
- 将其重构为当前项目自己的 `xt_trader.py` 适配器；
- 保留核心映射思路，但调整配置输入和生命周期控制。

建议保留的内容：

- `XtQuantTrader` 初始化与 `register_callback/start/connect/subscribe` 顺序；
- `order_stock_async` / `cancel_order_stock_async` / `query_stock_*_async` 这组调用路径；
- `on_stock_asset`、`on_stock_order`、`on_stock_position`、`on_stock_trade` 的事件转换骨架；
- `order_remark` 作为本地订单标识的思路。

建议重写或增强的内容：

- `session_id` 不能使用当前时间自动生成，应外部配置；
- `connect()` 应明确失败处理与状态返回，而不是只写日志；
- `close()` / 资源释放 / 重连策略需要补齐；
- 需要引入 `probe`、`dry_run`、`simulate`、`live` 模式分支；
- 需要增加显式的下单前安全校验。

### 3. MD

源码：

- [`vendor/vnpy_qmt/vnpy_qmt/md.py`](/C:/Users/sai/project/vnpy/.worktrees/xt-first/vendor/vnpy_qmt/vnpy_qmt/md.py)

当前职责：

- 订阅 tick；
- 扫描多个板块，建立合约缓存；
- 将 xt tick 转成 vn.py `TickData`。

是否直接复用：

- 只建议局部复用，不建议整体直接拿来。

建议处理方式：

- 可以借鉴 `subscribe_quote(..., period='tick')` 的订阅写法；
- 可以借鉴 tick 回调到 `TickData` 的字段映射；
- 不建议在当前项目正式实盘层保留“启动即全市场拉合约”的行为。

原因：

- 当前项目主线不是做一个通用 GUI gateway；
- 你已经有 `vnpy_xt` 负责历史数据，不需要让 `vnpy_qmt` 再承担历史研究入口；
- 实盘阶段最重要的是最小化、可控、可安全验证，而不是一上来拉全量合约。

### 4. utils.py

源码：

- [`vendor/vnpy_qmt/vnpy_qmt/utils.py`](/C:/Users/sai/project/vnpy/.worktrees/xt-first/vendor/vnpy_qmt/vnpy_qmt/utils.py)

当前职责：

- QMT 代码和 vn.py 交易所代码互转；
- 下单方向映射；
- 订单状态映射；
- 时间戳转 `datetime`。

是否直接复用：

- 强烈建议复用其核心思路，并按当前项目边界重构成独立公共映射模块。

建议处理方式：

- 把交易所代码、方向、状态映射抽到当前项目统一位置；
- 保持与 `stock_a` 已有 `.SH/.SZ` 外部风格边界兼容；
- 不直接让 `stock_a.live` 依赖 vendor 包内路径。

## 与当前 live 计划的映射

当前 live 计划中已有以下模块：

- `config.py`
- `models.py`
- `xt_trader.py`
- `service.py`

与 `vnpy_qmt` 的复用关系建议如下：

### config.py

- 不复用 `vnpy_qmt`
- 完全按当前项目自己的安全模型实现

原因：

- `vnpy_qmt` 没有这层配置抽象；
- 当前项目需要更细的模式控制和风险闸门。

### models.py

- 不直接复用 `vnpy_qmt`
- 参考其回报字段，定义项目自己的快照与订单草稿模型

原因：

- 当前项目需要的不只是 vn.py 原始对象，还需要 `probe`/`dry_run`/`simulate` 等模式结果模型。

### xt_trader.py

- 这是最应该复用 `vnpy_qmt.TD` 的地方

建议：

- 以 `TD` 为蓝本重写；
- 让它返回当前项目自己的结果对象，或者最少返回更稳定的中间模型；
- 不直接把 `TD` 原样搬进运行主线。

### service.py

- 不复用 `vnpy_qmt`
- 由当前项目自己编排

原因：

- `service.py` 承担的是“运行模式和安全策略”；
- 这是 `vnpy_qmt` 完全没有覆盖的一层。

## 最小实现建议

如果后续进入实现阶段，建议按以下顺序落地：

1. 先从 `utils.py` 提炼公共映射；
2. 再从 `TD` 提炼当前项目自己的 `XtTraderAdapter`；
3. 先只做 `probe` 模式，验证连接、查资金、查持仓、查委托、查成交；
4. 再接 `dry_run`；
5. 最后才放开真实下单。

## 明确不建议的做法

本次明确不建议：

1. 直接把 `QmtGateway` 原样作为当前项目正式实盘边界；
2. 直接把 `MD.get_contract()` 的全市场扫描逻辑接进启动流程；
3. 让当前项目正式代码长期直接 import `vendor.vnpy_qmt...` 并把 vendor 包当成最终架构依赖；
4. 在没有 `probe` 和 `dry_run` 的前提下直接走实盘下单。

## 结论

当前最合适的路线是：

- `vnpy_xt` 负责历史数据；
- `vnpy_qmt` 负责提供可复用的交易适配参考；
- `stock_a.live` 负责成为正式运行边界。

也就是说，后续实现时应当：

- **重用 `TD` 和 `utils.py` 的成熟部分**
- **只局部借鉴 `MD`**
- **不直接把 `QmtGateway` 当最终成品接入**
